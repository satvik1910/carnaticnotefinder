from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from authlib.integrations.flask_client import OAuth
from config import Config

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
csrf = CSRFProtect()
mail = Mail()
oauth = OAuth()

def create_app(config_class=Config):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    if isinstance(config_class, type):
        app.config.from_object(config_class())
    else:
        app.config.from_object(config_class)
    
    # Configure logging
    import logging
    from logging.handlers import RotatingFileHandler
    import os
    
    # Ensure the log directory exists
    log_dir = os.path.dirname(app.config['LOG_FILE'])
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Set the log level
    log_level = getattr(logging, app.config['LOG_LEVEL'].upper(), logging.INFO)
    app.logger.setLevel(log_level)
    
    # Create file handler for logging
    file_handler = RotatingFileHandler(
        app.config['LOG_FILE'],
        maxBytes=10240,
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(app.config['LOG_FORMAT']))
    file_handler.setLevel(log_level)
    
    # Add the handlers to the app
    if not app.debug:
        app.logger.addHandler(file_handler)
    
    app.logger.info('RagaNoteFinder startup')
    app.logger.info(f'Logging level: {logging.getLevelName(log_level)}')
    app.logger.info(f'Application root: {os.path.abspath(os.curdir)}')
    
    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    
    # Initialize login manager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    # Import User model for login manager
    from app.models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from app.main import bp as main_bp
    from app.auth import bp as auth_bp
    from app.api import bp as api_bp
    from app.analysis import bp as analysis_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(analysis_bp, url_prefix='/analysis')
    
    # Register error handlers
    from app.errors import register_error_handlers
    register_error_handlers(app)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Add context processor to make current year available in all templates
    @app.context_processor
    def inject_now():
        from datetime import datetime
        return {'now': datetime.utcnow()}
    
    # Initialize database with admin user if in development
    if app.config.get('FLASK_ENV') == 'development':
        try:
            from app.models import User
            with app.app_context():
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
        except Exception as e:
            app.logger.warning(f'Could not initialize admin user: {str(e)}')
    
    return app
