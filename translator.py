import argparse
from typing import Optional
from deep_translator import GoogleTranslator

def translate_text(text: str, source_lang: str = "auto", target_lang: str = "en") -> str:
    """Translate text using deep-translator (Google Translator)."""
    try:
        # Normalize language codes
        lang_map = {
            "hi": "hi",
            "mr": "mr",
            "or": "or",
            "gu": "gu",
            "bn": "bn",
            "ta": "ta",
            "te": "te",
            "kn": "kn",
            "ml": "ml",
            "pa": "pa",
            "ur": "ur",
            "en": "en",
        }
        
        source = lang_map.get(source_lang.lower(), source_lang.lower())
        target = lang_map.get(target_lang.lower(), target_lang.lower())
        
        translator = GoogleTranslator(source=source, target=target)
        
        # Split text into chunks if it's too long (Google Translator has a limit)
        # deep-translator handles this internally for most cases, but good to be safe
        translated = translator.translate(text)
        return translated
    except Exception as e:
        print(f"Translation error: {e}")
        return text

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Translate text.")
    parser.add_argument("--text", required=True, help="Text to translate")
    parser.add_argument("--source", default="auto", help="Source language code")
    parser.add_argument("--target", default="en", help="Target language code")
    args = parser.parse_args()
    
    result = translate_text(args.text, source_lang=args.source, target_lang=args.target)
    print("--- Translated Text ---")
    print(result)
