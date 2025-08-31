import React from 'react';

interface ProductionTogglesProps {
  showDebugInfo: boolean;
  showConfidenceScores: boolean;
  showMedicalAlerts: boolean;
  showExtractionMethods: boolean;
  showDemoScenarios: boolean;
  showMedicalAI: boolean;
  onToggleChange: (key: string, value: boolean) => void;
  onProductionMode: () => void;
  onDemoMode: () => void;
}

const ProductionToggles: React.FC<ProductionTogglesProps> = ({
  showDebugInfo,
  showConfidenceScores,
  showMedicalAlerts,
  showExtractionMethods,
  showDemoScenarios,
  showMedicalAI,
  onToggleChange,
  onProductionMode,
  onDemoMode
}) => {
  return (
    <div className="bg-gray-100 border-b border-gray-200 p-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <span className="text-sm font-medium text-gray-700">Demo Mode:</span>
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={showDebugInfo}
              onChange={(e) => onToggleChange('showDebugInfo', e.target.checked)}
              className="rounded"
            />
            <span className="text-xs">Debug Info</span>
          </label>
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={showConfidenceScores}
              onChange={(e) => onToggleChange('showConfidenceScores', e.target.checked)}
              className="rounded"
            />
            <span className="text-xs">Confidence Scores</span>
          </label>
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={showMedicalAlerts}
              onChange={(e) => onToggleChange('showMedicalAlerts', e.target.checked)}
              className="rounded"
            />
            <span className="text-xs">Medical Alerts</span>
          </label>
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={showExtractionMethods}
              onChange={(e) => onToggleChange('showExtractionMethods', e.target.checked)}
              className="rounded"
            />
            <span className="text-xs">AI Methods</span>
          </label>
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={showDemoScenarios}
              onChange={(e) => onToggleChange('showDemoScenarios', e.target.checked)}
              className="rounded"
            />
            <span className="text-xs">Demo Scenarios</span>
          </label>
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={showMedicalAI}
              onChange={(e) => onToggleChange('showMedicalAI', e.target.checked)}
              className="rounded"
            />
            <span className="text-xs">Medical AI Data</span>
          </label>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={onProductionMode}
            className="text-xs bg-red-500 text-white px-2 py-1 rounded hover:bg-red-600"
          >
            Production Mode
          </button>
          <button
            onClick={onDemoMode}
            className="text-xs bg-blue-500 text-white px-2 py-1 rounded hover:bg-blue-600"
          >
            Demo Mode
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProductionToggles;
