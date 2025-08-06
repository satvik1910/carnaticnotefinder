import os
from werkzeug.utils import secure_filename
from flask import current_app

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def save_file(file, folder=None, filename=None):
    """
    Save an uploaded file to the server.
    
    Args:
        file: The file object to save
        folder: Subfolder within UPLOAD_FOLDER to save the file
        filename: Custom filename (without extension)
    
    Returns:
        str: The path to the saved file relative to UPLOAD_FOLDER
    """
    if not file or file.filename == '':
        return None
    
    # Ensure the filename is safe
    original_filename = secure_filename(file.filename)
    file_ext = os.path.splitext(original_filename)[1].lower()
    
    # Generate a secure filename if not provided
    if not filename:
        from datetime import datetime
        from uuid import uuid4
        filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"
    
    # Create the full filename with extension
    secure_filename = f"{filename}{file_ext}"
    
    # Create the upload path
    if folder:
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], folder)
    else:
        upload_dir = current_app.config['UPLOAD_FOLDER']
    
    # Ensure the upload directory exists
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save the file
    filepath = os.path.join(upload_dir, secure_filename)
    file.save(filepath)
    
    # Return the relative path
    if folder:
        return os.path.join(folder, secure_filename)
    return secure_filename

def delete_file(filepath):
    """
    Delete a file from the server.
    
    Args:
        filepath: Path to the file relative to UPLOAD_FOLDER
    
    Returns:
        bool: True if the file was deleted, False otherwise
    """
    if not filepath:
        return False
    
    full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filepath)
    
    try:
        if os.path.isfile(full_path):
            os.remove(full_path)
            return True
    except Exception as e:
        current_app.logger.error(f"Error deleting file {filepath}: {str(e)}")
    
    return False

def format_duration(seconds):
    """Format a duration in seconds to HH:MM:SS format."""
    try:
        seconds = float(seconds)
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:06.3f}"
        else:
            return f"{minutes}:{seconds:06.3f}"
    except (ValueError, TypeError):
        return "0:00.000"

def get_file_size(filepath):
    """Get the size of a file in a human-readable format."""
    try:
        size_bytes = os.path.getsize(filepath)
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
            
        return f"{size_bytes:.1f} PB"
    except (OSError, TypeError):
        return "Unknown"

def is_safe_url(target):
    """Check if a URL is safe for redirection."""
    from urllib.parse import urlparse, urljoin
    from flask import request
    
    if not target:
        return False
    
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    
    return (test_url.scheme in ('http', 'https') and 
            ref_url.netloc == test_url.netloc)

def paginate(query, page, per_page=20, error_out=True):
    """Paginate a SQLAlchemy query."""
    return query.paginate(page=page, per_page=per_page, error_out=error_out)

def get_pagination_info(pagination, endpoint, **kwargs):
    """Generate pagination information for templates."""
    return {
        'has_prev': pagination.has_prev,
        'has_next': pagination.has_next,
        'prev_num': pagination.prev_num,
        'next_num': pagination.next_num,
        'page': pagination.page,
        'pages': pagination.pages,
        'per_page': pagination.per_page,
        'total': pagination.total,
        'iter_pages': pagination.iter_pages(),
        'endpoint': endpoint,
        'kwargs': kwargs
    }
