# Audio to Text Translation

This project provides tools to transcribe audio files to text using **OpenAI Whisper (Free & Local)** and translate them into English.

## Features
- Speech-to-Text (ASR) support for multiple languages (Hindi, Marathi, Odia, Gujarati, etc.) using OpenAI Whisper.
- Runs locally on your machine—no API keys or costs required for transcription.
- Automatic translation to English using `deep-translator`.
- Supports various audio formats (wav, mp3, m4a).

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Audio Processing (FFmpeg)**:
   - This project uses `pydub` and `whisper`, both of which require FFmpeg to be installed on your system.

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
python asr.py --input audio/sample_hindi.wav --lang hi --model base
```

Options:
- `--model`: Whisper model size (`tiny`, `base`, `small`, `medium`, `large`). Default is `base`.

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
