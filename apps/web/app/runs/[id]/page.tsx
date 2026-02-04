"use client";

import { useQuery } from "@tanstack/react-query";
import { runsApi } from "@/lib/api/runs";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Header } from "@/components/layout/header";
import { Footer } from "@/components/layout/footer";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, Clock, CheckCircle, XCircle, AlertCircle } from "lucide-react";
import { formatRelativeTime, getStatusColor } from "@/lib/utils";

export default function RunDetailPage() {
  const params = useParams();
  const runId = params.id as string;

  const { data: run, isLoading } = useQuery({
    queryKey: ["run", runId],
    queryFn: () => runsApi.getById(runId),
    refetchInterval: (data) => {
      // Poll while running
      return data?.status === "running" || data?.status === "queued" ? 2000 : false;
    },
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case "failed":
        return <XCircle className="h-5 w-5 text-red-500" />;
      case "running":
        return <Clock className="h-5 w-5 text-blue-500 animate-spin" />;
      default:
        return <AlertCircle className="h-5 w-5 text-yellow-500" />;
    }
  };

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1">
        <div className="container py-8 max-w-5xl">
          {/* Back button */}
          <Link href="/runs" className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground mb-6">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Runs
          </Link>

          {isLoading ? (
            <div className="space-y-4">
              <div className="h-32 rounded-lg bg-muted animate-pulse" />
              <div className="h-64 rounded-lg bg-muted animate-pulse" />
            </div>
          ) : !run ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-16">
                <AlertCircle className="h-16 w-16 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">Run not found</h3>
                <p className="text-sm text-muted-foreground">This workflow run does not exist</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-6">
              {/* Header */}
              <Card>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <CardTitle className="text-2xl">Run {run.id.slice(0, 8)}</CardTitle>
                      <CardDescription>
                        Started {formatRelativeTime(run.created_at)}
                      </CardDescription>
                    </div>
                    <div className="flex items-center gap-2">
                      {getStatusIcon(run.status)}
                      <Badge variant={getStatusColor(run.status) as any}>
                        {run.status}
                      </Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <div className="text-sm text-muted-foreground">Workflow</div>
                      <div className="font-medium">{run.workflow_id.slice(0, 8)}</div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">Mode</div>
                      <div className="font-medium">{run.mode}</div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">Started</div>
                      <div className="font-medium">
                        {new Date(run.created_at).toLocaleString()}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">Updated</div>
                      <div className="font-medium">
                        {new Date(run.updated_at).toLocaleString()}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Input Data */}
              {run.input_data && Object.keys(run.input_data).length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Input Data</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <pre className="bg-muted p-4 rounded-lg overflow-x-auto text-sm">
                      {JSON.stringify(run.input_data, null, 2)}
                    </pre>
                  </CardContent>
                </Card>
              )}

              {/* Output Data */}
              {run.output_data && Object.keys(run.output_data).length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Output Data</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <pre className="bg-muted p-4 rounded-lg overflow-x-auto text-sm">
                      {JSON.stringify(run.output_data, null, 2)}
                    </pre>
                  </CardContent>
                </Card>
              )}

              {/* Error */}
              {run.error && (
                <Card className="border-red-200">
                  <CardHeader>
                    <CardTitle className="text-red-600">Error</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <pre className="bg-red-50 p-4 rounded-lg overflow-x-auto text-sm text-red-900">
                      {run.error}
                    </pre>
                  </CardContent>
                </Card>
              )}

              {/* Metrics */}
              {run.metrics && Object.keys(run.metrics).length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Metrics</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <pre className="bg-muted p-4 rounded-lg overflow-x-auto text-sm">
                      {JSON.stringify(run.metrics, null, 2)}
                    </pre>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
}
