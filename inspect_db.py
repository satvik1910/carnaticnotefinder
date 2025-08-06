import sqlite3
import os
from pprint import pprint

def inspect_database():
    db_path = 'app.db'  # Default SQLite database path
    
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return
    
    print(f"Inspecting database: {os.path.abspath(db_path)}")
    
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get the list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("\nTables in the database:")
        for table in tables:
            table_name = table[0]
            print(f"\nTable: {table_name}")
            
            # Get table info
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            print("\nColumns:")
            for col in columns:
                print(f"  {col[1]} ({col[2]}) - {'NULL' if col[3] else 'NOT NULL'} - Default: {col[4]}")
            
            # Get indexes
            cursor.execute(f"PRAGMA index_list({table_name});")
            indexes = cursor.fetchall()
            
            if indexes:
                print("\nIndexes:")
                for idx in indexes:
                    idx_name = idx[1]
                    cursor.execute(f"PRAGMA index_info({idx_name});")
                    idx_columns = cursor.fetchall()
                    col_names = [col[2] for col in idx_columns]
                    print(f"  {idx_name}: {', '.join(col_names)}")
        
        # Check for any pending migrations
        print("\nChecking for pending migrations...")
        try:
            from app import create_app
            from flask_migrate import upgrade
            
            app = create_app()
            with app.app_context():
                print("Applying any pending migrations...")
                upgrade()
                print("Migrations applied successfully!")
        except Exception as e:
            print(f"Error applying migrations: {e}")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    inspect_database()
