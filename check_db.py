from app import create_app, db
from app.models import Analysis
import sqlite3
import os

def check_database_schema():
    app = create_app()
    
    with app.app_context():
        # Get the database path from the app config
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        db_path = db_uri.replace('sqlite:///', '')
        print(f"Database URI from config: {db_uri}")
        print(f"Database path: {db_path}")
        
        # Check if database file exists
        if not os.path.exists(db_path):
            print("\nError: Database file does not exist!")
            # Try to find other database files
            print("\nSearching for other database files...")
            for root, dirs, files in os.walk('.'):
                for file in files:
                    if file.endswith('.db') or file.endswith('.sqlite'):
                        print(f"Found database file: {os.path.join(root, file)}")
            return
        
        # Connect to the database
        print(f"\nConnecting to database at: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Get all tables in the database
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print("\nTables in the database:")
            for table in tables:
                print(f"- {table[0]}")
            
            # Get table info for analyses
            print("\nColumns in 'analyses' table:")
            cursor.execute("PRAGMA table_info(analyses)")
            columns = cursor.fetchall()
            for col in columns:
                print(f"- {col[1]} ({col[2]})")
                
            # Check if shruthi column exists
            shruthi_exists = any(col[1] == 'shruthi' for col in columns)
            print(f"\n'shruthi' column exists: {shruthi_exists}")
            
            if not shruthi_exists:
                print("\nTo fix this, you need to:")
                print("1. Delete the database file:")
                print(f"   del " + db_path.replace('/', '\\'))
                print("2. Run the reset_db.py script:")
                print("   python reset_db.py")
            else:
                print("\nThe 'shruthi' column exists in the database.")
                print("The error might be due to one of these reasons:")
                print("1. The Flask application is not using this database file")
                print("2. There are multiple database files")
                print("3. The Flask application needs to be restarted")
                print("4. There's a caching issue")
                
                # Check for other database files
                print("\nSearching for other database files...")
                other_dbs = []
                for root, dirs, files in os.walk('.'):
                    for file in files:
                        if (file.endswith('.db') or file.endswith('.sqlite')) and file != os.path.basename(db_path):
                            full_path = os.path.join(root, file)
                            other_dbs.append(full_path)
                            print(f"Found other database file: {full_path}")
                
                if other_dbs:
                    print("\nOther database files found. These might be causing conflicts.")
                    print("You might want to delete these files or update your configuration.")
                
        except sqlite3.Error as e:
            print(f"\nError checking database: {e}")
            
        finally:
            conn.close()

if __name__ == '__main__':
    check_database_schema()
