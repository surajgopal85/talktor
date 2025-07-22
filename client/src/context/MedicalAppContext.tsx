// src/context/MedicalAppContext.tsx
import React, { createContext, useContext, useReducer } from 'react';
import type { ReactNode } from 'react';
import type { SessionData, MedicalContext as MedicalContextType } from '../types/medical';

interface MedicalState {
  currentSession: SessionData | null;
  sessionHistory: SessionData[];
  medicalSettings: {
    defaultSourceLanguage: string;
    defaultTargetLanguage: string;
    preferredVoiceGender: 'male' | 'female';
    speechRate: number;
  };
}

type MedicalAction = 
  | { type: 'SET_CURRENT_SESSION'; payload: SessionData }
  | { type: 'ADD_TO_HISTORY'; payload: SessionData }
  | { type: 'CLEAR_SESSION' }
  | { type: 'UPDATE_SETTINGS'; payload: Partial<MedicalState['medicalSettings']> };

const initialState: MedicalState = {
  currentSession: null,
  sessionHistory: [],
  medicalSettings: {
    defaultSourceLanguage: 'en',
    defaultTargetLanguage: 'es',
    preferredVoiceGender: 'female',
    speechRate: 0.8
  }
};

const medicalReducer = (state: MedicalState, action: MedicalAction): MedicalState => {
  switch (action.type) {
    case 'SET_CURRENT_SESSION':
      return { ...state, currentSession: action.payload };
    case 'ADD_TO_HISTORY':
      return { 
        ...state, 
        sessionHistory: [action.payload, ...state.sessionHistory.slice(0, 49)] // Keep last 50
      };
    case 'CLEAR_SESSION':
      return { ...state, currentSession: null };
    case 'UPDATE_SETTINGS':
      return { 
        ...state, 
        medicalSettings: { ...state.medicalSettings, ...action.payload }
      };
    default:
      return state;
  }
};

const MedicalAppContext = createContext<{
  state: MedicalState;
  dispatch: React.Dispatch<MedicalAction>;
} | null>(null);

export const MedicalProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(medicalReducer, initialState);
  
  return (
    <MedicalAppContext.Provider value={{ state, dispatch }}>
      {children}
    </MedicalAppContext.Provider>
  );
};

export const useMedicalContext = () => {
  const context = useContext(MedicalAppContext);
  if (!context) {
    throw new Error('useMedicalContext must be used within MedicalProvider');
  }
  return context;
};