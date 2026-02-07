import apiClient from "./client";

// RAG Pipeline Types
export interface RAGPipelineConfig {
  name: string;
  description?: string;
  chunking?: {
    strategy?: string;
    chunk_size?: number;
    chunk_overlap?: number;
  };
  embedding?: {
    provider?: string;
    model?: string;
  };
  vector_store?: {
    store_type?: string;
    collection_name?: string;
  };
  retrieval?: {
    top_k?: number;
    score_threshold?: number;
  };
}

export interface RAGPipeline {
  id: string;
  name: string;
  description: string;
  status: "created" | "ingesting" | "ready" | "error";
  config: Record<string, any>;
  document_count: number;
  chunk_count: number;
  created_at: string;
  updated_at: string;
}

export interface DocumentUploadResponse {
  pipeline_id: string;
  file_name: string;
  file_size_bytes: number;
  chunks_created: number;
  status: string;
  message: string;
}

export interface RAGQueryResponse {
  query: string;
  answer: string | null;
  results: Array<{
    content: string;
    metadata: Record<string, any>;
    score: number | null;
  }>;
  total_results: number;
  pipeline_id: string;
}

export interface ConfigOption {
  value: string;
  label: string;
  description: string;
}

export interface RAGConfigOptions {
  chunking_strategies: ConfigOption[];
  embedding_providers: ConfigOption[];
  vector_stores: ConfigOption[];
  defaults: {
    chunk_size: number;
    chunk_overlap: number;
    top_k: number;
    chunking_strategy: string;
    embedding_provider: string;
    vector_store: string;
  };
}

export const ragApi = {
  // Get configuration options
  getConfigOptions: async (): Promise<RAGConfigOptions> => {
    const response = await apiClient.get("/rag/config/options");
    return response.data;
  },

  // Create pipeline
  createPipeline: async (config: RAGPipelineConfig): Promise<RAGPipeline> => {
    const response = await apiClient.post("/rag/pipelines", config);
    return response.data;
  },

  // List pipelines
  listPipelines: async (): Promise<RAGPipeline[]> => {
    const response = await apiClient.get("/rag/pipelines");
    return response.data;
  },

  // Get pipeline
  getPipeline: async (id: string): Promise<RAGPipeline> => {
    const response = await apiClient.get(`/rag/pipelines/${id}`);
    return response.data;
  },

  // Delete pipeline
  deletePipeline: async (id: string): Promise<void> => {
    await apiClient.delete(`/rag/pipelines/${id}`);
  },

  // Upload document
  uploadDocument: async (
    pipelineId: string,
    file: File
  ): Promise<DocumentUploadResponse> => {
    const formData = new FormData();
    formData.append("file", file);
    const response = await apiClient.post(
      `/rag/pipelines/${pipelineId}/documents`,
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 120000, // 2 minutes for large files
      }
    );
    return response.data;
  },

  // Query pipeline
  queryPipeline: async (
    pipelineId: string,
    query: string,
    topK?: number
  ): Promise<RAGQueryResponse> => {
    const response = await apiClient.post(
      `/rag/pipelines/${pipelineId}/query`,
      { query, top_k: topK, generate_answer: true }
    );
    return response.data;
  },
};
