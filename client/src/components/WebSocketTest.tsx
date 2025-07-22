// components/WebSocketTest.tsx - React WebSocket Test Component
import React, { useState, useEffect, useRef } from 'react';

interface ConversationSession {
  session_id: string;
  doctor_language: string;
  patient_language: string;
  websocket_urls: {
    doctor: string;
    patient: string;
  };
  status: string;
}

interface LogMessage {
  timestamp: string;
  message: string;
  type: 'info' | 'success' | 'error' | 'sent' | 'received';
}

export const WebSocketTest: React.FC = () => {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [websocket, setWebsocket] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [currentRole, setCurrentRole] = useState<'doctor' | 'patient'>('doctor');
  const [logs, setLogs] = useState<LogMessage[]>([]);
  const [testMessage, setTestMessage] = useState(JSON.stringify({
    type: "transcription", 
    text: "Estoy embarazada tomando vitaminas prenatales", 
    language: "es"
  }, null, 2));

  const logRef = useRef<HTMLDivElement>(null);

  const addLog = (message: string, type: LogMessage['type'] = 'info') => {
    const newLog: LogMessage = {
      timestamp: new Date().toLocaleTimeString(),
      message,
      type
    };
    
    setLogs(prev => [...prev, newLog]);
  };

  useEffect(() => {
    // Auto-scroll logs
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [logs]);

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

      const data: ConversationSession = await response.json();
      setSessionId(data.session_id);
      addLog(`✅ Session created: ${data.session_id}`, 'success');
      
    } catch (error) {
      addLog(`❌ Error creating session: ${error}`, 'error');
    }
  };

  const connectWebSocket = () => {
    if (!sessionId) {
      alert('Create a session first!');
      return;
    }

    const wsUrl = `ws://localhost:8000/conversation/ws/${sessionId}/${currentRole}`;

    try {
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        addLog(`✅ WebSocket connected as ${currentRole}`, 'success');
        setIsConnected(true);
        setWebsocket(ws);
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        addLog(`📨 Received: ${JSON.stringify(data, null, 2)}`, 'received');
      };

      ws.onclose = (event) => {
        addLog(`🔌 WebSocket closed: ${event.reason}`, 'info');
        setIsConnected(false);
        setWebsocket(null);
      };

      ws.onerror = (error) => {
        addLog(`❌ WebSocket error: ${error}`, 'error');
      };

    } catch (error) {
      addLog(`Connection error: ${error}`, 'error');
    }
  };

  const disconnectWebSocket = () => {
    if (websocket) {
      websocket.close();
      setWebsocket(null);
      setIsConnected(false);
    }
  };

  const sendTestMessage = () => {
    if (!websocket) {
      alert('Connect WebSocket first!');
      return;
    }

    try {
      const message = JSON.parse(testMessage);
      websocket.send(JSON.stringify(message));
      addLog(`📤 Sent: ${testMessage}`, 'sent');
    } catch (error) {
      addLog(`Send error: ${error}`, 'error');
    }
  };

  const sendAudioTest = () => {
    if (!websocket) {
      alert('Connect WebSocket first!');
      return;
    }

    const audioMessage = {
      type: "audio_chunk",
      audio_data: "dGVzdCBhdWRpbyBkYXRh", // base64 for "test audio data"
      language: currentRole === 'doctor' ? 'en' : 'es'
    };

    websocket.send(JSON.stringify(audioMessage));
    addLog(`🎤 Sent audio test: ${JSON.stringify(audioMessage)}`, 'sent');
  };

  const testSpanishMedical = () => {
    const spanishTests = [
      {
        type: "transcription",  // Changed from "audio_chunk"
        text: "Estoy embarazada",
        language: "es"
      },
      {
        type: "transcription",  // Changed from "audio_chunk"
        text: "tomando ibuprofeno", 
        language: "es"
      }
    ];
  
    spanishTests.forEach((test, i) => {
      setTimeout(() => {
        if (websocket) {
          websocket.send(JSON.stringify(test));
          addLog(`🇪🇸 Spanish medical test ${i + 1}: ${test.text}`, 'sent');
        }
      }, i * 2000);
    });
  };

  const clearLogs = () => {
    setLogs([]);
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">🚀 Talktor WebSocket Test</h1>

      {/* Session Management */}
      <div className="bg-white p-4 rounded-lg shadow mb-6">
        <h3 className="text-lg font-semibold mb-3">Step 1: Create Session</h3>
        <button
          onClick={createSession}
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
        >
          Create Conversation Session
        </button>
        {sessionId && (
          <div className="mt-3 p-3 bg-green-100 rounded">
            <strong>✅ Session ID:</strong> {sessionId}
          </div>
        )}
      </div>

      {/* WebSocket Connection */}
      <div className="bg-white p-4 rounded-lg shadow mb-6">
        <h3 className="text-lg font-semibold mb-3">Step 2: Connect WebSocket</h3>
        <div className="flex items-center gap-4 mb-3">
          <label>
            Role:
            <select
              value={currentRole}
              onChange={(e) => setCurrentRole(e.target.value as 'doctor' | 'patient')}
              className="ml-2 border rounded px-2 py-1"
            >
              <option value="doctor">Doctor</option>
              <option value="patient">Patient</option>
            </select>
          </label>
          <button
            onClick={connectWebSocket}
            disabled={isConnected}
            className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 disabled:opacity-50"
          >
            Connect WebSocket
          </button>
          <button
            onClick={disconnectWebSocket}
            disabled={!isConnected}
            className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600 disabled:opacity-50"
          >
            Disconnect
          </button>
        </div>
        {isConnected && (
          <div className="p-3 bg-green-100 rounded">
            ✅ Connected as {currentRole}
          </div>
        )}
      </div>

      {/* Test Messages */}
      <div className="bg-white p-4 rounded-lg shadow mb-6">
        <h3 className="text-lg font-semibold mb-3">Step 3: Test Messages</h3>
        <textarea
          value={testMessage}
          onChange={(e) => setTestMessage(e.target.value)}
          className="w-full h-32 border rounded p-2 font-mono text-sm mb-3"
          placeholder="JSON message to send"
        />
        <div className="flex gap-2">
          <button
            onClick={sendTestMessage}
            disabled={!isConnected}
            className="bg-purple-500 text-white px-4 py-2 rounded hover:bg-purple-600 disabled:opacity-50"
          >
            Send Test Message
          </button>
          <button
            onClick={sendAudioTest}
            disabled={!isConnected}
            className="bg-orange-500 text-white px-4 py-2 rounded hover:bg-orange-600 disabled:opacity-50"
          >
            Send Audio Test
          </button>
          <button
            onClick={testSpanishMedical}
            disabled={!isConnected}
            className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600 disabled:opacity-50"
          >
            🇪🇸 Test Spanish Medical
          </button>
        </div>
      </div>

      {/* Message Log */}
      <div className="bg-white p-4 rounded-lg shadow">
        <div className="flex justify-between items-center mb-3">
          <h3 className="text-lg font-semibold">Message Log</h3>
          <button
            onClick={clearLogs}
            className="bg-gray-500 text-white px-3 py-1 rounded text-sm hover:bg-gray-600"
          >
            Clear Log
          </button>
        </div>
        <div
          ref={logRef}
          className="h-80 overflow-y-auto bg-gray-50 p-3 rounded font-mono text-sm"
        >
          {logs.map((log, i) => (
            <div
              key={i}
              className={`mb-2 p-2 rounded ${
                log.type === 'success' ? 'bg-green-100 text-green-800' :
                log.type === 'error' ? 'bg-red-100 text-red-800' :
                log.type === 'sent' ? 'bg-blue-100 text-blue-800' :
                log.type === 'received' ? 'bg-purple-100 text-purple-800' :
                'bg-gray-100 text-gray-800'
              }`}
            >
              <strong>[{log.timestamp}]</strong> {log.message}
            </div>
          ))}
          {logs.length === 0 && (
            <div className="text-gray-500 text-center">No logs yet...</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default WebSocketTest;