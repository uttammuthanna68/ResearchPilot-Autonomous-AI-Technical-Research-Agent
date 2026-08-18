"use client";

import React, { useState, useEffect } from "react";

type ResearchMode = "hybrid" | "knowledge_base" | "web_research";

type StageStatus = "pending" | "running" | "completed" | "failed";

interface WorkflowStage {
  id: string;
  name: string;
  description: string;
  status: StageStatus;
}

interface DocumentSource {
  title: string;
  url: string;
  source: string;
  snippet: string;
}

interface EvidenceVerification {
  status: "supported" | "insufficient" | "conflicting";
  summary: string;
  verified_claims: string[];
  conflicting_claims: string[];
  missing_elements: string[];
}

interface HistoryItem {
  id: string;
  query: string;
  mode: ResearchMode;
  timestamp: string;
  source_count: number;
  verification_status: string;
}

interface ResearchResponse {
  id?: string;
  query: string;
  mode: ResearchMode;
  router?: { type: string; logic: string };
  steps: string[];
  evidence_verification: EvidenceVerification;
  research_loop_count?: number;
  followup_queries?: string[];
  documents: DocumentSource[];
  report: string;
}

const EXAMPLE_QUERIES = [
  "How does state persistence work in LangGraph using checkpointers?",
  "Compare vector similarity search indexing algorithms: HNSW vs IVF.",
  "What are the key architectural trade-offs of event-driven microservices?",
  "My code threw an error, how do I fix it?",
];

const INITIAL_STAGES: WorkflowStage[] = [
  { id: "analysis", name: "Query Analysis", description: "Classifies intent & evaluates technical scope", status: "pending" },
  { id: "planning", name: "Research Planning", description: "Formulates structured sub-task research plan", status: "pending" },
  { id: "tasks", name: "Research Tasks", description: "Expands sub-tasks into target search queries", status: "pending" },
  { id: "retrieval", name: "Retrieval & Search", description: "Parallel vector store & web search retrieval", status: "pending" },
  { id: "verification", name: "Evidence Verification", description: "Evaluates claim support, gaps & conflicts", status: "pending" },
  { id: "synthesis", name: "Report Synthesis", description: "Synthesizes structured cited technical report", status: "pending" },
];

