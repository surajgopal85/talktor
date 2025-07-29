import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  Mic, MicOff, Volume2, Phone, PhoneOff, 
  User, Stethoscope, AlertTriangle, 
  MessageSquare, Shield, Activity, Bug, Globe, Heart, Clock, CheckCircle
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

export const TalktorMedicalInterface: React.FC = () => {
  // Basic State
  const [session, setSession] = useState<ConversationSession | null>(null);
  const [websocket, setWebsocket] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [currentRole, setCurrentRole] = useState<'doctor' | 'patient'>('doctor');
  const [conversationActive, setConversationActive] = useState(false);

  // Messages & Medical Intelligence
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [medicalAlerts, setMedicalAlerts] = useState<MedicalAlert[]>([]);
  const [medicalContext, setMedicalContext] = useState<any>(null);

  // Audio State
  const [isListening, setIsListening] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [audioSupported, setAudioSupported] = useState(true);

  // Debug State
  const [debugLogs, setDebugLogs] = useState<DebugLog[]>([]);
  const [showDebug, setShowDebug] = useState(false);

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Debug logging function
  const addDebugLog = useCallback((level: 'info' | 'error' | 'warning', message: string, data?: any) => {
    const log: DebugLog = {
      timestamp: new Date().toISOString(),
      level,
      message,
      data
    };
    
    setDebugLogs(prev => [...prev.slice(-49), log]);
    console[level](`[${level.toUpperCase()}] ${message}`, data || '');
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Create session
  const createSession = async () => {
    try {
      addDebugLog('info', '🚀 Creating session...');
      
      const response = await fetch('http://localhost:8000/conversation/create', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          doctor_language: 'en',
          patient_language: 'es',
          medical_specialty: 'obgyn'
        })
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      const sessionData = await response.json();
      addDebugLog('info', '✅ Session created successfully', sessionData);
      
      setSession(sessionData);
      setTimeout(() => connectWebSocket(sessionData), 1000);
      
    } catch (error) {
      addDebugLog('error', '❌ Session creation failed', error);
      alert(`Session creation failed: ${error}`);
    }
  };

  // Connect WebSocket
  const connectWebSocket = useCallback((sessionData?: ConversationSession) => {
    const sessionToUse = sessionData || session;
    if (!sessionToUse) {
      addDebugLog('error', '❌ No session available for WebSocket connection');
      return;
    }

    const wsUrl = `ws://localhost:8000/api/v2/conversation/ws/${sessionToUse.session_id}/${currentRole}`;
    addDebugLog('info', `🔗 Connecting to WebSocket: ${wsUrl}`);

    try {
      const ws = new WebSocket(wsUrl);

      const connectionTimeout = setTimeout(() => {
        if (ws.readyState === WebSocket.CONNECTING) {
          addDebugLog('error', '⏰ WebSocket connection timeout');
          ws.close();
        }
      }, 10000);

      ws.onopen = () => {
        clearTimeout(connectionTimeout);
        addDebugLog('info', `✅ WebSocket connected as ${currentRole}`);
        setIsConnected(true);
        setWebsocket(ws);
        setConversationActive(true);
        
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }
      };

      ws.onmessage = (event) => {
        try {
          const message: ConversationMessage = JSON.parse(event.data);
          addDebugLog('info', '📨 Received WebSocket message', { 
            type: message.message_type, 
            speaker: message.speaker,
            contentPreview: typeof message.content === 'string' ? message.content.slice(0, 50) : 'Object'
          });
          handleIncomingMessage(message);
        } catch (error) {
          addDebugLog('error', '❌ Error parsing WebSocket message', { event: event.data, error });
        }
      };

      ws.onclose = (event) => {
        clearTimeout(connectionTimeout);
        addDebugLog('warning', `🔌 WebSocket closed: ${event.code} - ${event.reason}`);
        setIsConnected(false);
        setWebsocket(null);
        setIsListening(false);
        
        if (event.code !== 1000) {
          addDebugLog('info', '🔄 Attempting reconnection in 3 seconds...');
          reconnectTimeoutRef.current = setTimeout(() => {
            if (sessionToUse) {
              connectWebSocket(sessionToUse);
            }
          }, 3000);
        } else {
          setConversationActive(false);
        }
      };

      ws.onerror = (error) => {
        clearTimeout(connectionTimeout);
        addDebugLog('error', '❌ WebSocket error', error);
      };

    } catch (error) {
      addDebugLog('error', '❌ WebSocket connection failed', error);
    }
  }, [session, currentRole, addDebugLog]);

  // Handle incoming messages - THIS IS WHERE WE FIX TRANSLATION DISPLAY
  const handleIncomingMessage = useCallback((message: ConversationMessage) => {
    // Add all messages to the conversation
    setMessages(prev => [...prev, message]);

    // Handle specific message types
    switch (message.message_type) {
      case 'system_status':
        addDebugLog('info', '🔧 System status update', message.content);
        break;

      case 'transcription':
      case 'streaming_transcription':
        addDebugLog('info', '🎤 Transcription received', { 
          text: message.content?.text, 
          confidence: message.content?.confidence 
        });
        break;

      case 'translation':
        addDebugLog('info', '🔄 Translation received', { 
          original: message.content?.original_text,
          translated: message.content?.translated_text,
          confidence: message.content?.confidence
        });
        // Translation messages are now properly handled and will appear in the UI
        break;

      case 'medical_alert':
        const alert: MedicalAlert = {
          id: message.id,
          type: message.content?.alert_type || 'alert',
          message: message.content?.message || 'Medical alert',
          severity: message.content?.severity || 'medium',
          timestamp: message.timestamp
        };
        setMedicalAlerts(prev => [...prev, alert]);
        addDebugLog('warning', '🚨 Medical alert generated', alert);
        break;

      case 'conversation_summary':
        setMedicalContext(message.content);
        addDebugLog('info', '📋 Conversation summary updated', message.content);
        break;

      case 'audio_status':
        if (message.content?.audio_level !== undefined) {
          setAudioLevel(message.content.audio_level);
        }
        break;

      case 'error':
        addDebugLog('error', '❌ Server error', message.content);
        break;
    }
  }, [addDebugLog]);

  // Audio initialization
  const initializeAudio = useCallback(async () => {
    try {
      addDebugLog('info', '🎤 Initializing audio...');
      
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('MediaDevices API not supported');
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });
      
      streamRef.current = stream;
      addDebugLog('info', '✅ Audio stream acquired');

      const mimeTypes = [
        'audio/webm;codecs=opus',
        'audio/webm',
        'audio/mp4',
        'audio/ogg'
      ];

      let selectedMimeType = '';
      for (const mimeType of mimeTypes) {
        if (MediaRecorder.isTypeSupported(mimeType)) {
          selectedMimeType = mimeType;
          break;
        }
      }

      if (!selectedMimeType) {
        throw new Error('No supported audio format found');
      }

      mediaRecorderRef.current = new MediaRecorder(stream, {
        mimeType: selectedMimeType
      });
      
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0 && websocket && websocket.readyState === WebSocket.OPEN) {
          const reader = new FileReader();
          reader.onloadend = () => {
            const base64Audio = (reader.result as string).split(',')[1];
            
            const audioMessage = {
              type: 'audio_chunk_stream',
              audio_data: base64Audio,
              language: currentRole === 'doctor' ? 'en' : 'es'
            };

            websocket.send(JSON.stringify(audioMessage));
            addDebugLog('info', `📤 Sent audio chunk (${event.data.size} bytes)`);
          };
          reader.readAsDataURL(event.data);
        }
      };
      
      addDebugLog('info', '✅ Audio initialized successfully');
      return true;
    } catch (error) {
      addDebugLog('error', '❌ Audio initialization failed', error);
      setAudioSupported(false);
      alert('Could not access microphone. Please check permissions.');
      return false;
    }
  }, [websocket, currentRole, addDebugLog]);

  // Toggle listening
  const toggleListening = useCallback(async () => {
    if (!audioSupported) {
      alert('Audio not supported or not initialized');
      return;
    }

    if (!websocket || websocket.readyState !== WebSocket.OPEN) {
      addDebugLog('error', '❌ WebSocket not connected for audio');
      alert('WebSocket not connected. Cannot start audio streaming.');
      return;
    }

    if (!isListening) {
      addDebugLog('info', '🎤 Starting audio recording...');
      
      const audioReady = await initializeAudio();
      if (audioReady && mediaRecorderRef.current) {
        try {
          websocket.send(JSON.stringify({ type: 'start_listening' }));
          mediaRecorderRef.current.start(250);
          setIsListening(true);
          addDebugLog('info', '✅ Audio recording started');
        } catch (error) {
          addDebugLog('error', '❌ Failed to start recording', error);
        }
      }
    } else {
      addDebugLog('info', '🎤 Stopping audio recording...');
      
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        mediaRecorderRef.current.stop();
      }
      
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
        streamRef.current = null;
      }
      
      if (websocket && websocket.readyState === WebSocket.OPEN) {
        websocket.send(JSON.stringify({ type: 'stop_listening' }));
      }
      
      setIsListening(false);
      setAudioLevel(0);
      addDebugLog('info', '✅ Audio recording stopped');
    }
  }, [isListening, audioSupported, initializeAudio, websocket, addDebugLog]);

  // Send test message
  const sendTestMessage = (text: string, language: string) => {
    if (!websocket || websocket.readyState !== WebSocket.OPEN) {
      addDebugLog('error', '❌ Cannot send test message - WebSocket not connected');
      alert('WebSocket not connected!');
      return;
    }
    
    const message = {
      type: "transcription",
      text: text,
      language: language
    };
    
    addDebugLog('info', '📤 Sending test message', message);
    websocket.send(JSON.stringify(message));
  };

  // End conversation
  const endConversation = async () => {
    addDebugLog('info', '📞 Ending conversation...');
    
    if (isListening) {
      toggleListening();
    }
    
    if (websocket) {
      websocket.close(1000, 'User ended conversation');
    }
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (session) {
      try {
        await fetch('http://localhost:8000/conversation/end', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: session.session_id })
        });
        addDebugLog('info', '✅ Session ended on backend');
      } catch (error) {
        addDebugLog('error', '❌ Failed to end session on backend', error);
      }
    }
    
    setSession(null);
    setMessages([]);
    setMedicalAlerts([]);
    setMedicalContext(null);
    setConversationActive(false);
    setIsListening(false);
    setIsConnected(false);
  };

  // Utility functions
  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit',
      second: '2-digit'
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
      case 'doctor': return 'Healthcare Provider';
      case 'patient': return 'Patient';
      default: return 'System';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'urgent':
      case 'high': 
        return 'bg-red-100 border-red-500 text-red-800';
      case 'medium': 
        return 'bg-yellow-100 border-yellow-500 text-yellow-800';
      default: 
        return 'bg-blue-100 border-blue-500 text-blue-800';
    }
  };

  // Render message content - FIXED TO HANDLE TRANSLATIONS PROPERLY
  const renderMessageContent = (message: ConversationMessage) => {
    const content = message.content;
    
    // Handle different message types with specific rendering
    if (message.message_type === 'translation') {
      return (
        <div className="space-y-2">
          <div className="p-3 bg-gray-100 rounded-lg">
            <div className="text-xs font-medium text-gray-600 mb-1">Original:</div>
            <div className="font-medium">{content?.original_text}</div>
          </div>
          <div className="p-3 bg-blue-50 rounded-lg border-2 border-blue-200">
            <div className="flex items-center space-x-1 mb-1">
              <Globe className="w-3 h-3 text-blue-600" />
              <span className="text-xs font-medium text-blue-600">TRANSLATION</span>
              {content?.confidence && (
                <span className="text-xs text-blue-500">
                  ({Math.round(content.confidence * 100)}% confidence)
                </span>
              )}
            </div>
            <div className="font-medium text-blue-800">{content?.translated_text}</div>
          </div>
        </div>
      );
    }
    
    // Handle transcription messages
    if (message.message_type === 'transcription' || message.message_type === 'streaming_transcription') {
      return (
        <div>
          <div className="font-medium">{content?.text}</div>
          {content?.confidence && (
            <div className="text-xs mt-1 opacity-75">
              Confidence: {Math.round(content.confidence * 100)}%
            </div>
          )}
        </div>
      );
    }

    // Handle medical alerts
    if (message.message_type === 'medical_alert') {
      return (
        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-red-600" />
            <span className="font-semibold text-red-800">MEDICAL ALERT</span>
          </div>
          <div className="font-medium">{content?.message}</div>
          {content?.clinical_recommendation && (
            <div className="text-sm mt-2 p-2 bg-red-50 rounded border-l-4 border-red-300">
              <strong>Clinical Recommendation:</strong> {content.clinical_recommendation}
            </div>
          )}
        </div>
      );
    }
    
    // Fallback for other content types
    if (typeof content === 'string') {
      return content;
    }
    
    if (content?.text) {
      return content.text;
    }
    
    if (content?.message) {
      return content.message;
    }

    if (content?.status) {
      return `Status: ${content.status}`;
    }
    
    try {
      return JSON.stringify(content, null, 2);
    } catch {
      return 'Invalid message content';
    }
  };

  const getActualMedications = (context: any) => {
    if (!context?.medications_discussed) return [];
    
    const nonMedications = ['estoy', 'embarazada', 'tomando', 'tengo', 'dolor', 'cabeza'];
    
    return context.medications_discussed.filter((med: any) => 
      med.original_term && 
      !nonMedications.includes(med.original_term.toLowerCase()) &&
      med.extraction_confidence > 0.6
    );
  };

  return (
    <div className="h-screen bg-gradient-to-br from-blue-50 via-white to-green-50 flex">
      {/* Left Sidebar - Medical Intelligence */}
      <div className="w-80 bg-white shadow-xl border-r border-gray-200 flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-gray-100 bg-gradient-to-r from-blue-600 to-green-600">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-white/20 rounded-lg">
              <Stethoscope className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">Talktor</h1>
              <p className="text-blue-100 text-sm">Medical AI Interpreter</p>
            </div>
          </div>
        </div>

        {/* Connection Status */}
        <div className="p-4 border-b border-gray-100">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">Connection Status</span>
            <div className={`flex items-center space-x-2 ${isConnected ? 'text-green-600' : 'text-red-600'}`}>
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
              <span className="text-sm capitalize">{isConnected ? 'Connected' : 'Disconnected'}</span>
            </div>
          </div>
        </div>

        {/* Medical Alerts */}
        <div className="flex-1 overflow-y-auto">
          <div className="p-4">
            <h3 className="font-semibold text-gray-800 mb-3 flex items-center">
              <Shield className="w-4 h-4 mr-2 text-red-500" />
              Safety Alerts ({medicalAlerts.length})
            </h3>
            
            {medicalAlerts.map((alert) => (
              <div key={alert.id} className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-start">
                  <AlertTriangle className="w-5 h-5 text-red-600 mr-2 mt-0.5 flex-shrink-0" />
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-semibold text-red-800 text-sm">CRITICAL ALERT</span>
                      <span className="text-xs text-gray-500">{formatTimestamp(alert.timestamp)}</span>
                    </div>
                    <p className="text-sm text-red-700">{alert.message}</p>
                    <div className="mt-2 text-xs text-red-600">
                      <span className="font-medium">Type:</span> {alert.type}
                    </div>
                  </div>
                </div>
              </div>
            ))}
            
            {medicalAlerts.length === 0 && (
              <div className="text-center py-4 text-gray-500">
                <Shield className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No active alerts</p>
              </div>
            )}
          </div>

          {/* Medical Intelligence Summary */}
          {medicalContext && (
            <div className="p-4 border-t border-gray-100">
              <h3 className="font-semibold text-gray-800 mb-3 flex items-center">
                <Heart className="w-4 h-4 mr-2 text-blue-500" />
                Session Intelligence
              </h3>
              
              <div className="space-y-3">
                <div className="p-3 bg-blue-50 rounded-lg">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-blue-800">Medications Detected</span>
                    <span className="text-xs bg-blue-200 text-blue-800 px-2 py-1 rounded">
                      {getActualMedications(medicalContext).length}
                    </span>
                  </div>
                  {getActualMedications(medicalContext).map((med: any, index: number) => (
                    <div key={index} className="text-sm text-blue-700">
                      • {med.original_term}
                    </div>
                  ))}
                </div>

                <div className="p-3 bg-green-50 rounded-lg">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-green-800">Specialization</span>
                    <CheckCircle className="w-4 h-4 text-green-600" />
                  </div>
                  <div className="text-sm text-green-700">OBGYN Active</div>
                </div>

                <div className="p-3 bg-orange-50 rounded-lg">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-orange-800">Safety Alerts</span>
                    <span className="text-xs bg-orange-200 text-orange-800 px-2 py-1 rounded">
                      {medicalAlerts.length}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Debug Toggle */}
        <div className="p-4 border-t border-gray-100">
          <button
            onClick={() => setShowDebug(!showDebug)}
            className={`w-full flex items-center justify-center space-x-2 px-3 py-2 rounded-lg text-sm ${
              showDebug ? 'bg-yellow-100 text-yellow-800' : 'bg-gray-100 text-gray-600'
            }`}
          >
            <Bug className="w-4 h-4" />
            <span>{showDebug ? 'Hide' : 'Show'} Debug Logs</span>
          </button>
        </div>
      </div>

      {/* Main Conversation Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white shadow-sm border-b border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Globe className="w-5 h-5 text-blue-600" />
                <span className="font-semibold text-gray-800">Live Medical Translation</span>
              </div>
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <Clock className="w-4 h-4" />
                <span>Session: {session ? `${session.session_id.slice(0, 8)}...` : 'Not started'}</span>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-2 bg-gray-100 px-3 py-1 rounded-lg">
                {getSpeakerIcon(currentRole)}
                <span className="text-sm font-medium">
                  {currentRole === 'doctor' ? 'Provider (EN→ES)' : 'Patient (ES→EN)'}
                </span>
              </div>
              
              <div className={`px-3 py-1 rounded-lg text-sm flex items-center space-x-1 ${
                isConnected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              }`}>
                <Activity size={12} />
                <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Debug Panel */}
        {showDebug && (
          <div className="bg-gray-900 text-green-400 p-4 border-b max-h-64 overflow-y-auto font-mono text-xs">
            <div className="flex justify-between items-center mb-2">
              <span className="text-green-300 font-bold">Debug Logs ({debugLogs.length})</span>
              <button
                onClick={() => setDebugLogs([])}
                className="text-red-400 hover:text-red-300"
              >
                Clear
              </button>
            </div>
            {debugLogs.slice(-20).map((log, index) => (
              <div key={index} className={`mb-1 ${
                log.level === 'error' ? 'text-red-400' : 
                log.level === 'warning' ? 'text-yellow-400' : 
                'text-green-400'
              }`}>
                <span className="text-gray-500">[{formatTimestamp(log.timestamp)}]</span> {log.message}
                {log.data && <div className="ml-4 text-gray-400">{JSON.stringify(log.data, null, 2)}</div>}
              </div>
            ))}
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 && !conversationActive && (
            <div className="text-center py-12">
              <MessageSquare className="mx-auto text-gray-400 mb-4" size={48} />
              <h3 className="text-lg font-medium text-gray-700 mb-2">
                Ready for Medical Consultation
              </h3>
              <p className="text-gray-500 mb-4">
                Professional medical translation with OBGYN specialization
              </p>
            </div>
          )}
          
          {messages.map((message) => (
            <div key={message.id} className={`flex ${
              message.speaker === 'doctor' ? 'justify-end' : 
              message.speaker === 'patient' ? 'justify-start' : 
              'justify-center'
            }`}>
              <div className={`max-w-2xl ${message.speaker === 'doctor' ? 'order-2' : 'order-1'}`}>
                <div className={`flex items-center space-x-2 mb-1 ${
                  message.speaker === 'doctor' ? 'justify-end' : 'justify-start'
                }`}>
                  <div className={`flex items-center space-x-1 ${
                    message.speaker === 'doctor' ? 'flex-row-reverse space-x-reverse' : ''
                  }`}>
                    {getSpeakerIcon(message.speaker)}
                    <span className="text-sm font-medium text-gray-700">
                      {getSpeakerName(message.speaker)}
                    </span>
                    <span className="text-xs text-gray-500">{message.message_type}</span>
                    <span className="text-xs text-gray-500">{formatTimestamp(message.timestamp)}</span>
                  </div>
                </div>
                
                <div className={`${
                  message.speaker === 'doctor' ? 'text-right' : 
                  message.speaker === 'patient' ? 'text-left' : 
                  'text-center'
                }`}>
                  <div className={`inline-block p-4 rounded-lg shadow-sm ${
                    message.speaker === 'doctor' ? 'bg-blue-600 text-white' :
                    message.speaker === 'patient' ? 'bg-green-500 text-white' :
                    message.message_type === 'medical_alert' ? getSeverityColor(message.content?.severity || 'medium') :
                    message.message_type === 'translation' ? 'bg-purple-50 border border-purple-200' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {renderMessageContent(message)}
                  </div>
                </div>
              </div>
            </div>
          ))}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Controls */}
        <div className="bg-white border-t border-gray-200 p-6">
          {!conversationActive ? (
            <div className="flex justify-center space-x-4">
              <select
                value={currentRole}
                onChange={(e) => setCurrentRole(e.target.value as 'doctor' | 'patient')}
                className="border border-gray-300 rounded-lg px-3 py-2 bg-white"
              >
                <option value="doctor">👩‍⚕️ Healthcare Provider (English → Spanish)</option>
                <option value="patient">👤 Patient (Spanish → English)</option>
              </select>
              
              <button
                onClick={createSession}
                className="bg-green-500 text-white px-6 py-2 rounded-lg hover:bg-green-600 flex items-center space-x-2 shadow-sm"
              >
                <Phone size={16} />
                <span>Start Medical Consultation</span>
              </button>
            </div>
          ) : (
            <div className="flex justify-between items-center">
              {/* Audio Controls */}
              <div className="flex items-center space-x-4">
                <button
                  onClick={toggleListening}
                  disabled={!isConnected || !audioSupported}
                  className={`p-3 rounded-full shadow-sm transition-all ${
                    isListening 
                      ? 'bg-red-500 text-white animate-pulse' 
                      : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
                  } ${!isConnected || !audioSupported ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  {isListening ? <Mic size={20} /> : <MicOff size={20} />}
                </button>
                
                {isListening && (
                  <div className="flex items-center space-x-2">
                    <Volume2 className="w-4 h-4 text-gray-500" />
                    <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-green-500 transition-all duration-100"
                        style={{ width: `${Math.min(audioLevel * 1000, 100)}%` }}
                      />
                    </div>
                    <span className="text-xs text-gray-500">
                      {audioLevel > 0.01 ? 'Speaking...' : 'Silent'}
                    </span>
                  </div>
                )}
              </div>

              {/* Test Buttons */}
              <div className="flex items-center space-x-2">
                <span className="text-xs text-gray-500">Quick Tests:</span>
                <button
                  onClick={() => sendTestMessage("Estoy embarazada tomando ibuprofeno", "es")}
                  className="bg-red-500 text-white px-3 py-2 rounded text-sm hover:bg-red-600"
                >
                  🚨 Safety Alert Test
                </button>
                <button
                  onClick={() => sendTestMessage("How are you feeling today?", "en")}
                  className="bg-blue-500 text-white px-3 py-2 rounded text-sm hover:bg-blue-600"
                >
                  💬 Translation Test
                </button>
              </div>

              {/* End Call */}
              <button
                onClick={endConversation}
                className="bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600 flex items-center space-x-2"
              >
                <PhoneOff size={16} />
                <span>End Session</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TalktorMedicalInterface;
// // components/SeamlessConversationInterface.tsx - FIXED VERSION
// import React, { useState, useEffect, useRef, useCallback } from 'react';
// import { 
//   Mic, MicOff, Volume2, Phone, PhoneOff, 
//   User, Stethoscope, AlertTriangle, 
//   MessageSquare, Shield, Activity, Bug
// } from 'lucide-react';

// interface ConversationMessage {
//   id: string;
//   speaker: 'doctor' | 'patient' | 'system';
//   message_type: string;
//   content: any;
//   timestamp: string;
//   language: string;
// }

// interface MedicalAlert {
//   id: string;
//   type: string;
//   message: string;
//   severity: string;
//   timestamp: string;
// }

// interface ConversationSession {
//   session_id: string;
//   doctor_language: string;
//   patient_language: string;
//   status: string;
// }

// interface DebugLog {
//   timestamp: string;
//   level: 'info' | 'error' | 'warning';
//   message: string;
//   data?: any;
// }

// export const SeamlessConversationInterface: React.FC = () => {
//   // Basic State
//   const [session, setSession] = useState<ConversationSession | null>(null);
//   const [websocket, setWebsocket] = useState<WebSocket | null>(null);
//   const [isConnected, setIsConnected] = useState(false);
//   const [currentRole, setCurrentRole] = useState<'doctor' | 'patient'>('doctor');
//   const [conversationActive, setConversationActive] = useState(false);

//   // Messages & Medical Intelligence
//   const [messages, setMessages] = useState<ConversationMessage[]>([]);
//   const [medicalAlerts, setMedicalAlerts] = useState<MedicalAlert[]>([]);
//   const [medicalContext, setMedicalContext] = useState<any>(null);

//   // Audio State
//   const [isListening, setIsListening] = useState(false);
//   const [audioLevel, setAudioLevel] = useState(0);
//   const [audioSupported, setAudioSupported] = useState(true);

//   // Debug State
//   const [debugLogs, setDebugLogs] = useState<DebugLog[]>([]);
//   const [showDebug, setShowDebug] = useState(false);
//   const [showDetailedSummary, setShowDetailedSummary] = useState(false);

//   // Refs
//   const messagesEndRef = useRef<HTMLDivElement>(null);
//   const mediaRecorderRef = useRef<MediaRecorder | null>(null);
//   const streamRef = useRef<MediaStream | null>(null);
//   const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

//   // Debug logging function
//   const addDebugLog = useCallback((level: 'info' | 'error' | 'warning', message: string, data?: any) => {
//     const log: DebugLog = {
//       timestamp: new Date().toISOString(),
//       level,
//       message,
//       data
//     };
    
//     setDebugLogs(prev => [...prev.slice(-49), log]); // Keep last 50 logs
    
//     // Also log to console
//     console[level](`[${level.toUpperCase()}] ${message}`, data || '');
//   }, []);

//   // Auto-scroll to bottom
//   useEffect(() => {
//     messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
//   }, [messages]);

//   // Create session with better error handling
//   const createSession = async () => {
//     try {
//       addDebugLog('info', '🚀 Creating session...');
      
//       const response = await fetch('http://localhost:8000/conversation/create', {
//         method: 'POST',
//         headers: { 
//           'Content-Type': 'application/json',
//           'Accept': 'application/json'
//         },
//         body: JSON.stringify({
//           doctor_language: 'en',
//           patient_language: 'es',
//           medical_specialty: 'obgyn'
//         })
//       });

//       addDebugLog('info', `Session API response: ${response.status} ${response.statusText}`);

//       if (!response.ok) {
//         const errorText = await response.text();
//         throw new Error(`HTTP ${response.status}: ${errorText}`);
//       }

//       const sessionData = await response.json();
//       addDebugLog('info', '✅ Session created successfully', sessionData);
      
//       setSession(sessionData);
      
//       // Auto-connect WebSocket after a short delay
//       setTimeout(() => connectWebSocket(sessionData), 1000);
      
//     } catch (error) {
//       addDebugLog('error', '❌ Session creation failed', error);
//       alert(`Session creation failed: ${error}`);
//     }
//   };

//   // Connect WebSocket with better error handling and reconnection
//   const connectWebSocket = useCallback((sessionData?: ConversationSession) => {
//     const sessionToUse = sessionData || session;
//     if (!sessionToUse) {
//       addDebugLog('error', '❌ No session available for WebSocket connection');
//       return;
//     }

//     // CORRECT: Your backend DOES use /api/v2 prefix for WebSocket
//     const wsUrl = `ws://localhost:8000/api/v2/conversation/ws/${sessionToUse.session_id}/${currentRole}`;
//     addDebugLog('info', `🔗 Connecting to WebSocket: ${wsUrl}`);

//     try {
//       const ws = new WebSocket(wsUrl);

//       // Set connection timeout
//       const connectionTimeout = setTimeout(() => {
//         if (ws.readyState === WebSocket.CONNECTING) {
//           addDebugLog('error', '⏰ WebSocket connection timeout');
//           ws.close();
//         }
//       }, 10000);

//       ws.onopen = () => {
//         clearTimeout(connectionTimeout);
//         addDebugLog('info', `✅ WebSocket connected as ${currentRole}`);
//         setIsConnected(true);
//         setWebsocket(ws);
//         setConversationActive(true);
        
//         // Clear any pending reconnection
//         if (reconnectTimeoutRef.current) {
//           clearTimeout(reconnectTimeoutRef.current);
//           reconnectTimeoutRef.current = null;
//         }
//       };

//       ws.onmessage = (event) => {
//         try {
//           const message: ConversationMessage = JSON.parse(event.data);
//           addDebugLog('info', '📨 Received WebSocket message', { 
//             type: message.message_type, 
//             speaker: message.speaker,
//             contentPreview: typeof message.content === 'string' ? message.content.slice(0, 50) : 'Object'
//           });
//           handleIncomingMessage(message);
//         } catch (error) {
//           addDebugLog('error', '❌ Error parsing WebSocket message', { event: event.data, error });
//         }
//       };

//       ws.onclose = (event) => {
//         clearTimeout(connectionTimeout);
//         addDebugLog('warning', `🔌 WebSocket closed: ${event.code} - ${event.reason}`);
//         setIsConnected(false);
//         setWebsocket(null);
//         setIsListening(false);
        
//         // Only set conversation inactive if it wasn't a manual close
//         if (event.code !== 1000) {
//           // Attempt reconnection after 3 seconds
//           addDebugLog('info', '🔄 Attempting reconnection in 3 seconds...');
//           reconnectTimeoutRef.current = setTimeout(() => {
//             if (sessionToUse) {
//               connectWebSocket(sessionToUse);
//             }
//           }, 3000);
//         } else {
//           setConversationActive(false);
//         }
//       };

//       ws.onerror = (error) => {
//         clearTimeout(connectionTimeout);
//         addDebugLog('error', '❌ WebSocket error', error);
//       };

//     } catch (error) {
//       addDebugLog('error', '❌ WebSocket connection failed', error);
//     }
//   }, [session, currentRole, addDebugLog]);

//   // Handle incoming messages with better type checking
//   const handleIncomingMessage = useCallback((message: ConversationMessage) => {
//     // Add all messages to the conversation
//     setMessages(prev => [...prev, message]);

//     // Handle specific message types
//     switch (message.message_type) {
//       case 'system_status':
//         addDebugLog('info', '🔧 System status update', message.content);
//         break;

//       case 'transcription':
//       case 'streaming_transcription': // Backend sends this type for streaming
//         addDebugLog('info', '🎤 Transcription received', { 
//           text: message.content?.text, 
//           confidence: message.content?.confidence 
//         });
//         break;

//       case 'translation':
//         addDebugLog('info', '🔄 Translation received', { 
//           original: message.content?.original_text,
//           translated: message.content?.translated_text,
//           confidence: message.content?.confidence
//         });
//         break;

//       case 'medical_alert':
//         const alert: MedicalAlert = {
//           id: message.id,
//           type: message.content?.alert_type || 'alert',
//           message: message.content?.message || 'Medical alert',
//           severity: message.content?.severity || 'medium',
//           timestamp: message.timestamp
//         };
//         setMedicalAlerts(prev => [...prev, alert]);
//         addDebugLog('warning', '🚨 Medical alert generated', alert);
//         break;

//       case 'conversation_summary':
//         setMedicalContext(message.content);
//         addDebugLog('info', '📋 Conversation summary updated', message.content);
//         break;

//       case 'audio_status':
//         if (message.content?.audio_level !== undefined) {
//           setAudioLevel(message.content.audio_level);
//         }
//         if (message.content?.status) {
//           addDebugLog('info', `🎤 Audio status: ${message.content.status}`);
//         }
//         break;

//       case 'streaming_tts':
//         addDebugLog('info', '🔊 Received TTS audio chunk');
//         // Handle TTS audio if needed
//         break;

//       case 'error':
//         addDebugLog('error', '❌ Server error', message.content);
//         break;

//       default:
//         addDebugLog('info', `📨 Unknown message type: ${message.message_type}`, message);
//     }
//   }, [addDebugLog]);

//   // Simplified audio initialization
//   const initializeAudio = useCallback(async () => {
//     try {
//       addDebugLog('info', '🎤 Initializing audio...');
      
//       if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
//         throw new Error('MediaDevices API not supported');
//       }

//       const stream = await navigator.mediaDevices.getUserMedia({
//         audio: {
//           sampleRate: 16000,
//           channelCount: 1,
//           echoCancellation: true,
//           noiseSuppression: true,
//           autoGainControl: true
//         }
//       });
      
//       streamRef.current = stream;
//       addDebugLog('info', '✅ Audio stream acquired');

//       // Check MediaRecorder support
//       if (!MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
//         addDebugLog('warning', '⚠️ Opus codec not supported, trying default');
//       }

//       // Set up media recorder with fallback mime types
//       const mimeTypes = [
//         'audio/webm;codecs=opus',
//         'audio/webm',
//         'audio/mp4',
//         'audio/ogg'
//       ];

//       let selectedMimeType = '';
//       for (const mimeType of mimeTypes) {
//         if (MediaRecorder.isTypeSupported(mimeType)) {
//           selectedMimeType = mimeType;
//           break;
//         }
//       }

//       if (!selectedMimeType) {
//         throw new Error('No supported audio format found');
//       }

//       addDebugLog('info', `🎵 Using audio format: ${selectedMimeType}`);

//       mediaRecorderRef.current = new MediaRecorder(stream, {
//         mimeType: selectedMimeType
//       });
      
//       mediaRecorderRef.current.ondataavailable = (event) => {
//         if (event.data.size > 0 && websocket && websocket.readyState === WebSocket.OPEN) {
//           // Convert to base64 and send
//           const reader = new FileReader();
//           reader.onloadend = () => {
//             const base64Audio = (reader.result as string).split(',')[1];
            
//             const audioMessage = {
//               type: 'audio_chunk_stream', // Match backend StreamingAudioMessageTypes.AUDIO_CHUNK_STREAM
//               audio_data: base64Audio,
//               language: currentRole === 'doctor' ? 'en' : 'es'
//             };

//             websocket.send(JSON.stringify(audioMessage));
//             addDebugLog('info', `📤 Sent audio chunk (${event.data.size} bytes)`);
//           };
//           reader.readAsDataURL(event.data);
//         }
//       };

//       mediaRecorderRef.current.onerror = (event) => {
//         addDebugLog('error', '❌ MediaRecorder error', event);
//       };
      
//       addDebugLog('info', '✅ Audio initialized successfully');
//       return true;
//     } catch (error) {
//       addDebugLog('error', '❌ Audio initialization failed', error);
//       setAudioSupported(false);
//       alert('Could not access microphone. Please check permissions.');
//       return false;
//     }
//   }, [websocket, currentRole, addDebugLog]);

//   // Toggle listening with better error handling
//   const toggleListening = useCallback(async () => {
//     if (!audioSupported) {
//       alert('Audio not supported or not initialized');
//       return;
//     }

//     if (!websocket || websocket.readyState !== WebSocket.OPEN) {
//       addDebugLog('error', '❌ WebSocket not connected for audio');
//       alert('WebSocket not connected. Cannot start audio streaming.');
//       return;
//     }

//     if (!isListening) {
//       addDebugLog('info', '🎤 Starting audio recording...');
      
//       const audioReady = await initializeAudio();
//       if (audioReady && mediaRecorderRef.current) {
//         try {
//           // Send start listening signal
//           websocket.send(JSON.stringify({ type: 'start_listening' }));
          
//           // Start recording with smaller chunks for lower latency
//           mediaRecorderRef.current.start(250); // 250ms chunks for better real-time performance
//           setIsListening(true);
//           addDebugLog('info', '✅ Audio recording started');
//         } catch (error) {
//           addDebugLog('error', '❌ Failed to start recording', error);
//         }
//       }
//     } else {
//       addDebugLog('info', '🎤 Stopping audio recording...');
      
//       // Stop recording
//       if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
//         mediaRecorderRef.current.stop();
//       }
      
//       // Stop audio stream
//       if (streamRef.current) {
//         streamRef.current.getTracks().forEach(track => track.stop());
//         streamRef.current = null;
//       }
      
//       // Send stop signal
//       if (websocket && websocket.readyState === WebSocket.OPEN) {
//         websocket.send(JSON.stringify({ type: 'stop_listening' }));
//       }
      
//       setIsListening(false);
//       setAudioLevel(0);
//       addDebugLog('info', '✅ Audio recording stopped');
//     }
//   }, [isListening, audioSupported, initializeAudio, websocket, addDebugLog]);

//   // Send test message with validation
//   const sendTestMessage = (text: string, language: string) => {
//     if (!websocket || websocket.readyState !== WebSocket.OPEN) {
//       addDebugLog('error', '❌ Cannot send test message - WebSocket not connected');
//       alert('WebSocket not connected!');
//       return;
//     }
    
//     const message = {
//       type: "transcription",
//       text: text,
//       language: language
//     };
    
//     addDebugLog('info', '📤 Sending test message', message);
//     websocket.send(JSON.stringify(message));
//   };

//   // End conversation with cleanup
//   const endConversation = async () => {
//     addDebugLog('info', '📞 Ending conversation...');
    
//     // Stop audio if running
//     if (isListening) {
//       toggleListening();
//     }
    
//     // Close WebSocket
//     if (websocket) {
//       websocket.close(1000, 'User ended conversation');
//     }
    
//     // Clear reconnection timeout
//     if (reconnectTimeoutRef.current) {
//       clearTimeout(reconnectTimeoutRef.current);
//       reconnectTimeoutRef.current = null;
//     }
    
//     // End session on backend
//     if (session) {
//       try {
//         await fetch('http://localhost:8000/conversation/end', {
//           method: 'POST',
//           headers: { 'Content-Type': 'application/json' },
//           body: JSON.stringify({ session_id: session.session_id })
//         });
//         addDebugLog('info', '✅ Session ended on backend');
//       } catch (error) {
//         addDebugLog('error', '❌ Failed to end session on backend', error);
//       }
//     }
    
//     // Reset state
//     setSession(null);
//     setMessages([]);
//     setMedicalAlerts([]);
//     setMedicalContext(null);
//     setConversationActive(false);
//     setIsListening(false);
//     setIsConnected(false);
//     setShowDetailedSummary(false);
//   };

//   // Utility functions for medical context
//   const getActualMedications = (context: any) => {
//     if (!context?.medications_discussed) return [];
    
//     // Filter out non-medications (Spanish words that shouldn't be medications)
//     const nonMedications = ['estoy', 'embarazada', 'tomando', 'tengo', 'dolor', 'cabeza'];
    
//     return context.medications_discussed.filter((med: any) => 
//       med.original_term && 
//       !nonMedications.includes(med.original_term.toLowerCase()) &&
//       med.extraction_confidence > 0.6 // Only show high-confidence extractions
//     );
//   };

//   const getActualMedicationsCount = (context: any) => {
//     return getActualMedications(context).length;
//   };

//   // Utility functions
//   const formatTimestamp = (timestamp: string) => {
//     return new Date(timestamp).toLocaleTimeString([], { 
//       hour: '2-digit', 
//       minute: '2-digit',
//       second: '2-digit'
//     });
//   };

//   const getSpeakerIcon = (speaker: string) => {
//     switch (speaker) {
//       case 'doctor': return <Stethoscope className="text-blue-600" size={16} />;
//       case 'patient': return <User className="text-green-600" size={16} />;
//       default: return <Shield className="text-gray-500" size={16} />;
//     }
//   };

//   const getSpeakerName = (speaker: string) => {
//     switch (speaker) {
//       case 'doctor': return 'Doctor';
//       case 'patient': return 'Patient';
//       default: return 'System';
//     }
//   };

//   const getSeverityColor = (severity: string) => {
//     switch (severity) {
//       case 'urgent':
//       case 'high': 
//         return 'bg-red-100 border-red-500 text-red-800';
//       case 'medium': 
//         return 'bg-yellow-100 border-yellow-500 text-yellow-800';
//       default: 
//         return 'bg-blue-100 border-blue-500 text-blue-800';
//     }
//   };

//   // Render message content with better fallbacks
//   const renderMessageContent = (message: ConversationMessage) => {
//     const content = message.content;
    
//     // Handle different content structures
//     if (typeof content === 'string') {
//       return content;
//     }
    
//     if (content?.text) {
//       return content.text;
//     }
    
//     if (content?.translated_text) {
//       return content.translated_text;
//     }
    
//     if (content?.message) {
//       return content.message;
//     }

//     if (content?.status) {
//       return `Status: ${content.status}`;
//     }
    
//     // Fallback: show formatted JSON
//     try {
//       return JSON.stringify(content, null, 2);
//     } catch {
//       return 'Invalid message content';
//     }
//   };

//   return (
//     <div className="max-w-7xl mx-auto h-screen flex bg-white">
//       {/* Main Conversation Area */}
//       <div className="flex-1 flex flex-col">
//         {/* Header */}
//         <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white p-4">
//           <div className="flex items-center justify-between">
//             <div className="flex items-center space-x-3">
//               <Stethoscope size={24} />
//               <div>
//                 <h2 className="text-xl font-semibold">🎤 Streaming Medical Consultation</h2>
//                 <p className="text-blue-100 text-sm">
//                   {session ? `Session: ${session.session_id.slice(0, 8)}... | OBGYN Specialty` : 'No active session'}
//                 </p>
//               </div>
//             </div>
            
//             <div className="flex items-center space-x-2">
//               {/* Debug Toggle */}
//               <button
//                 onClick={() => setShowDebug(!showDebug)}
//                 className={`px-3 py-1 rounded-lg text-sm flex items-center space-x-1 ${
//                   showDebug ? 'bg-yellow-500' : 'bg-blue-700'
//                 }`}
//               >
//                 <Bug size={12} />
//                 <span>Debug</span>
//               </button>

//               {/* Role Indicator */}
//               <div className="flex items-center space-x-2 bg-blue-700 px-3 py-1 rounded-lg">
//                 {getSpeakerIcon(currentRole)}
//                 <span className="text-sm font-medium">
//                   {currentRole === 'doctor' ? 'Doctor (English)' : 'Patient (Spanish)'}
//                 </span>
//               </div>
              
//               {/* Connection Status */}
//               <div className={`px-3 py-1 rounded-lg text-sm flex items-center space-x-1 ${
//                 isConnected ? 'bg-green-500' : 'bg-red-500'
//               }`}>
//                 <Activity size={12} />
//                 <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
//               </div>
//             </div>
//           </div>
//         </div>

//         {/* Debug Panel */}
//         {showDebug && (
//           <div className="bg-gray-900 text-green-400 p-4 border-b max-h-64 overflow-y-auto font-mono text-xs">
//             <div className="flex justify-between items-center mb-2">
//               <span className="text-green-300 font-bold">Debug Logs ({debugLogs.length})</span>
//               <button
//                 onClick={() => setDebugLogs([])}
//                 className="text-red-400 hover:text-red-300"
//               >
//                 Clear
//               </button>
//             </div>
//             {debugLogs.slice(-20).map((log, index) => (
//               <div key={index} className={`mb-1 ${
//                 log.level === 'error' ? 'text-red-400' : 
//                 log.level === 'warning' ? 'text-yellow-400' : 
//                 'text-green-400'
//               }`}>
//                 <span className="text-gray-500">[{formatTimestamp(log.timestamp)}]</span> {log.message}
//                 {log.data && <div className="ml-4 text-gray-400">{JSON.stringify(log.data, null, 2)}</div>}
//               </div>
//             ))}
//           </div>
//         )}

//         {/* Conversation Messages */}
//         <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
//           {messages.length === 0 && !conversationActive && (
//             <div className="text-center py-12">
//               <MessageSquare className="mx-auto text-gray-400 mb-4" size={48} />
//               <h3 className="text-lg font-medium text-gray-700 mb-2">
//                 Ready for Streaming Medical Consultation
//               </h3>
//               <p className="text-gray-500 mb-4">
//                 Beta: Doctor (English) ↔ Patient (Spanish) with OBGYN Intelligence
//               </p>
//               <div className="text-sm text-gray-400">
//                 Features: Continuous Audio • Real-time Translation • Medical Safety Alerts
//               </div>
//             </div>
//           )}
          
//           {/* Render All Messages */}
//           {messages.map((message) => (
//             <div key={message.id} className="mb-4">
//               {/* Message Bubble */}
//               <div className={`flex ${
//                 message.speaker === 'doctor' ? 'justify-end' : 
//                 message.speaker === 'patient' ? 'justify-start' : 
//                 'justify-center'
//               }`}>
//                 <div className={`max-w-md px-4 py-3 rounded-lg shadow-sm ${
//                   message.speaker === 'doctor' ? 'bg-blue-500 text-white' :
//                   message.speaker === 'patient' ? 'bg-green-500 text-white' :
//                   message.message_type === 'medical_alert' ? getSeverityColor(message.content?.severity || 'medium') :
//                   'bg-gray-200 text-gray-800'
//                 }`}>
//                   {/* Message Header */}
//                   <div className="flex items-center justify-between mb-2">
//                     <div className="flex items-center space-x-2">
//                       {getSpeakerIcon(message.speaker)}
//                       <span className="text-xs font-medium">
//                         {getSpeakerName(message.speaker)}
//                       </span>
//                       <span className="text-xs opacity-75">
//                         {message.message_type}
//                       </span>
//                     </div>
//                     <span className="text-xs opacity-75">
//                       {formatTimestamp(message.timestamp)}
//                     </span>
//                   </div>
                  
//                   {/* Message Content */}
//                   <div className="text-sm">
//                     {message.message_type === 'medical_alert' && (
//                       <div className="flex items-center space-x-2 mb-1">
//                         <AlertTriangle size={16} />
//                         <span className="font-semibold">Medical Alert</span>
//                       </div>
//                     )}
//                     <p className="font-medium whitespace-pre-wrap">{renderMessageContent(message)}</p>
                    
//                     {/* Show confidence if available */}
//                     {message.content?.confidence && (
//                       <div className="text-xs mt-1 opacity-75">
//                         Confidence: {Math.round(message.content.confidence * 100)}%
//                       </div>
//                     )}
                    
//                     {/* Show clinical recommendation if available */}
//                     {message.content?.clinical_recommendation && (
//                       <div className="text-xs mt-2 italic">
//                         <strong>Recommendation:</strong> {message.content.clinical_recommendation}
//                       </div>
//                     )}
//                   </div>
//                 </div>
//               </div>
//             </div>
//           ))}
          
//           <div ref={messagesEndRef} />
//         </div>

//         {/* Controls */}
//         <div className="bg-white border-t p-4">
//           {!conversationActive ? (
//             <div className="flex justify-center space-x-4">
//               <select
//                 value={currentRole}
//                 onChange={(e) => setCurrentRole(e.target.value as 'doctor' | 'patient')}
//                 className="border rounded-lg px-3 py-2 bg-white"
//               >
//                 <option value="doctor">👩‍⚕️ Doctor (English → Spanish)</option>
//                 <option value="patient">👤 Patient (Spanish → English)</option>
//               </select>
              
//               <button
//                 onClick={createSession}
//                 className="bg-green-500 text-white px-6 py-2 rounded-lg hover:bg-green-600 flex items-center space-x-2 shadow-sm"
//               >
//                 <Phone size={16} />
//                 <span>Start Streaming Consultation</span>
//               </button>
//             </div>
//           ) : (
//             <div className="flex justify-between items-center">
//               {/* Audio Controls */}
//               <div className="flex items-center space-x-4">
//                 <button
//                   onClick={toggleListening}
//                   disabled={!isConnected || !audioSupported}
//                   className={`p-3 rounded-full shadow-sm transition-all ${
//                     isListening 
//                       ? 'bg-red-500 text-white animate-pulse' 
//                       : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
//                   } ${!isConnected || !audioSupported ? 'opacity-50 cursor-not-allowed' : ''}`}
//                 >
//                   {isListening ? <Mic size={20} /> : <MicOff size={20} />}
//                 </button>
                
//                 {/* Audio Level */}
//                 {isListening && (
//                   <div className="flex items-center space-x-2">
//                     <Volume2 className="w-4 h-4 text-gray-500" />
//                     <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
//                       <div 
//                         className="h-full bg-green-500 transition-all duration-100"
//                         style={{ width: `${Math.min(audioLevel * 1000, 100)}%` }}
//                       />
//                     </div>
//                     <span className="text-xs text-gray-500">
//                       {audioLevel > 0.01 ? 'Speaking...' : 'Silent'}
//                     </span>
//                   </div>
//                 )}

//                 {!audioSupported && (
//                   <span className="text-xs text-red-500">Audio not supported</span>
//                 )}
//               </div>

//               {/* Test Buttons */}
//               <div className="flex items-center space-x-2">
//                 <span className="text-xs text-gray-500">Quick Tests:</span>
//                 <button
//                   onClick={() => sendTestMessage("Estoy embarazada tomando ibuprofeno", "es")}
//                   className="bg-red-500 text-white px-3 py-2 rounded text-sm hover:bg-red-600"
//                 >
//                   🚨 Combined Test
//                 </button>
//                 <button
//                   onClick={() => sendTestMessage("Estoy embarazada", "es")}
//                   className="bg-purple-500 text-white px-3 py-2 rounded text-sm hover:bg-purple-600"
//                 >
//                   🤰 Pregnant
//                 </button>
//                 <button
//                   onClick={() => sendTestMessage("tomando ibuprofeno", "es")}
//                   className="bg-orange-500 text-white px-3 py-2 rounded text-sm hover:bg-orange-600"
//                 >
//                   💊 Ibuprofen
//                 </button>
//                 <button
//                   onClick={() => sendTestMessage("How are you feeling today?", "en")}
//                   className="bg-blue-500 text-white px-3 py-2 rounded text-sm hover:bg-blue-600"
//                 >
//                   ❓ Check-in
//                 </button>
//               </div>

//               {/* End Call */}
//               <button
//                 onClick={endConversation}
//                 className="bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600 flex items-center space-x-2"
//               >
//                 <PhoneOff size={16} />
//                 <span>End</span>
//               </button>
//             </div>
//           )}
//         </div>
//       </div>

//       {/* Medical Intelligence Sidebar */}
//       <div className="w-80 bg-white border-l flex flex-col">
//         {/* Sidebar Header */}
//         <div className="bg-gray-100 p-4 border-b">
//           <h3 className="font-semibold text-gray-800 flex items-center space-x-2">
//             <Shield size={20} />
//             <span>Live Medical Intelligence</span>
//           </h3>
//           <p className="text-xs text-gray-600 mt-1">OBGYN Specialty • Real-time Analysis</p>
//         </div>

//         {/* Medical Alerts */}
//         {medicalAlerts.length > 0 && (
//           <div className="p-4 border-b">
//             <h4 className="font-medium text-gray-700 mb-3 flex items-center">
//               <AlertTriangle size={16} className="mr-2 text-orange-500" />
//               Active Alerts ({medicalAlerts.length})
//             </h4>
//             <div className="space-y-2 max-h-32 overflow-y-auto">
//               {medicalAlerts.slice(-5).map((alert) => (
//                 <div key={alert.id} className={`p-3 rounded border-l-4 text-sm ${getSeverityColor(alert.severity)}`}>
//                   <div className="font-medium flex items-center justify-between">
//                     <span>{alert.type.replace('_', ' ').toUpperCase()}</span>
//                     <span className="text-xs opacity-75">
//                       {formatTimestamp(alert.timestamp)}
//                     </span>
//                   </div>
//                   <p className="text-xs mt-1">{alert.message}</p>
//                 </div>
//               ))}
//             </div>
//           </div>
//         )}

//         {/* Medical Context Summary */}
//         {medicalContext && (
//           <div className="p-4 border-b">
//             <h4 className="font-medium text-gray-700 mb-3">📋 Session Summary</h4>
            
//             {/* Clean Summary View */}
//             <div className="space-y-2 text-sm">
//               <div className="flex justify-between">
//                 <span className="text-gray-600">Real Medications:</span>
//                 <span className="font-medium">{getActualMedicationsCount(medicalContext)}</span>
//               </div>
//               <div className="flex justify-between">
//                 <span className="text-gray-600">Safety Alerts:</span>
//                 <span className="font-medium text-red-600">{medicalAlerts.length}</span>
//               </div>
//               {medicalContext.last_updated && (
//                 <div className="flex justify-between">
//                   <span className="text-gray-600">Updated:</span>
//                   <span className="text-xs">{formatTimestamp(medicalContext.last_updated)}</span>
//                 </div>
//               )}
//             </div>

//             {/* Show Actual Medications */}
//             {getActualMedications(medicalContext).length > 0 && (
//               <div className="mt-3 p-2 bg-blue-50 rounded">
//                 <div className="text-xs font-medium text-blue-800 mb-1">Medications Detected:</div>
//                 {getActualMedications(medicalContext).map((med, index) => (
//                   <div key={index} className="text-xs text-blue-700">
//                     • {med.original_term} ({med.confidence}% confidence)
//                   </div>
//                 ))}
//               </div>
//             )}

//             {/* Toggle for detailed view */}
//             <button
//               onClick={() => setShowDetailedSummary(!showDetailedSummary)}
//               className="mt-2 text-xs text-gray-500 hover:text-gray-700 underline"
//             >
//               {showDetailedSummary ? 'Hide' : 'Show'} detailed medical analysis
//             </button>

//             {/* Detailed Raw Summary (collapsible) */}
//             {showDetailedSummary && (
//               <div className="mt-3 p-2 bg-gray-50 rounded text-xs max-h-32 overflow-y-auto">
//                 <div className="text-gray-700 font-medium mb-1">Raw Medical Data:</div>
//                 <pre className="text-gray-600 whitespace-pre-wrap">
//                   {JSON.stringify(medicalContext, null, 2)}
//                 </pre>
//               </div>
//             )}
//           </div>
//         )}

//         {/* Debug Info */}
//         <div className="p-4 flex-1">
//           <h4 className="font-medium text-gray-700 mb-3">🔧 Status Info</h4>
//           <div className="space-y-2 text-xs">
//             <div>Messages: {messages.length}</div>
//             <div>Alerts: {medicalAlerts.length}</div>
//             <div>Connected: {isConnected ? '✅' : '❌'}</div>
//             <div>Listening: {isListening ? '🎤' : '🔇'}</div>
//             <div>Audio Level: {audioLevel.toFixed(3)}</div>
//             <div>Audio Support: {audioSupported ? '✅' : '❌'}</div>
//             <div>Session ID: {session?.session_id.slice(0, 8) || 'None'}</div>
//           </div>
//         </div>

//         {/* Status */}
//         <div className="p-4 border-t bg-gray-50 text-center">
//           <div className="text-xs text-gray-600">
//             {isListening ? (
//               <div className="flex items-center justify-center space-x-1 text-green-600">
//                 <Activity size={12} className="animate-pulse" />
//                 <span>Live Audio Processing</span>
//               </div>
//             ) : (
//               <span className="text-gray-500">Ready for conversation</span>
//             )}
//           </div>
//         </div>
//       </div>
//     </div>
//   );
// };

// export default SeamlessConversationInterface;