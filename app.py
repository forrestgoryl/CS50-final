import datetime, os, random, psycopg2, boto3

from helpers import *
from __init__ import *
from additions.secret import secret_key
from additions.schema import schema
from additions.aws import aws_access_key_id, aws_secret_access
from pathlib import Path
from flask import Flask, render_template, redirect, session, request, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = secret_key

db_initialize()
download_files_from_aws()

# webpage-serving routes ----

# homepage
@app.route("/")
def index():
    session["route"] = "/"
    with db_connect() as db:
        with db.cursor() as cursor:
            check_index_photos_date_in_database(cursor)
            photos = append_index_photos_src_to_photos(cursor)
            photo4 = find_fourth_photo_for_small_screens(cursor, photos)
            return render_template("index.html", photos=photos, photo4=photo4, name=NAME)

# photo of the day
@app.route("/potd")
def potd():
    session["route"] = "/potd"
    with db_connect() as db:
        with db.cursor() as cursor:
            potd = gather_current_potd(cursor)
            potd_date = potd[2]
            if datetime.date.today() != potd_date:
                potd_photo_id = potd[1]
                replace_potd_photo(potd_photo_id, cursor)
                potd = gather_current_potd(cursor)
            potd_src = IMAGE_PATH + potd[4]
    return render_template("potd.html", potd=potd, potd_src=potd_src, name=NAME)

# gallery
@app.route("/gallery")
def gallery():
    session["route"] = "/gallery"
    with db_connect() as db:
        with db.cursor() as cursor:
            gallery_names = gather_gallery_names(cursor)
            galleries = gather_photos_in_galleries(gallery_names, cursor)
            if session.get("admin"):
                if session["alert"]:
                    message = session["message"]
                    session["alert"] = False
                    return render_template("adminGallery.html", gallery_names=gallery_names, galleries=galleries, message=message, name=NAME)
                else:
                    return render_template("adminGallery.html", gallery_names=gallery_names, galleries=galleries, name=NAME)
            else:
                return render_template("gallery.html", galleries=galleries, name=NAME)

# contact
@app.route("/contact")
def contact():
    session["route"] = "/contact"
    with db_connect() as db:
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM photo LIMIT 5")
            photos = cursor.fetchall()
            cursor.execute("SELECT email FROM admin")
            email = cursor.fetchone()[0]
            photosSRC = []
            for row in photos:
                src = IMAGE_PATH + row[1]
                photosSRC.append(src)
            return render_template("contact.html", photos=photosSRC, email=email, name=NAME)

# admin settings
@app.route("/settings")
def settings():
    if session.get("admin"):
        session["route"] = "/settings"
        if session["alert"]:
            message = session["message"]
            session["alert"] = False
            return render_template("settings.html", message=message, name=NAME)
        return render_template("settings.html", name=NAME)
    else:
        return redirect("/")

# login page
@app.route("/login")
def serve_login_webpage():
    if session.get("alert"):
        if session["alert"]:
            message = session["message"]
            session.clear()
            return render_template("login.html", message=message, name=NAME)
    else:
        return render_template("login.html", name=NAME)


# non-webpage-servering routes ----

# admin login
@app.route("/admin_login", methods=["POST"])
def admin_login():
    with db_connect() as db:
        with db.cursor() as cursor:
            username = request.form.get("username")
            password = request.form.get("password")
            result = query_database_for_admin(username, password, cursor)
            if result[0] == "error":
                session["route"] = "/login"
                return alert(result[0], result[1])
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
    if "image" not in request.files:
        return alert("error", "No image was submitted")
    with db_connect() as db:
        with db.cursor() as cursor:
            values = process_request_info(request, cursor)
            if type(values) == list:
                if values[0] == "error":
                    return alert(values[0], values[1])
            result = process_image(values, request.files["image"], cursor)
            return alert(result[0], result[1])

# update email
@app.route("/update_email", methods=["POST"])
def update_email():
    if session.get("admin"):
        if request.form.get("new_email"):
            new_email = request.form.get("new_email")
            if new_email != request.form.get("confirm_email"):
                return alert("error", "Email did not match confirmation")
            else:
                update_admin_info("email", new_email, session["admin"])
                return alert("success", f"Email changed successfully to {new_email}")

# update username
@app.route("/update_username", methods=["POST"])
def update_username():
    if session.get("admin"):
        if request.form.get("new_username"):
            new_username = request.form.get("new_username")
            if new_username != request.form.get("confirm_username"):
                return alert("error", "Username did not match confirmation")
            else:
                update_admin_info("username", new_username, session["admin"])
                return alert("success", f"Username changed successfully to {new_username}")

# update password
@app.route("/update_password", methods=["POST"])
def update_password():
    if session.get("admin"):
        if request.form.get("new_password"):
            new_password = request.form.get("new_password")
            if new_password != request.form.get("confirm_password"):
                return alert("error", "Password did not match confirmation")
            else:
                new_hash = generate_password_hash(new_password)
                update_admin_info("hash", new_hash, session["admin"])
                return alert("success", "Password changed successfully")

# delete a photo
@app.route("/delete", methods=["POST"])
def delete_photo():
    if session.get("admin"):
        with db_connect() as db:
            with db.cursor() as cursor:
                photo_id = int(request.form.get("id"))
                result = delete_file(photo_id, cursor)
                return alert(result[0], result[1])
                

# admin logout
@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
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