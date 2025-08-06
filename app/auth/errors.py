from flask import jsonify
from werkzeug.http import HTTP_STATUS_CODES

def error_response(status_code, message=None):
    """Create a standard error response."""
    payload = {'error': HTTP_STATUS_CODES.get(status_code, 'Unknown error')}
    if message:
        payload['message'] = message
    response = jsonify(payload)
    response.status_code = status_code
    return response

def bad_request(message):
    """400 Bad Request"""
    return error_response(400, message)

def unauthorized(message='Please authenticate to access this resource'):
    """401 Unauthorized"""
    return error_response(401, message)

def forbidden(message='You do not have permission to access this resource'):
    """403 Forbidden"""
    return error_response(403, message)

def not_found(message='The requested resource was not found'):
    """404 Not Found"""
    return error_response(404, message)
