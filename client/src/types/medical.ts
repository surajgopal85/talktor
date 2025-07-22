// src/types/medical.ts
export interface MedicalContext {
    specialty: string;
    confidence: number;
    detected_keywords: string[];
    safety_alerts: Array<{
      type: string;
      message: string;
      severity: 'low' | 'medium' | 'high' | 'critical';
    }>;
    follow_up_questions: string[];
    patient_education: string[];
  }
  
  export interface TranslationQuality {
    confidence: number;
    medical_accuracy: number;
  }
  
  export interface SessionData {
    sessionId: string;
    originalText: string;
    translatedText: string;
    medicalContext: MedicalContext | null;
    timestamp: Date;
  }
  
  export interface MedicalTranslationResponse {
    translated_text: string;
    medical_context: MedicalContext;
    translation_quality: TranslationQuality;
  }