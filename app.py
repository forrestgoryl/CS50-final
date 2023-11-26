import datetime, os, random, psycopg2, boto3

from additions.secret import secret_key
from additions.schema import schema
from additions.aws import aws_access_key_id, aws_secret_access
from pathlib import Path
from flask import Flask, render_template, redirect, session, request, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from __init__ import *
from helpers import *
from index_functions import *
from potd_functions import *
from gallery_functions import *
from contact_functions import *
from admin_functions import *

app = Flask(__name__)
app.secret_key = secret_key

# Initialize database
db_initialize()

# Download photos from Amazon Web Services
download_files_from_aws()



# webpage-serving routes ----

# homepage
@app.route("/")
def index():

    # Define route for helpers.alert() usage and POST methods
    session["route"] = "/"

    # Open database connection
    with db_connect() as db:
        with db.cursor() as cursor:

            # Manage Index Photos
            check_index_photos_date_in_database(cursor)

            # Gather Index Photos' src
            clauses = 'INNER JOIN photo ON index_photo.photo_id = photo.id'
            index_photos = gather_data_from_table('index_photo', cursor, clauses)
            index_photos_src = [IMAGE_PATH + photo[4] for photo in index_photos]

            # Gather 4th photo for small screen viewing
            photo4 = find_fourth_photo_for_small_screens(cursor)

            # Render webpage
            return render_template("index.html", photos=index_photos_src, photo4=photo4, name=NAME)


# photo of the day
@app.route("/potd")
def potd():

    # Define route for helpers.alert() usage and POST methods
    session["route"] = "/potd"

    # Open database connection
    with db_connect() as db:
        with db.cursor() as cursor:

            # Gather current PotD
            clauses = 'JOIN photo ON photo_id = photo.id WHERE photo_of_the_day.id = 1'
            potd = gather_data_from_table('photo_of_the_day', cursor, clauses)[0]

            # Check whether PotD exists
            if potd != None:

                # Check whether PotD date is current
                if datetime.date.today() != potd[2]:

                    # If date isn't current, replace PotD
                    replace_potd_photo(potd[1], cursor)
                    potd = gather_data_from_table('photo_of_the_day', cursor, clauses)[0]
                
            # If PotD doesn't exist in database, create PotD
            else:
                create_potd(cursor)
                potd = gather_data_from_table('photo_of_the_day', cursor, clauses)[0]

            # Gather PotD src
            potd_src = IMAGE_PATH + potd[4]

            # Render webpage
            return render_template("potd.html", potd=potd, potd_src=potd_src, name=NAME)   


# gallery
@app.route("/gallery")
def gallery():

    # Define route for helpers.alert() usage and POST methods
    session["route"] = "/gallery"

    # Open database connection
    with db_connect() as db:
        with db.cursor() as cursor:

            # Gather names of galleries that are in the database
            gallery_names = gather_gallery_names(cursor)

            # Create dict of photos in galleries
            galleries = gather_photos_in_galleries(gallery_names, cursor)

            # Determine whether to serve Admin Gallery
            if session.get("admin"):

                # Determine whether helpers.alert() message exists
                if session["alert"]:
                    message = session["message"]
                    session["alert"] = False

                    # Render Admin Gallery with helpers.alert() message
                    return render_template("adminGallery.html", gallery_names=gallery_names, galleries=galleries, message=message, name=NAME)

                else:
                    
                    # Render Admin Gallery without helpers.alert() message
                    return render_template("adminGallery.html", gallery_names=gallery_names, galleries=galleries, name=NAME)
            
            # Render non-Admin Gallery
            return render_template("gallery.html", galleries=galleries, name=NAME)


# contact
@app.route("/contact")
def contact():

    # Define route for helpers.alert() usage and POST methods
    session["route"] = "/contact"

    # Open database connection
    with db_connect() as db:
        with db.cursor() as cursor:

            # Select five photos
            photos = return_five_photos(cursor)

            # Sort out the photos src
            photos_src = [IMAGE_PATH + photo[1] for photo in photos]

            # Check for helpers.alert() messages
            if session.get('alert'):
                if session['alert']:
                    message = session['message']
                    session['alert'] = False

                # Render webpage with helpers.alert() message
                return render_template("contact.html", photos=photos_src, name=NAME, message=message)

            # Render webpage without helpers.alert() message
            else:
                return render_template("contact.html", photos=photos_src, name=NAME)


# admin settings
@app.route("/settings")
def settings():

    # Determine whether admin is logged in
    if session.get("admin"):

        # Define route for helpers.alert() usage and POST methods
        session["route"] = "/settings"

        # Determine whether helpers.alert() message exists
        if session["alert"]:
            message = session["message"]
            session["alert"] = False

            # Render webpage with message
            return render_template("settings.html", message=message, name=NAME)
        
        # Render webpage without message
        return render_template("settings.html", name=NAME)
    
    # If admin isn't logged in, redirect to index
    else:
        return redirect("/")


