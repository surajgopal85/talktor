// src/pages/TranslatorPage.tsx
import React, { useState } from 'react';
import { AudioRecorder } from '../components/AudioRecorder';
import { MedicalTranslationDisplay } from '../components/MedicalTranslationDisplay';
import { useMedicalContext } from '../context/MedicalAppContext';

export const TranslatorPage: React.FC = () => {
  const { state, dispatch } = useMedicalContext();
  const [transcribedText, setTranscribedText] = useState('');
  const [currentSessionId, setCurrentSessionId] = useState('');

  const handleTranscription = (text: string, sessionId: string) => {
    setTranscribedText(text);
    setCurrentSessionId(sessionId);
  };

  const clearSession = () => {
    setTranscribedText('');
    setCurrentSessionId('');
    dispatch({ type: 'CLEAR_SESSION' });
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Medical Translator</h1>
          <p className="text-gray-600">
            AI-powered medical interpreter with specialty-aware intelligence
          </p>
        </div>

        {/* Audio Recorder */}
        <div className="bg-white rounded-xl shadow-lg p-8">
          <h2 className="text-2xl font-semibold text-gray-800 text-center mb-6">
            Voice Recording
          </h2>
          <AudioRecorder onTranscription={handleTranscription} />
        </div>

        {/* Medical Translation Display */}
        <div className="bg-white rounded-xl shadow-lg p-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-semibold text-gray-800">
              Enhanced Medical Translation
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
          <MedicalTranslationDisplay
            originalText={transcribedText}
            sessionId={currentSessionId}
          />
        </div>
      </div>
    </div>
  );
};