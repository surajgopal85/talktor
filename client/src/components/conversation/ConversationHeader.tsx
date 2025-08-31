import React from 'react';
import { Globe } from 'lucide-react';

interface ConversationHeaderProps {
  conversationActive: boolean;
  sessionId: string;
  doctorLanguage: string;
  patientLanguage: string;
}

const ConversationHeader: React.FC<ConversationHeaderProps> = ({
  conversationActive,
  sessionId,
  doctorLanguage,
  patientLanguage
}) => {
  return (
    <div className="bg-white shadow-sm border-b border-gray-200 p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Globe className="w-5 h-5 text-blue-600" />
            <span className="font-semibold text-gray-800">Live Medical Translation</span>
          </div>
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <span>Session:</span>
            <span className="font-mono text-xs bg-gray-100 px-2 py-1 rounded">
              {sessionId.substring(0, 8)}...
            </span>
          </div>
        </div>
        <div className="flex items-center space-x-4 text-sm">
          <div className="flex items-center space-x-2">
            <span className="text-gray-600">Languages:</span>
            <span className="font-medium">{doctorLanguage.toUpperCase()}</span>
            <span className="text-gray-400">→</span>
            <span className="font-medium">{patientLanguage.toUpperCase()}</span>
          </div>
          <div className={`px-2 py-1 rounded-full text-xs font-medium ${
            conversationActive 
              ? 'bg-green-100 text-green-800' 
              : 'bg-gray-100 text-gray-600'
          }`}>
            {conversationActive ? 'Active' : 'Ready'}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConversationHeader;
