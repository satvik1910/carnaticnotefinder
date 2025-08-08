"""
WSGI config for RagaNoteFinder.

This module contains the WSGI application used by the application server.
"""

from app import create_app

application = create_app()

if __name__ == "__main__":
    application.run()
