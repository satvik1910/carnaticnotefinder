import os
import time
import tempfile
import shutil
from datetime import datetime
from flask import current_app
from .models import db, Analysis, Note
from .audio_utils import analyze_audio_segment

def analyze_audio_task(analysis_id):
    """Background task to analyze audio from a video URL."""
    analysis = Analysis.query.get(analysis_id)
    if not analysis:
        current_app.logger.error(f'Analysis {analysis_id} not found')
        return
    
    try:
        # Update status to processing
        analysis.status = 'processing'
        analysis.started_at = datetime.utcnow()
        db.session.commit()
        
        # Create a temporary directory for processing
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Extract audio from video
            audio_path = os.path.join(temp_dir, 'audio.wav')
            
            # Download and extract audio using yt-dlp
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(temp_dir, 'audio.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                    'preferredquality': '192',
                }],
                'noplaylist': True,
                'quiet': True,
                'no_warnings': True,
            }
            
            import yt_dlp
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([analysis.video_url])
            
            # Check if audio file was created
            if not os.path.exists(audio_path):
                # Try to find the audio file with different extensions
                for ext in ['wav', 'mp3', 'm4a', 'ogg']:
                    test_path = os.path.join(temp_dir, f'audio.{ext}')
                    if os.path.exists(test_path):
                        audio_path = test_path
                        break
            
            if not os.path.exists(audio_path):
                raise Exception('Failed to extract audio from video')
            
            # Analyze the audio segment
            notes = analyze_audio_segment(
                audio_path=audio_path,
                start_time=analysis.start_time,
                end_time=analysis.end_time,
                shruthi=analysis.shruthi
            )
            
            # Save notes to database
            for note_data in notes:
                note = Note(
                    analysis_id=analysis.id,
                    note_name=note_data['note'],
                    frequency=note_data['frequency'],
                    start_time=note_data['start_time'],
                    duration=note_data['duration'],
                    confidence=note_data.get('confidence', 1.0)
                )
                db.session.add(note)
            
            # Update analysis status and completion time
            analysis.status = 'completed'
            analysis.completed_at = datetime.utcnow()
            db.session.commit()
            
            # Send notification email if user has email notifications enabled
            if analysis.user.email_notifications:
                from .email import send_analysis_complete_notification
                send_analysis_complete_notification(analysis.user, analysis)
            
        except Exception as e:
            # Log the error and update status
            current_app.logger.error(f'Error processing analysis {analysis_id}: {str(e)}', 
                                   exc_info=True)
            analysis.status = 'failed'
            analysis.error_message = str(e)
            db.session.commit()
            
            # Re-raise the exception to trigger task retry if needed
            raise
            
        finally:
            # Clean up temporary files
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    except Exception as e:
        # Handle any other unexpected errors
        current_app.logger.error(f'Unexpected error in analysis task {analysis_id}: {str(e)}', 
                               exc_info=True)
        if 'analysis' in locals():
            analysis.status = 'failed'
            analysis.error_message = str(e)
            db.session.commit()
        raise

def cleanup_old_analyses(days=30):
    """Clean up old analysis data that is no longer needed."""
    try:
        from datetime import datetime, timedelta
        
        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Find analyses older than the cutoff date that are not marked as saved
        old_analyses = Analysis.query.filter(
            Analysis.created_at < cutoff_date,
            Analysis.is_saved == False
        ).all()
        
        # Delete associated notes and then the analyses
        for analysis in old_analyses:
            # Delete associated notes
            Note.query.filter_by(analysis_id=analysis.id).delete()
            
            # Delete analysis record
            db.session.delete(analysis)
        
        # Commit the changes
        db.session.commit()
        
        current_app.logger.info(f'Cleaned up {len(old_analyses)} old analyses')
        return f'Successfully cleaned up {len(old_analyses)} old analyses'
    
    except Exception as e:
        current_app.logger.error(f'Error cleaning up old analyses: {str(e)}', exc_info=True)
        db.session.rollback()
        raise
