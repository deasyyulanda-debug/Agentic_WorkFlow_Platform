"use client";

import { useQuery } from "@tanstack/react-query";
import { settingsApi } from "@/lib/api/settings";
import { workflowsApi } from "@/lib/api/workflows";
import { runsApi } from "@/lib/api/runs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Activity, Workflow, Settings, PlayCircle, CheckCircle, XCircle, Clock } from "lucide-react";
import { formatRelativeTime, getStatusColor, getProviderName } from "@/lib/utils";
import Link from "next/link";
import { Header } from "@/components/layout/header";
import { Footer } from "@/components/layout/footer";

export default function DashboardPage() {
  const { data: settings, isLoading: settingsLoading } = useQuery({
    queryKey: ["settings"],
    queryFn: () => settingsApi.list({}),
  });

  const { data: workflows, isLoading: workflowsLoading } = useQuery({
    queryKey: ["workflows"],
    queryFn: () => workflowsApi.list({}),
  });

  const { data: runs, isLoading: runsLoading } = useQuery({
    queryKey: ["runs"],
    queryFn: () => runsApi.list({}),
  });

  const activeSettings = settings?.filter((s) => s.is_active) || [];
  const activeWorkflows = workflows?.filter((w) => w.is_active) || [];
  const recentRuns = runs?.slice(0, 5) || [];

  const runsByStatus = runs?.reduce((acc, run) => {
    acc[run.status] = (acc[run.status] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const stats = [
    {
      title: "Active Providers",
      value: activeSettings.length,
      icon: Settings,
      description: `${settings?.length || 0} total configured`,
      gradient: "from-blue-500 to-cyan-500",
      iconBg: "bg-blue-100 dark:bg-blue-950",
      iconColor: "text-blue-600 dark:text-blue-400",
      borderColor: "border-l-blue-500",
    },
    {
      title: "Active Workflows",
      value: activeWorkflows.length,
      icon: Workflow,
      description: `${workflows?.length || 0} total created`,
      gradient: "from-purple-500 to-pink-500",
      iconBg: "bg-purple-100 dark:bg-purple-950",
      iconColor: "text-purple-600 dark:text-purple-400",
      borderColor: "border-l-purple-500",
    },
    {
      title: "Total Runs",
      value: runs?.length || 0,
      icon: Activity,
      description: `${runsByStatus?.completed || 0} completed`,
      gradient: "from-orange-500 to-red-500",
      iconBg: "bg-orange-100 dark:bg-orange-950",
      iconColor: "text-orange-600 dark:text-orange-400",
      borderColor: "border-l-orange-500",
    },
    {
      title: "Success Rate",
      value: runs?.length ? `${Math.round(((runsByStatus?.completed || 0) / runs.length) * 100)}%` : "0%",
      icon: CheckCircle,
      description: `${runsByStatus?.failed || 0} failed`,
      gradient: "from-green-500 to-emerald-500",
      iconBg: "bg-green-100 dark:bg-green-950",
      iconColor: "text-green-600 dark:text-green-400",
      borderColor: "border-l-green-500",
    },
  ];

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1">
        <div className="container py-8">
          <div className="mb-8">
            <h1 className="text-4xl font-bold">Dashboard</h1>
            <p className="mt-2 text-muted-foreground">Monitor your agentic workflow platform</p>
          </div>

          {/* Stats Grid */}
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mb-8">
            {stats.map((stat) => {
              const Icon = stat.icon;
              return (
                <Card 
                  key={stat.title} 
                  className={`relative overflow-hidden border-l-4 ${stat.borderColor} hover:shadow-lg transition-all duration-300 group`}
                >
                  <div className="absolute top-0 right-0 w-32 h-32 opacity-5">
                    <div className={`w-full h-full bg-gradient-to-br ${stat.gradient} blur-2xl`} />
                  </div>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
                    <CardTitle className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                      {stat.title}
                    </CardTitle>
                    <div className={`p-3 rounded-xl ${stat.iconBg} group-hover:scale-110 transition-transform duration-300`}>
                      <Icon className={`h-5 w-5 ${stat.iconColor}`} />
                    </div>
                  </CardHeader>
                  <CardContent className="text-center">
                    <div className={`text-5xl font-extrabold bg-gradient-to-r ${stat.gradient} bg-clip-text text-transparent mb-2`}>
                      {stat.value}
                    </div>
                    <p className="text-xs text-gray-600 dark:text-gray-400 font-medium">
                      {stat.description}
                    </p>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          <div className="grid gap-8 md:grid-cols-2">
            {/* Recent Runs */}
            <Card>
              <CardHeader>
                <CardTitle>Recent Runs</CardTitle>
                <CardDescription>Latest workflow executions</CardDescription>
              </CardHeader>
              <CardContent>
                {runsLoading ? (
                  <div className="space-y-3">
                    {[...Array(3)].map((_, i) => (
                      <div key={i} className="h-20 rounded-md bg-muted animate-pulse" />
                    ))}
                  </div>
                ) : recentRuns.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-8 text-center">
                    <PlayCircle className="h-12 w-12 text-muted-foreground mb-3" />
                    <p className="text-sm text-muted-foreground">No runs yet. Create and execute a workflow to get started.</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {recentRuns.map((run) => (
                      <Link
                        key={run.id}
                        href={`/runs/${run.id}`}
                        className="flex items-center justify-between p-3 rounded-lg border hover:bg-accent transition-colors"
                      >
                        <div className="space-y-1">
                          <p className="text-sm font-medium leading-none">
                            {run.workflow?.name || `Run ${run.id.slice(0, 8)}`}
                          </p>
                          <p className="text-xs text-muted-foreground">{formatRelativeTime(run.created_at)}</p>
                        </div>
                        <Badge className={getStatusColor(run.status)}>{run.status}</Badge>
                      </Link>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Active Workflows */}
            <Card>
              <CardHeader>
                <CardTitle>Active Workflows</CardTitle>
                <CardDescription>Ready to execute</CardDescription>
              </CardHeader>
              <CardContent>
                {workflowsLoading ? (
                  <div className="space-y-3">
                    {[...Array(3)].map((_, i) => (
                      <div key={i} className="h-20 rounded-md bg-muted animate-pulse" />
                    ))}
                  </div>
                ) : activeWorkflows.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-8 text-center">
                    <Workflow className="h-12 w-12 text-muted-foreground mb-3" />
                    <p className="text-sm text-muted-foreground">No active workflows. Create one to start automating.</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {activeWorkflows.slice(0, 5).map((workflow) => (
                      <Link
                        key={workflow.id}
                        href={`/workflows/${workflow.id}`}
                        className="flex items-center justify-between p-3 rounded-lg border hover:bg-accent transition-colors"
                      >
                        <div className="space-y-1">
                          <p className="text-sm font-medium leading-none">{workflow.name}</p>
                          <p className="text-xs text-muted-foreground">{workflow.definition?.steps?.length || 0} steps</p>
                        </div>
                        <Badge variant="secondary">{workflow.persona}</Badge>
                      </Link>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}
