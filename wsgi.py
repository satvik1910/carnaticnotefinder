"""
WSGI config for RagaNoteFinder.

This module contains the WSGI application used by the application server.
"""

from app import app as application

if __name__ == "__main__":
    application.run()
