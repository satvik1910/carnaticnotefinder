from flask import url_for, redirect, session, current_app, flash, request
from authlib.integrations.flask_client import OAuth
from urllib.parse import urlencode, urlparse, urlunparse
from config import Config

oauth = OAuth()

def init_oauth(app):
    oauth.init_app(app)
    
    # Get OAuth config
    google_config = app.config['OAUTH_CREDENTIALS']['google']
    
    # Log the OAuth configuration for debugging
    app.logger.debug(f"Initializing OAuth with client ID: {google_config['client_id']}")
    app.logger.debug(f"Using redirect URIs: {google_config['redirect_uris']}")
    
    # Register Google OAuth client
    oauth.register(
        name='google',
        client_id=google_config['client_id'],
        client_secret=google_config['client_secret'],
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': ' '.join(google_config['scopes'])
        },
        # Use the first redirect URI as the default
        redirect_uri=google_config['redirect_uris'][0] if google_config.get('redirect_uris') else None,
        # Add authorize params
        authorize_params={
            'access_type': 'offline',
            'prompt': 'consent',
            'include_granted_scopes': 'true'
        }
    )

def get_google_auth_url():
    """Generate the Google OAuth authorization URL."""
    # Get the redirect URI from the first configured URI
    redirect_uri = current_app.config['OAUTH_CREDENTIALS']['google']['redirect_uris'][0]
    
    # Generate the authorization URL
    auth_url = oauth.google.authorize_redirect(redirect_uri)
    
    # Log the auth URL for debugging
    current_app.logger.debug(f"Generated auth URL: {auth_url.location if hasattr(auth_url, 'location') else auth_url}")
    return auth_url

def handle_google_authorized():
    """Handle the OAuth callback from Google."""
    try:
        # Log the request args for debugging (without sensitive data)
        safe_args = {k: v for k, v in request.args.items() if k not in ('state', 'code')}
        current_app.logger.debug(f"OAuth callback received. Args: {safe_args}")
        
        # Check for error in the OAuth response
        if 'error' in request.args:
            error = request.args.get('error')
            error_desc = request.args.get('error_description', 'No description provided')
            current_app.logger.error(f"OAuth error: {error} - {error_desc}")
            flash(f'Authentication failed: {error_desc}', 'error')
            return None
            
        # Get the token and user info
        current_app.logger.debug("Attempting to get access token...")
        try:
            token = oauth.google.authorize_access_token()
            current_app.logger.debug(f"OAuth token received. Token keys: {list(token.keys()) if token else 'None'}")
        except Exception as e:
            current_app.logger.error(f"Error getting access token: {str(e)}", exc_info=True)
            flash('Failed to authenticate with Google: Could not obtain access token', 'error')
            return None
        
        if not token:
            current_app.logger.error("No access token received from Google")
            flash('Failed to authenticate with Google: No access token received', 'error')
            return None
            
        # Get user info
        try:
            current_app.logger.debug("Attempting to fetch user info...")
            
            # First try to get user info from the userinfo endpoint
            try:
                userinfo = oauth.google.userinfo()
                current_app.logger.debug(f"Fetched user info from userinfo endpoint: {userinfo}")
            except Exception as e:
                current_app.logger.error(f"Failed to fetch user info from userinfo endpoint: {str(e)}")
                # If that fails, try to parse the ID token directly (without nonce for now)
                try:
                    if 'id_token' in token:
                        # Parse the ID token without nonce verification for now
                        from authlib.jose import jwt
                        from authlib.oidc.core import CodeIDToken
                        
                        id_token = token.get('id_token')
                        if id_token:
                            # Get the keys from the JWKS endpoint
                            jwk_set = oauth.google.load_server_metadata()
                            claims = jwt.decode(
                                id_token,
                                key=jwk_set['jwks'],
                                claims_cls=CodeIDToken,
                                claims_options={
                                    'iss': {'values': ['https://accounts.google.com']},
                                    'aud': {'values': [current_app.config['GOOGLE_CLIENT_ID']]}
                                }
                            )
                            claims.validate()
                            userinfo = claims
                            current_app.logger.debug("Successfully parsed ID token")
                        else:
                            raise ValueError("No ID token in the response")
                    else:
                        raise ValueError("No ID token in the response")
                except Exception as e2:
                    current_app.logger.error(f"Failed to parse ID token: {str(e2)}")
                    flash('Failed to process authentication response from Google', 'error')
                    return None
            
            # Log the received user info (without sensitive data)
            safe_user_info = {k: v for k, v in userinfo.items() if k not in ('sub', 'at_hash')}
            current_app.logger.debug(f"User info from Google: {safe_user_info}")
            
            # Extract user data
            user_data = {
                'oauth_provider': 'google',
                'oauth_id': userinfo.get('sub'),
                'email': userinfo.get('email'),
                'name': userinfo.get('name', ''),
                'username': userinfo.get('name', '').replace(' ', '_').lower(),
                'profile_pic': userinfo.get('picture')
            }
            
            if not user_data.get('email'):
                current_app.logger.error(f"No email in user data. User data: {user_data}")
                flash('Failed to authenticate: No email address provided by Google', 'error')
                return None
                
            if not user_data.get('oauth_id'):
                current_app.logger.error(f"No OAuth ID in user data. User data: {user_data}")
                flash('Failed to authenticate: No user ID provided by Google', 'error')
                return None
                
            current_app.logger.debug(f"Successfully processed user data for {user_data['email']}")
            return user_data
            
        except Exception as e:
            current_app.logger.error(f"Error processing user info: {str(e)}", exc_info=True)
            flash('Failed to process user information from Google', 'error')
            return None
            
    except Exception as e:
        current_app.logger.error(f"Unexpected error in OAuth callback: {str(e)}", exc_info=True)
        flash('An unexpected error occurred during authentication. Please try again.', 'error')
        return None
