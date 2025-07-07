from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import whisper
import tempfile
import os
from typing import Optional
import logging
from datetime import datetime
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Medical Interpreter API",
    description="AI-powered medical interpretation service",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Whisper model (consider moving to startup event for better performance)
model = whisper.load_model("base")

# Pydantic models for request/response validation
class TranslationRequest(BaseModel):
    text: str
    source_language: str = "auto"
    target_language: str = "en"
    medical_context: Optional[str] = None

class TranslationResponse(BaseModel):
    original_text: str
    translated_text: str
    confidence: Optional[float] = None
    medical_terms: Optional[list] = None
    session_id: str

class TranscriptionResponse(BaseModel):
    text: str
    language: Optional[str] = None
    confidence: Optional[float] = None
    session_id: str

# In-memory session storage (replace with Redis/DB later)
sessions = {}

@app.get("/")
async def root():
    return {
        "message": "Medical Interpreter API is running",
        "version": "1.0.0",
        "endpoints": ["/speech-to-text", "/translate", "/health"]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "whisper_model": "base"
    }

@app.post("/speech-to-text", response_model=TranscriptionResponse)
async def speech_to_text(
    file: UploadFile = File(...),
    session_id: Optional[str] = None
):
    """
    Convert speech to text using Whisper
    """
    try:
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Validate file type
        if not file.content_type.startswith("audio/"):
            raise HTTPException(
                status_code=400, 
                detail="File must be audio format"
            )
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Transcribe
        logger.info(f"Transcribing audio for session {session_id}")
        result = model.transcribe(tmp_path)
        
        # Clean up
        os.remove(tmp_path)
        
        # Store in session
        if session_id not in sessions:
            sessions[session_id] = []
        
        sessions[session_id].append({
            "type": "transcription",
            "timestamp": datetime.now().isoformat(),
            "original_text": result["text"],
            "language": result.get("language", "unknown")
        })
        
        return TranscriptionResponse(
            text=result["text"],
            language=result.get("language"),
            confidence=result.get("confidence"),
            session_id=session_id
        )
        
    except Exception as e:
        logger.error(f"Error in speech-to-text: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/translate", response_model=TranslationResponse)
async def translate_text(request: TranslationRequest):
    """
    Translate text with medical context awareness
    """
    try:
        session_id = str(uuid.uuid4())
        
        # Simple translation logic using deep-translator
        try:
            from deep_translator import GoogleTranslator
            
            # Auto-detect source language or use specified
            if request.source_language == "auto":
                # Use GoogleTranslator's auto-detect
                translator = GoogleTranslator(source='auto', target=request.target_language)
            else:
                translator = GoogleTranslator(source=request.source_language, target=request.target_language)
            
            translated_text = translator.translate(request.text)
            confidence = 0.95  # GoogleTranslator doesn't provide confidence scores
            
        except ImportError:
            # Fallback if deep-translator not installed
            translated_text = f"[TRANSLATION PLACEHOLDER] {request.text}"
            confidence = 0.0
        except Exception as translation_error:
            logger.warning(f"Translation failed: {translation_error}")
            translated_text = f"[TRANSLATION FAILED] {request.text}"
            confidence = 0.0
        
        # Medical term extraction
        medical_terms = extract_medical_terms(request.text)
        
        # Store in session
        if session_id not in sessions:
            sessions[session_id] = []
            
        sessions[session_id].append({
            "type": "translation",
            "timestamp": datetime.now().isoformat(),
            "original_text": request.text,
            "translated_text": translated_text,
            "source_language": request.source_language,
            "target_language": request.target_language,
            "medical_context": request.medical_context
        })
        
        return TranslationResponse(
            original_text=request.text,
            translated_text=translated_text,
            confidence=confidence,
            medical_terms=medical_terms,
            session_id=session_id
        )
        
    except Exception as e:
        logger.error(f"Error in translation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """
    Retrieve session history
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "history": sessions[session_id]
    }

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    Delete session for privacy compliance
    """
    if session_id in sessions:
        del sessions[session_id]
        return {"message": "Session deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")

def extract_medical_terms(text: str) -> list:
    """
    Extract medical terms from text
    TODO: Implement proper medical NLP
    """
    # Placeholder medical terms
    common_medical_terms = [
        "dolor", "pain", "fiebre", "fever", "presión", "pressure",
        "corazón", "heart", "pulmón", "lung", "estómago", "stomach"
    ]
    
    found_terms = []
    text_lower = text.lower()
    
    for term in common_medical_terms:
        if term in text_lower:
            found_terms.append(term)
    
    return found_terms

# Startup event to load models
@app.on_event("startup")
async def startup_event():
    logger.info("Medical Interpreter API starting up...")
    logger.info(f"Whisper model loaded: {model}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)