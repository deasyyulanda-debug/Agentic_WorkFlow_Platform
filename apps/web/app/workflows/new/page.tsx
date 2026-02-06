"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { workflowsApi } from "@/lib/api/workflows";
import { settingsApi } from "@/lib/api/settings";
import { Header } from "@/components/layout/header";
import { Footer } from "@/components/layout/footer";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Plus, Trash2, ArrowLeft } from "lucide-react";
import { toast } from "sonner";
import Link from "next/link";
import type { WorkflowCreate, Persona } from "@/types/api";
import { getProviderName } from "@/lib/utils";

export default function NewWorkflowPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [persona, setPersona] = useState<Persona>("researcher");
  const [steps, setSteps] = useState<Array<{
    prompt: string;
    settings_id: string;
    model?: string;
    type?: string;
  }>>([
    { prompt: "", settings_id: "", model: "", type: "prompt" },
  ]);
  const [availableModels, setAvailableModels] = useState<Record<number, string[]>>({});

  const { data: settingsData } = useQuery({
    queryKey: ["settings"],
    queryFn: () => settingsApi.list({}),
  });

  const createMutation = useMutation({
    mutationFn: (data: WorkflowCreate) => workflowsApi.create(data),
    onSuccess: (data) => {
      toast.success("Workflow created successfully!");
      queryClient.invalidateQueries({ queryKey: ["workflows"] });
      router.push("/workflows");
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to create workflow");
    },
  });

  const activeSettings = settingsData?.filter((s) => s.is_active) || [];

  const handleAddStep = () => {
    setSteps([
      ...steps,
      { prompt: "", settings_id: "", model: "", type: "prompt" },
    ]);
  };

  const handleRemoveStep = (index: number) => {
    if (steps.length === 1) {
      toast.error("Workflow must have at least one step");
      return;
    }
    setSteps(steps.filter((_, i) => i !== index));
  };

  const handleStepChange = async (index: number, field: string, value: any) => {
    const newSteps = [...steps];
    newSteps[index] = { ...newSteps[index], [field]: value };
    
    // If provider changed, fetch available models
    if (field === "settings_id" && value) {
      const selectedSetting = activeSettings.find(s => s.id === value);
      if (selectedSetting) {
        try {
          const models = await settingsApi.getModels(selectedSetting.provider);
          setAvailableModels(prev => ({ ...prev, [index]: models }));
          // Reset model selection when provider changes
          newSteps[index].model = "";
        } catch (error) {
          console.error("Failed to fetch models:", error);
        }
      }
    }
    
    setSteps(newSteps);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!name.trim()) {
      toast.error("Please enter a workflow name");
      return;
    }

    if (steps.some((s) => !s.prompt.trim() || !s.settings_id)) {
      toast.error("All steps must have a prompt and provider");
      return;
    }

    const workflowData: WorkflowCreate = {
      name,
      description,
      persona,
      definition: {
        steps: steps.map((step) => ({
          type: "prompt",
          template: step.prompt,
          settings_id: step.settings_id,
          model: step.model || undefined, // Include model if selected
        })),
      },
      is_active: true,
    };

    console.log("Creating workflow with data:", JSON.stringify(workflowData, null, 2));
    createMutation.mutate(workflowData);
  };

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1">
        <div className="container py-8 max-w-4xl">
          <div className="mb-8">
            <Link href="/workflows">
              <Button variant="ghost" size="sm" className="mb-4">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Workflows
              </Button>
            </Link>
            <h1 className="text-4xl font-bold">Create Workflow</h1>
            <p className="mt-2 text-muted-foreground">Design a multi-step AI workflow</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Basic Info */}
            <Card>
              <CardHeader>
                <CardTitle>Basic Information</CardTitle>
                <CardDescription>Configure your workflow details</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Name *</Label>
                  <Input
                    id="name"
                    placeholder="My Workflow"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    placeholder="What does this workflow do?"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    rows={3}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Persona (applies to all steps)</Label>
                  <select
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    value={persona}
                    onChange={(e) => setPersona(e.target.value as Persona)}
                  >
                    <option value="student">Student</option>
                    <option value="researcher">Researcher</option>
                    <option value="ml_engineer">ML Engineer</option>
                    <option value="data_scientist">Data Scientist</option>
                    <option value="ai_architect">AI Architect</option>
                  </select>
                </div>
              </CardContent>
            </Card>

            {/* Steps */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Workflow Steps</CardTitle>
                    <CardDescription>Define the sequence of AI operations</CardDescription>
                  </div>
                  <Button type="button" size="sm" onClick={handleAddStep}>
                    <Plus className="mr-2 h-4 w-4" />
                    Add Step
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {steps.map((step, index) => (
                  <div key={index} className="relative border rounded-lg p-4 space-y-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-semibold">Step {index + 1}</span>
                      {steps.length > 1 && (
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => handleRemoveStep(index)}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      )}
                    </div>

                    <div className="space-y-2">
                      <Label>Prompt *</Label>
                      <Textarea
                        placeholder="Enter your prompt for this step..."
                        value={step.prompt}
                        onChange={(e) => handleStepChange(index, "prompt", e.target.value)}
                        rows={3}
                        required
                      />
                    </div>

                    <div className="space-y-2">
                      <Label>Provider *</Label>
                      <select
                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                        value={step.settings_id}
                        onChange={(e) => handleStepChange(index, "settings_id", e.target.value)}
                        required
                      >
                        <option value="">Select provider...</option>
                        {activeSettings.map((setting) => (
                          <option key={setting.id} value={setting.id}>
                            {getProviderName(setting.provider)}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Model Selection - shown only when provider is selected */}
                    {step.settings_id && availableModels[index] && (
                      <div className="space-y-2">
                        <Label>Model (optional)</Label>
                        <select
                          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                          value={step.model || ""}
                          onChange={(e) => handleStepChange(index, "model", e.target.value)}
                        >
                          <option value="">Use default model</option>
                          {availableModels[index].map((model) => (
                            <option key={model} value={model}>
                              {model}
                            </option>
                          ))}
                        </select>
                        <p className="text-xs text-muted-foreground">
                          Choose a specific model or leave blank to use the provider default
                        </p>
                      </div>
                    )}
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Actions */}
            <div className="flex justify-end gap-3">
              <Link href="/workflows">
                <Button type="button" variant="outline">
                  Cancel
                </Button>
              </Link>
              <Button type="submit" disabled={createMutation.isPending}>
                {createMutation.isPending ? "Creating..." : "Create Workflow"}
              </Button>
            </div>
          </form>
        </div>
      </main>
      <Footer />
    </div>
  );
}
