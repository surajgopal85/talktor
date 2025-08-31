# tests/ml/test_obgyn_conversations.py
# Comprehensive testing framework for BERT-enhanced OBGYN extraction

import asyncio
import json
import logging
from typing import Dict, List, Any
from datetime import datetime
import pandas as pd
from dataclasses import dataclass

# Your existing services
from services.medical_intelligence.core.extraction import MedicationExtractionService
from services.medical_intelligence.specialties.obgyn.extraction import OBGYNEnhancedExtractionService

# New BERT enhancement
from services.ml.confidence_booster import BERTConfidenceBooster

logger = logging.getLogger(__name__)

@dataclass
class ConversationTestResult:
    conversation_id: str
    original_accuracy: float
    enhanced_accuracy: float
    processing_time_original: float
    processing_time_enhanced: float
    medications_found_original: int
    medications_found_enhanced: int
    confidence_improvements: List[Dict]
    missed_medications: List[str]

class OBGYNConversationTester:
    """
    Testing framework for BERT-enhanced OBGYN conversations
    """
    
    def __init__(self):
        # Initialize services
        self.original_service = MedicationExtractionService()
        self.obgyn_service = OBGYNEnhancedExtractionService()
        self.bert_booster = BERTConfidenceBooster()
        
        # Test results storage
        self.test_results = []
    
    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """
        Run complete test suite and generate report for your dad
        """
        logger.info("Starting comprehensive OBGYN conversation testing...")
        
        # Load test conversations
        conversations = self.get_realistic_obgyn_conversations()
        
        # Test each conversation
        for conv_id, conversation in conversations.items():
            logger.info(f"Testing conversation: {conv_id}")
            
            result = await self.test_single_conversation(conv_id, conversation)
            self.test_results.append(result)
        
        # Generate summary report
        summary_report = self.generate_summary_report()
        
        # Save detailed results
        self.save_test_results()
        
        return summary_report
    
    async def test_single_conversation(self, conv_id: str, conversation: Dict) -> ConversationTestResult:
        """
        Test a single conversation with both original and BERT-enhanced extraction
        """
        # Combine all patient statements for testing
        patient_statements = [
            turn["text"] for turn in conversation["turns"] 
            if turn["speaker"] == "patient"
        ]
        combined_text = " ".join(patient_statements)
        
        # Test original extraction
        start_time = datetime.now()
        original_result = await self.original_service.extract_medications(
            combined_text, f"test_session_{conv_id}", "obgyn"
        )
        original_time = (datetime.now() - start_time).total_seconds()
        
        # Test BERT-enhanced extraction
        start_time = datetime.now()
        enhanced_medications = await self.bert_booster.boost_medication_confidence(
            original_result["medications"], combined_text
        )
        enhanced_time = (datetime.now() - start_time).total_seconds()
        
        # Calculate improvements
        confidence_improvements = []
        for i, enhanced_med in enumerate(enhanced_medications):
            original_med = original_result["medications"][i]
            if enhanced_med["bert_boost"] > 0:
                confidence_improvements.append({
                    "medication": enhanced_med["original_term"],
                    "original_confidence": original_med["extraction_confidence"],
                    "enhanced_confidence": enhanced_med["extraction_confidence"],
                    "boost": enhanced_med["bert_boost"]
                })
        
        # Check against expected medications
        expected_meds = conversation.get("expected_medications", [])
        found_meds = {med["original_term"].lower() for med in enhanced_medications}
        missed_medications = [med for med in expected_meds if med.lower() not in found_meds]
        
        return ConversationTestResult(
            conversation_id=conv_id,
            original_accuracy=self.calculate_accuracy(original_result["medications"], expected_meds),
            enhanced_accuracy=self.calculate_accuracy(enhanced_medications, expected_meds),
            processing_time_original=original_time,
            processing_time_enhanced=enhanced_time + original_time,  # Total time
            medications_found_original=len(original_result["medications"]),
            medications_found_enhanced=len(enhanced_medications),
            confidence_improvements=confidence_improvements,
            missed_medications=missed_medications
        )
    
    def calculate_accuracy(self, extracted_meds: List[Dict], expected_meds: List[str]) -> float:
        """Calculate extraction accuracy"""
        if not expected_meds:
            return 1.0
        
        found_terms = {med["original_term"].lower() for med in extracted_meds}
        expected_terms = {med.lower() for med in expected_meds}
        
        correct = len(found_terms.intersection(expected_terms))
        return correct / len(expected_terms)
    
    def get_realistic_obgyn_conversations(self) -> Dict[str, Dict]:
        """
        Enhanced realistic OBGYN conversations for comprehensive testing
        Each represents a detailed hospital scenario with complex medical terminology
        """
        return {
            "prenatal_medication_safety": {
                "description": "Pregnant patient with complex medication history discussing safety",
                "turns": [
                    {"speaker": "doctor", "text": "Good morning, Mrs. García. I see you're 12 weeks pregnant. How are you feeling today?"},
                    {"speaker": "patient", "text": "Buenos días, doctora. Me siento bien en general, pero tengo muchas preguntas sobre los medicamentos que tomaba antes del embarazo."},
                    {"speaker": "doctor", "text": "Of course, let's review your medication history. What were you taking before pregnancy?"},
                    {"speaker": "patient", "text": "Tomaba lisinopril para la presión alta, metformina para la diabetes tipo 2, y sertralina para la depresión. También tomaba omeprazol para la acidez estomacal."},
                    {"speaker": "doctor", "text": "I see. When did you stop taking these medications?"},
                    {"speaker": "patient", "text": "Dejé de tomar todo cuando supe que estaba embarazada, hace como 8 semanas. Pero ahora me duele mucho la cabeza y no sé qué puedo tomar."},
                    {"speaker": "doctor", "text": "What about your current medications and supplements?"},
                    {"speaker": "patient", "text": "Solo tomo las vitaminas prenatales que me recetó mi doctor anterior, y ácido fólico. También tomo calcio y hierro porque tenía anemia antes del embarazo."},
                    {"speaker": "doctor", "text": "For headaches, acetaminophen is safe during pregnancy. Let's discuss your diabetes management."},
                    {"speaker": "patient", "text": "¿Puedo volver a tomar metformina? Mi azúcar en sangre ha estado alta últimamente."},
                    {"speaker": "patient", "text": "También quería preguntarle sobre la sertralina. Me siento muy ansiosa y deprimida sin ella."}
                ],
                "expected_medications": ["lisinopril", "metformina", "sertralina", "omeprazol", "vitaminas prenatales", "ácido fólico", "calcio", "hierro", "acetaminophen"],
                "medical_context": "pregnancy, diabetes, hypertension, depression",
                "risk_level": "high"
            },
            
            "contraception_consultation": {
                "description": "Young woman with complex medical history discussing birth control",
                "turns": [
                    {"speaker": "doctor", "text": "Hello, I see you're here for contraception consultation. What brings you in today?"},
                    {"speaker": "patient", "text": "Hola doctora. Quiero hablar sobre opciones de control de natalidad, pero tengo algunas condiciones médicas que me preocupan."},
                    {"speaker": "doctor", "text": "What medical conditions do you have?"},
                    {"speaker": "patient", "text": "Tengo migrañas con aura, y mi mamá tuvo trombosis venosa profunda. También tengo PCOS y tomo metformina para eso."},
                    {"speaker": "doctor", "text": "I see. What other medications are you currently taking?"},
                    {"speaker": "patient", "text": "Tomo metformina 500mg dos veces al día, y a veces tomo sumatriptán para las migrañas. También tomo vitamina D y omega-3."},
                    {"speaker": "doctor", "text": "Have you used any contraception before?"},
                    {"speaker": "patient", "text": "Sí, probé las píldoras anticonceptivas hace dos años, pero me dieron dolores de cabeza terribles. También probé el parche, pero me irritó la piel."},
                    {"speaker": "patient", "text": "Mi amiga usa el anillo vaginal y dice que le va bien. ¿Eso sería seguro para mí con mis condiciones?"},
                    {"speaker": "doctor", "text": "Given your history of migraines with aura and family history of blood clots, we need to be very careful."},
                    {"speaker": "patient", "text": "También quería preguntarle sobre el DIU de cobre. ¿Eso no tiene hormonas, verdad?"}
                ],
                "expected_medications": ["metformina", "sumatriptán", "vitamina D", "omega-3", "píldoras anticonceptivas", "parche", "anillo vaginal", "DIU cobre"],
                "medical_context": "contraception, migraine, PCOS, family_history",
                "risk_level": "moderate_to_high"
            },
            
            "gestational_diabetes_complex": {
                "description": "Pregnant patient with complex gestational diabetes management",
                "turns": [
                    {"speaker": "doctor", "text": "Your glucose tolerance test confirms gestational diabetes. Let's discuss management options."},
                    {"speaker": "patient", "text": "¿Qué significa eso exactamente, doctora? ¿Es peligroso para mi bebé? Mi hermana tuvo diabetes gestacional también."},
                    {"speaker": "doctor", "text": "It's manageable with proper care. What medications are you currently taking?"},
                    {"speaker": "patient", "text": "Tomo las vitaminas prenatales, ácido fólico, hierro para la anemia, y calcio. También tomo progesterona porque tuve amenaza de aborto."},
                    {"speaker": "doctor", "text": "Any other medications or supplements?"},
                    {"speaker": "patient", "text": "Sí, tomo magnesio para los calambres en las piernas, y DHA para el desarrollo del cerebro del bebé. También uso una crema con progesterona."},
                    {"speaker": "doctor", "text": "For gestational diabetes, we may need to add medication. Have you taken metformin before?"},
                    {"speaker": "patient", "text": "No, nunca he tomado metformina. ¿Es seguro durante el embarazo? También quería preguntarle sobre la insulina."},
                    {"speaker": "doctor", "text": "Both metformin and insulin can be used safely. Let's start with dietary changes and monitoring."},
                    {"speaker": "patient", "text": "¿Debo seguir tomando todas las vitaminas y suplementos? ¿Y qué pasa con la progesterona?"},
                    {"speaker": "patient", "text": "También tengo presión alta y tomo labetalol. ¿Eso afecta la diabetes gestacional?"}
                ],
                "expected_medications": ["vitaminas prenatales", "ácido fólico", "hierro", "calcio", "progesterona", "magnesio", "DHA", "crema progesterona", "metformina", "insulina", "labetalol"],
                "medical_context": "gestational_diabetes, pregnancy, hypertension, threatened_abortion",
                "risk_level": "high"
            },
            
            "postpartum_complex": {
                "description": "New mother with complex postpartum recovery and breastfeeding",
                "turns": [
                    {"speaker": "doctor", "text": "How are you recovering from your cesarean section? I see you're breastfeeding."},
                    {"speaker": "patient", "text": "Bien en general, doctora, pero tengo algunas complicaciones. Me duele mucho la incisión y tengo infección."},
                    {"speaker": "doctor", "text": "What medications are you currently taking for pain and infection?"},
                    {"speaker": "patient", "text": "Tomo ibuprofeno cada 6 horas para el dolor, y amoxicilina para la infección. También uso una crema con antibiótico en la incisión."},
                    {"speaker": "doctor", "text": "Are you taking any other medications or supplements?"},
                    {"speaker": "patient", "text": "Sí, sigo tomando las vitaminas prenatales, hierro para la anemia, y calcio. También tomo docusato sódico para el estreñimiento."},
                    {"speaker": "doctor", "text": "How is breastfeeding going? Any issues with milk supply?"},
                    {"speaker": "patient", "text": "El bebé no está ganando suficiente peso. Mi doctor me recetó domperidona para aumentar la producción de leche."},
                    {"speaker": "doctor", "text": "Are you experiencing any postpartum depression symptoms?"},
                    {"speaker": "patient", "text": "Sí, me siento muy triste y ansiosa. Mi doctor anterior me sugirió sertralina, pero me preocupa que afecte al bebé."},
                    {"speaker": "patient", "text": "También tengo hemorroides y uso una crema con hidrocortisona. ¿Todo esto es seguro mientras amamanto?"}
                ],
                "expected_medications": ["ibuprofeno", "amoxicilina", "crema antibiótico", "vitaminas prenatales", "hierro", "calcio", "docusato sódico", "domperidona", "sertralina", "crema hidrocortisona"],
                "medical_context": "postpartum, cesarean, infection, breastfeeding, depression",
                "risk_level": "moderate"
            },
            
            "menopause_complex": {
                "description": "Menopausal woman with complex medical history discussing HRT",
                "turns": [
                    {"speaker": "doctor", "text": "You mentioned you're interested in hormone replacement therapy. Let's review your medical history."},
                    {"speaker": "patient", "text": "Sí, doctora. Los sofocos son insoportables y no duermo bien. También tengo sequedad vaginal y dolor durante las relaciones."},
                    {"speaker": "doctor", "text": "What medications are you currently taking?"},
                    {"speaker": "patient", "text": "Tomo lisinopril para la presión alta, atorvastatina para el colesterol, y metformina para la diabetes tipo 2."},
                    {"speaker": "doctor", "text": "Any other medications or supplements?"},
                    {"speaker": "patient", "text": "Sí, tomo calcio y vitamina D para los huesos, magnesio para los calambres, y omega-3 para el corazón. También tomo melatonina para dormir."},
                    {"speaker": "doctor", "text": "Have you tried any natural remedies for menopause symptoms?"},
                    {"speaker": "patient", "text": "Sí, probé cohosh negro, soya, y valeriana, pero no me ayudaron mucho. Mi hermana toma estrógeno y dice que le va muy bien."},
                    {"speaker": "doctor", "text": "Given your cardiovascular risk factors, we need to be very careful with HRT."},
                    {"speaker": "patient", "text": "¿Qué opciones tengo? ¿Puedo tomar solo estrógeno o necesito progesterona también?"},
                    {"speaker": "patient", "text": "También tengo osteoporosis y tomo alendronato. ¿Eso afecta la terapia hormonal?"}
                ],
                "expected_medications": ["lisinopril", "atorvastatina", "metformina", "calcio", "vitamina D", "magnesio", "omega-3", "melatonina", "cohosh negro", "soya", "valeriana", "estrógeno", "progesterona", "alendronato"],
                "medical_context": "menopause, cardiovascular_risk, diabetes, osteoporosis",
                "risk_level": "high"
            },
            
            "infertility_treatment": {
                "description": "Woman undergoing complex infertility treatment",
                "turns": [
                    {"speaker": "doctor", "text": "I see you've been trying to conceive for 18 months. Let's review your treatment history."},
                    {"speaker": "patient", "text": "Sí, doctora. He estado tomando clomifeno durante 6 meses, pero no ha funcionado. También probé letrozol."},
                    {"speaker": "doctor", "text": "What other medications are you currently taking?"},
                    {"speaker": "patient", "text": "Tomo metformina para el PCOS, y mi endocrinólogo me recetó levotiroxina para el hipotiroidismo."},
                    {"speaker": "doctor", "text": "Any supplements or vitamins?"},
                    {"speaker": "patient", "text": "Sí, tomo ácido fólico, vitamina D, coenzima Q10, y inositol. También tomo probióticos para la salud intestinal."},
                    {"speaker": "doctor", "text": "Have you had any fertility procedures?"},
                    {"speaker": "patient", "text": "Sí, tuve una inseminación intrauterina el mes pasado, pero no funcionó. Mi doctor me sugiere la fertilización in vitro."},
                    {"speaker": "doctor", "text": "For IVF, we'll need to adjust your medications. Are you taking any pain medications?"},
                    {"speaker": "patient", "text": "A veces tomo ibuprofeno para los dolores menstruales, y acetaminofén para los dolores de cabeza."},
                    {"speaker": "patient", "text": "También tomo alprazolam para la ansiedad. ¿Todo esto afecta la fertilidad?"}
                ],
                "expected_medications": ["clomifeno", "letrozol", "metformina", "levotiroxina", "ácido fólico", "vitamina D", "coenzima Q10", "inositol", "probióticos", "ibuprofeno", "acetaminofén", "alprazolam"],
                "medical_context": "infertility, PCOS, hypothyroidism, anxiety",
                "risk_level": "moderate"
            }
        }
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive summary report for medical professional review
        """
        if not self.test_results:
            return {"error": "No test results available"}
        
        # Calculate overall metrics
        total_conversations = len(self.test_results)
        accuracy_improvements = [
            result.enhanced_accuracy - result.original_accuracy 
            for result in self.test_results
        ]
        
        confidence_boosts = []
        for result in self.test_results:
            for improvement in result.confidence_improvements:
                confidence_boosts.append(improvement["boost"])
        
        avg_original_accuracy = sum(r.original_accuracy for r in self.test_results) / total_conversations
        avg_enhanced_accuracy = sum(r.enhanced_accuracy for r in self.test_results) / total_conversations
        
        summary = {
            "test_summary": {
                "conversations_tested": total_conversations,
                "test_date": datetime.now().isoformat(),
                "bert_model": "PlanTL-GOB-ES/roberta-base-biomedical-clinical-es"
            },
            "accuracy_metrics": {
                "original_average_accuracy": round(avg_original_accuracy, 3),
                "enhanced_average_accuracy": round(avg_enhanced_accuracy, 3),
                "average_improvement": round(avg_enhanced_accuracy - avg_original_accuracy, 3),
                "conversations_improved": sum(1 for imp in accuracy_improvements if imp > 0),
                "conversations_unchanged": sum(1 for imp in accuracy_improvements if imp == 0),
                "conversations_degraded": sum(1 for imp in accuracy_improvements if imp < 0)
            },
            "confidence_metrics": {
                "medications_boosted": len(confidence_boosts),
                "average_confidence_boost": round(sum(confidence_boosts) / len(confidence_boosts), 3) if confidence_boosts else 0,
                "max_confidence_boost": round(max(confidence_boosts), 3) if confidence_boosts else 0
            },
            "performance_metrics": {
                "average_processing_time_ms": round(sum(r.processing_time_enhanced * 1000 for r in self.test_results) / total_conversations, 1),
                "bert_overhead_ms": round(sum((r.processing_time_enhanced - r.processing_time_original) * 1000 for r in self.test_results) / total_conversations, 1)
            },
            "detailed_results": [
                {
                    "conversation": result.conversation_id,
                    "accuracy_improvement": round(result.enhanced_accuracy - result.original_accuracy, 3),
                    "medications_found": result.medications_found_enhanced,
                    "confidence_boosts": len(result.confidence_improvements),
                    "missed_medications": result.missed_medications
                } for result in self.test_results
            ]
        }
        
        return summary
    
    def save_test_results(self):
        """Save detailed test results to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save summary JSON
        summary = self.generate_summary_report()
        with open(f"data/ml/test_results_summary_{timestamp}.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        # Save detailed CSV for analysis
        detailed_data = []
        for result in self.test_results:
            for improvement in result.confidence_improvements:
                detailed_data.append({
                    "conversation_id": result.conversation_id,
                    "medication": improvement["medication"],
                    "original_confidence": improvement["original_confidence"],
                    "enhanced_confidence": improvement["enhanced_confidence"],
                    "bert_boost": improvement["boost"],
                    "accuracy_improvement": result.enhanced_accuracy - result.original_accuracy
                })
        
        if detailed_data:
            df = pd.DataFrame(detailed_data)
            df.to_csv(f"data/ml/detailed_results_{timestamp}.csv", index=False)
        
        logger.info(f"Test results saved with timestamp {timestamp}")
    
    def print_clinical_summary(self, summary: Dict[str, Any]):
        """
        Print a clinical summary suitable for medical professional review
        """
        print("\n" + "="*60)
        print("TALKTOR OBGYN AI ENHANCEMENT - CLINICAL EVALUATION REPORT")
        print("="*60)
        
        print(f"\nTEST OVERVIEW:")
        print(f"• Conversations Tested: {summary['test_summary']['conversations_tested']}")
        print(f"• AI Model: Medical Spanish BERT")
        print(f"• Test Date: {summary['test_summary']['test_date'][:10]}")
        
        print(f"\nMEDICATION EXTRACTION ACCURACY:")
        print(f"• Baseline System: {summary['accuracy_metrics']['original_average_accuracy']:.1%}")
        print(f"• BERT-Enhanced: {summary['accuracy_metrics']['enhanced_average_accuracy']:.1%}")
        print(f"• Average Improvement: +{summary['accuracy_metrics']['average_improvement']:.1%}")
        
        print(f"\nCONFIDENCE CALIBRATION:")
        print(f"• Medications with Boosted Confidence: {summary['confidence_metrics']['medications_boosted']}")
        print(f"• Average Confidence Increase: +{summary['confidence_metrics']['average_confidence_boost']:.3f}")
        
        print(f"\nPERFORMANCE:")
        print(f"• Processing Time: {summary['performance_metrics']['average_processing_time_ms']:.0f}ms per conversation")
        print(f"• BERT Overhead: {summary['performance_metrics']['bert_overhead_ms']:.0f}ms")
        
        print(f"\nCONVERSATION BREAKDOWN:")
        for result in summary['detailed_results']:
            improvement_symbol = "↑" if result['accuracy_improvement'] > 0 else "→" if result['accuracy_improvement'] == 0 else "↓"
            print(f"• {result['conversation'].replace('_', ' ').title()}: {result['medications_found']} medications found {improvement_symbol}")
        
        print("\n" + "="*60)

# Quick test runner
async def quick_test():
    """Quick test for immediate feedback"""
    tester = OBGYNConversationTester()
    
    # Test just one conversation
    conversations = tester.get_realistic_obgyn_conversations()
    test_conv = conversations["prenatal_medication_safety"]
    
    result = await tester.test_single_conversation("prenatal_test", test_conv)
    
    print(f"\nQuick Test Results:")
    print(f"Medications found: {result.medications_found_enhanced}")
    print(f"Confidence improvements: {len(result.confidence_improvements)}")
    print(f"Processing time: {result.processing_time_enhanced*1000:.0f}ms")
    
    for improvement in result.confidence_improvements:
        print(f"• {improvement['medication']}: {improvement['original_confidence']:.3f} → {improvement['enhanced_confidence']:.3f}")

if __name__ == "__main__":
    # Run comprehensive tests
    async def main():
        tester = OBGYNConversationTester()
        summary = await tester.run_comprehensive_tests()
        tester.print_clinical_summary(summary)
    
    asyncio.run(main())