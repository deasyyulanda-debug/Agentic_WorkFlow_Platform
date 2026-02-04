// API Response Types
// Generated from backend FastAPI schemas

export type Provider = "openai" | "anthropic" | "gemini" | "deepseek";

export type Persona = 
  | "student"
  | "researcher"
  | "ml_engineer"
  | "data_scientist"
  | "ai_architect";

export type RunStatus =
  | "queued"
  | "validating"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

export type RunMode =
  | "validate_only"
  | "test_run"
  | "full_run";

// Settings
export interface Settings {
  id: string;
  provider: Provider;
  api_key: string; // Masked in responses
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface SettingsCreate {
  provider: Provider;
  api_key: string;
  is_active?: boolean;
}

export interface SettingsUpdate {
  api_key?: string;
  is_active?: boolean;
}

// Workflows
export interface Workflow {
  id: string;
  name: string;
  description: string;
  persona: Persona;
  definition: {
    steps: Array<{
      type?: string;
      template?: string;
      prompt?: string;
      system_prompt?: string;
      temperature?: number;
      max_tokens?: number;
      output_variable?: string;
      settings_id?: string;
      [key: string]: any;
    }>;
  };
  is_active: boolean;
  tags?: string[];
  created_at: string;
  updated_at: string;
}

export interface WorkflowCreate {
  name: string;
  description: string;
  persona: Persona;
  definition: {
    steps: Array<{
      type?: string;
      template?: string;
      prompt?: string;
      settings_id?: string;
      [key: string]: any;
    }>;
  };
  is_active?: boolean;
  tags?: string[];
}

export interface WorkflowUpdate {
  name?: string;
  description?: string;
  definition?: {
    steps?: Array<{
      [key: string]: any;
    }>;
  };
  is_active?: boolean;
  tags?: string[];
}

// Runs
export interface Run {
  id: string;
  workflow_id: string;
  status: RunStatus;
  mode: RunMode;
  input_data: Record<string, any>;
  output_data?: Record<string, any> | null;
  metrics?: Record<string, any> | null;
  validation_result?: Record<string, any> | null;
  error_message?: string | null;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
}

export interface RunCreate {
  workflow_id: string;
  input_data: Record<string, any>;
  mode?: RunMode;
}

export interface RunExecutionResult {
  run: Run;
  output?: Record<string, any> | null;
  metrics?: Record<string, any> | null;
}

export interface RunStatus {
  run_id: string;
  status: RunStatus;
  started_at?: string | null;
  completed_at?: string | null;
  error_message?: string | null;
}

// Artifacts
export interface Artifact {
  id: string;
  run_id: string;
  step_index: number;
  artifact_type: string;
  file_path: string;
  file_size_bytes: number;
  mime_type: string;
  created_at: string;
}

// API Responses
export interface HealthResponse {
  status: string;
  version: string;
  environment: string;
}

export interface ValidationResult {
  valid: boolean;
  workflow_id?: string;
  errors?: string[];
  warnings?: string[];
}

// Error Response
export interface ErrorResponse {
  error: string;
  details?: Record<string, any>;
}
