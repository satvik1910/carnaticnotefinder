from flask import Blueprint

# Create main blueprint
bp = Blueprint('main', __name__, template_folder='templates')

# Import routes after creating the blueprint to avoid circular imports
from . import routes  # This imports the routes after the blueprint is created
