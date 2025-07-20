# =============================================================================
# services/medical_intelligence/specialties/obgyn/integration.py
# =============================================================================

import logging
from typing import Dict, List, Optional, Union
from datetime import datetime

# Import from specialties module
from .. import SpecialtyInterface

# Import from local OBGYN module
from .extraction import OBGYNEnhancedExtractionService
from .specialty_engine import OBGYNSpecialtyEngine, PregnancyStage, OBGYNCondition

logger = logging.getLogger(__name__)

class OBGYNSpecialty(SpecialtyInterface):
    """
    OBGYN specialty implementation of SpecialtyInterface
    Provides standardized interface for OBGYN medical intelligence
    """
    
    @property
    def specialty_name(self) -> str:
        return "obgyn"
    
    @property 
    def keywords(self) -> List[str]:
        return [
            "pregnant", "pregnancy", "prenatal", "postpartum", "breastfeeding",
            "birth control", "contraception", "period", "menstrual", "cycle",
            "pcos", "endometriosis", "fertility", "ovulation", "gynecologist",
            "obgyn", "ob/gyn", "prenatal vitamins", "folic acid", "gestational",
            "trimester", "labor", "delivery", "cervical", "uterine", "ovarian"
        ]
    
    def __init__(self):
        self.intelligence = OBGYNMedicalIntelligence()
    
    async def process_text(self, text: str, session_id: str, 
                          patient_profile: Optional[Dict] = None) -> Dict:
        """Process text for OBGYN specialty"""
        return await self.intelligence.process_obgyn_text(text, session_id, patient_profile)
    
    async def get_medication_safety(self, medication_name: str, 
                                  context: Optional[Dict] = None) -> Dict:
        """Get medication safety for OBGYN context"""
        pregnancy_stage = "not_pregnant"
        if context:
            pregnancy_stage = context.get("pregnancy_stage", "not_pregnant")
        
        return await self.intelligence.get_medication_safety_summary(medication_name, pregnancy_stage)

