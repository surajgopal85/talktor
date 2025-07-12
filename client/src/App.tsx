import React, { useState } from 'react';
import { AudioRecorder } from './components/AudioRecorder';
import { TranslationDisplay } from './components/TranslationDisplay';
import { Stethoscope } from 'lucide-react';

function App() {
  const [transcribedText, setTranscribedText] = useState('');
  const [currentSessionId, setCurrentSessionId] = useState('');

  const handleTranscription = (text: string, sessionId: string) => {
    setTranscribedText(text);
    setCurrentSessionId(sessionId);
  };

  const clearSession = () => {
    setTranscribedText('');
    setCurrentSessionId('');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center space-x-3 mb-4">
            <Stethoscope className="text-blue-600" size={48} />
            <h1 className="text-4xl font-bold text-gray-800">talktor</h1>
          </div>
          <p className="text-gray-600 max-w-2xl mx-auto">
            AI-powered medical interpreter for seamless communication between healthcare providers and patients.
            Record, transcribe, and translate medical conversations instantly.
          </p>
        </div>

        {/* Main Content */}
        <div className="space-y-8">
          {/* Audio Recorder */}
          <div className="bg-white rounded-xl shadow-lg p-8">
            <h2 className="text-2xl font-semibold text-gray-800 text-center mb-6">
              Voice Recording
            </h2>
            <AudioRecorder onTranscription={handleTranscription} />
          </div>

          {/* Translation Display */}
          <div className="bg-white rounded-xl shadow-lg p-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-semibold text-gray-800">
                Translation
              </h2>
              {currentSessionId && (
                <button
                  onClick={clearSession}
                  className="px-4 py-2 text-sm bg-gray-100 text-gray-600 rounded-md hover:bg-gray-200 transition-colors"
                >
                  Clear Session
                </button>
              )}
            </div>
            <TranslationDisplay 
              originalText={transcribedText}
              sessionId={currentSessionId}
            />
          </div>
        </div>

        {/* Footer */}
        <div className="text-center mt-12 text-gray-500 text-sm">
          <p>Built for medical professionals • HIPAA compliance ready • Secure conversations</p>
        </div>
      </div>
    </div>
  );
}

export default App;