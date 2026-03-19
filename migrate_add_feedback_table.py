"""
Migration script to add Feedback table to the database.
Run this script once to create the Feedback table.
"""
from ChatbotWebsite import create_app, db
from ChatbotWebsite.models import Feedback
import sqlite3
import os

app = create_app()

def migrate_database():
    with app.app_context():
        # Get the database path from config
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///users.db')
        
        # Extract path from SQLite URI
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri.replace('sqlite:///', '')
            # If it's a relative path, make it absolute
            if not os.path.isabs(db_path):
                # Check if it's in instance folder
                instance_path = os.path.join(os.path.dirname(__file__), 'instance', 'users.db')
                if os.path.exists(instance_path):
                    db_path = instance_path
                else:
                    db_path = os.path.join(os.path.dirname(__file__), db_path)
        else:
            print(f"Unsupported database URI: {db_uri}")
            print("Please run this migration manually for your database type.")
            return
        
        # Check if database exists
        if not os.path.exists(db_path):
            print(f"Database not found at {db_path}. Creating new database with all tables...")
            db.create_all()
            print("Database created successfully!")
            return
        
        print(f"Migrating database at: {db_path}")
        
        # Check if Feedback table already exists
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Try to query the Feedback table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='feedback'")
            result = cursor.fetchone()
            if result:
                print("Feedback table already exists in the database.")
                conn.close()
                return
        except Exception as e:
            print(f"Error checking for table: {e}")
        
        # Table doesn't exist, create it using SQLAlchemy
        print("Creating Feedback table...")
        try:
            db.create_all()
            print("Successfully created Feedback table!")
        except Exception as e:
            print(f"Error creating table: {e}")
            print("Trying alternative method...")
            # Alternative: Create table manually
            try:
                cursor.execute("""
                    CREATE TABLE feedback (
                        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME NOT NULL,
                        rating INTEGER NOT NULL,
                        notes VARCHAR(2000),
                        user_id INTEGER,
                        is_approved BOOLEAN NOT NULL DEFAULT 0,
                        is_published BOOLEAN NOT NULL DEFAULT 0,
                        FOREIGN KEY(user_id) REFERENCES user (id)
                    )
                """)
                conn.commit()
                print("Successfully created Feedback table using SQL!")
            except Exception as e2:
                print(f"Error creating table with SQL: {e2}")
        finally:
            conn.close()

if __name__ == '__main__':
    print("Starting database migration for Feedback table...")
    migrate_database()
    print("Migration completed!")

