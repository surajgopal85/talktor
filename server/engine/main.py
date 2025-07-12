from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import whisper
import tempfile
import os
from typing import Optional, List, Dict
import logging
from datetime import datetime
import uuid

# from medical_intelligence import medical_intelligence, MedicalCategory
from external_medical_intelligence import scalable_medical_intelligence, MedicalSpecialty, enhanced_medication_lookup, get_specialty_context_suggestions

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

# New Pydantic models for medical responses
class MedicalTerm(BaseModel):
    original_text: str
    canonical_name: str
    category: str
    confidence: float
    translation: str
    context_clues: List[str]

class MedicalNote(BaseModel):
    term: str
    category: str
    translation: str
    note: str

class EnhancedTranslationResponse(BaseModel):
    original_text: str
    standard_translation: str
    enhanced_translation: str
    medical_terms: List[MedicalTerm]
    medical_notes: List[MedicalNote]
    follow_up_questions: List[str]
    medical_accuracy_score: float
    confidence: float
    session_id: str

class MedicalTranscriptionResponse(BaseModel):
    text: str
    language: Optional[str] = None
    confidence: Optional[float] = None
    medical_terms: List[Dict]
    follow_up_questions: List[str]
    medical_context_detected: str
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

# Add this to your existing server/engine/main.py

