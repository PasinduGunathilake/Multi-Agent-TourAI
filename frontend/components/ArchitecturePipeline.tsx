"use client";

import React from "react";
import { GitBranch, Sparkles, Database, Cpu, Zap } from "lucide-react";
import ScrollReveal from "./ScrollReveal";
import { GlowingEffect } from "./ui/glowing-effect";

export default function ArchitecturePipeline() {
  const steps = [
    {
      num: "01",
      title: "Fan-Out State Graph",
      subtitle: "LangGraph Asynchronous Branching",
      desc: "Deconstructs query and simultaneously dispatches 3 independent worker agents (Flight, Hotel, Weather) in parallel threads.",
      icon: <GitBranch className="w-5 h-5 text-teal-400" />,
      tag: "Fan-Out Concurrency",
      badgeColor: "border-teal-500/20 bg-teal-500/10 text-teal-400",
    },
    {
      num: "02",
      title: "3-Agent MCP Swarm",
      subtitle: "FastMCP & Remote Protocols",
      desc: "AviationStack MCP queries live flights, Tavily MCP ranks boutique stays, and OpenWeatherMap FastMCP fetches live 5-day forecasts.",
      icon: <Zap className="w-5 h-5 text-sky-400" />,
      tag: "MCP Grounded",
      badgeColor: "border-sky-500/20 bg-sky-500/10 text-sky-400",
    },
    {
      num: "03",
      title: "Fan-In Synthesis & Fallback",
      subtitle: "Groq 120B + Gemini Flash",
      desc: "Synchronizes parallel outputs into Itinerary & Final agents using Groq 120B flagship reasoning with zero-downtime Gemini fallback.",
      icon: <Cpu className="w-5 h-5 text-indigo-400" />,
      tag: "Zero-Downtime Fallback",
      badgeColor: "border-indigo-500/20 bg-indigo-500/10 text-indigo-400",
    },
    {
      num: "04",
      title: "Dual PostgreSQL Memory",
      subtitle: "Checkpointer + Long-Term Store",
      desc: "Thread-safe PostgreSQL Checkpointer for short-term turn replays combined with persistent store for long-term trip memories.",
      icon: <Database className="w-5 h-5 text-emerald-400" />,
      tag: "ACID Guaranteed",
      badgeColor: "border-emerald-500/20 bg-emerald-500/10 text-emerald-400",
    },
  ];

  return (
    <section className="w-full py-24 px-4 relative z-10 scroll-reveal-native" id="architecture">
      <div className="max-w-6xl mx-auto">
        {/* Section Header */}
        <ScrollReveal direction="up" durationMs={800}>
          <div className="flex flex-col items-center text-center mb-16">
            <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-teal-500/10 border border-teal-500/20 text-xs font-mono text-teal-400 mb-4">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Multi-Agent Coordination Pipeline</span>
            </div>
            <h2 className="text-3xl sm:text-4xl font-bold text-white tracking-tight">
              How TourAI Coordinates Agents
            </h2>
            <p className="text-sm text-white/50 max-w-xl mx-auto mt-3 leading-relaxed">
              Production-grade LangGraph Fan-Out / Fan-In state graph with 3 parallel MCP worker nodes, Groq 120B synthesis, and cross-provider Gemini fallback.
            </p>
          </div>
        </ScrollReveal>

        {/* 4-Step Pipeline Cards with staggered reveal */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 relative">
          {steps.map((step, idx) => (
            <ScrollReveal
              key={idx}
              direction="up"
              delayMs={idx * 150}
              durationMs={700}
              className="h-full"
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
                <div className="relative z-10 rounded-2xl p-6 bg-gradient-to-b from-[#0f1420]/95 to-[#080b12]/95 border border-white/8 transition-all duration-300 hover:-translate-y-1 shadow-lg h-full flex flex-col justify-between">
                  <div>
                    {/* Step indicator */}
                    <div className="flex items-center justify-between mb-4">
                      <span className="text-2xl font-black font-mono text-white/20 group-hover:text-teal-400/40 transition-colors">
                        {step.num}
                      </span>
                      <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${step.badgeColor}`}>
                        {step.tag}
                      </span>
                    </div>

                    {/* Icon */}
                    <div className="w-10 h-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                      {step.icon}
                    </div>

                    <h3 className="text-base font-semibold text-white tracking-tight mb-1">
                      {step.title}
                    </h3>
                    <div className="text-xs font-mono text-white/40 mb-3">{step.subtitle}</div>
                    <p className="text-xs text-white/50 leading-relaxed">{step.desc}</p>
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
