import os
import shutil
import json
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from asr import transcribe_audio_whisper
from translator import translate_text
from evaluator import StartupEvaluator
from bmc import generate_bmc_dict

app = FastAPI(title="Audio-Trans AI API", version="1.0.0")

# Setup CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production ready: restrict this to specific origins later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
TRANSCRIPTS_DIR = Path("transcripts")
TRANSCRIPTS_DIR.mkdir(exist_ok=True)

@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "Audio-Trans API is running successfully"}

from pydantic import BaseModel

class TranslateRequest(BaseModel):
    text: str
    detected_lang: str

class TextRequest(BaseModel):
    text: str

@app.post("/api/process")
async def process_audio(
    file: UploadFile = File(...),
    model_size: str = Form("base")
):
    try:
        # Validate file type
        valid_extensions = (".wav", ".mp3", ".m4a", ".ogg")
        if not file.filename.lower().endswith(valid_extensions):
            raise HTTPException(status_code=400, detail="Invalid audio file format")

        # Save uploaded file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = file.filename.replace(" ", "_").lower()
        file_path = UPLOAD_DIR / f"{timestamp}_{safe_filename}"
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 1. Transcribe Audio (Language Auto-Detect)
        try:
            transcript, detected_lang = transcribe_audio_whisper(str(file_path), language=None, model_size=model_size)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Transcription Failed: {str(e)}")
            
        if not detected_lang:
            detected_lang = 'en' # Fallback
            
        allowed_langs = ['en', 'hi', 'english', 'hindi']
        if detected_lang.lower() not in allowed_langs:
            raise HTTPException(status_code=400, detail=f"Only Hindi and English are supported. Detected language '{detected_lang}'. Please use only these 2 languages.")

        # Try to clean up the uploaded file to save disk space
        try:
            os.remove(file_path)
        except:
            pass

        return {
            "status": "success",
            "message": "Audio processed successfully",
            "detected_language": detected_lang,
            "transcript": transcript
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/translate")
def translate_api(req: TranslateRequest):
    try:
        if req.detected_lang.lower() in ['hi', 'hindi']:
            translated_text = translate_text(req.text, source_lang='hi', target_lang='en')
        else:
            translated_text = translate_text(req.text, source_lang='en', target_lang='hi')
        return {"status": "success", "translated_text": translated_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation Failed: {str(e)}")

@app.post("/api/generate_bmc")
def generate_bmc_api(req: TextRequest):
    try:
        bmc_data = generate_bmc_dict(req.text)
        return {"status": "success", "bmc": bmc_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"BMC Generation Failed: {str(e)}")

@app.post("/api/evaluate")
def evaluate_api(req: TextRequest):
    try:
        evaluator = StartupEvaluator()
        evaluation_data = evaluator.evaluate_idea(req.text)
        return {"status": "success", "evaluation": evaluation_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation Failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
