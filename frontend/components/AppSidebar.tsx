"use client";

import React, { useEffect, useState } from "react";
import {
  Plus,
  Clock,
  Trash2,
} from "lucide-react";

export interface JourneySession {
  sessionId: string;
  title: string;
  timestamp: string;
  turnCount: number;
  turns?: any[];
}

interface AppSidebarProps {
  onNewTrip: () => void;
  activeView?: "chat" | "explore" | "telemetry";
  setActiveView?: (view: "chat" | "explore" | "telemetry") => void;
  currentSessionId?: string;
  onLoadSession?: (sessionId: string) => void;
}

export default function AppSidebar({
  onNewTrip,
  currentSessionId,
  onLoadSession,
}: AppSidebarProps) {
  const [history, setHistory] = useState<JourneySession[]>([]);

  // Load history from localStorage on mount and whenever currentSessionId changes
  useEffect(() => {
    try {
      const raw = localStorage.getItem("touraiJourneyHistory");
      if (raw) setHistory(JSON.parse(raw));
    } catch {
      /* ignore */
    }
  }, [currentSessionId]);

  const deleteSession = async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    const updated = history.filter((s) => s.sessionId !== sessionId);
    setHistory(updated);
    try {
      localStorage.setItem("touraiJourneyHistory", JSON.stringify(updated));
      localStorage.removeItem(`tourai_session_${sessionId}`);
    } catch {
      /* ignore */
    }

    // Purge checkpoints from PostgreSQL backend
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      await fetch(`${baseUrl}/api/session/${sessionId}`, {
        method: "DELETE",
      });
    } catch (err) {
      console.warn("Could not delete session from DB:", err);
    }
  };

  return (
    <aside className="fixed top-0 left-0 bottom-0 z-50 w-64 h-screen bg-[#07090f] border-r border-white/[0.08] flex flex-col justify-between p-3 select-none backdrop-blur-xl font-medium">
      {/* ── 1. Top Section: Brand + New Journey ── */}
      <div className="flex flex-col gap-3 shrink-0">
        {/* Brand Header */}
        <div
          onClick={onNewTrip}
          className="flex items-center gap-2.5 px-1 py-1 cursor-pointer group/brand"
        >
          {/* Modern Square Brand Icon */}
          <div className="w-8 h-8 rounded-lg bg-white flex items-center justify-center shadow-md shrink-0 group-hover/brand:scale-105 transition-transform">
            <span className="text-black font-black text-sm tracking-tighter">.\\</span>
          </div>
          <div className="flex flex-col min-w-0">
            <div className="text-base font-bold text-white tracking-tight flex items-center">
              TourAI <span className="text-teal-400"> .ai</span>
            </div>
          </div>
        </div>

        {/* New Journey Action Button */}
        <button
          type="button"
          onClick={onNewTrip}
          className="w-full flex items-center justify-start gap-2.5 px-3.5 py-2.5 rounded-xl bg-gradient-to-r from-teal-500/15 to-sky-500/10 border border-teal-500/25 text-teal-300 hover:text-white hover:border-teal-400/40 hover:bg-teal-500/20 transition-all text-xs font-medium shadow-sm cursor-pointer"
        >
          <Plus className="w-4 h-4 shrink-0 text-teal-400" />
          <span>New Journey</span>
        </button>
      </div>

      {/* ── 2. Middle Section: Recent Journeys (Full-height Scrollable) ── */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden py-3 space-y-2 custom-scrollbar pr-0.5">
        <div className="px-2 py-1 text-[10px] font-mono font-medium text-white/35 uppercase tracking-wider flex items-center justify-between">
          <span>Recent Journeys</span>
          {history.length > 0 && (
            <span className="text-white/25">({history.length})</span>
          )}
        </div>

        {history.length > 0 ? (
          <div className="space-y-0.5">
            {history.slice(0, 50).map((session) => (
              <div
                key={session.sessionId}
                className="relative group/session"
              >
                <button
                  type="button"
                  onClick={() => onLoadSession?.(session.sessionId)}
                  className={`w-full flex items-start gap-2.5 px-3 py-2 rounded-xl text-xs font-medium transition-all cursor-pointer text-left pr-8 ${
                    session.sessionId === currentSessionId
                      ? "bg-teal-500/12 border border-teal-500/25 text-white"
                      : "text-white/60 hover:text-white hover:bg-white/[0.05] border border-transparent"
                  }`}
                >
                  <Clock className="w-3.5 h-3.5 shrink-0 text-white/35 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <div className="text-[11px] font-medium text-neutral-200 truncate group-hover/session:text-white">
                      {session.title}
                    </div>
                    <div className="text-[9px] text-neutral-500 font-mono font-medium mt-0.5">
                      {session.timestamp}
                    </div>
                  </div>
                </button>

                {/* Delete Button */}
                <button
                  type="button"
                  onClick={(e) => deleteSession(e, session.sessionId)}
                  title="Delete Journey"
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded-md opacity-0 group-hover/session:opacity-100 text-white/30 hover:text-red-400 hover:bg-white/10 transition-all cursor-pointer"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="px-3 py-10 text-center text-white/30 text-xs">
            <Clock className="w-5 h-5 mx-auto mb-2 text-white/20" />
            <p className="text-[11px] text-white/40">No past journeys yet</p>
            <p className="text-[10px] text-white/25 mt-0.5">Trips you plan will appear here</p>
          </div>
        )}
      </div>

    </aside>
  );
}
