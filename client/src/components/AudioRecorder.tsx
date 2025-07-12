import React, { useState, useRef } from 'react';
import { Mic, Square, Loader2 } from 'lucide-react';

interface AudioRecorderProps {
  onTranscription: (text: string, sessionId: string) => void;
}

export const AudioRecorder: React.FC<AudioRecorderProps> = ({ onTranscription }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/wav' });
        await sendAudioToServer(audioBlob);
        
        // Stop all tracks to release microphone
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Error accessing microphone:', error);
      alert('Could not access microphone. Please check permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setIsProcessing(true);
    }
  };

  const sendAudioToServer = async (audioBlob: Blob) => {
    try {
      const formData = new FormData();
      formData.append('file', audioBlob, 'recording.wav');

      const response = await fetch('http://127.0.0.1:8000/speech-to-text', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      onTranscription(result.text, result.session_id);
    } catch (error) {
      console.error('Error sending audio to server:', error);
      alert('Failed to process audio. Make sure the server is running.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleRecordToggle = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  return (
    <div className="flex flex-col items-center space-y-4">
      <button
        onClick={handleRecordToggle}
        disabled={isProcessing}
        className={`
          w-24 h-24 rounded-full flex items-center justify-center text-white text-2xl
          transition-all duration-200 shadow-lg hover:shadow-xl
          ${isRecording 
            ? 'bg-red-500 hover:bg-red-600 animate-pulse' 
            : 'bg-blue-500 hover:bg-blue-600'
          }
          ${isProcessing ? 'opacity-50 cursor-not-allowed' : 'hover:scale-105'}
        `}
      >
        {isProcessing ? (
          <Loader2 className="animate-spin" size={32} />
        ) : isRecording ? (
          <Square size={32} />
        ) : (
          <Mic size={32} />
        )}
      </button>

      <div className="text-center">
        {isProcessing && (
          <p className="text-gray-600 animate-pulse">Processing audio...</p>
        )}
        {isRecording && (
          <p className="text-red-500 font-medium">Recording... Click to stop</p>
        )}
        {!isRecording && !isProcessing && (
          <p className="text-gray-600">Click to start recording</p>
        )}
      </div>
    </div>
  );
};