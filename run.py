from app import create_app, db
from app.models import User, Analysis, Note, Favorite

def init_db():
    """Initialize the database."""
    app = create_app()
    with app.app_context():
        # Create database tables
        db.create_all()
        
        # Create admin user if it doesn't exist
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                is_admin=True
            )
            admin.set_password('admin')
            db.session.add(admin)
            db.session.commit()
            print("Created admin user with username 'admin' and password 'admin'")

if __name__ == '__main__':
    app = create_app()
    # Initialize the database
    init_db()
    # Run the application
    app.run(debug=True, port=5002)
