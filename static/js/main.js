// Main JavaScript for RagaNoteFinder

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('analysisForm');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const resultsDiv = document.getElementById('results');
    const resultsBody = document.getElementById('resultsBody');
    const noResultsDiv = document.getElementById('noResults');
    const errorDiv = document.getElementById('error');

    // Form submission handler
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Reset UI
        errorDiv.classList.add('d-none');
        resultsDiv.classList.add('d-none');
        noResultsDiv.classList.add('d-none');
        
        // Get form values
        const videoUrl = document.getElementById('videoUrl').value.trim();
        const startTime = parseFloat(document.getElementById('startTime').value);
        const endTime = parseFloat(document.getElementById('endTime').value);
        const shruthi = document.getElementById('shruthi').value;
        
        // Validate input
        if (!videoUrl) {
            showError('Please enter a valid video URL');
            return;
        }
        
        if (isNaN(startTime) || isNaN(endTime) || startTime < 0 || endTime <= startTime) {
            showError('Please enter valid start and end times (end time must be after start time)');
            return;
        }
        
        // Show loading state
        const spinner = analyzeBtn.querySelector('.spinner-border');
        spinner.classList.remove('d-none');
        analyzeBtn.disabled = true;
        
        try {
            // Send request to backend
            const response = await fetch('/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    video_url: videoUrl,
                    start_time: startTime,
                    end_time: endTime,
                    shruthi: shruthi
                })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to analyze video');
            }
            
            // Display results with the correct timing
            displayResults(data.notes, endTime - startTime, startTime);
            
        } catch (error) {
            console.error('Error:', error);
            showError(error.message || 'An error occurred while processing your request');
        } finally {
            // Reset loading state
            spinner.classList.add('d-none');
            analyzeBtn.disabled = false;
        }
    });
    
    // Display analysis results with timing information
    function displayResults(notes, duration, startTime) {
        resultsBody.innerHTML = '';
        
        if (!notes || notes.length === 0) {
            noResultsDiv.classList.remove('d-none');
            resultsDiv.classList.remove('d-none');
            return;
        }
        
        // Get the start time from the form
        const startTimeValue = parseFloat(document.getElementById('startTime').value) || 0;
        
        // Sort notes by time
        notes.sort((a, b) => a.time - b.time);
        
        // Group nearby notes (within 0.1s) for better visualization
        const noteGroups = [];
        let currentGroup = null;
        const timeThreshold = 0.1; // seconds
        
        notes.forEach(note => {
            // Add start time offset to each note's time
            const absoluteTime = note.time + startTimeValue;
            
            if (!currentGroup || (absoluteTime - currentGroup.endTime) > timeThreshold) {
                // Start a new group
                currentGroup = {
                    startTime: absoluteTime,
                    endTime: absoluteTime,
                    notes: new Set([note.note]),
                    frequencies: [note.frequency]
                };
                noteGroups.push(currentGroup);
            } else {
                // Add to current group
                currentGroup.notes.add(note.note);
                currentGroup.frequencies.push(note.frequency);
                currentGroup.endTime = Math.max(currentGroup.endTime, absoluteTime);
            }
        });
        
        // Display each note group
        noteGroups.forEach(group => {
            const row = document.createElement('tr');
            
            // Time cell with range
            const timeCell = document.createElement('td');
            timeCell.textContent = `${group.startTime.toFixed(2)} - ${group.endTime.toFixed(2)}s`;
            
            // Notes cell (sorted)
            const noteCell = document.createElement('td');
            noteCell.textContent = Array.from(group.notes).sort().join(', ');
            
            // Average frequency
            const avgFreq = group.frequencies.reduce((a, b) => a + b, 0) / group.frequencies.length;
            const freqCell = document.createElement('td');
            freqCell.textContent = avgFreq.toFixed(2) + ' Hz';
            
            // Duration indicator (visual)
            const durationCell = document.createElement('td');
            const duration = group.endTime - group.startTime;
            const durationBar = document.createElement('div');
            durationBar.className = 'duration-bar';
            durationBar.style.width = `${Math.min(100, duration * 10)}%`; // Scale for visibility
            durationBar.title = `Duration: ${duration.toFixed(2)}s`;
            durationCell.appendChild(durationBar);
            
            row.appendChild(timeCell);
            row.appendChild(noteCell);
            row.appendChild(freqCell);
            row.appendChild(durationCell);
            
            resultsBody.appendChild(row);
        });
        
        // Show the results section
        resultsDiv.classList.remove('d-none');
        noResultsDiv.classList.add('d-none');
    }
    
    // Group notes by time for better visualization
    function groupNotesByTime(notes, duration) {
        const timeSlots = 20; // Number of time slots to group notes into
        const slotDuration = duration / timeSlots;
        const groups = [];
        
        for (let i = 0; i < timeSlots; i++) {
            const startTime = i * slotDuration;
            const endTime = (i + 1) * slotDuration;
            
            // Filter notes in this time slot
            const notesInSlot = notes.filter(note => 
                note.time >= startTime && note.time < endTime
            );
            
            if (notesInSlot.length > 0) {
                // Get unique notes in this time slot
                const uniqueNotes = [...new Set(notesInSlot.map(note => note.note))];
                
                // Calculate average frequency
                const totalFreq = notesInSlot.reduce((sum, note) => sum + note.frequency, 0);
                const avgFreq = totalFreq / notesInSlot.length;
                
                groups.push({
                    time: startTime,
                    notes: uniqueNotes,
                    avgFrequency: avgFreq
                });
            }
        }
        
        return groups;
    }
    
    // Show error message
    function showError(message) {
        errorDiv.textContent = message;
        errorDiv.classList.remove('d-none');
    }
    
    // Set end time to 10 seconds after start time when start time changes
    document.getElementById('startTime').addEventListener('change', function() {
        const startTime = parseFloat(this.value);
        const endTimeInput = document.getElementById('endTime');
        
        if (!isNaN(startTime) && parseFloat(endTimeInput.value) <= startTime) {
            endTimeInput.value = (startTime + 10).toFixed(1);
        }
    });
});
