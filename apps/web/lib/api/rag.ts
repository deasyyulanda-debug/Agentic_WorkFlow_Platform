import apiClient from "./client";

// ============================================================================
// RAG Pipeline Types - Enterprise-Grade
// ============================================================================

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
    reranking_enabled?: boolean;
    reranking_top_k?: number;
    reranker_model?: string;
  };
  llm?: {
    provider?: string;
    model?: string;
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
  total_queries: number;
  last_query_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentUploadResponse {
  pipeline_id: string;
  document_id: string;
  file_name: string;
  file_size_bytes: number;
  chunks_created: number;
  processing_time_ms: number;
  character_count: number;
  word_count: number;
  status: string;
  message: string;
}

export interface DocumentInfo {
  id: string;
  pipeline_id: string;
  file_name: string;
  file_size_bytes: number;
  file_type: string;
  chunk_count: number;
  character_count: number | null;
  word_count: number | null;
  status: string;
  error_message: string | null;
  processing_time_ms: number | null;
  created_at: string;
}

export interface MetadataFilter {
  field: string;
  operator?: "eq" | "ne" | "gt" | "gte" | "lt" | "lte" | "in" | "nin";
  value: any;
}

export interface RAGQueryResponse {
  query: string;
  answer: string | null;
  results: Array<{
    content: string;
    metadata: Record<string, any>;
    score: number | null;
    rerank_score: number | null;
  }>;
  total_results: number;
  pipeline_id: string;
  reranking_applied: boolean;
  query_time_ms: number | null;
}

export interface PipelineStatistics {
  pipeline_id: string;
  pipeline_name: string;
  status: string;
  document_count: number;
  chunk_count: number;
  total_queries: number;
  last_query_at: string | null;
  documents: DocumentInfo[];
  config: Record<string, any>;
  embedding_provider: string;
  chunking_strategy: string;
  chunk_size: number;
  chunk_overlap: number;
  top_k: number;
  reranking_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface ConfigOption {
  value: string;
  label: string;
  description: string;
}

export interface LLMModelOption {
  value: string;
  label: string;
  default?: boolean;
}

export interface LLMProviderOption {
  value: string;
  label: string;
  description: string;
  models: LLMModelOption[];
}

export interface FileTypeOption {
  extension: string;
  label: string;
}

export interface RAGConfigOptions {
  chunking_strategies: ConfigOption[];
  embedding_providers: ConfigOption[];
  vector_stores: ConfigOption[];
  supported_file_types: FileTypeOption[];
  llm_providers: LLMProviderOption[];
  reranker_models: ConfigOption[];
  defaults: {
    chunk_size: number;
    chunk_overlap: number;
    top_k: number;
    chunking_strategy: string;
    embedding_provider: string;
    vector_store: string;
    reranking_enabled: boolean;
    reranking_top_k: number;
    reranker_model: string;
    max_file_size_mb: number;
    llm_provider: string;
    llm_model: string;
  };
}

// ============================================================================
// RAG API Client
// ============================================================================

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

  // List documents in pipeline
  listDocuments: async (pipelineId: string): Promise<DocumentInfo[]> => {
    const response = await apiClient.get(
      `/rag/pipelines/${pipelineId}/documents`
    );
    return response.data;
  },

  // Delete document from pipeline
  deleteDocument: async (
    pipelineId: string,
    documentId: string
  ): Promise<void> => {
    await apiClient.delete(
      `/rag/pipelines/${pipelineId}/documents/${documentId}`
    );
  },

  // Query pipeline - calls backend directly to bypass Next.js proxy timeout
  queryPipeline: async (
    pipelineId: string,
    query: string,
    topK?: number,
    metadataFilters?: MetadataFilter[],
    rerankingEnabled?: boolean
  ): Promise<RAGQueryResponse> => {
    // Use native fetch directly to backend, bypassing Next.js rewrite proxy
    // which has an internal timeout we cannot configure
    const backendUrl = "http://localhost:8000/api/v1";
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 600000); // 10 min timeout

    try {
      const res = await fetch(
        `${backendUrl}/rag/pipelines/${pipelineId}/query`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query,
            top_k: topK,
            generate_answer: true,
            metadata_filters: metadataFilters,
            reranking_enabled: rerankingEnabled,
          }),
          signal: controller.signal,
        }
      );
      clearTimeout(timeoutId);

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw { response: { data: errData, status: res.status }, message: res.statusText };
      }
      return await res.json();
    } catch (err: any) {
      clearTimeout(timeoutId);
      if (err.name === "AbortError") {
        throw { message: "Query timed out (10 min). Model inference on CPU may be too slow." };
      }
      throw err;
    }
  },

  // Get pipeline statistics
  getPipelineStats: async (pipelineId: string): Promise<PipelineStatistics> => {
    const response = await apiClient.get(
      `/rag/pipelines/${pipelineId}/stats`
    );
    return response.data;
  },
};
