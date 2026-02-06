"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ragApi } from "@/lib/api/rag";
import type {
  RAGPipeline,
  RAGPipelineConfig,
  RAGConfigOptions,
  RAGQueryResponse,
} from "@/lib/api/rag";
import { Header } from "@/components/layout/header";
import { Footer } from "@/components/layout/footer";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Database,
  Upload,
  Search,
  Trash2,
  Plus,
  FileText,
  Layers,
  Zap,
  CheckCircle,
  AlertCircle,
  Loader2,
} from "lucide-react";
import { toast } from "sonner";

type ViewMode = "list" | "create" | "detail";

export default function RAGPipelinePage() {
  const queryClient = useQueryClient();
  const [viewMode, setViewMode] = useState<ViewMode>("list");
  const [selectedPipeline, setSelectedPipeline] = useState<RAGPipeline | null>(
    null
  );

  // Form state for creating pipeline
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [chunkStrategy, setChunkStrategy] = useState("recursive");
  const [chunkSize, setChunkSize] = useState(1000);
  const [chunkOverlap, setChunkOverlap] = useState(200);
  const [embeddingProvider, setEmbeddingProvider] = useState("chroma_default");
  const [topK, setTopK] = useState(5);

  // Query / Upload state
  const [queryText, setQueryText] = useState("");
  const [queryResults, setQueryResults] = useState<RAGQueryResponse | null>(
    null
  );

  // Fetch config options
  const { data: configOptions } = useQuery<RAGConfigOptions>({
    queryKey: ["rag-config"],
    queryFn: ragApi.getConfigOptions,
  });

  // Fetch pipelines
  const { data: pipelines, isLoading: pipelinesLoading } = useQuery<
    RAGPipeline[]
  >({
    queryKey: ["rag-pipelines"],
    queryFn: ragApi.listPipelines,
  });

  // Create pipeline mutation
  const createMutation = useMutation({
    mutationFn: (config: RAGPipelineConfig) => ragApi.createPipeline(config),
    onSuccess: (pipeline) => {
      toast.success(`Pipeline "${pipeline.name}" created!`);
      queryClient.invalidateQueries({ queryKey: ["rag-pipelines"] });
      setSelectedPipeline(pipeline);
      setViewMode("detail");
      resetForm();
    },
    onError: (error: any) => {
      toast.error(
        error.response?.data?.detail || "Failed to create pipeline"
      );
    },
  });

  // Delete pipeline mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => ragApi.deletePipeline(id),
    onSuccess: () => {
      toast.success("Pipeline deleted");
      queryClient.invalidateQueries({ queryKey: ["rag-pipelines"] });
      setSelectedPipeline(null);
      setViewMode("list");
    },
    onError: (error: any) => {
      toast.error(
        error.response?.data?.detail || "Failed to delete pipeline"
      );
    },
  });

  // Upload document mutation
  const uploadMutation = useMutation({
    mutationFn: ({ pipelineId, file }: { pipelineId: string; file: File }) =>
      ragApi.uploadDocument(pipelineId, file),
    onSuccess: (result) => {
      toast.success(result.message);
      queryClient.invalidateQueries({ queryKey: ["rag-pipelines"] });
      if (selectedPipeline) {
        ragApi.getPipeline(selectedPipeline.id).then(setSelectedPipeline);
      }
    },
    onError: (error: any) => {
      toast.error(
        error.response?.data?.detail || "Failed to upload document"
      );
    },
  });

  // Query mutation
  const queryMutation = useMutation({
    mutationFn: ({
      pipelineId,
      query,
    }: {
      pipelineId: string;
      query: string;
    }) => ragApi.queryPipeline(pipelineId, query, topK),
    onSuccess: (result) => {
      setQueryResults(result);
    },
    onError: (error: any) => {
      toast.error(
        error.response?.data?.detail || "Query failed"
      );
    },
  });

  const resetForm = () => {
    setName("");
    setDescription("");
    setChunkStrategy("recursive");
    setChunkSize(1000);
    setChunkOverlap(200);
    setEmbeddingProvider("chroma_default");
    setTopK(5);
  };

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      toast.error("Please enter a pipeline name");
      return;
    }
    createMutation.mutate({
      name,
      description,
      chunking: {
        strategy: chunkStrategy,
        chunk_size: chunkSize,
        chunk_overlap: chunkOverlap,
      },
      embedding: { provider: embeddingProvider },
      vector_store: { store_type: "chroma" },
      retrieval: { top_k: topK },
    });
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!selectedPipeline || !e.target.files?.[0]) return;
    const file = e.target.files[0];
    uploadMutation.mutate({ pipelineId: selectedPipeline.id, file });
  };

  const handleQuery = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPipeline || !queryText.trim()) return;
    queryMutation.mutate({
      pipelineId: selectedPipeline.id,
      query: queryText,
    });
  };

  const statusBadge = (status: string) => {
    switch (status) {
      case "ready":
        return (
          <Badge className="bg-green-100 text-green-800">
            <CheckCircle className="mr-1 h-3 w-3" /> Ready
          </Badge>
        );
      case "ingesting":
        return (
          <Badge className="bg-blue-100 text-blue-800">
            <Loader2 className="mr-1 h-3 w-3 animate-spin" /> Ingesting
          </Badge>
        );
      case "error":
        return (
          <Badge className="bg-red-100 text-red-800">
            <AlertCircle className="mr-1 h-3 w-3" /> Error
          </Badge>
        );
      default:
        return (
          <Badge className="bg-gray-100 text-gray-800">
            <Database className="mr-1 h-3 w-3" /> Created
          </Badge>
        );
    }
  };

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1">
        <div className="container py-8 max-w-6xl">
          {/* Page Header */}
          <div className="mb-8 flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold flex items-center gap-3">
                <Database className="h-8 w-8" />
                RAG Pipeline Builder
              </h1>
              <p className="mt-2 text-muted-foreground">
                Build retrieval-augmented generation pipelines — Upload
                documents, configure chunking & embeddings, query with
                similarity search
              </p>
            </div>
            {viewMode !== "create" && (
              <Button onClick={() => setViewMode("create")}>
                <Plus className="mr-2 h-4 w-4" />
                New Pipeline
              </Button>
            )}
          </div>

          {/* Pipeline List View */}
          {viewMode === "list" && (
            <div className="space-y-4">
              {/* Stats */}
              <div className="grid grid-cols-3 gap-4">
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-2xl font-bold">
                      {pipelines?.length || 0}
                    </div>
                    <p className="text-sm text-muted-foreground">
                      Total Pipelines
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-2xl font-bold">
                      {pipelines?.filter((p) => p.status === "ready").length ||
                        0}
                    </div>
                    <p className="text-sm text-muted-foreground">
                      Ready for Queries
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-2xl font-bold">
                      {pipelines?.reduce(
                        (acc, p) => acc + p.document_count,
                        0
                      ) || 0}
                    </div>
                    <p className="text-sm text-muted-foreground">
                      Documents Ingested
                    </p>
                  </CardContent>
                </Card>
              </div>

              {/* Pipeline Cards */}
              {pipelinesLoading ? (
                <Card>
                  <CardContent className="py-12 text-center text-muted-foreground">
                    <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2" />
                    Loading pipelines...
                  </CardContent>
                </Card>
              ) : !pipelines?.length ? (
                <Card>
                  <CardContent className="py-12 text-center text-muted-foreground">
                    <Database className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <h3 className="text-lg font-semibold mb-2">
                      No RAG Pipelines Yet
                    </h3>
                    <p className="mb-4">
                      Create your first pipeline to start ingesting documents
                      and querying with AI
                    </p>
                    <Button onClick={() => setViewMode("create")}>
                      <Plus className="mr-2 h-4 w-4" />
                      Create Pipeline
                    </Button>
                  </CardContent>
                </Card>
              ) : (
                <div className="grid gap-4">
                  {pipelines.map((pipeline) => (
                    <Card
                      key={pipeline.id}
                      className="cursor-pointer hover:border-primary/50 transition-colors"
                      onClick={() => {
                        setSelectedPipeline(pipeline);
                        setViewMode("detail");
                        setQueryResults(null);
                      }}
                    >
                      <CardContent className="py-4">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-4">
                            <Database className="h-8 w-8 text-primary" />
                            <div>
                              <h3 className="font-semibold text-lg">
                                {pipeline.name}
                              </h3>
                              <p className="text-sm text-muted-foreground">
                                {pipeline.description || "No description"}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-4">
                            <div className="text-right text-sm">
                              <div>
                                {pipeline.document_count} docs •{" "}
                                {pipeline.chunk_count} chunks
                              </div>
                              <div className="text-muted-foreground">
                                {new Date(
                                  pipeline.created_at
                                ).toLocaleDateString()}
                              </div>
                            </div>
                            {statusBadge(pipeline.status)}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Create Pipeline View */}
          {viewMode === "create" && (
            <form onSubmit={handleCreate} className="space-y-6">
              <Button
                type="button"
                variant="ghost"
                onClick={() => setViewMode("list")}
              >
                ← Back to Pipelines
              </Button>

              {/* Basic Info */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Database className="h-5 w-5" />
                    Pipeline Configuration
                  </CardTitle>
                  <CardDescription>
                    Configure your RAG pipeline settings
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="name">Pipeline Name *</Label>
                      <Input
                        id="name"
                        placeholder="My RAG Pipeline"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="description">Description</Label>
                      <Input
                        id="description"
                        placeholder="What is this pipeline for?"
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Chunking Configuration */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Layers className="h-5 w-5" />
                    Document Chunking
                  </CardTitle>
                  <CardDescription>
                    How documents are split into searchable chunks
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>Chunking Strategy</Label>
                    <select
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      value={chunkStrategy}
                      onChange={(e) => setChunkStrategy(e.target.value)}
                    >
                      {configOptions?.chunking_strategies?.map((s) => (
                        <option key={s.value} value={s.value}>
                          {s.label} — {s.description}
                        </option>
                      )) || (
                        <>
                          <option value="recursive">
                            Recursive — Recommended
                          </option>
                          <option value="fixed_size">
                            Fixed Size
                          </option>
                          <option value="sentence">Sentence</option>
                          <option value="paragraph">Paragraph</option>
                        </>
                      )}
                    </select>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Chunk Size (characters)</Label>
                      <Input
                        type="number"
                        min={100}
                        max={10000}
                        value={chunkSize}
                        onChange={(e) =>
                          setChunkSize(parseInt(e.target.value) || 1000)
                        }
                      />
                      <p className="text-xs text-muted-foreground">
                        Target size for each chunk (100–10,000)
                      </p>
                    </div>
                    <div className="space-y-2">
                      <Label>Chunk Overlap (characters)</Label>
                      <Input
                        type="number"
                        min={0}
                        max={2000}
                        value={chunkOverlap}
                        onChange={(e) =>
                          setChunkOverlap(parseInt(e.target.value) || 200)
                        }
                      />
                      <p className="text-xs text-muted-foreground">
                        Overlap between consecutive chunks (0–2,000)
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Embedding Configuration */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Zap className="h-5 w-5" />
                    Embedding & Retrieval
                  </CardTitle>
                  <CardDescription>
                    How documents are embedded and retrieved
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>Embedding Provider</Label>
                    <select
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      value={embeddingProvider}
                      onChange={(e) => setEmbeddingProvider(e.target.value)}
                    >
                      {configOptions?.embedding_providers?.map((p) => (
                        <option key={p.value} value={p.value}>
                          {p.label}
                        </option>
                      )) || (
                        <>
                          <option value="chroma_default">
                            ChromaDB Default (all-MiniLM-L6-v2)
                          </option>
                          <option value="openai">
                            OpenAI Embeddings
                          </option>
                        </>
                      )}
                    </select>
                  </div>
                  <div className="space-y-2">
                    <Label>Top-K Results</Label>
                    <Input
                      type="number"
                      min={1}
                      max={50}
                      value={topK}
                      onChange={(e) =>
                        setTopK(parseInt(e.target.value) || 5)
                      }
                    />
                    <p className="text-xs text-muted-foreground">
                      Number of results returned per query (1–50)
                    </p>
                  </div>
                </CardContent>
              </Card>

              {/* Actions */}
              <div className="flex justify-end gap-3">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setViewMode("list")}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={createMutation.isPending}>
                  {createMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    <>
                      <Plus className="mr-2 h-4 w-4" />
                      Create Pipeline
                    </>
                  )}
                </Button>
              </div>
            </form>
          )}

          {/* Pipeline Detail View */}
          {viewMode === "detail" && selectedPipeline && (
            <div className="space-y-6">
              <Button
                type="button"
                variant="ghost"
                onClick={() => {
                  setViewMode("list");
                  setSelectedPipeline(null);
                  setQueryResults(null);
                }}
              >
                ← Back to Pipelines
              </Button>

              {/* Pipeline Header */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-2xl flex items-center gap-3">
                        <Database className="h-6 w-6" />
                        {selectedPipeline.name}
                      </CardTitle>
                      <CardDescription className="mt-1">
                        {selectedPipeline.description || "No description"}
                      </CardDescription>
                    </div>
                    <div className="flex items-center gap-3">
                      {statusBadge(selectedPipeline.status)}
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() =>
                          deleteMutation.mutate(selectedPipeline.id)
                        }
                      >
                        <Trash2 className="mr-1 h-4 w-4" /> Delete
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-4 gap-4 text-sm">
                    <div>
                      <div className="text-muted-foreground">Documents</div>
                      <div className="text-lg font-bold">
                        {selectedPipeline.document_count}
                      </div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Chunks</div>
                      <div className="text-lg font-bold">
                        {selectedPipeline.chunk_count}
                      </div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Strategy</div>
                      <div className="text-lg font-bold capitalize">
                        {selectedPipeline.config?.chunking?.strategy ||
                          "recursive"}
                      </div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Embedding</div>
                      <div className="text-lg font-bold">
                        {selectedPipeline.config?.embedding?.provider ===
                        "openai"
                          ? "OpenAI"
                          : "Default"}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Upload Document */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Upload className="h-5 w-5" />
                    Upload Document
                  </CardTitle>
                  <CardDescription>
                    Upload a document to ingest into this pipeline (TXT, CSV,
                    MD, PDF, JSON — max 10MB)
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-4">
                    <Input
                      type="file"
                      accept=".txt,.csv,.md,.pdf,.json"
                      onChange={handleFileUpload}
                      disabled={uploadMutation.isPending}
                      className="max-w-md"
                    />
                    {uploadMutation.isPending && (
                      <div className="flex items-center text-sm text-muted-foreground">
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Processing document...
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Query Pipeline */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Search className="h-5 w-5" />
                    Query Pipeline
                  </CardTitle>
                  <CardDescription>
                    Search for relevant document chunks using semantic similarity
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <form onSubmit={handleQuery} className="flex gap-3">
                    <Input
                      placeholder="Enter your query..."
                      value={queryText}
                      onChange={(e) => setQueryText(e.target.value)}
                      disabled={
                        selectedPipeline.status !== "ready" ||
                        queryMutation.isPending
                      }
                      className="flex-1"
                    />
                    <Button
                      type="submit"
                      disabled={
                        selectedPipeline.status !== "ready" ||
                        queryMutation.isPending ||
                        !queryText.trim()
                      }
                    >
                      {queryMutation.isPending ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <>
                          <Search className="mr-2 h-4 w-4" />
                          Search
                        </>
                      )}
                    </Button>
                  </form>

                  {selectedPipeline.status !== "ready" && (
                    <p className="text-sm text-muted-foreground">
                      Upload at least one document to enable querying
                    </p>
                  )}

                  {/* Query Results */}
                  {queryResults && (
                    <div className="space-y-3 mt-4">
                      <h4 className="font-semibold">
                        Results ({queryResults.total_results} found)
                      </h4>
                      {queryResults.results.map((result, i) => (
                        <Card key={i} className="bg-muted/50">
                          <CardContent className="py-3">
                            <div className="flex items-start justify-between mb-2">
                              <Badge variant="outline">
                                <FileText className="mr-1 h-3 w-3" />
                                {result.metadata?.file_name || "Unknown"}
                              </Badge>
                              {result.score !== null && (
                                <Badge variant="secondary">
                                  Score: {(result.score * 100).toFixed(1)}%
                                </Badge>
                              )}
                            </div>
                            <p className="text-sm whitespace-pre-wrap">
                              {result.content}
                            </p>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
}
