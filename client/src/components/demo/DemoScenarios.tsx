import React from 'react';
import { Stethoscope, Bug } from 'lucide-react';

interface DemoScenariosProps {
  onRunScenario: (scenarioType: string) => void;
  showDemoScenarios: boolean;
  conversationActive: boolean;
}

const DemoScenarios: React.FC<DemoScenariosProps> = ({
  onRunScenario,
  showDemoScenarios,
  conversationActive
}) => {
  if (!showDemoScenarios) return null;

  return (
    <>
      {/* Demo Scenarios Section */}
      {!conversationActive && (
        <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-6 mb-6">
          <h3 className="text-lg font-semibold text-blue-800 mb-4 flex items-center">
            <Stethoscope className="w-5 h-5 mr-2" />
            Medical Translation Demo Scenarios
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* OBGYN Scenarios */}
            <div className="space-y-3">
              <h4 className="font-medium text-blue-700">🏥 OBGYN Consultation</h4>
              <div className="space-y-2">
                <button
                  onClick={() => onRunScenario('prenatal_safety')}
                  className="w-full text-left p-3 bg-white border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors"
                >
                  <div className="font-medium text-sm">Prenatal Medication Safety</div>
                  <div className="text-xs text-gray-600">"Estoy embarazada tomando ibuprofeno y amoxicilina"</div>
                </button>
                
                <button
                  onClick={() => onRunScenario('postpartum_complex')}
                  className="w-full text-left p-3 bg-white border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors"
                >
                  <div className="font-medium text-sm">Postpartum Recovery</div>
                  <div className="text-xs text-gray-600">Complex medication interactions</div>
                </button>
                
                <button
                  onClick={() => onRunScenario('menopause_hrt')}
                  className="w-full text-left p-3 bg-white border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors"
                >
                  <div className="font-medium text-sm">Menopause HRT Discussion</div>
                  <div className="text-xs text-gray-600">Hormone replacement therapy</div>
                </button>
              </div>
            </div>
            
            {/* General Medical Scenarios */}
            <div className="space-y-3">
              <h4 className="font-medium text-blue-700">💊 General Medical</h4>
              <div className="space-y-2">
                <button
                  onClick={() => onRunScenario('medication_list')}
                  className="w-full text-left p-3 bg-white border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors"
                >
                  <div className="font-medium text-sm">Current Medications</div>
                  <div className="text-xs text-gray-600">"Tomo metformina para diabetes y lisinopril"</div>
                </button>
                
                <button
                  onClick={() => onRunScenario('symptom_discussion')}
                  className="w-full text-left p-3 bg-white border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors"
                >
                  <div className="font-medium text-sm">Symptom Discussion</div>
                  <div className="text-xs text-gray-600">Pain, fever, side effects</div>
                </button>
                
                <button
                  onClick={() => onRunScenario('allergy_alert')}
                  className="w-full text-left p-3 bg-white border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors"
                >
                  <div className="font-medium text-sm">Allergy Alert</div>
                  <div className="text-xs text-gray-600">"Soy alérgica a penicilina y aspirina"</div>
                </button>
              </div>
            </div>
          </div>
          
          <div className="mt-4 p-3 bg-blue-100 rounded-lg">
            <div className="text-sm text-blue-800">
              <strong>Demo Features:</strong> Each scenario tests the BERT-enhanced medical translation system, 
              including medication extraction, safety alerts, and confidence scoring. Perfect for demonstrating 
              to medical professionals.
            </div>
          </div>
        </div>
      )}

      {/* Enhanced Test Buttons */}
      {conversationActive && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
          <h4 className="font-medium text-yellow-800 mb-3 flex items-center">
            <Bug className="w-4 h-4 mr-2" />
            Quick Test Scenarios
          </h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            <button
              onClick={() => onRunScenario('prenatal_safety')}
              className="bg-red-500 text-white px-3 py-2 rounded text-xs hover:bg-red-600 transition-colors"
            >
              🚨 Pregnancy Safety
            </button>
            <button
              onClick={() => onRunScenario('medication_list')}
              className="bg-blue-500 text-white px-3 py-2 rounded text-xs hover:bg-blue-600 transition-colors"
            >
              💊 Medication List
            </button>
            <button
              onClick={() => onRunScenario('allergy_alert')}
              className="bg-orange-500 text-white px-3 py-2 rounded text-xs hover:bg-orange-600 transition-colors"
            >
              ⚠️ Allergy Alert
            </button>
            <button
              onClick={() => onRunScenario('symptom_discussion')}
              className="bg-green-500 text-white px-3 py-2 rounded text-xs hover:bg-green-600 transition-colors"
            >
              💬 Translation
            </button>
          </div>
        </div>
      )}
    </>
  );
};

export default DemoScenarios;
