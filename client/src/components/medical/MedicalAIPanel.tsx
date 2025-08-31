import React from 'react';
import { Brain, AlertTriangle, Activity, Target } from 'lucide-react';

interface MedicalAIPanelProps {
  medicalContext: any;
  medicalAlerts: any[];
  showMedicalAI: boolean;
}

const MedicalAIPanel: React.FC<MedicalAIPanelProps> = ({
  medicalContext,
  medicalAlerts,
  showMedicalAI
}) => {
  if (!showMedicalAI) {
    return null;
  }

  return (
    <div className="bg-white shadow-lg border-l border-gray-200 w-80 overflow-y-auto">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center space-x-2">
          <Brain className="w-5 h-5 text-purple-600" />
          <h3 className="font-semibold text-gray-800">Medical AI Analysis</h3>
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* Medical Alerts */}
        {medicalAlerts.length > 0 && (
          <div className="bg-red-50 rounded-lg p-3 border border-red-200">
            <div className="flex items-center space-x-2 mb-2">
              <AlertTriangle className="w-4 h-4 text-red-600" />
              <span className="font-medium text-red-800">Medical Alerts</span>
            </div>
            <div className="space-y-1">
              {medicalAlerts.map((alert, index) => (
                <div key={index} className="text-sm text-red-700">
                  <span className="font-medium">{alert.type}:</span> {alert.message}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Medications Detected */}
        {medicalContext?.medications_discussed && medicalContext.medications_discussed.length > 0 && (
          <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
            <div className="flex items-center space-x-2 mb-2">
              <Target className="w-4 h-4 text-blue-600" />
              <span className="font-medium text-blue-800">Medications Detected</span>
            </div>
            <div className="flex flex-wrap gap-1">
              {medicalContext.medications_discussed.map((medication: string, index: number) => (
                <span
                  key={index}
                  className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs"
                >
                  {medication}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Confidence Scores */}
        {medicalContext?.confidence_scores && Object.keys(medicalContext.confidence_scores).length > 0 && (
          <div className="bg-green-50 rounded-lg p-3 border border-green-200">
            <div className="flex items-center space-x-2 mb-2">
              <Activity className="w-4 h-4 text-green-600" />
              <span className="font-medium text-green-800">Confidence Scores</span>
            </div>
            <div className="space-y-1">
              {Object.entries(medicalContext.confidence_scores).map(([term, score]: [string, any]) => (
                <div key={term} className="flex justify-between text-sm">
                  <span className="text-green-700">{term}:</span>
                  <span className="font-medium text-green-800">{(score * 100).toFixed(1)}%</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Extraction Methods */}
        {medicalContext?.extraction_strategies && medicalContext.extraction_strategies.length > 0 && (
          <div className="bg-purple-50 rounded-lg p-3 border border-purple-200">
            <div className="flex items-center space-x-2 mb-2">
              <Brain className="w-4 h-4 text-purple-600" />
              <span className="font-medium text-purple-800">AI Methods Used</span>
            </div>
            <div className="space-y-1">
              {medicalContext.extraction_strategies.map((method: string, index: number) => (
                <div key={index} className="text-sm text-purple-700">
                  • {method.replace(/_/g, ' ')}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MedicalAIPanel;
