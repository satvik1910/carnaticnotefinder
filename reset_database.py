import os
import sys
from sqlalchemy import create_engine, MetaData, Table, text

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def reset_database():
    print("Resetting the database...")
    
    # Import app after setting up the path
    from app import create_app, db
    
    # Create app with test config
    app = create_app()
    
    with app.app_context():
        # Get the database URI
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        db_path = db_uri.replace('sqlite:///', '')
        
        print(f"Database path: {db_path}")
        
        # Close all connections
        db.session.close()
        
        # Drop all tables
        print("Dropping all tables...")
        db.drop_all()
        
        # Create all tables
        print("Creating all tables...")
        db.create_all()
        
        # Create admin user
        from app.models import User
        from werkzeug.security import generate_password_hash
        
        admin = User(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('admin123'),
            is_admin=True
        )
        
        db.session.add(admin)
        db.session.commit()
        
        print("Database reset complete!")
        print(f"Admin user created with username: admin, password: admin123")

if __name__ == '__main__':
    reset_database()
