# Clean main.py using service architecture pattern
# This separates concerns and makes the code much more maintainable

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import whisper
import tempfile
import os
from typing import Optional, List, Dict
import logging
from datetime import datetime
import uuid

# Service imports following your nested architecture

# no longer works in current architecture - 7.20.25
# from services.medical_intelligence.extraction import MedicationExtractionService 
from services.translation.translator import TranslationService
from services.session.manager import SessionService
from services.audio.whisper_service import WhisperService

# no longer works in current architecture - 7.20.25
# from services.medical_intelligence.learning import LearningManager

# 7.20.25 - replaced with new architecture
# NEW imports (after migration)
from services.medical_intelligence import MedicationExtractionService, LearningManager
# OR for OBGYN-specific:
from services.medical_intelligence import process_obgyn_case, extract_medications

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Talktor - Medical Interpreter API",
    description="AI-powered medical interpretation with learning intelligence",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Whisper model
model = whisper.load_model("base")

# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class TranslationRequest(BaseModel):
    text: str
    source_language: str = "auto"
    target_language: str = "en"
    medical_context: Optional[str] = None

class LearningMetadata(BaseModel):
    extraction_strategies_used: List[str]
    candidates_analyzed: int
    ready_for_feedback: bool
    confidence_scores: Dict[str, float]

class EnhancedTranslationResponse(BaseModel):
    original_text: str
    standard_translation: str
    enhanced_translation: str
    medical_terms: List[Dict]
    medical_notes: List[Dict]
    follow_up_questions: List[str]
    medical_accuracy_score: float
    confidence: float
    session_id: str
    learning_metadata: LearningMetadata

class TranscriptionResponse(BaseModel):
    text: str
    language: Optional[str] = None
    confidence: Optional[float] = None
    session_id: str

# =============================================================================
# DEPENDENCY INJECTION (Service instances)
# =============================================================================

def get_extraction_service() -> MedicationExtractionService:
    """Dependency injection for extraction service"""
    return MedicationExtractionService()

def get_translation_service() -> TranslationService:
    """Dependency injection for translation service"""
    return TranslationService()

def get_session_service() -> SessionService:
    """Dependency injection for session service"""
    return SessionService()

def get_learning_manager() -> LearningManager:
    """Dependency injection for learning/feedback service"""
    return LearningManager()

# =============================================================================
# CORE API ENDPOINTS
# =============================================================================

@app.get("/")
async def root():
    return {
        "message": "Talktor - Medical Interpreter API",
        "version": "2.0.0",
        "status": "Learning-Ready",
        "features": [
            "Multi-strategy medication extraction",
            "External API integration (RxNorm, FDA)",
            "Confidence-based learning",
            "Feedback collection for RL",
            "Service-oriented architecture"
        ],
        "endpoints": {
            "core": ["/speech-to-text", "/translate", "/translate/medical"],
            "learning": ["/feedback/extraction/{extraction_id}", "/learning/analytics/{session_id}"],
            "testing": ["/test/extraction", "/test/external-apis"],
            "health": ["/health", "/api-status"]
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "whisper_model": "base",
        "learning_system": "active",
        "services": {
            "extraction": "ready",
            "translation": "ready", 
            "session_management": "ready",
            "feedback_collection": "ready"
        }
    }

@app.post("/speech-to-text", response_model=TranscriptionResponse)
async def speech_to_text(
    file: UploadFile = File(...),
    session_id: Optional[str] = None,
    session_service: SessionService = Depends(get_session_service)
):
    """Convert speech to text using Whisper"""
    try:
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Validate file type
        if not file.content_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="File must be audio format")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Transcribe
        logger.info(f"🎤 Transcribing audio for session {session_id}")
        result = model.transcribe(tmp_path)
        
        # Clean up
        os.remove(tmp_path)
        
        # Store in session
        await session_service.store_transcription(session_id, result)
        
        return TranscriptionResponse(
            text=result["text"],
            language=result.get("language"),
            confidence=result.get("confidence"),
            session_id=session_id
        )
        
    except Exception as e:
        logger.error(f"❌ Error in speech-to-text: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/translate")
