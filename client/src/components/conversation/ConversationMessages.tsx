import React, { useRef, useEffect } from 'react';
import { MessageSquare } from 'lucide-react';
import MessageBubble from './MessageBubble';

interface ConversationMessage {
  id: string;
  speaker: 'doctor' | 'patient' | 'system';
  message_type: string;
  content: any;
  timestamp: string;
  language: string;
}

interface ConversationMessagesProps {
  messages: ConversationMessage[];
  showConfidenceScores: boolean;
  showDebugInfo: boolean;
  conversationActive: boolean;
}

const ConversationMessages: React.FC<ConversationMessagesProps> = ({
  messages,
  showConfidenceScores,
  showDebugInfo,
  conversationActive
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
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
      
      {messages.length === 0 && conversationActive && (
        <div className="text-center py-12">
          <MessageSquare className="mx-auto text-gray-400 mb-4" size={48} />
          <h3 className="text-lg font-medium text-gray-700 mb-2">
            Conversation Started
          </h3>
          <p className="text-gray-500">
            Start speaking or use the test buttons to begin the conversation
          </p>
        </div>
      )}
      
      {messages.map((message) => (
        <MessageBubble
          key={message.id}
          message={message}
          showConfidenceScores={showConfidenceScores}
          showDebugInfo={showDebugInfo}
        />
      ))}
      
      <div ref={messagesEndRef} />
    </div>
  );
};

export default ConversationMessages;
