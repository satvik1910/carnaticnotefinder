import os
import sys
from sqlalchemy import text

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app import create_app, db

def fix_oauth_columns():
    print("Fixing OAuth columns in the database...")
    app = create_app()
    
    with app.app_context():
        # Get the database connection
        with db.engine.connect() as conn:
            # Check if the users table exists
            result = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            ).fetchone()
            
            if not result:
                print("Error: 'users' table not found in the database.")
                return
            
            # Check if oauth_provider column exists
            result = conn.execute(
                text("PRAGMA table_info(users)")
            ).fetchall()
            
            # Get all column names
            columns = [row[1] for row in result]
            
            # Add missing OAuth columns if they don't exist
            if 'oauth_provider' not in columns:
                print("Adding OAuth columns to users table...")
                try:
                    # Add the new columns one by one
                    conn.execute(text("ALTER TABLE users ADD COLUMN oauth_provider VARCHAR(20)"))
                    print("Added column: oauth_provider")
                    
                    conn.execute(text("ALTER TABLE users ADD COLUMN oauth_id VARCHAR(100)"))
                    print("Added column: oauth_id")
                    
                    conn.execute(text("ALTER TABLE users ADD COLUMN profile_pic VARCHAR(200)"))
                    print("Added column: profile_pic")
                    
                    conn.execute(text("ALTER TABLE users ADD COLUMN name VARCHAR(100)"))
                    print("Added column: name")
                    
                    # Add index for oauth_id
                    conn.execute(text(
                        "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_oauth_id ON users (oauth_id) "
                        "WHERE oauth_id IS NOT NULL"
                    ))
                    print("Created index: ix_users_oauth_id")
                    
                    # Commit the changes
                    conn.commit()
                    print("Successfully added OAuth columns to users table.")
                    
                except Exception as e:
                    print(f"Error adding OAuth columns: {e}")
                    conn.rollback()
            else:
                print("OAuth columns already exist in the users table.")

if __name__ == '__main__':
    fix_oauth_columns()
