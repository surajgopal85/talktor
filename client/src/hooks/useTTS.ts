import { useState, useEffect, useCallback } from 'react';

interface Voice {
  name: string;
  lang: string;
  gender: 'male' | 'female' | 'unknown';
  voice: SpeechSynthesisVoice;
}

interface TTSOptions {
  rate?: number;    // 0.1 to 10 (default: 1)
  pitch?: number;   // 0 to 2 (default: 1)
  volume?: number;  // 0 to 1 (default: 1)
  voice?: SpeechSynthesisVoice;
}

export const useTTS = () => {
  const [voices, setVoices] = useState<Voice[]>([]);
  const [isSupported, setIsSupported] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [currentUtterance, setCurrentUtterance] = useState<SpeechSynthesisUtterance | null>(null);

  // Initialize voices
  useEffect(() => {
    if ('speechSynthesis' in window) {
      setIsSupported(true);
      
      const loadVoices = () => {
        const availableVoices = speechSynthesis.getVoices();
        
        const processedVoices: Voice[] = availableVoices
          .filter(voice => 
            voice.lang.startsWith('en') || 
            voice.lang.startsWith('es') ||
            voice.lang.startsWith('fr') ||
            voice.lang.startsWith('pt')
          )
          .map(voice => ({
            name: voice.name,
            lang: voice.lang,
            gender: detectGender(voice.name),
            voice: voice
          }));
        
        setVoices(processedVoices);
      };

      // Load voices immediately if available
      loadVoices();
      
      // Also listen for voice loading (some browsers load asynchronously)
      speechSynthesis.onvoiceschanged = loadVoices;
    }
  }, []);

  // Helper function to detect gender from voice name
  const detectGender = (voiceName: string): 'male' | 'female' | 'unknown' => {
    const name = voiceName.toLowerCase();
    
    // Common patterns in voice names
    if (name.includes('female') || name.includes('woman') || 
        name.includes('karen') || name.includes('samantha') ||
        name.includes('alex') && name.includes('female') ||
        name.includes('paulina') || name.includes('monica')) {
      return 'female';
    }
    
    if (name.includes('male') || name.includes('man') ||
        name.includes('daniel') || name.includes('diego') ||
        name.includes('alex') && name.includes('male') ||
        name.includes('jorge') || name.includes('juan')) {
      return 'male';
    }
    
    return 'unknown';
  };

  // Get best voice for language
  const getBestVoice = (language: string, preferredGender?: 'male' | 'female'): SpeechSynthesisVoice | null => {
    const languageVoices = voices.filter(voice => 
      voice.lang.startsWith(language)
    );

    if (languageVoices.length === 0) return null;

    // Try to find preferred gender first
    if (preferredGender) {
      const genderMatch = languageVoices.find(voice => voice.gender === preferredGender);
      if (genderMatch) return genderMatch.voice;
    }

    // Fall back to first available voice for the language
    return languageVoices[0].voice;
  };

  // Main speak function
  const speak = useCallback((
    text: string, 
    language: string = 'en',
    options: TTSOptions = {}
  ) => {
    if (!isSupported || !text.trim()) return;

    // Stop any current speech
    stop();

    const utterance = new SpeechSynthesisUtterance(text);
    
    // Set voice
    const selectedVoice = options.voice || getBestVoice(language);
    if (selectedVoice) {
      utterance.voice = selectedVoice;
    }

    // Set speech parameters
    utterance.rate = options.rate || 0.8;  // Slightly slower for medical context
    utterance.pitch = options.pitch || 1;
    utterance.volume = options.volume || 1;

    // Event handlers
    utterance.onstart = () => {
      setIsSpeaking(true);
      console.log('TTS started');
    };

    utterance.onend = () => {
      setIsSpeaking(false);
      setCurrentUtterance(null);
      console.log('TTS finished');
    };

    utterance.onerror = (event) => {
      setIsSpeaking(false);
      setCurrentUtterance(null);
      console.error('TTS error:', event.error);
    };

    // Store current utterance for control
    setCurrentUtterance(utterance);

    // Start speaking
    speechSynthesis.speak(utterance);
  }, [isSupported, voices]);

  // Stop speaking
  const stop = useCallback(() => {
    if (speechSynthesis.speaking) {
      speechSynthesis.cancel();
    }
    setIsSpeaking(false);
    setCurrentUtterance(null);
  }, []);

  // Pause/Resume
  const pause = useCallback(() => {
    if (speechSynthesis.speaking && !speechSynthesis.paused) {
      speechSynthesis.pause();
    }
  }, []);

  const resume = useCallback(() => {
    if (speechSynthesis.paused) {
      speechSynthesis.resume();
    }
  }, []);

  return {
    // State
    isSupported,
    isSpeaking,
    voices,
    isPaused: speechSynthesis.paused,
    
    // Actions
    speak,
    stop,
    pause,
    resume,
    
    // Utilities
    getBestVoice
  };
};