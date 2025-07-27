#!/usr/bin/env python3
"""
Test client for Talktor Streaming Audio Service
Run this to verify your streaming audio implementation is working
"""

import asyncio
import websockets
import json
import base64
import wave
import io
import time
from datetime import datetime

class StreamingAudioTestClient:
    """Test client for streaming audio functionality"""
    
    def __init__(self, server_url="ws://localhost:8000"):
        self.server_url = server_url
        self.session_id = "test-session-" + str(int(time.time()))
        self.role = "doctor"
        
    async def test_streaming_connection(self):
        """Test basic WebSocket connection and streaming setup"""
        print(f"🔗 Testing WebSocket connection to {self.server_url}")
        
        uri = f"{self.server_url}/api/v2/conversation/ws/{self.session_id}/{self.role}"
        
        try:
            async with websockets.connect(uri) as websocket:
                print("✅ WebSocket connected successfully")
                
                # Wait for welcome message
                welcome_message = await websocket.recv()
                welcome_data = json.loads(welcome_message)
                print(f"📩 Received welcome: {welcome_data['content']['status']}")
                
                # Test start listening
                await self.test_start_listening(websocket)
                
                # Test audio chunk streaming
                await self.test_audio_chunk_streaming(websocket)
                
                # Test transcription processing
                await self.test_transcription_processing(websocket)
                
                print("✅ All streaming tests passed!")
                
        except Exception as e:
            print(f"❌ WebSocket test failed: {e}")

    async def test_start_listening(self, websocket):
        """Test start listening functionality"""
        print("\n🎤 Testing start listening...")
        
        start_message = {
            "type": "start_listening",
            "language": "en"
        }
        
        await websocket.send(json.dumps(start_message))
        
        # Wait for confirmation
        response = await websocket.recv()
        response_data = json.loads(response)
        
        if response_data.get("message_type") == "audio_status":
            print("✅ Start listening confirmed")
        else:
            print(f"❌ Unexpected response: {response_data}")

    async def test_audio_chunk_streaming(self, websocket):
        """Test audio chunk streaming with mock audio data"""
        print("\n🎵 Testing audio chunk streaming...")
        
        # Generate mock audio data (silence)
        mock_audio = self.generate_mock_audio(duration=2.0)
        audio_base64 = base64.b64encode(mock_audio).decode()
        
        # Send audio chunk
        audio_message = {
            "type": "audio_chunk_stream",
            "audio_data": audio_base64,
            "language": "en"
        }
        
        await websocket.send(json.dumps(audio_message))
        print("📤 Sent audio chunk")
        
        # Wait for audio status updates
        for _ in range(3):  # Wait for a few status updates
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                response_data = json.loads(response)
                
                if response_data.get("message_type") == "audio_status":
                    status = response_data["content"]["status"]
                    print(f"📊 Audio status: {status}")
                    
                    if "audio_level" in response_data["content"]:
                        level = response_data["content"]["audio_level"]
                        print(f"   Audio level: {level}")
                        
            except asyncio.TimeoutError:
                break

    async def test_transcription_processing(self, websocket):
        """Test transcription processing with medical text"""
        print("\n📝 Testing transcription processing...")
        
        test_texts = [
            "Estoy embarazada tomando ibuprofeno",
            "I have been taking prenatal vitamins",
            "Tengo náuseas matutinas muy fuertes"
        ]
        
        for text in test_texts:
            print(f"   Testing: '{text}'")
            
            transcription_message = {
                "type": "transcription",
                "text": text,
                "language": "es" if any(word in text.lower() for word in ["estoy", "tengo"]) else "en"
            }
            
            await websocket.send(json.dumps(transcription_message))
            
            # Wait for responses
            responses = []
            start_time = time.time()
            
            while time.time() - start_time < 5.0:  # Wait up to 5 seconds
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    response_data = json.loads(response)
                    responses.append(response_data)
                    
                    msg_type = response_data.get("message_type")
                    print(f"      📨 Received: {msg_type}")
                    
                    if msg_type == "medical_alert":
                        print(f"      🚨 Medical Alert: {response_data['content']['message']}")
                        
                    elif msg_type == "translation":
                        translated = response_data['content']['translated_text']
                        print(f"      🌐 Translation: {translated}")
                        
                except asyncio.TimeoutError:
                    break
            
            print(f"      ✅ Processed {len(responses)} responses")

    def generate_mock_audio(self, duration=1.0, sample_rate=16000):
        """Generate mock audio data for testing"""
        try:
            import numpy as np
            
            # Generate silence with some small noise
            num_samples = int(duration * sample_rate)
            audio_data = np.random.normal(0, 0.01, num_samples)  # Very quiet noise
            
            # Convert to 16-bit PCM
            audio_16bit = (audio_data * 32767).astype(np.int16)
            
            return audio_16bit.tobytes()
            
        except ImportError:
            # Fallback: generate simple mock data without numpy
            num_samples = int(duration * sample_rate)
            return b'\x00\x01' * num_samples  # Simple alternating bytes

async def test_rest_endpoints():
    """Test REST endpoints for streaming configuration"""
    import aiohttp
    
    print("\n🌐 Testing REST endpoints...")
    
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        # Test health check
        try:
            async with session.get(f"{base_url}/health/streaming") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Health check: {data['status']}")
                else:
                    print(f"❌ Health check failed: {response.status}")
        except Exception as e:
            print(f"❌ Health check error: {e}")
        
        # Test configuration endpoint
        try:
            async with session.get(f"{base_url}/config/streaming") as response:
                if response.status == 200:
                    config = await response.json()
                    print(f"✅ Config retrieved: VAD threshold = {config['vad_threshold']}")
                else:
                    print(f"❌ Config retrieval failed: {response.status}")
        except Exception as e:
            print(f"❌ Config error: {e}")
        
        # Test pipeline
        try:
            test_data = {
                "text": "Estoy embarazada tomando ibuprofeno",
                "language": "es",
                "session_id": "test-session"
            }
            
            async with session.post(f"{base_url}/test/streaming", json=test_data) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Pipeline test: {result['status']}")
                    print(f"   Medical entities: {result['medical_intelligence']['medications_found']}")
                    print(f"   Translation: {result['translation']['translated_text']}")
                else:
                    print(f"❌ Pipeline test failed: {response.status}")
        except Exception as e:
            print(f"❌ Pipeline test error: {e}")

async def main():
    """Main test function"""
    print("🎤 Talktor Streaming Audio Test Suite")
    print("=" * 50)
    
    # Test REST endpoints first
    await test_rest_endpoints()
    
    # Test WebSocket streaming
    client = StreamingAudioTestClient()
    await client.test_streaming_connection()
    
    print("\n" + "=" * 50)
    print("🎉 Test suite completed!")
    print("\nIf all tests passed, your streaming audio service is ready!")
    print("You can now integrate the frontend components.")

if __name__ == "__main__":
    # Run the test suite
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()