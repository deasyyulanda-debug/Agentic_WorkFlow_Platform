import apiClient from "./client";
import type {
  Run,
  RunCreate,
  RunExecutionResult,
  RunStatus as RunStatusType,
  RunMode,
} from "@/types/api";

export const runsApi = {
  // Create run (queued)
  create: async (data: RunCreate): Promise<Run> => {
    const response = await apiClient.post("/runs", data);
    return response.data;
  },

  // Create and execute run (sync)
  execute: async (data: RunCreate): Promise<RunExecutionResult> => {
    const response = await apiClient.post("/runs/execute", data);
    return response.data;
  },

  // Create and execute run (async)
  executeAsync: async (data: RunCreate): Promise<Run> => {
    const response = await apiClient.post("/runs/execute-async", data);
    return response.data;
  },

  // List all runs
  list: async (params?: {
    skip?: number;
    limit?: number;
    workflow_id?: string;
    status_filter?: RunStatusType;
    run_mode?: RunMode;
  }): Promise<Run[]> => {
    const response = await apiClient.get("/runs", { params });
    return response.data;
  },

  // Get run by ID
  getById: async (id: string): Promise<Run> => {
    const response = await apiClient.get(`/runs/${id}`);
    return response.data;
  },

  // Execute existing run
  executeById: async (id: string): Promise<RunExecutionResult> => {
    const response = await apiClient.post(`/runs/${id}/execute`);
    return response.data;
  },

  // Delete run
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/runs/${id}`);
  },

  // Get run status
  getStatus: async (id: string): Promise<RunStatusType> => {
    const response = await apiClient.get(`/runs/${id}/status`);
    return response.data;
  },
};
