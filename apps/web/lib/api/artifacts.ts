import apiClient from "./client";
import type { Artifact } from "@/types/api";

export const artifactsApi = {
  // List all artifacts
  list: async (params?: {
    skip?: number;
    limit?: number;
  }): Promise<Artifact[]> => {
    const response = await apiClient.get("/artifacts", { params });
    return response.data;
  },

  // Get artifact by ID
  getById: async (id: string): Promise<Artifact> => {
    const response = await apiClient.get(`/artifacts/${id}`);
    return response.data;
  },

  // Get artifact content
  getContent: async (id: string): Promise<any> => {
    const response = await apiClient.get(`/artifacts/${id}/content`);
    return response.data;
  },

  // Get artifacts for a run
  getByRun: async (runId: string): Promise<Artifact[]> => {
    const response = await apiClient.get(`/artifacts/run/${runId}`);
    return response.data;
  },

  // Download artifact
  download: async (id: string): Promise<Blob> => {
    const response = await apiClient.get(`/artifacts/${id}/download`, {
      responseType: "blob",
    });
    return response.data;
  },

  // Delete artifact
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/artifacts/${id}`);
  },
};
