import os
import sys

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import after setting up the path
from app import create_app, db
from app.models import User, Analysis, Note, Favorite

# Apply configuration overrides
try:
    from config_override import ConfigOverride
except ImportError:
    pass

def init_db():
    print("Initializing database...")
    app = create_app()
    
    with app.app_context():
        # Get the database URI from the app config
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        db_path = db_uri.replace('sqlite:///', '')
        
        print(f"Using database: {db_path}")
        
        # Remove existing database file if it exists
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
                print(f"Removed existing database: {db_path}")
            except PermissionError as e:
                print(f"Warning: Could not remove {db_path}: {e}")
                print("Trying to continue with existing database...")
        
        # Create all database tables
        db.create_all()
        print("Created new database with all tables.")
        
        # Create an admin user if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Created admin user.")
        
        print("Database initialization complete!")

if __name__ == '__main__':
    init_db()
