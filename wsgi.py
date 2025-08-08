"""
WSGI config for RagaNoteFinder.

This module contains the WSGI application used by the application server.
"""

import os
from app import create_app
from config import Config

# Create application instance
application = create_app(Config())

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    application.run(host='0.0.0.0', port=port)
