import boto3
from pathlib import Path
from additions.secret import secret_key
from additions.schema import schema
from additions.aws import aws_access_key_id, aws_secret_access
from helpers import db_connect, connect_to_aws, db_initialize_admin, list_files_in_aws, list_files_in_local, create_image_folder, NAME, IMAGE_PATH, S3_BUCKET, download_single_file_from_aws

def db_initialize():
    # connects to db
    # uses schema.py's script to create db tables
    with db_connect() as db:
        with db.cursor() as cursor:
            for command in schema:
                cursor.execute(command)
            db_initialize_admin(cursor)

def download_files_from_aws():
    create_image_folder()
    local_files = list_files_in_local()
    for filename in list_files_in_aws():
        if filename not in local_files:
            download_single_file_from_aws(filename)