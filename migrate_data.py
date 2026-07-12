"""
One-time data migration script: SQLite (hotels.db) -> PostgreSQL.

Used once to migrate existing data (users, hotels, rooms, bookings,
experiences, experience_requests) after switching the app's database
from SQLite to PostgreSQL. Schema/tables are created separately via
Alembic migrations (`alembic upgrade head`) before running this script.

NOT intended to be re-run against a Postgres database that already has
data in it -- primary keys are preserved via session.merge(), so
re-running this would attempt to overwrite/collide with existing rows
rather than append new ones.

Kept in the repo as a record of the migration process, not as part of
the app's normal runtime.
"""

import sqlite3
from database import SessionLocal
import models

# Connect directly to your old SQLite file
#? What is doing this? - what is connecting to this? the file? python? what?
sqlite_conn = sqlite3.connect("hotels.db")
sqlite_conn.row_factory = sqlite3.Row
cursor = sqlite_conn.cursor()

db = SessionLocal()

def migrate_table(table_name, model_class):
    cursor.execute(f"SELECT * FROM {table_name}")   # ← ask SQLite: "give me every row in this table"
    rows = cursor.fetchall()                         # ← actually retrieve those rows into Python

    for row in rows:                                 # ← loop through each row one at a time
        row_dict = dict(row)                         # ← convert it into a plain Python dictionary
        obj = model_class(**row_dict)                # ← build a SQLAlchemy model object using that data
        db.merge(obj)                                # ← tell SQLAlchemy: "save this object" (into Postgres!)

    db.commit()                                       # ← actually write everything to Postgres

migrate_table("users", models.User)
migrate_table("hotels", models.Hotel)
migrate_table("rooms", models.Room)
migrate_table("experiences", models.Experience)
migrate_table("bookings", models.Booking)
migrate_table("experience_requests", models.ExperienceRequest)

db.close()
sqlite_conn.close()

print("Migration complete.")