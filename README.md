# Audio to Text Translation

This project provides tools to transcribe audio files to text using Google Cloud Speech-to-Text and translate them into English.

## Features
- Speech-to-Text (ASR) support for multiple languages (Hindi, Marathi, Odia, Gujarati, etc.).
- Speaker diarization (detecting different speakers).
- Automatic translation to English using `deep-translator`.
- Supports various audio formats (wav, mp3, m4a).

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Google Cloud Credentials**:
   - Obtain a Google Cloud service account key JSON file.
   - Set the environment variable `GOOGLE_APPLICATION_CREDENTIALS` to the path of your JSON file.
   - You can use the provided `.env.example` as a template for your `.env` file.

3. **Audio Processing (FFmpeg)**:
   - This project uses `pydub`, which requires FFmpeg to be installed on your system.

## Usage

### Run the Pipeline
Use the `main.py` script to transcribe and translate an audio file:

```bash
python main.py --input audio/sample_hindi.wav --lang hi
```

Options:
- `--input`: Path to the audio file.
- `--lang`: Language code (e.g., `hi`, `mr`, `or`, `gu`, `en`).
- `--no-translate`: Disable translation to English.

### Transcribe Only
You can also use `asr.py` directly for transcription:

```bash
python asr.py --input audio/sample_hindi.wav --lang hi --diarize
```

### Translate Only
Use `translator.py` for text translation:

```bash
python translator.py --text "नमस्ते" --source hi --target en
```

## Supported Languages
- English (`en`)
- Hindi (`hi`)
- Marathi (`mr`)
- Odia (`or`)
- Gujarati (`gu`)
- Bengali (`bn`)
- Tamil (`ta`)
- Telugu (`te`)
- Kannada (`kn`)
- Malayalam (`ml`)
- Punjabi (`pa`)
- Urdu (`ur`)
