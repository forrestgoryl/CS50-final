THANK YOU for visiting my repository. A short video description of this project is available here:

https://youtu.be/Fa4Z_K0mOBE

This project is a website application that allows an amateur photographer the ability to upload photos to distinct galleries and showcase the best ones by allowing the photo to be 'Photo of the Day' eligible. It can be easily used by a non-technical person and can be shared with prospective clients and friends.

The website consists of four main pages: Home, Photo of the Day (PotD), Gallery, and Contact. 

Home showcases three photos that change daily which are eligible for PotD, but does not provide descriptions of the photos. This page is meant to show-off your best work and encourage the website user to click on the Photo of the Day or Gallery page. 

Photo of the Day showcases one photo that changes daily and shows a description written by the photographer at the bottom of the photo. It is meant to highlight your best work.

Gallery showcases all photos uploaded to the application and they are organized in galleries, named by the photographer.

Contact has a form that can allow an email to be sent to the photographer, while also protecting the photographer from spam via an anonymous email sender. The photographer can read the email and respond via their personal email once they have verified the sender's authenticity.

The website relies on the photographer logging in as an admin and uploading photos via the Gallery page. The default username and password is:

        username: admin
        password: password

These are changable, and should be changed, via the Settings page that shows once an admin is logged in.



-- Technical Details --

This is a Flask-based application that is reliant on Heroku and Amazon Web Services (AWS) S3 storage. It utilizes Bootstrap for much of the CSS and makes use of Lokesh Dhakar's Lightbox2 javascript library (http://lokeshdhakar.com/projects/lightbox2/).

There are four things that must be done to use the application properly:

        1.) In additions/aws.py, change aws_access_key_id and aws_secret_access to your own access key and secret key.
        2.) In additions/secret.py, generate a more-secure secret key.
        3.) In helpers.py, change NAME to your name and S3_BUCKET to your own bucket that you wish photos to be stored in.
        4.) Finally, upload your code to a Heroku dyno. Make sure to set the dyno up with the requisite support detailed in requirements.txt.

After it is setup, the project should be usable without technical know-how via the website itself.