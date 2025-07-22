# =============================================================================
# services/medical_intelligence/specialties/obgyn/extraction.py
# =============================================================================

import logging
from typing import Dict, List, Optional
from datetime import datetime
import re

# Import from core module
from ...core.extraction import MedicationExtractionService
from ...core.confidence import ConfidenceScorer

# Import from local OBGYN module
from .specialty_engine import OBGYNSpecialtyEngine, PregnancyStage, OBGYNCondition

logger = logging.getLogger(__name__)

class OBGYNEnhancedExtractionService(MedicationExtractionService):
    """
    OBGYN-enhanced medication extraction service
    Extends base extraction with specialty-specific intelligence
    """
    
    def __init__(self):
        super().__init__()
        self.obgyn_engine = OBGYNSpecialtyEngine()
        self.obgyn_confidence_threshold = 0.25  # Lower threshold for OBGYN context
        
        # OBGYN-specific extraction patterns
        self.obgyn_medication_patterns = {
            # Contraceptives
            r'\b(?:birth\s+control|contraceptive|pill|oral\s+contraceptive)\b': {
                "category": "contraception",
                "confidence_boost": 0.3,
                "pregnancy_concern": True
            },
            
            # Prenatal supplements (enhanced for coverage)
            r'\b(?:prenatal\s+vitamins?|folic\s+acid|folate|iron\s+supplement|vitaminas\s+prenatales|ácido\s+fólico)\b': {
                "category": "prenatal_supplement",
                "confidence_boost": 0.4,
                "pregnancy_related": True
            },
            
            # Fertility medications
            r'\b(?:clomid|clomiphene|letrozole|femara|gonadotropin)\b': {
                "category": "fertility",
                "confidence_boost": 0.35,
                "pregnancy_concern": True
            },
            
            # Labor medications
            r'\b(?:epidural|pitocin|oxytocin|magnesium\s+sulfate)\b': {
                "category": "labor_delivery",
                "confidence_boost": 0.4,
                "pregnancy_stage_specific": "third_trimester"
            },
            
            # PCOS medications
            r'\b(?:metformin|spironolactone|inositol)\b': {
                "category": "pcos_treatment",
                "confidence_boost": 0.25,
                "condition_specific": "pcos"
            },
            
            # HRT and menopause
            r'\b(?:estrogen|progesterone|hormone\s+replacement|hrt|premarin)\b': {
                "category": "hormone_therapy",
                "confidence_boost": 0.3,
                "age_considerations": True
            }
        }
    
    async def extract_obgyn_medications(self, text: str, session_id: str, 
                                      patient_profile: Optional[Dict] = None) -> Dict:
        """
        OBGYN-specialized medication extraction
        """
        logger.info(f"🏥 OBGYN Extraction: Processing '{text}' with patient context")
        
        # Step 1: Analyze OBGYN context
        obgyn_context = await self.obgyn_engine.analyze_obgyn_context(text, patient_profile)
        
        # Step 2: Perform enhanced candidate identification
        candidates = await self._identify_obgyn_candidates(text, obgyn_context)
        
        # Step 3: Validate with OBGYN-specific logic
        validated_medications = await self._validate_obgyn_candidates(
            candidates, obgyn_context, text, patient_profile
        )
        
        # Step 4: Generate OBGYN-specific metadata
        metadata = self._generate_obgyn_metadata(candidates, validated_medications, text, obgyn_context)
        
        # Step 5: Store for learning with OBGYN context
        extraction_id = await self.learning_manager.store_extraction_attempt(
            session_id, text, candidates, validated_medications, metadata
        )
        
        # Step 6: Generate OBGYN-specific recommendations
        recommendations = await self._generate_obgyn_recommendations(
            validated_medications, obgyn_context, patient_profile
        )
        
        return {
            "medications": validated_medications,
            "obgyn_context": obgyn_context,
            "recommendations": recommendations,
            "metadata": metadata,
            "learning_data": {
                "session_id": session_id,
                "extraction_id": extraction_id,
                "ready_for_feedback": True,
                "specialty": "obgyn"
            }
        }
    
    async def _identify_obgyn_candidates(self, text: str, obgyn_context: Dict) -> List[Dict]:
        """Enhanced candidate identification with OBGYN patterns"""
        
        # Get base candidates from parent class
        base_candidates = await super()._identify_candidates(text)
        
        # Add OBGYN-specific pattern candidates
        obgyn_candidates = self._extract_obgyn_patterns(text, obgyn_context)
        
        # Enhance existing candidates with OBGYN context
        enhanced_candidates = self._enhance_candidates_with_obgyn_context(
            base_candidates, obgyn_context
        )
        
        # Combine and deduplicate
        all_candidates = enhanced_candidates + obgyn_candidates
        return self._deduplicate_obgyn_candidates(all_candidates)
    
    def _extract_obgyn_patterns(self, text: str, obgyn_context: Dict) -> List[Dict]:
        """Extract OBGYN-specific medication patterns"""
        candidates = []
        
        pregnancy_stage = PregnancyStage(obgyn_context.get("pregnancy_stage", "not_pregnant"))
        conditions = [OBGYNCondition(c) for c in obgyn_context.get("identified_conditions", [])]
        
        for pattern, pattern_info in self.obgyn_medication_patterns.items():
            matches = re.finditer(pattern, text.lower())
            
            for match in matches:
                term = match.group()
                word_position = len(text[:match.start()].split())
                
                # Calculate OBGYN-specific confidence modifiers
                confidence_modifiers = {
                    "obgyn_pattern_matched": True,
                    "obgyn_confidence_boost": pattern_info["confidence_boost"],
                    "category": pattern_info["category"]
                }
                
                # Context-specific boosts
                if pattern_info.get("pregnancy_related") and pregnancy_stage != PregnancyStage.NOT_PREGNANT:
                    confidence_modifiers["pregnancy_context_boost"] = 0.2
                
                if pattern_info.get("condition_specific"):
                    target_condition = OBGYNCondition(pattern_info["condition_specific"])
                    if target_condition in conditions:
                        confidence_modifiers["condition_match_boost"] = 0.15
                
                if pattern_info.get("pregnancy_stage_specific"):
                    target_stage = PregnancyStage(pattern_info["pregnancy_stage_specific"])
                    if pregnancy_stage == target_stage:
                        confidence_modifiers["stage_match_boost"] = 0.2
                
                candidates.append({
                    "term": term,
                    "strategy": "obgyn_pattern_match",
                    "context": text[max(0, match.start()-30):match.end()+30],
                    "position": word_position,
                    "confidence_modifiers": confidence_modifiers,
                    "obgyn_category": pattern_info["category"]
                })
        
        return candidates
    
    def _enhance_candidates_with_obgyn_context(self, candidates: List[Dict], 
                                             obgyn_context: Dict) -> List[Dict]:
        """Enhance existing candidates with OBGYN context"""
        
        enhanced = []
        pregnancy_stage = PregnancyStage(obgyn_context.get("pregnancy_stage", "not_pregnant"))
        
        for candidate in candidates:
            enhanced_candidate = candidate.copy()
            
            # Add OBGYN context to confidence modifiers
            if "confidence_modifiers" not in enhanced_candidate:
                enhanced_candidate["confidence_modifiers"] = {}
            
            enhanced_candidate["confidence_modifiers"]["obgyn_context"] = True
            enhanced_candidate["confidence_modifiers"]["pregnancy_stage"] = pregnancy_stage.value
            
            # Boost confidence for pregnancy-relevant terms
            term = candidate["term"].lower()
            if pregnancy_stage != PregnancyStage.NOT_PREGNANT:
                pregnancy_relevant_terms = [
                    "prenatal", "folic", "iron", "vitamin", "calcium", "dha",
                    "acetaminophen", "tylenol"  # Safe pain relief
                ]
                
                if any(relevant_term in term for relevant_term in pregnancy_relevant_terms):
                    enhanced_candidate["confidence_modifiers"]["pregnancy_relevance_boost"] = 0.15
                
                # Flag potentially dangerous medications
                risky_terms = ["ibuprofen", "aspirin", "nsaid", "warfarin", "ace"]
                if any(risky_term in term for risky_term in risky_terms):
                    enhanced_candidate["confidence_modifiers"]["pregnancy_risk_flag"] = True
                    enhanced_candidate["confidence_modifiers"]["risk_confidence_penalty"] = -0.1
            
            enhanced.append(enhanced_candidate)
        
        return enhanced
    
    def _deduplicate_obgyn_candidates(self, candidates: List[Dict]) -> List[Dict]:
        """OBGYN-specific deduplication preserving specialty information"""
        unique_candidates = []
        seen_terms = {}
        
        for candidate in candidates:
            term = candidate["term"]
            strategy = candidate["strategy"]
            
            # Create composite key
            key = f"{term}_{strategy}"
            
            if key not in seen_terms:
                seen_terms[key] = candidate
                unique_candidates.append(candidate)
            else:
                # Merge OBGYN-specific information if duplicate found
                existing = seen_terms[key]
                if candidate.get("obgyn_category"):
                    existing["obgyn_category"] = candidate["obgyn_category"]
                
                # Combine confidence modifiers
                if "confidence_modifiers" in candidate:
                    existing.setdefault("confidence_modifiers", {}).update(
                        candidate["confidence_modifiers"]
                    )
        
        return unique_candidates
    
    async def _validate_obgyn_candidates(self, candidates: List[Dict], obgyn_context: Dict,
                                       text: str, patient_profile: Optional[Dict]) -> List[Dict]:
        """Validate candidates with OBGYN-specific intelligence"""
        
        validated_medications = []
        pregnancy_stage = PregnancyStage(obgyn_context.get("pregnancy_stage", "not_pregnant"))
        
        for candidate in candidates:
            try:
                # Get OBGYN-specific medication information
                obgyn_med_info = await self.obgyn_engine.get_obgyn_medication_info(
                    candidate["term"], pregnancy_stage
                )
                
                # Calculate enhanced confidence score
                confidence_score = await self._calculate_obgyn_confidence(
                    candidate, obgyn_med_info, text, obgyn_context
                )
                
                # Apply OBGYN-specific threshold
                if confidence_score > self.obgyn_confidence_threshold:
                    
                    # Perform safety assessment
                    safety_assessment = self._assess_obgyn_safety(
                        obgyn_med_info, pregnancy_stage, obgyn_context
                    )
                    
                    validated_medication = {
                        "medication": obgyn_med_info,
                        "extraction_confidence": confidence_score,
                        "extraction_strategy": candidate["strategy"],
                        "context": candidate["context"],
                        "position": candidate["position"],
                        "original_term": candidate["term"],
                        "obgyn_category": candidate.get("obgyn_category", "general"),
                        "safety_assessment": safety_assessment,
                        "pregnancy_stage": pregnancy_stage.value,
                        "validation_timestamp": datetime.now().isoformat(),
                        "specialty": "obgyn"
                    }
                    
                    validated_medications.append(validated_medication)
                    
            except Exception as e:
                logger.warning(f"⚠️ OBGYN validation failed for '{candidate['term']}': {e}")
                continue
        
        return validated_medications
    
    async def _calculate_obgyn_confidence(self, candidate: Dict, obgyn_med_info: Dict,
                                        text: str, obgyn_context: Dict) -> float:
        """Calculate OBGYN-enhanced confidence score"""
        
        # Start with base confidence
        base_confidence = self.confidence_scorer.calculate_confidence(
            candidate, obgyn_med_info, text
        )
        
        # OBGYN-specific confidence adjustments
        obgyn_boost = 0.0
        
        # Pattern matching boost
        if candidate.get("confidence_modifiers", {}).get("obgyn_pattern_matched"):
            obgyn_boost += candidate["confidence_modifiers"].get("obgyn_confidence_boost", 0)
        
        # Pregnancy context boost
        if candidate.get("confidence_modifiers", {}).get("pregnancy_context_boost"):
            obgyn_boost += candidate["confidence_modifiers"]["pregnancy_context_boost"]
        
        # Condition-specific boost
        if candidate.get("confidence_modifiers", {}).get("condition_match_boost"):
            obgyn_boost += candidate["confidence_modifiers"]["condition_match_boost"]
        
        # Stage-specific boost
        if candidate.get("confidence_modifiers", {}).get("stage_match_boost"):
            obgyn_boost += candidate["confidence_modifiers"]["stage_match_boost"]
        
        # Risk penalty for dangerous combinations
        if candidate.get("confidence_modifiers", {}).get("pregnancy_risk_flag"):
            risk_penalty = candidate["confidence_modifiers"].get("risk_confidence_penalty", 0)
            obgyn_boost += risk_penalty  # This will be negative
        
        # Specialty database boost
        if "obgyn_analysis" in obgyn_med_info:
            relevance = obgyn_med_info["obgyn_analysis"].get("obgyn_relevance", "unknown")
            if relevance == "high":
                obgyn_boost += 0.15
        
        # Cap total confidence at 1.0
        final_confidence = min(base_confidence + obgyn_boost, 1.0)
        
        logger.debug(f"🎯 OBGYN confidence: base={base_confidence:.3f}, boost={obgyn_boost:.3f}, final={final_confidence:.3f}")
        
        return final_confidence
    
    def _assess_obgyn_safety(self, medication_info: Dict, pregnancy_stage: PregnancyStage,
                           obgyn_context: Dict) -> Dict:
        """Comprehensive OBGYN safety assessment"""
        
        safety_assessment = {
            "overall_safety": "unknown",
            "pregnancy_safety": "unknown",
            "breastfeeding_safety": "unknown",
            "contraindications": [],
            "warnings": [],
            "patient_counseling_required": False,
            "physician_consultation_required": False
        }
        
        # Pregnancy safety assessment
        if pregnancy_stage in [PregnancyStage.FIRST_TRIMESTER, PregnancyStage.SECOND_TRIMESTER, 
                              PregnancyStage.THIRD_TRIMESTER, PregnancyStage.UNKNOWN]:
            
            pregnancy_category = medication_info.get("pregnancy_safety", "unknown")
            
            if pregnancy_category == "A":
                safety_assessment["pregnancy_safety"] = "safe"
                safety_assessment["overall_safety"] = "safe"
            elif pregnancy_category == "B":
                safety_assessment["pregnancy_safety"] = "probably_safe"
                safety_assessment["overall_safety"] = "probably_safe"
            elif pregnancy_category == "C":
                safety_assessment["pregnancy_safety"] = "use_with_caution"
                safety_assessment["warnings"].append("Risk-benefit analysis required")
                safety_assessment["physician_consultation_required"] = True
            elif pregnancy_category in ["D", "X"]:
                safety_assessment["pregnancy_safety"] = "avoid"
                safety_assessment["overall_safety"] = "contraindicated"
                safety_assessment["warnings"].append("Not recommended during pregnancy")
                safety_assessment["physician_consultation_required"] = True
        
        # Breastfeeding safety
        elif pregnancy_stage == PregnancyStage.POSTPARTUM:
            bf_safety = medication_info.get("breastfeeding_safety", "unknown")
            safety_assessment["breastfeeding_safety"] = bf_safety
            
            if bf_safety == "unknown":
                safety_assessment["warnings"].append("Breastfeeding safety not established")
                safety_assessment["physician_consultation_required"] = True
        
        # Check for contraindications
        contraindications = medication_info.get("contraindications", [])
        safety_assessment["contraindications"] = contraindications
        
        # Additional safety flags from OBGYN context
        safety_flags = obgyn_context.get("safety_flags", [])
        for flag in safety_flags:
            if flag["severity"] in ["high", "urgent"]:
                safety_assessment["warnings"].append(flag["message"])
                safety_assessment["physician_consultation_required"] = True
        
        # Determine if patient counseling is needed
        if (safety_assessment["warnings"] or 
            pregnancy_stage != PregnancyStage.NOT_PREGNANT or
            medication_info.get("category") in ["contraception", "fertility", "hormone_therapy"]):
            safety_assessment["patient_counseling_required"] = True
        
        return safety_assessment
    
    def _generate_obgyn_metadata(self, candidates: List[Dict], validated: List[Dict],
                               text: str, obgyn_context: Dict) -> Dict:
        """Generate OBGYN-specific extraction metadata"""
        
        base_metadata = super()._generate_extraction_metadata(candidates, validated, text)
        
        obgyn_metadata = {
            **base_metadata,
            "specialty": "obgyn",
            "obgyn_context": obgyn_context,
            "pregnancy_stage": obgyn_context.get("pregnancy_stage"),
            "identified_conditions": obgyn_context.get("identified_conditions"),
            "safety_flags_count": len(obgyn_context.get("safety_flags", [])),
            "obgyn_patterns_found": len([c for c in candidates if c.get("strategy") == "obgyn_pattern_match"]),
            "requires_specialist_review": obgyn_context.get("requires_specialist_review", False),
            "medications_by_category": self._categorize_extracted_medications(validated)
        }
        
        return obgyn_metadata
    
    def _categorize_extracted_medications(self, validated_medications: List[Dict]) -> Dict:
        """Categorize extracted medications by OBGYN category"""
        categories = {}
        
        for med in validated_medications:
            category = med.get("obgyn_category", "general")
            if category not in categories:
                categories[category] = []
            
            categories[category].append({
                "name": med["medication"].get("canonical_name", med["original_term"]),
                "confidence": med["extraction_confidence"],
                "safety": med["safety_assessment"]["overall_safety"]
            })
        
        return categories
    
    async def _generate_obgyn_recommendations(self, validated_medications: List[Dict],
                                            obgyn_context: Dict, 
                                            patient_profile: Optional[Dict]) -> Dict:
        """Generate OBGYN-specific recommendations and follow-up questions"""
        
        recommendations = {
            "medication_recommendations": [],
            "safety_alerts": [],
            "follow_up_questions": [],
            "patient_education_topics": [],
            "specialist_referral_needed": False
        }
        
        pregnancy_stage = PregnancyStage(obgyn_context.get("pregnancy_stage", "not_pregnant"))
        safety_flags = obgyn_context.get("safety_flags", [])
        
        # Medication-specific recommendations
        for med in validated_medications:
            safety = med["safety_assessment"]
            
            if safety["physician_consultation_required"]:
                recommendations["medication_recommendations"].append(
                    f"Discuss {med['original_term']} safety with your OB/GYN"
                )
                recommendations["specialist_referral_needed"] = True
            
            if safety["patient_counseling_required"]:
                medication_name = med["medication"].get("canonical_name", med["original_term"])
                recommendations["patient_education_topics"].append(
                    f"Proper use and safety of {medication_name}"
                )
        
        # Safety alerts
        for flag in safety_flags:
            if flag["severity"] in ["high", "urgent"]:
                recommendations["safety_alerts"].append(flag["message"])
                if flag["severity"] == "urgent":
                    recommendations["specialist_referral_needed"] = True
        
        # Pregnancy-specific recommendations
        if pregnancy_stage != PregnancyStage.NOT_PREGNANT:
            recommendations["follow_up_questions"].extend([
                "Are you taking prenatal vitamins?",
                "When is your next prenatal appointment?",
                "Are you experiencing any concerning symptoms?"
            ])
            
            if pregnancy_stage == PregnancyStage.FIRST_TRIMESTER:
                recommendations["patient_education_topics"].extend([
                    "First trimester medication safety",
                    "Prenatal vitamin importance",
                    "Foods and substances to avoid"
                ])
        
        # Condition-specific recommendations
        conditions = obgyn_context.get("identified_conditions", [])
        if "pcos" in conditions:
            recommendations["follow_up_questions"].append("How are you managing your PCOS symptoms?")
            recommendations["patient_education_topics"].append("PCOS management strategies")
        
        if "contraception" in conditions:
            recommendations["follow_up_questions"].extend([
                "Are you satisfied with your current birth control method?",
                "Are you experiencing any side effects?"
            ])
        
        # Menstrual cycle information
        cycle_info = obgyn_context.get("menstrual_cycle_info", {})
        if cycle_info.get("cycle_regularity") == "irregular":
            recommendations["follow_up_questions"].append("How long have your cycles been irregular?")
            recommendations["specialist_referral_needed"] = True
        
        return recommendations