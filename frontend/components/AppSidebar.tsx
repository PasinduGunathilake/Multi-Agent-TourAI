"use client";

import React from "react";
import { Plus, Compass, Database, Settings, Sparkles, MessageSquare } from "lucide-react";

interface AppSidebarProps {
  onNewTrip: () => void;
  activeView: "chat" | "explore" | "telemetry";
  setActiveView: (view: "chat" | "explore" | "telemetry") => void;
}

export default function AppSidebar({
  onNewTrip,
  activeView,
  setActiveView,
}: AppSidebarProps) {
  return (
    <aside className="fixed top-0 left-0 bottom-0 w-16 h-screen bg-[#07090e] border-r border-white/[0.08] flex flex-col items-center justify-between py-5 z-50 shrink-0">
      {/* Top: Brand Logo + New Trip */}
      <div className="flex flex-col items-center gap-6">
        {/* Brand Logo Icon */}
        <button
          type="button"
          onClick={onNewTrip}
          className="w-10 h-10 rounded-xl bg-gradient-to-tr from-teal-500/20 to-sky-500/20 border border-teal-500/30 flex items-center justify-center text-teal-300 hover:scale-105 transition-all shadow-lg shadow-teal-500/10 cursor-pointer"
          title="TourAI Home"
        >
          <Sparkles className="w-5 h-5" />
        </button>

        {/* New Chat / New Journey Button */}
        <button
          type="button"
          onClick={onNewTrip}
          className="w-10 h-10 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 hover:border-teal-400/40 text-white/70 hover:text-white flex items-center justify-center transition-all cursor-pointer group relative"
          title="Start New Journey"
        >
          <Plus className="w-5 h-5 group-hover:rotate-90 transition-transform duration-200" />
          <span className="absolute left-14 px-2.5 py-1 rounded-md bg-black/90 border border-white/10 text-[11px] text-white whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none shadow-xl">
            New Journey
          </span>
        </button>

        <div className="w-6 h-px bg-white/10 my-1" />

        {/* Navigation Actions */}
        <div className="flex flex-col items-center gap-3">
          <button
            type="button"
            onClick={() => setActiveView("chat")}
            className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all cursor-pointer group relative ${
              activeView === "chat"
                ? "bg-teal-500/15 border border-teal-500/30 text-teal-300"
                : "text-white/40 hover:text-white hover:bg-white/5 border border-transparent"
            }`}
            title="Chat & Swarm"
          >
            <MessageSquare className="w-4 h-4" />
            <span className="absolute left-14 px-2.5 py-1 rounded-md bg-black/90 border border-white/10 text-[11px] text-white whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none shadow-xl">
              Travel Swarm
            </span>
          </button>

          <button
            type="button"
            onClick={() => setActiveView("explore")}
            className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all cursor-pointer group relative ${
              activeView === "explore"
                ? "bg-sky-500/15 border border-sky-500/30 text-sky-300"
                : "text-white/40 hover:text-white hover:bg-white/5 border border-transparent"
            }`}
            title="Explore Architecture"
          >
            <Compass className="w-4 h-4" />
            <span className="absolute left-14 px-2.5 py-1 rounded-md bg-black/90 border border-white/10 text-[11px] text-white whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none shadow-xl">
              Architecture & Features
            </span>
          </button>

          <button
            type="button"
            onClick={() => setActiveView("telemetry")}
            className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all cursor-pointer group relative ${
              activeView === "telemetry"
                ? "bg-indigo-500/15 border border-indigo-500/30 text-indigo-300"
                : "text-white/40 hover:text-white hover:bg-white/5 border border-transparent"
            }`}
            title="Agent Telemetry"
          >
            <Database className="w-4 h-4" />
            <span className="absolute left-14 px-2.5 py-1 rounded-md bg-black/90 border border-white/10 text-[11px] text-white whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none shadow-xl">
              PostgreSQL Telemetry
            </span>
          </button>
        </div>
      </div>

      {/* Bottom: Settings & User Indicator */}
      <div className="flex flex-col items-center gap-3">
        <button
          type="button"
          onClick={() => alert("TourAI Multi-Agent v0.2 • LangGraph & Groq LLaMA 3.3 70B Active")}
          className="w-10 h-10 rounded-xl text-white/40 hover:text-white hover:bg-white/5 flex items-center justify-center transition-all cursor-pointer group relative"
          title="System Settings"
        >
          <Settings className="w-4 h-4" />
          <span className="absolute left-14 px-2.5 py-1 rounded-md bg-black/90 border border-white/10 text-[11px] text-white whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none shadow-xl">
            Settings & APIs
          </span>
        </button>

        {/* User Avatar */}
        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-emerald-500 to-teal-400 text-black font-bold text-xs flex items-center justify-center shadow-md">
          P
        </div>
      </div>
    </aside>
  );
}