# login page
@app.route("/login")
def serve_login_webpage():

    # Determine whether helpers.alert() message exists
    if session.get("alert"):
        if session["alert"]:
            message = session["message"]
            session["alert"] = False

            # Render webpage with message
            return render_template("login.html", message=message, name=NAME)

    # Render webpage without message
    else:
        return render_template("login.html", name=NAME)



# non-webpage-serving routes ----

# admin login
@app.route("/admin_login", methods=["POST"])
def admin_login():

    # Open database connection
    with db_connect() as db:
        with db.cursor() as cursor:

            # Gather data from request.form
            username = request.form.get("username")
            password = request.form.get("password")

            # Query database
            result = query_database_for_admin(username, password, cursor)

            # If username and password do not match database
            if result[0] == "error":
                session["route"] = "/login"
                return alert(result[0], result[1])
            
            # Otherwise login and redirect to session['route'] or index
            else:
                session["admin"] = result[1]
                session["alert"] = False
                if session.get("route"):
                    if session["route"] != "/login":
                        return redirect(session["route"])
                return redirect("/")


# upload image
@app.route("/upload", methods=["POST"])
def upload():

    # Determine whether image was sent in request.files
    if "image" not in request.files:
        return alert("error", "No image was submitted")

    # Open database connection
    with db_connect() as db:
        with db.cursor() as cursor:

            # Gather values in request object
            values = process_request_info(request, cursor)

            # Determine whether error was thrown (values will be type list if error was thrown)
            if type(values) == list:
                return alert(values[0], values[1])
            
            # Upload image
            result = process_image(values, request.files["image"], cursor)

            # Return result of process_image (either succcess or error)
            return alert(result[0], result[1])


@app.route('/update', methods=['POST'])
def update():

    # Open database connection
    with db_connect() as db:
        with db.cursor() as cursor:

            # Send update info request to database
            result = info_update(request, cursor)

            # Return result
            return alert(result[0], result[1])


# send an email to admin
@app.route("/email", methods=["POST"])
def email():

    # Open database connection
    with db_connect() as db:
        with db.cursor() as cursor:

            # Take form information
            client_email = request.form.get('email')
            client_message = request.form.get('text')

            result = send_email(client_email, client_message, cursor)
            
            # Tell client the result
            if result:
                return alert('success', "You successfully sent me an email. I'll respond as soon as I can!")
            else:
                return alert('error', "Something went wrong! Sorry about that, please try again.")


# update email
@app.route("/update_email", methods=["POST"])
def update_email():

    # Determine whether admin is logged in
    if session.get("admin"):

        # Determine whether new_email information is included in request.form
        if request.form.get("new_email"):

            new_email = request.form.get("new_email")

            # Determine whether confirmation matches
            if new_email != request.form.get("confirm_email"):
                return alert("error", "Email did not match confirmation")
            
            # Update email
            else:
                update_admin_info("email", new_email, session["admin"])
                return alert("success", f"Email changed successfully to {new_email}")


# update username
@app.route("/update_username", methods=["POST"])
def update_username():

    # Determine whether admin is logged in
    if session.get("admin"):

        # Determine whether new_username information is included in request.form
        if request.form.get("new_username"):

            new_username = request.form.get("new_username")

            # Determine whether confirmation matches
            if new_username != request.form.get("confirm_username"):
                return alert("error", "Username did not match confirmation")

            # Update username
            else:
                update_admin_info("username", new_username, session["admin"])
                return alert("success", f"Username changed successfully to {new_username}")


# update password
@app.route("/update_password", methods=["POST"])
def update_password():

    # Determine whether admin is logged in
    if session.get("admin"):

        # Determine whether new_password information is included in request.form
        if request.form.get("new_password"):

            new_password = request.form.get("new_password")

            # Determine whether confirmation matches
            if new_password != request.form.get("confirm_password"):
                return alert("error", "Password did not match confirmation")
            
            # Update password
            else:
                new_hash = generate_password_hash(new_password)
                update_admin_info("hash", new_hash, session["admin"])
                return alert("success", "Password changed successfully")


# delete a photo
@app.route("/delete", methods=["POST"])
def delete_photo():

    # Determine whether admin is logged in
    if session.get("admin"):

        # Open database connection
        with db_connect() as db:
            with db.cursor() as cursor:

                # Gather ID from request.form
                photo_id = int(request.form.get("id"))

                # Attempt to delete photo
                result = delete_file(photo_id, cursor)

                # Return message (either 'error' or 'success')
                return alert(result[0], result[1])
                

# admin logout
@app.route("/logout", methods=["POST"])
def logout():

    # Clear all session information
    session.clear()

    # Redirect to index route
    return redirect("/")


@app.route("/favicon.ico")
def favicon():
    # Favicon used from https://iconscout.com/icon/camera-1468811 under creative common license
    return send_from_directory(
        os.path.join(app.root_path, "static"), 
        "favicon.ico", mimetype="image/vnd.microsoft.icon"
        )


if __name__ == "__main__":
    app.debug = True
    app.run()