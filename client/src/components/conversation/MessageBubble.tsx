import React from 'react';
import { User, Shield, Stethoscope } from 'lucide-react';

interface ConversationMessage {
  id: string;
  speaker: 'doctor' | 'patient' | 'system';
  message_type: string;
  content: any;
  timestamp: string;
  language: string;
}

interface MessageBubbleProps {
  message: ConversationMessage;
  showConfidenceScores: boolean;
  showDebugInfo: boolean;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  showConfidenceScores,
  showDebugInfo
}) => {
  const getSpeakerIcon = (speaker: string) => {
    switch (speaker) {
      case 'doctor':
        return <Stethoscope className="w-4 h-4 text-blue-600" />;
      case 'patient':
        return <User className="w-4 h-4 text-green-600" />;
      case 'system':
        return <Shield className="w-4 h-4 text-purple-600" />;
      default:
        return <User className="w-4 h-4 text-gray-600" />;
    }
  };

  const getSpeakerName = (speaker: string) => {
    switch (speaker) {
      case 'doctor':
        return 'Dr. Smith';
      case 'patient':
        return 'Patient';
      case 'system':
        return 'Medical AI';
      default:
        return 'Unknown';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const renderMessageContent = (message: ConversationMessage) => {
    if (message.message_type === 'translation') {
      return (
        <div className="text-sm font-medium">
          {message.content.translated_text}
        </div>
      );
    }

    if (message.message_type === 'transcription') {
      return (
        <div className="text-sm opacity-60">
          {message.content.text}
        </div>
      );
    }

    if (message.message_type === 'error') {
      return (
        <div className="text-red-700">
          <div className="font-medium">Error:</div>
          <div className="text-sm">{message.content.text}</div>
        </div>
      );
    }

    // Default text message
    return (
      <div className="text-sm">
        {message.content.text || JSON.stringify(message.content)}
      </div>
    );
  };

  return (
    <div className={`flex ${
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
            {showDebugInfo && (
              <span className="text-xs text-gray-500">{message.message_type}</span>
            )}
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
            message.message_type === 'medical_alert' ? 'bg-red-100 border border-red-300' :
            message.message_type === 'translation' ? 'bg-yellow-100 border-2 border-yellow-300 shadow-md' :
            message.message_type === 'transcription' ? 'bg-gray-100 text-gray-600 opacity-60' :
            'bg-gray-100 text-gray-800'
          }`}>
            {renderMessageContent(message)}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MessageBubble;
