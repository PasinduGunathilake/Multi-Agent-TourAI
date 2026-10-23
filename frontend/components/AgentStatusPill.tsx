"use client";

import React from "react";
import { AgentStepStatus } from "@/components/AgentWorkflowVisualizer";

interface AgentStatusPillProps {
  intent?: "new_plan" | "specific_query" | "follow_up" | string;
  status: AgentStepStatus;
}

const intentConfig: Record<string, { icon: string; label: string; colorClass: string }> = {
  new_plan: {
    icon: "🚀",
    label: "Deploying Flight, Hotel & Weather Agents...",
    colorClass: "text-teal-300 bg-teal-500/10 border-teal-500/25",
  },
  specific_query: {
    icon: "🔎",
    label: "Consulting specialist agent...",
    colorClass: "text-sky-300 bg-sky-500/10 border-sky-500/25",
  },
  follow_up: {
    icon: "🧠",
    label: "Recalling your travel context...",
    colorClass: "text-indigo-300 bg-indigo-500/10 border-indigo-500/25",
  },
  default: {
    icon: "✨",
    label: "Researching...",
    colorClass: "text-teal-300 bg-teal-500/10 border-teal-500/25",
  },
};

export default function AgentStatusPill({ intent, status }: AgentStatusPillProps) {
  const config = (intent && intentConfig[intent]) || intentConfig.default;
  const label = status.currentAgent && status.currentAgent !== "Idle"
    ? status.currentAgent
    : config.label;

  return (
    <div className="flex items-center gap-2.5 py-2">
      <div className="w-6 h-6 rounded-full bg-white/8 border border-white/10 flex items-center justify-center shrink-0 text-sm">
        {config.icon}
      </div>
      <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-mono ${config.colorClass}`}>
        <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
        <span>{label}</span>
        {status.elapsedMs > 0 && (
          <span className="text-white/30 ml-1">{(status.elapsedMs / 1000).toFixed(1)}s</span>
        )}
      </div>
    </div>
  );
}
