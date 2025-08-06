import os
from datetime import timedelta

class Config:
    # App
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-123'
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    TEMP_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Audio processing
    ALLOWED_AUDIO_EXTENSIONS = {'wav', 'mp3', 'ogg', 'flac', 'm4a'}
    
    # OAuth Configuration
    GOOGLE_CLIENT_ID = "395707312620-i6nq9lirn82gv31hjqt1fi3qqq3nsrf4.apps.googleusercontent.com"
    GOOGLE_CLIENT_SECRET = "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"
    
    # OAuth settings
    OAUTH_CREDENTIALS = {
        'google': {
            'client_id': GOOGLE_CLIENT_ID,
            'client_secret': GOOGLE_CLIENT_SECRET,
            'authorize_url': 'https://accounts.google.com/o/oauth2/v2/auth',
            'token_url': 'https://oauth2.googleapis.com/token',
            'userinfo': {
                'url': 'https://www.googleapis.com/oauth2/v3/userinfo',
                'email': lambda json: json['email'],
                'username': lambda json: json.get('name', '').replace(' ', '_').lower(),
                'name': lambda json: json.get('name', ''),
                'picture': lambda json: json.get('picture', '')
            },
            'scopes': ['openid', 'email', 'profile'],
            'redirect_uris': [
                'http://localhost:5002/auth/login/google/authorized',
                'http://127.0.0.1:5002/auth/login/google/authorized',
                'http://localhost:5002/authorized',
                'http://127.0.0.1:5002/authorized'
            ],
            'authorize_params': {
                'access_type': 'offline',
                'prompt': 'consent',
                'include_granted_scopes': 'true'
            },
            'token_placement': 'header',
            'client_kwargs': {
                'scope': 'openid email profile',
                'token_endpoint_auth_method': 'client_secret_basic',
                'jwks_uri': 'https://www.googleapis.com/oauth2/v3/certs'
            },
            'server_metadata_url': 'https://accounts.google.com/.well-known/openid-configuration'
        }
    }
    
    # Carnatic music settings
    CARNATIC_NOTES = ["Sa", "Ri1", "Ri2", "Ga2", "Ga3", "Ma1", "Ma2", "Pa", "Da1", "Da2", "Ni2", "Ni3"]
    
    # Shruthi (base note) to frequency mapping
    SHRUTHI_FREQUENCIES = {
        'C': 261.63,    # Middle C
        'C#': 277.18,   # C#/D♭
        'D': 293.66,    # D
        'D#': 311.13,   # D#/E♭
        'E': 329.63,    # E
        'F': 349.23,    # F
        'F#': 369.99,   # F#/G♭
        'G': 392.00,    # G
        'G#': 415.30,   # G#/A♭
        'A': 440.00,    # A4 (standard tuning)
        'A#': 466.16,   # A#/B♭
        'B': 493.88     # B
    }
    
    # Default settings
    DEFAULT_SHRUTHI = 'C#'
    DEFAULT_START_TIME = 0
    DEFAULT_END_TIME = 10
    
    # Analysis settings
    SAMPLE_RATE = 44100
    FRAME_LENGTH = 2048
    HOP_LENGTH = 512
    CONFIDENCE_THRESHOLD = 0.7
    
    # Logging configuration
    LOG_LEVEL = 'DEBUG'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = 'app.log'
    SHRUTHI_THRESHOLD = 0.4
