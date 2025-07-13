from typing import Dict, List, Optional, Tuple
import json
import re
from dataclasses import dataclass
from enum import Enum
import difflib

class MedicalCategory(Enum):
    MEDICATION = "medication"
    SYMPTOM = "symptom"
    BODY_PART = "body_part"
    PROCEDURE = "procedure"
    CONDITION = "condition"
    MEASUREMENT = "measurement"

@dataclass
class MedicalTerm:
    canonical_name: str
    category: MedicalCategory
    aliases: List[str]
    translations: Dict[str, str]  # language_code -> translation
    pronunciation_variants: List[str]
    context_clues: List[str]
    confidence_boost: float = 1.0

class MedicalIntelligence:
    def __init__(self):
        self.medical_database = self._initialize_medical_database()
        self.fuzzy_match_threshold = 0.8
        
    def _initialize_medical_database(self) -> Dict[str, List[MedicalTerm]]:
        """Initialize comprehensive medical terminology database"""
        
        # Common medications with variations
        medications = [
            MedicalTerm(
                canonical_name="acetaminophen",
                category=MedicalCategory.MEDICATION,
                aliases=["tylenol", "paracetamol", "panadol"],
                translations={
                    "es": "acetaminofén",
                    "en": "acetaminophen"
                },
                pronunciation_variants=[
                    "acetaminophen", "acetaminofen", "acetiminophen",
                    "tylenol", "tylanol", "tilenal"
                ],
                context_clues=["pain relief", "fever reducer", "500mg", "tablet"]
            ),
            MedicalTerm(
                canonical_name="ibuprofen",
                category=MedicalCategory.MEDICATION,
                aliases=["advil", "motrin", "nurofen"],
                translations={
                    "es": "ibuprofeno",
                    "en": "ibuprofen"
                },
                pronunciation_variants=[
                    "ibuprofen", "ibuprofin", "ibuprofen", "advil", "advill"
                ],
                context_clues=["anti-inflammatory", "200mg", "400mg", "gel caps"]
            ),
            MedicalTerm(
                canonical_name="azithromycin",
                category=MedicalCategory.MEDICATION,
                aliases=["z-pack", "zithromax"],
                translations={
                    "es": "azitromicina",
                    "en": "azithromycin"
                },
                pronunciation_variants=[
                    "azithromycin", "azithromicin", "azith-row-mycin", 
                    "z pack", "z-pack", "zithromax"
                ],
                context_clues=["antibiotic", "5 days", "infection", "bacterial"]
            ),
            MedicalTerm(
                canonical_name="metformin",
                category=MedicalCategory.MEDICATION,
                aliases=["glucophage"],
                translations={
                    "es": "metformina",
                    "en": "metformin"
                },
                pronunciation_variants=[
                    "metformin", "metformina", "glucophage"
                ],
                context_clues=["diabetes", "blood sugar", "500mg", "twice daily"]
            )
        ]
        
        # Common symptoms
        symptoms = [
            MedicalTerm(
                canonical_name="chest_pain",
                category=MedicalCategory.SYMPTOM,
                aliases=["chest discomfort", "heart pain"],
                translations={
                    "es": "dolor en el pecho",
                    "en": "chest pain"
                },
                pronunciation_variants=["chest pain", "chest ache"],
                context_clues=["heart", "breathing", "pressure", "tightness"]
            ),
            MedicalTerm(
                canonical_name="shortness_of_breath",
                category=MedicalCategory.SYMPTOM,
                aliases=["difficulty breathing", "breathlessness", "dyspnea"],
                translations={
                    "es": "dificultad para respirar",
                    "en": "shortness of breath"
                },
                pronunciation_variants=["short of breath", "can't breathe"],
                context_clues=["lungs", "oxygen", "winded", "breathing"]
            )
        ]
        
        # Body parts
        body_parts = [
            MedicalTerm(
                canonical_name="abdomen",
                category=MedicalCategory.BODY_PART,
                aliases=["belly", "stomach area", "tummy"],
                translations={
                    "es": "abdomen",
                    "en": "abdomen"
                },
                pronunciation_variants=["abdomen", "belly", "stomach"],
                context_clues=["digestive", "intestines", "organs"]
            )
        ]
        
        # Medical procedures
        procedures = [
            MedicalTerm(
                canonical_name="blood_pressure_check",
                category=MedicalCategory.PROCEDURE,
                aliases=["BP check", "pressure reading"],
                translations={
                    "es": "tomar la presión arterial",
                    "en": "blood pressure check"
                },
                pronunciation_variants=["blood pressure", "BP check"],
                context_clues=["cuff", "systolic", "diastolic", "mmHg"]
            )
        ]
        
        return {
            "medications": medications,
            "symptoms": symptoms,
            "body_parts": body_parts,
            "procedures": procedures
        }
    
    def extract_medical_terms(self, text: str, source_language: str = "en") -> List[Dict]:
        """Extract and categorize medical terms from text"""
        text_lower = text.lower()
        found_terms = []
        
        # Search through all categories
        for category, terms in self.medical_database.items():
            for term in terms:
                matches = self._find_term_matches(text_lower, term)
                if matches:
                    for match in matches:
                        found_terms.append({
                            "original_text": match["matched_text"],
                            "canonical_name": term.canonical_name,
                            "category": term.category.value,
                            "confidence": match["confidence"],
                            "translation": term.translations.get(source_language, term.canonical_name),
                            "context_clues": term.context_clues,
                            "start_pos": match["start_pos"],
                            "end_pos": match["end_pos"]
                        })
        
        # Sort by confidence and remove duplicates
        found_terms.sort(key=lambda x: x["confidence"], reverse=True)
        return self._remove_duplicate_matches(found_terms)
    
    def _find_term_matches(self, text: str, term: MedicalTerm) -> List[Dict]:
        """Find all matches for a medical term in text"""
        matches = []
        
        # Check canonical name and aliases
        all_variants = [term.canonical_name] + term.aliases + term.pronunciation_variants
        
        for variant in all_variants:
            variant_lower = variant.lower()
            
            # Exact match
            if variant_lower in text:
                start_pos = text.find(variant_lower)
                matches.append({
                    "matched_text": variant,
                    "confidence": 1.0,
                    "start_pos": start_pos,
                    "end_pos": start_pos + len(variant_lower)
                })
            
            # Fuzzy match for misspellings
            else:
                fuzzy_matches = self._fuzzy_search(text, variant_lower)
                matches.extend(fuzzy_matches)
        
        # Boost confidence if context clues are present
        for match in matches:
            context_boost = self._calculate_context_boost(text, term.context_clues)
            match["confidence"] *= context_boost
        
        return matches
    
    def _fuzzy_search(self, text: str, target: str) -> List[Dict]:
        """Find fuzzy matches for misspelled medical terms"""
        words = text.split()
        matches = []
        
        for i, word in enumerate(words):
            # Single word fuzzy match
            similarity = difflib.SequenceMatcher(None, word, target).ratio()
            if similarity >= self.fuzzy_match_threshold:
                start_pos = text.find(word)
                matches.append({
                    "matched_text": word,
                    "confidence": similarity,
                    "start_pos": start_pos,
                    "end_pos": start_pos + len(word)
                })
            
            # Multi-word fuzzy match (for compound terms)
            if i < len(words) - 1:
                two_word = f"{word} {words[i+1]}"
                similarity = difflib.SequenceMatcher(None, two_word, target).ratio()
                if similarity >= self.fuzzy_match_threshold:
                    start_pos = text.find(two_word)
                    matches.append({
                        "matched_text": two_word,
                        "confidence": similarity,
                        "start_pos": start_pos,
                        "end_pos": start_pos + len(two_word)
                    })
        
        return matches
    
    def _calculate_context_boost(self, text: str, context_clues: List[str]) -> float:
        """Boost confidence if context clues are present"""
        boost = 1.0
        text_lower = text.lower()
        
        for clue in context_clues:
            if clue.lower() in text_lower:
                boost += 0.2  # 20% boost per context clue
        
        return min(boost, 2.0)  # Cap at 2x boost
    
    def _remove_duplicate_matches(self, matches: List[Dict]) -> List[Dict]:
        """Remove overlapping or duplicate matches"""
        if not matches:
            return matches
        
        # Sort by position
        matches.sort(key=lambda x: x["start_pos"])
        
        filtered = [matches[0]]
        
        for match in matches[1:]:
            last_match = filtered[-1]
            
            # Check for overlap
            if (match["start_pos"] >= last_match["end_pos"] or 
                match["confidence"] > last_match["confidence"] * 1.5):
                filtered.append(match)
        
        return filtered
    
    def enhance_translation(self, original_text: str, translated_text: str, 
                          source_lang: str, target_lang: str) -> Dict:
        """Enhance translation with medical context"""
        
        # Extract medical terms from original
        medical_terms = self.extract_medical_terms(original_text, source_lang)
        
        enhanced_translation = translated_text
        medical_notes = []
        
        # Improve translation of medical terms
        for term in medical_terms:
            if term["confidence"] > 0.7:  # High confidence medical terms
                canonical = term["canonical_name"]
                
                # Get proper medical translation
                if canonical in self.medical_database.get("medications", []):
                    proper_translation = self._get_medical_translation(
                        canonical, target_lang, MedicalCategory.MEDICATION
                    )
                    
                    if proper_translation:
                        # Replace in translation if needed
                        enhanced_translation = self._replace_medical_term(
                            enhanced_translation, term["original_text"], 
                            proper_translation, target_lang
                        )
                        
                        medical_notes.append({
                            "term": canonical,
                            "category": term["category"],
                            "translation": proper_translation,
                            "note": f"Medical term: {canonical}"
                        })
        
        return {
            "enhanced_translation": enhanced_translation,
            "medical_terms_found": medical_terms,
            "medical_notes": medical_notes,
            "medical_accuracy_score": self._calculate_medical_accuracy(medical_terms)
        }
    
    def _get_medical_translation(self, canonical_name: str, target_lang: str, 
                               category: MedicalCategory) -> Optional[str]:
        """Get accurate medical translation for a term"""
        category_key = f"{category.value}s"  # medications, symptoms, etc.
        
        if category_key in self.medical_database:
            for term in self.medical_database[category_key]:
                if term.canonical_name == canonical_name:
                    return term.translations.get(target_lang)
        
        return None
    
    def _replace_medical_term(self, text: str, original: str, 
                            replacement: str, target_lang: str) -> str:
        """Intelligently replace medical terms in translation"""
        # Simple replacement for now - could be made more sophisticated
        return text.replace(original.lower(), replacement.lower())
    
    def _calculate_medical_accuracy(self, medical_terms: List[Dict]) -> float:
        """Calculate overall medical accuracy score"""
        if not medical_terms:
            return 1.0
        
        total_confidence = sum(term["confidence"] for term in medical_terms)
        return min(total_confidence / len(medical_terms), 1.0)
    
    def suggest_follow_up_questions(self, medical_terms: List[Dict], 
                                  context: str = "general") -> List[str]:
        """Suggest relevant follow-up questions based on medical terms found"""
        questions = []
        
        # Medication-related questions
        for term in medical_terms:
            if term["category"] == "medication":
                questions.extend([
                    "What dosage are you currently taking?",
                    "How long have you been taking this medication?",
                    "Are you experiencing any side effects?"
                ])
            
            elif term["category"] == "symptom":
                if "pain" in term["canonical_name"]:
                    questions.extend([
                        "On a scale of 1-10, how severe is the pain?",
                        "When did the pain start?",
                        "What makes the pain better or worse?"
                    ])
                
                if "breath" in term["canonical_name"]:
                    questions.extend([
                        "When did the breathing difficulty start?",
                        "Is it worse with activity?",
                        "Do you have any chest pain?"
                    ])
        
        # Remove duplicates and limit
        unique_questions = list(set(questions))
        return unique_questions[:5]  # Return top 5 most relevant

# Initialize global medical intelligence
medical_intelligence = MedicalIntelligence()