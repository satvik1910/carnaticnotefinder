import os
import numpy as np
import librosa
from scipy import signal
from scipy.stats import mode
from config import Config  # Using relative import

def extract_audio_segment(audio_path, start_time, end_time, sr=44100):
    """Extract a segment from an audio file."""
    try:
        # Load the audio file
        y, sr = librosa.load(audio_path, sr=sr, mono=True)
        
        # Calculate start and end samples
        start_sample = int(start_time * sr)
        end_sample = int(end_time * sr)
        
        # Ensure we don't go out of bounds
        if start_sample >= len(y):
            return np.array([]), sr
        
        end_sample = min(end_sample, len(y))
        
        # Extract the segment
        segment = y[start_sample:end_sample]
        
        return segment, sr
    except Exception as e:
        print(f"Error extracting audio segment: {str(e)}")
        return np.array([]), sr

def analyze_audio_segment(audio_path, start_time, end_time, shruthi='C#', **kwargs):
    """Analyze an audio segment and detect musical notes."""
    try:
        # Extract the audio segment
        y, sr = extract_audio_segment(audio_path, start_time, end_time)
        
        if len(y) == 0:
            return []
            
        # Get base frequency for the selected shruthi
        base_freq = Config.SHRUTHI_FREQUENCIES.get(shruthi, 277.18)
        
        # Parameters for pitch detection
        frame_length = kwargs.get('frame_length', 2048)
        hop_length = kwargs.get('hop_length', 512)
        fmin = kwargs.get('fmin', 100)
        fmax = kwargs.get('fmax', 2000)
        
        # Use PYIN algorithm for pitch detection
        f0, voiced_flag, voiced_probs = librosa.pyin(
            y,
            fmin=fmin,
            fmax=fmax,
            sr=sr,
            frame_length=frame_length,
            hop_length=hop_length
        )
        
        # Only keep voiced frames with high confidence
        confidence_threshold = kwargs.get('confidence_threshold', 0.7)
        valid_indices = (voiced_flag & (voiced_probs > confidence_threshold))
        f0_voiced = f0[valid_indices]
        
        if len(f0_voiced) == 0:
            return []
            
        # Filter out constant frequencies (like shruthi/drone)
        freq_hist, bin_edges = np.histogram(f0_voiced, bins=50)
        max_freq_count = np.max(freq_hist)
        
        # Only keep frequencies that aren't too dominant (likely shruthi)
        shruthi_threshold = kwargs.get('shruthi_threshold', 0.4)
        dominant_freqs = bin_edges[:-1][freq_hist > (max_freq_count * shruthi_threshold)]
        
        # Map frequencies to musical notes
        notes = []
        time_per_frame = hop_length / sr
        
        for i, freq in enumerate(f0_voiced):
            # Skip if this is likely a shruthi frequency
            if any(abs(freq - df) < 2.0 for df in dominant_freqs):
                continue
                
            if freq > 0:  # Only process valid frequencies
                # Calculate the time for this frame
                time = i * time_per_frame
                
                # Map frequency to a musical note
                note_name, note_freq = freq_to_note(freq, base_freq)
                
                # Add to notes list
                notes.append({
                    'time': time,
                    'note': note_name,
                    'frequency': float(freq),
                    'duration': time_per_frame,
                    'confidence': float(voiced_probs[i] if i < len(voiced_probs) else 1.0)
                })
        
        # Group nearby notes of the same pitch
        return group_notes(notes)
        
    except Exception as e:
        print(f"Error analyzing audio segment: {str(e)}")
        return []

def group_notes(notes, time_threshold=0.1):
    """Group nearby notes of the same pitch."""
    if not notes:
        return []
    
    grouped_notes = []
    current_note = notes[0]
    
    for note in notes[1:]:
        # If same note and close in time, extend duration
        if (note['note'] == current_note['note'] and 
            note['time'] <= current_note['time'] + current_note['duration'] + time_threshold):
            current_note['duration'] = note['time'] + note['duration'] - current_note['time']
        else:
            grouped_notes.append(current_note)
            current_note = note
    
    # Add the last note
    grouped_notes.append(current_note)
    
    return grouped_notes

def freq_to_note(freq, base_freq=277.18):
    """Convert a frequency to the nearest musical note."""
    # Carnatic note names
    note_names = [
        "Sa", "Ri1", "Ri2", "Ga2", "Ga3", 
        "Ma1", "Ma2", "Pa", "Da1", "Da2", "Ni2", "Ni3"
    ]
    
    # Calculate the number of semitones from the base frequency
    semitones = 12 * np.log2(freq / base_freq)
    
    # Round to the nearest semitone
    semitone = int(round(semitones))
    
    # Calculate the octave shift
    octave = semitone // 12
    note_index = semitone % 12
    
    # Handle notes that wrap around
    if note_index < 0:
        note_index += 12
        octave -= 1
    
    # Get the note name
    if 0 <= note_index < len(note_names):
        note_name = note_names[note_index]
    else:
        note_name = f"Unknown({note_index})"
    
    # Calculate the exact frequency of the note
    note_freq = base_freq * (2 ** (semitone / 12.0))
    
    return note_name, note_freq
