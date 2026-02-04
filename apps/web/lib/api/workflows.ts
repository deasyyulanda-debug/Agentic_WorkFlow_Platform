import apiClient from "./client";
import type {
  Workflow,
  WorkflowCreate,
  WorkflowUpdate,
  ValidationResult,
  Persona,
} from "@/types/api";

export const workflowsApi = {
  // List all workflows
  list: async (params?: {
    skip?: number;
    limit?: number;
    active_only?: boolean;
    persona?: Persona;
    search?: string;
  }): Promise<Workflow[]> => {
    const response = await apiClient.get("/workflows", { params });
    return response.data;
  },

  // Get workflow by ID
  getById: async (id: string): Promise<Workflow> => {
    const response = await apiClient.get(`/workflows/${id}`);
    return response.data;
  },

  // Create new workflow
  create: async (data: WorkflowCreate): Promise<Workflow> => {
    const response = await apiClient.post("/workflows", data);
    return response.data;
  },

  // Update workflow
  update: async (id: string, data: WorkflowUpdate): Promise<Workflow> => {
    const response = await apiClient.put(`/workflows/${id}`, data);
    return response.data;
  },

  // Delete workflow
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/workflows/${id}`);
  },

  // Activate workflow
  activate: async (id: string): Promise<Workflow> => {
    const response = await apiClient.post(`/workflows/${id}/activate`);
    return response.data;
  },

  // Deactivate workflow
  deactivate: async (id: string): Promise<Workflow> => {
    const response = await apiClient.post(`/workflows/${id}/deactivate`);
    return response.data;
  },

  // Validate workflow
  validate: async (id: string): Promise<ValidationResult> => {
    const response = await apiClient.post(`/workflows/${id}/validate`);
    return response.data;
  },
};
