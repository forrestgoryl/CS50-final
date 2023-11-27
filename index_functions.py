import datetime, psycopg2, random

from helpers import *


def check_index_photos_date_in_database(cursor):

    # Determine whether Index Photos have changed today
    date_in_database = return_date_in_database("index_photo", cursor)
    result = date_in_database_is_today(date_in_database, "index_photo", cursor)

    # If Index Photos haven't changed today, change Index Photos
    if not result:
        potd_photos = gather_data_from_table("photo", cursor, "WHERE potd = True")
        index_photos = gather_data_from_table("index_photo", cursor)
        for x in range(3):
            index_photos = change_index_photo(x, index_photos, potd_photos, cursor)


def change_index_photo(x, index_photos, potd_photos, cursor):

    # Change Index Photo if there are at least 3 Index Photos and more than 3 PotD Photos
    if len(index_photos) > 2 and len(potd_photos) > 3:

        # Grab list of old index_photos IDs
        index_photos_ids = [photo[1] for photo in index_photos]

        # Make index_photos[x] a list instead of tuple so that it is changeable
        index_photos[x] = list(index_photos[x])

        # Get PotD ID that is not currently in index_photo_ids
        while index_photos[x][1] in index_photos_ids:
            index_photos[x][1] = potd_photos[random.randint(0, len(potd_photos) - 1)][0]

        # Update database
        command =   """
                    UPDATE index_photo SET photo_id = %s
                    WHERE id = %s
                    """
        cursor.execute(command, (index_photos[x][1], index_photos[x][0]))
    
    # Insert new Index Photo if amount is less than 3
    elif len(index_photos) < 3:
        command =   """
                    INSERT INTO index_photo (photo_id, day) VALUES (%s, %s)
                    """
        cursor.execute(command, (potd_photos[x][0], potd_photos[x][6]))

    return index_photos


def date_in_database_is_today(date_in_database, table, cursor):
    today = datetime.date.today()
    
    # Check all datapoints in list date_in_database. date_in_database is a list of tuples.
    for day in date_in_database:

        # Change day to datetime obj from tuple
        day = day[0]

        # If the day isn't today, update dates in database and return False
        if day != today:
            command =   """
                        UPDATE {} SET day = %s
                        """.format(table)
            cursor.execute(command, (today, ))
            return False
    
    # Return True if every day == today
    return True


def find_fourth_photo_for_small_screens(cursor):

    # Query database for photos
    command =   """
                SELECT * FROM photo
                """
    cursor.execute(command)
    photos = cursor.fetchall()

    # Query database for Index Photos
    command =   """
                SELECT * FROM index_photo
                JOIN photo ON photo_id = photo.id
                """
    cursor.execute(command)
    index_photos = cursor.fetchall()

    # Gather Index Photo's photo_ids
    index_photo_ids = [photo[1] for photo in index_photos]

    photo4 = None

    # Pick new photo randomly that is not already an Index Photo
    if len(photos) > 3:
        while photo4 == None or photo4[0] in index_photo_ids:
            photo4 = photos[random.randint(0, len(photos) - 1)][1]
        photo4 = IMAGE_PATH + photo4
    
    return photo4
