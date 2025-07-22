# =============================================================================
# services/medical_intelligence/specialties/obgyn/specialty_engine.py
# =============================================================================

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum
import re

# Import from core module
from ...core.api_client import ExternalMedicalAPIClient, MedicalSpecialty
from ...core.confidence import ConfidenceScorer

logger = logging.getLogger(__name__)

class PregnancyStage(Enum):
    PRECONCEPTION = "preconception"
    FIRST_TRIMESTER = "first_trimester"  # 0-13 weeks
    SECOND_TRIMESTER = "second_trimester"  # 14-27 weeks
    THIRD_TRIMESTER = "third_trimester"  # 28+ weeks
    POSTPARTUM = "postpartum"
    NOT_PREGNANT = "not_pregnant"
    UNKNOWN = "unknown"

class OBGYNCondition(Enum):
    PREGNANCY = "pregnancy"
    PCOS = "pcos"
    ENDOMETRIOSIS = "endometriosis"
    MENSTRUAL_DISORDERS = "menstrual_disorders"
    CONTRACEPTION = "contraception"
    FERTILITY = "fertility"
    MENOPAUSE = "menopause"
    STI_STD = "sti_std"
    GYNECOLOGIC_CANCER = "gynecologic_cancer"
    GENERAL_GYNECOLOGY = "general_gynecology"

