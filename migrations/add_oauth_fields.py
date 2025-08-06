import os
import sys
from sqlalchemy import text

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app import create_app, db
from app.models import User

def upgrade():
    app = create_app()
    with app.app_context():
        # Check if the oauth_provider column exists
        with db.engine.connect() as conn:
            # Get all columns in the users table
            result = conn.execute(text("PRAGMA table_info(users)")).fetchall()
            columns = [row[1] for row in result]  # Column names are in the second position
            
            # Check if oauth_provider column exists
            if 'oauth_provider' not in columns:
                print("Adding OAuth columns to users table...")
                # Add the new columns
                conn.execute(text(
                    "ALTER TABLE users "
                    "ADD COLUMN oauth_provider VARCHAR(20)"
                ))
                conn.execute(text(
                    "ALTER TABLE users "
                    "ADD COLUMN oauth_id VARCHAR(100)"
                ))
                conn.execute(text(
                    "ALTER TABLE users "
                    "ADD COLUMN profile_pic VARCHAR(200)"
                ))
                conn.execute(text(
                    "ALTER TABLE users "
                    "ADD COLUMN name VARCHAR(100)"
                ))
                
                # Add index for oauth_id
                conn.execute(text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_oauth_id ON users (oauth_id) "
                    "WHERE oauth_id IS NOT NULL"
                ))
                conn.commit()
                print("Successfully added OAuth columns to users table.")
            else:
                print("OAuth columns already exist in users table.")

if __name__ == '__main__':
    upgrade()
