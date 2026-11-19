"use client";

import React, { useEffect, useState, useCallback } from "react";
import {
  Plus,
  Clock,
  Trash2,
  LogIn,
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { fetchUserThreads, deleteThreadSession } from "@/lib/api";
import { DropdownMenuProfileDropdownWithStatus } from "@/components/dropdown-menu-profile-dropdown-with-status";

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
  onOpenAuth?: () => void;
}

export default function AppSidebar({
  onNewTrip,
  currentSessionId,
  onLoadSession,
  onOpenAuth,
}: AppSidebarProps) {
  const [history, setHistory] = useState<JourneySession[]>([]);
  const { user, logout, getToken } = useAuth();

  // Load user's threads from backend when user changes or session updates
  const loadThreads = useCallback(async () => {
    if (!user) {
      setHistory([]);
      return;
    }
    try {
      const data = await fetchUserThreads(getToken);
      const mapped: JourneySession[] = (data.threads || []).map((t) => ({
        sessionId: t.thread_id,
        title: t.title || "Untitled Journey",
        timestamp: new Date(t.updated_at).toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
        turnCount: 1,
      }));
      setHistory(mapped);
    } catch (err) {
      console.warn("Could not load threads from backend:", err);
    }
  }, [user, getToken]);

  useEffect(() => {
    loadThreads();
  }, [loadThreads, currentSessionId]);

  const deleteSession = async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    const updated = history.filter((s) => s.sessionId !== sessionId);
    setHistory(updated);

    try {
      localStorage.removeItem(`tourai_session_${sessionId}`);
    } catch {}

    // Purge thread and checkpoints from PostgreSQL backend via authenticated API
    try {
      await deleteThreadSession(sessionId, getToken);
    } catch (err) {
      console.warn("Could not delete session from DB:", err);
      // reload threads to restore consistency if deletion failed
      loadThreads();
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

        {/* Create Journey Action Button */}
        <button
          type="button"
          onClick={onNewTrip}
          className="w-full flex items-center justify-start gap-2.5 px-3.5 py-2.5 rounded-xl bg-gradient-to-r from-teal-600 to-sky-600 hover:from-teal-500 hover:to-sky-500 border border-teal-400/30 text-white font-bold transition-all text-xs shadow-md shadow-teal-950/40 cursor-pointer"
        >
          <Plus className="w-4 h-4 shrink-0 text-white stroke-[2.5]" />
          <span className="text-white font-bold text-xs tracking-tight">Create Journey</span>
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

      {/* ── 3. Bottom Section: User Account & Sign Out ── */}
      <div className="pt-3 border-t border-white/[0.08] shrink-0">
        {user ? (
          <DropdownMenuProfileDropdownWithStatus showDetails={true} className="w-full" />
        ) : (
          <button
            type="button"
            onClick={onOpenAuth}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-xl bg-white/[0.05] hover:bg-white/[0.1] border border-white/[0.08] text-white text-xs font-medium transition-all cursor-pointer"
          >
            <LogIn className="w-3.5 h-3.5 text-teal-400" />
            <span>Sign In</span>
          </button>
        )}
      </div>
    </aside>
  );
}
