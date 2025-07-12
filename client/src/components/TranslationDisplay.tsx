import React, { useState } from 'react';
import { ArrowRight, Languages, Volume2, VolumeX, Pause, Play, Settings } from 'lucide-react';
import { useTTS } from '../hooks/useTTS';

interface TranslationDisplayProps {
  originalText: string;
  sessionId: string;
}

export const TranslationDisplay: React.FC<TranslationDisplayProps> = ({ 
  originalText, 
  sessionId 
}) => {
  const [translatedText, setTranslatedText] = useState('');
  const [isTranslating, setIsTranslating] = useState(false);
  const [sourceLanguage, setSourceLanguage] = useState('en');
  const [targetLanguage, setTargetLanguage] = useState('es');
  const [showVoiceSettings, setShowVoiceSettings] = useState(false);
  const [speechRate, setSpeechRate] = useState(0.8);
  const [preferredGender, setPreferredGender] = useState<'male' | 'female'>('female');

  // TTS Hook
  const { 
    isSupported: ttsSupported, 
    isSpeaking, 
    speak, 
    stop, 
    pause, 
    resume, 
    isPaused,
    voices,
    getBestVoice
  } = useTTS();

  const translateText = async () => {
    if (!originalText) return;

    setIsTranslating(true);
    try {
      const response = await fetch('http://127.0.0.1:8000/translate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: originalText,
          source_language: sourceLanguage,
          target_language: targetLanguage,
          medical_context: 'general'
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setTranslatedText(result.translated_text);
    } catch (error) {
      console.error('Error translating text:', error);
      alert('Failed to translate text. Make sure the server is running.');
    } finally {
      setIsTranslating(false);
    }
  };

  const swapLanguages = () => {
    setSourceLanguage(targetLanguage);
    setTargetLanguage(sourceLanguage);
    setTranslatedText(''); // Clear previous translation
  };

  // TTS Functions
  const speakOriginal = () => {
    if (originalText) {
      const voice = getBestVoice(sourceLanguage, preferredGender);
      speak(originalText, sourceLanguage, { 
        rate: speechRate, 
        voice: voice || undefined 
      });
    }
  };

  const speakTranslation = () => {
    if (translatedText) {
      const voice = getBestVoice(targetLanguage, preferredGender);
      speak(translatedText, targetLanguage, { 
        rate: speechRate, 
        voice: voice || undefined 
      });
    }
  };

  const getLanguageName = (code: string) => {
    const names: Record<string, string> = {
      'en': 'English',
      'es': 'Spanish',
      'fr': 'French',
      'pt': 'Portuguese',
      'auto': 'Auto-detect'
    };
    return names[code] || code;
  };

  const getAvailableVoices = (language: string) => {
    return voices.filter(voice => voice.lang.startsWith(language));
  };

  return (
    <div className="w-full max-w-4xl mx-auto space-y-4">
      {/* Language Controls */}
      <div className="flex items-center justify-center space-x-4 p-4 bg-gray-50 rounded-lg">
        <select 
          value={sourceLanguage}
          onChange={(e) => setSourceLanguage(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
        >
          <option value="en">English</option>
          <option value="es">Spanish</option>
          <option value="auto">Auto-detect</option>
        </select>

        <button
          onClick={swapLanguages}
          className="p-2 text-gray-500 hover:text-gray-700 transition-colors"
          title="Swap languages"
        >
          <ArrowRight className="rotate-0 hover:rotate-180 transition-transform duration-300" size={20} />
        </button>

        <select 
          value={targetLanguage}
          onChange={(e) => setTargetLanguage(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
        >
          <option value="es">Spanish</option>
          <option value="en">English</option>
          <option value="fr">French</option>
          <option value="pt">Portuguese</option>
        </select>

        <button
          onClick={translateText}
          disabled={!originalText || isTranslating}
          className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
        >
          <Languages size={16} />
          <span>{isTranslating ? 'Translating...' : 'Translate'}</span>
        </button>

        {/* Voice Settings Toggle */}
        {ttsSupported && (
          <button
            onClick={() => setShowVoiceSettings(!showVoiceSettings)}
            className="p-2 text-gray-500 hover:text-gray-700 transition-colors"
            title="Voice settings"
          >
            <Settings size={20} />
          </button>
        )}
      </div>

      {/* Voice Settings Panel */}
      {showVoiceSettings && ttsSupported && (
        <div className="p-4 bg-blue-50 rounded-lg space-y-3">
          <h4 className="font-medium text-gray-800">Voice Settings</h4>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Speech Rate */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Speech Rate: {speechRate}x
              </label>
              <input
                type="range"
                min="0.5"
                max="2"
                step="0.1"
                value={speechRate}
                onChange={(e) => setSpeechRate(parseFloat(e.target.value))}
                className="w-full"
              />
            </div>

            {/* Preferred Gender */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Preferred Voice
              </label>
              <select
                value={preferredGender}
                onChange={(e) => setPreferredGender(e.target.value as 'male' | 'female')}
                className="w-full px-3 py-1 border border-gray-300 rounded-md"
              >
                <option value="female">Female</option>
                <option value="male">Male</option>
              </select>
            </div>
          </div>

          {/* Available Voices Info */}
          <div className="text-xs text-gray-600">
            <p>Available voices:</p>
            <p>• {getLanguageName(sourceLanguage)}: {getAvailableVoices(sourceLanguage).length} voices</p>
            <p>• {getLanguageName(targetLanguage)}: {getAvailableVoices(targetLanguage).length} voices</p>
          </div>
        </div>
      )}

      {/* Text Display with TTS Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Original Text */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-gray-700 uppercase text-sm tracking-wide">
              Original ({getLanguageName(sourceLanguage)})
            </h3>
            
            {/* TTS Controls for Original */}
            {ttsSupported && originalText && (
              <div className="flex items-center space-x-1">
                {isSpeaking ? (
                  <>
                    {isPaused ? (
                      <button
                        onClick={resume}
                        className="p-1 text-green-600 hover:text-green-700 transition-colors"
                        title="Resume"
                      >
                        <Play size={16} />
                      </button>
                    ) : (
                      <button
                        onClick={pause}
                        className="p-1 text-yellow-600 hover:text-yellow-700 transition-colors"
                        title="Pause"
                      >
                        <Pause size={16} />
                      </button>
                    )}
                    <button
                      onClick={stop}
                      className="p-1 text-red-600 hover:text-red-700 transition-colors"
                      title="Stop"
                    >
                      <VolumeX size={16} />
                    </button>
                  </>
                ) : (
                  <button
                    onClick={speakOriginal}
                    className="p-1 text-blue-600 hover:text-blue-700 transition-colors"
                    title="Speak original text"
                  >
                    <Volume2 size={16} />
                  </button>
                )}
              </div>
            )}
          </div>
          
          <div className="p-4 bg-white border border-gray-200 rounded-lg min-h-24">
            {originalText ? (
              <p className="text-gray-800 leading-relaxed">{originalText}</p>
            ) : (
              <p className="text-gray-400 italic">Record audio to see transcription here...</p>
            )}
          </div>
        </div>

        {/* Translated Text */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-gray-700 uppercase text-sm tracking-wide">
              Translation ({getLanguageName(targetLanguage)})
            </h3>
            
            {/* TTS Controls for Translation */}
            {ttsSupported && translatedText && (
              <div className="flex items-center space-x-1">
                {isSpeaking ? (
                  <>
                    {isPaused ? (
                      <button
                        onClick={resume}
                        className="p-1 text-green-600 hover:text-green-700 transition-colors"
                        title="Resume"
                      >
                        <Play size={16} />
                      </button>
                    ) : (
                      <button
                        onClick={pause}
                        className="p-1 text-yellow-600 hover:text-yellow-700 transition-colors"
                        title="Pause"
                      >
                        <Pause size={16} />
                      </button>
                    )}
                    <button
                      onClick={stop}
                      className="p-1 text-red-600 hover:text-red-700 transition-colors"
                      title="Stop"
                    >
                      <VolumeX size={16} />
                    </button>
                  </>
                ) : (
                  <button
                    onClick={speakTranslation}
                    className="p-1 text-blue-600 hover:text-blue-700 transition-colors"
                    title="Speak translation"
                  >
                    <Volume2 size={16} />
                  </button>
                )}
              </div>
            )}
          </div>
          
          <div className="p-4 bg-white border border-gray-200 rounded-lg min-h-24">
            {isTranslating ? (
              <p className="text-gray-400 italic animate-pulse">Translating...</p>
            ) : translatedText ? (
              <p className="text-gray-800 leading-relaxed">{translatedText}</p>
            ) : (
              <p className="text-gray-400 italic">Translation will appear here...</p>
            )}
          </div>
        </div>
      </div>

      {/* TTS Support Warning */}
      {!ttsSupported && (
        <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-yellow-800 text-sm">
            ⚠️ Text-to-speech is not supported in this browser. For best experience, use Chrome, Safari, or Edge.
          </p>
        </div>
      )}

      {/* Session Info */}
      {sessionId && (
        <div className="text-xs text-gray-500 text-center">
          Session: {sessionId}
        </div>
      )}
    </div>
  );
};