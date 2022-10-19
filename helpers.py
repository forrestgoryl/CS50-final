import datetime, os, random, psycopg2, boto3
from additions.secret import secret_key
from additions.schema import schema
from additions.aws import aws_access_key_id, aws_secret_access
from pathlib import Path
from flask import Flask, render_template, redirect, session, request, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash

NAME = "YOUR_NAME"
S3_BUCKET = "YOUR_S3_BUCKET"
ALLOWED_EXTENSIONS = set(["png", "jpg", "jpeg", "gif", "PNG", "JPG", "JPEG", "GIF"])
IMAGE_PATH = "static/images/gallery/"
DATABASE_URL = os.environ["DATABASE_URL"]

def db_connect():
    with psycopg2.connect(DATABASE_URL, sslmode="require") as db:
        return db

def db_initialize_admin(cursor):
    cursor.execute("SELECT * FROM admin")
    if len(cursor.fetchall()) == 0:
        cursor.execute("""
        INSERT INTO admin (username, hash, email)
        VALUES (%s, %s, %s)
        """, 
        ("admin", 
        generate_password_hash("password"), 
        "fake@email.com")
        )

def allowed_file_type(filename):
    # returns True if filename ends in .png, .jpg, .jpeg, or .gif
    # otherwise returns False
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def gather_gallery_names(cursor):
    gallery_names = []
    cursor.execute("SELECT name FROM gallery")
    query = cursor.fetchall()
    for tuple in query:
        gallery_names.append(tuple[0])
    return gallery_names

def gather_photos_in_galleries(gallery_names, cursor):
    galleries = {}
    for name in gallery_names:
        galleries[name] = []
        i = 0
        command = """SELECT * FROM gallery 
        JOIN photo ON gallery.id = gallery_id 
        WHERE name = %s"""
        cursor.execute(command, (name, ))
        query = cursor.fetchall()
        for tuple in query:
            galleries[name].append({})
            galleries[name][i]["id"] = tuple[2]
            galleries[name][i]["src"] = IMAGE_PATH + tuple[3]
            galleries[name][i]["location"] = tuple[7]
            galleries[name][i]["description"] = str(tuple[6])
            galleries[name][i]["date"] = tuple[8]
            i += 1
        if galleries[name] == []:
            galleries.pop(name)
    return galleries
            
def gather_image_db_values(request_data, cursor):
    values = {}
    values["src"] = request_data["image"].filename
    values["location"] = request_data.get("location")
    values["description"] = request_data.get("desc")
    if request_data.get("potd") == None:
        values["potd"] = False
    else:
        values["potd"] = True
    if request_data.get("gallery_create"):
        gallery = request_data.get("gallery_create")
    else:
        gallery = request_data.get("gallery")
    result = gather_gallery_value(gallery, cursor)
    if result[0] != "error":
        values["gallery"] = result[1]
    else:
        return result
    return ["success", values]

def create_new_gallery_in_database(gallery, cursor):
    cursor.execute("INSERT INTO gallery (name) VALUES (%s)", (gallery, ))
    db.commit()

def gather_gallery_value(gallery, cursor):
    if gallery != "":
        gallery = gallery.title()
        command = "SELECT id FROM gallery WHERE name LIKE %s"
        cursor.execute(command, (gallery, ))
        result = cursor.fetchall()
        if len(result) == 0:
            create_new_gallery_in_database(gallery, cursor)
            command = "SELECT id FROM gallery WHERE name LIKE %s"
            cursor.execute(command, (gallery, ))
            gallery_value = cursor.fetchall()[0][0]
            return ["success", gallery_value]
        elif len(result) > 1:
            return ["error", "Database search returned abnormal number of results and could not process upload"]                  
        else:
            gallery_value = result[0][0]
    else:
        # values["gallery"] will be the 'General' gallery
        gallery_value = 1
    return ["success", gallery_value]

def query_database_for_admin(username, password, cursor):
    # returns ["error", "<error message>"] if username or password do not match
    # else returns ["success", admin id]
    cursor.execute("SELECT * FROM admin WHERE username = %s", (username,))
    query_admin = cursor.fetchall()
    if len(query_admin) != 1:
        return ["error", "Password and username don't match"]
    
    if not check_password_hash(query_admin[0][2], password):
        return ["error", "Password and username don't match"]
    
    admin_id = query_admin[0][0]
    return ["success", admin_id]

def connect_to_aws():
    # connects to Amazon Web Services (AWS)

    s3 = boto3.client("s3", 
        region_name = "us-east-2",
        aws_access_key_id = aws_access_key_id,
        aws_secret_access_key = aws_secret_access
    )
    return s3

def upload_file_to_aws(filename):
    if filename not in list_files_in_aws():
        s3 = connect_to_aws()
        upload_file_url = NAME + "/" + filename
        local_file_url = IMAGE_PATH + filename
        s3.upload_file(local_file_url, S3_BUCKET, upload_file_url)

