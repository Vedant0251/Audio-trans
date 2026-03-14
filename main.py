import argparse
import os
from pathlib import Path
from asr import transcribe_audio_google
from translator import translate_text

def process_audio(file_path: str, language: str = "hi", translate: bool = True):
    """Full pipeline: ASR -> Optional Translation."""
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        return

    print(f"--- Processing: {file_path} ---")
    
    # 1. Transcribe audio (ASR)
    print(f"Transcribing (Language: {language})...")
    try:
        transcript, speaker_count = transcribe_audio_google(file_path, language=language)
        
        print("\n--- Original Transcript ---")
        print(transcript)
        
        if speaker_count is not None:
            print(f"Detected {speaker_count} speakers.")
            
        # 2. Translate if requested and language is not English
        if translate and language.lower() not in ["en", "en-us"]:
            print(f"\nTranslating to English...")
            translated_text = translate_text(transcript, source_lang=language, target_lang="en")
            print("\n--- Translated (English) ---")
            print(translated_text)
            
            return transcript, translated_text
        
        return transcript, None
        
    except Exception as e:
        print(f"Error in processing: {e}")
        return None, None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audio to Text Translation Pipeline.")
    parser.add_argument("--input", required=True, help="Path to audio file (wav, mp3, m4a, etc.)")
    parser.add_argument("--lang", default="hi", help="Language code (hi, mr, or, etc.)")
    parser.add_argument("--no-translate", action="store_true", help="Disable translation to English")
    
    args = parser.parse_args()
    
    process_audio(args.input, language=args.lang, translate=not args.no_translate)
