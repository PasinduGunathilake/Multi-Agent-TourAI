"use client";

import React, { useState } from "react";
import { Plus, ArrowUp, Sparkles, Plane, Hotel, Map, CloudSun } from "lucide-react";
import { GlowingEffect } from "@/components/ui/glowing-effect";

interface ChatInputProps {
  onSend: (message: string, mode: string) => void;
  isLoading: boolean;
  isDockedBottom?: boolean;
}

export default function ChatInput({
  onSend,
  isLoading,
  isDockedBottom = false,
}: ChatInputProps) {
  const [input, setInput] = useState("");
  const [selectedMode, setSelectedMode] = useState("all");

  const modes = [
    { id: "all", label: "Fan-Out Swarm (5 Agents)", icon: <Sparkles className="w-3.5 h-3.5" /> },
    { id: "flights", label: "Live Flights (AviationStack)", icon: <Plane className="w-3.5 h-3.5" /> },
    { id: "hotels", label: "Boutique Hotels (Tavily)", icon: <Hotel className="w-3.5 h-3.5" /> },
    { id: "weather", label: "Live Weather (FastMCP)", icon: <CloudSun className="w-3.5 h-3.5" /> },
    { id: "itinerary", label: "Curated Itinerary", icon: <Map className="w-3.5 h-3.5" /> },
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    onSend(input.trim(), selectedMode);
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className={`w-full transition-all duration-300 ${isDockedBottom ? "max-w-3xl mx-auto" : "max-w-2xl mx-auto"}`}>
      {/* Outer Pill Container with Glowing Effect */}
      <div className="relative rounded-full p-[1px] shadow-2xl">
        <GlowingEffect
          spread={45}
          glow={true}
          disabled={false}
          proximity={80}
          inactiveZone={0.01}
          borderWidth={2}
        />
        <form
          onSubmit={handleSubmit}
          className={`relative z-10 flex items-center gap-3 px-4 py-3 rounded-full border transition-all duration-300 ${
            isDockedBottom
              ? "bg-[#10141e]/95 border-white/10 backdrop-blur-2xl shadow-black/80"
              : "bg-[#0f1422]/90 border-white/10 backdrop-blur-2xl shadow-cyan-950/20"
          }`}
        >
          {/* Plus / Add context icon */}
          <button
            type="button"
            onClick={() => alert("Multi-Agent Settings: AviationStack (Live Flights) + Tavily (Hotels) Active")}
            className="w-8 h-8 rounded-full bg-white/5 hover:bg-white/10 text-white/50 hover:text-white flex items-center justify-center transition-colors shrink-0 cursor-pointer"
            title="Swarm Context"
          >
            <Plus className="w-4 h-4" />
          </button>

          {/* Input */}
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            placeholder={
              isDockedBottom
                ? "Ask a follow-up or refine this itinerary..."
                : "Ask TourAI to plan a trip, search flights, or curate hotels..."
            }
            className="flex-1 bg-transparent border-none text-sm text-white placeholder-white/35 outline-none font-normal"
          />

          {/* Submit / Send Button */}
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className={`w-9 h-9 rounded-full flex items-center justify-center transition-all duration-200 shrink-0 ${
              input.trim()
                ? "bg-gradient-to-r from-teal-400 to-sky-400 text-black shadow-lg shadow-teal-500/35 hover:shadow-teal-400/50 hover:scale-105 active:scale-95 cursor-pointer"
                : "bg-white/15 border border-white/25 text-white/90 hover:bg-white/20 cursor-not-allowed shadow-sm"
            }`}
            title="Submit to Agent Swarm"
          >
            {isLoading ? (
              <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
            ) : (
              <ArrowUp className="w-4.5 h-4.5 stroke-[2.5]" />
            )}
          </button>
        </form>
      </div>

      {/* Mode Pills (Only shown in centered empty state or subtly under bottom bar) */}
      {!isDockedBottom && (
        <div className="flex items-center justify-center gap-2 mt-4 flex-wrap">
          {modes.map((mode) => (
            <button
              key={mode.id}
              type="button"
              onClick={() => setSelectedMode(mode.id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all cursor-pointer ${
                selectedMode === mode.id
                  ? "bg-white/15 text-white border border-teal-400/40 shadow-sm"
                  : "bg-white/[0.03] text-white/45 hover:text-white/80 border border-white/6 hover:bg-white/[0.07]"
              }`}
            >
              {mode.icon}
              <span>{mode.label}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
