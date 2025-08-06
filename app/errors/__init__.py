from flask import jsonify, render_template, request, redirect, url_for, flash
from werkzeug.http import HTTP_STATUS_CODES
from sqlalchemy.exc import IntegrityError
from flask_wtf.csrf import CSRFError

def error_response(status_code, message=None):
    """Create a standardized error response."""
    payload = {
        'error': HTTP_STATUS_CODES.get(status_code, 'Unknown error'),
        'status': 'error',
        'code': status_code
    }
    
    if message:
        payload['message'] = message
    
    response = jsonify(payload)
    response.status_code = status_code
    return response

def bad_request(message):
    """Return a 400 Bad Request error."""
    return error_response(400, message)

def unauthorized(message):
    """Return a 401 Unauthorized error."""
    return error_response(401, message)

def forbidden(message):
    """Return a 403 Forbidden error."""
    return error_response(403, message)

def not_found(message):
    """Return a 404 Not Found error."""
    return error_response(404, message)

def internal_error(message=None):
    """Return a 500 Internal Server Error."""
    return error_response(500, message or 'An unexpected error has occurred.')

def validation_error(field, message):
    """Return a 422 Unprocessable Entity error for validation failures."""
    return error_response(422, {field: message})

# Register error handlers
def register_error_handlers(app):
    """Register error handlers for the application."""
    @app.errorhandler(400)
    def bad_request_error(error):
        if request.is_json or request.path.startswith('/api/'):
            return error_response(400, str(error.description) if hasattr(error, 'description') else 'Bad request')
        return render_template('errors/400.html', error=error), 400
    
    @app.errorhandler(401)
    def unauthorized_error(error):
        if request.is_json or request.path.startswith('/api/'):
            return error_response(401, 'Please authenticate to access this resource')
        return render_template('errors/401.html', error=error), 401
    
    @app.errorhandler(403)
    def forbidden_error(error):
        if request.is_json or request.path.startswith('/api/'):
            return error_response(403, 'You do not have permission to access this resource')
        return render_template('errors/403.html', error=error), 403
    
    @app.errorhandler(404)
    def not_found_error(error):
        if request.is_json or request.path.startswith('/api/'):
            return error_response(404, 'The requested resource was not found')
        return render_template('errors/404.html', error=error), 404
    
    @app.errorhandler(405)
    def method_not_allowed_error(error):
        if request.is_json or request.path.startswith('/api/'):
            return error_response(405, 'The method is not allowed for the requested URL')
        return render_template('errors/405.html', error=error), 405
    
    @app.errorhandler(413)
    def request_entity_too_large_error(error):
        if request.is_json or request.path.startswith('/api/'):
            return error_response(413, 'The request is larger than the server is willing or able to process')
        return render_template('errors/413.html', error=error), 413
    
    @app.errorhandler(429)
    def too_many_requests_error(error):
        if request.is_json or request.path.startswith('/api/'):
            return error_response(429, 'You have exceeded the rate limit for this endpoint')
        return render_template('errors/429.html', error=error), 429
    
    @app.errorhandler(500)
    def internal_error_error(error):
        if request.is_json or request.path.startswith('/api/'):
            return error_response(500, 'An internal server error occurred')
        return render_template('errors/500.html', error=error), 500
    
    @app.errorhandler(503)
    def service_unavailable_error(error):
        if request.is_json or request.path.startswith('/api/'):
            return error_response(503, 'The server is temporarily unable to handle the request')
        return render_template('errors/503.html', error=error), 503
    
    # Handle SQLAlchemy database errors
    @app.errorhandler(IntegrityError)
    def handle_integrity_error(error):
        db.session.rollback()
        if request.is_json or request.path.startswith('/api/'):
            return error_response(400, 'Database integrity error occurred')
        flash('A database error occurred. Please try again.', 'danger')
        return redirect(request.referrer or url_for('main.index'))
    
    # Handle CSRF token errors
    @app.errorhandler(CSRFError)
    def handle_csrf_error(error):
        # Log detailed information about the CSRF error
        csrf_token = request.form.get('csrf_token', 'No CSRF token in form data')
        cookies = request.cookies
        headers = dict(request.headers)
        
        # Log the error details
        app.logger.error(f'CSRF Error: {str(error)}')
        app.logger.error(f'CSRF Token in form: {csrf_token}')
        app.logger.error(f'Request Path: {request.path}')
        app.logger.error(f'Request Method: {request.method}')
        app.logger.error(f'Request Headers: {headers}')
        app.logger.error(f'Request Cookies: {cookies}')
        
        if request.is_json or request.path.startswith('/api/'):
            return error_response(400, 'The CSRF token is missing or invalid')
            
        # For form submissions, redirect back with a flash message
        if request.method == 'POST':
            flash('The form has expired or the CSRF token is invalid. Please try again.', 'danger')
            return redirect(request.referrer or url_for('main.index'))
            
        # For GET requests, show a 400 error page
        return render_template('errors/400.html', 
                            error=error,
                            message='The form has expired or the CSRF token is invalid. Please try again.'), 400
    
    # Handle all other exceptions
    @app.errorhandler(Exception)
    def handle_exception(error):
        # Log the error for debugging
        app.logger.error(f'Unhandled exception: {str(error)}', exc_info=True)
        
        if request.is_json or request.path.startswith('/api/'):
            return error_response(500, 'An unexpected error occurred')
        
        # For template-based responses, show a generic error page
        return render_template('errors/500.html', error=error), 500
