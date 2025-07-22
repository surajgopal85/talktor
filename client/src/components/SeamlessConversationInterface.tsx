// components/SeamlessConversationInterface.tsx
import React, { useState, useEffect, useRef } from 'react';
import { 
  Mic, MicOff, Volume2, VolumeX, Phone, PhoneOff, 
  User, UserCheck, Stethoscope, AlertTriangle, 
  MessageSquare, FileText, Clock, Shield
} from 'lucide-react';

interface ConversationMessage {
  id: string;
  speaker: 'doctor' | 'patient' | 'system';
  message_type: string;
  content: any;
  timestamp: string;
  language: string;
}

interface MedicalAlert {
  type: string;
  message: string;
  severity: 'low' | 'medium' | 'high' | 'urgent';
  timestamp: string;
}

interface ConversationSession {
  session_id: string;
  doctor_language: string;
  patient_language: string;
  status: string;
}

export const SeamlessConversationInterface: React.FC = () => {
  // Connection State
  const [session, setSession] = useState<ConversationSession | null>(null);
  const [websocket, setWebsocket] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [currentRole, setCurrentRole] = useState<'doctor' | 'patient'>('doctor');

  // Conversation State
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [medicalAlerts, setMedicalAlerts] = useState<MedicalAlert[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeakerOn, setIsSpeakerOn] = useState(true);
  const [conversationActive, setConversationActive] = useState(false);

  // Medical Intelligence
  const [detectedConditions, setDetectedConditions] = useState<string[]>([]);
  const [currentMedications, setCurrentMedications] = useState<any[]>([]);
  const [followUpQuestions, setFollowUpQuestions] = useState<string[]>([]);

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const createSession = async () => {
    try {
      const response = await fetch('http://localhost:8000/conversation/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          doctor_language: 'en',
          patient_language: 'es',
          medical_specialty: 'obgyn'
        })
      });

      const sessionData = await response.json();
      setSession(sessionData);
      
      // Auto-connect after session creation
      setTimeout(() => connectWebSocket(sessionData), 500);
      
    } catch (error) {
      console.error('Session creation failed:', error);
    }
  };

  const connectWebSocket = (sessionData?: ConversationSession) => {
    const sessionToUse = sessionData || session;
    if (!sessionToUse) return;

    const wsUrl = `ws://localhost:8000/conversation/ws/${sessionToUse.session_id}/${currentRole}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setIsConnected(true);
      setWebsocket(ws);
      setConversationActive(true);
    };

    ws.onmessage = (event) => {
      const message: ConversationMessage = JSON.parse(event.data);
      
      // Add to messages
      setMessages(prev => [...prev, message]);
      
      // Process medical intelligence
      if (message.metadata?.medical_intelligence) {
        const intelligence = message.metadata.medical_intelligence;
        
        // Update medical context
        if (intelligence.obgyn_context?.identified_conditions) {
          setDetectedConditions(intelligence.obgyn_context.identified_conditions);
        }
        
        if (intelligence.medications) {
          setCurrentMedications(intelligence.medications);
        }
        
        if (intelligence.recommendations?.follow_up_questions) {
          setFollowUpQuestions(intelligence.recommendations.follow_up_questions);
        }
        
        // Handle safety alerts
        if (intelligence.recommendations?.safety_alerts) {
          intelligence.recommendations.safety_alerts.forEach((alert: any) => {
            setMedicalAlerts(prev => [...prev, {
              type: alert.type || 'safety_alert',
              message: alert.message,
              severity: alert.importance || 'medium',
              timestamp: new Date().toISOString()
            }]);
          });
        }
      }
      
      // Handle medical alerts
      if (message.message_type === 'medical_alert') {
        setMedicalAlerts(prev => [...prev, {
          type: message.content.alert_type,
          message: message.content.message,
          severity: message.content.severity || 'medium',
          timestamp: message.timestamp
        }]);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      setWebsocket(null);
      setConversationActive(false);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  };

  const sendTestMessage = (text: string, language: string = 'es') => {
    if (!websocket) return;
    
    const message = {
      type: "transcription",
      text: text,
      language: language
    };
    
    websocket.send(JSON.stringify(message));
  };

  const endConversation = async () => {
    if (websocket) {
      websocket.close();
    }
    
    if (session) {
      try {
        await fetch('http://localhost:8000/conversation/end', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: session.session_id })
        });
      } catch (error) {
        console.error('Error ending conversation:', error);
      }
    }
    
    // Reset state
    setSession(null);
    setMessages([]);
    setMedicalAlerts([]);
    setDetectedConditions([]);
    setCurrentMedications([]);
    setFollowUpQuestions([]);
    setConversationActive(false);
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const getSpeakerIcon = (speaker: string) => {
    switch (speaker) {
      case 'doctor': return <Stethoscope className="text-blue-600" size={16} />;
      case 'patient': return <User className="text-green-600" size={16} />;
      default: return <Shield className="text-gray-500" size={16} />;
    }
  };

  const getSpeakerName = (speaker: string) => {
    switch (speaker) {
      case 'doctor': return 'Doctor';
      case 'patient': return 'Patient';
      default: return 'System';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'urgent': return 'bg-red-100 border-red-500 text-red-800';
      case 'high': return 'bg-orange-100 border-orange-500 text-orange-800';
      case 'medium': return 'bg-yellow-100 border-yellow-500 text-yellow-800';
      default: return 'bg-blue-100 border-blue-500 text-blue-800';
    }
  };

  return (
    <div className="max-w-7xl mx-auto h-screen flex bg-white">
      {/* Main Conversation Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Stethoscope size={24} />
              <div>
                <h2 className="text-xl font-semibold">Medical Consultation</h2>
                <p className="text-blue-100 text-sm">
                  {session ? `Session: ${session.session_id.slice(0, 8)}...` : 'No active session'}
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              {/* Role Indicator */}
              <div className="flex items-center space-x-2 bg-blue-700 px-3 py-1 rounded-lg">
                {getSpeakerIcon(currentRole)}
                <span className="text-sm font-medium">{getSpeakerName(currentRole)}</span>
              </div>
              
              {/* Connection Status */}
              <div className={`px-3 py-1 rounded-lg text-sm ${
                isConnected ? 'bg-green-500' : 'bg-red-500'
              }`}>
                {isConnected ? '● Connected' : '○ Disconnected'}
              </div>
            </div>
          </div>
        </div>

        {/* Conversation Messages */}
        <div 
          ref={messagesContainerRef}
          className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50"
        >
          {messages.length === 0 && !conversationActive && (
            <div className="text-center py-12">
              <MessageSquare className="mx-auto text-gray-400 mb-4" size={48} />
              <h3 className="text-lg font-medium text-gray-700 mb-2">
                Ready to Start Medical Consultation
              </h3>
              <p className="text-gray-500">
                Click "Start Conversation" to begin real-time translation
              </p>
            </div>
          )}
          
          {messages.map((message) => (
            <div key={message.id} className="flex flex-col">
              {/* Transcription Messages */}
              {message.message_type === 'transcription' && (
                <div className={`flex ${message.speaker === 'doctor' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                    message.speaker === 'doctor' 
                      ? 'bg-blue-500 text-white' 
                      : 'bg-green-500 text-white'
                  }`}>
                    <div className="flex items-center space-x-2 mb-1">
                      {getSpeakerIcon(message.speaker)}
                      <span className="text-xs font-medium">
                        {getSpeakerName(message.speaker)} ({message.language?.toUpperCase()})
                      </span>
                      <span className="text-xs opacity-75">
                        {formatTimestamp(message.timestamp)}
                      </span>
                    </div>
                    <p className="text-sm">{message.content.text}</p>
                  </div>
                </div>
              )}
              
              {/* Translation Messages */}
              {message.message_type === 'translation' && (
                <div className={`flex ${message.speaker === 'doctor' ? 'justify-start' : 'justify-end'} mt-2`}>
                  <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg border-2 ${
                    message.speaker === 'doctor' 
                      ? 'bg-blue-50 border-blue-200 text-blue-900' 
                      : 'bg-green-50 border-green-200 text-green-900'
                  }`}>
                    <div className="flex items-center space-x-2 mb-1">
                      <Volume2 size={12} />
                      <span className="text-xs font-medium">
                        Translation ({message.content.target_language?.toUpperCase()})
                      </span>
                    </div>
                    <p className="text-sm font-medium">{message.content.translated_text}</p>
                  </div>
                </div>
              )}
              
              {/* Medical Alerts */}
              {message.message_type === 'medical_alert' && (
                <div className="flex justify-center my-2">
                  <div className={`px-4 py-3 rounded-lg border-l-4 ${getSeverityColor(message.content.severity)} max-w-md`}>
                    <div className="flex items-center space-x-2">
                      <AlertTriangle size={16} />
                      <span className="text-sm font-semibold">Medical Alert</span>
                    </div>
                    <p className="text-sm mt-1">{message.content.message}</p>
                  </div>
                </div>
              )}
            </div>
          ))}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Controls */}
        <div className="bg-white border-t p-4">
          {!conversationActive ? (
            <div className="flex justify-center space-x-4">
              <select
                value={currentRole}
                onChange={(e) => setCurrentRole(e.target.value as 'doctor' | 'patient')}
                className="border rounded-lg px-3 py-2"
              >
                <option value="doctor">Doctor (English)</option>
                <option value="patient">Patient (Spanish)</option>
              </select>
              
              <button
                onClick={createSession}
                className="bg-green-500 text-white px-6 py-2 rounded-lg hover:bg-green-600 flex items-center space-x-2"
              >
                <Phone size={16} />
                <span>Start Conversation</span>
              </button>
            </div>
          ) : (
            <div className="flex justify-between items-center">
              {/* Left: Audio Controls */}
              <div className="flex items-center space-x-4">
                <button
                  onClick={() => setIsRecording(!isRecording)}
                  className={`p-3 rounded-full ${
                    isRecording 
                      ? 'bg-red-500 text-white animate-pulse' 
                      : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
                  }`}
                >
                  {isRecording ? <Mic size={20} /> : <MicOff size={20} />}
                </button>
                
                <button
                  onClick={() => setIsSpeakerOn(!isSpeakerOn)}
                  className={`p-3 rounded-full ${
                    isSpeakerOn 
                      ? 'bg-blue-500 text-white' 
                      : 'bg-gray-200 text-gray-600'
                  }`}
                >
                  {isSpeakerOn ? <Volume2 size={20} /> : <VolumeX size={20} />}
                </button>
              </div>

              {/* Center: Quick Test Buttons */}
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => sendTestMessage("Estoy embarazada", "es")}
                  className="bg-purple-500 text-white px-3 py-2 rounded text-sm hover:bg-purple-600"
                >
                  🤰 Test: Pregnant
                </button>
                <button
                  onClick={() => sendTestMessage("tomando ibuprofeno", "es")}
                  className="bg-orange-500 text-white px-3 py-2 rounded text-sm hover:bg-orange-600"
                >
                  💊 Test: Ibuprofen
                </button>
              </div>

              {/* Right: End Call */}
              <button
                onClick={endConversation}
                className="bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600 flex items-center space-x-2"
              >
                <PhoneOff size={16} />
                <span>End Consultation</span>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Medical Intelligence Sidebar */}
      <div className="w-80 bg-white border-l flex flex-col">
        {/* Sidebar Header */}
        <div className="bg-gray-100 p-4 border-b">
          <h3 className="font-semibold text-gray-800 flex items-center space-x-2">
            <Shield size={20} />
            <span>Medical Intelligence</span>
          </h3>
        </div>

        {/* Medical Alerts */}
        {medicalAlerts.length > 0 && (
          <div className="p-4 border-b">
            <h4 className="font-medium text-gray-700 mb-2">🚨 Active Alerts</h4>
            <div className="space-y-2">
              {medicalAlerts.slice(-3).map((alert, i) => (
                <div key={i} className={`p-2 rounded border-l-4 text-sm ${getSeverityColor(alert.severity)}`}>
                  <p className="font-medium">{alert.type.replace('_', ' ').toUpperCase()}</p>
                  <p className="text-xs mt-1">{alert.message}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Detected Conditions */}
        {detectedConditions.length > 0 && (
          <div className="p-4 border-b">
            <h4 className="font-medium text-gray-700 mb-2">🔍 Detected Conditions</h4>
            <div className="space-y-1">
              {detectedConditions.map((condition, i) => (
                <span key={i} className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded mr-2">
                  {condition.replace('_', ' ')}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Current Medications */}
        {currentMedications.length > 0 && (
          <div className="p-4 border-b">
            <h4 className="font-medium text-gray-700 mb-2">💊 Medications Discussed</h4>
            <div className="space-y-2">
              {currentMedications.map((med, i) => (
                <div key={i} className="text-sm bg-gray-50 p-2 rounded">
                  <p className="font-medium">{med.original_term}</p>
                  <p className="text-xs text-gray-600">Confidence: {(med.extraction_confidence * 100).toFixed(0)}%</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Follow-up Questions */}
        {followUpQuestions.length > 0 && (
          <div className="p-4">
            <h4 className="font-medium text-gray-700 mb-2">❓ Suggested Questions</h4>
            <div className="space-y-2">
              {followUpQuestions.slice(0, 3).map((question, i) => (
                <button
                  key={i}
                  onClick={() => sendTestMessage(question, 'en')}
                  className="w-full text-left text-sm bg-gray-50 hover:bg-gray-100 p-2 rounded border"
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {medicalAlerts.length === 0 && detectedConditions.length === 0 && currentMedications.length === 0 && (
          <div className="p-4 text-center text-gray-500">
            <FileText className="mx-auto mb-2" size={32} />
            <p className="text-sm">Medical intelligence will appear here during the conversation</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default SeamlessConversationInterface;