from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db
from app import login_manager

class User(UserMixin, db.Model):
    """User account model."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=True)  # Made nullable for OAuth users
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=True)  # Nullable for OAuth users
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    
    # OAuth fields
    oauth_provider = db.Column(db.String(20), nullable=True)
    oauth_id = db.Column(db.String(100), nullable=True, unique=True)
    profile_pic = db.Column(db.String(200), nullable=True)
    name = db.Column(db.String(100), nullable=True)  # Full name from OAuth
    
    # Methods for OAuth
    @classmethod
    def create_oauth_user(cls, oauth_data):
        """Create a new user from OAuth data."""
        user = cls(
            email=oauth_data['email'],
            username=oauth_data['username'],
            name=oauth_data.get('name', ''),
            oauth_provider=oauth_data['oauth_provider'],
            oauth_id=oauth_data['oauth_id'],
            profile_pic=oauth_data.get('profile_pic', ''),
            is_active=True
        )
        db.session.add(user)
        return user
    
    @classmethod
    def get_by_oauth_id(cls, provider, oauth_id):
        """Get a user by OAuth provider and ID."""
        return cls.query.filter_by(oauth_provider=provider, oauth_id=oauth_id).first()
    
    @property
    def is_oauth_user(self):
        """Check if this is an OAuth-authenticated user."""
        return self.oauth_provider is not None
    
    # Relationships
    analyses = db.relationship('Analysis', backref='author', lazy='dynamic')
    favorites = db.relationship('Favorite', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        """Create hashed password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check hashed password."""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Analysis(db.Model):
    """Analysis model for storing analysis results."""
    __tablename__ = 'analyses'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    video_url = db.Column(db.String(500), nullable=False)
    start_time = db.Column(db.Float, nullable=False)
    end_time = db.Column(db.Float, nullable=False)
    duration = db.Column(db.Float, nullable=False)
    shruthi = db.Column(db.String(10), default='C#', nullable=False)  # Base pitch for analysis
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    is_public = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    notes = db.relationship('Note', backref='analysis', lazy='dynamic', cascade='all, delete-orphan')
    favorites = db.relationship('Favorite', backref='analysis', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Analysis {self.title}>'

class Note(db.Model):
    """Note model for storing detected notes."""
    __tablename__ = 'notes'
    
    id = db.Column(db.Integer, primary_key=True)
    note_name = db.Column(db.String(20), nullable=False)
    frequency = db.Column(db.Float, nullable=False)
    start_time = db.Column(db.Float, nullable=False)
    duration = db.Column(db.Float, nullable=False)
    confidence = db.Column(db.Float, nullable=True)
    
    # Foreign Keys
    analysis_id = db.Column(db.Integer, db.ForeignKey('analyses.id'), nullable=False)
    
    def __repr__(self):
        return f'<Note {self.note_name} at {self.start_time:.2f}s>'

class Favorite(db.Model):
    """Favorite analyses for users."""
    __tablename__ = 'favorites'
    
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    analysis_id = db.Column(db.Integer, db.ForeignKey('analyses.id'), nullable=False)
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('user_id', 'analysis_id', name='_user_analysis_uc'),)
    
    def __repr__(self):
        return f'<Favorite user_id={self.user_id} analysis_id={self.analysis_id}>'

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))