async def basic_translate(request: TranslationRequest):
    """Basic translation endpoint for backward compatibility"""
    try:
        from deep_translator import GoogleTranslator
        
        if request.source_language == "auto":
            translator = GoogleTranslator(source='auto', target=request.target_language)
        else:
            translator = GoogleTranslator(source=request.source_language, target=request.target_language)
        
        translated_text = translator.translate(request.text)
        session_id = str(uuid.uuid4())
        
        return {
            "original_text": request.text,
            "translated_text": translated_text,
            "confidence": 0.95,
            "medical_terms": [],
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"❌ Error in basic translation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/translate/medical", response_model=EnhancedTranslationResponse)
async def medical_translate_with_learning(
    request: TranslationRequest,
    extraction_service: MedicationExtractionService = Depends(get_extraction_service),
    translation_service: TranslationService = Depends(get_translation_service),
    session_service: SessionService = Depends(get_session_service)
):
    """Enhanced medical translation with OBGYN specialization and learning-ready extraction"""
    try:
        session_id = str(uuid.uuid4())
        
        logger.info(f"🚀 Medical translation with learning: '{request.text}'")
        
        # ENHANCED: Auto-detect OBGYN context and use appropriate extraction
        obgyn_keywords = [
            "pregnant", "pregnancy", "prenatal", "postpartum", "breastfeeding",
            "birth control", "contraception", "period", "menstrual", "cycle", 
            "pcos", "endometriosis", "fertility", "ovulation", "trimester",
            "folic acid", "prenatal vitamins", "gestational", "labor", "delivery",
            # Spanish terms
            "embarazada", "embarazo", "prenatal", "anticonceptivos", "período",
            "ácido fólico", "vitaminas prenatales", "gestacional", "trimestre",
            "lactancia", "materna", "parto", "ginecólogo", "obstetra"
        ]
        
        text_lower = request.text.lower()
        is_obgyn_context = any(keyword in text_lower for keyword in obgyn_keywords)
        
        if is_obgyn_context:
            # Use OBGYN specialization
            from services.medical_intelligence import process_obgyn_case
            
            # Create patient profile from request
            patient_profile = {
                "source_language": request.source_language,
                "medical_context": request.medical_context
            }
            
            logger.info(f"🏥 Using OBGYN specialization for: '{request.text}'")
            obgyn_result = await process_obgyn_case(request.text, session_id, patient_profile)
            
            # Convert OBGYN result to standard extraction format
            extraction_result = {
                "medications": obgyn_result["medications"],
                "metadata": obgyn_result["metadata"],
                "obgyn_context": obgyn_result["obgyn_context"],
                "recommendations": obgyn_result["recommendations"]
            }
        else:
            # Use general extraction (your existing code)
            logger.info(f"📋 Using general extraction for: '{request.text}'")
            extraction_result = await extraction_service.extract_medications(
                request.text, 
                session_id, 
                request.medical_context or "general"
            )
        
        # Step 2: Translation (same as before)
        translation_result = await translation_service.translate_with_medical_context(
            request.text,
            request.source_language,
            request.target_language,
            extraction_result["medications"]
        )
        
        # Step 3: Generate follow-up questions (enhanced for OBGYN)
        if is_obgyn_context and "recommendations" in extraction_result:
            follow_up_questions = extraction_result["recommendations"].get("follow_up_questions", [])
        else:
            follow_up_questions = await translation_service.get_follow_up_questions(
                request.text, 
                request.medical_context or "general"
            )
        
        # Step 4: Format medical terms for response (enhanced)
        medical_terms_list = []
        confidence_scores = {}
        
        for med_result in extraction_result["medications"]:
            medication = med_result["medication"]
            
            # Enhanced term data with OBGYN context
            term_data = {
                "original_text": med_result["original_term"],
                "canonical_name": medication.get("canonical_name", ""),
                "category": "medication",
                "confidence": med_result["extraction_confidence"],
                "translation": medication.get("canonical_name", ""),
                "context_clues": medication.get("indications", [])[:2] if medication.get("indications") else [],
                "extraction_strategy": med_result["extraction_strategy"],
                "api_data": {
                    "rxcui": medication.get("rxcui"),
                    "pregnancy_category": medication.get("pregnancy_category"),
                    "brand_names": medication.get("brand_names", [])
                }
            }
            
            # Add OBGYN-specific data if available
            if "obgyn_category" in med_result:
                term_data["obgyn_category"] = med_result["obgyn_category"]
                term_data["pregnancy_stage"] = med_result.get("pregnancy_stage", "unknown")
                term_data["safety_assessment"] = med_result.get("safety_assessment", {})
            
            medical_terms_list.append(term_data)
            confidence_scores[med_result["original_term"]] = med_result["extraction_confidence"]
        
        # Step 5: Calculate accuracy score
        accuracy_score = 0.0
        if extraction_result["metadata"]["total_candidates"] > 0:
            accuracy_score = extraction_result["metadata"]["successful_extractions"] / extraction_result["metadata"]["total_candidates"]
        
        # Step 6: Enhanced medical notes with OBGYN insights
        medical_notes = []
        
        if is_obgyn_context and "obgyn_context" in extraction_result:
            obgyn_context = extraction_result["obgyn_context"]
            
            # Add pregnancy stage note
            if obgyn_context.get("pregnancy_stage") != "not_pregnant":
                medical_notes.append({
                    "type": "pregnancy_context",
                    "message": f"Patient pregnancy stage: {obgyn_context['pregnancy_stage']}",
                    "importance": "high"
                })
            
            # Add safety alerts
            if "recommendations" in extraction_result:
                safety_alerts = extraction_result["recommendations"].get("safety_alerts", [])
                for alert in safety_alerts:
                    medical_notes.append({
                        "type": "safety_alert", 
                        "message": alert,
                        "importance": "urgent"
                    })
            
            # Add OBGYN-specific notes
            conditions = obgyn_context.get("identified_conditions", [])
            if "pcos" in conditions:
                medical_notes.append({
                    "type": "condition_context",
                    "message": "Patient has PCOS - consider medication interactions",
                    "importance": "medium"
                })
        
        # Step 7: Store session data
        await session_service.store_medical_translation(
            session_id, request, translation_result, extraction_result, follow_up_questions
        )
        
        response = EnhancedTranslationResponse(
            original_text=request.text,
            standard_translation=translation_result["standard_translation"],
            enhanced_translation=translation_result["enhanced_translation"],
            medical_terms=medical_terms_list,
            medical_notes=medical_notes,
            follow_up_questions=follow_up_questions,
            medical_accuracy_score=accuracy_score,
            confidence=0.95,
            session_id=session_id,
            learning_metadata=LearningMetadata(
                extraction_strategies_used=extraction_result["metadata"]["extraction_strategies_used"],
                candidates_analyzed=extraction_result["metadata"]["total_candidates"],
                ready_for_feedback=True,
                confidence_scores=confidence_scores
            )
        )
        
        specialty_used = extraction_result["metadata"].get("specialty", "general")
        logger.info(f"✅ Medical translation completed ({specialty_used}): {len(medical_terms_list)} medications extracted")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error in medical translation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/debug/obgyn")
