import React, { useState, useRef } from 'react';
import {
  UploadCloud, FileAudio, X, Volume2, Globe, Languages, Wand2, Copy, Check, ChevronDown, Loader2, FileText, ArrowRight
} from 'lucide-react';
import './App.css';

const MODELS = [
  { id: 'tiny', name: 'Tiny (Fastest)' },
  { id: 'base', name: 'Base (Balanced)' },
  { id: 'small', name: 'Small (Accurate)' },
  { id: 'medium', name: 'Medium (High Accuracy)' },
  { id: 'large', name: 'Large (Best Quality)' }
];

export default function App() {
  const [file, setFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [model, setModel] = useState('base');
  
  const [step, setStep] = useState(1);
  const [isProcessing, setIsProcessing] = useState(false);
  
  const [transcript, setTranscript] = useState('');
  const [detectedLanguage, setDetectedLanguage] = useState('');
  const [translatedText, setTranslatedText] = useState('');
  const [bmc, setBmc] = useState(null);
  const [evaluation, setEvaluation] = useState(null);

  const [copiedTranscript, setCopiedTranscript] = useState(false);
  const [copiedTranslation, setCopiedTranslation] = useState(false);
  
  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault(); e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true);
    else if (e.type === 'dragleave') setDragActive(false);
  };

  const handleDrop = (e) => {
    e.preventDefault(); e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) handleFile(e.target.files[0]);
  };

  const handleFile = (selectedFile) => {
    if (selectedFile.type.startsWith('audio/') || selectedFile.name.match(/\.(wav|mp3|m4a|ogg)$/i)) {
      setFile(selectedFile);
      setStep(1); setTranscript(''); setTranslatedText(''); setBmc(null); setEvaluation(null);
    } else {
      alert("Please upload an audio file (wav, mp3, m4a).");
    }
  };

  const triggerSelect = () => {
    if (fileInputRef.current) fileInputRef.current.click();
  };

  const removeFile = () => {
    setFile(null);
    setStep(1); setTranscript(''); setTranslatedText(''); setBmc(null); setEvaluation(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const formatSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024; const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getLanguageName = (code) => {
    const map = {hi: 'Hindi', en: 'English'};
    return map[code] || code;
  };

  const copyToClipboard = (text, isTranslation) => {
    navigator.clipboard.writeText(text);
    if (isTranslation) {
      setCopiedTranslation(true); setTimeout(() => setCopiedTranslation(false), 2000);
    } else {
      setCopiedTranscript(true); setTimeout(() => setCopiedTranscript(false), 2000);
    }
  };

  const handleTranscribe = async () => {
    if (!file) return;
    setIsProcessing(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('model_size', model);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/process', { method: 'POST', body: formData });
      const data = await response.json();
      if (response.ok && data.status === 'success') {
        setTranscript(data.transcript);
        setDetectedLanguage(data.detected_language);
        setStep(2);
      } else {
        alert('Transcription Failed: ' + (data.detail || data.message || 'Unknown Error'));
      }
    } catch (error) {
      alert('Network Error. Is the backend server running?');
    } finally { setIsProcessing(false); }
  };

  const handleTranslate = async () => {
    setIsProcessing(true);
    try {
      const response = await fetch('http://127.0.0.1:8000/api/translate', { 
        method: 'POST', 
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({text: transcript, detected_lang: detectedLanguage})
      });
      const data = await response.json();
      if (response.ok && data.status === 'success') {
        setTranslatedText(data.translated_text);
        setStep(3);
      } else alert('Translation Failed: ' + data.detail);
    } catch (error) { alert('Network Error.'); } 
    finally { setIsProcessing(false); }
  };

  const handleGenerateBMC = async () => {
    setIsProcessing(true);
    const textToUse = translatedText || transcript;
    try {
      const response = await fetch('http://127.0.0.1:8000/api/generate_bmc', { 
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({text: textToUse})
      });
      const data = await response.json();
      if (response.ok && data.status === 'success') {
        setBmc(data.bmc);
        setStep(4);
      } else alert('BMC Generation Failed: ' + data.detail);
    } catch (error) { alert('Network Error.'); } 
    finally { setIsProcessing(false); }
  };

  const handleEvaluate = async () => {
    setIsProcessing(true);
    const textToUse = translatedText || transcript;
    try {
      const response = await fetch('http://127.0.0.1:8000/api/evaluate', { 
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({text: textToUse})
      });
      const data = await response.json();
      if (response.ok && data.status === 'success') {
        setEvaluation(data.evaluation);
        setStep(5);
      } else alert('Evaluation Failed: ' + data.detail);
    } catch (error) { alert('Network Error.'); } 
    finally { setIsProcessing(false); }
  };

  return (
    <div className="app-container">
      <div className="header">
        <h1><Wand2 className="header-icon" /> Audio-Trans <span style={{fontWeight: 300, opacity: 0.5}}>|</span> AI</h1>
        <p>Step-by-Step AI Pitch Evaluation</p>
      </div>

      {!file ? (
        <div 
          className={`upload-zone ${dragActive ? 'drag-active' : ''}`}
          onDragEnter={handleDrag} onDragLeave={handleDrag} onDragOver={handleDrag}
          onDrop={handleDrop} onClick={triggerSelect}
        >
          <input type="file" ref={fileInputRef} onChange={handleChange} accept="audio/*" style={{ display: 'none' }} />
          <UploadCloud className="upload-icon" />
          <div className="upload-text">Click to upload or drag & drop</div>
          <div className="upload-subtext">Supports WAV, MP3, M4A up to 50MB</div>
        </div>
      ) : (
        <div className="file-selected">
          <div className="file-info">
            <div className="file-icon"><FileAudio size={32} /></div>
            <div>
              <div className="file-name">{file.name}</div>
              <div className="file-size">{formatSize(file.size)}</div>
            </div>
          </div>
          <button className="remove-file" onClick={removeFile} title="Remove file"><X size={20} /></button>
        </div>
      )}

      {file && step === 1 && (
        <div className="step-container" style={{marginTop: '2rem'}}>
          <div className="controls-grid" style={{marginBottom: '1rem'}}>
            <div className="control-group">
              <label>Whisper Model</label>
              <div className="select-wrapper">
                <select className="custom-select" value={model} onChange={(e) => setModel(e.target.value)}>
                  {MODELS.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
                </select>
                <ChevronDown className="select-icon" size={18} />
              </div>
            </div>
          </div>
          <button className="submit-btn" onClick={handleTranscribe} disabled={isProcessing}>
            {isProcessing ? <><Loader2 className="loading-spinner" size={22} /> Transcribing...</> : <><Volume2 size={22} /> Step 1: Transcribe Audio</>}
          </button>
        </div>
      )}

      {step >= 2 && transcript && (
        <div className="results-section" style={{marginTop: '2rem'}}>
          <div className="result-card">
            <div className="result-header">
              <div className="result-title"><FileText size={18} className="file-icon" /> Original Transcript <span style={{fontSize: '0.85rem', marginLeft: '10px', color: 'var(--text-secondary)', fontWeight: 'normal'}}>Auto-detected: {getLanguageName(detectedLanguage)}</span></div>
              <button className="copy-btn" onClick={() => copyToClipboard(transcript, false)}>
                {copiedTranscript ? <><Check size={16} /> Copied</> : <><Copy size={16} /> Copy</>}
              </button>
            </div>
            <div className="result-content">{transcript}</div>
          </div>
          
          {step === 2 && (
             <div style={{display: 'flex', gap: '15px', marginTop: '1rem'}}>
               <button className="submit-btn" style={{backgroundColor: 'var(--accent-secondary)', flex: 1}} onClick={handleTranslate} disabled={isProcessing}>
                 {isProcessing ? <><Loader2 className="loading-spinner" size={22} /> Translating...</> : <><Globe size={22} /> Step 2: Auto-Translate (Hi ↔ En)</>}
               </button>
               <button className="submit-btn" style={{backgroundColor: 'transparent', border: '1px solid var(--border-color)', color: 'var(--text-primary)', flex: 1}} onClick={() => setStep(3)} disabled={isProcessing}>
                 Skip Translate <ArrowRight size={18} />
               </button>
             </div>
          )}
        </div>
      )}

      {step >= 3 && (
        <div className="results-section" style={{marginTop: '2rem'}}>
          {translatedText && (
            <div className="result-card">
              <div className="result-header">
                <div className="result-title"><Languages size={18} style={{color: 'var(--success)'}} /> Auto-Translation</div>
                <button className="copy-btn" onClick={() => copyToClipboard(translatedText, true)}>
                  {copiedTranslation ? <><Check size={16} /> Copied</> : <><Copy size={16} /> Copy</>}
                </button>
              </div>
              <div className="result-content">{translatedText}</div>
            </div>
          )}

          {step === 3 && (
             <button className="submit-btn" style={{marginTop: '1rem', backgroundColor: 'var(--accent-secondary)'}} onClick={handleGenerateBMC} disabled={isProcessing}>
               {isProcessing ? <><Loader2 className="loading-spinner" size={22} /> Generating BMC...</> : <><FileText size={22} /> Step 3: Generate Business Canvas</>}
             </button>
          )}
        </div>
      )}

      {step >= 4 && bmc && (
        <div className="report-section" style={{ marginTop: '2rem', padding: '1.5rem', backgroundColor: 'var(--surface-color)', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
          <h3 style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '10px' }}>Business Model Canvas</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '15px', marginTop: '15px' }}>
            {Object.entries(bmc).map(([key, items]) => (
              <div key={key} style={{ backgroundColor: 'var(--bg-color)', padding: '15px', borderRadius: '8px' }}>
                <h4 style={{ margin: '0 0 10px 0', fontSize: '0.9rem', color: 'var(--text-primary)' }}>{key}</h4>
                <ul style={{ margin: 0, paddingLeft: '15px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  {items.map((item, idx) => <li key={idx} style={{marginBottom: '4px'}}>{item}</li>)}
                </ul>
              </div>
            ))}
          </div>

          {step === 4 && (
             <button className="submit-btn" style={{marginTop: '2rem', backgroundColor: 'var(--accent-primary)'}} onClick={handleEvaluate} disabled={isProcessing}>
               {isProcessing ? <><Loader2 className="loading-spinner" size={22} /> Evaluating...</> : <><Wand2 size={22} /> Step 4: Fast Evaluate Pitch</>}
             </button>
          )}
        </div>
      )}

      {step >= 5 && evaluation && (
        <div className="report-section" style={{ marginTop: '2rem', padding: '1.5rem', backgroundColor: 'var(--surface-color)', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
          <h2><Wand2 size={24} style={{ color: 'var(--accent-primary)', marginRight: '10px' }} /> Pitch Final Verdict</h2>
          <div style={{ marginTop: '20px' }}>
            <div style={{ display: 'flex', gap: '2rem', alignItems: 'center', marginTop: '1rem' }}>
              <div style={{ padding: '1.5rem', borderRadius: '12px', backgroundColor: evaluation.verdict === 'GO' ? 'rgba(40, 167, 69, 0.1)' : evaluation.verdict === 'NO-GO' ? 'rgba(239,68,68,0.1)' : 'rgba(255, 193, 7, 0.1)', flex: 1 }}>
                <h1 style={{ color: evaluation.verdict === 'GO' ? '#28a745' : evaluation.verdict === 'NO-GO' ? '#ef4444' : '#ffc107', margin: 0 }}>{evaluation.verdict}</h1>
                <p style={{ margin: '10px 0 0 0', color: 'var(--text-secondary)' }}>Recommendation</p>
              </div>
              <div style={{ flex: 2 }}>
                <div style={{ marginBottom: '10px' }}>
                  <strong>Overall Score: </strong> 
                  <span style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--accent-primary)' }}>
                    {(() => { const vals = Object.values(evaluation.scores || {}); return vals.length > 0 ? (vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(1) : 'N/A'; })()} / 10
                  </span>
                </div>
                <div>
                  <strong>Key Strengths:</strong>
                  <ul style={{ paddingLeft: '20px', marginTop: '5px' }}>
                    {(evaluation.strengths || []).map((str, idx) => <li key={idx}>{str}</li>)}
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
