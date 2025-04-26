from app import app
from extensions import db
import sqlite3
import os

def update_database():
    with app.app_context():
        # Get the database path
        # Try to find the database file
        possible_paths = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'healthconnect.db'),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'healthconnect.db'),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')
        ]

        db_path = None
        for path in possible_paths:
            if os.path.exists(path):
                db_path = path
                print(f"Found database at: {db_path}")
                break

        if db_path is None:
            # List all files in the current directory to find the database
            print("Searching for database file...")
            for root, dirs, files in os.walk(os.path.dirname(os.path.abspath(__file__))):
                for file in files:
                    if file.endswith('.db'):
                        db_path = os.path.join(root, file)
                        print(f"Found database at: {db_path}")
                        break
                if db_path:
                    break

        if db_path is None:
            raise FileNotFoundError("Could not find the database file.")

        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if the rejection_reason column exists
        cursor.execute("PRAGMA table_info(doctor)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]

        # Add the rejection_reason column if it doesn't exist
        if 'rejection_reason' not in column_names:
            print("Adding rejection_reason column to doctor table...")
            cursor.execute("ALTER TABLE doctor ADD COLUMN rejection_reason TEXT")
        else:
            print("rejection_reason column already exists.")

        # Add the verified_at column if it doesn't exist
        if 'verified_at' not in column_names:
            print("Adding verified_at column to doctor table...")
            cursor.execute("ALTER TABLE doctor ADD COLUMN verified_at TIMESTAMP")
        else:
            print("verified_at column already exists.")

        # Commit the changes
        conn.commit()
        conn.close()

        print("Database updated successfully!")

if __name__ == "__main__":
    update_database()
