// src/components/ErrorTrackingChatInterface.tsx
import React, { useState, useRef, useEffect } from 'react';
import { Mic, MicOff, Volume2, AlertTriangle, CheckCircle, RotateCcw, MessageSquare, FileText, UserCheck, Bug, Database, Wifi } from 'lucide-react';

interface MedicalIntelligenceData {
  backendResponse: any;
  frontendParsed: any;
  discrepancies: string[];
}

interface Message {
  id: string;
  speaker: 'doctor' | 'patient';
  originalText: string;
  translatedText: string;
  timestamp: Date;
  medicalIntelligence: MedicalIntelligenceData;
  errorReported?: boolean;
  errorType?: string;
  errorDescription?: string;
}

interface ErrorLog {
  timestamp: Date;
  messageId: string;
  errorType: string;
  expectedBehavior: string;
  actualBehavior: string;
  backendResponse: any;
  resolved: boolean;
}

export const ErrorTrackingChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentSpeaker, setCurrentSpeaker] = useState<'doctor' | 'patient'>('doctor');
  const [isRecording, setIsRecording] = useState(false);
  const [isTranslating, setIsTranslating] = useState(false);
  const [sessionId, setSessionId] = useState('');
  const [errorLogs, setErrorLogs] = useState<ErrorLog[]>([]);
  const [showInvestigation, setShowInvestigation] = useState(false);
  const [debugMode, setDebugMode] = useState(true);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setSessionId(`debug_session_${Date.now()}`);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const analyzeDiscrepancies = (backendResponse: any, frontendParsed: any): string[] => {
    const issues: string[] = [];
    
    // Check OBGYN detection
    if (backendResponse.medical_notes?.some((note: any) => note.type === 'pregnancy_context')) {
      if (!frontendParsed.detectedSpecialty || frontendParsed.detectedSpecialty === 'General') {
        issues.push('🚨 OBGYN specialty detection failed in frontend parsing');
      }
    }
    
    // Check safety alerts
    const urgentAlerts = backendResponse.medical_notes?.filter((note: any) => 
      note.importance === 'urgent' || note.importance === 'critical'
    );
    if (urgentAlerts?.length > 0 && (!frontendParsed.safetyAlerts || frontendParsed.safetyAlerts.length === 0)) {
      issues.push('🚨 CRITICAL: Safety alerts not parsed from backend response');
    }
    
    // Check accuracy score
    if (backendResponse.confidence > 0.8 && (!frontendParsed.medicalAccuracy || frontendParsed.medicalAccuracy < 0.1)) {
      issues.push('⚠️ Medical accuracy score mismatch (backend confident, frontend low)');
    }
    
    return issues;
  };

  const addMessage = async (originalText: string, speaker: 'doctor' | 'patient') => {
    setIsTranslating(true);
    
    let backendResponse: any = null;
    let frontendParsed: any = {};
    
    try {
      console.log('🔍 Calling backend with:', { originalText, speaker });
      
      const response = await fetch('http://127.0.0.1:8000/translate/medical', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: originalText,
          source_language: speaker === 'doctor' ? 'en' : 'es',
          target_language: speaker === 'doctor' ? 'es' : 'en',
          session_id: sessionId,
          speaker_role: speaker
        }),
      });

      if (!response.ok) {
        throw new Error(`Translation failed: ${response.status}`);
      }

      backendResponse = await response.json();
      console.log('✅ Backend response:', backendResponse);
      
      // Parse response (your current logic)
      const translatedText = backendResponse.enhanced_translation || backendResponse.standard_translation;
      const medicalNotes = backendResponse.medical_notes || [];
      const followUpQuestions = backendResponse.follow_up_questions || [];
      const medicalAccuracy = backendResponse.medical_accuracy_score || backendResponse.confidence || 0;
      const confidence = backendResponse.confidence || 0;
      
      // Detect specialty
      let detectedSpecialty = 'General';
      const pregnancyNote = medicalNotes.find((note: any) => note.type === 'pregnancy_context');
      if (pregnancyNote) {
        detectedSpecialty = 'OBGYN';
      }
      
      // Extract safety alerts
      const safetyAlerts = medicalNotes.filter((note: any) => 
        note.importance === 'urgent' || note.importance === 'critical' || note.type === 'safety_alert'
      );
      
      frontendParsed = {
        translatedText,
        medicalNotes,
        followUpQuestions,
        medicalAccuracy,
        confidence,
        detectedSpecialty,
        safetyAlerts
      };
      
      console.log('🔧 Frontend parsed:', frontendParsed);
      
      // Analyze discrepancies
      const discrepancies = analyzeDiscrepancies(backendResponse, frontendParsed);
      console.log('⚠️ Discrepancies found:', discrepancies);

      const newMessage: Message = {
        id: `msg_${Date.now()}`,
        speaker,
        originalText,
        translatedText,
        timestamp: new Date(),
        medicalIntelligence: {
          backendResponse,
          frontendParsed,
          discrepancies
        }
      };

      // Log errors if found
      if (discrepancies.length > 0) {
        const errorLog: ErrorLog = {
          timestamp: new Date(),
          messageId: newMessage.id,
          errorType: 'medical_intelligence_discrepancy',
          expectedBehavior: 'Medical intelligence should be fully parsed and displayed',
          actualBehavior: discrepancies.join('; '),
          backendResponse,
          resolved: false
        };
        
        setErrorLogs(prev => [...prev, errorLog]);
      }

      setMessages(prev => [...prev, newMessage]);

    } catch (error) {
      console.error('💥 Translation error:', error);
    } finally {
      setIsTranslating(false);
    }
  };

  const runTestScenario = (scenario: string) => {
    const testCases = {
      'pregnancy_ibuprofen': 'I am pregnant and taking ibuprofen for headaches',
      'contractions': 'You are having contractions every 5 minutes, go to hospital now', 
      'medication_list': 'I take lisinopril and metformin daily',
      'spanish_pregnancy': 'Estoy embarazada de 12 semanas tomando ácido fólico'
    };
    
    const text = testCases[scenario as keyof typeof testCases];
    if (text) {
      addMessage(text, scenario.includes('spanish') ? 'patient' : 'doctor');
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Debug Header */}
      {debugMode && (
        <div className="bg-yellow-50 border-b border-yellow-200 p-2 text-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <span className="font-medium">🔍 Debug Mode Active</span>
              <span>Session: {sessionId.slice(-8)}</span>
              <span>Errors: {errorLogs.filter(e => !e.resolved).length}</span>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setShowInvestigation(!showInvestigation)}
                className="px-2 py-1 bg-yellow-200 text-yellow-800 rounded text-xs"
              >
                Investigation
              </button>
              <select 
                onChange={(e) => runTestScenario(e.target.value)}
                className="text-xs border rounded px-2 py-1"
                defaultValue=""
              >
                <option value="">Quick Tests</option>
                <option value="pregnancy_ibuprofen">🚨 Pregnancy + Ibuprofen</option>
                <option value="contractions">⚡ Emergency Contractions</option>
                <option value="medication_list">💊 Medication List</option>
                <option value="spanish_pregnancy">🇪🇸 Spanish Pregnancy</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div key={message.id} className={`flex ${message.speaker === 'doctor' ? 'justify-start' : 'justify-end'}`}>
            <div className={`max-w-lg px-4 py-3 rounded-lg space-y-3 ${
              message.speaker === 'doctor' 
                ? 'bg-blue-100 text-blue-900' 
                : 'bg-green-100 text-green-900'
            }`}>
              {/* Speaker & Text */}
              <div>
                <div className="text-xs font-semibold uppercase tracking-wide opacity-70 mb-1">
                  {message.speaker === 'doctor' ? 'Doctor (EN)' : 'Patient (ES)'}
                </div>
                <div className="font-medium">{message.originalText}</div>
                <div className="text-sm opacity-80 mt-1 pt-1 border-t">
                  <span className="text-xs uppercase tracking-wide">Translation: </span>
                  {message.translatedText}
                </div>
              </div>

              {/* Medical Intelligence Status */}
              {message.medicalIntelligence && (
                <div className="space-y-2">
                  {/* Backend Status */}
                  <div className="flex items-center justify-between text-xs">
                    <span>Backend: {message.medicalIntelligence.backendResponse?.confidence || 0} confidence</span>
                    <span>Issues: {message.medicalIntelligence.discrepancies.length}</span>
                  </div>

                  {/* Safety Alerts */}
                  {message.medicalIntelligence.frontendParsed.safetyAlerts?.length > 0 && (
                    <div className="bg-red-50 border border-red-200 rounded p-2">
                      <div className="text-xs font-semibold text-red-700 mb-1">🚨 SAFETY ALERT</div>
                      {message.medicalIntelligence.frontendParsed.safetyAlerts.map((alert: any, idx: number) => (
                        <div key={idx} className="text-xs text-red-600">{alert.message}</div>
                      ))}
                    </div>
                  )}

                  {/* Medical Context */}
                  {message.medicalIntelligence.frontendParsed.detectedSpecialty !== 'General' && (
                    <div className="bg-blue-50 border border-blue-200 rounded p-2">
                      <div className="text-xs font-semibold text-blue-700">
                        🏥 {message.medicalIntelligence.frontendParsed.detectedSpecialty} Context Detected
                      </div>
                    </div>
                  )}

                  {/* Discrepancy Warnings */}
                  {message.medicalIntelligence.discrepancies.length > 0 && (
                    <div className="bg-orange-50 border border-orange-200 rounded p-2">
                      <div className="text-xs font-semibold text-orange-700 mb-1">⚠️ Issues Detected:</div>
                      {message.medicalIntelligence.discrepancies.map((issue, idx) => (
                        <div key={idx} className="text-xs text-orange-600">{issue}</div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
        
        {isTranslating && (
          <div className="flex justify-center">
            <div className="bg-gray-200 px-4 py-2 rounded-lg text-sm text-gray-600 animate-pulse">
              Analyzing medical context...
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="bg-white border-t p-4">
        {/* Speaker Toggle */}
        <div className="flex justify-center mb-4">
          <div className="flex bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setCurrentSpeaker('doctor')}
              className={`px-6 py-2 rounded-md text-sm font-medium transition-colors ${
                currentSpeaker === 'doctor' 
                  ? 'bg-blue-600 text-white' 
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Doctor Speaking
            </button>
            <button
              onClick={() => setCurrentSpeaker('patient')}
              className={`px-6 py-2 rounded-md text-sm font-medium transition-colors ${
                currentSpeaker === 'patient' 
                  ? 'bg-green-600 text-white' 
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Patient Speaking
            </button>
          </div>
        </div>

        {/* Recording Button */}
        <div className="flex justify-center">
          <button
            onClick={() => {
              if (isRecording) {
                setIsRecording(false);
                addMessage("I am pregnant and taking ibuprofen for headaches", currentSpeaker);
              } else {
                setIsRecording(true);
              }
            }}
            disabled={isTranslating}
            className={`w-16 h-16 rounded-full flex items-center justify-center text-white text-xl transition-all duration-200 ${
              isRecording 
                ? 'bg-red-500 hover:bg-red-600 animate-pulse' 
                : 'bg-blue-500 hover:bg-blue-600 hover:scale-105'
            } ${isTranslating ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            {isRecording ? <MicOff size={24} /> : <Mic size={24} />}
          </button>
        </div>
        
        <div className="text-center mt-2 text-sm text-gray-600">
          {isRecording ? (
            <span className="text-red-600 font-medium">Recording {currentSpeaker}... Tap to stop</span>
          ) : (
            <span>Tap to record {currentSpeaker}'s message (test mode)</span>
          )}
        </div>
      </div>

      {/* Investigation Panel */}
      {showInvestigation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 max-h-96 overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">🔍 Error Investigation Dashboard</h3>
              <button
                onClick={() => setShowInvestigation(false)}
                className="text-gray-500 hover:text-gray-700 text-xl"
              >
                ×
              </button>
            </div>
            
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-red-50 p-3 rounded">
                  <div className="text-red-800 font-medium">Critical Issues</div>
                  <div className="text-2xl font-bold text-red-600">
                    {errorLogs.filter(e => e.errorType.includes('safety') || e.errorType.includes('critical')).length}
                  </div>
                </div>
                <div className="bg-yellow-50 p-3 rounded">
                  <div className="text-yellow-800 font-medium">Parsing Issues</div>
                  <div className="text-2xl font-bold text-yellow-600">
                    {errorLogs.filter(e => e.errorType.includes('discrepancy')).length}
                  </div>
                </div>
                <div className="bg-blue-50 p-3 rounded">
                  <div className="text-blue-800 font-medium">Total Logs</div>
                  <div className="text-2xl font-bold text-blue-600">{errorLogs.length}</div>
                </div>
              </div>
              
              <div>
                <h4 className="font-medium text-gray-800 mb-2">Recent Error Logs</h4>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {errorLogs.slice(-10).reverse().map((log, idx) => (
                    <div key={idx} className="text-sm p-3 bg-gray-50 rounded border">
                      <div className="flex justify-between items-start mb-1">
                        <span className="font-medium text-red-600">{log.errorType}</span>
                        <span className="text-gray-500 text-xs">{log.timestamp.toLocaleTimeString()}</span>
                      </div>
                      <div className="text-gray-700">{log.actualBehavior}</div>
                      {log.backendResponse && (
                        <details className="mt-2">
                          <summary className="cursor-pointer text-blue-600 text-xs">Backend Response</summary>
                          <pre className="text-xs bg-gray-100 p-2 rounded mt-1 overflow-x-auto">
                            {JSON.stringify(log.backendResponse, null, 2)}
                          </pre>
                        </details>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};