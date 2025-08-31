import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Mic, MicOff } from 'lucide-react';
import ProductionToggles from './controls/ProductionToggles';
import ConversationHeader from './conversation/ConversationHeader';
import ConversationMessages from './conversation/ConversationMessages';
import AudioControls from './controls/AudioControls';
import MedicalContextPanel from './medical/MedicalContextPanel';
import MedicalAIPanel from './medical/MedicalAIPanel';
import DemoScenarios from './demo/DemoScenarios';
import DebugPanel from './debug/DebugPanel';
import ConversationSummary from './conversation/ConversationSummary';
import { AudioRecorder } from './AudioRecorder';

interface ConversationMessage {
  id: string;
  speaker: 'doctor' | 'patient' | 'system';
  message_type: string;
  content: any;
  timestamp: string;
  language: string;
}

interface MedicalAlert {
  id: string;
  type: string;
  message: string;
  severity: string;
  timestamp: string;
}

interface ConversationSession {
  session_id: string;
  doctor_language: string;
  patient_language: string;
  status: string;
}

interface DebugLog {
  timestamp: string;
  level: 'info' | 'error' | 'warning';
  message: string;
  data?: any;
}

const TalktorMedicalInterface: React.FC = () => {
  // Core state
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [medicalAlerts, setMedicalAlerts] = useState<MedicalAlert[]>([]);
  const [medicalContext, setMedicalContext] = useState<any>(null);
  const [conversationActive, setConversationActive] = useState(false);
  const [sessionId, setSessionId] = useState<string>('');

  // Audio state
  const [isListening, setIsListening] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [currentSpeaker, setCurrentSpeaker] = useState<'doctor' | 'patient'>('patient');
  const [audioSupported, setAudioSupported] = useState(false);
  const [websocket, setWebsocket] = useState<WebSocket | null>(null);

  // Debug state
  const [showDebug, setShowDebug] = useState(false);
  const [debugLogs, setDebugLogs] = useState<DebugLog[]>([]);

  // Production mode toggles
  const [showDebugInfo, setShowDebugInfo] = useState(true);
  const [showConfidenceScores, setShowConfidenceScores] = useState(true);
  const [showMedicalAlerts, setShowMedicalAlerts] = useState(true);
  const [showExtractionMethods, setShowExtractionMethods] = useState(true);
  const [showDemoScenarios, setShowDemoScenarios] = useState(true);
  const [showMedicalAI, setShowMedicalAI] = useState(false); // New toggle for medical AI data

  // Refs
  const reconnectTimeoutRef = useRef<number | null>(null);
  const audioRecorderRef = useRef<any>(null);

  // Initialize session
  useEffect(() => {
    setSessionId(`session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  }, []);

  // Debug logging function
  const addDebugLog = useCallback((level: 'info' | 'error' | 'warning', message: string, data?: any) => {
    const log: DebugLog = {
      timestamp: new Date().toISOString(),
      level,
      message,
      data
    };
    setDebugLogs(prev => [...prev, log]);
    
    // Also log to console
    if (level === 'error') {
      console.error(message, data);
    } else if (level === 'warning') {
      console.warn(message, data);
    } else {
      console.log(message, data);
    }
  }, []);

  // Audio initialization
  const initializeAudio = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      setAudioSupported(true);
      addDebugLog('info', '✅ Audio initialized successfully');
      stream.getTracks().forEach(track => track.stop()); // Stop the stream after testing
    } catch (error) {
      setAudioSupported(false);
      addDebugLog('error', '❌ Audio initialization failed', error);
    }
  }, [addDebugLog]);

  // WebSocket connection
  useEffect(() => {
    const connectWebSocket = () => {
      try {
        const ws = new WebSocket(`ws://127.0.0.1:8000/conversation/ws/${sessionId}/doctor`);
        
        ws.onopen = () => {
          addDebugLog('info', '🔗 WebSocket connected');
          setWebsocket(ws);
        };
        
        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            addDebugLog('info', '📨 WebSocket message received', data);
            
            // Handle different message types
            if (data.type === 'transcription') {
              const message: ConversationMessage = {
                id: `msg_${Date.now()}_${Math.random()}`,
                speaker: data.speaker || 'patient',
                message_type: 'transcription',
                content: { text: data.text },
                timestamp: new Date().toISOString(),
                language: data.language || 'es'
              };
              setMessages(prev => [...prev, message]);
            } else if (data.type === 'translation') {
              const message: ConversationMessage = {
                id: `trans_${Date.now()}_${Math.random()}`,
                speaker: 'system',
                message_type: 'translation',
                content: data.content,
                timestamp: new Date().toISOString(),
                language: 'en'
              };
              setMessages(prev => [...prev, message]);
              
              // Update medical context
              if (data.content.medical_terms) {
                setMedicalContext((prev: any) => ({
                  ...prev,
                  medications_discussed: [
                    ...(prev?.medications_discussed || []),
                    ...data.content.medical_terms.map((term: any) => term.original_text)
                  ],
                  confidence_scores: {
                    ...(prev?.confidence_scores || {}),
                    ...data.content.confidence_scores
                  }
                }));
              }
            }
          } catch (error) {
            addDebugLog('error', '❌ Failed to parse WebSocket message', error);
          }
        };
        
        ws.onclose = () => {
          addDebugLog('warning', '🔌 WebSocket disconnected');
          setWebsocket(null);
          
          // Attempt to reconnect
          if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
          }
          reconnectTimeoutRef.current = window.setTimeout(connectWebSocket, 3000);
        };
        
        ws.onerror = (error) => {
          addDebugLog('error', '❌ WebSocket error', error);
        };
      } catch (error) {
        addDebugLog('error', '❌ Failed to create WebSocket connection', error);
      }
    };

    connectWebSocket();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (websocket) {
        websocket.close();
      }
    };
  }, [addDebugLog]);

  // Audio controls
  const startListening = useCallback(() => {
    if (!websocket || websocket.readyState !== WebSocket.OPEN) {
      addDebugLog('error', '❌ Cannot start listening - WebSocket not connected');
      return;
    }
    
    setIsListening(true);
    addDebugLog('info', '🎤 Started listening');
    
    // Send start listening message
    websocket.send(JSON.stringify({ type: 'start_listening' }));
  }, [websocket, addDebugLog]);

  const stopListening = useCallback(() => {
    setIsListening(false);
    addDebugLog('info', '🔇 Stopped listening');
    
    if (websocket && websocket.readyState === WebSocket.OPEN) {
      websocket.send(JSON.stringify({ type: 'stop_listening' }));
    }
  }, [websocket, addDebugLog]);

  const startRecordingWithSpeaker = useCallback((speaker: 'doctor' | 'patient') => {
    // Use the working AudioRecorder component for actual recording
    setIsListening(true);
    addDebugLog('info', `🎤 Started recording for ${speaker}`);
    
    // The AudioRecorder component will handle the actual recording
    // and call the onTranscription callback when done
  }, [addDebugLog]);

  const startConversation = useCallback(() => {
    setConversationActive(true);
    setMessages([]);
    setMedicalAlerts([]);
    setMedicalContext(null);
    addDebugLog('info', '🚀 Started new conversation');
  }, [addDebugLog]);

  const endConversation = useCallback(() => {
    setConversationActive(false);
    setIsListening(false);
    addDebugLog('info', '🏁 Ended conversation');
  }, [addDebugLog]);

  // Demo scenario function
  const runDemoScenario = useCallback((scenarioType: string) => {
    addDebugLog('info', `🚀 Running demo scenario: ${scenarioType}`);
    let textToSend = '';
    let language = '';

    switch (scenarioType) {
      case 'prenatal_safety':
        textToSend = "Estoy embarazada tomando ibuprofeno y amoxicilina";
        language = "es";
        break;
      case 'postpartum_complex':
        textToSend = "Tomo metformina para diabetes y lisinopril para presión alta";
        language = "es";
        break;
      case 'menopause_hrt':
        textToSend = "Hormone replacement therapy for menopause symptoms";
        language = "en";
        break;
      case 'medication_list':
        textToSend = "Tomo metformina para diabetes y lisinopril para presión alta";
        language = "es";
        break;
      case 'symptom_discussion':
        textToSend = "Pain, fever, side effects from medications";
        language = "en";
        break;
      case 'allergy_alert':
        textToSend = "Soy alérgica a penicilina y aspirina";
        language = "es";
        break;
      default:
        textToSend = "How are you feeling today?";
        language = "en";
        break;
    }

    sendTestMessage(textToSend, language);
  }, [addDebugLog]);

  // Send test message
  const sendTestMessage = async (text: string, language: string) => {
    const totalStartTime = performance.now();
    addDebugLog('info', `🚀 Processing translation for: "${text}" (${language})`);
    
    // Note: The transcription message is already added by the AudioRecorder callback
    // We only need to add the translation message here
    
    try {
      // Call the medical translation API directly
      const apiStartTime = performance.now();
      const response = await fetch('http://127.0.0.1:8000/translate/medical', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: text,
          source_language: language,
          target_language: language === 'es' ? 'en' : 'es',
          medical_context: 'obgyn'
        })
      });
      
      const apiEndTime = performance.now();
      const apiLatency = apiEndTime - apiStartTime;
      addDebugLog('info', `⏱️ API call completed in ${apiLatency.toFixed(2)}ms`);

      if (!response.ok) {
        throw new Error(`Translation failed: ${response.status}`);
      }

      const jsonStartTime = performance.now();
      const result = await response.json();
      const jsonEndTime = performance.now();
      const jsonLatency = jsonEndTime - jsonStartTime;
      addDebugLog('info', `⏱️ JSON parsing completed in ${jsonLatency.toFixed(2)}ms`);
      
      addDebugLog('info', '✅ Medical translation completed', result);
      
      // Add the translation as a bright, focused message
      const translationMessage: ConversationMessage = {
        id: `translation_${Date.now()}`,
        speaker: currentSpeaker === 'doctor' ? 'patient' : 'doctor', // Opposite speaker for translation
        message_type: 'translation',
        content: {
          original_text: text,
          translated_text: result.enhanced_translation || result.standard_translation,
          medical_terms: result.medical_terms || [],
          medical_notes: result.medical_notes || [],
          follow_up_questions: result.follow_up_questions || [],
          confidence: result.confidence || 0,
          medical_accuracy: result.medical_accuracy_score || 0
        },
        timestamp: new Date(Date.now() + 100).toISOString(), // Slightly later timestamp to maintain order
        language: currentSpeaker === 'doctor' ? 'es' : 'en' // Opposite language
      };
      
      setMessages(prev => [...prev, translationMessage]);
      
      // Update medical context if available
      if (result.medical_terms && result.medical_terms.length > 0) {
        setMedicalContext({
          medications_discussed: result.medical_terms.map((term: any) => term.original_text),
          confidence_scores: result.learning_metadata?.confidence_scores || {},
          extraction_strategies: result.learning_metadata?.extraction_strategies_used || []
        });
      }
      
      // Add medical alerts if any
      if (result.medical_notes && result.medical_notes.length > 0) {
        const alerts = result.medical_notes.map((note: any) => ({
          id: `alert_${Date.now()}_${Math.random()}`,
          type: note.type,
          message: note.message,
          severity: note.importance || 'medium',
          timestamp: new Date().toISOString()
        }));
        
        setMedicalAlerts(prev => [...prev, ...alerts]);
      }
      
      // Total time measurement
      const totalEndTime = performance.now();
      const totalLatency = totalEndTime - totalStartTime;
      addDebugLog('info', `⏱️ Total translation pipeline completed in ${totalLatency.toFixed(2)}ms`);
      
    } catch (error) {
      addDebugLog('error', '❌ Demo scenario failed', error);
      
      // Add error message to conversation
      const errorMessage: ConversationMessage = {
        id: `error_${Date.now()}`,
        speaker: 'system',
        message_type: 'error',
        content: { 
          text: `Demo scenario failed: ${error}`,
          error: error
        },
        timestamp: new Date().toISOString(),
        language: 'en'
      };
      
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  // Toggle handlers
  const handleToggleChange = useCallback((key: string, value: boolean) => {
    switch (key) {
      case 'showDebugInfo':
        setShowDebugInfo(value);
        break;
      case 'showConfidenceScores':
        setShowConfidenceScores(value);
        break;
      case 'showMedicalAlerts':
        setShowMedicalAlerts(value);
        break;
      case 'showExtractionMethods':
        setShowExtractionMethods(value);
        break;
      case 'showDemoScenarios':
        setShowDemoScenarios(value);
        break;
      case 'showMedicalAI':
        setShowMedicalAI(value);
        break;
    }
  }, []);

  const handleProductionMode = useCallback(() => {
    setShowDebugInfo(false);
    setShowConfidenceScores(false);
    setShowMedicalAlerts(false);
    setShowExtractionMethods(false);
    setShowDemoScenarios(false);
  }, []);

  const handleDemoMode = useCallback(() => {
    setShowDebugInfo(true);
    setShowConfidenceScores(true);
    setShowMedicalAlerts(true);
    setShowExtractionMethods(true);
    setShowDemoScenarios(true);
  }, []);

  return (
    <div className="h-screen flex flex-col">
      {/* Production Mode Toggles */}
      <ProductionToggles
        showDebugInfo={showDebugInfo}
        showConfidenceScores={showConfidenceScores}
        showMedicalAlerts={showMedicalAlerts}
        showExtractionMethods={showExtractionMethods}
        showDemoScenarios={showDemoScenarios}
        showMedicalAI={showMedicalAI}
        onToggleChange={handleToggleChange}
        onProductionMode={handleProductionMode}
        onDemoMode={handleDemoMode}
      />

      {/* Conversation Header */}
      <ConversationHeader
        conversationActive={conversationActive}
        sessionId={sessionId}
        doctorLanguage="en"
        patientLanguage="es"
      />

      {/* Main Content Area */}
      <div className="flex-1 flex">
        {/* Left Side - Conversation */}
        <div className="flex-1 flex flex-col">
          {/* Unified Voice Chat Controls */}
          <div className="bg-white shadow-sm border-b border-gray-200 p-6">
            <div className="max-w-4xl mx-auto">
              {/* Conversation Status */}
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-4">
                  <div className={`w-3 h-3 rounded-full ${
                    conversationActive ? 'bg-green-500' : 'bg-gray-400'
                  }`} />
                  <span className="text-sm font-medium text-gray-700">
                    {conversationActive ? 'Conversation Active' : 'Conversation Inactive'}
                  </span>
                </div>
                
                <div className="flex space-x-2">
                  <button
                    onClick={conversationActive ? endConversation : startConversation}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      conversationActive
                        ? 'bg-red-500 text-white hover:bg-red-600'
                        : 'bg-green-500 text-white hover:bg-green-600'
                    }`}
                  >
                    {conversationActive ? 'End Conversation' : 'Start Conversation'}
                  </button>
                </div>
              </div>



              {/* Demo Scenarios (only show when not in conversation) */}
              {!conversationActive && (
                <DemoScenarios
                  onRunScenario={runDemoScenario}
                  showDemoScenarios={showDemoScenarios}
                  conversationActive={conversationActive}
                />
              )}

              {/* AudioRecorder for actual recording - integrated with the interface */}
              {conversationActive && (
                <div className="fixed bottom-0 left-0 right-0 bg-white shadow-lg border-t border-gray-200 p-4 z-50">
                  <div className="max-w-7xl mx-auto">
                    <div className="flex items-center justify-between">
                      {/* Speaker Toggle */}
                      <div className="flex items-center space-x-4">
                        <span className="text-sm font-medium text-gray-700">Speaker:</span>
                        <div className="flex bg-gray-100 rounded-lg p-1">
                          <button
                            onClick={() => setCurrentSpeaker('patient')}
                            className={`px-3 py-2 text-sm rounded-md transition-colors ${
                              currentSpeaker === 'patient'
                                ? 'bg-green-500 text-white shadow-sm'
                                : 'text-gray-600 hover:text-gray-800'
                            }`}
                          >
                            Patient (Spanish)
                          </button>
                          <button
                            onClick={() => setCurrentSpeaker('doctor')}
                            className={`px-3 py-2 text-sm rounded-md transition-colors ${
                              currentSpeaker === 'doctor'
                                ? 'bg-blue-500 text-white shadow-sm'
                                : 'text-gray-600 hover:text-gray-800'
                              }`}
                          >
                            Doctor (English)
                          </button>
                        </div>
                      </div>

                      {/* Audio Recorder */}
                      <div className="flex-1 max-w-md mx-8">
                        {!audioSupported ? (
                          <div className="text-center">
                            <p className="text-red-500 text-sm mb-2">Microphone access required</p>
                            <button
                              onClick={initializeAudio}
                              className="px-4 py-2 bg-yellow-500 text-white rounded-lg text-sm hover:bg-yellow-600"
                            >
                              Enable Microphone
                            </button>
                          </div>
                        ) : (
                          <AudioRecorder 
                            currentSpeaker={currentSpeaker}
                            onTranscription={(text, sessionId) => {
                              addDebugLog('info', `🎤 Audio transcription (${currentSpeaker}): ${text}`);
                              
                              // Add the original STT as a message (lower opacity for fidelity checking)
                              const timestamp = new Date().toISOString();
                              const originalMessage: ConversationMessage = {
                                id: `audio_${Date.now()}`,
                                speaker: currentSpeaker,
                                message_type: 'transcription',
                                content: { text },
                                timestamp: timestamp,
                                language: currentSpeaker === 'doctor' ? 'en' : 'es'
                              };
                              setMessages(prev => [...prev, originalMessage]);
                              
                              // Process the transcribed text through medical translation
                              // Note: sendTestMessage will add the translation message, not another transcription
                              sendTestMessage(text, currentSpeaker === 'doctor' ? 'en' : 'es');
                            }}
                          />
                        )}
                      </div>

                      {/* Export & End Buttons */}
                      <div className="flex space-x-2">
                        <button
                          onClick={() => {
                            const conversationData = {
                              sessionId,
                              timestamp: new Date().toISOString(),
                              messages: messages,
                              medicalContext: medicalContext,
                              medicalAlerts: medicalAlerts
                            };
                            const blob = new Blob([JSON.stringify(conversationData, null, 2)], { type: 'application/json' });
                            const url = URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = `conversation_${sessionId}_${new Date().toISOString().split('T')[0]}.json`;
                            a.click();
                            URL.revokeObjectURL(url);
                          }}
                          className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors text-sm font-medium"
                        >
                          📥 Export
                        </button>
                        <button
                          onClick={endConversation}
                          className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors text-sm font-medium"
                        >
                          End Conversation
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Conversation Messages */}
          <div className={conversationActive ? "pb-32" : ""}>
            <ConversationMessages
              messages={messages}
              showConfidenceScores={showConfidenceScores}
              showDebugInfo={showDebugInfo}
              conversationActive={conversationActive}
            />
          </div>
        </div>

        {/* Right Side - Medical Context */}
        <MedicalContextPanel
          medicalContext={medicalContext}
          medicalAlerts={medicalAlerts}
          showConfidenceScores={showConfidenceScores}
          showMedicalAlerts={showMedicalAlerts}
          showExtractionMethods={showExtractionMethods}
          conversationActive={conversationActive}
          messages={messages}
        />

        {/* Medical AI Panel - Toggleable */}
        <MedicalAIPanel
          medicalContext={medicalContext}
          medicalAlerts={medicalAlerts}
          showMedicalAI={showMedicalAI}
        />
      </div>

      {/* Debug Panel */}
      <DebugPanel
        showDebug={showDebug}
        debugLogs={debugLogs}
        onToggleDebug={() => setShowDebug(!showDebug)}
      />

      {/* Conversation Summary */}
      {!conversationActive && messages.length > 0 && (
        <ConversationSummary
          messages={messages}
          medicalAlerts={medicalAlerts}
          medicalContext={medicalContext}
          sessionId={sessionId}
        />
      )}
    </div>
  );
};

export default TalktorMedicalInterface;