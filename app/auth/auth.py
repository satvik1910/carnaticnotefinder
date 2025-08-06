from flask import g, jsonify, request
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth
from ..models import User
from . import bp as auth_bp
from .errors import unauthorized, forbidden

basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth(scheme='Bearer')

@basic_auth.verify_password
def verify_password(email, password):
    """Verify user credentials for basic auth."""
    if email == '':
        return False
    
    user = User.query.filter_by(email=email).first()
    if not user:
        return False
    
    g.current_user = user
    return user.verify_password(password)

@basic_auth.error_handler
def basic_auth_error():
    """Handle basic auth errors."""
    return unauthorized('Invalid credentials')

@token_auth.verify_token
def verify_token(token):
    """Verify a token for token-based authentication."""
    if not token:
        return False
    
    # Check if the token is valid and get the user
    user = User.verify_auth_token(token)
    if not user:
        return False
    
    g.current_user = user
    return True

@token_auth.error_handler
def token_auth_error():
    """Handle token auth errors."""
    return unauthorized('Invalid token')

@auth_bp.before_request
def before_request():
    """Handle authentication before each request."""
    # Skip authentication for login and registration pages
    if request.endpoint in ['auth.login', 'auth.register']:
        return
        
    # Require token authentication for other endpoints
    token_auth.login_required()
    
    if not g.current_user.is_anonymous and not g.current_user.is_active:
        return forbidden('Account is disabled')

@auth_bp.route('/tokens', methods=['POST'])
@basic_auth.login_required
def get_token():
    """Get an authentication token."""
    if g.current_user.is_anonymous or g.token_used:
        return unauthorized('Invalid credentials')
    
    # Generate a new token
    token = g.current_user.get_auth_token()
    
    # Return the token and its expiration time
    return jsonify({
        'token': token,
        'expires_in': 3600,  # 1 hour
        'user': g.current_user.to_dict()
    })

@auth_bp.route('/tokens', methods=['DELETE'])
@token_auth.login_required
def revoke_token():
    """Revoke the current authentication token."""
    g.current_user.revoke_token()
    db.session.commit()
    return '', 204
