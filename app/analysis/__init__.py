from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify, abort, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
from ..models import db, Analysis, Note, Favorite
from ..audio_utils import analyze_audio_segment
from ..tasks import analyze_audio_task
from ..utils import allowed_file

bp = Blueprint('analysis', __name__)

@bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_analysis():
    """Create a new analysis."""
    if request.method == 'POST':
        # Get form data
        title = request.form.get('title', 'Untitled Analysis')
        description = request.form.get('description', '')
        video_url = request.form.get('video_url', '')
        start_time = float(request.form.get('start_time', 0))
        end_time = float(request.form.get('end_time', 10))
        shruthi = request.form.get('shruthi', 'C#')
        is_public = 'is_public' in request.form
        
        # Create a new analysis record
        analysis = Analysis(
            user_id=current_user.id,
            title=title,
            description=description,
            video_url=video_url,
            start_time=start_time,
            end_time=end_time,
            shruthi=shruthi,
            is_public=is_public,
            status='queued'
        )
        
        # Handle file upload if provided
        if 'audio_file' in request.files:
            file = request.files['audio_file']
            if file and allowed_file(file.filename):
                # Generate a unique filename
                filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                
                # Ensure upload directory exists
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                
                # Save the file
                file.save(filepath)
                analysis.audio_path = filepath
        
        db.session.add(analysis)
        db.session.commit()
        
        # Start the analysis task in the background
        analyze_audio_task.delay(analysis.id)
        
        flash('Your analysis has been queued. You will be notified when it is complete!', 'info')
        return redirect(url_for('analysis.view_analysis', analysis_id=analysis.id))
    
    # For GET request, show the analysis form
    return render_template('analysis/new.html',
                         title='New Analysis',
                         default_shruthi='C#',
                         default_start=0,
                         default_end=10)

@bp.route('/<int:analysis_id>')
def view_analysis(analysis_id):
    """View an analysis and its results."""
    analysis = Analysis.query.get_or_404(analysis_id)
    
    # Check if the analysis is public or belongs to the current user
    if not analysis.is_public and (not current_user.is_authenticated or 
                                  current_user.id != analysis.user_id):
        flash('You do not have permission to view this analysis.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get all notes for this analysis
    notes = analysis.notes.order_by(Note.start_time).all()
    
    # Prepare data for visualization
    note_data = [{
        'time': note.start_time,
        'note': note.note_name,
        'duration': note.duration,
        'frequency': note.frequency
    } for note in notes]
    
    # Check if the current user has favorited this analysis
    is_favorited = False
    if current_user.is_authenticated:
        is_favorited = Favorite.query.filter_by(
            user_id=current_user.id,
            analysis_id=analysis.id
        ).first() is not None
    
    return render_template('analysis/view.html',
                         analysis=analysis,
                         notes=notes,
                         note_data=note_data,
                         is_favorited=is_favorited,
                         title=f'Analysis: {analysis.title}')

@bp.route('/<int:analysis_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_analysis(analysis_id):
    """Edit an existing analysis."""
    analysis = Analysis.query.get_or_404(analysis_id)
    
    # Check if the current user owns this analysis
    if current_user.id != analysis.user_id and not current_user.is_admin:
        flash('You do not have permission to edit this analysis.', 'danger')
        return redirect(url_for('analysis.view_analysis', analysis_id=analysis.id))
    
    if request.method == 'POST':
        # Update analysis with form data
        analysis.title = request.form.get('title', analysis.title)
        analysis.description = request.form.get('description', analysis.description)
        analysis.is_public = 'is_public' in request.form
        
        # Only allow changing these if the analysis hasn't started
        if analysis.status in ['queued', 'failed']:
            analysis.video_url = request.form.get('video_url', analysis.video_url)
            analysis.start_time = float(request.form.get('start_time', analysis.start_time))
            analysis.end_time = float(request.form.get('end_time', analysis.end_time))
            analysis.shruthi = request.form.get('shruthi', analysis.shruthi)
            
            # If the analysis failed, requeue it
            if analysis.status == 'failed':
                analysis.status = 'queued'
                analysis.error_message = None
                analyze_audio_task.delay(analysis.id)
        
        db.session.commit()
        
        flash('Analysis updated successfully!', 'success')
        return redirect(url_for('analysis.view_analysis', analysis_id=analysis.id))
    
    # For GET request, show the edit form
    return render_template('analysis/edit.html',
                         analysis=analysis,
                         title=f'Edit: {analysis.title}')

@bp.route('/<int:analysis_id>/delete', methods=['POST'])
@login_required
def delete_analysis(analysis_id):
    """Delete an analysis."""
    analysis = Analysis.query.get_or_404(analysis_id)
    
    # Check if the current user owns this analysis or is admin
    if current_user.id != analysis.user_id and not current_user.is_admin:
        flash('You do not have permission to delete this analysis.', 'danger')
        return redirect(url_for('main.index'))
    
    # Delete associated notes
    Note.query.filter_by(analysis_id=analysis_id).delete()
    
    # Delete the analysis
    db.session.delete(analysis)
    db.session.commit()
    
    flash('Analysis deleted successfully!', 'success')
    return redirect(url_for('main.dashboard'))

@bp.route('/<int:analysis_id>/favorite', methods=['POST'])
@login_required
def toggle_favorite(analysis_id):
    """Add or remove an analysis from favorites."""
    analysis = Analysis.query.get_or_404(analysis_id)
    favorite = Favorite.query.filter_by(
        user_id=current_user.id,
        analysis_id=analysis_id
    ).first()
    
    if favorite:
        # Remove from favorites
        db.session.delete(favorite)
        action = 'removed'
    else:
        # Add to favorites
        favorite = Favorite(user_id=current_user.id, analysis_id=analysis_id)
        db.session.add(favorite)
        action = 'added'
    
    db.session.commit()
    
    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'status': 'success',
            'action': action,
            'is_favorited': action == 'added'
        })
    
    flash(f'Analysis {action} from favorites!', 'success')
    return redirect(url_for('analysis.view_analysis', analysis_id=analysis_id))

@bp.route('/<int:analysis_id>/export')
@login_required
def export_analysis(analysis_id):
    """Export analysis data as JSON."""
    analysis = Analysis.query.get_or_404(analysis_id)
    
    # Check if the analysis is public or belongs to the current user
    if not analysis.is_public and current_user.id != analysis.user_id:
        flash('You do not have permission to export this analysis.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get all notes for this analysis
    notes = [{
        'note': note.note_name,
        'frequency': note.frequency,
        'start_time': note.start_time,
        'duration': note.duration,
        'confidence': note.confidence
    } for note in analysis.notes.order_by(Note.start_time).all()]
    
    # Prepare the export data
    export_data = {
        'id': analysis.id,
        'title': analysis.title,
        'description': analysis.description,
        'video_url': analysis.video_url,
        'start_time': analysis.start_time,
        'end_time': analysis.end_time,
        'duration': analysis.end_time - analysis.start_time,
        'shruthi': analysis.shruthi,
        'status': analysis.status,
        'created_at': analysis.created_at.isoformat() if analysis.created_at else None,
        'completed_at': analysis.completed_at.isoformat() if analysis.completed_at else None,
        'notes': notes,
        'user': {
            'id': analysis.user.id,
            'username': analysis.user.username
        }
    }
    
    # Return as JSON response
    response = jsonify(export_data)
    response.headers['Content-Disposition'] = f'attachment; filename=analysis_{analysis.id}.json'
    return response
