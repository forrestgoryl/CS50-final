schema = [
    """
    CREATE TABLE IF NOT EXISTS admin (
        id SERIAL PRIMARY KEY,
        username VARCHAR(100),
        hash TEXT,
        email VARCHAR(255)
    )""",
    """
    CREATE TABLE IF NOT EXISTS gallery (
        id SERIAL PRIMARY KEY,
        name VARCHAR(50)
    )""",
    """
    CREATE TABLE IF NOT EXISTS photo (
        id SERIAL PRIMARY KEY,
        src TEXT,
        gallery_id INTEGER REFERENCES gallery,
        potd BOOLEAN,
        description TEXT,
        location VARCHAR(255),
        uploaded DATE
    )""",
    """
    CREATE TABLE IF NOT EXISTS photo_of_the_day (
        id SERIAL PRIMARY KEY,
        photo_id INTEGER REFERENCES photo,
        day DATE
    )""",
    """
    CREATE TABLE IF NOT EXISTS index_photo (
        id SERIAL PRIMARY KEY,
        photo_id INTEGER REFERENCES photo,
        day DATE
    )"""
]