async def debug_obgyn_processing(text: str = "I'm pregnant taking prenatal vitamins"):
    """Debug OBGYN processing to see the actual result structure"""
    try:
        from services.medical_intelligence import process_obgyn_case
        
        session_id = f"debug_{uuid.uuid4()}"
        patient_profile = {"source_language": "en"}
        
        result = await process_obgyn_case(text, session_id, patient_profile)
        
        return {
            "input": text,
            "result_keys": list(result.keys()),  # Show what keys exist
            "full_result": result,
            "success": True
        }
        
    except Exception as e:
        return {
            "input": text,
            "error": str(e),
            "error_type": type(e).__name__,
            "success": False
        }

@app.post("/debug/obgyn-routing") 
async def debug_obgyn_routing(text: str = "I'm pregnant taking prenatal vitamins"):
    """Debug why OBGYN routing isn't working"""
    try:
        # Test the specialty registry detection
        from services.medical_intelligence.specialties import specialty_registry
        
        detected_specialty = specialty_registry.detect_specialty(text, {"pregnancy_status": True})
        available_specialties = specialty_registry.get_available_specialties()
        obgyn_service = specialty_registry.get_specialty("obgyn")
        
        # Test direct OBGYN call
        if obgyn_service:
            session_id = f"debug_direct_{uuid.uuid4()}"
            direct_result = await obgyn_service.process_text(text, session_id, {"pregnancy_status": True})
            has_obgyn_context = "obgyn_context" in direct_result
        else:
            direct_result = None
            has_obgyn_context = False
        
        return {
            "text": text,
            "detected_specialty": detected_specialty,
            "available_specialties": available_specialties, 
            "obgyn_service_exists": obgyn_service is not None,
            "direct_obgyn_result_keys": list(direct_result.keys()) if direct_result else None,
            "has_obgyn_context": has_obgyn_context,
            "success": True
        }
        
    except Exception as e:
        return {"error": str(e), "success": False}

