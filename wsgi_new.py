"""
WSGI config for RagaNoteFinder.

This module contains the WSGI application used by the application server.
"""

import os
import sys

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(__file__))

# Import the Flask app
from app import app as application

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    application.run(host='0.0.0.0', port=port)
