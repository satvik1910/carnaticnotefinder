from flask import render_template, current_app
from flask_mail import Message
from . import mail
from threading import Thread

def send_async_email(app, msg):
    """Send an email asynchronously."""
    with app.app_context():
        mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body):
    """Send an email with the given parameters."""
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    
    # Send email asynchronously
    Thread(target=send_async_email, 
           args=(current_app._get_current_object(), msg)).start()

def send_password_reset_email(user):
    """Send a password reset email to the user."""
    token = user.get_reset_password_token()
    send_email(
        'Reset Your Password',
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[user.email],
        text_body=render_template('email/reset_password.txt', user=user, token=token),
        html_body=render_template('email/reset_password.html', user=user, token=token)
    )

def send_welcome_email(user):
    """Send a welcome email to new users."""
    send_email(
        'Welcome to RagaNoteFinder!',
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[user.email],
        text_body=render_template('email/welcome.txt', user=user),
        html_body=render_template('email/welcome.html', user=user)
    )

def send_analysis_complete_notification(user, analysis):
    """Send a notification when an analysis is complete."""
    send_email(
        f'Your analysis "{analysis.title}" is ready!',
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[user.email],
        text_body=render_template('email/analysis_complete.txt', 
                                user=user, analysis=analysis),
        html_body=render_template('email/analysis_complete.html', 
                                user=user, analysis=analysis)
    )
