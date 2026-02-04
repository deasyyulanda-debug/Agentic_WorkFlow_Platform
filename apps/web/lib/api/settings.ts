import apiClient from "./client";
import type {
  Settings,
  SettingsCreate,
  SettingsUpdate,
  Provider,
} from "@/types/api";

export const settingsApi = {
  // List all settings
  list: async (params?: {
    skip?: number;
    limit?: number;
    active_only?: boolean;
  }): Promise<Settings[]> => {
    const response = await apiClient.get("/settings", { params });
    return response.data;
  },

  // Get settings by ID
  getById: async (id: string): Promise<Settings> => {
    const response = await apiClient.get(`/settings/${id}`);
    return response.data;
  },

  // Get settings by provider
  getByProvider: async (provider: Provider): Promise<Settings> => {
    const response = await apiClient.get(`/settings/provider/${provider}`);
    return response.data;
  },

  // Create new settings
  create: async (data: SettingsCreate): Promise<Settings> => {
    const response = await apiClient.post("/settings", data);
    return response.data;
  },

  // Update settings
  update: async (id: string, data: SettingsUpdate): Promise<Settings> => {
    const response = await apiClient.put(`/settings/${id}`, data);
    return response.data;
  },

  // Delete settings
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/settings/${id}`);
  },

  // Activate settings
  activate: async (id: string): Promise<Settings> => {
    const response = await apiClient.post(`/settings/${id}/activate`);
    return response.data;
  },

  // Deactivate settings
  deactivate: async (id: string): Promise<Settings> => {
    const response = await apiClient.post(`/settings/${id}/deactivate`);
    return response.data;
  },

  // Test API key
  test: async (id: string): Promise<{ valid: boolean; message: string }> => {
    const response = await apiClient.post(`/settings/${id}/test`);
    return response.data;
  },
};
