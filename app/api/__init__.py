from flask import Blueprint, jsonify, request, current_app
from flask_login import current_user, login_required
from ..models import db, Analysis, Note, User, Favorite
from ..auth.auth import token_auth
from datetime import datetime
import os

bp = Blueprint('api', __name__)

@bp.route('/token')
@login_required
@token_auth.login_required
def get_token():
    """Get an authentication token."""
    token = current_user.get_token()
    db.session.commit()
    return jsonify({'token': token, 'expires_in': 3600})

@bp.route('/analyses', methods=['GET'])
def get_analyses():
    """Get a list of public analyses."""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    
    # Base query for public analyses
    query = Analysis.query.filter_by(is_public=True)
    
    # Apply filters
    if 'user_id' in request.args:
        query = query.filter_by(user_id=request.args.get('user_id', type=int))
    
    if 'q' in request.args:
        search = f"%{request.args.get('q')}%"
        query = query.filter(
            (Analysis.title.ilike(search)) |
            (Analysis.description.ilike(search))
        )
    
    # Order and paginate
    data = query.order_by(Analysis.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'items': [item.to_dict() for item in data.items],
        '_meta': {
            'page': page,
            'per_page': per_page,
            'total_pages': data.pages,
            'total_items': data.total
        }
    })

@bp.route('/analyses/<int:id>')
def get_analysis(id):
    """Get a single analysis by ID."""
    analysis = Analysis.query.get_or_404(id)
    
    # Check if the analysis is public or belongs to the current user
    if not analysis.is_public and (not current_user.is_authenticated or 
                                  current_user.id != analysis.user_id):
        return jsonify({'error': 'Forbidden'}), 403
    
    return jsonify(analysis.to_dict())

@bp.route('/analyses', methods=['POST'])
@token_auth.login_required
def create_analysis():
    """Create a new analysis."""
    data = request.get_json() or {}
    
    # Validate required fields
    if 'video_url' not in data or not data['video_url']:
        return jsonify({'error': 'video_url is required'}), 400
    
    # Create new analysis
    analysis = Analysis()
    analysis.from_dict(data)
    analysis.user_id = current_user.id
    
    db.session.add(analysis)
    db.session.commit()
    
    # In production, you would use a task queue like Celery
    # to process the analysis in the background
    from ..tasks import analyze_audio_task
    analyze_audio_task.delay(analysis.id)
    
    response = jsonify(analysis.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_analysis', id=analysis.id)
    return response

@bp.route('/analyses/<int:id>', methods=['PUT'])
@token_auth.login_required
def update_analysis(id):
    """Update an existing analysis."""
    analysis = Analysis.query.get_or_404(id)
    
    # Check if the current user owns this analysis
    if current_user.id != analysis.user_id and not current_user.is_admin:
        return jsonify({'error': 'Forbidden'}), 403
    
    data = request.get_json() or {}
    analysis.from_dict(data)
    db.session.commit()
    
    return jsonify(analysis.to_dict())

@bp.route('/analyses/<int:id>', methods=['DELETE'])
@token_auth.login_required
def delete_analysis(id):
    """Delete an analysis."""
    analysis = Analysis.query.get_or_404(id)
    
    # Check if the current user owns this analysis or is admin
    if current_user.id != analysis.user_id and not current_user.is_admin:
        return jsonify({'error': 'Forbidden'}), 403
    
    # Delete associated notes
    Note.query.filter_by(analysis_id=id).delete()
    
    # Delete the analysis
    db.session.delete(analysis)
    db.session.commit()
    
    return '', 204

@bp.route('/analyses/<int:id>/notes')
def get_analysis_notes(id):
    """Get all notes for an analysis."""
    analysis = Analysis.query.get_or_404(id)
    
    # Check if the analysis is public or belongs to the current user
    if not analysis.is_public and (not current_user.is_authenticated or 
                                  current_user.id != analysis.user_id):
        return jsonify({'error': 'Forbidden'}), 403
    
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    
    # Get paginated notes
    pagination = analysis.notes.order_by(Note.start_time)\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'items': [item.to_dict() for item in pagination.items],
        '_meta': {
            'page': page,
            'per_page': per_page,
            'total_pages': pagination.pages,
            'total_items': pagination.total
        }
    })

