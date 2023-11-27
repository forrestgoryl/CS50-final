import psycopg2 

from helpers import *


def gather_gallery_names(cursor):
    
    # Query database
    command =   """ 
                SELECT name FROM gallery
                """ 
    cursor.execute(command)

    # Fetch query results
    gallery_names = cursor.fetchall()

    # Return list of gallery names
    return [gallery_name[0] for gallery_name in gallery_names]


def gather_photos_in_galleries(gallery_names, cursor):

    # Create galleries dict
    galleries = {}

    # Query database for each gallery name
    for name in gallery_names:

        command =   """
                    SELECT * FROM gallery 
                    JOIN photo ON gallery.id = gallery_id 
                    WHERE name = %s
                    """
        cursor.execute(command, (name, ))

        # Fetch query results
        photos_in_gallery = cursor.fetchall()

        # Append photo data to gallery name in galleries dict
        galleries[name] = []
        i = 0
        for photo in photos_in_gallery:
            galleries[name].append({})
            galleries[name][i]["id"] = photo[2]
            galleries[name][i]["src"] = IMAGE_PATH + photo[3]
            galleries[name][i]["location"] = photo[7]
            galleries[name][i]["description"] = str(photo[6])
            galleries[name][i]["date"] = photo[8]
            i += 1

        # Remove gallery from dict if no photos exist inside the gallery
        if galleries[name] == []:
            galleries.pop(name)
            
            # Remove gallery from database
            command =   """
                        DELETE FROM gallery
                        WHERE name = %s
                        """
            cursor.execute(command, (name, ))

    # Return dict of galleries
    return galleries