"use client";

import React, { useState } from "react";
import { Search, Sparkles, Plane, Hotel, Map, ArrowRight, Compass } from "lucide-react";

interface HeroSearchProps {
  onSearch: (query: string, mode?: string) => void;
  isLoading: boolean;
}

export default function HeroSearch({ onSearch, isLoading }: HeroSearchProps) {
  const [query, setQuery] = useState("");
  const [selectedMode, setSelectedMode] = useState<"all" | "flights" | "hotels" | "itinerary">("all");

  const modes = [
    { id: "all" as const, label: "Full AI Plan", icon: <Sparkles className="w-3.5 h-3.5" />, color: "text-teal-400" },
    { id: "flights" as const, label: "Flights", icon: <Plane className="w-3.5 h-3.5" />, color: "text-sky-400" },
    { id: "hotels" as const, label: "Hotels", icon: <Hotel className="w-3.5 h-3.5" />, color: "text-indigo-400" },
    { id: "itinerary" as const, label: "Itinerary", icon: <Map className="w-3.5 h-3.5" />, color: "text-emerald-400" },
  ];

  const quickPills = [
    "5 Days in Tokyo & Kyoto",
    "Direct flights to Zurich next month",
    "Luxury boutique hotels in Paris",
    "7-Day Scenic Tour in Sri Lanka",
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isLoading) return;
    onSearch(query.trim(), selectedMode);
  };

  return (
    <div className="w-full max-w-3xl mx-auto mt-8 px-4">
      {/* Outer glowing border wrapper */}
      <div
        className="relative rounded-2xl p-[1px]"
        style={{
          background: "linear-gradient(135deg, rgba(45,212,191,0.35), rgba(56,189,248,0.2) 40%, rgba(129,140,248,0.25) 70%, rgba(45,212,191,0.35))",
        }}
      >
        {/* Card */}
        <div
          className="rounded-[15px] p-4 sm:p-5"
          style={{
            background: "rgba(8, 12, 20, 0.9)",
            backdropFilter: "blur(24px)",
            border: "1px solid rgba(255,255,255,0.06)",
          }}
        >
          {/* Mode Selector Tabs */}
          <div className="flex items-center gap-1.5 mb-4 overflow-x-auto pb-0.5">
            {modes.map((mode) => (
              <button
                key={mode.id}
                type="button"
                onClick={() => setSelectedMode(mode.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 cursor-pointer whitespace-nowrap ${
                  selectedMode === mode.id
                    ? "bg-white text-black shadow-md"
                    : "text-white/40 hover:text-white/75 hover:bg-white/6"
                }`}
              >
                <span className={selectedMode === mode.id ? "text-black" : mode.color}>
                  {mode.icon}
                </span>
                {mode.label}
              </button>
            ))}
          </div>

          {/* Input + Submit */}
          <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-2.5">
            <div className="relative flex-1 flex items-center">
              <Search className="absolute left-3.5 w-4 h-4 text-white/25 pointer-events-none" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Where do you want to go? (e.g., 5 days in Tokyo for 2, budget friendly)"
                disabled={isLoading}
                className="w-full pl-10 pr-4 py-3 rounded-xl text-white placeholder-white/25 text-sm font-normal outline-none transition-all"
                style={{
                  background: "rgba(255,255,255,0.04)",
                  border: "1px solid rgba(255,255,255,0.08)",
                }}
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = "rgba(56,189,248,0.4)";
                  e.currentTarget.style.boxShadow = "0 0 20px rgba(56,189,248,0.08)";
                }}
                onBlur={(e) => {
                  e.currentTarget.style.borderColor = "rgba(255,255,255,0.08)";
                  e.currentTarget.style.boxShadow = "none";
                }}
              />
            </div>

            <button
              type="submit"
              disabled={isLoading || !query.trim()}
              className="w-full sm:w-auto px-6 py-3 rounded-xl text-black text-sm font-semibold flex items-center justify-center gap-2 transition-all duration-200 shrink-0 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
              style={{
                background: "linear-gradient(135deg, #2dd4bf, #38bdf8)",
                boxShadow: "0 4px 24px rgba(56,189,248,0.25)",
              }}
            >
              {isLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-black/40 border-t-black rounded-full animate-spin" />
                  <span>Synthesizing...</span>
                </>
              ) : (
                <>
                  <span>Orchestrate Trip</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Quick Suggestion Pills */}
          <div className="mt-3.5 flex items-center gap-2 flex-wrap">
            <span className="flex items-center gap-1 text-[11px] text-white/25 font-medium">
              <Compass className="w-3 h-3" /> Try:
            </span>
            {quickPills.map((pill, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => {
                  setQuery(pill);
                  onSearch(pill, selectedMode);
                }}
                disabled={isLoading}
                className="text-[11px] px-2.5 py-1 rounded-lg text-white/50 hover:text-white/85 transition-colors cursor-pointer"
                style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.07)" }}
              >
                {pill}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
