import psycopg2, random

from helpers import *


def create_potd(cursor):

    # Grab list of potd photos
    potd_photos = gather_data_from_table('photo', cursor, 'WHERE potd = True')

    if len(potd_photos) != 0:

        # Pick PotD at random from pool of potd-enabled photos
        potd_id = potd_photos[random.randint(0, len(potd_photos) - 1)][0]

        # Insert into database
        command =   """
                    INSERT INTO photo_of_the_day (photo_id, day)
                    VALUES (%s, %s)
                    """
        cursor.execute(command, (potd_id, datetime.date.today()))

        return True
    
    # If there are no PotD photos, do not create PotD
    else:
        return False