class OBGYNSpecialtyEngine:
    """
    OBGYN-specific medical intelligence engine
    Provides specialized medication analysis, safety assessments, and patient education
    """
    
    def __init__(self):
        self.api_client = ExternalMedicalAPIClient()
        self.confidence_scorer = ConfidenceScorer()
        
        # OBGYN-specific medication database
        self.obgyn_medications = self._initialize_obgyn_database()
        
        # Pregnancy safety categories
        self.pregnancy_categories = {
            "A": {"safety": "safe", "description": "Adequate and well-controlled studies show no risk"},
            "B": {"safety": "probably_safe", "description": "Animal studies show no risk, human studies lacking"},
            "C": {"safety": "use_with_caution", "description": "Risk cannot be ruled out"},
            "D": {"safety": "risky", "description": "Positive evidence of risk, but benefits may warrant use"},
            "X": {"safety": "contraindicated", "description": "Contraindicated in pregnancy"}
        }
    
    def _initialize_obgyn_database(self) -> Dict:
        """Initialize comprehensive OBGYN medication database"""
        return {
            # Prenatal vitamins and supplements
            "folic_acid": {
                "category": "prenatal_supplement",
                "pregnancy_safety": "A",
                "breastfeeding_safety": "safe",
                "common_uses": ["neural tube defect prevention", "anemia prevention"],
                "dosing": {
                    "preconception": "400-800 mcg daily",
                    "pregnancy": "400-800 mcg daily",
                    "lactation": "500 mcg daily"
                },
                "patient_education": [
                    "Start before conception if possible",
                    "Take with or without food",
                    "Continue throughout pregnancy"
                ],
                "contraindications": ["vitamin B12 deficiency (mask symptoms)"],
                "interactions": ["phenytoin", "methotrexate"]
            },
            
            "prenatal_vitamins": {
                "category": "prenatal_supplement",
                "pregnancy_safety": "A",
                "breastfeeding_safety": "safe",
                "common_uses": ["pregnancy nutrition support", "prevent birth defects"],
                "dosing": {
                    "preconception": "one tablet daily",
                    "pregnancy": "one tablet daily",
                    "lactation": "one tablet daily"
                },
                "patient_education": [
                    "Take with food to reduce nausea",
                    "Iron may cause constipation - increase fiber",
                    "Don't take with coffee or tea (reduces iron absorption)"
                ],
                "contraindications": ["iron overload disorders"],
                "side_effects": ["nausea", "constipation", "dark stools"]
            },
            
            # Hormonal contraceptives
            "birth_control": {
                "category": "contraception",
                "pregnancy_safety": "X",
                "breastfeeding_safety": "varies_by_type",
                "common_uses": ["pregnancy prevention", "menstrual regulation", "acne treatment"],
                "types": {
                    "combined_pill": {
                        "breastfeeding_safety": "avoid_first_6_weeks",
                        "patient_education": ["Take at same time daily", "Use backup method if vomiting within 2 hours"]
                    },
                    "progestin_only": {
                        "breastfeeding_safety": "safe",
                        "patient_education": ["Must take at exact same time daily", "No pill-free interval"]
                    }
                },
                "contraindications": ["active pregnancy", "uncontrolled hypertension", "migraine with aura"],
                "side_effects": ["breakthrough bleeding", "breast tenderness", "mood changes"]
            },
            
            # PCOS medications
            "metformin": {
                "category": "diabetes_pcos",
                "pregnancy_safety": "B",
                "breastfeeding_safety": "safe",
                "common_uses": ["PCOS management", "gestational diabetes", "insulin resistance"],
                "dosing": {
                    "pcos": "500mg twice daily, titrate to 1000mg twice daily",
                    "gestational_diabetes": "500mg twice daily, adjust as needed"
                },
                "patient_education": [
                    "Take with meals to reduce GI upset",
                    "May improve ovulation in PCOS",
                    "Monitor blood sugar if diabetic"
                ],
                "contraindications": ["kidney disease", "severe heart failure"],
                "side_effects": ["diarrhea", "nausea", "metallic taste"]
            },
            
            # Labor and delivery
            "epidural": {
                "category": "labor_analgesia",
                "pregnancy_safety": "B",
                "breastfeeding_safety": "safe",
                "common_uses": ["labor pain management"],
                "patient_education": [
                    "May slow labor progression initially",
                    "You can still feel pressure during pushing",
                    "Rare risk of spinal headache"
                ],
                "contraindications": ["bleeding disorders", "infection at injection site"],
                "side_effects": ["temporary leg weakness", "blood pressure changes"]
            },
            
            # Antibiotics (pregnancy-safe)
            "amoxicillin": {
                "category": "antibiotic",
                "pregnancy_safety": "B",
                "breastfeeding_safety": "safe",
                "common_uses": ["UTI treatment", "bacterial infections"],
                "dosing": {
                    "uti": "500mg three times daily for 7 days",
                    "general": "250-500mg three times daily"
                },
                "patient_education": [
                    "Complete full course even if feeling better",
                    "Take with food if stomach upset",
                    "May reduce birth control effectiveness"
                ],
                "contraindications": ["penicillin allergy"],
                "side_effects": ["diarrhea", "yeast infections", "rash"]
            },
            
            # Fertility medications
            "clomid": {
                "category": "fertility",
                "pregnancy_safety": "X",
                "breastfeeding_safety": "unknown",
                "common_uses": ["ovulation induction", "fertility treatment"],
                "dosing": {
                    "fertility": "50mg daily for 5 days, cycle days 3-7"
                },
                "patient_education": [
                    "Stop if pregnancy occurs",
                    "Monitor ovulation with tracking",
                    "May increase chance of multiple births"
                ],
                "contraindications": ["pregnancy", "liver disease", "abnormal bleeding"],
                "side_effects": ["hot flashes", "mood swings", "visual disturbances"]
            }
        }
    
    async def analyze_obgyn_context(self, text: str, patient_profile: Optional[Dict] = None) -> Dict:
        """
        Analyze text for OBGYN-specific context and medical conditions
        """
        text_lower = text.lower()
        
        # Detect pregnancy stage
        pregnancy_stage = self._detect_pregnancy_stage(text_lower, patient_profile)
        
        # Identify OBGYN conditions
        conditions = self._identify_obgyn_conditions(text_lower)
        
        # Extract menstrual cycle information
        cycle_info = self._extract_cycle_information(text_lower)
        
        # Assess medication safety concerns
        safety_flags = self._assess_safety_flags(text_lower, pregnancy_stage)
        
        return {
            "pregnancy_stage": pregnancy_stage.value,
            "identified_conditions": [c.value for c in conditions],
            "menstrual_cycle_info": cycle_info,
            "safety_flags": safety_flags,
            "specialty_context": "obgyn",
            "requires_specialist_review": len(safety_flags) > 0 or pregnancy_stage != PregnancyStage.NOT_PREGNANT
        }
    
    def _detect_pregnancy_stage(self, text: str, patient_profile: Optional[Dict] = None) -> PregnancyStage:
        """ENHANCED: Detect pregnancy stage with Spanish support"""
        text_lower = text.lower()
        
        # BILINGUAL pregnancy patterns
        pregnancy_patterns = {
            PregnancyStage.PRECONCEPTION: [
                # English
                "trying to conceive", "planning pregnancy", "want to get pregnant",
                "before conception", "preconception",
                # Spanish
                "tratando de concebir", "planificando embarazo", "quiero quedar embarazada",
                "antes de la concepción", "preconcepción"
            ],
            PregnancyStage.FIRST_TRIMESTER: [
                # English
                "first trimester", "6 weeks pregnant", "8 weeks pregnant",
                "10 weeks pregnant", "12 weeks pregnant", "morning sickness",
                # Spanish  
                "primer trimestre", "6 semanas embarazada", "8 semanas embarazada",
                "10 semanas embarazada", "12 semanas embarazada", "náuseas matutinas"
            ],
            PregnancyStage.SECOND_TRIMESTER: [
                # English
                "second trimester", "16 weeks pregnant", "20 weeks pregnant",
                "24 weeks pregnant", "anatomy scan",
                # Spanish
                "segundo trimestre", "16 semanas embarazada", "20 semanas embarazada", 
                "24 semanas embarazada", "ultrasonido anatómico"
            ],
            PregnancyStage.THIRD_TRIMESTER: [
                # English
                "third trimester", "32 weeks pregnant", "36 weeks pregnant",
                "full term", "due date", "labor",
                # Spanish
                "tercer trimestre", "32 semanas embarazada", "36 semanas embarazada",
                "a término", "fecha de parto", "trabajo de parto"
            ],
            PregnancyStage.POSTPARTUM: [
                # English
                "postpartum", "after delivery", "breastfeeding", "nursing",
                "gave birth", "delivered",
                # Spanish
                "posparto", "después del parto", "amamantando", "lactancia",
                "dio a luz", "tuvo el bebé"
            ]
        }
        
        # Check for specific stage indicators (bilingual)
        for stage, patterns in pregnancy_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                return stage
        
        # ENHANCED: General pregnancy indicators (bilingual)
        english_pregnancy_terms = ["pregnant", "pregnancy", "expecting", "prenatal"]
        spanish_pregnancy_terms = ["embarazada", "embarazo", "esperando bebé", "prenatal"]
        
        if (any(word in text_lower for word in english_pregnancy_terms) or 
            any(word in text_lower for word in spanish_pregnancy_terms)):
            return PregnancyStage.UNKNOWN  # Pregnant but stage unclear
        
        # Check patient profile if available
        if patient_profile:
            if patient_profile.get("pregnancy_status"):
                weeks = patient_profile.get("gestational_weeks", 0)
                if weeks <= 13:
                    return PregnancyStage.FIRST_TRIMESTER
                elif weeks <= 27:
                    return PregnancyStage.SECOND_TRIMESTER
                else:
                    return PregnancyStage.THIRD_TRIMESTER
        
        return PregnancyStage.NOT_PREGNANT
    
    def _identify_obgyn_conditions(self, text: str) -> List[OBGYNCondition]:
        """ENHANCED: Identify OBGYN conditions with Spanish support"""
        conditions = []
        
        # BILINGUAL condition patterns
        condition_patterns = {
            OBGYNCondition.PCOS: [
                # English
                "pcos", "polycystic ovary", "irregular periods", "hirsutism",
                # Spanish
                "ovarios poliquísticos", "períodos irregulares", "reglas irregulares"
            ],
            OBGYNCondition.PREGNANCY: [
                # English
                "pregnant", "pregnancy", "prenatal", "expecting",
                # Spanish
                "embarazada", "embarazo", "prenatal", "esperando bebé"
            ],
            OBGYNCondition.CONTRACEPTION: [
                # English
                "birth control", "contraception", "prevent pregnancy",
                # Spanish
                "anticonceptivos", "control natal", "prevenir embarazo", "píldora"
            ],
            OBGYNCondition.MENSTRUAL_DISORDERS: [
                # English
                "irregular periods", "heavy bleeding", "amenorrhea",
                # Spanish
                "períodos irregulares", "reglas irregulares", "sangrado abundante", "amenorrea"
            ],
            OBGYNCondition.FERTILITY: [
                # English
                "fertility", "trying to conceive", "ovulation", "infertility",
                # Spanish
                "fertilidad", "tratando de concebir", "ovulación", "infertilidad"
            ]
        }
        
        for condition, patterns in condition_patterns.items():
            if any(pattern in text for pattern in patterns):
                conditions.append(condition)
        
        return conditions if conditions else [OBGYNCondition.GENERAL_GYNECOLOGY]
    
    def _extract_cycle_information(self, text: str) -> Dict:
        """Extract menstrual cycle information from text"""
        cycle_info = {
            "last_menstrual_period": None,
            "cycle_length": None,
            "cycle_regularity": None,
            "symptoms": []
        }
        
        # Look for LMP (Last Menstrual Period)
        lmp_patterns = [
            r"last period was (\d+) days? ago",
            r"lmp was (\w+) (\d+)",
            r"period started (\d+) days? ago"
        ]
        
        for pattern in lmp_patterns:
            match = re.search(pattern, text)
            if match:
                cycle_info["last_menstrual_period"] = match.groups()
                break
        
        # Look for cycle length
        cycle_patterns = [
            r"(\d+) day cycle",
            r"cycles? (?:are|is) (\d+) days?"
        ]
        
        for pattern in cycle_patterns:
            match = re.search(pattern, text)
            if match:
                cycle_info["cycle_length"] = int(match.group(1))
                break
        
        # Regularity indicators
        if any(word in text for word in ["irregular", "unpredictable"]):
            cycle_info["cycle_regularity"] = "irregular"
        elif any(word in text for word in ["regular", "consistent"]):
            cycle_info["cycle_regularity"] = "regular"
        
        # Symptoms
        symptoms = []
        symptom_patterns = {
            "cramping": ["cramps", "cramping", "painful"],
            "heavy_bleeding": ["heavy", "flooding", "clots"],
            "light_bleeding": ["light", "spotting"],
            "pms": ["pms", "mood swings", "bloating"]
        }
        
        for symptom, patterns in symptom_patterns.items():
            if any(pattern in text for pattern in patterns):
                symptoms.append(symptom)
        
        cycle_info["symptoms"] = symptoms
        return cycle_info
    
    def _assess_safety_flags(self, text: str, pregnancy_stage: PregnancyStage) -> List[Dict]:
        """ENHANCED: Safety flags with Spanish support"""
        flags = []
        text_lower = text.lower()
        
        # BILINGUAL pregnancy-specific safety flags
        if pregnancy_stage in [PregnancyStage.FIRST_TRIMESTER, PregnancyStage.SECOND_TRIMESTER, 
                            PregnancyStage.THIRD_TRIMESTER, PregnancyStage.UNKNOWN]:
            
            # High-risk medications (bilingual detection)
            risky_terms_english = ["ibuprofen", "aspirin", "accutane", "warfarin", "ace inhibitor"]
            risky_terms_spanish = ["ibuprofeno", "aspirina", "warfarina"]
            
            all_risky_terms = risky_terms_english + risky_terms_spanish
            
            for term in all_risky_terms:
                if term in text_lower:
                    flags.append({
                        "type": "medication_pregnancy_risk",
                        "medication": term,
                        "severity": "high",
                        "message": f"{term} may not be safe during pregnancy / {term} puede no ser seguro durante el embarazo",
                        "bilingual": True
                    })
            
            # Alcohol/substance use (bilingual)
            substance_terms_english = ["alcohol", "drinking", "smoking"]
            substance_terms_spanish = ["alcohol", "bebiendo", "fumando", "cigarrillos"]
            
            if any(word in text_lower for word in (substance_terms_english + substance_terms_spanish)):
                flags.append({
                    "type": "substance_use_pregnancy",
                    "severity": "high", 
                    "message": "Alcohol and smoking should be avoided during pregnancy / Alcohol y fumar deben evitarse durante el embarazo",
                    "bilingual": True
                })
        
        return flags
    
    async def get_obgyn_medication_info(self, medication_name: str, pregnancy_stage: PregnancyStage = PregnancyStage.NOT_PREGNANT) -> Dict:
        """Get OBGYN-specific medication information"""
        
        # Normalize medication name
        med_name = medication_name.lower().replace(" ", "_")
        
        # Check local OBGYN database first
        if med_name in self.obgyn_medications:
            local_info = self.obgyn_medications[med_name]
            
            # Enhance with pregnancy stage-specific information
            enhanced_info = {
                **local_info,
                "stage_specific_info": self._get_stage_specific_info(local_info, pregnancy_stage),
                "safety_assessment": self._assess_medication_safety(local_info, pregnancy_stage),
                "patient_counseling_points": self._generate_counseling_points(local_info, pregnancy_stage)
            }
            
            return enhanced_info
        
        # Fall back to general API lookup with OBGYN enhancement
        try:
            api_result = await self.api_client.lookup_medication(medication_name, "obgyn")
            
            # CRITICAL FIX: Handle None/empty API results
            if not api_result or api_result is None:
                return {"error": f"No information available for {medication_name}"}
            
            # Ensure required fields exist
            api_result.setdefault("indications", [])
            api_result.setdefault("drug_class", [])
            api_result.setdefault("contraindications", [])
            
            # Enhance API result with OBGYN-specific analysis
            enhanced_result = {
                **api_result,
                "obgyn_analysis": await self._analyze_medication_for_obgyn(api_result, pregnancy_stage),
                "safety_assessment": self._assess_general_medication_safety(api_result, pregnancy_stage)
            }
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Failed to get medication info for {medication_name}: {e}")
            return {"error": f"Could not retrieve information for {medication_name}"}
    
    def _get_stage_specific_info(self, medication_info: Dict, stage: PregnancyStage) -> Dict:
        """Get pregnancy stage-specific medication information"""
        
        stage_info = {
            "recommended_dosing": medication_info.get("dosing", {}).get(stage.value),
            "safety_level": "unknown",
            "special_considerations": []
        }
        
        pregnancy_safety = medication_info.get("pregnancy_safety", "unknown")
        
        if stage in [PregnancyStage.FIRST_TRIMESTER, PregnancyStage.SECOND_TRIMESTER, PregnancyStage.THIRD_TRIMESTER]:
            stage_info["safety_level"] = self.pregnancy_categories.get(pregnancy_safety, {}).get("safety", "unknown")
            
            # First trimester special considerations
            if stage == PregnancyStage.FIRST_TRIMESTER:
                stage_info["special_considerations"].append("Critical organ development period")
                if pregnancy_safety in ["D", "X"]:
                    stage_info["special_considerations"].append("Avoid during organogenesis")
            
            # Third trimester considerations
            elif stage == PregnancyStage.THIRD_TRIMESTER:
                if medication_info.get("category") == "contraception":
                    stage_info["special_considerations"].append("Discontinue immediately")
        
        elif stage == PregnancyStage.POSTPARTUM:
            stage_info["safety_level"] = medication_info.get("breastfeeding_safety", "unknown")
            stage_info["special_considerations"].append("Consider breastfeeding compatibility")
        
        return stage_info
    
    def _assess_medication_safety(self, medication_info: Dict, stage: PregnancyStage) -> Dict:
        """Assess medication safety for specific pregnancy stage"""
        
        safety_assessment = {
            "overall_safety": "unknown",
            "recommendation": "consult_physician",
            "risk_level": "unknown",
            "key_concerns": []
        }
        
        pregnancy_category = medication_info.get("pregnancy_safety", "unknown")
        
        if stage in [PregnancyStage.FIRST_TRIMESTER, PregnancyStage.SECOND_TRIMESTER, PregnancyStage.THIRD_TRIMESTER]:
            
            category_mapping = {
                "A": {"safety": "safe", "recommendation": "safe_to_use", "risk": "minimal"},
                "B": {"safety": "probably_safe", "recommendation": "generally_safe", "risk": "low"},
                "C": {"safety": "use_with_caution", "recommendation": "risk_benefit_analysis", "risk": "moderate"},
                "D": {"safety": "risky", "recommendation": "avoid_unless_essential", "risk": "high"},
                "X": {"safety": "contraindicated", "recommendation": "do_not_use", "risk": "very_high"}
            }
            
            if pregnancy_category in category_mapping:
                mapping = category_mapping[pregnancy_category]
                safety_assessment.update({
                    "overall_safety": mapping["safety"],
                    "recommendation": mapping["recommendation"],
                    "risk_level": mapping["risk"]
                })
                
                # Add specific concerns
                if pregnancy_category == "X":
                    safety_assessment["key_concerns"].append("Known to cause birth defects")
                elif pregnancy_category == "D":
                    safety_assessment["key_concerns"].append("Potential for serious adverse effects")
        
        return safety_assessment
    
    def _generate_counseling_points(self, medication_info: Dict, stage: PregnancyStage) -> List[str]:
        """Generate patient counseling points specific to pregnancy stage"""
        
        counseling_points = []
        
        # Add general patient education
        counseling_points.extend(medication_info.get("patient_education", []))
        
        # Add stage-specific counseling
        if stage == PregnancyStage.PRECONCEPTION:
            counseling_points.append("Consider medication safety before conception")
            if medication_info.get("pregnancy_safety") in ["D", "X"]:
                counseling_points.append("Discuss alternative medications with your doctor")
        
        elif stage in [PregnancyStage.FIRST_TRIMESTER, PregnancyStage.SECOND_TRIMESTER, PregnancyStage.THIRD_TRIMESTER]:
            counseling_points.append("Always inform healthcare providers about your pregnancy")
            
            if medication_info.get("pregnancy_safety") == "A":
                counseling_points.append("This medication is considered safe during pregnancy")
            elif medication_info.get("pregnancy_safety") in ["D", "X"]:
                counseling_points.append("This medication should be avoided during pregnancy")
        
        elif stage == PregnancyStage.POSTPARTUM:
            if medication_info.get("breastfeeding_safety") == "safe":
                counseling_points.append("Safe to use while breastfeeding")
            else:
                counseling_points.append("Discuss breastfeeding safety with your healthcare provider")
        
        return counseling_points
    
    async def _analyze_medication_for_obgyn(self, api_result: Dict, stage: PregnancyStage) -> Dict:
        """Analyze general medication API result for OBGYN context"""
        
        analysis = {
            "obgyn_relevance": "unknown",
            "pregnancy_considerations": [],
            "breastfeeding_considerations": [],
            "contraceptive_interactions": False
        }
        
        # Check for OBGYN relevance
        indications = api_result.get("indications", [])
        obgyn_keywords = ["pregnancy", "contraception", "menstrual", "ovarian", "uterine", "vaginal"]
        
        if any(keyword in " ".join(indications).lower() for keyword in obgyn_keywords):
            analysis["obgyn_relevance"] = "high"
        
        # Pregnancy considerations
        pregnancy_category = api_result.get("pregnancy_category", "unknown")
        if pregnancy_category != "unknown":
            analysis["pregnancy_considerations"].append(
                f"Pregnancy Category {pregnancy_category}: {self.pregnancy_categories.get(pregnancy_category, {}).get('description', 'See prescribing information')}"
            )
        
        # Check for contraceptive interactions
        drug_class = api_result.get("drug_class", [])
        if any("antibiotic" in str(cls).lower() for cls in drug_class):
            analysis["contraceptive_interactions"] = True
            analysis["pregnancy_considerations"].append("May reduce effectiveness of hormonal contraceptives")
        
        return analysis
    
    def _assess_general_medication_safety(self, api_result: Dict, stage: PregnancyStage) -> Dict:
        """Assess safety of general medication for pregnancy stage"""
        
        pregnancy_category = api_result.get("pregnancy_category", "unknown")
        
        if stage in [PregnancyStage.FIRST_TRIMESTER, PregnancyStage.SECOND_TRIMESTER, PregnancyStage.THIRD_TRIMESTER]:
            return self._assess_medication_safety({"pregnancy_safety": pregnancy_category}, stage)
        
        return {
            "overall_safety": "consult_physician",
            "recommendation": "discuss_with_doctor",
            "risk_level": "unknown",
            "key_concerns": ["Pregnancy safety not established"]
        }