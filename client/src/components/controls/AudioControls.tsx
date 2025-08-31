import React from 'react';
import { Mic, MicOff, Volume2, Phone, PhoneOff } from 'lucide-react';

interface AudioControlsProps {
  isListening: boolean;
  conversationActive: boolean;
  audioSupported: boolean;
  onStartListening: () => void;
  onStopListening: () => void;
  onStartConversation: () => void;
  onEndConversation: () => void;
  onInitializeAudio: () => void;
}

const AudioControls: React.FC<AudioControlsProps> = ({
  isListening,
  conversationActive,
  audioSupported,
  onStartListening,
  onStopListening,
  onStartConversation,
  onEndConversation,
  onInitializeAudio
}) => {
  return (
    <div className="bg-white shadow-sm border-b border-gray-200 p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          {/* Audio Status */}
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${
              audioSupported ? 'bg-green-500' : 'bg-red-500'
            }`} />
            <span className="text-sm text-gray-600">
              {audioSupported ? 'Audio Ready' : 'Audio Not Supported'}
            </span>
          </div>

          {/* Microphone Controls */}
          <div className="flex items-center space-x-2">
            <button
              onClick={isListening ? onStopListening : onStartListening}
              disabled={!audioSupported || !conversationActive}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                isListening
                  ? 'bg-red-500 text-white hover:bg-red-600'
                  : 'bg-blue-500 text-white hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed'
              }`}
            >
              {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
              <span>{isListening ? 'Stop Listening' : 'Start Listening'}</span>
            </button>
          </div>

          {/* Conversation Controls */}
          <div className="flex items-center space-x-2">
            <button
              onClick={conversationActive ? onEndConversation : onStartConversation}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                conversationActive
                  ? 'bg-red-500 text-white hover:bg-red-600'
                  : 'bg-green-500 text-white hover:bg-green-600'
              }`}
            >
              {conversationActive ? <PhoneOff className="w-4 h-4" /> : <Phone className="w-4 h-4" />}
              <span>{conversationActive ? 'End Conversation' : 'Start Conversation'}</span>
            </button>
          </div>
        </div>

        {/* Audio Initialization */}
        {!audioSupported && (
          <button
            onClick={onInitializeAudio}
            className="flex items-center space-x-2 px-3 py-2 bg-yellow-500 text-white rounded-lg text-sm hover:bg-yellow-600"
          >
            <Volume2 className="w-4 h-4" />
            <span>Initialize Audio</span>
          </button>
        )}
      </div>
    </div>
  );
};

export default AudioControls;
