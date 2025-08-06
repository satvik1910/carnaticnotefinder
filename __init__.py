# This file makes the directory a Python package
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5002)
