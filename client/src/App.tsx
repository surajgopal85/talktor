// src/App.tsx - Simplified & Clean
import React, { useState } from 'react';
import { Stethoscope, Settings, Eye, EyeOff } from 'lucide-react';
import { TalktorMedicalInterface } from './components/TalktorMedicalInterface';
import { ErrorTrackingChatInterface } from './components/ErrorTrackingChatInterface';
import { TailwindTest } from './components/TailwindTest';

type AppMode = 'production' | 'development';

function App() {
  const [appMode, setAppMode] = useState<AppMode>('production');
  const [showDevTools, setShowDevTools] = useState(false);

  return (
    <div className="min-h-screen bg-gray-100">
      <TailwindTest />
      {/* Simple Header - Only show in development mode */}
      {appMode === 'development' && (
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between max-w-7xl mx-auto">
            <div className="flex items-center space-x-3">
              <Stethoscope className="text-blue-600" size={28} />
              <div>
                <h1 className="text-xl font-bold text-gray-800">Talktor Development</h1>
                <p className="text-sm text-gray-600">Medical AI Interpreter - Testing Environment</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Mode Toggle */}
              <div className="flex items-center space-x-2">
                <label className="text-sm font-medium text-gray-700">Mode:</label>
                <select
                  value={appMode}
                  onChange={(e) => setAppMode(e.target.value as AppMode)}
                  className="border border-gray-300 rounded-md px-3 py-1 text-sm bg-white"
                >
                  <option value="production">🏥 Production Interface</option>
                  <option value="development">🔧 Development Testing</option>
                </select>
              </div>

              {/* Dev Tools Toggle */}
              {appMode === 'development' && (
                <button
                  onClick={() => setShowDevTools(!showDevTools)}
                  className={`flex items-center space-x-2 px-3 py-1 rounded-md text-sm ${
                    showDevTools 
                      ? 'bg-yellow-100 text-yellow-800' 
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {showDevTools ? <EyeOff size={16} /> : <Eye size={16} />}
                  <span>{showDevTools ? 'Hide' : 'Show'} Legacy Interface</span>
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="h-screen">
        {appMode === 'production' ? (
          // Production Mode: Beautiful Medical Interface Only
          <TalktorMedicalInterface />
        ) : (
          // Development Mode: Choose between interfaces
          <div className="flex h-full">
            {/* Main Interface */}
            <div className={showDevTools ? 'w-2/3' : 'w-full'}>
              <TalktorMedicalInterface />
            </div>

            {/* Legacy Development Interface */}
            {showDevTools && (
              <div className="w-1/3 border-l border-gray-300 bg-white">
                <div className="p-4 border-b border-gray-200">
                  <h3 className="font-semibold text-gray-800 flex items-center space-x-2">
                    <Settings size={16} />
                    <span>Legacy Development Interface</span>
                  </h3>
                  <p className="text-xs text-gray-600 mt-1">
                    Phase 1 testing - Translation only (no WebSocket)
                  </p>
                </div>
                <div className="p-4">
                  <ErrorTrackingChatInterface />
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Development Footer */}
      {appMode === 'development' && (
        <div className="fixed bottom-4 right-4">
          <div className="bg-yellow-100 border border-yellow-300 rounded-lg px-3 py-2 shadow-sm">
            <p className="text-xs text-yellow-800 font-medium">
              🔧 Development Mode Active
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;