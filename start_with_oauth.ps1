# Start with OAuth Script
# This script sets up environment variables and starts the Flask application

# Set your Google OAuth credentials here
$env:GOOGLE_CLIENT_ID = "395707312620-i6nq9lirn82gv31hjqt1fi3qqq3nsrf4.apps.googleusercontent.com"
$env:GOOGLE_CLIENT_SECRET = "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"

# Print the environment variables for verification
Write-Host "Starting RagaNoteFinder with the following OAuth settings:"
Write-Host "GOOGLE_CLIENT_ID: $env:GOOGLE_CLIENT_ID"
Write-Host "GOOGLE_CLIENT_SECRET: $($env:GOOGLE_CLIENT_SECRET.Substring(0, 5))..."  # Only show first 5 chars of secret

# Start the Flask application
Write-Host "`nStarting Flask application..."  # Using backtick for newline
python start_app.py
