import os
import tempfile
import json
import yt_dlp
import numpy as np
import librosa
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import subprocess
import ffmpeg
from datetime import datetime
import io
import soundfile as sf

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')

# Ensure temp directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Carnatic music notes (sapta swaras)
CARNATIC_NOTES = ["Sa", "Ri1", "Ri2", "Ga2", "Ga3", "Ma1", "Ma2", "Pa", "Da1", "Da2", "Ni2", "Ni3"]

# Base frequency for Shadjam (Sa) in Carnatic music
BASE_FREQ = 240.0  # Can be adjusted based on the recording

# Note frequencies for one octave (Carnatic scale)
NOTE_FREQUENCIES = {
    'Sa': 1.0, 'Ri1': 16/15, 'Ri2': 10/9, 'Ga2': 9/8, 'Ga3': 6/5,
    'Ma1': 5/4, 'Ma2': 4/3, 'Pa': 3/2, 'Da1': 8/5, 'Da2': 5/3,
    'Ni2': 9/5, 'Ni3': 15/8
}

def get_audio_from_video_url(video_url, start_time, end_time):
    """Extract audio from a video URL for the specified time range."""
    temp_dir = tempfile.mkdtemp()
    output_path = os.path.join(temp_dir, 'audio_segment.wav')
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(temp_dir, 'audio'),
        'noplaylist': True,
        'quiet': True,
    }
    
    try:
        # Get video info to check duration
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            duration = info.get('duration', 0)
            
            # Validate time range
            if end_time <= start_time or start_time < 0 or end_time > duration:
                raise ValueError("Invalid time range")
            
            # Extract the specific segment
            ydl_opts['postprocessor_args'] = [
                '-ss', str(start_time),
                '-t', str(end_time - start_time)
            ]
            
            # Download and extract audio
            ydl.download([video_url])
            
            # Rename the output file to our expected name
            os.rename(os.path.join(temp_dir, 'audio.wav'), output_path)
            
            return output_path
    except Exception as e:
        print(f"Error processing video URL: {str(e)}")
        if os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir)
        return None

# Shruthi (base note) to frequency mapping
SHRUTHI_FREQUENCIES = {
    'C': 261.63,    # Middle C
    'C#': 277.18,   # C#/D♭
    'D': 293.66,    # D
    'D#': 311.13,   # D#/E♭
    'E': 329.63,    # E
    'F': 349.23,    # F
    'F#': 369.99,   # F#/G♭
    'G': 392.00,    # G
    'G#': 415.30,   # G#/A♭
    'A': 440.00,    # A4 (standard tuning)
    'A#': 466.16,   # A#/B♭
    'B': 493.88     # B
}

def analyze_audio(audio_path, shruthi='C#'):
    """Analyze audio to detect Carnatic notes with improved time resolution.
    
    Args:
        audio_path (str): Path to the audio file to analyze
        shruthi (str): The base note to use as Shadjam (Sa)
    """
    try:
        # Set the base frequency based on the selected shruthi
        global BASE_FREQ
        original_base_freq = BASE_FREQ
        if shruthi in SHRUTHI_FREQUENCIES:
            BASE_FREQ = SHRUTHI_FREQUENCIES[shruthi]
        
        # Load audio file with a higher sample rate for better frequency resolution
        y, sr = librosa.load(audio_path, sr=44100)
        
        # Parameters for analysis
        frame_length = 2048
        hop_length = 512
        
        # Extract pitch using PYIN algorithm with better parameters
        f0, voiced_flag, voiced_probs = librosa.pyin(
            y,
            fmin=librosa.note_to_hz('C2'),
            fmax=librosa.note_to_hz('C7'),
            sr=sr,
            frame_length=frame_length,
            hop_length=hop_length,
            n_thresholds=100,
            beta_parameters=(2, 2),
            boltzmann_parameter=2,
            resolution=0.1,
            max_transition_rate=35,
            switch_prob=0.01,
            no_trough_prob=0.01
        )
        
        # Get time points for each frame
        times = librosa.frames_to_time(
            np.arange(len(f0)),
            sr=sr,
            hop_length=hop_length,
            n_fft=frame_length
        )
        
        # Only keep voiced frames with high confidence
        confidence_threshold = 0.7
        valid_indices = (voiced_flag & (voiced_probs > confidence_threshold))
        f0_voiced = f0[valid_indices]
        times_voiced = times[valid_indices]
        
        if len(f0_voiced) == 0:
            return []
        
        # Filter out constant frequencies (like shruthi/drone)
        # by removing frequencies that appear too consistently
        freq_hist, bin_edges = np.histogram(f0_voiced, bins=50)
        max_freq_count = np.max(freq_hist)
        
        # Only keep frequencies that aren't too dominant (likely shruthi)
        shruthi_threshold = 0.4  # Adjust based on testing
        dominant_freqs = bin_edges[:-1][freq_hist > (max_freq_count * shruthi_threshold)]
        
        # Map frequencies to Carnatic notes with timing information
        notes = []
        for i, (freq, time) in enumerate(zip(f0_voiced, times_voiced)):
            # Skip if this is likely a shruthi frequency
            if any(abs(freq - df) < 2.0 for df in dominant_freqs):
                continue
                
            if freq > 0:  # Only process valid frequencies
                # Find the closest Carnatic note
                note_ratios = {note: abs((freq / BASE_FREQ) - ratio) 
                             for note, ratio in NOTE_FREQUENCIES.items()}
                closest_note, min_diff = min(note_ratios.items(), key=lambda x: x[1])
                
                # Only include notes with reasonable confidence
                if min_diff < 0.1:  # Adjust threshold as needed
                    notes.append({
                        'note': closest_note,
                        'frequency': float(freq),
                        'time': float(time)
                    })
        
        return notes
    except Exception as e:
        print(f"Error analyzing audio: {str(e)}")
        return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        video_url = data.get('video_url')
        start_time = float(data.get('start_time', 0))
        end_time = float(data.get('end_time', 10))
        shruthi = data.get('shruthi', 'C#')  # Default to C# if not specified
        
        if not video_url:
            return jsonify({'error': 'Video URL is required'}), 400
        
        # Get audio from video URL
        audio_path = get_audio_from_video_url(video_url, start_time, end_time)
        
        if not audio_path or not os.path.exists(audio_path):
            return jsonify({'error': 'Failed to extract audio from video'}), 500
        
        # Analyze the audio with the selected shruthi
        notes = analyze_audio(audio_path, shruthi=shruthi)
        
        # Clean up
        if os.path.exists(audio_path):
            os.remove(audio_path)
            os.rmdir(os.path.dirname(audio_path))
        
        return jsonify({
            'status': 'success',
            'notes': notes,
            'duration': end_time - start_time,
            'shruthi': shruthi,
            'base_frequency': SHRUTHI_FREQUENCIES.get(shruthi, 277.18)  # Default to C# if not found
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_ENV') == 'development')
