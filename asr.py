import os
import argparse
from datetime import datetime
from pathlib import Path
import ssl
import urllib3

from dotenv import load_dotenv
from pydub import AudioSegment
from typing import Optional, Tuple
import whisper

# Load environment variables
load_dotenv()

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
os.environ['PYTHONHTTPSVERIFY'] = '0'
ssl._create_default_https_context = ssl._create_unverified_context


def _normalize_language_code(lang: str | None) -> str | None:
    """Normalize language to Whisper codes (short codes like 'en', 'hi', 'mr')."""
    if not lang:
        return None
    lang = lang.strip().lower()
    # Whisper uses ISO 639-1 short codes
    mapping = {
        "en-us": "en",
        "hi-in": "hi",
        "mr-in": "mr",
        "or-in": "or",
        "gu-in": "gu",
        "bn-in": "bn",
        "ta-in": "ta",
        "te-in": "te",
        "kn-in": "kn",
        "ml-in": "ml",
        "pa-in": "pa",
        "ur-in": "ur",
        "odia": "or",
        "gujarati": "gu",
        "marathi": "mr",
        "hindi": "hi",
        "english": "en",
    }
    return mapping.get(lang, lang)


def convert_to_wav_mono_16k(input_path: str) -> str:
    """Convert any input audio to mono 16kHz WAV and return path to temp file."""
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_frame_rate(16000).set_channels(1)
    
    # Create unique temp file name
    out_dir = Path("audio_temp")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = Path(input_path).stem
    temp_path = out_dir / f"{base_name}_{timestamp}_normalized.wav"
    
    print(f"Normalizing audio to: {temp_path}")
    audio.export(temp_path, format="wav")
    return str(temp_path)


def transcribe_audio_whisper(
    input_path: str,
    language: str | None = None,
    model_size: str = "base",
) -> Tuple[str, Optional[int]]:
    """Transcribe an audio file using OpenAI Whisper (Free & Local).

    - ALWAYS converts audio to normalized WAV mono @ 16kHz first
    - Returns plain text transcript
    """
    language_code = _normalize_language_code(language)

    # 1. ALWAYS convert to normalized WAV first
    wav_path = convert_to_wav_mono_16k(input_path)
    
    print(f"Loading Whisper model ({model_size})...")
    model = whisper.load_model(model_size)
    
    print("Transcribing...")
    result = model.transcribe(wav_path, language=language_code)
    
    # Extract detected language
    detected_lang = result.get("language")
    
    return result["text"].strip(), detected_lang


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transcribe audio to text using Whisper.")
    parser.add_argument("--input", required=True, help="Path to audio file")
    parser.add_argument("--lang", default=None, help="Language code (en, hi, mr, etc.)")
    parser.add_argument("--model", default="base", help="Whisper model size (tiny, base, small, medium, large)")
    args = parser.parse_args()

    try:
        text, _ = transcribe_audio_whisper(args.input, language=args.lang, model_size=args.model)
        print("--- Transcript ---")
        print(text)
    except Exception as e:
        print(f"Error: {e}")
