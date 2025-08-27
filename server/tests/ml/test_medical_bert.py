# tests/ml/test_medical_bert.py
import pytest
import asyncio
from services.ml.medical_bert import MedicalSpanishBERT, MedicalEntity

class TestMedicalSpanishBERT:
    """Test cases for Medical Spanish BERT"""
    
    @pytest.fixture
    def bert_model(self):
        """Create BERT model for testing"""
        return MedicalSpanishBERT()
    
    @pytest.mark.asyncio
    async def test_simple_medication_extraction(self, bert_model):
        """Test extracting simple medication"""
        text = "Tomo ibuprofeno para el dolor"
        result = await bert_model.extract_medical_entities(text)
        
        assert len(result.entities) > 0
        medication_entities = [e for e in result.entities if e.entity_type == "medication"]
        assert len(medication_entities) > 0
        assert any("ibuprofeno" in e.spanish_term.lower() for e in medication_entities)
    
    @pytest.mark.asyncio 
    async def test_pregnancy_condition_extraction(self, bert_model):
        """Test extracting pregnancy condition"""
        text = "Estoy embarazada de 8 semanas"
        result = await bert_model.extract_medical_entities(text)
        
        condition_entities = [e for e in result.entities if e.entity_type == "condition"]
        assert len(condition_entities) > 0
        assert any("embarazada" in e.spanish_term.lower() for e in condition_entities)
    
    @pytest.mark.asyncio
    async def test_complex_medical_text(self, bert_model):
        """Test complex medical conversation"""
        text = "Estoy embarazada tomando ácido fólico y vitaminas prenatales"
        result = await bert_model.extract_medical_entities(text)
        
        # Should find both condition and medications
        medications = [e for e in result.entities if e.entity_type == "medication"]
        conditions = [e for e in result.entities if e.entity_type == "condition"]
        
        assert len(medications) >= 1  # At least ácido fólico
        assert len(conditions) >= 1   # At least embarazada
        assert result.bert_confidence > 0.0
    
    @pytest.mark.asyncio
    async def test_embedding_generation(self, bert_model):
        """Test medical text embedding"""
        text = "Tengo diabetes tipo 2"
        embedding = await bert_model.get_medical_embedding(text)
        
        assert embedding.shape[0] > 0  # Should have embedding dimensions
        assert not np.allclose(embedding, 0)  # Should not be all zeros

# Example usage script
if __name__ == "__main__":
    async def demo():
        """Demo the medical BERT functionality"""
        bert = MedicalSpanishBERT()
        
        test_cases = [
            "Tomo ibuprofeno para el dolor de cabeza",
            "Estoy embarazada de 12 semanas",
            "Tengo diabetes y tomo metformina",
            "Me duele el estómago después de comer",
            "Necesito una radiografía del pecho"
        ]
        
        print("🧠 Medical Spanish BERT Demo")
        print("=" * 50)
        
        for text in test_cases:
            print(f"\n📝 Input: {text}")
            result = await bert.extract_medical_entities(text)
            
            print(f"⏱️  Processing time: {result.processing_time_ms:.2f}ms")
            print(f"🎯 Confidence: {result.bert_confidence:.3f}")
            print(f"🔍 Entities found: {len(result.entities)}")
            
            for entity in result.entities:
                print(f"   • {entity.spanish_term} ({entity.entity_type}) - {entity.confidence:.3f}")
    
    # Run demo
    asyncio.run(demo())