# @app.post("/translate/medical", response_model=EnhancedTranslationResponse)
# async def medical_translate_with_learning(
#     request: TranslationRequest,
#     extraction_service: MedicationExtractionService = Depends(get_extraction_service),
#     translation_service: TranslationService = Depends(get_translation_service),
#     session_service: SessionService = Depends(get_session_service)
# ):
#     """Enhanced medical translation with learning-ready extraction"""
#     try:
#         session_id = str(uuid.uuid4())
        
#         logger.info(f"🚀 Medical translation with learning: '{request.text}'")
        
#         # Step 1: Intelligent medication extraction
#         extraction_result = await extraction_service.extract_medications(
#             request.text, 
#             session_id, 
#             request.medical_context or "general"
#         )
        
#         # Step 2: Translation
#         translation_result = await translation_service.translate_with_medical_context(
#             request.text,
#             request.source_language,
#             request.target_language,
#             extraction_result["medications"]
#         )
        
#         # Step 3: Generate follow-up questions
#         follow_up_questions = await translation_service.get_follow_up_questions(
#             request.text, 
#             request.medical_context or "general"
#         )
        
#         # Step 4: Format medical terms for response
#         medical_terms_list = []
#         confidence_scores = {}
        
#         for med_result in extraction_result["medications"]:
#             medication = med_result["medication"]
#             term_data = {
#                 "original_text": med_result["original_term"],
#                 "canonical_name": medication.get("canonical_name", ""),
#                 "category": "medication",
#                 "confidence": med_result["extraction_confidence"],
#                 "translation": medication.get("canonical_name", ""),
#                 "context_clues": medication.get("indications", [])[:2] if medication.get("indications") else [],
#                 "extraction_strategy": med_result["extraction_strategy"],
#                 "api_data": {
#                     "rxcui": medication.get("rxcui"),
#                     "pregnancy_category": medication.get("pregnancy_category"),
#                     "brand_names": medication.get("brand_names", [])
#                 }
#             }
#             medical_terms_list.append(term_data)
#             confidence_scores[med_result["original_term"]] = med_result["extraction_confidence"]
        
#         # Step 5: Calculate accuracy score
#         accuracy_score = 0.0
#         if extraction_result["metadata"]["total_candidates"] > 0:
#             accuracy_score = extraction_result["metadata"]["successful_extractions"] / extraction_result["metadata"]["total_candidates"]
        
#         # Step 6: Store session data
#         await session_service.store_medical_translation(
#             session_id, request, translation_result, extraction_result, follow_up_questions
#         )
        
#         response = EnhancedTranslationResponse(
#             original_text=request.text,
#             standard_translation=translation_result["standard_translation"],
#             enhanced_translation=translation_result["enhanced_translation"],
#             medical_terms=medical_terms_list,
#             medical_notes=[],
#             follow_up_questions=follow_up_questions,
#             medical_accuracy_score=accuracy_score,
#             confidence=0.95,
#             session_id=session_id,
#             learning_metadata=LearningMetadata(
#                 extraction_strategies_used=extraction_result["metadata"]["extraction_strategies_used"],
#                 candidates_analyzed=extraction_result["metadata"]["total_candidates"],
#                 ready_for_feedback=True,
#                 confidence_scores=confidence_scores
#             )
#         )
        
#         logger.info(f"✅ Medical translation completed: {len(medical_terms_list)} medications extracted")
#         return response
        
#     except Exception as e:
#         logger.error(f"❌ Error in medical translation: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# LEARNING & FEEDBACK ENDPOINTS
# =============================================================================

@app.post("/feedback/extraction/{extraction_id}")
async def provide_extraction_feedback(
    extraction_id: str, 
    feedback: Dict[str, bool],  # {"medication_name": True/False}
    learning_manager: LearningManager = Depends(get_learning_manager)
):
    """Provide feedback on medication extraction for learning"""
    try:
        result = await learning_manager.record_feedback(extraction_id, feedback)
        logger.info(f"📝 Feedback recorded for extraction {extraction_id}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error recording feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/learning/analytics/{session_id}")