def upload_file_to_local(filename):
    if filename not in list_files_in_local():
        download_single_file_from_aws(filename)

def list_files_in_local():
    files = []
    for file in os.listdir(path=IMAGE_PATH):
        if allowed_file_type(file):
            files.append(file)
    return files

def list_files_in_aws():
    s3 = connect_to_aws()
    response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=NAME)
    files = []
    for data in response["Contents"]:
        filename = data["Key"].replace(NAME + "/", "")
        files.append(filename)
    return files

def download_single_file_from_aws(filename):
    s3 = connect_to_aws()
    download_file_url = NAME + "/" + filename
    local_file_url = IMAGE_PATH + filename
    s3.download_file(S3_BUCKET, download_file_url, local_file_url)

def delete_file(photo_id, cursor):
    photo_src = gather_photo_src(photo_id, cursor)
    stop_photo_deletion = check_index_photos(photo_id, cursor)
    if stop_photo_deletion:
        return ["error", "Cannot delete photo. Photo is being used on homescreen. Upload more photos and label the good ones as 'Photo of the Day' eligible."]
    stop_photo_deletion = check_potd_photo(photo_id, cursor)
    if stop_photo_deletion:
        return ["error", "Cannot delete photo. Photo is being used as 'Photo of the Day' and there are no alternatives. Upload more photos and label them 'Photo of the Day' elibile."]
    delete_file_from_database(photo_id, cursor)
    delete_file_from_aws(photo_src)
    return ["success", "Successfully deleted photo"]

def gather_photo_src(photo_id, cursor):
    command = "SELECT * FROM photo WHERE id = %s"
    cursor.execute(command, (photo_id, ))
    return cursor.fetchone()[1]

def delete_file_from_aws(photo_src):
    s3 = connect_to_aws()
    key = NAME + "/" + photo_src
    s3.delete_object(Bucket=S3_BUCKET, Key=key)

def delete_file_from_database(photo_id, cursor):
    command = "DELETE FROM photo WHERE id = %s"
    cursor.execute(command, (photo_id, ))

def check_index_photos(photo_id, cursor):
    index_photos = gather_index_photos(cursor)
    for photo in index_photos:
        if photo[1] == photo_id:
            return replace_index_photo(photo[0], cursor)
    return False

def replace_index_photo(index_photo_id, cursor):
    potd_photos = gather_potd_photos()
    all_index_photo_ids = gather_index_photo_ids(cursor)
    if len(potd_photos) <= 4:   # if system has less than useable amount of index photos for home screen
        return True
    for photo in potd_photos:
        if photo[0] not in all_index_photo_ids:
            if photo[0] != index_photo_id:
                command = "UPDATE index_photo SET photo_id = %s WHERE id = %s"
                cursor.execute(command, (photo[0], index_photo_id))
                return False

def gather_index_photos(cursor):
    command = "SELECT * FROM index_photo"
    cursor.execute(command)
    return cursor.fetchall()

def gather_index_photo_ids(cursor):
    command = "SELECT photo_id FROM index_photo"
    cursor.execute(command)
    id_list = []
    for tuple in cursor.fetchall():
        id_list.append(tuple[0])
    return id_list

def gather_potd_photos(cursor):
    command = "SELECT * FROM photo WHERE potd = True"
    cursor.execute(command)
    return cursor.fetchall()

def gather_current_potd(cursor):
    command = "SELECT * FROM photo_of_the_day JOIN photo ON photo_id = photo.id WHERE photo_of_the_day.id = 1"
    cursor.execute(command)
    return cursor.fetchone()

def check_potd_photo(photo_id, cursor):
    command = "SELECT * FROM photo_of_the_day"
    cursor.execute(command)
    potd_photo = cursor.fetchall()
    potd_photo_id = int(potd_photo[0][1])
    if potd_photo_id == photo_id:
        return replace_potd_photo(photo_id, cursor)
    return False

def replace_potd_photo(photo_id, cursor):
    potd_photos = gather_potd_photos(cursor)
    for photo in potd_photos:
        if int(photo[0]) != photo_id:
            command = "UPDATE photo_of_the_day SET photo_id = %s"
            cursor.execute(command, (photo[0], ))
            return False
    # if all photos in potd_photos match photo_id, that means there is only one PotD photo
    return True

def create_image_folder():
    if not Path(IMAGE_PATH).exists():
        Path(IMAGE_PATH).mkdir(parents=True)

