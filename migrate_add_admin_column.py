"""
Migration script to add is_admin column to User table.
Run this script once to update your existing database.
"""
from ChatbotWebsite import create_app, db
from ChatbotWebsite.models import User
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
        
        # Check if column already exists
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Try to query the is_admin column
            cursor.execute("SELECT is_admin FROM user LIMIT 1")
            print("Column 'is_admin' already exists in the database.")
            conn.close()
            return
        except sqlite3.OperationalError:
            # Column doesn't exist, add it
            print("Adding 'is_admin' column to 'user' table...")
            try:
                cursor.execute("ALTER TABLE user ADD COLUMN is_admin BOOLEAN DEFAULT 0")
                conn.commit()
                print("Successfully added 'is_admin' column!")
                
                # Set default value for existing users
                cursor.execute("UPDATE user SET is_admin = 0 WHERE is_admin IS NULL")
                conn.commit()
                print("Set default value for existing users.")
                
            except Exception as e:
                print(f"Error adding column: {e}")
                conn.rollback()
            finally:
                conn.close()

if __name__ == '__main__':
    print("Starting database migration...")
    migrate_database()
    print("Migration completed!")