@bp.route('/users/<int:id>')
def get_user(id):
    """Get user information."""
    user = User.query.get_or_404(id)
    
    # Only allow viewing public information unless it's the current user
    if current_user.is_anonymous or current_user.id != id:
        return jsonify(user.to_dict(include_email=False))
    
    return jsonify(user.to_dict())

@bp.route('/users/<int:id>/analyses')
def get_user_analyses(id):
    """Get all analyses for a user."""
    user = User.query.get_or_404(id)
    
    # Only show public analyses unless it's the current user
    if current_user.is_anonymous or current_user.id != id:
        query = user.analyses.filter_by(is_public=True)
    else:
        query = user.analyses
    
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 50)
    
    # Apply filters
    if 'q' in request.args:
        search = f"%{request.args.get('q')}%"
        query = query.filter(
            (Analysis.title.ilike(search)) |
            (Analysis.description.ilike(search))
        )
    
    # Order and paginate
    pagination = query.order_by(Analysis.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'items': [item.to_dict() for item in pagination.items],
        '_meta': {
            'page': page,
            'per_page': per_page,
            'total_pages': pagination.pages,
            'total_items': pagination.total
        }
    })

@bp.route('/me')
@token_auth.login_required
def get_current_user():
    """Get the current authenticated user's information."""
    return jsonify(current_user.to_dict())

@bp.route('/me/analyses')
@token_auth.login_required
def get_my_analyses():
    """Get the current user's analyses."""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 50)
    
    # Apply filters
    query = current_user.analyses
    
    if 'q' in request.args:
        search = f"%{request.args.get('q')}%"
        query = query.filter(
            (Analysis.title.ilike(search)) |
            (Analysis.description.ilike(search))
        )
    
    # Order and paginate
    pagination = query.order_by(Analysis.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'items': [item.to_dict() for item in pagination.items],
        '_meta': {
            'page': page,
            'per_page': per_page,
            'total_pages': pagination.pages,
            'total_items': pagination.total
        }
    })

@bp.route('/me/favorites', methods=['GET'])
@token_auth.login_required
def get_my_favorites():
    """Get the current user's favorite analyses."""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 50)
    
    # Get favorite analyses
    query = Analysis.query.join(Favorite)\
        .filter(Favorite.user_id == current_user.id)
    
    # Apply filters
    if 'q' in request.args:
        search = f"%{request.args.get('q')}%"
        query = query.filter(
            (Analysis.title.ilike(search)) |
            (Analysis.description.ilike(search))
        )
    
    # Order and paginate
    pagination = query.order_by(Favorite.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'items': [item.to_dict() for item in pagination.items],
        '_meta': {
            'page': page,
            'per_page': per_page,
            'total_pages': pagination.pages,
            'total_items': pagination.total
        }
    })

@bp.route('/analyses/<int:id>/favorite', methods=['POST'])
@token_auth.login_required
def toggle_favorite(id):
    """Add or remove an analysis from favorites."""
    analysis = Analysis.query.get_or_404(id)
    favorite = Favorite.query.filter_by(
        user_id=current_user.id,
        analysis_id=id
    ).first()
    
    if favorite:
        # Remove from favorites
        db.session.delete(favorite)
        db.session.commit()
        return jsonify({'status': 'removed', 'favorite': False})
    else:
        # Add to favorites
        favorite = Favorite(user_id=current_user.id, analysis_id=id)
        db.session.add(favorite)
        db.session.commit()
        return jsonify({'status': 'added', 'favorite': True})
