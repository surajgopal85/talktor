// src/App.tsx - Updated with WebSocket Testing
import React, { useState } from 'react';
import { ErrorTrackingChatInterface } from './components/ErrorTrackingChatInterface';
import { Stethoscope, MessageSquare, Radio } from 'lucide-react';

// updated conversation UI test & seamless
import { WebSocketTest } from './components/WebSocketTest';
import { SeamlessConversationInterface } from './components/SeamlessConversationInterface';

// toggle modes
type TestMode = 'chat' | 'websocket' | 'conversation';

function App() {
  const [testMode, setTestMode] = useState<TestMode>('chat');

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-4">
        {/* Header */}
        <div className="text-center mb-6">
          <div className="flex items-center justify-center space-x-3 mb-2">
            <Stethoscope className="text-blue-600" size={32} />
            <h1 className="text-3xl font-bold text-gray-800">talktor</h1>
          </div>
          <p className="text-gray-600">
            AI-powered medical interpreter - Phase 2 Development & Testing
          </p>
        </div>

        {/* Test Mode Toggle */}
        <div className="flex justify-center mb-6">
          <div className="bg-white rounded-lg p-1 shadow-md">
            <button
              onClick={() => setTestMode('chat')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-all ${
                testMode === 'chat'
                  ? 'bg-blue-500 text-white shadow-sm'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <MessageSquare size={18} />
              <span>Chat Interface</span>
            </button>
            <button
              onClick={() => setTestMode('websocket')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-all ${
                testMode === 'websocket'
                  ? 'bg-green-500 text-white shadow-sm'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <Radio size={18} />
              <span>WebSocket Test</span>
            </button>
            <button
              onClick={() => setTestMode('conversation')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-all ${
                testMode === 'conversation'
                  ? 'bg-purple-500 text-white shadow-sm'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <Stethoscope size={18} />
              <span>Live Consultation</span>
            </button>
          </div>
        </div>

        {/* Test Mode Description */}
        <div className="text-center mb-6">
          {testMode === 'chat' ? (
            <p className="text-sm text-gray-600">
              <strong>Phase 1 Testing:</strong> Translation + Spanish Medical Intelligence
            </p>
          ) : (
            <p className="text-sm text-gray-600">
              <strong>Phase 2 Testing:</strong> Real-time WebSocket Conversations
            </p>
          )}
        </div>

        {/* Content based on test mode */}
        <div className="transition-all duration-300">
          {testMode === 'chat' ? (
            <ErrorTrackingChatInterface />
          ) : (
            <WebSocketTest />
          )}
          {/* added conversation mode */}
          {testMode === 'conversation' && <SeamlessConversationInterface />}
        </div>

        {/* Development Footer */}
        <div className="text-center mt-8 pt-6 border-t border-gray-200">
          <p className="text-xs text-gray-500">
            Development Mode - Phase {testMode === 'chat' ? '1' : '2'} Testing
          </p>
        </div>
      </div>
    </div>
  );
}

export default App;

// // src/App.tsx (Simplified - No Routing)
// import React, { useState } from 'react';
// import { AudioRecorder } from './components/AudioRecorder';
// import { MedicalTranslationDisplay } from './components/MedicalTranslationDisplay';
// import { Stethoscope } from 'lucide-react';

// function App() {
//   const [transcribedText, setTranscribedText] = useState('');
//   const [currentSessionId, setCurrentSessionId] = useState('');

//   const handleTranscription = (text: string, sessionId: string) => {
//     setTranscribedText(text);
//     setCurrentSessionId(sessionId);
//   };

//   const clearSession = () => {
//     setTranscribedText('');
//     setCurrentSessionId('');
//   };

//   return (
//     <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
//       <div className="container mx-auto px-4 py-8">
//         {/* Header */}
//         <div className="text-center mb-8">
//           <div className="flex items-center justify-center space-x-3 mb-4">
//             <Stethoscope className="text-blue-600" size={48} />
//             <h1 className="text-4xl font-bold text-gray-800">talktor</h1>
//           </div>
//           <p className="text-gray-600 max-w-2xl mx-auto">
//             AI-powered medical interpreter for English-speaking doctors and Spanish-speaking patients.
//             Translate medical conversations and suggest helpful questions patients can ask.
//           </p>
//         </div>

//         {/* Main Content */}
//         <div className="space-y-8">
//           {/* Audio Recorder */}
//           <div className="bg-white rounded-xl shadow-lg p-8">
//             <h2 className="text-2xl font-semibold text-gray-800 text-center mb-6">
//               Voice Recording
//             </h2>
//             <AudioRecorder onTranscription={handleTranscription} />
//           </div>

//           {/* Enhanced Medical Translation Display */}
//           <div className="bg-white rounded-xl shadow-lg p-8">
//             <div className="flex items-center justify-between mb-6">
//               <h2 className="text-2xl font-semibold text-gray-800">
//                 Enhanced Medical Translation
//               </h2>
//               {currentSessionId && (
//                 <button
//                   onClick={clearSession}
//                   className="px-4 py-2 text-sm bg-gray-100 text-gray-600 rounded-md hover:bg-gray-200 transition-colors"
//                 >
//                   Clear Session
//                 </button>
//               )}
//             </div>
//             <MedicalTranslationDisplay
//               originalText={transcribedText}
//               sessionId={currentSessionId}
//             />
//           </div>
//         </div>

//         {/* Footer */}
//         <div className="text-center mt-12 text-gray-500 text-sm">
//           <p>Empowering patient communication • HIPAA compliance ready • Enhanced medical intelligence</p>
//         </div>
//       </div>
//     </div>
//   );
// }

// export default App;