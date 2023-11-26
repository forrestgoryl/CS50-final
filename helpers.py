import datetime, os, random, psycopg2, boto3
from additions.secret import secret_key
from additions.schema import schema
from additions.aws import aws_access_key_id, aws_secret_access
from pathlib import Path
from flask import Flask, render_template, redirect, session, request, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash

NAME = "YOUR NAME"
S3_BUCKET = "YOUR S3 BUCKET"
ALLOWED_EXTENSIONS = set(["png", "jpg", "jpeg", "gif"])
IMAGE_PATH = "static/images/gallery/"
DATABASE_URL = os.environ.get('DATABASE_URL')


# many functions use alert() to send messages to the admin
# they will return alert() and expect alert() to redirect
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


def allowed_file_type(filename):
    # returns True if filename ends in filetypes in ALLOWED_EXTENSIONS
    # otherwise returns False
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def connect_to_aws():
    # connects to Amazon Web Services (AWS)

    s3 = boto3.client("s3", 
        region_name = "us-east-2",
        aws_access_key_id = aws_access_key_id,
        aws_secret_access_key = aws_secret_access
    )
    return s3


def create_image_folder():

    # Creates empty folder for images the user inputs
    if not Path(IMAGE_PATH).exists():
        Path(IMAGE_PATH).mkdir(parents=True)


def db_connect():

    # Connect to Heroku PostgreSQL database (Heroku PostgreSQL app sets DATABASE_URL)
    with psycopg2.connect(DATABASE_URL, sslmode="require") as db:
        return db


def db_initialize_admin(cursor):

    # Query database for admin credentials
    result = gather_data_from_table('admin', cursor)

    # If admin credentials are not found, create admin
    if len(result) == 0:
        command =   """
                    INSERT INTO admin (username, hash, email)
                    VALUES (%s, %s, %s)
                    """
        cursor.execute(command, 
            ("admin", 
            generate_password_hash("password"), 
            "fake@email.com")
        )


def download_single_file_from_aws(filename):

    # Connect to AWS
    s3 = connect_to_aws()

    # Craft URLs
    download_file_url = NAME + "/" + filename
    local_file_url = IMAGE_PATH + filename

    # Download file
    s3.download_file(S3_BUCKET, download_file_url, local_file_url)


def gather_data_from_table(table, cursor, *args):

    # Craft command
    command =   f"""
                SELECT * FROM {table}
                """
    
    # Add other clauses to command ('WHERE _ = _')
    for arg in args:
        command += " " + arg

    # Query database
    cursor.execute(command)

    # Return query result
    return cursor.fetchall()


def list_files_in_local():

    # Return a list of files in IMAGE_PATH
    return [file for file in os.listdir(path=IMAGE_PATH) if allowed_file_type(file)]


def list_files_in_aws():

    # Connect to AWS
    s3 = connect_to_aws()

    # Query AWS for list of objects
    response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=NAME)
    
    # Return list of filenames from response object
    return [data['Key'].replace(NAME + '/', '') for data in response['Contents']]


def replace_potd_photo(photo_id, cursor):

    # Gather PotD photos
    potd_photos = gather_data_from_table('photo', cursor, 'WHERE potd = True')

    # Gather old PotD photo_id
    clauses =  'JOIN photo ON photo_id = photo.id WHERE photo_of_the_day.id = 1'
    old_potd_photo_id = gather_data_from_table('photo_of_the_day', cursor, clauses)[0][1]

    # Define variable for later use, to not recalculate
    number_of_potd_photos = len(potd_photos)

    # If there are at least two PotD photos,
    if number_of_potd_photos > 1:

        # Find a new PotD
        new_potd_photo_id = None
        while new_potd_photo_id == None or new_potd_photo_id == old_potd_photo_id:
            new_potd_photo_id = potd_photos[random.randint(0, number_of_potd_photos - 1)][0]

        # Update database
        command =   """
                    UPDATE photo_of_the_day
                    SET photo_id = %s,
                    DAY = %s
                    """
        cursor.execute(command, (new_potd_photo_id, datetime.date.today()))
        
        return True
    
    # Return False if function cannot replace PotD
    else:
        return False


def return_date_in_database(table, cursor):

    # Query database
    command =   f"""
                SELECT day FROM {table}
                """
    cursor.execute(command)
    result = cursor.fetchall()

    # If no result, make result a datetime obj of (1, 1, 1)
    if result == []:
        result = [datetime.date.min]

    return result