async def get_learning_analytics(
    session_id: str,
    session_service: SessionService = Depends(get_session_service)
):
    """Get learning analytics for a session"""
    try:
        analytics = await session_service.get_session_analytics(session_id)
        return analytics
        
    except Exception as e:
        logger.error(f"❌ Error getting analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# TESTING ENDPOINTS
# =============================================================================

@app.post("/test/extraction")
async def test_intelligent_extraction(text: str = "I'm taking azithromycin for my infection"):
    """Test the intelligent extraction system with OBGYN auto-detection"""
    try:
        from services.medical_intelligence import extract_medications, health_check
        
        session_id = f"test_{uuid.uuid4()}"
        
        logger.info(f"🧪 Testing extraction with: '{text}'")
        
        # USE NEW SYSTEM: This will auto-detect OBGYN
        result = await extract_medications(text, session_id)
        
        # Test health check too
        health_status = await health_check()
        
        return {
            "test_text": text,
            "extraction_result": result,
            "specialty_detected": result.get("metadata", {}).get("specialty", "general"),
            "medications_found": len(result.get("medications", [])),
            "strategies_used": result.get("metadata", {}).get("extraction_strategies_used", []),
            "obgyn_context": result.get("obgyn_context", {}),  # Show OBGYN context if present
            "health_check": health_status.get("status", "unknown"),
            "session_id": session_id,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"❌ Test extraction failed: {str(e)}")
        return {
            "error": str(e),
            "test_text": text,
            "success": False
        }

# @app.post("/test/extraction")
# async def test_intelligent_extraction(
#     text: str = "I'm taking azithromycin for my infection",
#     extraction_service: MedicationExtractionService = Depends(get_extraction_service)
# ):
#     """Test the intelligent extraction system"""
#     try:
#         session_id = f"test_{uuid.uuid4()}"
        
#         logger.info(f"🧪 Testing extraction with: '{text}'")
        
#         result = await extraction_service.extract_medications(text, session_id, "general")
        
#         return {
#             "test_text": text,
#             "extraction_result": result,
#             "medications_found": len(result["medications"]),
#             "strategies_used": result["metadata"]["extraction_strategies_used"],
#             "session_id": session_id,
#             "success": True
#         }
        
#     except Exception as e:
#         logger.error(f"❌ Test extraction failed: {str(e)}")
#         return {
#             "error": str(e),
#             "test_text": text,
#             "success": False
#         }

@app.get("/test/external-apis")
async def test_external_apis(drug_name: str = "azithromycin"):
    """Test external medical APIs integration"""
    try:
        from external_medical_intelligence import enhanced_medication_lookup
        
        logger.info(f"🧪 Testing external APIs with drug: {drug_name}")
        
        result = await enhanced_medication_lookup(drug_name, "general")
        
        return {
            "success": True,
            "drug_tested": drug_name,
            "api_results": result,
            "api_status": {
                "has_canonical_name": bool(result.get("canonical_name")),
                "has_brand_names": bool(result.get("brand_names")),
                "has_pregnancy_category": bool(result.get("pregnancy_category")),
                "has_indications": bool(result.get("indications"))
            }
        }
        
    except Exception as e:
        logger.error(f"❌ External API test failed: {str(e)}")
        return {
            "success": False,
            "drug_tested": drug_name,
            "error": str(e),
            "error_type": type(e).__name__
        }

# =============================================================================
# SESSION MANAGEMENT ENDPOINTS
# =============================================================================

@app.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    session_service: SessionService = Depends(get_session_service)
):
    """Retrieve session history"""
    try:
        session_data = await session_service.get_session(session_id)
        return session_data
        
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail="Session not found")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    session_service: SessionService = Depends(get_session_service)
):
    """Delete session for privacy compliance"""
    try:
        await session_service.delete_session(session_id)
        return {"message": "Session deleted successfully"}
        
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail="Session not found")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# STARTUP EVENTS
# =============================================================================

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Talktor Medical Interpreter API starting up...")
    logger.info(f"📡 Whisper model loaded: {model}")
    logger.info("🧠 Learning system: ACTIVE")
    logger.info("🏗️ Service architecture: READY")
    logger.info("✅ All systems operational!")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)