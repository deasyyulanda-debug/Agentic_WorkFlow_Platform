"use client";

import { useQuery, useMutation } from "@tanstack/react-query";
import { workflowsApi } from "@/lib/api/workflows";
import { runsApi } from "@/lib/api/runs";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Header } from "@/components/layout/header";
import { Footer } from "@/components/layout/footer";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Workflow, Plus, Search, CheckCircle, XCircle, Play } from "lucide-react";
import { formatRelativeTime } from "@/lib/utils";
import { toast } from "sonner";

export default function WorkflowsPage() {
  const router = useRouter();
  const [search, setSearch] = useState("");
  const [activeFilter, setActiveFilter] = useState<"all" | "active" | "inactive">("all");

  const { data, isLoading } = useQuery({
    queryKey: ["workflows", search],
    queryFn: () => workflowsApi.list({ search }),
  });

  const executeWorkflow = useMutation({
    mutationFn: (workflowId: string) => 
      runsApi.executeAsync({ 
        workflow_id: workflowId,
        input_data: {},
        mode: "test_run"
      }),
    onSuccess: (data) => {
      toast.success("Workflow execution started!");
      router.push(`/runs`);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to execute workflow");
    },
  });

  const workflows = data || [];
  const filteredWorkflows = workflows.filter((w) => {
    if (activeFilter === "active") return w.is_active;
    if (activeFilter === "inactive") return !w.is_active;
    return true;
  });

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1">
        <div className="container py-8">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-4xl font-bold">Workflows</h1>
              <p className="mt-2 text-muted-foreground">Create and manage your AI workflows</p>
            </div>
            <Link href="/workflows/new">
              <Button size="lg">
                <Plus className="mr-2 h-4 w-4" />
                New Workflow
              </Button>
            </Link>
          </div>

          {/* Filters */}
          <div className="flex items-center gap-4 mb-6">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search workflows..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
            <div className="flex gap-2">
              <Button
                variant={activeFilter === "all" ? "default" : "outline"}
                onClick={() => setActiveFilter("all")}
                size="sm"
              >
                All ({workflows.length})
              </Button>
              <Button
                variant={activeFilter === "active" ? "default" : "outline"}
                onClick={() => setActiveFilter("active")}
                size="sm"
              >
                Active ({workflows.filter((w) => w.is_active).length})
              </Button>
              <Button
                variant={activeFilter === "inactive" ? "default" : "outline"}
                onClick={() => setActiveFilter("inactive")}
                size="sm"
              >
                Inactive ({workflows.filter((w) => !w.is_active).length})
              </Button>
            </div>
          </div>

          {/* Workflows Grid */}
          {isLoading ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="h-48 rounded-lg bg-muted animate-pulse" />
              ))}
            </div>
          ) : filteredWorkflows.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-16">
                <Workflow className="h-16 w-16 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">No workflows found</h3>
                <p className="text-sm text-muted-foreground mb-4 text-center max-w-md">
                  {search
                    ? "Try adjusting your search or filter criteria"
                    : "Get started by creating your first workflow"}
                </p>
                <Link href="/workflows/new">
                  <Button>
                    <Plus className="mr-2 h-4 w-4" />
                    Create Workflow
                  </Button>
                </Link>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {filteredWorkflows.map((workflow) => (
                <Card key={workflow.id} className="hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <CardTitle className="text-lg">{workflow.name}</CardTitle>
                      {workflow.is_active ? (
                        <CheckCircle className="h-5 w-5 text-green-500" />
                      ) : (
                        <XCircle className="h-5 w-5 text-gray-400" />
                      )}
                    </div>
                    {workflow.description && (
                      <CardDescription className="line-clamp-2">{workflow.description}</CardDescription>
                    )}
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Steps:</span>
                        <Badge variant="secondary">{workflow.definition?.steps?.length || 0}</Badge>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Persona:</span>
                        <Badge variant="outline">{workflow.persona}</Badge>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Updated {formatRelativeTime(workflow.updated_at)}
                      </div>
                      <div className="flex gap-2 pt-2">
                        <Link href={`/workflows/${workflow.id}`} className="flex-1">
                          <Button variant="outline" size="sm" className="w-full">
                            View
                          </Button>
                        </Link>
                        <Button 
                          size="sm" 
                          className="flex-1"
                          onClick={() => executeWorkflow.mutate(workflow.id)}
                          disabled={executeWorkflow.isPending}
                        >
                          <Play className="mr-1 h-3 w-3" />
                          {executeWorkflow.isPending ? "Starting..." : "Run"}
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
}
