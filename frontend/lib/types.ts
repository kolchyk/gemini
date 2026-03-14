export type ModelMode = "Flash" | "Pro" | "Both";
export type AspectRatio = "1:1" | "16:9" | "9:16" | "4:3" | "3:4" | "2:3" | "3:2" | "4:5" | "5:4" | "21:9" | "1:4" | "4:1" | "1:8" | "8:1";
export type PromptType = "custom" | "women" | "men" | "darnytsia";

export interface GenerationResult {
  image_base64: string | null;
  text_output: string;
  error?: string | null;
}

export interface GenerateResponse {
  results: Record<string, GenerationResult>;
  fallback_used?: boolean;
}

export type GenerationJobStatus = "queued" | "running" | "completed" | "failed";

export interface GenerateJobSubmitResponse {
  job_id: string;
  status: GenerationJobStatus;
}

export interface GenerateJobStatusResponse {
  job_id: string;
  status: GenerationJobStatus;
  results?: Record<string, GenerationResult>;
  fallback_used?: boolean;
  error?: string | null;
}

export interface PromptsResponse {
  custom: string;
  women: string;
  men: string;
  darnytsia: string;
}

export interface GenerationState {
  modelMode: ModelMode;
  aspectRatio: AspectRatio;
  temperature: number;
  promptType: PromptType;
  prompt: string;
  referenceFiles: File[];
  results: Record<string, GenerationResult> | null;
  isGenerating: boolean;
  error: string | null;
}
