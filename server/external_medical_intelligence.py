import httpx
import asyncio
from typing import Dict, List, Optional
import json
from dataclasses import dataclass
from enum import Enum
import os

class MedicalSpecialty(Enum):
    OBGYN = "obgyn"
    CARDIOLOGY = "cardiology"
    PEDIATRICS = "pediatrics"
    EMERGENCY = "emergency"
    GENERAL = "general"

@dataclass
class ExternalMedicalAPI:
    name: str
    base_url: str
    api_key: Optional[str]
    specialty_focus: List[MedicalSpecialty]
    rate_limit: int  # requests per minute

class ScalableMedicalIntelligence:
    def __init__(self):
        self.external_apis = self._initialize_apis()
        self.cache = {}  # In-memory cache for frequently accessed terms
        self.specialty_context = None
        
    def _initialize_apis(self) -> List[ExternalMedicalAPI]:
        """Initialize connections to external medical databases"""
        return [
            # FDA Orange Book API - All approved medications
            ExternalMedicalAPI(
                name="fda_orange_book",
                base_url="https://api.fda.gov/drug/ndc.json",
                api_key=None,  # Public API
                specialty_focus=[MedicalSpecialty.GENERAL],
                rate_limit=240  # 240 requests per minute
            ),
            
            # RxNorm API - Medication terminology
            ExternalMedicalAPI(
                name="rxnorm",
                base_url="https://rxnav.nlm.nih.gov/REST",
                api_key=None,  # Public API
                specialty_focus=[MedicalSpecialty.GENERAL],
                rate_limit=20
            ),
            
            # OpenFDA Drug API - Comprehensive drug information
            ExternalMedicalAPI(
                name="openfda_drugs",
                base_url="https://api.fda.gov/drug/label.json",
                api_key=None,
                specialty_focus=[MedicalSpecialty.GENERAL],
                rate_limit=240
            ),
            
            # Custom OBGYN API (we'll build this)
            ExternalMedicalAPI(
                name="obgyn_speciality",
                base_url="https://api.talktor.com/medical/obgyn",  # Future endpoint
                api_key=os.getenv("TALKTOR_MEDICAL_API_KEY"),
                specialty_focus=[MedicalSpecialty.OBGYN],
                rate_limit=1000
            )
        ]
    
    async def identify_medication(self, drug_name: str, specialty: MedicalSpecialty = MedicalSpecialty.GENERAL) -> Dict:
        """
        Use external APIs to identify and get comprehensive info about a medication
        """
        # Check cache first
        cache_key = f"{drug_name}_{specialty.value}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Try multiple APIs for comprehensive information
        medication_info = {
            "drug_name": drug_name,
            "canonical_name": None,
            "brand_names": [],
            "generic_names": [],
            "drug_class": None,
            "indications": [],
            "contraindications": [],
            "pregnancy_category": None,  # Important for OBGYN
            "translations": {},
            "specialty_specific": {}
        }
        
        # 1. Try RxNorm for standardized drug names
        rxnorm_info = await self._query_rxnorm(drug_name)
        if rxnorm_info:
            medication_info.update(rxnorm_info)
        
        # 2. Try FDA APIs for detailed drug information
        fda_info = await self._query_fda_drugs(drug_name)
        if fda_info:
            medication_info.update(fda_info)
        
        # 3. Add specialty-specific information
        if specialty == MedicalSpecialty.OBGYN:
            obgyn_info = await self._get_obgyn_specific_info(drug_name)
            medication_info["specialty_specific"] = obgyn_info
        
        # Cache the result
        self.cache[cache_key] = medication_info
        
        return medication_info
    
    async def _query_rxnorm(self, drug_name: str) -> Dict:
        """Query RxNorm API for standardized drug terminology"""
        try:
            async with httpx.AsyncClient() as client:
                # Search for drug by name
                url = f"https://rxnav.nlm.nih.gov/REST/drugs.json?name={drug_name}"
                response = await client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Extract useful information
                    drug_group = data.get("drugGroup", {})
                    concept_group = drug_group.get("conceptGroup", [])
                    
                    if concept_group:
                        # Get the first concept (usually most relevant)
                        concept = concept_group[0].get("conceptProperties", [])
                        if concept:
                            return {
                                "canonical_name": concept[0].get("name"),
                                "rxcui": concept[0].get("rxcui"),  # Unique identifier
                                "synonym": concept[0].get("synonym", ""),
                                "generic_names": [c.get("name") for c in concept if c.get("tty") == "IN"],
                                "brand_names": [c.get("name") for c in concept if c.get("tty") == "BN"]
                            }
        except Exception as e:
            print(f"RxNorm API error: {e}")
            
        return {}
    
    async def _query_fda_drugs(self, drug_name: str) -> Dict:
        """Query FDA APIs for comprehensive drug information"""
        try:
            async with httpx.AsyncClient() as client:
                # Search FDA drug labels
                url = f"https://api.fda.gov/drug/label.json?search=openfda.brand_name:{drug_name}"
                response = await client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    
                    if results:
                        drug_info = results[0]  # Take first result
                        
                        return {
                            "indications": drug_info.get("indications_and_usage", []),
                            "contraindications": drug_info.get("contraindications", []),
                            "drug_class": drug_info.get("openfda", {}).get("pharm_class_epc", []),
                            "pregnancy_category": self._extract_pregnancy_category(drug_info),
                            "dosage_forms": drug_info.get("dosage_forms_and_strengths", [])
                        }
        except Exception as e:
            print(f"FDA API error: {e}")
            
        return {}
    
    async def _get_obgyn_specific_info(self, drug_name: str) -> Dict:
        """Get OBGYN-specific medication information"""
        
        # Hardcoded OBGYN-specific database (you'd expand this)
        obgyn_medications = {
            "folic_acid": {
                "pregnancy_trimester_safety": "all_trimesters",
                "breastfeeding_safety": "safe",
                "common_obgyn_uses": ["neural tube defect prevention", "anemia prevention"],
                "typical_dosage": "400-800 mcg daily",
                "patient_education": "Take before conception and during early pregnancy"
            },
            "metformin": {
                "pregnancy_trimester_safety": "generally_safe",
                "breastfeeding_safety": "safe", 
                "common_obgyn_uses": ["PCOS management", "gestational diabetes"],
                "typical_dosage": "500mg twice daily",
                "patient_education": "Monitor blood sugar levels regularly"
            },
            "prenatal_vitamins": {
                "pregnancy_trimester_safety": "all_trimesters",
                "breastfeeding_safety": "safe",
                "common_obgyn_uses": ["pregnancy nutrition support"],
                "typical_dosage": "one tablet daily",
                "patient_education": "Take with food to reduce nausea"
            }
        }
        
        # Normalize drug name for lookup
        normalized_name = drug_name.lower().replace(" ", "_")
        
        return obgyn_medications.get(normalized_name, {
            "pregnancy_trimester_safety": "consult_physician",
            "breastfeeding_safety": "consult_physician",
            "common_obgyn_uses": [],
            "typical_dosage": "as_prescribed",
            "patient_education": "Follow physician instructions"
        })
    
    def _extract_pregnancy_category(self, drug_info: Dict) -> str:
        """Extract pregnancy category from FDA drug information"""
        
        # Look for pregnancy information in various fields
        pregnancy_sections = [
            "pregnancy",
            "use_in_specific_populations", 
            "warnings_and_cautions"
        ]
        
        for section in pregnancy_sections:
            content = drug_info.get(section, [])
            if content and isinstance(content, list):
                text = " ".join(content).lower()
                
                # Look for pregnancy categories
                if "category a" in text:
                    return "A"
                elif "category b" in text:
                    return "B" 
                elif "category c" in text:
                    return "C"
                elif "category d" in text:
                    return "D"
                elif "category x" in text:
                    return "X"
        
        return "unknown"
    
    async def get_specialty_suggestions(self, text: str, specialty: MedicalSpecialty) -> List[str]:
        """Get specialty-specific follow-up questions and suggestions"""
        
        if specialty == MedicalSpecialty.OBGYN:
            return await self._get_obgyn_suggestions(text)
        elif specialty == MedicalSpecialty.CARDIOLOGY:
            return await self._get_cardiology_suggestions(text)
        else:
            return await self._get_general_suggestions(text)
    
    async def _get_obgyn_suggestions(self, text: str) -> List[str]:
        """OBGYN-specific follow-up questions"""
        text_lower = text.lower()
        suggestions = []
        
        # Pregnancy-related
        if any(word in text_lower for word in ["pregnant", "pregnancy", "expecting"]):
            suggestions.extend([
                "What is your current gestational age?",
                "Are you taking prenatal vitamins?",
                "Have you had any complications this pregnancy?",
                "When was your last prenatal appointment?"
            ])
        
        # Menstrual-related  
        if any(word in text_lower for word in ["period", "menstrual", "cycle"]):
            suggestions.extend([
                "When was your last menstrual period?",
                "How regular are your cycles?",
                "Are you experiencing any unusual symptoms?"
            ])
        
        # Contraception-related
        if any(word in text_lower for word in ["birth control", "contraception", "pill"]):
            suggestions.extend([
                "What type of contraception are you currently using?",
                "Are you experiencing any side effects?",
                "How long have you been using this method?"
            ])
        
        # Medication safety in pregnancy
        if any(word in text_lower for word in ["taking", "medication", "medicine"]):
            suggestions.extend([
                "Are you currently pregnant or trying to conceive?",
                "Are you breastfeeding?",
                "Have you discussed this medication with your OB/GYN?"
            ])
        
        return suggestions[:5]  # Return top 5 most relevant
    
    async def _get_cardiology_suggestions(self, text: str) -> List[str]:
        """Cardiology-specific suggestions (placeholder for future)"""
        return [
            "Do you have a history of heart disease?",
            "Are you experiencing chest pain?",
            "What is your blood pressure?"
        ]
    
    async def _get_general_suggestions(self, text: str) -> List[str]:
        """General medical suggestions"""
        return [
            "How long have you been experiencing these symptoms?",
            "Are you taking any other medications?",
            "Do you have any allergies?"
        ]

# Global instance
scalable_medical_intelligence = ScalableMedicalIntelligence()

# Integration functions for your existing endpoints
async def enhanced_medication_lookup(drug_name: str, specialty: str = "general") -> Dict:
    """Enhanced medication lookup using external APIs"""
    specialty_enum = MedicalSpecialty(specialty.lower())
    return await scalable_medical_intelligence.identify_medication(drug_name, specialty_enum)

async def get_specialty_context_suggestions(text: str, specialty: str = "general") -> List[str]:
    """Get specialty-specific suggestions"""
    specialty_enum = MedicalSpecialty(specialty.lower())
    return await scalable_medical_intelligence.get_specialty_suggestions(text, specialty_enum)