export default function Home() {
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<ResearchMode>("hybrid");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stages, setStages] = useState<WorkflowStage[]>(INITIAL_STAGES);
  const [liveTasks, setLiveTasks] = useState<string[]>([]);
  const [sourceCount, setSourceCount] = useState<number>(0);
  const [result, setResult] = useState<ResearchResponse | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [activeTab, setActiveTab] = useState<"report" | "sources" | "verification">("report");
  const [backendStatus, setBackendStatus] = useState<"checking" | "connected" | "offline">("checking");
  const [docCount, setDocCount] = useState<number>(0);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState<string | null>(null);
  const [replanLoopCount, setReplanLoopCount] = useState<number>(0);

  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000";

  useEffect(() => {
    checkHealth();
    fetchHistory();
    fetchDocStats();
  }, []);

  const fetchDocStats = async () => {
    try {
      const res = await fetch(`${backendUrl}/api/documents/stats`);
      if (res.ok) {
        const data = await res.json();
        setDocCount(data.document_count || 0);
      }
    } catch (e) {
      console.warn("Failed to fetch doc stats:", e);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadMsg(null);
    setError(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${backendUrl}/api/documents/upload`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to upload document");

      setUploadMsg(`Success: ${data.message}`);
      fetchDocStats();
    } catch (err: any) {
      setUploadMsg(`Error: ${err.message || "Failed to upload file"}`);
    } finally {
      setUploading(false);
    }
  };


  const checkHealth = async () => {
    try {
      const res = await fetch(`${backendUrl}/api/health`);
      if (res.ok) {
        setBackendStatus("connected");
      } else {
        setBackendStatus("offline");
      }
    } catch {
      setBackendStatus("offline");
    }
  };

  const fetchHistory = async () => {
    try {
      const res = await fetch(`${backendUrl}/api/history`);
      if (res.ok) {
        const data = await res.json();
        setHistory(data);
      }
    } catch (e) {
      console.warn("Failed to load history:", e);
    }
  };

  const handleOpenHistorySession = async (sessionId: string) => {
    try {
      setIsLoading(true);
      setError(null);
      const res = await fetch(`${backendUrl}/api/history/${sessionId}`);
      if (!res.ok) throw new Error("Could not load historical session");
      const data: ResearchResponse = await res.json();
      setResult(data);
      setQuery(data.query);
      setMode(data.mode);
      setLiveTasks(data.steps || []);
      setSourceCount(data.documents ? data.documents.length : 0);
      setStages(INITIAL_STAGES.map((s) => ({ ...s, status: "completed" })));
      setShowHistory(false);
    } catch (err: any) {
      setError(err.message || "Failed to load session details.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteHistorySession = async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    try {
      const res = await fetch(`${backendUrl}/api/history/${sessionId}`, { method: "DELETE" });
      if (res.ok) {
        setHistory((prev) => prev.filter((h) => h.id !== sessionId));
        if (result?.id === sessionId) {
          setResult(null);
        }
      }
    } catch (err) {
      console.error("Failed to delete session:", err);
    }
  };

  const updateStage = (stageId: string, status: StageStatus) => {
    setStages((prev) =>
      prev.map((s) => (s.id === stageId ? { ...s, status } : s))
    );
  };

  const handleReset = () => {
    setQuery("");
    setResult(null);
    setError(null);
    setIsLoading(false);
    setLiveTasks([]);
    setSourceCount(0);
    setStages(INITIAL_STAGES.map((s) => ({ ...s, status: "pending" })));
  };

  const handleStartResearch = async (searchQuery?: string) => {
    const targetQuery = searchQuery || query;
    if (!targetQuery.trim() || isLoading) return;

    setIsLoading(true);
    setError(null);
    setResult(null);
    setLiveTasks([]);
    setSourceCount(0);
    setStages(INITIAL_STAGES.map((s) => ({ ...s, status: "pending" })));

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000);

    try {
      const response = await fetch(`${backendUrl}/api/research/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: targetQuery, mode }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`Server returned status ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) throw new Error("Response body reader unavailable");

      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith("data: ")) {
            const jsonStr = trimmed.replace(/^data:\s*/, "");
            try {
              const data = JSON.parse(jsonStr);

              if (data.event === "error") {
                throw new Error(data.error || "Execution error in research workflow");
              }

              if (data.event === "stage") {
                if (data.stage === "re-planning") {
                  setReplanLoopCount(data.loop_count || 1);
                }
                updateStage(data.stage, data.status);
                if (data.tasks) setLiveTasks(data.tasks);
                if (data.source_count !== undefined) setSourceCount(data.source_count);
              } else if (data.event === "complete") {
                setResult(data);
                if (data.research_loop_count) setReplanLoopCount(data.research_loop_count);
                if (data.steps) setLiveTasks(data.steps);
                if (data.documents) setSourceCount(data.documents.length);
                setStages((prev) => prev.map((s) => ({ ...s, status: "completed" })));
                setIsLoading(false);
                fetchHistory(); // Refresh history list
              }

            } catch (e: any) {
              throw e;
            }
          }
        }
      }
    } catch (err: any) {
      const msg = err.name === "AbortError" ? "Research request timed out after 60s." : err.message || "Failed to execute research.";
      setError(msg);
      setStages((prev) =>
        prev.map((s) => (s.status === "running" ? { ...s, status: "failed" } : s))
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Navbar Header */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-50 px-6 py-4 flex flex-col sm:flex-row justify-between items-center gap-4">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-blue-500/20 font-bold text-xl text-white">
            RP
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
              ResearchPilot
            </h1>
            <p className="text-xs text-slate-400">Autonomous AI Technical Research Agent</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowUploadModal(true)}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-indigo-600/30 hover:bg-indigo-600/50 border border-indigo-500/40 text-xs font-medium text-indigo-200 transition-all"
          >
            <span>📁 Upload Docs ({docCount})</span>
          </button>

          <button
            onClick={() => setShowHistory(!showHistory)}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-medium text-slate-200 transition-all"
          >
            <span>📜 Research History ({history.length})</span>
          </button>

          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-800/80 border border-slate-700 text-xs">
            <span
              className={`h-2.5 w-2.5 rounded-full ${
                backendStatus === "connected"
                  ? "bg-emerald-400 shadow-sm shadow-emerald-400"
                  : backendStatus === "checking"
                  ? "bg-amber-400 animate-pulse"
                  : "bg-rose-500"
              }`}
            />
            <span className="text-slate-300 font-medium hidden md:inline">
              Backend: {backendStatus === "connected" ? "Online" : backendStatus === "checking" ? "Checking" : "Offline"}
            </span>
          </div>

          {result && (
            <button
              onClick={handleReset}
              className="px-3 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-md transition-all"
            >
              + New Research
            </button>
          )}
        </div>
      </header>

      {/* Document Ingestion Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 max-w-lg w-full shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <span>📁 Upload Custom Documents</span>
              </h3>
              <button
                onClick={() => { setShowUploadModal(false); setUploadMsg(null); }}
                className="text-slate-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>
            <p className="text-xs text-slate-400">
              Upload PDF, Markdown, Text, or JSON files to index them directly into ChromaDB vector store for autonomous research retrieval.
            </p>
            <div className="border-2 border-dashed border-slate-700 hover:border-indigo-500/70 rounded-xl p-6 text-center space-y-3 bg-slate-950/50 transition-all">
              <input
                type="file"
                accept=".pdf,.txt,.md,.json"
                onChange={handleFileUpload}
                disabled={uploading}
                id="doc-file-input"
                className="hidden"
              />
              <label
                htmlFor="doc-file-input"
                className="cursor-pointer inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg transition-all"
              >
                {uploading ? "Processing & Chunking..." : "Choose PDF / TXT / MD File"}
              </label>
              <p className="text-[11px] text-slate-500">Supports PDF, Markdown, Plain Text, JSON (Max 25MB)</p>
            </div>
            {uploadMsg && (
              <div className={`p-3 rounded-xl text-xs ${uploadMsg.startsWith("Success") ? "bg-emerald-950/80 border border-emerald-800/60 text-emerald-300" : "bg-rose-950/80 border border-rose-800/60 text-rose-300"}`}>
                {uploadMsg}
              </div>
            )}
            <div className="flex justify-between items-center text-xs text-slate-400 pt-2 border-t border-slate-800">
              <span>Indexed Document Chunks: <strong className="text-indigo-400">{docCount}</strong></span>
              <button
                onClick={() => { setShowUploadModal(false); setUploadMsg(null); }}
                className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}


      {/* Persistent Research History Slide-Over Drawer */}
      {showHistory && (
        <aside className="bg-slate-900 border-b border-slate-800 p-6 shadow-2xl space-y-4 animate-in slide-in-from-top duration-200">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">Saved Research Sessions</h3>
            <button
              onClick={() => setShowHistory(false)}
              className="text-xs text-slate-400 hover:text-white"
            >
              ✕ Close
            </button>
          </div>

          {history.length === 0 ? (
            <p className="text-xs text-slate-500 py-4">No saved research sessions in history yet.</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 max-h-60 overflow-y-auto pr-2">
              {history.map((h) => (
                <div
                  key={h.id}
                  onClick={() => handleOpenHistorySession(h.id)}
                  className="bg-slate-950 border border-slate-800 hover:border-blue-500/60 rounded-xl p-3.5 transition-all cursor-pointer flex flex-col justify-between space-y-2 group"
                >
                  <div className="flex items-start justify-between gap-2">
                    <h4 className="text-xs font-semibold text-slate-200 group-hover:text-blue-300 line-clamp-2">
                      {h.query}
                    </h4>
                    <button
                      onClick={(e) => handleDeleteHistorySession(e, h.id)}
                      title="Delete session"
                      className="text-slate-600 hover:text-rose-400 p-1 transition-colors text-xs shrink-0"
                    >
                      🗑
                    </button>
                  </div>

                  <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono pt-2 border-t border-slate-900">
                    <span className="capitalize text-slate-400">{h.mode}</span>
                    <span>Sources: {h.source_count}</span>
                    <span>{new Date(h.timestamp).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </aside>
      )}

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-8">
        {/* Research Input & Mode Controls Card */}
        <section className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
          <div>
            <h2 className="text-lg font-semibold text-white mb-1">Technical Research Console</h2>
            <p className="text-sm text-slate-400">
              Submit any software engineering, AI/ML, cloud architecture, or database inquiry.
            </p>
          </div>

          {/* Prompt Text Area */}
          <div className="space-y-3">
            <textarea
              rows={3}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              disabled={isLoading}
              placeholder="e.g. How does state persistence work in LangGraph using checkpointers?"
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-4 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all text-sm leading-relaxed disabled:opacity-50"
            />

            {/* Example Queries Chips */}
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs text-slate-400 font-medium mr-1">Examples:</span>
              {EXAMPLE_QUERIES.map((eq, i) => (
                <button
                  key={i}
                  disabled={isLoading}
                  onClick={() => {
                    setQuery(eq);
                    handleStartResearch(eq);
                  }}
                  className="text-xs bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white px-3 py-1.5 rounded-lg border border-slate-700/60 transition-all text-left truncate max-w-xs disabled:opacity-40"
                >
                  {eq}
                </button>
              ))}
            </div>
          </div>

          {/* Mode Selector & Submit Action */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 pt-2 border-t border-slate-800/60">
            <div className="flex items-center gap-2 bg-slate-950 p-1.5 rounded-xl border border-slate-800">
              <span className="text-xs text-slate-400 font-semibold px-2">Mode:</span>
              {(["hybrid", "knowledge_base", "web_research"] as ResearchMode[]).map((m) => (
                <button
                  key={m}
                  disabled={isLoading}
                  onClick={() => setMode(m)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all capitalize disabled:opacity-50 ${
                    mode === m
                      ? "bg-blue-600 text-white shadow-md shadow-blue-600/30"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
                  }`}
                >
                  {m === "hybrid" ? "Hybrid (Dual)" : m === "knowledge_base" ? "Knowledge Base" : "Web Research"}
                </button>
              ))}
            </div>

            <button
              onClick={() => handleStartResearch()}
              disabled={isLoading || !query.trim()}
              className={`px-6 py-3 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 transition-all ${
                isLoading || !query.trim()
                  ? "bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700/50"
                  : "bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-lg shadow-blue-600/25 active:scale-95"
              }`}
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  <span>Executing Workflow...</span>
                </>
              ) : (
                <>
                  <span>Start Autonomous Research</span>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                  </svg>
                </>
              )}
            </button>
          </div>
        </section>

        {/* Real-time Agent Workflow Stepper */}
        {(isLoading || result || stages.some((s) => s.status !== "pending")) && (
          <section className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">
                Live LangGraph Execution Workflow
              </h3>

              <div className="flex items-center gap-4 text-xs font-mono">
                {liveTasks.length > 0 && (
                  <span className="text-blue-400 bg-blue-950/80 px-2.5 py-1 rounded-lg border border-blue-800/50">
                    Tasks: {liveTasks.length}
                  </span>
                )}
                {sourceCount > 0 && (
                  <span className="text-emerald-400 bg-emerald-950/80 px-2.5 py-1 rounded-lg border border-emerald-800/50">
                    Retrieved Sources: {sourceCount}
                  </span>
                )}
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
              {stages.map((stage) => (
                <div
                  key={stage.id}
                  className={`p-3.5 rounded-xl border transition-all flex flex-col justify-between ${
                    stage.status === "completed"
                      ? "bg-slate-950/80 border-emerald-500/40 text-emerald-300"
                      : stage.status === "running"
                      ? "bg-blue-950/50 border-blue-500 text-blue-200 glow-pulse"
                      : stage.status === "failed"
                      ? "bg-rose-950/50 border-rose-500 text-rose-300"
                      : "bg-slate-950/40 border-slate-800 text-slate-500"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold uppercase tracking-wider">{stage.name}</span>
                    {stage.status === "completed" && (
                      <span className="h-5 w-5 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-xs font-bold">✓</span>
                    )}
                    {stage.status === "running" && (
                      <svg className="animate-spin h-4 w-4 text-blue-400" viewBox="0 0 24 24" fill="none">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                    )}
                    {stage.status === "failed" && (
                      <span className="h-5 w-5 rounded-full bg-rose-500/20 text-rose-400 flex items-center justify-center text-xs font-bold">✕</span>
                    )}
                    {stage.status === "pending" && (
                      <span className="h-2 w-2 rounded-full bg-slate-700" />
                    )}
                  </div>
                  <p className="text-[11px] leading-tight text-slate-400">{stage.description}</p>
                </div>
              ))}
            </div>

            {liveTasks.length > 0 && (
              <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-2">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Active Sub-Tasks Plan</h4>
                <div className="flex flex-wrap gap-2">
                  {liveTasks.map((t, idx) => (
                    <span key={idx} className="text-xs bg-slate-900 border border-slate-800 text-slate-300 px-3 py-1 rounded-lg">
                      Task {idx + 1}: {t}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </section>
        )}

        {/* Error Alert Box */}
        {error && (
          <div className="bg-rose-950/60 border border-rose-800/80 rounded-2xl p-5 text-rose-200 flex items-start justify-between gap-4">
            <div className="flex items-start gap-3">
              <div className="h-6 w-6 rounded-full bg-rose-500/20 text-rose-400 flex items-center justify-center font-bold text-sm shrink-0 mt-0.5">!</div>
              <div>
                <h4 className="font-semibold text-sm text-rose-100">Research Execution Issue</h4>
                <p className="text-xs text-rose-300/90 mt-1">{error}</p>
              </div>
            </div>
            <button
              onClick={() => handleStartResearch()}
              className="px-3 py-1.5 rounded-lg bg-rose-900 hover:bg-rose-800 text-rose-100 text-xs font-medium shrink-0 transition-all"
            >
              Retry Research
            </button>
          </div>
        )}

        {/* Final Report */}
        {result && (
          <section className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-4 gap-4">
              <div>
                <span className="text-xs font-mono uppercase text-emerald-400 tracking-wider font-semibold">
                  ✓ Verified Research Report
                </span>
                <h2 className="text-xl font-bold text-white mt-1">{result.query}</h2>
              </div>

              <div className="flex items-center gap-2">
                <span className="px-3 py-1 rounded-full text-xs font-semibold bg-slate-800 border border-slate-700 text-slate-300 capitalize">
                  Mode: {result.mode}
                </span>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-semibold border ${
                    result.evidence_verification?.status === "supported"
                      ? "bg-emerald-950/80 border-emerald-600 text-emerald-300"
                      : result.evidence_verification?.status === "conflicting"
                      ? "bg-amber-950/80 border-amber-600 text-amber-300"
                      : "bg-rose-950/80 border-rose-600 text-rose-300"
                  }`}
                >
                  Verification: {result.evidence_verification?.status || "Verified"}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
              <button
                onClick={() => setActiveTab("report")}
                className={`px-4 py-2 rounded-xl text-xs font-medium transition-all ${
                  activeTab === "report" ? "bg-blue-600 text-white" : "text-slate-400 hover:text-white hover:bg-slate-800"
                }`}
              >
                Structured Technical Report
              </button>
              <button
                onClick={() => setActiveTab("verification")}
                className={`px-4 py-2 rounded-xl text-xs font-medium transition-all ${
                  activeTab === "verification" ? "bg-blue-600 text-white" : "text-slate-400 hover:text-white hover:bg-slate-800"
                }`}
              >
                Evidence Verification
              </button>
              <button
                onClick={() => setActiveTab("sources")}
                className={`px-4 py-2 rounded-xl text-xs font-medium transition-all ${
                  activeTab === "sources" ? "bg-blue-600 text-white" : "text-slate-400 hover:text-white hover:bg-slate-800"
                }`}
              >
                Retrieved Sources ({result.documents ? result.documents.length : 0})
              </button>
            </div>

            {activeTab === "report" && (
              <div className="prose prose-invert max-w-none text-slate-200 text-sm leading-relaxed whitespace-pre-wrap font-sans space-y-4 break-words overflow-x-auto">
                {result.report}
              </div>
            )}

            {activeTab === "verification" && (
              <div className="space-y-4 min-w-0 max-w-full">
                <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-2 min-w-0">
                  <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">Verification Summary</h4>
                  <p className="text-sm text-slate-300 break-words">{result.evidence_verification?.summary || "Evidence verified across sources."}</p>
                </div>

                {result.evidence_verification?.verified_claims?.length > 0 && (
                  <div className="bg-emerald-950/40 border border-emerald-800/60 rounded-xl p-4 space-y-2 min-w-0">
                    <h4 className="text-xs font-bold text-emerald-300 uppercase tracking-wider">Verified Claims</h4>
                    <ul className="list-disc list-inside text-xs text-emerald-200 space-y-1 break-words">
                      {result.evidence_verification.verified_claims.map((claim, idx) => (
                        <li key={idx} className="break-words">{claim}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {result.evidence_verification?.conflicting_claims?.length > 0 && (
                  <div className="bg-amber-950/40 border border-amber-800/60 rounded-xl p-4 space-y-2 min-w-0">
                    <h4 className="text-xs font-bold text-amber-300 uppercase tracking-wider">Conflicting Claims Detected</h4>
                    <ul className="list-disc list-inside text-xs text-amber-200 space-y-1 break-words">
                      {result.evidence_verification.conflicting_claims.map((claim, idx) => (
                        <li key={idx} className="break-words">{claim}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {result.evidence_verification?.missing_elements?.length > 0 && (
                  <div className="bg-rose-950/40 border border-rose-800/60 rounded-xl p-4 space-y-2 min-w-0">
                    <h4 className="text-xs font-bold text-rose-300 uppercase tracking-wider">Context Gaps & Missing Information</h4>
                    <ul className="list-disc list-inside text-xs text-rose-200 space-y-1 break-words">
                      {result.evidence_verification.missing_elements.map((gap, idx) => (
                        <li key={idx} className="break-words">{gap}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {activeTab === "sources" && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 min-w-0 max-w-full">
                {(result.documents || []).map((doc, idx) => (
                  <div key={idx} className="bg-slate-950 border border-slate-800 hover:border-blue-500/50 rounded-xl p-4 transition-all flex flex-col justify-between space-y-3 min-w-0 max-w-full overflow-hidden">
                    <div className="min-w-0">
                      <div className="flex items-center justify-between mb-2 gap-2 min-w-0">
                        <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800/50 truncate max-w-[70%]">
                          {doc.source}
                        </span>
                        <span className="text-xs text-slate-500 font-mono shrink-0">[{idx + 1}]</span>
                      </div>
                      <h4 className="font-semibold text-sm text-slate-100 line-clamp-2 break-words">{doc.title}</h4>
                      <p className="text-xs text-slate-400 mt-2 line-clamp-3 leading-relaxed break-words">{doc.snippet}</p>
                    </div>

                    <a
                      href={doc.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-blue-400 hover:text-blue-300 font-medium flex items-center gap-1.5 pt-2 border-t border-slate-900 min-w-0 max-w-full overflow-hidden"
                    >
                      <span className="truncate min-w-0 flex-1 break-all">{doc.url}</span>
                      <svg className="w-3.5 h-3.5 shrink-0 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                    </a>
                  </div>
                ))}
              </div>
            )}

          </section>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 py-6 text-center text-xs text-slate-500">
        ResearchPilot Portfolio Project — Built with LangGraph, Google Gemini, ChromaDB & Next.js
      </footer>
    </div>
  );
}
