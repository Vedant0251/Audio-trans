# Audio-Trans AI Pipeline 🚀

Welcome to **Audio-Trans AI Pipeline**, an intelligent full-stack project that transforms spoken audio into text, translates it seamlessly, evaluates business ideas using an LLM, and generates a Business Model Canvas (BMC). 

This tool is designed for founders, entrepreneurs, and note-takers to immediately analyze their audio recordings, translating regional languages and returning actionable startup insights.

## ✨ Features

- **Local Speech-to-Text (ASR):** Uses **OpenAI Whisper** for local, free, and accurate transcription.
- **Auto-Translation:** Translates Hindi/Regional languages to English or English to Hindi using `deep-translator`.
- **Startup Idea Evaluator:** Evaluates pitch/audio transcripts leveraging LLMs (Google Generative AI) to provide constructive feedback, pros/cons, and next steps for the business idea.
- **Business Model Canvas Generator (BMC):** Automatically structure your transcript into a standard JSON/PNG Business Model Canvas.
- **Robust Backend APIs:** Fully functional REST APIs powered by **FastAPI**.
- **Interactive Frontend UI:** A modern web client built with **React** and **Vite**.

---

## 🛠️ Tech Stack

### **Backend**
- **Python 3.10+**
- **FastAPI / Uvicorn:** For high-performance backend serving and API management.
- **OpenAI Whisper:** Locally run ASR inference.
- **Google Generative AI (Gemini):** Used for idea evaluation and intelligence.
- **Deep Translator:** Open-source translation support.

### **Frontend**
- **React (Vite)**
- **Tailwind CSS / Vanilla CSS**
- **Axios** (for API communication)

---

## ⚙️ Installation & Setup

### 1. Prerequisites
- **Python 3.10+** (A virtual environment is recommended)
- **Node.js** (v16+)
- **FFmpeg** (Required by `pydub` and `whisper` to process audio files)

### 2. Backend Setup
Navigate to the root directory and install Python dependencies:
```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your Google Gemini API Key and other necessary keys.
```

### 3. Frontend Setup
Navigate to the `frontend` directory:
```bash
cd frontend
npm install
```

---

## 🚀 Usage

### Option A: Running the Web Application (Recommended)

1. **Start the Backend Server (FastAPI):**
   ```bash
   python app.py
   ```
   > The API server will start on `http://localhost:8000`. Swagger UI is available at `http://localhost:8000/docs`.

2. **Start the Frontend Application:**
   ```bash
   cd frontend
   npm run dev
   ```
   > The web app will be accessible via `http://localhost:5173`.

### Option B: Running the CLI Pipeline

You can run the full toolchain directly from your terminal using `main.py`.

```bash
python main.py --input audio/sample_hindi.wav --lang hi --model base
```

**CLI Flags:**
- `--input`: Path to the audio file (required).
- `--lang`: Language code (`hi`, `en`, `mr`, etc., default: `hi`).
- `--model`: Whisper model size (`tiny`, `base`, `small`, `medium`, `large`). default: `base`.
- `--no-translate`: Disable translation to English.
- `--no-evaluate`: Disable business idea evaluation and BMC generation.

### Individual Python Modules
- **Transcribe only:** `python asr.py --input audio/sample.wav --lang hi`
- **Translate only:** `python translator.py --text "नमस्ते" --source hi --target en`

---

## 📡 API Endpoints

The FastAPI backend exposes the following key endpoints:

- `GET /api/health` - Check if the API is running.
- `POST /api/process` - Upload an audio file, returns transcript & detected language.
- `POST /api/translate` - Translates text between Hindi and English.
- `POST /api/generate_bmc` - Returns a JSON Business Model Canvas representation of an idea.
- `POST /api/evaluate` - Evaluates a startup idea from text and returns actionable insights.

---

## 📂 Project Structure

```
Audio-trans/
├── app.py                # FastAPI web server and endpoints
├── main.py               # CLI tool for full pipeline execution
├── asr.py                # Whisper ASR transcription logic
├── translator.py         # Text translation utilities
├── evaluator.py          # Startup evaluation logic (Gemini)
├── bmc.py                # Business Model Canvas (BMC) generator
├── requirements.txt      # Python dependencies
├── .env.example          # Environment variables template
├── frontend/             # React (Vite) web application
│   ├── src/              # UI components and pages
│   ├── package.json      # Node dependencies
│   └── vite.config.js    # Vite configuration
├── audio/                # Source audio files (Sample inputs)
├── transcripts/          # Output textual transcripts and reports
└── uploads/              # Temporary audio uploads folder
```

---

## 🌍 Supported Languages (Speech-to-Text)
The local Whisper setup natively supports multiple languages including, but not limited to:
English (`en`), Hindi (`hi`), Marathi (`mr`), Odia (`or`), Gujarati (`gu`), Bengali (`bn`), Tamil (`ta`), Telugu (`te`), Kannada (`kn`), Malayalam (`ml`), Punjabi (`pa`), Urdu (`ur`).
