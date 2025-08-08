"""
Run the RagaNoteFinder application using Waitress WSGI server.
"""

import os
import sys
from pathlib import Path

# Add the root directory to the Python path
root_dir = str(Path(__file__).parent.absolute())
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from waitress import serve
from app import app

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting server on port {port}...")
    serve(app, host='0.0.0.0', port=port)
