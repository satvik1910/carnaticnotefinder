import os
import sys

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def initialize_database():
    print("Initializing database...")
    from app import create_app, db
    from app.models import User
    from werkzeug.security import generate_password_hash
    
    app = create_app()
    
    with app.app_context():
        # Create all database tables
        print("Creating database tables...")
        db.create_all()
        
        # Create admin user if it doesn't exist
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("Creating admin user...")
            admin = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin user created with username: admin, password: admin123")
        
        print("Database initialization complete!")
        return app

def start_application():
    print("Starting RagaNoteFinder application...")
    app = initialize_database()
    
    # Run the application
    host = '0.0.0.0'  # Listen on all network interfaces
    port = 5002
    
    print(f"\nApplication is running at http://{host}:{port}/")
    print("Press Ctrl+C to stop the server\n")
    
    # Set debug to False to prevent auto-reloader which can cause issues
    app.run(host=host, port=port, debug=False)

if __name__ == '__main__':
    start_application()
