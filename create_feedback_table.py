"""
Simple script to create Feedback table in the database.
This script directly creates the table without importing the full Flask app.
"""
import sqlite3
import os

# Database path
db_path = os.path.join(os.path.dirname(__file__), 'instance', 'users.db')

# If database doesn't exist in instance folder, try root
if not os.path.exists(db_path):
    db_path = os.path.join(os.path.dirname(__file__), 'users.db')

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    print("Please make sure your database exists first.")
    exit(1)

print(f"Connecting to database at: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check if Feedback table already exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='feedback'")
    result = cursor.fetchone()
    
    if result:
        print("Feedback table already exists. No migration needed.")
    else:
        print("Creating Feedback table...")
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
        print("Successfully created Feedback table!")
        
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
finally:
    conn.close()

print("Done!")

