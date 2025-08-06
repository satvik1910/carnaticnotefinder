from flask import render_template, jsonify, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from . import bp
from ..models import db, Analysis, Note, User, Favorite
from datetime import datetime
import os
import tempfile

@bp.route('/')
def index():
    """Home page with featured analyses and app information."""
    try:
        # Get recent public analyses
        recent_analyses = Analysis.query.filter_by(is_public=True)\
            .order_by(Analysis.created_at.desc())\
            .limit(6).all()
        
        return render_template('main/index.html',
                            recent_analyses=recent_analyses,
                            title='Home')
    except Exception as e:
        current_app.logger.error(f"Error in index route: {str(e)}")
        return render_template('main/index.html',
                            recent_analyses=[],
                            title='Home')

@bp.route('/about')
def about():
    """About page with information about the application."""
    return render_template('main/about.html', title='About')

@bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard showing their analyses and statistics."""
    try:
        # Get user's recent analyses
        recent_analyses = current_user.analyses\
            .order_by(Analysis.created_at.desc())\
            .limit(5).all()
        
        # Get user's favorite analyses
        favorites = current_user.favorites\
            .join(Analysis)\
            .order_by(Analysis.created_at.desc())\
            .limit(5).all()
        
        # Get some statistics
        total_analyses = current_user.analyses.count()
        total_notes = Note.query.join(Analysis)\
            .filter(Analysis.user_id == current_user.id)\
            .count()
        
        return render_template('main/dashboard.html',
                             recent_analyses=recent_analyses,
                             favorites=favorites,
                             total_analyses=total_analyses,
                             total_notes=total_notes,
                             title='Dashboard')
    except Exception as e:
        current_app.logger.error(f"Error in dashboard route: {str(e)}")
        flash('An error occurred while loading your dashboard.', 'error')
        return redirect(url_for('main.index'))

@bp.route('/browse')
def browse():
    """Browse public analyses from all users."""
    page = request.args.get('page', 1, type=int)
    query = request.args.get('q', '')
    
    # Base query for public analyses
    analyses = Analysis.query.filter_by(is_public=True)
    
    # Apply search filter if provided
    if query:
        analyses = analyses.filter(
            (Analysis.title.ilike(f'%{query}%')) |
            (Analysis.description.ilike(f'%{query}%'))
        )
    
    # Order and paginate
    analyses = analyses.order_by(Analysis.created_at.desc())\
        .paginate(page=page, per_page=12, error_out=False)
    
    return render_template('browse.html',
                         analyses=analyses,
                         query=query,
                         title='Browse Analyses')

@bp.route('/analyze', methods=['GET', 'POST'])
@login_required
def analyze():
    """Analyze a video or audio file."""
    if request.method == 'POST':
        video_url = request.form.get('video_url')
        start_time = float(request.form.get('start_time', 0))
        end_time = float(request.form.get('end_time', 10))
        shruthi = request.form.get('shruthi', 'C#')
        title = request.form.get('title', 'Untitled Analysis')
        is_public = 'is_public' in request.form
        
        # Create a new analysis record
        analysis = Analysis(
            user_id=current_user.id,
            title=title,
            video_url=video_url,
            start_time=start_time,
            end_time=end_time,
            shruthi=shruthi,
            is_public=is_public
        )
        
        db.session.add(analysis)
        db.session.commit()
        
        # In a production environment, you would use a task queue like Celery
        # to process the analysis in the background
        from ..tasks import analyze_audio_task
        analyze_audio_task.delay(analysis.id)
        
        flash('Your analysis has been queued. Please check back in a moment!', 'info')
        return redirect(url_for('main.analysis', analysis_id=analysis.id))
    
    # For GET request, show the analysis form
    return render_template('analyze.html', 
                         title='Analyze Audio',
                         default_shruthi='C#',
                         default_start=0,
                         default_end=10)

@bp.route('/analysis/<int:analysis_id>')
def analysis(analysis_id):
    """View analysis results."""
    analysis = Analysis.query.get_or_404(analysis_id)
    
    # Check if the analysis is public or belongs to the current user
    if not analysis.is_public and (not current_user.is_authenticated or 
                                  current_user.id != analysis.user_id):
        flash('You do not have permission to view this analysis.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get all notes for this analysis
    notes = analysis.notes.order_by(Note.start_time).all()
    
    # Check if analysis is in user's favorites
    is_favorite = False
    if current_user.is_authenticated:
        is_favorite = Favorite.query.filter_by(
            user_id=current_user.id,
            analysis_id=analysis_id
        ).first() is not None
    
    return render_template('analysis.html',
                         analysis=analysis,
                         notes=notes,
                         is_favorite=is_favorite,
                         title=f'Analysis: {analysis.title}')

@bp.route('/analysis/<int:analysis_id>/delete', methods=['POST'])
@login_required
def delete_analysis(analysis_id):
    """Delete an analysis."""
    analysis = Analysis.query.get_or_404(analysis_id)
    
    # Check if the current user owns this analysis
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

@bp.route('/favorite/<int:analysis_id>', methods=['POST'])
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
        action = 'removed from'
        is_favorite = False
    else:
        # Add to favorites
        favorite = Favorite(user_id=current_user.id, analysis_id=analysis_id)
        db.session.add(favorite)
        action = 'added to'
        is_favorite = True
    
    db.session.commit()
    
    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'status': 'success',
            'action': action,
            'is_favorite': is_favorite
        })
    
    flash(f'Analysis {action} your favorites.', 'success')
    return redirect(url_for('main.analysis', analysis_id=analysis_id))
