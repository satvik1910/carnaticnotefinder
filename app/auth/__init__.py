from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_user, logout_user, login_required, current_user, LoginManager
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import urlparse, urlunparse

from ..models import db, User
from .forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm
from ..email import send_password_reset_email
from .oauth import oauth, init_oauth, handle_google_authorized, get_google_auth_url

bp = Blueprint('auth', __name__)

@bp.before_app_request
def before_request():
    """Ensure the current_user is available to all templates."""
    from flask import g
    g.current_user = current_user

@bp.record_once
def setup_auth(state):
    """Setup authentication components."""
    # Initialize login manager
    login_manager = LoginManager()
    login_manager.init_app(state.app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Initialize OAuth
    init_oauth(state.app)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password', 'danger')
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('main.index')
        return redirect(next_page)
    
    # Generate Google OAuth URL for the login button
    google_auth_url = url_for('auth.google_login')
    return render_template('auth/login.html', 
                         form=form, 
                         title='Sign In',
                         google_auth_url=google_auth_url)

@bp.route('/login/google')
def google_login():
    """
    Initiate Google OAuth login.
    This will redirect the user to Google's OAuth consent screen.
    """
    try:
        # Store the next URL if provided
        next_url = request.args.get('next')
        if next_url:
            session['next'] = next_url
        
        # Get the authorization URL
        auth_url = get_google_auth_url()
        current_app.logger.debug(f"Redirecting to Google OAuth: {auth_url.location if hasattr(auth_url, 'location') else auth_url}")
        return auth_url
    except Exception as e:
        current_app.logger.error(f"Error in google_login: {str(e)}", exc_info=True)
        flash('Failed to initiate Google login. Please try again.', 'error')
        return redirect(url_for('auth.login'))

@bp.route('/login/google/authorized')
@bp.route('/authorized')  # Keep for backward compatibility
def google_authorized():
    """
    Handle the OAuth callback from Google.
    This is the URL that Google will redirect to after authentication.
    """
    current_app.logger.debug(f"OAuth callback received. Args: {request.args}")
    
    # Check for error in the OAuth response
    if 'error' in request.args:
        error = request.args.get('error')
        error_desc = request.args.get('error_description', 'No description provided')
        current_app.logger.error(f"OAuth error: {error} - {error_desc}")
        flash(f'Authentication failed: {error_desc}', 'danger')
        return redirect(url_for('auth.login'))
    
    # Handle the OAuth callback
    try:
        user_data = handle_google_authorized()
        if not user_data:
            flash('Failed to authenticate with Google. No user data received.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Check if user already exists
        user = User.get_by_oauth_id('google', user_data['oauth_id'])
        
        if user is None:
            # Create new user
            try:
                user = User.create_oauth_user(user_data)
                db.session.commit()
                flash('Account created successfully!', 'success')
            except Exception as e:
                current_app.logger.error(f'Error creating user: {str(e)}', exc_info=True)
                db.session.rollback()
                flash('An error occurred while creating your account. Please try again or contact support.', 'danger')
                return redirect(url_for('auth.login'))
        
        # Log the user in
        login_user(user)
        
        # Redirect to the next URL if it exists
        next_url = session.pop('next', None)
        if next_url and urlparse(next_url).netloc == '':
            return redirect(next_url)
        
        return redirect(url_for('main.dashboard'))
        
    except Exception as e:
        current_app.logger.error(f'Error in OAuth callback: {str(e)}', exc_info=True)
        flash('An unexpected error occurred during authentication. Please try again.', 'danger')
        return redirect(url_for('auth.login'))

@bp.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    try:
        logout_user()
        flash('You have been logged out successfully.', 'success')
    except Exception as e:
        current_app.logger.error(f'Error during logout: {str(e)}')
        flash('An error occurred during logout. Please try again.', 'danger')
    
    return redirect(url_for('main.index'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle new user registration."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if username or email already exists
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already in use. Please choose a different one.', 'danger')
            return redirect(url_for('auth.register'))
            
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered. Please use a different email or login.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Congratulations, you are now a registered user!', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form, title='Register')

@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    """Handle password reset requests."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        
        flash('Check your email for the instructions to reset your password', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password_request.html',
                         form=form,
                         title='Reset Password')

@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Handle password reset with token."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    user = User.verify_reset_password_token(token)
    if not user:
        flash('Invalid or expired reset token', 'warning')
        return redirect(url_for('main.index'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.password = form.password.data
        db.session.commit()
        
        flash('Your password has been reset.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', form=form, title='Reset Password')

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page."""
    from .forms import ProfileForm
    
    form = ProfileForm()
    if form.validate_on_submit():
        # Update user profile
        current_user.username = form.username.data
        current_user.email = form.email.data
        
        if form.new_password.data:
            current_user.password = form.new_password.data
        
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('auth.profile'))
    
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    
    return render_template('auth/profile.html', form=form, title='My Profile')