def process_request_info(request_data, cursor):
    values = {}
    values["src"] = request_data.files["image"].filename
    values["location"] = request_data.form.get("location")
    values["description"] = request_data.form.get("desc")
    if request_data.form.get("potd") == None:
        values["potd"] = False
    else:
        values["potd"] = True
    if request_data.form.get("gallery_create"):
        gallery = request_data.form.get("gallery_create")    
    else:
        gallery = request_data.form.get("gallery")
    result = gather_gallery_value(gallery, cursor)
    if result[0] != "error":
        values["gallery"] = result[1]
    else:
        return [result[0], result[1]]
    return values

def process_image(values, image, cursor):
    # takes in request.form data
    # gathers values for database submission
    # submits to database and uploads to AWS
    # returns a list of 2 strings: ["error", "<error message>"] or ["success", "Successfully uploaded image"]
    if not allowed_file_type(image.filename):
        return ["error", "You can only upload .png, .jpg, .jpeg, and .gif files"]
    try:
        create_image_folder()
        path = IMAGE_PATH + image.filename
        Path(path).touch()
        image.save(path)
        upload_file_to_aws(image.filename)
        insert_photo_into_postgres(cursor, values)
    except Exception as error:
        return ["error", str(error)]
    return ["success", "Successfully uploaded image"]

def insert_photo_into_postgres(cursor, values):
    command =   """INSERT INTO photo 
                (src, gallery_id, potd, description, location, uploaded)
                VALUES 
                (%s, %s, %s, %s, %s, %s)"""
    cursor.execute(command, (
        values["src"], 
        values["gallery"],
        values["potd"],
        values["description"], 
        values["location"],
        datetime.date.today()))

def gather_data_from_table(table, cursor, *args):
    command = f"SELECT * FROM {table}"
    for arg in args:
        command += " " + arg
    cursor.execute(command)
    return cursor.fetchall()

def return_date_in_database(table, cursor):
    command = f"SELECT day FROM {table}"
    cursor.execute(command)
    result = cursor.fetchall()
    if result == []:
        result = [datetime.date.min]
    return result

def date_in_database_is_today(date_in_database, table, cursor):
    today = datetime.date.today()
    for day in date_in_database:
        day = day[0]
        if day != today:
            command = f"UPDATE {table} SET day = %s"
            cursor.execute(command, (today, ))
            return False
    return True

def check_index_photos_date_in_database(cursor):
    potd_photos = gather_data_from_table("photo", cursor, "WHERE potd = True")
    index_photos = gather_data_from_table("index_photo", cursor)
    date_in_database = return_date_in_database("index_photo", cursor)
    result = date_in_database_is_today(date_in_database, "index_photo", cursor)
    # if today isn't day_in_database, update index_photo
    if not result:
        for x in range(3):
            index_photos = change_index_photo(x, index_photos, potd_photos, cursor)

def change_index_photo(x, index_photos, potd_photos, cursor):
    i = 0
    while index_photos[x] in index_photos and i < len(potd_photos):
        index_photos[x] = list(index_photos[x])
        index_photos[x][1] = potd_photos[random.randint(0, len(potd_photos) - 1)][0]
        index_photos[x] = tuple(index_photos[x])
        i += 1
    command = "UPDATE index_photo SET photo_id = %s WHERE id = %s"
    cursor.execute(command, (index_photos[x][1], index_photos[x][0]))
    return index_photos

def append_index_photos_src_to_photos(cursor):
    cursor.execute("SELECT * FROM index_photo INNER JOIN photo ON index_photo.photo_id = photo.id")
    index_photos = cursor.fetchall()
    photos = []
    for row in index_photos:
        # row[4] is the photo src
        src = IMAGE_PATH + row[4]
        photos.append(src)
    return photos

def find_fourth_photo_for_small_screens(cursor, photos):
    cursor.execute("SELECT * FROM photo")
    query_photo = cursor.fetchall()
    if len(query_photo) > 1:
        photo4 = ""
        # x is to break while loop if query only has previously selected photos inside
        x = 0
        while photo4 in photos or photo4 == "":
            i = random.randint(0, len(query_photo) - 1)
            photo4 = query_photo[i][1]
            x += 1
            if x >= len(query_photo):
                break
    elif len(query_photo) == 0:
        photo4 = ""
    else:
        photo4 = query_photo[0][1]
    photo4 = IMAGE_PATH + photo4
    return photo4

def check_filestorage_for_urls(photos):
    local_files = list_files_in_local()
    for filename in photos:
        if filename not in local_files:
            return False
    return True

def update_admin_info(info, update, admin_id):
    with db_connect() as db:
        with db.cursor() as cursor:
            command = f"UPDATE admin SET {info} = %s WHERE id = %s"
            cursor.execute(command, (update, admin_id))

# many functions use alert() to send messages to the admin
# they will end with alert() and expect alert() to redirect
def alert(message_type, text):
    session["alert"] = True
    session["message"] = {
        "message_type": message_type,
        "text": text
        }
    if session.get("route"):
        return redirect(session["route"])
    else:
        return redirect("/")