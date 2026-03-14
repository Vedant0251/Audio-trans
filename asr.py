import os
import argparse
from datetime import datetime
from pathlib import Path
import ssl
import urllib3

from dotenv import load_dotenv
from pydub import AudioSegment
import wave
import io
from typing import Optional, Set, Tuple, List
from google.cloud import speech_v1 as speech

# Load environment variables (e.g., GOOGLE_APPLICATION_CREDENTIALS)
load_dotenv()

# Disable SSL warnings and certificate verification for corporate networks
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
os.environ['PYTHONHTTPSVERIFY'] = '0'
ssl._create_default_https_context = ssl._create_unverified_context


def _normalize_language_code(lang: str | None) -> str:
    """Normalize language to Google STT codes. Default to en-US if None.

    Accepts short codes like 'en', 'hi', 'mr' and maps to en-US, hi-IN, mr-IN.
    """
    if not lang:
        return "en-US"
    lang = lang.strip().lower()
    short_to_full = {
        "en": "en-US",
        "hi": "hi-IN",
        "mr": "mr-IN",
        "or": "or-IN",  # Odia
        "odia": "or-IN",  # Odia alias
        "bn": "bn-IN",
        "ta": "ta-IN",
        "te": "te-IN",
        "gu": "gu-IN",
        "kn": "kn-IN",
        "ml": "ml-IN",
        "pa": "pa-IN",
        "ur": "ur-IN",
    }
    return short_to_full.get(lang, lang)


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


def transcribe_audio_google(
    input_path: str,
    language: str | None = None,
    diarize: bool = False,
    min_speakers: Optional[int] = None,
    max_speakers: Optional[int] = None,
    chunk_secs: int = 58,
) -> Tuple[str, Optional[int]]:
    """Transcribe an audio file using Google Cloud Speech-to-Text.

    - ALWAYS converts audio to normalized WAV mono @ 16kHz first
    - Returns plain text transcript
    """
    language_code = _normalize_language_code(language)

    # 1. ALWAYS convert to normalized WAV first
    wav_path = convert_to_wav_mono_16k(input_path)
    
    with wave.open(wav_path, "rb") as w:
        sample_rate = w.getframerate()
        nframes = w.getnframes()
        duration_sec = nframes / float(sample_rate)

    # Initialize Google Cloud Speech Client
    client = speech.SpeechClient()

    def _recognize_bytes(audio_bytes: bytes, sample_rate: int) -> Tuple[list[str], Set[int], List[str]]:
        audio = speech.RecognitionAudio(content=audio_bytes)
        diarization_cfg = None
        if diarize:
            if min_speakers is None and max_speakers is None:
                min_speakers_local = 2
                max_speakers_local = 4
            else:
                min_speakers_local = min_speakers
                max_speakers_local = max_speakers
            diarization_cfg = speech.SpeakerDiarizationConfig()
            diarization_cfg.enable_speaker_diarization = True
            if min_speakers_local is not None:
                diarization_cfg.min_speaker_count = min_speakers_local
            if max_speakers_local is not None:
                diarization_cfg.max_speaker_count = max_speakers_local

        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate,
            language_code=language_code,
            enable_automatic_punctuation=True,
            enable_word_time_offsets=diarize,
            diarization_config=diarization_cfg,
        )
        response = client.recognize(config=config, audio=audio)
        parts: list[str] = []
        speaker_tags: Set[int] = set()
        diarized_lines: List[str] = []
        for result in response.results:
            if result.alternatives:
                alt = result.alternatives[0]
                parts.append(alt.transcript)
                if diarize and hasattr(alt, "words") and alt.words:
                    current_tag = None
                    current_words: List[str] = []
                    for w in alt.words:
                        tag = getattr(w, "speaker_tag", 0)
                        word_text = getattr(w, "word", "")
                        if tag:
                            speaker_tags.add(int(tag))
                        if current_tag is None:
                            current_tag = tag or 0
                            current_words = [word_text]
                        elif tag == current_tag:
                            current_words.append(word_text)
                        else:
                            label = f"Person {current_tag}" if current_tag else "Person"
                            diarized_lines.append(f"{label}: {' '.join(current_words).strip()}")
                            current_tag = tag or 0
                            current_words = [word_text]
                    if current_words:
                        label = f"Person {current_tag}" if current_tag else "Person"
                        diarized_lines.append(f"{label}: {' '.join(current_words).strip()}")
        return parts, speaker_tags, diarized_lines

    if duration_sec >= float(chunk_secs):
        transcripts: list[str] = []
        all_speaker_tags: Set[int] = set()
        with wave.open(wav_path, "rb") as w:
            channels = w.getnchannels()
            sampwidth = w.getsampwidth()
            framerate = w.getframerate()
            chunk_frames = int(framerate * chunk_secs)
            total_frames = w.getnframes()
            frames_read = 0

            while frames_read < total_frames:
                frames_to_read = min(chunk_frames, total_frames - frames_read)
                chunk_data = w.readframes(frames_to_read)
                frames_read += frames_to_read

                buf = io.BytesIO()
                with wave.open(buf, "wb") as out_wav:
                    out_wav.setnchannels(channels)
                    out_wav.setsampwidth(sampwidth)
                    out_wav.setframerate(framerate)
                    out_wav.writeframes(chunk_data)
                audio_bytes = buf.getvalue()

                parts, tags, diar_lines = _recognize_bytes(audio_bytes, framerate)
                if diarize and diar_lines:
                    transcripts.append("\n".join(diar_lines))
                elif parts:
                    transcripts.append(" ".join(parts))
                all_speaker_tags |= tags

        final_text = "\n".join(t.strip() for t in transcripts if t.strip())
        detected_count = len(all_speaker_tags) if diarize else None
        return final_text, detected_count
    else:
        with open(wav_path, "rb") as f:
            content = f.read()
        parts, tags, diar_lines = _recognize_bytes(content, sample_rate)
        if diarize and diar_lines:
            final_text = "\n".join(diar_lines)
        else:
            final_text = "\n".join(t.strip() for t in parts if t.strip())
        detected_count = len(tags) if diarize else None
        return final_text, detected_count

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transcribe audio to text.")
    parser.add_argument("--input", required=True, help="Path to audio file")
    parser.add_argument("--lang", default="en-US", help="Language code (en, hi, mr, etc.)")
    parser.add_argument("--diarize", action="store_true", help="Enable speaker diarization")
    args = parser.parse_args()

    try:
        text, speaker_count = transcribe_audio_google(args.input, language=args.lang, diarize=args.diarize)
        print("--- Transcript ---")
        print(text)
        if speaker_count is not None:
            print(f"--- Detected {speaker_count} speakers ---")
    except Exception as e:
        print(f"Error: {e}")
