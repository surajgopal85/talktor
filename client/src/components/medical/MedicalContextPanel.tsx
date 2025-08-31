import React from 'react';
import { Heart, User, Pill, AlertTriangle, Activity, Clock, Bug } from 'lucide-react';

interface MedicalAlert {
  id: string;
  type: string;
  message: string;
  severity: string;
  timestamp: string;
}

interface MedicalContextPanelProps {
  medicalContext: any;
  medicalAlerts: MedicalAlert[];
  showConfidenceScores: boolean;
  showMedicalAlerts: boolean;
  showExtractionMethods: boolean;
  conversationActive: boolean;
  messages: any[];
}

const MedicalContextPanel: React.FC<MedicalContextPanelProps> = ({
  medicalContext,
  medicalAlerts,
  showConfidenceScores,
  showMedicalAlerts,
  showExtractionMethods,
  conversationActive,
  messages
}) => {
  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className="w-80 bg-white shadow-xl border-l border-gray-200 flex flex-col">
      {/* Medical Context Header */}
      <div className="p-4 border-b border-gray-100 bg-gradient-to-r from-green-600 to-blue-600">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-white/20 rounded-lg">
            <Heart className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-white">Medical Context</h2>
            <p className="text-green-100 text-sm">Patient Information & Alerts</p>
          </div>
        </div>
      </div>

      {/* Medical Context Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Patient Summary */}
        <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
          <h3 className="font-medium text-blue-800 mb-2 flex items-center">
            <User className="w-4 h-4 mr-2" />
            Patient Summary
          </h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Language:</span>
              <span className="font-medium">Spanish (Patient) / English (Doctor)</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Specialty:</span>
              <span className="font-medium">OBGYN</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Session Status:</span>
              <span className={`font-medium ${
                conversationActive ? 'text-green-600' : 'text-gray-600'
              }`}>
                {conversationActive ? 'Active' : 'Demo Mode'}
              </span>
            </div>
          </div>
        </div>

        {/* Medications Discussed */}
        {medicalContext?.medications_discussed && medicalContext.medications_discussed.length > 0 && (
          <div className="bg-green-50 rounded-lg p-3 border border-green-200">
            <h3 className="font-medium text-green-800 mb-2 flex items-center">
              <Pill className="w-4 h-4 mr-2" />
              Medications Discussed
              <span className="ml-auto text-xs bg-green-200 text-green-700 px-2 py-1 rounded-full">
                {medicalContext.medications_discussed.length}
              </span>
            </h3>
            <div className="space-y-2">
              {medicalContext.medications_discussed.slice(0, 8).map((medication: string, index: number) => (
                <div key={index} className="flex items-center justify-between text-sm">
                  <span className="font-medium text-green-700">{medication}</span>
                  {showConfidenceScores && medicalContext.confidence_scores[medication] && (
                    <span className="text-xs bg-green-200 text-green-700 px-2 py-1 rounded">
                      {Math.round(medicalContext.confidence_scores[medication] * 100)}%
                    </span>
                  )}
                </div>
              ))}
              {medicalContext.medications_discussed.length > 8 && (
                <div className="text-xs text-green-600 text-center pt-2">
                  +{medicalContext.medications_discussed.length - 8} more medications
                </div>
              )}
            </div>
          </div>
        )}

        {/* Medical Alerts */}
        {showMedicalAlerts && medicalAlerts.length > 0 && (
          <div className="bg-red-50 rounded-lg p-3 border border-red-200">
            <h3 className="font-medium text-red-800 mb-2 flex items-center">
              <AlertTriangle className="w-4 h-4 mr-2" />
              Active Medical Alerts
              <span className="ml-auto text-xs bg-red-200 text-red-700 px-2 py-1 rounded-full">
                {medicalAlerts.length}
              </span>
            </h3>
            <div className="space-y-2">
              {medicalAlerts.slice(0, 5).map((alert) => (
                <div key={alert.id} className={`p-2 rounded text-sm ${
                  alert.severity === 'urgent' || alert.severity === 'critical'
                    ? 'bg-red-100 border-l-4 border-red-400'
                    : 'bg-orange-100 border-l-4 border-orange-400'
                }`}>
                  <div className="font-medium text-gray-800">{alert.type}</div>
                  <div className="text-xs text-gray-600 mt-1">{alert.message}</div>
                  <div className="text-xs text-gray-500 mt-1">
                    {formatTimestamp(alert.timestamp)}
                  </div>
                </div>
              ))}
              {medicalAlerts.length > 5 && (
                <div className="text-xs text-red-600 text-center pt-2">
                  +{medicalAlerts.length - 5} more alerts
                </div>
              )}
            </div>
          </div>
        )}

        {/* Extraction Strategies Used */}
        {showExtractionMethods && medicalContext?.extraction_strategies && medicalContext.extraction_strategies.length > 0 && (
          <div className="bg-purple-50 rounded-lg p-3 border border-purple-200">
            <h3 className="font-medium text-purple-800 mb-2 flex items-center">
              <Activity className="w-4 h-4 mr-2" />
              AI Analysis Methods
            </h3>
            <div className="space-y-1">
              {medicalContext.extraction_strategies.map((strategy: string, index: number) => (
                <div key={index} className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded">
                  {strategy.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Conversation Statistics */}
        <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
          <h3 className="font-medium text-gray-800 mb-2 flex items-center">
            <Clock className="w-4 h-4 mr-2" />
            Session Statistics
          </h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Messages:</span>
              <span className="font-medium">{messages.length}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Translations:</span>
              <span className="font-medium">
                {messages.filter(m => m.message_type === 'translation').length}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Alerts:</span>
              <span className="font-medium">{medicalAlerts.length}</span>
            </div>
            {medicalContext?.medications_discussed && (
              <div className="flex justify-between">
                <span className="text-gray-600">Medications:</span>
                <span className="font-medium">{medicalContext.medications_discussed.length}</span>
              </div>
            )}
          </div>
        </div>

        {/* Demo Instructions */}
        {!conversationActive && (
          <div className="bg-yellow-50 rounded-lg p-3 border border-yellow-200">
            <h3 className="font-medium text-yellow-800 mb-2 flex items-center">
              <Bug className="w-4 h-4 mr-2" />
              Demo Instructions
            </h3>
            <div className="text-xs text-yellow-700 space-y-1">
              <p>• Click any demo scenario to test</p>
              <p>• Watch medical context build</p>
              <p>• See real-time safety alerts</p>
              <p>• Observe confidence scoring</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MedicalContextPanel;