# Enhanced translation endpoint with medical intelligence
@app.post("/translate/medical", response_model=EnhancedTranslationResponse)
async def medical_translate(request: TranslationRequest):
    """
    Enhanced translation with medical intelligence
    """
    try:
        session_id = str(uuid.uuid4())
        
        # Step 1: Extract medical terms from original text
        medical_analysis = await enhanced_medication_lookup(request.text, request.medical_context or "general")
        
        logger.info(f"Found {len(medical_analysis)} medical terms: {[t['canonical_name'] for t in medical_analysis]}")
        
        # Step 2: Standard translation
        try:
            from deep_translator import GoogleTranslator
            
            if request.source_language == "auto":
                translator = GoogleTranslator(source='auto', target=request.target_language)
            else:
                translator = GoogleTranslator(source=request.source_language, target=request.target_language)
            
            standard_translation = translator.translate(request.text)
            
        except Exception as translation_error:
            logger.warning(f"Translation failed: {translation_error}")
            standard_translation = f"[TRANSLATION FAILED] {request.text}"
        
        # Step 3: Enhance translation with medical intelligence
        enhanced_result = medical_intelligence.enhance_translation(
            original_text=request.text,
            translated_text=standard_translation,
            source_lang=request.source_language,
            target_lang=request.target_language
        )
        
        # Step 4: Generate follow-up questions
        follow_up_questions = medical_intelligence.suggest_follow_up_questions(
            enhanced_result["medical_terms_found"],
            request.medical_context or "general"
        )
        
        # Step 5: Store enhanced session data
        if session_id not in sessions:
            sessions[session_id] = []
            
        sessions[session_id].append({
            "type": "medical_translation",
            "timestamp": datetime.now().isoformat(),
            "original_text": request.text,
            "standard_translation": standard_translation,
            "enhanced_translation": enhanced_result["enhanced_translation"],
            "medical_terms": enhanced_result["medical_terms_found"],
            "medical_notes": enhanced_result["medical_notes"],
            "medical_accuracy_score": enhanced_result["medical_accuracy_score"],
            "follow_up_questions": follow_up_questions,
            "source_language": request.source_language,
            "target_language": request.target_language,
            "medical_context": request.medical_context
        })
        
        return EnhancedTranslationResponse(
            original_text=request.text,
            standard_translation=standard_translation,
            enhanced_translation=enhanced_result["enhanced_translation"],
            medical_terms=enhanced_result["medical_terms_found"],
            medical_notes=enhanced_result["medical_notes"],
            follow_up_questions=follow_up_questions,
            medical_accuracy_score=enhanced_result["medical_accuracy_score"],
            confidence=0.95,
            session_id=session_id
        )
        
    except Exception as e:
        logger.error(f"Error in medical translation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Medical term analysis endpoint
@app.post("/analyze/medical-terms")
async def analyze_medical_terms(text: str, language: str = "en"):
    """
    Analyze text for medical terminology
    """
    try:
        medical_terms = medical_intelligence.extract_medical_terms(text, language)
        
        # Categorize terms
        categorized = {
            "medications": [t for t in medical_terms if t["category"] == "medication"],
            "symptoms": [t for t in medical_terms if t["category"] == "symptom"],
            "body_parts": [t for t in medical_terms if t["category"] == "body_part"],
            "procedures": [t for t in medical_terms if t["category"] == "procedure"],
            "conditions": [t for t in medical_terms if t["category"] == "condition"]
        }
        
        return {
            "text_analyzed": text,
            "total_medical_terms": len(medical_terms),
            "categorized_terms": categorized,
            "medical_complexity_score": len(medical_terms) / max(len(text.split()), 1),
            "recommended_context": determine_medical_context(medical_terms)
        }
        
    except Exception as e:
        logger.error(f"Error analyzing medical terms: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def determine_medical_context(medical_terms: List[Dict]) -> str:
    """Determine appropriate medical context based on terms found"""
    
    # Emergency indicators
    emergency_terms = ["chest pain", "shortness_of_breath", "severe pain", "bleeding"]
    if any(term["canonical_name"] in emergency_terms for term in medical_terms):
        return "emergency"
    
    # Medication focus
    medication_count = sum(1 for term in medical_terms if term["category"] == "medication")
    if medication_count >= 2:
        return "medication_review"
    
    # Symptom assessment
    symptom_count = sum(1 for term in medical_terms if term["category"] == "symptom")
    if symptom_count >= 2:
        return "symptom_assessment"
    
    return "general"

# Enhanced speech-to-text with medical analysis
@app.post("/speech-to-text/medical", response_model=MedicalTranscriptionResponse)
async def medical_speech_to_text(
    file: UploadFile = File(...),
    session_id: Optional[str] = None,
    medical_context: Optional[str] = None
):
    """
    Enhanced speech-to-text with immediate medical analysis
    """
    try:
        # Standard STT processing (same as before)
        if not session_id:
            session_id = str(uuid.uuid4())
        
        if not file.content_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="File must be audio format")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        logger.info(f"Processing medical transcription for session {session_id}")
        result = model.transcribe(tmp_path)
        os.remove(tmp_path)
        
        # Immediate medical analysis
        # Ensure transcribed_text is always a string
        transcribed_text = result["text"]
        if isinstance(transcribed_text, list):
            transcribed_text = " ".join(transcribed_text)  # Join list into single string
        elif transcribed_text is None:
            transcribed_text = ""  # Handle None case

        medical_analysis = await enhanced_medication_lookup(transcribed_text, medical_context or "general")

        # Suggest follow-up questions
        follow_up_questions = await get_specialty_context_suggestions(
            transcribed_text, medical_context or "general"
        )
        
        # Enhanced session storage
        if session_id not in sessions:
            sessions[session_id] = []
        
        sessions[session_id].append({
            "type": "medical_transcription",
            "timestamp": datetime.now().isoformat(),
            "original_audio_language": result.get("language", "unknown"),
            "transcribed_text": transcribed_text,
            "medical_terms": medical_analysis,
            "follow_up_questions": follow_up_questions,
            "medical_context": medical_context,
            "recommended_context": determine_medical_context(medical_analysis)
        })
        
        return MedicalTranscriptionResponse(
            text=transcribed_text,
            language=result.get("language"),
            confidence=result.get("confidence"),
            medical_terms=medical_analysis,
            follow_up_questions=follow_up_questions,
            medical_context_detected=determine_medical_context(medical_analysis),
            session_id=session_id
        )
        
    except Exception as e:
        logger.error(f"Error in medical speech-to-text: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Startup event to load models
@app.on_event("startup")
async def startup_event():
    logger.info("Medical Interpreter API starting up...")
    logger.info(f"Whisper model loaded: {model}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)