from app import create_app
from app.models import User, Analysis, Note, Favorite
import os

def reset_database():
    """Reset the database by dropping all tables and recreating them."""
    app = create_app()
    
    with app.app_context():
        from app import db  # Import db here to ensure it's within app context
        
        # Drop all tables
        db.drop_all()
        print("Dropped all tables.")
        
        # Create all tables based on current models
        db.create_all()
        print("Created all tables.")
        
        # Recreate admin user if in development
        if app.config.get('FLASK_ENV') == 'development':
            try:
                admin = User(
                    username='admin',
                    email='admin@example.com',
                    is_admin=True
                )
                admin.set_password('admin')
                db.session.add(admin)
                db.session.commit()
                print("Recreated admin user.")
            except Exception as e:
                print(f"Error creating admin user: {e}")
                db.session.rollback()

if __name__ == '__main__':
    reset_database()
