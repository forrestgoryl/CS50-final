import psycopg2, random, smtplib, os

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from helpers import *


def return_admin_email(cursor):

    command =   """
                SELECT email FROM admin
                """
    cursor.execute(command)
    return cursor.fetchone()[0]


def return_five_photos(cursor):
    
    # Gather photos
    command =   """ 
                SELECT * FROM photo
                """
    cursor.execute(command)
    return select_five_photos_randomly(cursor.fetchall())


def select_five_photos_randomly(photos):

    # Define variables
    selected_photos = []
    length_photos = len(photos)

    while len(selected_photos) < 5 and len(selected_photos) != length_photos:
        random_index = None

        # Choose index randomly but also not in selected_photos
        while random_index == None or photos[random_index] in selected_photos:
            random_index = random.randint(0, length_photos - 1)
        
        # Append new photo
        selected_photos.append(photos[random_index])
    
    return selected_photos


def send_email(client_email, client_message, cursor):
    
    try:
        # Read environment variables
        host = os.environ.get('MAILERTOGO_SMTP_HOST')
        port = os.environ.get('MAILERTOGO_SMTP_PORT', 587)
        username = os.environ.get('MAILERTOGO_SMTP_USER')
        password = os.environ.get('MAILERTOGO_SMTP_PASSWORD')

        # Gather admin email
        admin_email = gather_data_from_table('admin', cursor)[0][3]

        # Define sender email
        sender_email = 'noreply@photosby{}.com'.format(NAME.lower())

        # Setup server
        server = smtplib.SMTP(host, port)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(username, password)

        # Craft message
        message = MIMEMultipart()
        message['Subject'] = "New Contact Request from Photogallery"
        message['From'] = sender_email
        message['To'] = admin_email
        body = MIMEText("""
                    You've got a new message!
                    From: {},
                    Message: {}
                    """.format(client_email, client_message), 'plain')
        message.attach(body)

        # Send email
        server.sendmail(sender_email, admin_email, message.as_string())

        # Close server
        server.close()

        return True

    except Exception:
        return False
