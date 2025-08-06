from app import create_app, db
from app.models import User, Analysis, Note, Favorite

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 
        'User': User, 
        'Analysis': Analysis, 
        'Note': Note, 
        'Favorite': Favorite
    }
