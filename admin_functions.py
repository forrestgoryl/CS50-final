import psycopg2, boto3

from werkzeug.security import check_password_hash
from helpers import *


def create_new_gallery(cursor, gallery):

    # Insert new gallery into database
    command =   """
                INSERT INTO gallery (name) 
                VALUES (%s)
                """
    cursor.execute(command, (gallery, ))

    # Select newly-created gallery ID
    command =   """
                SELECT id FROM gallery 
                WHERE name = %s
                """
    cursor.execute(command, (gallery, ))

    # Return newly-created gallery ID
    return cursor.fetchall()[0][0]


def delete_file(photo_id, cursor):

    # Determine whether photo is being used as an Index Photo
    if is_index_photo(photo_id, cursor):
        if not replace_index_photo(photo_id, cursor):
            return ["error", "Cannot delete photo. Photo is being used on homescreen. Upload more photos and label the good ones as 'Photo of the Day' eligible."]

    # Determine whether photo is being used as PotD
    if is_potd_photo(photo_id, cursor):
        if not replace_potd_photo(photo_id, cursor):
            return ["error", "Cannot delete photo. Photo is being used as 'Photo of the Day' and there are no alternatives. Upload more photos and label them 'Photo of the Day' elibile."]

    # Gather photo src
    list_tuple_photo_info = gather_data_from_table('photo', cursor, f'WHERE id = {photo_id}')
    photo_src = list_tuple_photo_info[0][1]

    # Delete photo from database and AWS
    delete_file_from_database(photo_id, cursor)
    delete_file_from_aws(photo_src)

    # Return success message for alert()
    return ["success", "Successfully deleted photo"]


def delete_file_from_aws(photo_src):

    # Connect to AWS
    s3 = connect_to_aws()

    # Craft key
    key = NAME + "/" + photo_src

    # Delete from AWS
    s3.delete_object(Bucket=S3_BUCKET, Key=key)


def delete_file_from_database(photo_id, cursor):

    command =   """
                DELETE FROM photo 
                WHERE id = %s
                """
    cursor.execute(command, (photo_id, ))


def gather_gallery_value(gallery, cursor):

    # Determine whether gallery selection exists
    if gallery != "":

        # Capitalize each first letter of user input
        gallery = gallery.title()

        # Query database
        command =   """
                    SELECT id FROM gallery 
                    WHERE name = %s
                    """
        cursor.execute(command, (gallery, ))
        result = cursor.fetchall()

        # Determine whether gallery is present in database
        if len(result) == 0:

            # Create new gallery
            new_gallery_id = create_new_gallery(cursor, gallery)

            print('Galleries in database: ', gather_data_from_table('gallery', cursor))

            # Return gallery ID
            return ["success", new_gallery_id]

        # Else, return found gallery ID
        else:
            gallery_value = result[0][0]
            return ["success", gallery_value]
    
    # If gallery wasn't input by user, return General gallery ID (1)
    else:
        return ["success", 1]


def info_update(request_data, cursor):

    # Define values
    values = {}

    # Read data from request.form
    location = request_data.form.get('location')
    desc = request_data.form.get('desc')
    
    # Determine whether to change location
    if location != '':
        values['location'] = location

    # Determine whether to change description
    if desc != '' :
        values['description'] = desc

    # Determine whether to change gallery
    if request_data.form.get('gallery') != '':

        # Process gallery
        result = process_gallery_input(request_data, cursor)

        # Process result
        if result[0] != "error":
            values["gallery_id"] = result[1]
        else:
            return [result[0], result[1]]

    # Read PotD value from request.form
    potd_value = request_data.form.get('potd')

    # If potd_value is not None, add to values in boolean form
    if potd_value != None:
        if potd_value == '1':
            values['potd'] = True
        elif potd_value == '0':
            values['potd'] = False

    # Define photo_id
    photo_id = request_data.form.get('id')

    # Send updated info to database
    for key, value in values.items():
        command =   """
                    UPDATE photo SET {} = %s
                    WHERE photo.id = %s
                    """.format(key)
        cursor.execute(command, (values[key], photo_id))
    
    # Return result
    return ['success', 'Successfully updated image information!']

def is_index_photo(photo_id, cursor):

    # Gather Index Photo IDs
    index_photos_ids = [photo[1] for photo in gather_data_from_table('index_photo', cursor)]

    # Return True if photo_id in index_photos_ids
    if photo_id in index_photos_ids:
        return True
    else:
        return False


def is_potd_photo(photo_id, cursor):

    # Query database
    command =   """
                SELECT * FROM photo_of_the_day
                """
    cursor.execute(command)

    # Determine whether photo_id is ID of PotD
    if photo_id == int(cursor.fetchall()[0][1]):
        return True
    else:
        return False


