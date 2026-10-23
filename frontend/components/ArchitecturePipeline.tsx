"use client";

import React, { useState } from "react";
import {
  ShieldAlert,
  GitBranch,
  Zap,
  UserCheck,
  Cpu,
  Database,
  ArrowRight,
  CheckCircle2,
  Clock,
  Sparkles,
  Plane,
  Hotel,
  CloudSun,
  MapPin,
  FileCheck,
  Compass,
} from "lucide-react";
import ScrollReveal from "./ScrollReveal";
import { GlowingEffect } from "./ui/glowing-effect";

export default function ArchitecturePipeline() {
  const [selectedRoute, setSelectedRoute] = useState<"new_plan" | "specific_query" | "follow_up">("new_plan");

  const architectureSteps = [
    {
      num: "01",
      title: "Input Guardrail",
      subtitle: "Prompt security • < 0.5s",
      desc: "A sub-500ms gpt-oss-20b check stops prompt injections, jailbreaks, and off-topic requests before touching paid APIs or expensive 120B tokens.",
      icon: <ShieldAlert className="w-5 h-5 text-emerald-400" />,
      tag: "input_guardrail",
      stat: "🛡️ < 500ms • Fail-Open",
      badgeColor: "border-emerald-500/25 bg-emerald-500/10 text-emerald-400",
    },
    {
      num: "02",
      title: "Supervisor Router",
      subtitle: "3-way dynamic triage • ~1s",
      desc: "gpt-oss-20b triages into 3 paths: full parallel plan, single-tool lookup (~4–6s), or zero-tool follow-up (~1–2s direct from memory).",
      icon: <GitBranch className="w-5 h-5 text-sky-400" />,
      tag: "supervisor_agent",
      stat: "⚡ 3 paths • 1 LLM call",
      badgeColor: "border-sky-500/25 bg-sky-500/10 text-sky-400",
    },
    {
      num: "03",
      title: "Parallel Swarm",
      subtitle: "35–40% faster (~35s → ~21s)",
      desc: "Flights (5 MCP calls), Hotels (Tavily search, 0 LLM), Weather (2 MCP calls), and Maps (Geoapify Remote MCP, 0 LLM) run simultaneously. Slowest branch finishes in ~21s vs ~35s.",
      icon: <Zap className="w-5 h-5 text-teal-400" />,
      tag: "fan_out_swarm",
      stat: "🚀 ~21s parallel vs ~35s",
      badgeColor: "border-teal-500/25 bg-teal-500/10 text-teal-400",
    },
    {
      num: "04",
      title: "Human-in-the-Loop",
      subtitle: "LangGraph interrupt() pause",
      desc: "Pauses execution after draft itinerary creation. Review recommendations, then approve or request changes to resume from database checkpoints.",
      icon: <UserCheck className="w-5 h-5 text-amber-400" />,
      tag: "human_approval",
      stat: "⏸️ Review & resume",
      badgeColor: "border-amber-500/25 bg-amber-500/10 text-amber-400",
    },
    {
      num: "05",
      title: "Dual-Tier Memory",
      subtitle: "Smart 120B + Dual Memory",
      desc: "gpt-oss-120b polishes the 7-section guide with Gemini fallback. PostgresSaver manages session state, while PostgresStore retains user profiles.",
      icon: <Cpu className="w-5 h-5 text-indigo-400" />,
      tag: "dual_memory",
      stat: "🧠 Checkpoint + Store",
      badgeColor: "border-indigo-500/25 bg-indigo-500/10 text-indigo-400",
    },
  ];

  return (
    <section className="w-full py-24 px-4 relative z-10 scroll-reveal-native" id="architecture">
      <div className="max-w-6xl mx-auto">
        {/* Section Header */}
        <ScrollReveal direction="up" durationMs={800}>
          <div className="flex flex-col items-center text-center mb-14">
            <h2 className="text-3xl sm:text-4xl font-bold text-white tracking-tight">
              Intent-Aware Multi-Agent Architecture
            </h2>
            <p className="text-sm text-white/50 max-w-2xl mx-auto mt-3 leading-relaxed">
              An asynchronous LangGraph state graph combining Groq 20B/120B with Google Gemini failover, MCP search, parallel fan-out tool calling, and Human-in-the-Loop review.
            </p>
          </div>
        </ScrollReveal>

        {/* ── Interactive Workflow Graph Visualizer ── */}
        <ScrollReveal direction="up" durationMs={850} delayMs={100} className="mb-14">
          <div className="relative rounded-2xl p-[1px] group">
            <GlowingEffect
              spread={45}
              glow={true}
              disabled={false}
              proximity={80}
              inactiveZone={0.01}
              borderWidth={2}
            />
            <div className="relative z-10 rounded-2xl p-6 sm:p-8 bg-gradient-to-b from-[#0f1422]/95 to-[#080b13]/95 border border-white/10 backdrop-blur-2xl shadow-2xl">
              {/* Route Selector Tabs */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-white/8 mb-8">
                <div>
                  <div className="text-xs font-mono uppercase tracking-wider text-teal-400 mb-1 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-teal-400 animate-pulse" />
                    Interactive Execution Path Visualizer
                  </div>
                </div>

                <div className="flex items-center gap-2 p-1 rounded-xl bg-black/40 border border-white/8 self-start sm:self-auto">
                  <button
                    type="button"
                    onClick={() => setSelectedRoute("new_plan")}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                      selectedRoute === "new_plan"
                        ? "bg-teal-500/20 border border-teal-500/30 text-teal-300 shadow-sm"
                        : "text-white/50 hover:text-white"
                    }`}
                  >
                    1. New Plan (Fan-Out + HITL)
                  </button>
                  <button
                    type="button"
                    onClick={() => setSelectedRoute("specific_query")}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                      selectedRoute === "specific_query"
                        ? "bg-sky-500/20 border border-sky-500/30 text-sky-300 shadow-sm"
                        : "text-white/50 hover:text-white"
                    }`}
                  >
                    2. Specific Query (~4s)
                  </button>
                  <button
                    type="button"
                    onClick={() => setSelectedRoute("follow_up")}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                      selectedRoute === "follow_up"
                        ? "bg-indigo-500/20 border border-indigo-500/30 text-indigo-300 shadow-sm"
                        : "text-white/50 hover:text-white"
                    }`}
                  >
                    3. Follow-up (0-Tool ~1s)
                  </button>
                </div>
              </div>

              {/* Dynamic Visual Pipeline Diagram */}
              <div className="grid grid-cols-1 md:grid-cols-5 gap-3 relative">
                {/* Stage 1: START & Guardrail */}
                <div className="flex flex-col gap-2 p-4 rounded-xl bg-white/[0.02] border border-white/8 relative">
                  <div className="text-[10px] font-mono text-emerald-400 uppercase tracking-wider">Gate 1</div>
                  <div className="text-xs font-semibold text-white flex items-center gap-1.5">
                    <ShieldAlert className="w-3.5 h-3.5 text-emerald-400" />
                    Input Guardrail &amp; Security
                  </div>
                  <p className="text-[11px] text-white/50 leading-relaxed">
                    Filters prompt injections, jailbreaks, and off-topic requests in &lt; 0.5s. Adversarial prompts early-exit at <span className="font-mono text-neutral-400">guardrail_blocked</span>.
                  </p>
                  <div className="mt-auto pt-2 flex items-center gap-1 text-[10px] font-mono text-emerald-400/80">
                    <CheckCircle2 className="w-3 h-3" />
                    <span>~0.5s • Fail-Open safe</span>
                  </div>
                </div>

                {/* Stage 2: Supervisor Router */}
                <div className="flex flex-col gap-2 p-4 rounded-xl bg-white/[0.02] border border-white/8 relative">
                  <div className="text-[10px] font-mono text-sky-400 uppercase tracking-wider">Gate 2</div>
                  <div className="text-xs font-semibold text-white flex items-center gap-1.5">
                    <GitBranch className="w-3.5 h-3.5 text-sky-400" />
                    Supervisor Router / orchestrator
                  </div>
                  <p className="text-[11px] text-white/50 leading-relaxed">
                    <code className="text-sky-300 font-mono text-[10px]">gpt-oss-20b</code> reads your query + conversation history and picks a route: <span className="text-teal-300 font-mono">{selectedRoute}</span>.
                  </p>
                  <div className="mt-auto pt-2 text-[10px] font-sans text-sky-400/80">
                    → Intent: <span className="font-mono">{selectedRoute}</span>
                  </div>
                </div>

                {/* Stage 3: Dynamic Tool Execution */}
                <div className="flex flex-col gap-2 p-4 rounded-xl bg-white/[0.02] border border-white/8 relative">
                  <div className="text-[10px] font-mono text-teal-400 uppercase tracking-wider">Stage 3</div>
                  <div className="text-xs font-semibold text-white flex items-center gap-1.5">
                    <Zap className="w-3.5 h-3.5 text-teal-400" />
                    Tool Layer
                  </div>
                  {selectedRoute === "new_plan" && (
                    <div className="space-y-1.5 text-[11px]">
                      <div className="flex items-center gap-1 text-sky-300 font-sans text-[10px]">
                        <Plane className="w-3 h-3 shrink-0" /> Flight - 5 MCP calls + 1 LLM (~21s)
                      </div>
                      <div className="flex items-center gap-1 text-indigo-300 font-sans text-[10px]">
                        <Hotel className="w-3 h-3 shrink-0" /> Hotel - Tavily search, 0 LLM (~8s)
                      </div>
                      <div className="flex items-center gap-1 text-cyan-300 font-sans text-[10px]">
                        <CloudSun className="w-3 h-3 shrink-0" /> Weather - 2 MCP calls + 1 LLM (~3s)
                      </div>
                      <div className="flex items-center gap-1 text-emerald-300 font-sans text-[10px]">
                        <Compass className="w-3 h-3 shrink-0" /> Maps - Geoapify Remote MCP (~1-2s)
                      </div>
                      <div className="text-[10px] text-teal-400/70 pt-1">
                        Parallel: max(21s, 8s, 3s, 2s) = ~21s
                      </div>
                    </div>
                  )}
                  {selectedRoute === "specific_query" && (
                    <div className="text-[11px] text-sky-300 space-y-1">
                      <p className="text-white/60">Bypasses other tools. Dispatches only the requested agent.</p>
                      <div className="font-mono text-[10px] text-sky-400">⏱ ~4-6s (vs ~32s)</div>
                    </div>
                  )}
                  {selectedRoute === "follow_up" && (
                    <div className="text-[11px] text-indigo-300 space-y-1">
                      <p className="text-white/60">0 tools dispatched. Bypasses external network calls completely.</p>
                      <div className="font-mono text-[10px] text-emerald-400">0.0s Tool Latency</div>
                    </div>
                  )}
                </div>

                {/* Stage 4: Itinerary + HITL Pause */}
                <div className="flex flex-col gap-2 p-4 rounded-xl bg-white/[0.02] border border-white/8 relative">
                  <div className="text-[10px] font-mono text-amber-400 uppercase tracking-wider">Stage 4</div>
                  <div className="text-xs font-semibold text-white flex items-center gap-1.5">
                    <UserCheck className="w-3.5 h-3.5 text-amber-400" />
                    HITL Approval
                  </div>
                  {selectedRoute === "new_plan" ? (
                    <div className="space-y-1 text-[11px]">
                      <div className="flex items-center gap-1 text-teal-300 font-mono text-[10px]">
                        <MapPin className="w-3 h-3" /> Itinerary Barrier (Fan-In)
                      </div>
                      <p className="text-white/50 text-[10px]">
                        Pauses at <code className="text-amber-400">interrupt()</code> for user approval / custom revision.
                      </p>
                    </div>
                  ) : (
                    <div className="text-[11px] text-white/40 italic">
                      Bypassed for {selectedRoute === "follow_up" ? "follow-up questions" : "single-tool inquiries"}.
                    </div>
                  )}
                </div>

                {/* Stage 5: Final Synthesis & Checkpointing */}
                <div className="flex flex-col gap-2 p-4 rounded-xl bg-white/[0.02] border border-white/8 relative">
                  <div className="text-[10px] font-mono text-indigo-400 uppercase tracking-wider">Stage 5</div>
                  <div className="text-xs font-semibold text-white flex items-center gap-1.5">
                    <FileCheck className="w-3.5 h-3.5 text-indigo-400" />
                    Synthesis &amp; Dual Memory
                  </div>
                  <p className="text-[11px] text-white/50 leading-relaxed">
                    <code className="text-indigo-300 font-mono text-[10px]">gpt-oss-120b</code> polishes report.
                    {selectedRoute === "follow_up" && <span className="text-emerald-300"> 0 tools - pure memory recall in ~1-2s.</span>}
                    {selectedRoute !== "follow_up" && <span> Fallback: Gemini flash-lite → gpt-oss-20b.</span>}
                  </p>
                  <div className="mt-auto pt-2 flex flex-col gap-0.5 text-[9px] font-mono text-indigo-300/80">
                    <div className="flex items-center gap-1">
                      <Database className="w-2.5 h-2.5" />
                      <span>PostgresSaver: thread_id short-term</span>
                    </div>
                    <div className="flex items-center gap-1 text-cyan-300/80">
                      <Database className="w-2.5 h-2.5" />
                      <span>PostgresStore: user_id long-term</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Bottom Benchmark Stat Note */}
              <div className="mt-6 pt-4 border-t border-white/6 flex flex-wrap items-center justify-between text-xs text-white/40 gap-2">
                <div className="flex items-center gap-2">
                  <Clock className="w-3.5 h-3.5 text-teal-400" />
                  <span>
                    Sequential: <strong className="text-neutral-300 font-mono">T_flight (21s) + T_hotel (8s) + T_weather (3s) = ~32s total wait</strong>
                  </span>
                </div>
                <div className="flex items-center gap-2 text-teal-300">
                  <Zap className="w-3 h-3" />
                  <span>Parallel Fan-Out: <strong className="font-mono">max(21s, 8s, 3s) = ~21s</strong> - saves ~11s (~35% faster)</span>
                </div>
              </div>
            </div>
          </div>
        </ScrollReveal>

        {/* ── 5-Step Architecture Detail Cards ── */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3.5 relative">
          {architectureSteps.map((step, idx) => (
            <ScrollReveal
              key={idx}
              direction="up"
              delayMs={idx * 100}
              durationMs={700}
              className="h-full"
            >
              <div className="relative h-full rounded-2xl p-[1px] group">
                <GlowingEffect
                  spread={35}
                  glow={true}
                  disabled={false}
                  proximity={60}
                  inactiveZone={0.01}
                  borderWidth={2}
                />
                <div className="relative z-10 rounded-2xl p-5 bg-gradient-to-b from-[#0f1420]/95 to-[#080b12]/95 border border-white/8 transition-all duration-300 hover:-translate-y-1 shadow-lg h-full flex flex-col justify-between">
                  <div>
                    {/* Step indicator */}
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-xl font-bold text-white/35 group-hover:text-teal-400/50 transition-colors">
                        {step.num}
                      </span>
                      <span className={`text-[10px] font-medium px-2.5 py-0.5 rounded-full border ${step.badgeColor} whitespace-nowrap shrink-0`}>
                        {step.tag}
                      </span>
                    </div>

                    {/* Icon */}
                    <div className="w-9 h-9 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                      {step.icon}
                    </div>

                    <h3 className="text-sm font-semibold text-white tracking-normal mb-1">
                      {step.title}
                    </h3>
                    <div className="text-xs font-medium text-teal-400/90 mb-2">{step.subtitle}</div>
                    <p className="text-xs text-white/55 leading-relaxed">{step.desc}</p>
                  </div>

                  {step.stat && (
                    <div className="mt-4 pt-2.5 border-t border-white/6 text-[11px] font-medium text-white/50">
                      {step.stat}
                    </div>
                  )}
                </div>
              </div>
            </ScrollReveal>
          ))}
        </div>
      </div>
    </section>
  );
}
