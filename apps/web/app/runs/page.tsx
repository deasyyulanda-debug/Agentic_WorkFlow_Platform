"use client";

import { useQuery } from "@tanstack/react-query";
import { runsApi } from "@/lib/api/runs";
import { useState } from "react";
import Link from "next/link";
import { Header } from "@/components/layout/header";
import { Footer } from "@/components/layout/footer";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Activity, Search, PlayCircle } from "lucide-react";
import { formatRelativeTime, getStatusColor } from "@/lib/utils";

export default function RunsPage() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  const { data, isLoading } = useQuery({
    queryKey: ["runs", statusFilter],
    queryFn: () => runsApi.list({ 
      status_filter: statusFilter === "all" ? undefined : statusFilter as any 
    }),
    refetchInterval: 5000, // Poll every 5 seconds for running workflows
  });

  const runs = data || [];

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1">
        <div className="container py-8">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-4xl font-bold">Runs</h1>
              <p className="mt-2 text-muted-foreground">Monitor workflow executions</p>
            </div>
            <Link href="/runs/new">
              <Button size="lg">
                <PlayCircle className="mr-2 h-4 w-4" />
                Execute Workflow
              </Button>
            </Link>
          </div>

          {/* Filters */}
          <div className="flex items-center gap-4 mb-6">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search runs..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
            <div className="flex gap-2">
              {["all", "queued", "running", "completed", "failed"].map((status) => (
                <Button
                  key={status}
                  variant={statusFilter === status ? "default" : "outline"}
                  onClick={() => setStatusFilter(status)}
                  size="sm"
                >
                  {status.charAt(0).toUpperCase() + status.slice(1)}
                </Button>
              ))}
            </div>
          </div>

          {/* Runs List */}
          {isLoading ? (
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-24 rounded-lg bg-muted animate-pulse" />
              ))}
            </div>
          ) : runs.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-16">
                <Activity className="h-16 w-16 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">No runs found</h3>
                <p className="text-sm text-muted-foreground mb-4 text-center max-w-md">
                  Execute a workflow to see runs here
                </p>
                <Link href="/runs/new">
                  <Button>
                    <PlayCircle className="mr-2 h-4 w-4" />
                    Execute Workflow
                  </Button>
                </Link>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {runs.map((run) => (
                <Link key={run.id} href={`/runs/${run.id}`}>
                  <Card className="hover:shadow-lg transition-shadow">
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between">
                        <div className="space-y-1 flex-1">
                          <div className="flex items-center gap-3">
                            <h3 className="text-lg font-semibold">
                              {run.workflow?.name || `Run ${run.id.slice(0, 8)}`}
                            </h3>
                            <Badge className={getStatusColor(run.status)}>{run.status}</Badge>
                          </div>
                          <div className="flex items-center gap-4 text-sm text-muted-foreground">
                            <span>Mode: {run.mode}</span>
                            <span>•</span>
                            <span>Started {formatRelativeTime(run.created_at)}</span>
                            {run.execution_time_ms && (
                              <>
                                <span>•</span>
                                <span>{(run.execution_time_ms / 1000).toFixed(2)}s</span>
                              </>
                            )}
                          </div>
                        </div>
                        <div className="flex flex-col items-end gap-2">
                          {run.result?.steps_completed !== undefined && (
                            <span className="text-sm text-muted-foreground">
                              {run.result.steps_completed} / {run.workflow?.steps.length || 0} steps
                            </span>
                          )}
                          <Button variant="outline" size="sm">
                            View Details
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              ))}
            </div>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
}