def process_gallery_input(request_data, cursor):

    # Determine whether to create a new gallery
    if request_data.form.get("gallery_create"):
        gallery = request_data.form.get("gallery_create")    
    else:
        gallery = request_data.form.get("gallery")

    print('\nInside process_gallery_input(), gallery is: ', gallery, '\n')
    
    # Process gallery input
    return gather_gallery_value(gallery, cursor)


def process_image(values, image, cursor):

    # Determine whether image filetype is allowed
    if not allowed_file_type(image.filename):

        # Craft error message telling user the allowed file extensions
        filetypes = [filetype for filetype in ALLOWED_EXTENSIONS]
        error_message = "You can only upload these file types: "
        for filetype in filetypes:
            error_message = error_message + filetype

        # Return error message
        return ["error", error_message]
    
    # Attempt to upload image to database and AWS
    try:
        # Create image folder if non-existant
        create_image_folder()

        # Craft absolute path and create empty file
        path = IMAGE_PATH + image.filename
        Path(path).touch()

        # Save image to file
        image.save(path)

        # Upload to AWS
        upload_file_to_aws(image.filename)

        # Upload to database
        upload_into_postgres(cursor, values)

    except Exception as error:
        return ["error", str(error)]
    return ["success", "Successfully uploaded image"]


def process_request_info(request_data, cursor):

    # Sort request data into variables inside values dict
    values = {}
    values["src"] = request_data.files["image"].filename
    values["location"] = request_data.form.get("location")
    values["description"] = request_data.form.get("desc")

    # If PotD wasn't marked by user, photo isn't PotD-eligble
    if request_data.form.get("potd") == None:
        values["potd"] = False
    else:
        values["potd"] = True

    # Process gallery input
    result = process_gallery_input(request_data, cursor)

    # Process result
    if result[0] != "error":
        values["gallery"] = result[1]
    else:
        return [result[0], result[1]]

    # Return request.form values as dict
    return values


def query_database_for_admin(username, password, cursor):
    # returns ["error", "<error message>"] if username or password do not match
    # else returns ["success", admin id]

    # Gather admin credentials using user-inputted username
    command =   """
                SELECT * FROM admin
                WHERE username = %s
                """
    cursor.execute(command, (username,))
    admin_credentials = cursor.fetchall()

    # If username didn't match, no results will have returned
    # Return error
    if len(admin_credentials) == 0:
        return ["error", "Password and username don't match"]
    
    # Determine whether admin_credentials password matches user-inputted password
    if not check_password_hash(admin_credentials[0][2], password):
        return ["error", "Password and username don't match"]
    
    # If check passes, return success
    admin_id = admin_credentials[0][0]
    return ["success", admin_id]


def replace_index_photo(photo_id, cursor):

    # Gather Index Photo IDs
    index_photo_ids = [photo[1] for photo in gather_data_from_table('index_photo', cursor)]
    
    # Sort through PotD photos
    for photo in gather_potd_photos():

        # Determine whether photo is current Index Photo
        if photo[0] not in index_photo_ids:

            # Determine whether photo is not the photo that is to be replaced
            if photo[0] != photo_id:

                # Update database and return True
                command =   """
                            UPDATE index_photo SET photo_id = %s 
                            WHERE id = %s
                            """
                cursor.execute(command, (photo[0], photo_id))
                return True
    
    # Return False if photo was not replaced
    return False


def update_admin_info(info, update, admin_id):

    # Open database connection
    with db_connect() as db:
        with db.cursor() as cursor:

            # Update information
            command =   """
                        UPDATE admin SET {} = %s 
                        WHERE id = %s
                        """.format(info)
            cursor.execute(command, (update, admin_id))


def upload_file_to_aws(filename):
    
    # Determine whether file is already in AWS
    if filename not in list_files_in_aws():

        # Connect to AWS
        s3 = connect_to_aws()

        # Craft URLs
        upload_file_url = NAME + "/" + filename
        local_file_url = IMAGE_PATH + filename

        # Upload file to AWS
        s3.upload_file(local_file_url, S3_BUCKET, upload_file_url)


def upload_into_postgres(cursor, values):
    
    command =   """
                INSERT INTO photo 
                (src, gallery_id, potd, description, location, uploaded)
                VALUES 
                (%s, %s, %s, %s, %s, %s)
                """
    cursor.execute(command, (
        values["src"], 
        values["gallery"],
        values["potd"],
        values["description"], 
        values["location"],
        datetime.date.today())
    )