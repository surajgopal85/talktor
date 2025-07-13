# =============================================================================
# services/medical_intelligence/api_client.py
# =============================================================================

import httpx
import asyncio
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class ExternalMedicalAPIClient:
    """
    Client for external medical APIs (RxNorm, FDA, etc.)
    Centralizes all external API communication
    """
    
    def __init__(self):
        self.timeout = 10
        self.cache = {}  # Simple in-memory cache
        
    async def lookup_medication(self, drug_name: str, medical_context: str = "general") -> Dict:
        """
        Lookup medication using external APIs
        Integrates with your existing external_medical_intelligence
        """
        # Import your existing function
        from external_medical_intelligence import enhanced_medication_lookup
        
        # Check cache first
        cache_key = f"{drug_name}_{medical_context}"
        if cache_key in self.cache:
            logger.info(f"📦 Cache hit for {drug_name}")
            return self.cache[cache_key]
        
        try:
            # Use your existing API integration
            result = await enhanced_medication_lookup(drug_name, medical_context)
            
            # Cache the result
            self.cache[cache_key] = result
            
            logger.info(f"🌐 API lookup successful for {drug_name}")
            return result
            
        except Exception as e:
            logger.error(f"❌ API lookup failed for {drug_name}: {e}")
            raise
    
    async def test_api_connectivity(self) -> Dict:
        """Test connectivity to external APIs"""
        try:
            async with httpx.AsyncClient() as client:
                # Test RxNorm
                rxnorm_response = await client.get(
                    "https://rxnav.nlm.nih.gov/REST/drugs.json?name=aspirin", 
                    timeout=self.timeout
                )
                
                # Test FDA
                fda_response = await client.get(
                    "https://api.fda.gov/drug/label.json?search=openfda.brand_name:tylenol&limit=1",
                    timeout=self.timeout
                )
                
                return {
                    "rxnorm_api": "up" if rxnorm_response.status_code == 200 else "down",
                    "fda_api": "up" if fda_response.status_code == 200 else "down",
                    "cache_size": len(self.cache),
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }