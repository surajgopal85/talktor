import React from 'react';
import { Bug, ChevronDown, ChevronUp } from 'lucide-react';

interface DebugLog {
  timestamp: string;
  level: 'info' | 'error' | 'warning';
  message: string;
  data?: any;
}

interface DebugPanelProps {
  showDebug: boolean;
  debugLogs: DebugLog[];
  onToggleDebug: () => void;
}

const DebugPanel: React.FC<DebugPanelProps> = ({
  showDebug,
  debugLogs,
  onToggleDebug
}) => {
  if (!showDebug) return null;

  return (
    <div className="bg-gray-900 text-green-400 font-mono text-sm border-t border-gray-700">
      <div className="p-3 border-b border-gray-700">
        <button
          onClick={onToggleDebug}
          className="w-full flex items-center justify-center space-x-2 px-3 py-2 rounded-lg text-sm bg-gray-800 hover:bg-gray-700"
        >
          <Bug className="w-4 h-4" />
          <span>Hide Debug Logs</span>
        </button>
      </div>
      
      <div className="max-h-64 overflow-y-auto p-3 space-y-1">
        {debugLogs.length === 0 ? (
          <div className="text-gray-500 text-center py-4">
            No debug logs yet. Start a conversation to see logs.
          </div>
        ) : (
          debugLogs.map((log, index) => (
            <div key={index} className="flex items-start space-x-2">
              <span className="text-gray-500 text-xs min-w-[60px]">
                {new Date(log.timestamp).toLocaleTimeString()}
              </span>
              <span className={`text-xs px-1 rounded ${
                log.level === 'error' ? 'bg-red-900 text-red-300' :
                log.level === 'warning' ? 'bg-yellow-900 text-yellow-300' :
                'bg-blue-900 text-blue-300'
              }`}>
                {log.level.toUpperCase()}
              </span>
              <span className="flex-1">{log.message}</span>
              {log.data && (
                <details className="text-xs">
                  <summary className="cursor-pointer text-gray-400 hover:text-gray-300">
                    Data
                  </summary>
                  <pre className="mt-1 p-2 bg-gray-800 rounded text-xs overflow-x-auto">
                    {JSON.stringify(log.data, null, 2)}
                  </pre>
                </details>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default DebugPanel;
