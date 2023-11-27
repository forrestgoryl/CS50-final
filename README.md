# THANK YOU for visiting my repository. A short video walkthrough of what this project produces is available here:

[https://youtu.be/D7EX37tyVLU](https://youtu.be/D7EX37tyVLU)

## Photogallery

Example website that this code produces: [photosbyforrest.herokuapp.com](photosbyforrest.herokuapp.com)

This project is a website application that allows an amateur photographer the ability to upload photos to distinct galleries and showcase the best ones by allowing the photo to be 'Photo of the Day' eligible. It can be easily used by a non-technical person and can be shared with prospective clients and friends.

## -- Technical Details --

This is a Flask-based application that is reliant on Heroku and Amazon Web Services (AWS) S3 storage. It utilizes Bootstrap for much of the CSS and makes use of Lokesh Dhakar's Lightbox2 javascript library (http://lokeshdhakar.com/projects/lightbox2/).

There are three things that must be done to use the application properly:

1. Setup `additions/aws.py` and `additions/secret.py` appropriately. You will need an AWS access key ID and secret access.

2. In `helpers.py`, change `NAME` to your name and S3_BUCKET to your own bucket that you wish photos to be stored in.

3. Finally, upload your code to a Heroku dyno. Make sure to set the dyno up with the requisite support detailed in requirements.txt. You will need to addon a Heroku PostgreSQL database.

After it is setup, the project should be usable without technical know-how via the website itself.

## File By File Details

#### additions

A folder containing `aws.py`, `schema.py`, and `secret.py`.

`aws.py` contains two variables. These are used to connect with AWS S3.
`schema.py` contains code that sets up the postgresql DB.
`secret.py` contains the secret key variable.

#### node_modules

A folder containing bootstrap and it's accompanying files.

#### static

A folder containing CSS styles, Javascript files, `lightbox2`, the `favicon.ico` file, and `images`.

`styles` contains relevant CSS files.
`scripts` contains relevant Javascript files.
`lightbox2` contains CSS and javascript relevant to the lightbox2 library, which enables the user to click on any image and see a bigger version of the image transition into view.
`images` contains gallery, which is an empty folder used to house photos downloaded from AWS S3. `images` also contains the `update.png` and `x.png` file, used in `adminGallery.html`.

#### templates

A folder housing all html files used by the application.

#### **init**.py

Contains two functions integral to the setup of each new Heroku Dyno.

#### app.py

Contains major functions regarding website routes and POST-related processes.

#### helpers.py

Contains minor functions supporting the functions in the other python files.

#### index_functions.py

Contains functions relating to the functionality of the homepage.

#### potd_functions.py

Contains functions relating to the 'Photo of the Day' webpage.

#### gallery_functions.py

Contains functions relating to the 'Gallery' webpage.

#### contact_functions.py

Contains functions relating to the 'Contact' webpage.

#### admin_functions.py

Contains all admin-related functions in the project.

#### Procfile

Contains instruction information for Heroku's Dynos.

#### requirements.txt

Contains package names of requisite packages.