class OBGYNMedicalIntelligence:
    """
    Main integration class for OBGYN medical intelligence
    Provides unified interface for all OBGYN-specific functionality
    """
    
    def __init__(self):
        self.extraction_service = OBGYNEnhancedExtractionService()
        self.specialty_engine = OBGYNSpecialtyEngine()
        
    async def process_obgyn_text(self, text: str, session_id: str, 
                               patient_profile: Optional[Dict] = None,
                               include_recommendations: bool = True) -> Dict:
        """
        Main entry point for OBGYN text processing
        
        Args:
            text: Patient text to analyze
            session_id: Session identifier for learning
            patient_profile: Optional patient context
            include_recommendations: Whether to generate recommendations
            
        Returns:
            Complete OBGYN analysis with medications, context, and recommendations
        """
        
        logger.info(f"🏥 Processing OBGYN text for session {session_id}")
        
        try:
            # Process with OBGYN-enhanced extraction
            extraction_result = await self.extraction_service.extract_obgyn_medications(
                text, session_id, patient_profile
            )
            
            # Enhance with additional OBGYN insights
            enhanced_result = await self._enhance_with_obgyn_insights(
                extraction_result, text, patient_profile
            )
            
            logger.info(f"✅ OBGYN processing complete: {len(enhanced_result['medications'])} medications, "
                       f"{len(enhanced_result['recommendations']['safety_alerts'])} safety alerts")
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"❌ OBGYN processing failed: {e}")
            return {
                "error": str(e),
                "medications": [],
                "obgyn_context": {},
                "recommendations": {},
                "timestamp": datetime.now().isoformat()
            }
    
    async def _enhance_with_obgyn_insights(self, extraction_result: Dict, 
                                         text: str, patient_profile: Optional[Dict]) -> Dict:
        """Enhance extraction results with additional OBGYN insights"""
        
        # Add medication interaction analysis
        interaction_analysis = await self._analyze_medication_interactions(
            extraction_result["medications"], 
            extraction_result["obgyn_context"]
        )
        
        # Add patient education content
        education_content = await self._generate_patient_education(
            extraction_result["medications"],
            extraction_result["obgyn_context"]
        )
        
        # Add clinical decision support
        clinical_support = await self._generate_clinical_decision_support(
            extraction_result["medications"],
            extraction_result["obgyn_context"],
            patient_profile
        )
        
        return {
            **extraction_result,
            "interaction_analysis": interaction_analysis,
            "patient_education": education_content,
            "clinical_decision_support": clinical_support,
            "enhanced_timestamp": datetime.now().isoformat()
        }
    
    async def _analyze_medication_interactions(self, medications: List[Dict], 
                                             obgyn_context: Dict) -> Dict:
        """Analyze medication interactions specific to OBGYN context"""
        
        interactions = {
            "contraceptive_interactions": [],
            "pregnancy_drug_interactions": [],
            "hormone_interactions": [],
            "overall_risk_level": "low"
        }
        
        medication_names = [med["medication"].get("canonical_name", med["original_term"]) 
                          for med in medications]
        
        pregnancy_stage = PregnancyStage(obgyn_context.get("pregnancy_stage", "not_pregnant"))
        
        # Check for contraceptive interactions
        has_contraceptives = any("contraception" in med.get("obgyn_category", "") 
                               for med in medications)
        
        if has_contraceptives:
            # Check for medications that reduce contraceptive effectiveness
            interacting_meds = []
            for med in medications:
                med_name = med["medication"].get("canonical_name", "").lower()
                drug_class = med["medication"].get("drug_class", [])
                
                # Antibiotics that may interact
                if any("antibiotic" in str(cls).lower() for cls in drug_class):
                    interacting_meds.append(med_name)
                
                # Anticonvulsants
                anticonvulsants = ["phenytoin", "carbamazepine", "phenobarbital"]
                if any(anticonv in med_name for anticonv in anticonvulsants):
                    interacting_meds.append(med_name)
            
            if interacting_meds:
                interactions["contraceptive_interactions"] = [
                    {
                        "medications": interacting_meds,
                        "interaction": "May reduce contraceptive effectiveness",
                        "recommendation": "Use backup contraception",
                        "severity": "moderate"
                    }
                ]
                interactions["overall_risk_level"] = "moderate"
        
        # Pregnancy-specific drug interactions
        if pregnancy_stage != PregnancyStage.NOT_PREGNANT:
            risky_combinations = []
            
            for med in medications:
                safety = med.get("safety_assessment", {})
                if safety.get("pregnancy_safety") in ["avoid", "contraindicated"]:
                    risky_combinations.append({
                        "medication": med["original_term"],
                        "concern": "Not recommended during pregnancy",
                        "severity": "high"
                    })
            
            if risky_combinations:
                interactions["pregnancy_drug_interactions"] = risky_combinations
                interactions["overall_risk_level"] = "high"
        
        return interactions
    
    async def _generate_patient_education(self, medications: List[Dict], 
                                        obgyn_context: Dict) -> Dict:
        """Generate patient education content"""
        
        education = {
            "medication_instructions": [],
            "lifestyle_recommendations": [],
            "warning_signs": [],
            "when_to_call_doctor": []
        }
        
        pregnancy_stage = PregnancyStage(obgyn_context.get("pregnancy_stage", "not_pregnant"))
        
        # Medication-specific education
        for med in medications:
            med_info = med["medication"]
            
            # Get patient education from medication database
            patient_education = med_info.get("patient_education", [])
            stage_specific_info = med_info.get("stage_specific_info", {})
            
            education_item = {
                "medication": med["original_term"],
                "instructions": patient_education,
                "special_considerations": stage_specific_info.get("special_considerations", [])
            }
            
            education["medication_instructions"].append(education_item)
        
        # Pregnancy-specific education
        if pregnancy_stage != PregnancyStage.NOT_PREGNANT:
            education["lifestyle_recommendations"].extend([
                "Take prenatal vitamins daily",
                "Avoid alcohol and smoking",
                "Limit caffeine intake",
                "Eat a balanced diet with folic acid"
            ])
            
            education["warning_signs"].extend([
                "Severe abdominal pain",
                "Heavy bleeding",
                "Severe headaches",
                "Vision changes",
                "Persistent vomiting"
            ])
            
            education["when_to_call_doctor"].extend([
                "Any concerning symptoms",
                "Questions about medication safety",
                "Changes in fetal movement (if applicable)",
                "Signs of preterm labor"
            ])
        
        # Condition-specific education
        conditions = obgyn_context.get("identified_conditions", [])
        
        if "pcos" in conditions:
            education["lifestyle_recommendations"].extend([
                "Maintain healthy weight",
                "Regular exercise",
                "Low glycemic index diet"
            ])
        
        if "contraception" in conditions:
            education["medication_instructions"].append({
                "medication": "Birth Control",
                "instructions": [
                    "Take at the same time every day",
                    "Use backup method if pill is missed",
                    "Annual check-ups recommended"
                ]
            })
        
        return education
    
    async def _generate_clinical_decision_support(self, medications: List[Dict], 
                                                obgyn_context: Dict,
                                                patient_profile: Optional[Dict]) -> Dict:
        """Generate clinical decision support recommendations"""
        
        clinical_support = {
            "recommended_monitoring": [],
            "suggested_lab_tests": [],
            "follow_up_schedule": [],
            "referral_recommendations": [],
            "risk_stratification": "low"
        }
        
        pregnancy_stage = PregnancyStage(obgyn_context.get("pregnancy_stage", "not_pregnant"))
        safety_flags = obgyn_context.get("safety_flags", [])
        
        # Pregnancy monitoring
        if pregnancy_stage != PregnancyStage.NOT_PREGNANT:
            if pregnancy_stage == PregnancyStage.FIRST_TRIMESTER:
                clinical_support["recommended_monitoring"].extend([
                    "First prenatal visit",
                    "Confirm pregnancy with lab work",
                    "Assess for high-risk factors"
                ])
                
                clinical_support["suggested_lab_tests"].extend([
                    "CBC with differential",
                    "Blood type and Rh",
                    "Rubella immunity",
                    "Hepatitis B surface antigen"
                ])
            
            elif pregnancy_stage == PregnancyStage.SECOND_TRIMESTER:
                clinical_support["recommended_monitoring"].extend([
                    "Anatomy ultrasound (18-22 weeks)",
                    "Glucose screening (24-28 weeks)"
                ])
            
            elif pregnancy_stage == PregnancyStage.THIRD_TRIMESTER:
                clinical_support["recommended_monitoring"].extend([
                    "Group B Strep screening (35-37 weeks)",
                    "Weekly visits after 36 weeks"
                ])
        
        # Medication-specific monitoring
        for med in medications:
            med_name = med["original_term"].lower()
            
            if "metformin" in med_name:
                clinical_support["suggested_lab_tests"].append("Kidney function tests")
                clinical_support["recommended_monitoring"].append("Blood glucose monitoring")
            
            if "birth control" in med_name or "contraceptive" in med_name:
                clinical_support["recommended_monitoring"].extend([
                    "Blood pressure monitoring",
                    "Annual gynecologic exam"
                ])
        
        # Risk stratification
        high_risk_indicators = len([flag for flag in safety_flags if flag["severity"] in ["high", "urgent"]])
        
        if high_risk_indicators > 0:
            clinical_support["risk_stratification"] = "high"
            clinical_support["referral_recommendations"].append("Urgent OB/GYN consultation")
        elif pregnancy_stage != PregnancyStage.NOT_PREGNANT:
            clinical_support["risk_stratification"] = "moderate"
            clinical_support["follow_up_schedule"].append("Standard prenatal care schedule")
        
        return clinical_support
    
    async def get_medication_safety_summary(self, medication_name: str, 
                                          pregnancy_stage: str = "not_pregnant") -> Dict:
        """Get focused medication safety summary for OBGYN context"""
        
        try:
            stage = PregnancyStage(pregnancy_stage)
            medication_info = await self.specialty_engine.get_obgyn_medication_info(
                medication_name, stage
            )
            
            return {
                "medication": medication_name,
                "pregnancy_stage": pregnancy_stage,
                "safety_summary": {
                    "pregnancy_category": medication_info.get("pregnancy_safety", "unknown"),
                    "pregnancy_safety_description": self.specialty_engine.pregnancy_categories.get(
                        medication_info.get("pregnancy_safety", "unknown"), {}
                    ).get("description", "Safety information not available"),
                    "breastfeeding_safety": medication_info.get("breastfeeding_safety", "unknown"),
                    "key_considerations": medication_info.get("patient_counseling_points", [])
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get safety summary for {medication_name}: {e}")
            return {"error": str(e)}
    
    async def analyze_pregnancy_medication_profile(self, medications: List[str], 
                                                 gestational_weeks: int) -> Dict:
        """Analyze complete medication profile for pregnant patient"""
        
        # Determine pregnancy stage from gestational weeks
        if gestational_weeks <= 13:
            stage = PregnancyStage.FIRST_TRIMESTER
        elif gestational_weeks <= 27:
            stage = PregnancyStage.SECOND_TRIMESTER
        else:
            stage = PregnancyStage.THIRD_TRIMESTER
        
        analysis = {
            "gestational_weeks": gestational_weeks,
            "pregnancy_stage": stage.value,
            "medication_analysis": [],
            "overall_safety_assessment": "unknown",
            "recommendations": []
        }
        
        try:
            safe_count = 0
            total_medications = len(medications)
            
            for med_name in medications:
                med_info = await self.specialty_engine.get_obgyn_medication_info(med_name, stage)
                
                safety_assessment = med_info.get("safety_assessment", {})
                pregnancy_category = med_info.get("pregnancy_safety", "unknown")
                
                med_analysis = {
                    "medication": med_name,
                    "pregnancy_category": pregnancy_category,
                    "safety_level": safety_assessment.get("overall_safety", "unknown"),
                    "recommendation": safety_assessment.get("recommendation", "consult_physician")
                }
                
                analysis["medication_analysis"].append(med_analysis)
                
                # Count safe medications
                if pregnancy_category in ["A", "B"]:
                    safe_count += 1
            
            # Overall safety assessment
            if safe_count == total_medications:
                analysis["overall_safety_assessment"] = "safe"
                analysis["recommendations"].append("Current medications appear safe for pregnancy")
            elif safe_count >= total_medications * 0.8:
                analysis["overall_safety_assessment"] = "mostly_safe"
                analysis["recommendations"].append("Most medications are safe, review any concerning ones with doctor")
            else:
                analysis["overall_safety_assessment"] = "needs_review"
                analysis["recommendations"].append("Several medications need review for pregnancy safety")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze pregnancy medication profile: {e}")
            return {"error": str(e)}

# =============================================================================
# Integration functions for backward compatibility with existing system
# =============================================================================

# Global instance
_obgyn_intelligence = OBGYNMedicalIntelligence()

async def process_obgyn_medical_text(text: str, session_id: str, 
                                   patient_profile: Optional[Dict] = None) -> Dict:
    """Main integration function for existing codebase"""
    return await _obgyn_intelligence.process_obgyn_text(text, session_id, patient_profile)

async def get_obgyn_medication_safety(medication_name: str, pregnancy_stage: str = "not_pregnant") -> Dict:
    """Get OBGYN medication safety information"""
    return await _obgyn_intelligence.get_medication_safety_summary(medication_name, pregnancy_stage)

async def analyze_pregnancy_medications(medications: List[str], gestational_weeks: int) -> Dict:
    """Analyze medication profile for pregnant patient"""
    return await _obgyn_intelligence.analyze_pregnancy_medication_profile(medications, gestational_weeks)