export type InputType = 'claim' | 'url' | 'image' | 'video' | 'audio';

export type JobStatusType = 'queued' | 'processing' | 'completed' | 'failed';

export type VerdictStance = 'SUPPORTS' | 'CONTRADICTS' | 'NEUTRAL' | 'CONTEXT';

export interface EvidenceItem {
  id?: string;
  title: string;
  source_name: string;
  source_url?: string;
  publisher?: string;
  publish_date?: string;
  snippet: string;
  stance: VerdictStance;
  credibility_score: number;
}

export interface MediaAnalysisDetail {
  id: string;
  media_type: 'image' | 'video' | 'audio';
  file_path?: string;
  file_size_bytes: number;
  mime_type?: string;
  metadata_info: Record<string, any>;
  visual_findings: Record<string, any>;
  audio_findings: Record<string, any>;
  transcript?: string;
  ai_generated_score: number;
  deepfake_score: number;
  manipulation_indicators: string[];
}

/**
 * Status variants for report cards and badge indicators.
 * Supports both descriptive semantic states ('good' | 'warn' | 'bad' | 'unknown')
 * and standard UI alert variants ('success' | 'warning' | 'danger' | 'info').
 */
export type CardStatus =
  | 'good'
  | 'warn'
  | 'bad'
  | 'unknown'
  | 'success'
  | 'warning'
  | 'danger'
  | 'info';

export interface ReportCardSection {
  key: string;
  title: string;
  percent: number | null;
  status: CardStatus;
  detail: string;
  [key: string]: any;
}

export interface ReportCardData {
  overall_percent?: number | null;
  score?: number;
  grade: string;
  grade_label: string;
  confidence_score: number;
  confidence_level: string;
  sections: ReportCardSection[];
  how_calculated: string;
  explanation: string;
  summary?: string;
  caveats: string[];
  [key: string]: any;
}

export interface VerificationReport {
  id: string;
  job_id?: string;
  title?: string;
  input_type?: InputType;
  overall_verdict?: string;
  verdict_label?: string;
  confidence_score?: number;
  confidence_level?: 'LOW' | 'MEDIUM' | 'HIGH';
  factual_claim_verdict?: string;
  media_authenticity_verdict?: string;
  context_verdict?: string;
  summary?: string;
  explanation?: string;
  correctness_score?: number;
  correctness_explanation?: string;
  report_card?: {
    score?: number;
    summary?: string;
    [key: string]: any;
  };
  limitations?: string[];
  checks_performed?: string[];
  checks_unavailable?: string[];
  media_url?: string;
  input_preview?: string;
  created_at?: string;
  evidence_items?: EvidenceItem[];
  media_analysis?: MediaAnalysisDetail;
  [key: string]: any; // Allow flexibility for other properties
}

export interface JobStatus {
  id: string;
  job_type: InputType;
  status: JobStatusType;
  progress: number;
  current_stage: string;
  report_id?: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface JobListResponse {
  total: number;
  jobs: JobStatus[];
}

export interface HealthStatus {
  status: string;
  app_name: string;
  version: string;
  environment: string;
  demo_mode: boolean;
  system: {
    python_version: string;
    os: string;
    platform: string;
    opencv_available: boolean;
    whisper_available: boolean;
    google_factcheck_configured: boolean;
  };
}
