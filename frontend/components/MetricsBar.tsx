"use client";

import React from "react";
import { Route, Zap, Globe, ShieldCheck } from "lucide-react";
import ScrollReveal from "./ScrollReveal";
import { GlowingEffect } from "./ui/glowing-effect";

export default function MetricsBar() {
  const metrics = [
    {
      value: "4.2M+",
      label: "Itineraries Orchestrated",
      icon: <Route className="w-4 h-4 text-teal-400" />,
    },
    {
      value: "< 2.5s",
      label: "Swarm Synthesis Latency",
      icon: <Zap className="w-4 h-4 text-sky-400" />,
    },
    {
      value: "180+",
      label: "Global Carrier Networks",
      icon: <Globe className="w-4 h-4 text-indigo-400" />,
    },
    {
      value: "100%",
      label: "Live Grounded Routes",
      icon: <ShieldCheck className="w-4 h-4 text-emerald-400" />,
    },
  ];

  return (
    <div className="w-full max-w-5xl mx-auto px-4 mt-4 mb-16 relative z-10 scroll-reveal-native">
      <ScrollReveal direction="scale" durationMs={800}>
        <div className="relative rounded-2xl p-[1px] group">
          <GlowingEffect
            spread={40}
            glow={true}
            disabled={false}
            proximity={64}
            inactiveZone={0.01}
            borderWidth={2}
          />
          <div className="relative z-10 grid grid-cols-2 md:grid-cols-4 gap-4 p-5 rounded-2xl bg-[#090d16]/80 border border-white/8 backdrop-blur-xl">
            {metrics.map((m, idx) => (
              <div
                key={idx}
                className="flex flex-col items-center text-center p-3 sm:border-r last:border-r-0 border-white/6"
              >
                <div className="flex items-center gap-1.5 mb-1.5">
                  {m.icon}
                  <span className="text-xl sm:text-2xl font-bold font-mono text-white tracking-tight">
                    {m.value}
                  </span>
                </div>
                <span className="text-xs text-white/45 font-medium">{m.label}</span>
              </div>
            ))}
          </div>
        </div>
      </ScrollReveal>
    </div>
  );
}
