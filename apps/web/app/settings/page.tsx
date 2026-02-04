"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { settingsApi } from "@/lib/api/settings";
import { Header } from "@/components/layout/header";
import { Footer } from "@/components/layout/footer";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Plus, Settings as SettingsIcon, CheckCircle, XCircle, Trash2, Edit } from "lucide-react";
import { getProviderName } from "@/lib/utils";
import { toast } from "sonner";
import type { SettingsCreate, Provider } from "@/types/api";

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const [isCreating, setIsCreating] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [isMounted, setIsMounted] = useState(false);
  const [formData, setFormData] = useState<SettingsCreate>({
    provider: "openai",
    api_key: "",
    is_active: true,
  });

  useEffect(() => {
    setIsMounted(true);
  }, []);

  const { data, isLoading } = useQuery({
    queryKey: ["settings"],
    queryFn: () => settingsApi.list({}),
  });

  const createMutation = useMutation({
    mutationFn: (data: SettingsCreate) => settingsApi.create(data),
    onSuccess: () => {
      toast.success("Provider configured successfully!");
      queryClient.invalidateQueries({ queryKey: ["settings"] });
      setIsCreating(false);
      setFormData({ provider: "openai", api_key: "", is_active: true });
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to create provider");
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: SettingsCreate }) => settingsApi.update(id, data),
    onSuccess: () => {
      toast.success("Provider updated successfully!");
      queryClient.invalidateQueries({ queryKey: ["settings"] });
      setEditingId(null);
      setFormData({ provider: "openai", api_key: "", is_active: true });
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to update provider");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => settingsApi.delete(id),
    onSuccess: () => {
      toast.success("Provider deleted successfully!");
      queryClient.invalidateQueries({ queryKey: ["settings"] });
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to delete provider");
    },
  });

  const toggleActiveMutation = useMutation({
    mutationFn: ({ id, activate }: { id: string; activate: boolean }) =>
      activate ? settingsApi.activate(id) : settingsApi.deactivate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["settings"] });
    },
  });

  const testMutation = useMutation({
    mutationFn: (id: string) => settingsApi.test(id),
    onSuccess: () => {
      toast.success("Provider connection successful!");
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Connection test failed");
    },
  });

  const settings = data || [];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (editingId) {
      updateMutation.mutate({ id: editingId, data: formData });
    } else {
      createMutation.mutate(formData);
    }
  };

  const handleEdit = (setting: any) => {
    setEditingId(setting.id);
    setFormData({
      provider: setting.provider,
      api_key: "", // Don't show existing key
      is_active: setting.is_active,
    });
    setIsCreating(true);
  };

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1">
        <div className="container py-8 max-w-5xl">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-4xl font-bold">Settings</h1>
            <p className="mt-2 text-muted-foreground">Manage AI provider configurations</p>
          </div>

          {!isMounted ? (
            <div className="space-y-4">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-32 rounded-lg bg-muted animate-pulse" />
              ))}
            </div>
          ) : (
            <>
              {/* Stats */}
              <div className="grid gap-4 md:grid-cols-3 mb-8">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">Total Providers</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{settings.length}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">Active</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">
                  {settings.filter((s) => s.is_active).length}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">Inactive</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-gray-400">
                  {settings.filter((s) => !s.is_active).length}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Add New Provider */}
          {!isCreating && (
            <Button onClick={() => setIsCreating(true)} className="mb-6">
              <Plus className="mr-2 h-4 w-4" />
              Add Provider
            </Button>
          )}

          {isCreating && (
            <Card className="mb-6">
              <CardHeader>
                <CardTitle>{editingId ? "Update Provider Configuration" : "New Provider Configuration"}</CardTitle>
                <CardDescription>
                  {editingId ? "Update the API key for your provider" : "Add a new AI provider to your workflow platform"}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="provider">Provider *</Label>
                    <select
                      id="provider"
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      value={formData.provider}
                      onChange={(e) => setFormData({ ...formData, provider: e.target.value as Provider })}
                      disabled={!!editingId}
                      required
                    >
                      <option value="openai">OpenAI</option>
                      <option value="anthropic">Anthropic (Claude)</option>
                      <option value="gemini">Google Gemini</option>
                      <option value="deepseek">DeepSeek</option>
                    </select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="api_key">API Key *</Label>
                    <Input
                      id="api_key"
                      type="password"
                      placeholder="sk-..."
                      value={formData.api_key}
                      onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
                      required
                    />
                  </div>

                  <div className="flex gap-3">
                    <Button type="submit" disabled={createMutation.isPending || updateMutation.isPending}>
                      {editingId
                        ? (updateMutation.isPending ? "Updating..." : "Update Provider")
                        : (createMutation.isPending ? "Creating..." : "Create Provider")}
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => {
                        setIsCreating(false);
                        setEditingId(null);
                        setFormData({ provider: "openai", api_key: "", is_active: true });
                      }}
                    >
                      Cancel
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          )}

          {/* Provider List */}
          {isLoading ? (
            <div className="space-y-4">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-32 rounded-lg bg-muted animate-pulse" />
              ))}
            </div>
          ) : settings.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-16">
                <SettingsIcon className="h-16 w-16 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">No providers configured</h3>
                <p className="text-sm text-muted-foreground mb-4 text-center max-w-md">
                  Add your first AI provider to start creating workflows
                </p>
                <Button onClick={() => setIsCreating(true)}>
                  <Plus className="mr-2 h-4 w-4" />
                  Add Provider
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {settings.map((setting) => (
                <Card key={setting.id}>
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between">
                      <div className="space-y-1 flex-1">
                        <div className="flex items-center gap-3">
                          <h3 className="text-lg font-semibold">{getProviderName(setting.provider)}</h3>
                          <Badge variant="secondary">{setting.provider}</Badge>
                          <span suppressHydrationWarning>
                          {setting.is_active ? (
                            <Badge className="bg-green-100 text-green-800">
                              <CheckCircle className="mr-1 h-3 w-3" />
                              Active
                            </Badge>
                          ) : (
                            <Badge variant="outline" className="text-gray-500">
                              <XCircle className="mr-1 h-3 w-3" />
                              Inactive
                            </Badge>
                          )}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 text-sm text-muted-foreground" suppressHydrationWarning>
                          <span>ID: {setting.id.slice(0, 8)}</span>
                          {setting.last_tested_at && (
                            <>
                              <span>•</span>
                              <span>Last tested: {new Date(setting.last_tested_at).toLocaleDateString()}</span>
                              {setting.test_status && (
                                <>
                                  <span>•</span>
                                  <span className={setting.test_status === "success" ? "text-green-600" : "text-red-600"}>
                                    {setting.test_status}
                                  </span>
                                </>
                              )}
                            </>
                          )}
                        </div>
                      </div>

                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleEdit(setting)}
                        >
                          <Edit className="h-4 w-4 mr-1" />
                          Edit
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => testMutation.mutate(setting.id)}
                          disabled={testMutation.isPending}
                        >
                          Test
                        </Button>
                        <Button
                          variant={setting.is_active ? "outline" : "default"}
                          size="sm"
                          onClick={() =>
                            toggleActiveMutation.mutate({ id: setting.id, activate: !setting.is_active })
                          }
                        >
                          {setting.is_active ? "Deactivate" : "Activate"}
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => deleteMutation.mutate(setting.id)}
                          disabled={deleteMutation.isPending}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
            </>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
}
