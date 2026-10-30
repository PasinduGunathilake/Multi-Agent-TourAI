"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import AppSidebar, { JourneySession } from "@/components/AppSidebar";
import ChatInput from "@/components/ChatInput";
import ChatFeed from "@/components/ChatFeed";
import { ChatTurn } from "@/components/AgentTurnContainer";
import MetricsBar from "@/components/MetricsBar";
import ArchitecturePipeline from "@/components/ArchitecturePipeline";
import BentoGridFeatures from "@/components/BentoGridFeatures";
import SiteFooter from "@/components/SiteFooter";
import ScrollReveal from "@/components/ScrollReveal";
import HeroGlobe from "@/components/HeroGlobe";
import { HeroHighlight } from "@/components/ui/hero-highlight";
import { GlowingEffect } from "@/components/ui/glowing-effect";
import { Plus } from "lucide-react";
import { TypewriterEffect, TypewriterWord } from "@/components/ui/typewriter-effect";


// ── Helpers ──────────────────────────────────────────────────────────────────
const makeId = () => `turn_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
const makeTime = () =>
  new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

const heroWords: TypewriterWord[] = [
  { text: "Where", className: "text-white" },
  { text: "will", className: "text-white" },
  { text: "your", className: "text-white", lineBreakAfter: true },
  {
    text: "AI agents",
    className: "italic font-bold bg-gradient-to-r from-teal-400 via-sky-400 to-indigo-400 bg-clip-text text-transparent pb-2 pt-0.5",
  },
  { text: "take", className: "text-white" },
  { text: "you?", className: "text-white" },
];

const defaultAgentStatus = () => ({
  step: 0,
  flightAgent: "idle" as const,
  hotelAgent: "idle" as const,
  weatherAgent: "idle" as const,
  mapsAgent: "idle" as const,
  itineraryAgent: "idle" as const,
  finalAgent: "idle" as const,
  outputGuardrail: "idle" as const,
  currentAgent: "Initialising...",
  elapsedMs: 0,
});

// ── Main Page Component ──────────────────────────────────────────────────────
export default function HomePage() {
  const [hasStarted, setHasStarted] = useState(false);
  const [activeView, setActiveView] = useState<"chat" | "explore" | "telemetry">("chat");
  const [isPlanning, setIsPlanning] = useState(false);
  const [sessionId, setSessionId] = useState<string>("session_default");

  useEffect(() => {
    setSessionId(`session_${Date.now()}`);
  }, []);

  // ── Multi-Turn Thread ────────────────────────────────────────────────────
  const [turns, setTurns] = useState<ChatTurn[]>([]);

  // Helper: update a single turn by id
  const updateTurn = useCallback((id: string, patch: Partial<ChatTurn>) => {
    setTurns((prev) =>
      prev.map((t) => (t.id === id ? { ...t, ...patch } : t))
    );
  }, []);

  const isSwitchingSessionRef = useRef(false);
  const activeSessionRef = useRef(sessionId);

  useEffect(() => {
    activeSessionRef.current = sessionId;
  }, [sessionId]);

  // ── localStorage: Journey History & Turn Persistence ────────────────────
  const saveSessionToHistory = useCallback(
    (firstQuery: string, currentTurns?: ChatTurn[]) => {
      try {
        const raw = localStorage.getItem("touraiJourneyHistory");
        const history: JourneySession[] = raw ? JSON.parse(raw) : [];
        const existingIdx = history.findIndex((s) => s.sessionId === sessionId);
        const title = firstQuery.slice(0, 45) + (firstQuery.length > 45 ? "..." : "");
        const entry: JourneySession = {
          sessionId,
          title,
          timestamp: makeTime(),
          turnCount: currentTurns ? currentTurns.length : 1,
          turns: currentTurns,
        };

        let updated: JourneySession[];
        if (existingIdx !== -1) {
          updated = [...history];
          updated[existingIdx] = {
            ...updated[existingIdx],
            turnCount: currentTurns ? currentTurns.length : updated[existingIdx].turnCount,
            turns: currentTurns || updated[existingIdx].turns,
          };
        } else {
          updated = [entry, ...history].slice(0, 25);
        }
        localStorage.setItem("touraiJourneyHistory", JSON.stringify(updated));

        if (currentTurns && currentTurns.length > 0) {
          localStorage.setItem(`tourai_session_${sessionId}`, JSON.stringify(currentTurns));
        }
      } catch { /* ignore */ }
    },
    [sessionId]
  );

  // Automatically persist turns whenever turns change for active session (not when switching)
  useEffect(() => {
    if (sessionId && turns.length > 0 && !isSwitchingSessionRef.current) {
      try {
        localStorage.setItem(`tourai_session_${sessionId}`, JSON.stringify(turns));

        // Also update turns inside touraiJourneyHistory for unified integrity
        const raw = localStorage.getItem("touraiJourneyHistory");
        if (raw) {
          const history: JourneySession[] = JSON.parse(raw);
          const idx = history.findIndex((s) => s.sessionId === sessionId);
          if (idx !== -1) {
            history[idx].turns = turns;
            history[idx].turnCount = turns.length;
            localStorage.setItem("touraiJourneyHistory", JSON.stringify(history));
          }
        }
      } catch (err) {
        console.warn("Could not persist session turns:", err);
      }
    }
  }, [turns, sessionId]);

  // ── Reset ────────────────────────────────────────────────────────────────
  const resetToNewTrip = () => {
    isSwitchingSessionRef.current = true;
    setSessionId(`session_${Date.now()}`);
    setHasStarted(false);
    setTurns([]);
    setIsPlanning(false);
    setTimeout(() => {
      isSwitchingSessionRef.current = false;
    }, 100);
  };

  // ── Load existing session (sidebar click) ────────────────────────────────
  const handleLoadSession = async (sid: string) => {
    if (!sid) return;
    isSwitchingSessionRef.current = true;
    setSessionId(sid);
    setIsPlanning(false);

    // 1. Check tourai_session_${sid}
    try {
      const rawTurns = localStorage.getItem(`tourai_session_${sid}`);
      if (rawTurns) {
        const parsed: ChatTurn[] = JSON.parse(rawTurns);
        if (Array.isArray(parsed) && parsed.length > 0) {
          const restored = parsed.map((t) => ({
            ...t,
            isStreaming: false,
            isResuming: false,
          }));
          setTurns(restored);
          setHasStarted(true);
          setTimeout(() => { isSwitchingSessionRef.current = false; }, 100);
          return;
        }
      }
    } catch (err) {
      console.warn("Could not parse saved turns from localStorage:", err);
    }

    // 2. Check touraiJourneyHistory item.turns
    try {
      const raw = localStorage.getItem("touraiJourneyHistory");
      if (raw) {
        const history: JourneySession[] = JSON.parse(raw);
        const found = history.find((s) => s.sessionId === sid);
        if (found?.turns && Array.isArray(found.turns) && found.turns.length > 0) {
          const restored = found.turns.map((t) => ({
            ...t,
            isStreaming: false,
            isResuming: false,
          }));
          setTurns(restored);
          setHasStarted(true);
          setTimeout(() => { isSwitchingSessionRef.current = false; }, 100);
          return;
        }
      }
    } catch {}

    // 3. Fallback: Fetch persisted state from PostgreSQL checkpointer
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/history/${sid}`);
      if (res.ok) {
        const data = await res.json();
        if (data.turns && Array.isArray(data.turns) && data.turns.length > 0) {
          setTurns(data.turns);
          setHasStarted(true);
          localStorage.setItem(`tourai_session_${sid}`, JSON.stringify(data.turns));
          setTimeout(() => { isSwitchingSessionRef.current = false; }, 100);
          return;
        }
      }
    } catch (err) {
      console.warn("Could not fetch session history from backend:", err);
    }

    // 4. For older sessions that didn't have saved turns, create a user query turn from the title!
    try {
      const raw = localStorage.getItem("touraiJourneyHistory");
      if (raw) {
        const history: JourneySession[] = JSON.parse(raw);
        const found = history.find((s) => s.sessionId === sid);
        if (found && found.title) {
          const fallbackTurns: ChatTurn[] = [
            {
              id: `turn_user_${sid}`,
              role: "user",
              userContent: found.title,
              timestamp: found.timestamp || makeTime(),
            },
          ];
          setTurns(fallbackTurns);
          setHasStarted(true);
          setTimeout(() => { isSwitchingSessionRef.current = false; }, 100);
          return;
        }
      }
    } catch {}

    setTurns([]);
    setHasStarted(false);
    setTimeout(() => { isSwitchingSessionRef.current = false; }, 100);
  };

  // ── Main Plan Trip Handler ───────────────────────────────────────────────
  const handlePlanTrip = async (searchQuery: string, _mode: string = "all") => {
    if (!searchQuery.trim() || isPlanning) return;

    setHasStarted(true);
    setIsPlanning(true);

    const startTime = Date.now();
    const userTurnId = makeId();
    const assistantTurnId = makeId();
    const timeStr = makeTime();

    // Add user turn immediately
    const userTurn: ChatTurn = {
      id: userTurnId,
      role: "user",
      userContent: searchQuery,
      timestamp: timeStr,
    };

    // Add assistant placeholder turn
    const assistantTurn: ChatTurn = {
      id: assistantTurnId,
      role: "assistant",
      timestamp: timeStr,
      isStreaming: true,
      agentStatus: defaultAgentStatus(),
    };

    setTurns((prev) => [...prev, userTurn, assistantTurn]);
    saveSessionToHistory(searchQuery);

    try {
      const res = await fetch("http://127.0.0.1:8000/api/plan/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: searchQuery, thread_id: sessionId }),
      });

      if (!res.ok || !res.body) throw new Error(`Stream failed: ${res.status}`);

      const reader = res.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith("data: ")) continue;
          try {
            const ev = JSON.parse(trimmed.slice(6));

            // fan_out_start
            if (ev.event === "fan_out_start") {
              updateTurn(assistantTurnId, {
                intent: "new_plan",
                agentStatus: {
                  ...defaultAgentStatus(),
                  step: 1,
                  flightAgent: "running",
                  hotelAgent: "running",
                  weatherAgent: "running",
                  mapsAgent: "running",
                  currentAgent: "Fan-Out: Parallel Flight, Hotel, Weather & Maps Agents...",
                  elapsedMs: Date.now() - startTime,
                },
              });
            }

            // node_complete
            else if (ev.event === "node_complete") {
              setTurns((prev) =>
                prev.map((t) => {
                  if (t.id !== assistantTurnId) return t;
                  const s = t.agentStatus ?? defaultAgentStatus();
                  const elapsed = Date.now() - startTime;

                  if (ev.node === "supervisor") {
                    return {
                      ...t,
                      intent: ev.intent || t.intent,
                      agentStatus: {
                        ...s,
                        currentAgent:
                          ev.intent === "follow_up"
                            ? "🧠 Recalling your travel context..."
                            : ev.intent === "specific_query"
                            ? "🔎 Consulting specialist agent..."
                            : "🚀 Deploying agent swarm...",
                        elapsedMs: elapsed,
                      },
                    };
                  }
                  if (ev.node === "flight_agent") {
                    return {
                      ...t,
                      flightData: ev.flight_results || t.flightData,
                      agentStatus: { ...s, flightAgent: "done", elapsedMs: elapsed },
                    };
                  }
                  if (ev.node === "hotel_agent") {
                    return {
                      ...t,
                      hotelData: ev.hotel_results || t.hotelData,
                      agentStatus: { ...s, hotelAgent: "done", elapsedMs: elapsed },
                    };
                  }
                  if (ev.node === "weather_agent") {
                    return {
                      ...t,
                      weatherData: ev.weather_results || t.weatherData,
                      agentStatus: { ...s, weatherAgent: "done", elapsedMs: elapsed },
                    };
                  }
                  if (ev.node === "maps_agent") {
                    return {
                      ...t,
                      mapsData: ev.maps_results || t.mapsData,
                      agentStatus: { ...s, mapsAgent: "done", elapsedMs: elapsed },
                    };
                  }
                  if (ev.node === "itinerary_agent") {
                    return {
                      ...t,
                      itineraryData: ev.itinerary || t.itineraryData,
                      agentStatus: {
                        ...s,
                        step: 2,
                        itineraryAgent: "done",
                        finalAgent: "running",
                        currentAgent: "Fan-In: Synthesizing final dossier...",
                        elapsedMs: elapsed,
                      },
                    };
                  }
                  if (ev.node === "final_agent") {
                    return {
                      ...t,
                      agentStatus: {
                        ...s,
                        step: 3,
                        finalAgent: "done",
                        outputGuardrail: "running",
                        currentAgent: "🛡️ Output Guardrail: Auditing safety & format...",
                        elapsedMs: elapsed,
                      },
                    };
                  }
                  if (ev.node === "output_guardrail") {
                    return {
                      ...t,
                      agentStatus: {
                        ...s,
                        step: 4,
                        outputGuardrail: "done",
                        currentAgent: "Complete",
                        elapsedMs: elapsed,
                      },
                    };
                  }
                  return t;
                })
              );
            }

            // token — word-by-word typewriter
            else if (ev.event === "token" && ev.token) {
              setTurns((prev) =>
                prev.map((t) =>
                  t.id === assistantTurnId
                    ? { ...t, planResult: (t.planResult || "") + ev.token }
                    : t
                )
              );
            }

            // approval_required — HITL pause
            else if (ev.event === "approval_required") {
              updateTurn(assistantTurnId, {
                awaitingApproval: true,
                approvalQuestion: ev.question || "Do you approve this itinerary?",
                draftItinerary: ev.draft_itinerary,
                flightData: ev.flight_results || undefined,
                hotelData: ev.hotel_results || undefined,
                weatherData: ev.weather_results || undefined,
                mapsData: ev.maps_results || undefined,
                isStreaming: false,
                agentStatus: {
                  ...defaultAgentStatus(),
                  step: 2,
                  flightAgent: "done",
                  hotelAgent: "done",
                  weatherAgent: "done",
                  mapsAgent: "done",
                  itineraryAgent: "done",
                  currentAgent: "⏸ Awaiting your approval...",
                  elapsedMs: Date.now() - startTime,
                },
              });
              setIsPlanning(false);
              return; // stop processing — stream is paused
            }

            // complete
            else if (ev.event === "complete") {
              updateTurn(assistantTurnId, {
                isStreaming: false,
                planResult: ev.answer || undefined,
                flightData: ev.flight_results || undefined,
                hotelData: ev.hotel_results || undefined,
                weatherData: ev.weather_results || undefined,
                mapsData: ev.maps_results || undefined,
                itineraryData: ev.itinerary || undefined,
                llmCalls: ev.llm_calls,
                agentStatus: {
                  step: 4,
                  flightAgent: "done",
                  hotelAgent: "done",
                  weatherAgent: "done",
                  mapsAgent: "done",
                  itineraryAgent: "done",
                  finalAgent: "done",
                  currentAgent: "Complete",
                  elapsedMs: Date.now() - startTime,
                },
              });
            }

            // error
            else if (ev.event === "error") {
              updateTurn(assistantTurnId, {
                isStreaming: false,
                planResult: `⚠ Agent error: ${ev.message}`,
              });
            }
          } catch { /* ignore JSON parse errors */ }
        }
      }
    } catch (err) {
      console.error("Backend Connection Error:", err);
      updateTurn(assistantTurnId, {
        isStreaming: false,
        planResult: `Connection error. Please ensure the backend is running on http://127.0.0.1:8000`,
      });
    } finally {
      setIsPlanning(false);
    }
  };

  // ── HITL Resume (Approve) ────────────────────────────────────────────────
  const handleApprove = async (turnId: string) => {
    const turn = turns.find((t) => t.id === turnId);
    if (!turn) return;

    updateTurn(turnId, { isResuming: true, approvalResolved: "approved" });
    setIsPlanning(true);
    const startTime = Date.now();

    await runResumeStream(turnId, true, "", startTime);
  };

  // ── HITL Resume (Revise) ─────────────────────────────────────────────────
  const handleRevise = async (turnId: string, feedback: string) => {
    updateTurn(turnId, { isResuming: true, approvalResolved: "revised" });
    setIsPlanning(true);
    const startTime = Date.now();

    await runResumeStream(turnId, false, feedback, startTime);
  };

  // Shared resume stream logic
  const runResumeStream = async (
    turnId: string,
    approved: boolean,
    feedback: string,
    startTime: number
  ) => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/plan/resume/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ thread_id: sessionId, approved, feedback }),
      });

      if (!res.ok || !res.body) throw new Error(`Resume failed: ${res.status}`);

      const reader = res.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith("data: ")) continue;
          try {
            const ev = JSON.parse(trimmed.slice(6));

            if (ev.event === "token" && ev.token) {
              setTurns((prev) =>
                prev.map((t) =>
                  t.id === turnId
                    ? { ...t, planResult: (t.planResult || "") + ev.token, isStreaming: true }
                    : t
                )
              );
            } else if (ev.event === "complete") {
              updateTurn(turnId, {
                isStreaming: false,
                isResuming: false,
                planResult: ev.answer || undefined,
                flightData: ev.flight_results || undefined,
                hotelData: ev.hotel_results || undefined,
                weatherData: ev.weather_results || undefined,
                mapsData: ev.maps_results || undefined,
                itineraryData: ev.itinerary || undefined,
                llmCalls: ev.llm_calls,
              });
            }
          } catch { /* ignore */ }
        }
      }
    } catch (err) {
      console.error("Resume Error:", err);
      updateTurn(turnId, { isStreaming: false, isResuming: false });
    } finally {
      setIsPlanning(false);
    }
  };

  // ── Checkpoint Restore Handler ───────────────────────────────────────────
  const handleRestoreCheckpoint = (targetTurnId: string) => {
    const targetIdx = turns.findIndex((t) => t.id === targetTurnId);
    if (targetIdx !== -1) {
      setTurns(turns.slice(0, targetIdx + 1));
    }
  };

  // ── Sample Suggestions ───────────────────────────────────────────────────
  const sampleSuggestions = [
    { title: "5 Days in Tokyo & Kyoto", tag: "Cultural & Culinary", icon: "🌸" },
    { title: "Direct flights to Zurich & Swiss Alps", tag: "Scenic Train Tour", icon: "🏔️" },
    { title: "Luxury boutique hotels in Paris", tag: "Romantic Getaway", icon: "🥐" },
    { title: "7-Day Cultural Tour in Sri Lanka", tag: "Heritage & Wildlife", icon: "🐘" },
  ];

  // Header intent badge based on latest assistant turn
  const latestAssistantTurn = [...turns].reverse().find((t) => t.role === "assistant");
  const intentBadge =
    latestAssistantTurn?.intent === "follow_up"
      ? { label: "Context Memory", color: "indigo", icon: "🧠" }
      : latestAssistantTurn?.intent === "specific_query"
      ? { label: "Specialist Agent", color: "sky", icon: "🔎" }
      : { label: "Multi-Agent Swarm", color: "teal", icon: "🚀" };

  return (
    <div className="flex min-h-screen bg-[#000000] text-white w-full">
      {/* Permanent Fixed Sidebar (w-64, no toggle needed) */}
      <AppSidebar
        onNewTrip={resetToNewTrip}
        activeView={activeView}
        setActiveView={setActiveView}
        currentSessionId={sessionId}
        onLoadSession={handleLoadSession}
      />

      {/* Main Content Layout — permanently offset by pl-64 */}
      <div className="flex-1 flex flex-col min-h-screen relative overflow-x-hidden pl-64">
        {/* Grain overlay */}
        <div className="grain" aria-hidden="true" />

        {/* ═══════════════════════════════════════════════════ */}
        {/* STATE 1: HERO / EMPTY STATE */}
        {/* ═══════════════════════════════════════════════════ */}
        {!hasStarted ? (
          <div className="flex-1 flex flex-col justify-between relative z-10">
            {/* Top Nav Bar */}
            <ScrollReveal direction="down" durationMs={600} delayMs={50}>
              <header className="w-full flex items-center justify-between px-8 py-5 border-b border-white/5 bg-black/40 backdrop-blur-md">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-white flex items-center justify-center shadow-md shrink-0">
                    <span className="text-black font-black text-sm tracking-tighter">.\\</span>
                  </div>
                  <span className="text-xl font-bold text-white tracking-tight flex items-center">
                    TourAI<span className="text-teal-400">.ai</span>
                  </span>
                  <span className="text-[10px] font-medium px-0.5 py-0.5 text-teal-300 ml-2">
                    Powered by LangGraph
                  </span>
                </div>
                <div className="flex items-center gap-4 text-xs">
                  <a href="#architecture" className="text-white/50 hover:text-white transition-colors">Architecture</a>
                  <a href="#features" className="text-white/50 hover:text-white transition-colors">Features</a>
                  <button
                    type="button"
                    onClick={() => handlePlanTrip("5 Days in Tokyo & Kyoto")}
                    className="px-3.5 py-1.5 rounded-lg bg-white/8 hover:bg-white/12 border border-white/15 text-white font-medium transition-all cursor-pointer"
                  >
                    Quick Demo
                  </button>
                </div>
              </header>
            </ScrollReveal>

            {/* Hero */}
            <HeroHighlight containerClassName="w-full flex flex-col items-center justify-start bg-black py-0">
              <section className="relative w-full flex flex-col items-center justify-center pt-6 pb-6 sm:pt-10 sm:pb-8">
                <div className="absolute inset-0 w-full h-full pointer-events-none z-10 overflow-hidden" aria-hidden="true">
                  <HeroGlobe className="w-full h-full absolute inset-0" interactive={false} />
                </div>

                <div className="relative z-20 flex flex-col items-center max-w-5xl lg:max-w-6xl mx-auto w-full text-center px-4 py-8">

                  <ScrollReveal direction="up" durationMs={800} delayMs={200} className="w-full flex justify-center">
                    <TypewriterEffect
                      words={heroWords}
                      repeatIntervalMs={10000}
                      className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight mb-4 text-white drop-shadow-md w-full"
                      cursorClassName="bg-teal-400 h-8 sm:h-12 lg:h-14"
                    />
                  </ScrollReveal>

                  <ScrollReveal direction="up" durationMs={800} delayMs={280}>
                    <p className="text-medium sm:text-base text-white/60 max-w-xl mx-auto mb-10 leading-relaxed drop-shadow-sm">
                      Deploy parallel agents that query live flight routes, evaluate boutique hotels, and synthesize day-by-day itineraries in seconds.
                    </p>
                  </ScrollReveal>

                  <ScrollReveal direction="scale" durationMs={850} delayMs={360} className="w-full mb-8">
                    <ChatInput
                      onSend={(msg, mode) => handlePlanTrip(msg, mode)}
                      isLoading={isPlanning}
                      isDockedBottom={false}
                    />
                  </ScrollReveal>

                  <div className="grid grid-cols-1 :grid-cols-2 lg:grid-cols-4 gap-4 w-full max-w-6xl text-left">
                    {sampleSuggestions.map((item, idx) => (
                      <ScrollReveal key={idx} direction="up" durationMs={750} delayMs={500 + idx * 100} className="h-full">
                        <div className="relative h-full rounded-2xl p-[1px] group">
                          <GlowingEffect spread={40} glow={true} disabled={false} proximity={64} inactiveZone={0.01} borderWidth={2} />
                          <button
                            type="button"
                            onClick={() => handlePlanTrip(item.title)}
                            className="relative z-10 w-full h-full p-4 rounded-2xl bg-black/60 hover:bg-black/80 border border-white/10 backdrop-blur-md transition-all duration-200 text-left flex items-start justify-between cursor-pointer shadow-lg hover:scale-[1.01]"
                          >
                            <div>
                              <div className="text-xs font-medium text-white group-hover:text-teal-300 transition-colors">{item.title}</div>
                              <div className="text-[11px] text-white/40 mt-1 font-mono">{item.tag}</div>
                            </div>
                            <span className="text-base group-hover:scale-110 transition-transform shrink-0 ml-2">{item.icon}</span>
                          </button>
                        </div>
                      </ScrollReveal>
                    ))}
                  </div>
                </div>
              </section>

              <MetricsBar />
              <ArchitecturePipeline />
              <BentoGridFeatures />
            </HeroHighlight>

            <SiteFooter />
          </div>
        ) : (
          /* ═══════════════════════════════════════════════════ */
          /* STATE 2: CHAT WORKSPACE (Multi-turn Feed)          */
          /* ═══════════════════════════════════════════════════ */
          <div className="flex-1 flex flex-col relative z-10 min-h-screen">
            {/* Sticky Chat Header */}
            <header className="sticky top-0 z-30 w-full flex items-center justify-between px-6 py-3.5 border-b border-white/8 bg-[#07090e]/90 backdrop-blur-xl">
              <div className="flex items-center gap-3 min-w-0">
                {/* Journey title — first user message */}
                <span className="text-medium font-semibold text-white tracking-tight truncate max-w-xs sm:max-w-md">
                  {turns.find((t) => t.role === "user")?.userContent || "New Journey"}
                </span>

                {/* Dynamic Intent Badge */}
                {latestAssistantTurn && (
                  <span className={`hidden sm:inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-mono ${
                    intentBadge.color === "indigo"
                      ? "bg-indigo-500/10 border border-indigo-500/20 text-indigo-300"
                      : intentBadge.color === "sky"
                      ? "bg-sky-500/10 border border-sky-500/20 text-sky-300"
                      : "bg-teal-500/10 border border-teal-500/20 text-teal-300"
                  }`}>
                    <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
                    {intentBadge.icon} {intentBadge.label}
                  </span>
                )}
              </div>

              <button
                type="button"
                onClick={resetToNewTrip}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/8 hover:bg-white/12 border border-white/12 text-xs font-medium text-white transition-all cursor-pointer shrink-0"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>New Journey</span>
              </button>
            </header>

            {/* ── Chat Feed (scrollable multi-turn thread) ── */}
            <main className="flex-1 overflow-y-auto">
              <ChatFeed
                turns={turns}
                onApprove={handleApprove}
                onRevise={handleRevise}
                onRestoreCheckpoint={handleRestoreCheckpoint}
              />
            </main>

            {/* ── Floating Docked Chat Input permanently offset for sidebar (left-64) ── */}
            <div className="fixed bottom-6 left-64 right-0 flex justify-center z-40 px-4 pointer-events-none">
              <div className="pointer-events-auto w-full max-w-3xl">
                <ChatInput
                  onSend={(msg, mode) => handlePlanTrip(msg, mode)}
                  isLoading={isPlanning}
                  isDockedBottom={true}
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
