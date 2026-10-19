"use client";

import React from "react";
import { Zap, ShieldCheck, Cpu, Globe2, Network } from "lucide-react";
import ScrollReveal from "./ScrollReveal";
import { GlowingEffect } from "./ui/glowing-effect";

export default function BentoGridFeatures() {
  const features = [
    {
      icon: <Network className="w-5 h-5 text-teal-400" />,
      title: "Fan-Out / Fan-In Multi-Agent Swarm",
      desc: "START branches concurrently into Flight, Hotel, and Weather MCP agents, synchronizing into Itinerary & Final Dossier agents to cut execution time by over 50%.",
      tag: "LangGraph Fan-Out/In",
      colSpan: "md:col-span-2",
      accentColor: "rgba(45, 212, 191, 0.12)",
      borderColor: "rgba(45, 212, 191, 0.2)",
      tagColor: "text-teal-400",
    },
    {
      icon: <Cpu className="w-5 h-5 text-sky-400" />,
      title: "Hybrid Two-Tier LLM & Fallback",
      desc: "Fast Groq 20B (~0.5s) for destination extraction + Smart Groq 120B for deep reasoning, with automatic zero-downtime failover to Google Gemini 3.5 Flash Lite.",
      tag: "Groq 120B + Gemini",
      colSpan: "md:col-span-1",
      accentColor: "rgba(56, 189, 248, 0.1)",
      borderColor: "rgba(56, 189, 248, 0.2)",
      tagColor: "text-sky-400",
    },
    {
      icon: <Globe2 className="w-5 h-5 text-indigo-400" />,
      title: "Model Context Protocol (MCP)",
      desc: "AviationStack MCP (live routes/taxes), Tavily Remote MCP (hotel intelligence), and OpenWeatherMap FastMCP server ensure zero-hallucination real-time grounding.",
      tag: "FastMCP Standard",
      colSpan: "md:col-span-1",
      accentColor: "rgba(129, 140, 248, 0.1)",
      borderColor: "rgba(129, 140, 248, 0.2)",
      tagColor: "text-indigo-400",
    },
    {
      icon: <ShieldCheck className="w-5 h-5 text-emerald-400" />,
      title: "Dual PostgreSQL Memory (Checkpointer + Store)",
      desc: "PostgresSaver tracks short-term thread states and active turn recovery, while PostgresStore durably retains traveler preferences across long-term sessions.",
      tag: "ACID Guaranteed",
      colSpan: "md:col-span-2",
      accentColor: "rgba(52, 211, 153, 0.1)",
      borderColor: "rgba(52, 211, 153, 0.2)",
      tagColor: "text-emerald-400",
    },
  ];

  return (
    <section className="w-full py-24 px-4 relative z-10 scroll-reveal-native" id="features">
      <div className="max-w-5xl mx-auto">
        {/* Section Header */}
        <ScrollReveal direction="up" durationMs={800}>
          <div className="flex flex-col items-center text-center mb-14">
            <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-teal-500/10 border border-teal-500/20 text-xs font-mono text-teal-400 mb-4">
              <Zap className="w-3.5 h-3.5" />
              <span>Autonomous Intelligence</span>
            </div>
            <h2 className="text-3xl sm:text-4xl font-bold text-white tracking-tight">
              Why TourAI Multi-Agent Infrastructure?
            </h2>
            <p className="text-sm text-white/50 max-w-lg mx-auto mt-3 leading-relaxed">
              Traditional travel apps rely on manual filters. TourAI dispatches dedicated autonomous agents
              with real-time tool-calling capabilities across your entire network.
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

                <div className="relative z-10">
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
                    <span className={`text-[10px] font-mono px-2.5 py-1 rounded-full bg-white/5 border border-white/8 ${item.tagColor}`}>
                      {item.tag}
                    </span>
                  </div>

                  <h3 className="text-lg font-semibold text-white mb-2 tracking-tight">{item.title}</h3>
                  <p className="text-xs text-white/55 leading-relaxed">{item.desc}</p>
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
