# RagaNoteFinder

RagaNoteFinder is a web application that identifies Carnatic music notes from a specified time segment of a video URL. The application extracts audio from the video, analyzes it, and identifies the Carnatic notes being played.

## Features

- Extract audio from video URLs (YouTube, etc.)
- Specify custom time segments for analysis
- Identify Carnatic music notes (Swaras) in the audio
- Clean, responsive web interface
- No need to download the entire video

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/RagaNoteFinder.git
   cd RagaNoteFinder
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install FFmpeg (required for audio processing):
   - On Ubuntu/Debian: `sudo apt-get install ffmpeg`
   - On macOS: `brew install ffmpeg`
   - On Windows: Download from https://ffmpeg.org/download.html

## Usage

1. Run the application:
   ```bash
   python app.py
   ```

2. Open your web browser and navigate to `http://localhost:8080`

3. Enter a video URL and specify the time range you want to analyze

4. Click "Analyze Video Segment" to see the detected Carnatic notes

## How It Works

1. The application extracts audio from the specified video URL using `yt-dlp`
2. It processes only the specified time segment to save processing time
3. The audio is analyzed using LibROSA to detect pitches and frequencies
4. Detected frequencies are mapped to the nearest Carnatic music notes
5. Results are displayed in an easy-to-read table format

## Dependencies

- Python 3.8+
- Flask
- LibROSA
- NumPy
- yt-dlp
- FFmpeg
- Other dependencies listed in `requirements.txt`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
