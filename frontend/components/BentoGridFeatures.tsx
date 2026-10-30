"use client";

import React from "react";
import { Zap, ShieldCheck, Cpu, GitBranch, UserCheck, Network, Lock } from "lucide-react";
import ScrollReveal from "./ScrollReveal";
import { GlowingEffect } from "./ui/glowing-effect";

export default function BentoGridFeatures() {
  const features = [
    {
      icon: <GitBranch className="w-5 h-5 text-sky-400" />,
      title: "Smart Intent Routing",
      tag: "Supervisor Orchestrator",
      highlight: "Sends every question down the fastest possible route.",
      desc: "Full vacations launch all agents in parallel. Quick lookups (like weather) trigger only 1 specialist agent in ~4–6s. Follow-up questions (like currency conversion) skip external tools entirely and answer from memory in ~1–2s.",
      stat: "⚡ 3 dynamic routes • 1 Fast LLM call (~1s)",
      colSpan: "md:col-span-2",
      accentColor: "rgba(56, 189, 248, 0.12)",
      borderColor: "rgba(56, 189, 248, 0.2)",
      tagColor: "text-sky-400",
    },
    {
      icon: <Lock className="w-5 h-5 text-emerald-400" />,
      title: "Two-Tier Guardrails & Security",
      tag: "Input + Output Gates",
      highlight: "Stops prompt injections early, audits responses, and redacts leaked keys.",
      desc: "Gate 1 (<0.5s): Filters adversarial prompt injections and off-topic requests. Gate 2 (~0.4s): Zero-token regex redacts leaked API keys (Groq, Gemini, Tavily, PostgreSQL) and fast-LLM audits responses for hallucinations.",
      stat: "🛡️ 2-Tier Security • Zero-token regex",
      colSpan: "md:col-span-1",
      accentColor: "rgba(52, 211, 153, 0.1)",
      borderColor: "rgba(52, 211, 153, 0.2)",
      tagColor: "text-emerald-400",
    },
    {
      icon: <Network className="w-5 h-5 text-teal-400" />,
      title: "Parallel Tool Execution",
      tag: "Fan-Out Concurrency",
      highlight: "Runs flights, hotels, weather, and maps/attractions at the same time.",
      desc: "Instead of waiting for one search after another (~35s), all 4 agents run in parallel. The slowest tool sets the clock: max(21s, 8s, 3s, 2s) = ~21s — saving ~14 seconds (35–40% faster). Maps uses Geoapify Remote HTTP MCP (0 LLM overhead).",
      stat: "⚡ ~21s parallel vs ~35s sequential (~35% faster)",
      colSpan: "md:col-span-1",
      accentColor: "rgba(45, 212, 191, 0.12)",
      borderColor: "rgba(45, 212, 191, 0.2)",
      tagColor: "text-teal-400",
    },
    {
      icon: <UserCheck className="w-5 h-5 text-amber-400" />,
      title: "Human-in-the-Loop (HITL) Review",
      tag: "HITL State Pause",
      highlight: "Review, approve, or adjust your travel plan before finalization.",
      desc: "LangGraph's interrupt() pauses the workflow once the itinerary is drafted. You inspect flights, hotels, and schedule, then approve or request changes. Resumes instantly from the saved database checkpoint without repeating tool calls.",
      stat: "⏸️ LangGraph interrupt() • PostgreSQL checkpoint",
      colSpan: "md:col-span-1",
      accentColor: "rgba(251, 191, 36, 0.1)",
      borderColor: "rgba(251, 191, 36, 0.2)",
      tagColor: "text-amber-400",
    },
    {
      icon: <Zap className="w-5 h-5 text-cyan-400" />,
      title: "Dual-Tier Persistent Memory",
      tag: "Session + Long-Term Store",
      highlight: "Remembers your active conversation and your permanent preferences.",
      desc: "Short-Term Memory (PostgresSaver) stores chat history and intermediate outputs per thread. Long-Term Memory (PostgresStore) persists traveler preferences (airlines, dietary rules, budget) across all sessions under ('users', user_id).",
      stat: "🧠 PostgresSaver (thread) + PostgresStore (user)",
      colSpan: "md:col-span-1",
      accentColor: "rgba(6, 182, 212, 0.1)",
      borderColor: "rgba(6, 182, 212, 0.2)",
      tagColor: "text-cyan-400",
    },
    {
      icon: <ShieldCheck className="w-5 h-5 text-indigo-400" />,
      title: "Model Tiering & Zero-Downtime Fallback",
      tag: "Groq LPU + Google Gemini",
      highlight: "Ultra-fast reasoning paired with automatic multi-cloud backup.",
      desc: "Task-based tiering assigns fast gpt-oss-20b (~0.5s) to guardrails/routing, and flagship gpt-oss-120b (~3–6s) to creative itineraries. If Groq encounters rate limits or outages, requests automatically failover to Google Gemini without session interruption.",
      stat: "🔄 Groq 120B ➔ Gemini flash-lite ➔ Groq 20B",
      colSpan: "md:col-span-3",
      accentColor: "rgba(129, 140, 248, 0.1)",
      borderColor: "rgba(129, 140, 248, 0.2)",
      tagColor: "text-indigo-400",
    },
  ];

  return (
    <section className="w-full py-24 px-4 relative z-10 scroll-reveal-native" id="features">
      <div className="max-w-5xl mx-auto">
        {/* Section Header */}
        <ScrollReveal direction="up" durationMs={800}>
          <div className="flex flex-col items-center text-center mb-14">
            <h2 className="text-3xl sm:text-4xl font-bold text-white tracking-tight">
              Built on Modern Agentic Engineering
            </h2>
            <p className="text-sm text-white/50 max-w-xl mx-auto mt-3 leading-relaxed">
              Groq LPU speed (<code className="text-teal-300 font-mono text-[11px]">gpt-oss-20b</code> &amp; <code className="text-indigo-300 font-mono text-[11px]">120b</code>) with Google Gemini failover, Tavily MCP web search (0 LLM), LangGraph HITL interrupt, and PostgreSQL Dual Memory.
            </p>
          </div>
        </ScrollReveal>

        {/* Bento Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {features.map((item, index) => (
            <ScrollReveal
              key={index}
              direction="up"
              delayMs={index * 120}
              durationMs={750}
              className={`${item.colSpan}`}
            >
              <div className="relative h-full rounded-2xl p-[1px] group">
                <GlowingEffect
                  spread={40}
                  glow={true}
                  disabled={false}
                  proximity={64}
                  inactiveZone={0.01}
                  borderWidth={2}
                />
                <div
                  className="relative z-10 rounded-2xl p-7 border transition-all duration-300 hover:scale-[1.01] h-full flex flex-col justify-between overflow-hidden"
                  style={{
                    background: `linear-gradient(135deg, ${item.accentColor} 0%, rgba(10,14,24,0.92) 100%)`,
                    borderColor: item.borderColor,
                    backdropFilter: "blur(20px)",
                  }}
                >
                  {/* Hover glow effect */}
                  <div
                    className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"
                    style={{
                      background: `radial-gradient(circle at 30% 30%, ${item.accentColor} 0%, transparent 60%)`,
                    }}
                  />

                  <div className="relative z-10 flex flex-col h-full justify-between">
                    <div>
                      {/* Icon + Tag row */}
                      <div className="flex items-start justify-between mb-4">
                        <div
                          className="p-2.5 rounded-xl border"
                          style={{
                            background: item.accentColor,
                            borderColor: item.borderColor,
                          }}
                        >
                          {item.icon}
                        </div>
                        <span className={`text-[10px] font-medium px-2.5 py-1 rounded-full bg-white/5 border border-white/8 ${item.tagColor}`}>
                          {item.tag}
                        </span>
                      </div>

                      <h3 className="text-base sm:text-lg font-semibold text-white mb-1.5 tracking-normal">{item.title}</h3>
                      <p className="text-xs font-medium text-white/90 mb-2 leading-snug">{item.highlight}</p>
                      <p className="text-xs text-white/55 leading-relaxed">{item.desc}</p>
                    </div>

                    {item.stat && (
                      <div className="mt-5 pt-3 border-t border-white/8 flex items-center text-[11px] font-medium text-white/60">
                        <span>{item.stat}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </ScrollReveal>
          ))}
        </div>
      </div>
    </section>
  );
}
