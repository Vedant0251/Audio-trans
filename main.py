import argparse
import os
import json
from pathlib import Path
from datetime import datetime
from asr import transcribe_audio_whisper
from translator import translate_text
from evaluator import StartupEvaluator
from bmc import generate_bmc_dict, generate_bmc_png

def process_audio(file_path: str, language: str = "hi", translate: bool = True, model_size: str = "base", output_dir: str = "transcripts", evaluate: bool = True):
    """Full pipeline: ASR -> Optional Translation -> Save to File -> Evaluate Business Idea."""
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        return

    print(f"--- Processing: {file_path} ---")
    
    # Create output directory
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    base_name = Path(file_path).stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    transcript_file = out_path / f"{base_name}_{timestamp}_transcript.txt"
    report_file = out_path / f"{base_name}_{timestamp}_report.txt"
    bmc_png_file = out_path / f"{base_name}_{timestamp}_bmc.png"
    bmc_json_file = out_path / f"{base_name}_{timestamp}_bmc.json"

    # 1. Transcribe audio (ASR)
    print(f"Transcribing (Language: {language}, Model: {model_size})...")
    try:
        transcript, speaker_count = transcribe_audio_whisper(file_path, language=language, model_size=model_size)
        
        print("\n--- Original Transcript ---")
        print(transcript)
        
        # Prepare content to save
        file_content = [f"Source File: {file_path}", f"Language: {language}", f"Time: {timestamp}", "-" * 20, "ORIGINAL TRANSCRIPT:", transcript, "-" * 20]

        final_text = transcript

        # 2. Translate if requested and language is not English
        if translate and language.lower() not in ["en", "en-us"]:
            print(f"\nTranslating to English...")
            final_text = translate_text(transcript, source_lang=language, target_lang="en")
            print("\n--- Translated (English) ---")
            print(final_text)
            
            file_content.extend(["ENGLISH TRANSLATION:", final_text, "-" * 20])
            
        # Save transcript to file
        transcript_file.write_text("\n".join(file_content), encoding="utf-8")
        print(f"\nSuccess! Transcript saved to: {transcript_file}")

        if evaluate:
            print("\n--- Generating Business Model Canvas (BMC) ---")
            bmc_dict = generate_bmc_dict(final_text)
            with open(bmc_json_file, 'w', encoding='utf-8') as f:
                json.dump(bmc_dict, f, ensure_ascii=False, indent=2)
            generate_bmc_png(str(bmc_png_file), "Business Model Canvas", bmc_dict)
            print(f"BMC saved to: {bmc_png_file}")

            print("\n--- Evaluating Business Idea ---")
            evaluator = StartupEvaluator()
            results = evaluator.evaluate_idea(final_text)
            
            # Save evaluation report to file
            evaluator.save_to_file(results, final_text, output_dir=output_dir)
            
            return transcript, final_text, results, bmc_dict

        return transcript, None, None, None
        
    except Exception as e:
        print(f"Error in processing: {e}")
        return None, None, None, None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audio to Text Translation and Evaluation Pipeline.")
    parser.add_argument("--input", required=True, help="Path to audio file (wav, mp3, m4a, etc.)")
    parser.add_argument("--lang", default="hi", help="Language code (hi, mr, or, etc.)")
    parser.add_argument("--model", default="base", help="Whisper model size (tiny, base, small, medium, large)")
    parser.add_argument("--no-translate", action="store_true", help="Disable translation to English")
    parser.add_argument("--no-evaluate", action="store_true", help="Disable business idea evaluation")
    
    args = parser.parse_args()
    
    process_audio(args.input, language=args.lang, translate=not args.no_translate, model_size=args.model, evaluate=not args.no_evaluate)
