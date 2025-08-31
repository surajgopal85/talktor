import React from 'react';
import { FileText, Download, Share2, Clock, MessageSquare, AlertTriangle, Pill } from 'lucide-react';

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

interface ConversationSummaryProps {
  messages: ConversationMessage[];
  medicalAlerts: MedicalAlert[];
  medicalContext: any;
  sessionId: string;
}

const ConversationSummary: React.FC<ConversationSummaryProps> = ({
  messages,
  medicalAlerts,
  medicalContext,
  sessionId
}) => {
  const formatDuration = (startTime: string, endTime: string) => {
    const start = new Date(startTime);
    const end = new Date(endTime);
    const diffMs = end.getTime() - start.getTime();
    const minutes = Math.floor(diffMs / 60000);
    const seconds = Math.floor((diffMs % 60000) / 1000);
    return `${minutes}m ${seconds}s`;
  };

  const getConversationStats = () => {
    const doctorMessages = messages.filter(m => m.speaker === 'doctor').length;
    const patientMessages = messages.filter(m => m.speaker === 'patient').length;
    const systemMessages = messages.filter(m => m.speaker === 'system').length;
    const translations = messages.filter(m => m.message_type === 'translation').length;
    
    const startTime = messages[0]?.timestamp;
    const endTime = messages[messages.length - 1]?.timestamp;
    const duration = startTime && endTime ? formatDuration(startTime, endTime) : 'N/A';

    return {
      totalMessages: messages.length,
      doctorMessages,
      patientMessages,
      systemMessages,
      translations,
      duration,
      medications: medicalContext?.medications_discussed?.length || 0,
      alerts: medicalAlerts.length
    };
  };

  const stats = getConversationStats();

  const exportSummary = () => {
    const summary = {
      sessionId,
      timestamp: new Date().toISOString(),
      stats,
      medicalAlerts,
      medications: medicalContext?.medications_discussed || [],
      messages: messages.map(m => ({
        timestamp: m.timestamp,
        speaker: m.speaker,
        type: m.message_type,
        content: m.content
      }))
    };

    const blob = new Blob([JSON.stringify(summary, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `conversation-summary-${sessionId}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-white shadow-lg border-t border-gray-200 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <FileText className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-800">Conversation Summary</h2>
              <p className="text-sm text-gray-600">Session: {sessionId}</p>
            </div>
          </div>
          <div className="flex space-x-2">
            <button
              onClick={exportSummary}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
            >
              <Download className="w-4 h-4" />
              <span>Export</span>
            </button>
            <button className="flex items-center space-x-2 px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors">
              <Share2 className="w-4 h-4" />
              <span>Share</span>
            </button>
          </div>
        </div>

        {/* Statistics Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
            <div className="flex items-center space-x-2">
              <MessageSquare className="w-5 h-5 text-blue-600" />
              <span className="text-sm font-medium text-blue-800">Total Messages</span>
            </div>
            <div className="text-2xl font-bold text-blue-900 mt-1">{stats.totalMessages}</div>
          </div>
          
          <div className="bg-green-50 rounded-lg p-4 border border-green-200">
            <div className="flex items-center space-x-2">
              <Clock className="w-5 h-5 text-green-600" />
              <span className="text-sm font-medium text-green-800">Duration</span>
            </div>
            <div className="text-2xl font-bold text-green-900 mt-1">{stats.duration}</div>
          </div>
          
          <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
            <div className="flex items-center space-x-2">
              <Pill className="w-5 h-5 text-purple-600" />
              <span className="text-sm font-medium text-purple-800">Medications</span>
            </div>
            <div className="text-2xl font-bold text-purple-900 mt-1">{stats.medications}</div>
          </div>
          
          <div className="bg-red-50 rounded-lg p-4 border border-red-200">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-5 h-5 text-red-600" />
              <span className="text-sm font-medium text-red-800">Alerts</span>
            </div>
            <div className="text-2xl font-bold text-red-900 mt-1">{stats.alerts}</div>
          </div>
        </div>

        {/* Message Breakdown */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="font-medium text-gray-800 mb-3">Message Breakdown</h3>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Doctor Messages:</span>
                <span className="font-medium">{stats.doctorMessages}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Patient Messages:</span>
                <span className="font-medium">{stats.patientMessages}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">System Messages:</span>
                <span className="font-medium">{stats.systemMessages}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Translations:</span>
                <span className="font-medium">{stats.translations}</span>
              </div>
            </div>
          </div>

          {/* Medical Summary */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="font-medium text-gray-800 mb-3">Medical Summary</h3>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Medications Discussed:</span>
                <span className="font-medium">{stats.medications}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Medical Alerts:</span>
                <span className="font-medium">{stats.alerts}</span>
              </div>
              {medicalContext?.extraction_strategies && (
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">AI Methods Used:</span>
                  <span className="font-medium">{medicalContext.extraction_strategies.length}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Medical Alerts Summary */}
        {medicalAlerts.length > 0 && (
          <div className="bg-red-50 rounded-lg p-4 border border-red-200 mb-6">
            <h3 className="font-medium text-red-800 mb-3 flex items-center">
              <AlertTriangle className="w-4 h-4 mr-2" />
              Medical Alerts Summary
            </h3>
            <div className="space-y-2">
              {medicalAlerts.slice(0, 3).map((alert) => (
                <div key={alert.id} className="text-sm">
                  <span className="font-medium text-red-700">{alert.type}:</span>
                  <span className="text-red-600 ml-2">{alert.message}</span>
                </div>
              ))}
              {medicalAlerts.length > 3 && (
                <div className="text-sm text-red-600">
                  +{medicalAlerts.length - 3} more alerts
                </div>
              )}
            </div>
          </div>
        )}

        {/* Medications List */}
        {medicalContext?.medications_discussed && medicalContext.medications_discussed.length > 0 && (
          <div className="bg-green-50 rounded-lg p-4 border border-green-200">
            <h3 className="font-medium text-green-800 mb-3 flex items-center">
              <Pill className="w-4 h-4 mr-2" />
              Medications Discussed
            </h3>
            <div className="flex flex-wrap gap-2">
              {medicalContext.medications_discussed.map((medication: string, index: number) => (
                <span
                  key={index}
                  className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm"
                >
                  {medication}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ConversationSummary;
