"use client";

import React from "react";
import { Plane, Hotel, Map, BrainCircuit, Database, CheckCircle2, Loader2, ChevronRight, CloudSun, FileCheck } from "lucide-react";

export interface AgentStepStatus {
  step: number;
  flightAgent: "idle" | "running" | "done";
  hotelAgent: "idle" | "running" | "done";
  weatherAgent?: "idle" | "running" | "done";
  itineraryAgent: "idle" | "running" | "done";
  finalAgent?: "idle" | "running" | "done";
  currentAgent: string;
  elapsedMs: number;
}

interface AgentWorkflowVisualizerProps {
  status: AgentStepStatus;
  userQuery: string;
}

const statusConfig = {
  idle: { dot: "bg-white/15", ring: "", label: "Standby", labelClass: "text-white/30 bg-white/5 border border-white/6" },
  running: { dot: "bg-sky-400 animate-pulse", ring: "ring-2 ring-sky-400/30", label: "Active", labelClass: "text-sky-400 bg-sky-500/15 border border-sky-400/25" },
  done: { dot: "bg-teal-400", ring: "", label: "Done", labelClass: "text-teal-400 bg-teal-500/12 border border-teal-400/20" },
};

export default function AgentWorkflowVisualizer({ status, userQuery }: AgentWorkflowVisualizerProps) {
  // Parallel Fan-Out Workers
  const fanOutAgents = [
    {
      key: "flightAgent" as const,
      icon: <Plane className="w-4 h-4" />,
      name: "Flight Agent",
      detail: "AviationStack MCP · Live Routes",
      accentColor: "#38bdf8",
      bgClass: "bg-sky-500/8 border-sky-500/18",
      iconBg: "bg-sky-500/12 border border-sky-500/20 text-sky-400",
    },
    {
      key: "hotelAgent" as const,
      icon: <Hotel className="w-4 h-4" />,
      name: "Hotel Agent",
      detail: "Tavily Remote MCP · Boutique Stays",
      accentColor: "#818cf8",
      bgClass: "bg-indigo-500/8 border-indigo-500/18",
      iconBg: "bg-indigo-500/12 border border-indigo-500/20 text-indigo-400",
    },
    {
      key: "weatherAgent" as const,
      icon: <CloudSun className="w-4 h-4" />,
      name: "Weather Agent",
      detail: "FastMCP · OpenWeatherMap 5-Day",
      accentColor: "#38bdf8",
      bgClass: "bg-cyan-500/8 border-cyan-500/18",
      iconBg: "bg-cyan-500/12 border border-cyan-500/20 text-cyan-400",
    },
  ];

  // Fan-In Downstream Synthesis Agents
  const fanInAgents = [
    {
      key: "itineraryAgent" as const,
      icon: <Map className="w-4 h-4" />,
      name: "Itinerary Agent",
      detail: "Groq 120B · State Fusion (Smart LLM)",
      accentColor: "#2dd4bf",
      bgClass: "bg-teal-500/8 border-teal-500/18",
      iconBg: "bg-teal-500/12 border border-teal-500/20 text-teal-400",
    },
    {
      key: "finalAgent" as const,
      icon: <FileCheck className="w-4 h-4" />,
      name: "Final Agent",
      detail: "Dossier Synthesis · Gemini Fallback",
      accentColor: "#a78bfa",
      bgClass: "bg-purple-500/8 border-purple-500/18",
      iconBg: "bg-purple-500/12 border border-purple-500/20 text-purple-400",
    },
  ];

  const agentStatuses = {
    flightAgent: status.flightAgent,
    hotelAgent: status.hotelAgent,
    weatherAgent: status.weatherAgent || (status.flightAgent === "running" ? "running" : status.flightAgent === "done" ? "done" : "idle"),
    itineraryAgent: status.itineraryAgent,
    finalAgent: status.finalAgent || (status.itineraryAgent === "done" ? "done" : status.itineraryAgent === "running" ? "running" : "idle"),
  };

  return (
    <div className="w-full max-w-5xl mx-auto px-4 my-4">
      <div
        className="relative rounded-2xl overflow-hidden"
        style={{
          background: "linear-gradient(135deg, rgba(8,12,20,0.95) 0%, rgba(4,8,16,0.95) 100%)",
          border: "1px solid rgba(255,255,255,0.08)",
          backdropFilter: "blur(20px)",
          boxShadow: "0 24px 64px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.04)",
        }}
      >
        {/* Ambient glow */}
        <div className="absolute -top-16 -left-16 w-48 h-48 bg-teal-500/8 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-16 -right-16 w-48 h-48 bg-sky-500/8 rounded-full blur-3xl pointer-events-none" />

        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between p-5 border-b border-white/6 gap-3">
          <div className="flex items-center gap-2.5">
            <div className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.7)] animate-pulse" />
            <h3 className="text-sm font-semibold text-white flex items-center gap-1.5">
              <BrainCircuit className="w-4 h-4 text-sky-400" />
              LangGraph Fan-Out / Fan-In Orchestrator
            </h3>
          </div>
          <div className="flex items-center gap-2">
            <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-teal-500/10 border border-teal-500/20 text-[11px] font-mono text-teal-300">
              <span className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-pulse" />
              FastMCP Active
            </span>
            <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-[11px] font-mono text-indigo-400">
              <Database className="w-3 h-3" />
              Postgres Checkpointer
            </span>
            <span className="text-[11px] font-mono text-white/30">
              {status.elapsedMs > 0 ? `${(status.elapsedMs / 1000).toFixed(1)}s` : "Ready"}
            </span>
          </div>
        </div>

        {/* User Query Pill */}
        {userQuery && (
          <div className="mx-5 mt-4 px-3.5 py-2 rounded-xl flex items-center gap-2 text-xs" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)" }}>
            <span className="text-white/30 font-mono shrink-0">SharedState.user_query →</span>
            <span className="text-teal-300 font-medium truncate">&ldquo;{userQuery}&rdquo;</span>
          </div>
        )}

        {/* Agent Nodes Layout: Fan-Out Row (3) + Fan-In Row (2) */}
        <div className="p-5 space-y-4">
          {/* Fan-Out Stage Header */}
          <div className="flex items-center justify-between text-[11px] text-white/40 font-mono px-1">
            <span className="flex items-center gap-1.5 text-teal-400">
              <span className="w-1.5 h-1.5 rounded-full bg-teal-400" />
              STAGE 1: Fan-Out Concurrency (3 Parallel MCP Threads)
            </span>
            <span>~50% Latency Reduction</span>
          </div>

          {/* 3 Parallel Fan-Out Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {fanOutAgents.map((agent) => {
              const st = agentStatuses[agent.key];
              const cfg = statusConfig[st];

              return (
                <div
                  key={agent.key}
                  className={`relative p-3.5 rounded-xl border transition-all duration-500 ${agent.bgClass} ${st === "running" ? cfg.ring : ""}`}
                  style={st === "running" ? { boxShadow: `0 0 24px ${agent.accentColor}18` } : {}}
                >
                  <div className="absolute top-3 right-3">
                    <div className={`w-2 h-2 rounded-full ${cfg.dot}`} />
                  </div>

                  <div className="flex items-center gap-2.5 mb-2">
                    <div className={`p-2 rounded-lg ${agent.iconBg}`}>
                      {agent.icon}
                    </div>
                    <div>
                      <h4 className="text-xs font-semibold text-white">{agent.name}</h4>
                      <p className="text-[10px] text-white/40 font-mono">{agent.detail}</p>
                    </div>
                  </div>

                  <div className="flex items-center justify-between mt-2 pt-2 border-t border-white/5">
                    <span className={`inline-flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded-full ${cfg.labelClass}`}>
                      {st === "running" && <Loader2 className="w-2.5 h-2.5 animate-spin" />}
                      {st === "done" && <CheckCircle2 className="w-2.5 h-2.5" />}
                      {st === "running" ? "Fetching..." : st === "done" ? "Synchronized" : "Standby"}
                    </span>
                    <span className="text-[10px] font-mono text-white/30">Node: {agent.key}</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Fan-In Stage Header */}
          <div className="flex items-center justify-between text-[11px] text-white/40 font-mono px-1 pt-1">
            <span className="flex items-center gap-1.5 text-indigo-400">
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-400" />
              STAGE 2: Fan-In Convergence & Synthesis (Hybrid Smart LLM)
            </span>
            <span>Groq 120B Flagship + Gemini Fallback</span>
          </div>

          {/* 2 Fan-In Synthesis Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {fanInAgents.map((agent) => {
              const st = agentStatuses[agent.key];
              const cfg = statusConfig[st];

              return (
                <div
                  key={agent.key}
                  className={`relative p-3.5 rounded-xl border transition-all duration-500 ${agent.bgClass} ${st === "running" ? cfg.ring : ""}`}
                  style={st === "running" ? { boxShadow: `0 0 24px ${agent.accentColor}18` } : {}}
                >
                  <div className="absolute top-3 right-3">
                    <div className={`w-2 h-2 rounded-full ${cfg.dot}`} />
                  </div>

                  <div className="flex items-center gap-2.5 mb-2">
                    <div className={`p-2 rounded-lg ${agent.iconBg}`}>
                      {agent.icon}
                    </div>
                    <div>
                      <h4 className="text-xs font-semibold text-white">{agent.name}</h4>
                      <p className="text-[10px] text-white/40 font-mono">{agent.detail}</p>
                    </div>
                  </div>

                  <div className="flex items-center justify-between mt-2 pt-2 border-t border-white/5">
                    <span className={`inline-flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded-full ${cfg.labelClass}`}>
                      {st === "running" && <Loader2 className="w-2.5 h-2.5 animate-spin" />}
                      {st === "done" && <CheckCircle2 className="w-2.5 h-2.5" />}
                      {st === "running" ? "Reasoning..." : st === "done" ? "Complete" : "Awaiting Fan-In"}
                    </span>
                    <span className="text-[10px] font-mono text-white/30">Node: {agent.key}</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Flow Bar at bottom */}
          <div className="mt-2 pt-3 border-t border-white/5 flex items-center justify-between text-xs text-white/40">
            <div className="flex items-center gap-2">
              <ChevronRight className="w-3.5 h-3.5 text-white/20" />
              <span>Current Status: <span className="text-white/70 font-medium">{status.currentAgent || "Awaiting Request"}</span></span>
            </div>
            <div className="hidden sm:flex items-center gap-1 font-mono text-[10px]">
              <span className="text-teal-400">START</span>
              <span className="text-white/20">→</span>
              <span className="px-1.5 py-0.5 rounded bg-teal-500/10 text-teal-300">Fan-Out [3]</span>
              <span className="text-white/20">→</span>
              <span className="px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-300">itinerary_agent</span>
              <span className="text-white/20">→</span>
              <span className="px-1.5 py-0.5 rounded bg-purple-500/10 text-purple-300">final_agent</span>
              <span className="text-white/20">→</span>
              <span className="text-emerald-400">END</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
