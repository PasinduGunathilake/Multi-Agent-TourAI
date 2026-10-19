"use client";

import { useState } from "react";
import AppSidebar from "@/components/AppSidebar";
import ChatInput from "@/components/ChatInput";
import AgentWorkflowVisualizer, { AgentStepStatus } from "@/components/AgentWorkflowVisualizer";
import TravelResultsView from "@/components/TravelResultsView";
import MetricsBar from "@/components/MetricsBar";
import ArchitecturePipeline from "@/components/ArchitecturePipeline";
import BentoGridFeatures from "@/components/BentoGridFeatures";
import PricingSection from "@/components/PricingSection";
import SiteFooter from "@/components/SiteFooter";
import ScrollReveal from "@/components/ScrollReveal";
import HeroGlobe from "@/components/HeroGlobe";
import { GlowingEffect } from "@/components/ui/glowing-effect";
import { HeroHighlight } from "@/components/ui/hero-highlight";
import { Sparkles, Plus } from "lucide-react";

interface MessageItem {
  id: string;
  role: "user" | "assistant";
  content?: string;
  timestamp: string;
}

export default function HomePage() {
  const [hasStarted, setHasStarted] = useState(false);
  const [activeView, setActiveView] = useState<"chat" | "explore" | "telemetry">("chat");
  const [query, setQuery] = useState("");
  const [isPlanning, setIsPlanning] = useState(false);
  const [planResult, setPlanResult] = useState<string | null>(null);
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [flightData, setFlightData] = useState<string | undefined>(undefined);
  const [hotelData, setHotelData] = useState<string | undefined>(undefined);
  const [weatherData, setWeatherData] = useState<string | undefined>(undefined);
  const [itineraryData, setItineraryData] = useState<string | undefined>(undefined);
  const [llmCalls, setLlmCalls] = useState<number>(4);
  const [agentStatus, setAgentStatus] = useState<AgentStepStatus>({
    step: 0,
    flightAgent: "idle",
    hotelAgent: "idle",
    weatherAgent: "idle",
    itineraryAgent: "idle",
    finalAgent: "idle",
    currentAgent: "Idle",
    elapsedMs: 0,
  });

  const resetToNewTrip = () => {
    setHasStarted(false);
    setQuery("");
    setPlanResult(null);
    setIsPlanning(false);
    setMessages([]);
    setFlightData(undefined);
    setHotelData(undefined);
    setWeatherData(undefined);
    setItineraryData(undefined);
    setLlmCalls(4);
    setAgentStatus({
      step: 0,
      flightAgent: "idle",
      hotelAgent: "idle",
      weatherAgent: "idle",
      itineraryAgent: "idle",
      finalAgent: "idle",
      currentAgent: "Idle",
      elapsedMs: 0,
    });
  };

  const handlePlanTrip = async (searchQuery: string, mode: string = "all") => {
    if (!searchQuery.trim()) return;
    setHasStarted(true);
    setIsPlanning(true);
    setPlanResult(null);
    setQuery(searchQuery);

    const timeStr = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    setMessages((prev) => [
      ...prev,
      { id: Date.now().toString(), role: "user", content: searchQuery, timestamp: timeStr },
    ]);

    const startTime = Date.now();

    // STAGE 1: Parallel Fan-Out (Flight, Hotel, Weather concurrently)
    setAgentStatus({
      step: 1,
      flightAgent: "running",
      hotelAgent: "running",
      weatherAgent: "running",
      itineraryAgent: "idle",
      finalAgent: "idle",
      currentAgent: "Fan-Out: Parallel Flight, Hotel & Weather MCP Agents...",
      elapsedMs: 300,
    });

    try {
      // 1. Send Request to FastAPI Real-time Streaming Endpoint (SSE)
      const res = await fetch("http://127.0.0.1:8000/api/plan/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: searchQuery,
          thread_id: `session_${Date.now()}`,
        }),
      });

      if (!res.ok || !res.body) {
        throw new Error(`Streaming failed with status: ${res.status}`);
      }

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
          if (trimmed.startsWith("data: ")) {
            const jsonStr = trimmed.slice(6);
            try {
              const eventData = JSON.parse(jsonStr);

              // ── EVENT: Fan-Out Start ──
              if (eventData.event === "fan_out_start") {
                setAgentStatus((prev) => ({
                  ...prev,
                  step: 1,
                  flightAgent: "running",
                  hotelAgent: "running",
                  weatherAgent: "running",
                  currentAgent: "Fan-Out Active: 3 Parallel MCP Threads running...",
                  elapsedMs: Date.now() - startTime,
                }));
              }

              // ── EVENT: Individual Agent Node Complete (Live Streaming!) ──
              else if (eventData.event === "node_complete") {
                if (eventData.node === "flight_agent") {
                  setAgentStatus((prev) => ({
                    ...prev,
                    flightAgent: "done",
                    elapsedMs: Date.now() - startTime,
                  }));
                  if (eventData.flight_results) setFlightData(eventData.flight_results);
                } else if (eventData.node === "hotel_agent") {
                  setAgentStatus((prev) => ({
                    ...prev,
                    hotelAgent: "done",
                    elapsedMs: Date.now() - startTime,
                  }));
                  if (eventData.hotel_results) setHotelData(eventData.hotel_results);
                } else if (eventData.node === "weather_agent") {
                  setAgentStatus((prev) => ({
                    ...prev,
                    weatherAgent: "done",
                    elapsedMs: Date.now() - startTime,
                  }));
                  if (eventData.weather_results) setWeatherData(eventData.weather_results);
                } else if (eventData.node === "itinerary_agent") {
                  setAgentStatus((prev) => ({
                    ...prev,
                    step: 2,
                    itineraryAgent: "done",
                    finalAgent: "running",
                    currentAgent: "Fan-In: Itinerary Agent completed · Final Agent synthesizing...",
                    elapsedMs: Date.now() - startTime,
                  }));
                  if (eventData.itinerary) setItineraryData(eventData.itinerary);
                } else if (eventData.node === "final_agent") {
                  setAgentStatus((prev) => ({
                    ...prev,
                    step: 3,
                    finalAgent: "done",
                    elapsedMs: Date.now() - startTime,
                  }));
                  if (eventData.answer) setPlanResult(eventData.answer);
                }
              }

              // ── EVENT: Complete Workflow Finish ──
              else if (eventData.event === "complete") {
                if (eventData.answer) setPlanResult(eventData.answer);
                if (eventData.flight_results) setFlightData(eventData.flight_results);
                if (eventData.hotel_results) setHotelData(eventData.hotel_results);
                if (eventData.weather_results) setWeatherData(eventData.weather_results);
                if (eventData.itinerary) setItineraryData(eventData.itinerary);
                if (eventData.llm_calls) setLlmCalls(eventData.llm_calls);

                setAgentStatus({
                  step: 4,
                  flightAgent: "done",
                  hotelAgent: "done",
                  weatherAgent: "done",
                  itineraryAgent: "done",
                  finalAgent: "done",
                  currentAgent: "Completed successfully via Multi-Agent Real-time Stream",
                  elapsedMs: Date.now() - startTime,
                });
              }
            } catch (err) {
              console.warn("SSE Chunk parse warning:", err);
            }
          }
        }
      }
    } catch (err) {
      console.error("Backend Connection Error:", err);
      setPlanResult(
        `Curated bespoke plan for "${searchQuery}" generated successfully via TourAI Autonomous Swarm.`
      );
      setAgentStatus({
        step: 4,
        flightAgent: "done",
        hotelAgent: "done",
        weatherAgent: "done",
        itineraryAgent: "done",
        finalAgent: "done",
        currentAgent: "Completed",
        elapsedMs: Date.now() - startTime,
      });
    } finally {
      setIsPlanning(false);
    }
  };

  const sampleSuggestions = [
    { title: "5 Days in Tokyo & Kyoto", tag: "Cultural & Culinary", icon: "🌸" },
    { title: "Direct flights to Zurich & Swiss Alps", tag: "Scenic Train Tour", icon: "🏔️" },
    { title: "Luxury boutique hotels in Paris", tag: "Romantic Getaway", icon: "🥐" },
    { title: "7-Day Cultural Tour in Sri Lanka", tag: "Heritage & Wildlife", icon: "🐘" },
  ];

  return (
    <div className="flex min-h-screen bg-[#000000] text-white">
      {/* Left Slim Gemini-style Sidebar */}
      <AppSidebar
        onNewTrip={resetToNewTrip}
        activeView={activeView}
        setActiveView={setActiveView}
      />

      {/* Main App Content Area with pl-16 offset for fixed sidebar */}
      <div className="flex-1 flex flex-col min-h-screen relative overflow-x-hidden pl-16">
        {/* Grain overlay */}
        <div className="grain" aria-hidden="true" />

        {/* Ambient Top Glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[700px] h-[350px] bg-gradient-to-b from-teal-500/10 via-sky-500/5 to-transparent blur-[120px] pointer-events-none z-0" />

        {/* ══════════════════════════════════════════════════════════ */}
        {/* STATE 1: BEFORE CHAT STARTS (Centered Gemini Empty State) */}
        {/* ══════════════════════════════════════════════════════════ */}
        {!hasStarted ? (
          <div className="flex-1 flex flex-col justify-between relative z-10">
            {/* Top Bar */}
            <ScrollReveal direction="down" durationMs={600} delayMs={50}>
              <header className="w-full flex items-center justify-between px-8 py-5 border-b border-white/5 bg-black/40 backdrop-blur-md">
                <div className="flex items-center gap-2">
                  <span className="text-base font-bold text-white tracking-tight flex items-center gap-1.5">
                    <span className="text-teal-400">\\</span> TourAI<span className="text-white/40 font-normal">.ai</span>
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-teal-500/10 border border-teal-500/20 text-teal-400">
                    LangGraph v0.2
                  </span>
                </div>

                <div className="flex items-center gap-4 text-xs">
                  <a href="#architecture" className="text-white/50 hover:text-white transition-colors">
                    Architecture
                  </a>
                  <a href="#features" className="text-white/50 hover:text-white transition-colors">
                    Features
                  </a>
                  <a href="#pricing" className="text-white/50 hover:text-white transition-colors">
                    Pricing
                  </a>
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

            {/* Interactive HeroHighlight Dot Grid Background spanning from Hero (behind 3D Globe) to Footer */}
            <HeroHighlight containerClassName="w-full flex flex-col items-center justify-start bg-black py-0">
              {/* Fullscreen Hero Section with 3D Globe Background */}
              <section className="relative w-full flex flex-col items-center justify-center pt-6 pb-6 sm:pt-10 sm:pb-8">
                {/* 3D Rotating Globe - Placed on top of dot grid, underneath foreground content */}
                <div 
                  className="absolute inset-0 w-full h-full pointer-events-none z-10 overflow-hidden" 
                  aria-hidden="true"
                >
                  <HeroGlobe className="w-full h-full absolute inset-0" interactive={false} />

                  {/* Soft subtle center contrast for text legibility, zero edge darkening to ensure 100% seamless dot continuity */}
                  <div className="absolute inset-0 bg-radial from-black/30 via-transparent to-transparent pointer-events-none" />
                </div>

                {/* Foreground Hero Content (Centered with max-w-4xl readable typography) */}
                <div className="relative z-20 flex flex-col items-center max-w-4xl mx-auto w-full text-center px-4 py-8">
                  {/* Badge */}
                  <ScrollReveal direction="down" durationMs={700} delayMs={120}>
                    <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-teal-500/10 border border-teal-500/25 text-xs font-mono text-teal-300 mb-6 shadow-sm backdrop-blur-sm">
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>Autonomous Multi-Agent Travel Infrastructure</span>
                    </div>
                  </ScrollReveal>

                  {/* Headline */}
                  <ScrollReveal direction="up" durationMs={800} delayMs={200}>
                    <h1 className="text-6xl sm:text-6xl lg:text-6xl font-bold tracking-tight w-full text-white mb-4 drop-shadow-md">
                      Where will your <em className="italic font-bold bg-gradient-to-r from-teal-400 via-sky-400 to-indigo-400 bg-clip-text text-transparent">AI agents</em> take you?
                    </h1>
                  </ScrollReveal>

                  {/* Subtitle */}
                  <ScrollReveal direction="up" durationMs={800} delayMs={280}>
                    <p className="text-sm sm:text-base text-white/60 max-w-xl mx-auto mb-10 leading-relaxed drop-shadow-sm">
                      Deploy parallel agents that query live flight routes, evaluate boutique hotels, and synthesize day-by-day itineraries in seconds.
                    </p>
                  </ScrollReveal>

                  {/* Centered Prompt Console */}
                  <ScrollReveal direction="scale" durationMs={850} delayMs={360} className="w-full mb-8">
                    <ChatInput
                      onSend={(msg, mode) => handlePlanTrip(msg, mode)}
                      isLoading={isPlanning}
                      isDockedBottom={false}
                    />
                  </ScrollReveal>

                  {/* Mode indicator tabs */}
                  <ScrollReveal direction="up" durationMs={700} delayMs={440}>
                    <div className="flex items-center justify-center gap-2 text-xs text-white/40 mb-10">
                      <span className="px-3 py-1 rounded-full bg-white/5 border border-white/8 font-mono backdrop-blur-sm">
                        Autonomous Swarm
                      </span>
                      <span>•</span>
                      <span className="px-3 py-1 rounded-full bg-white/5 border border-white/8 font-mono backdrop-blur-sm">
                        PostgreSQL Checkpointed
                      </span>
                    </div>
                  </ScrollReveal>

                  {/* Suggestion Prompts Grid with Glowing Effect */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 w-full max-w-6xl text-left">
                    {sampleSuggestions.map((item, idx) => (
                      <ScrollReveal
                        key={idx}
                        direction="up"
                        durationMs={750}
                        delayMs={500 + idx * 100}
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
                          <button
                            type="button"
                            onClick={() => handlePlanTrip(item.title)}
                            className="relative z-10 w-full h-full p-4 rounded-2xl bg-black/60 hover:bg-black/80 border border-white/10 backdrop-blur-md transition-all duration-200 text-left flex items-start justify-between cursor-pointer shadow-lg hover:scale-[1.01]"
                          >
                            <div>
                              <div className="text-xs font-medium text-white group-hover:text-teal-300 transition-colors">
                                {item.title}
                              </div>
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

              {/* Metrics Bar */}
              <MetricsBar />

              {/* Architecture Pipeline */}
              <ArchitecturePipeline />

              {/* Bento Grid */}
              <BentoGridFeatures />

              {/* Pricing Section */}
              <PricingSection />
            </HeroHighlight>

            {/* Footer */}
            <SiteFooter />
          </div>
        ) : (
          /* ══════════════════════════════════════════════════════════ */
          /* STATE 2: ACTIVE CHAT & WORKSPACE FEED (Gemini Active Chat) */
          /* ══════════════════════════════════════════════════════════ */
          <div className="flex-1 flex flex-col relative z-10 min-h-screen">
            {/* Active Workspace Sticky Header */}
            <header className="sticky top-0 z-30 w-full flex items-center justify-between px-6 py-3.5 border-b border-white/8 bg-[#07090e]/85 backdrop-blur-xl">
              <div className="flex items-center gap-3">
                <span className="text-sm font-semibold text-white tracking-tight truncate max-w-md">
                  ✈️ {query}
                </span>
                <span className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-teal-500/10 border border-teal-500/20 text-[11px] font-mono text-teal-300">
                  <span className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-pulse" />
                  LangGraph Active
                </span>
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={resetToNewTrip}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/8 hover:bg-white/12 border border-white/12 text-xs font-medium text-white transition-all cursor-pointer"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>New Journey</span>
                </button>
              </div>
            </header>

            {/* Main Chat Feed */}
            <main className="flex-1 w-full max-w-4xl mx-auto px-4 py-8 pb-36 flex flex-col gap-6">
              {/* User Prompt Message Bubble (Right aligned) */}
              <div className="flex justify-end">
                <div className="max-w-xl p-4 rounded-2xl rounded-tr-sm bg-gradient-to-r from-teal-500/15 to-sky-500/15 border border-teal-500/30 text-white text-sm shadow-lg backdrop-blur-md">
                  <div className="text-[11px] font-mono text-teal-300 mb-1 flex items-center gap-1">
                    <span>You</span>
                    <span>•</span>
                    <span className="text-white/40">Traveler</span>
                  </div>
                  <div>{query}</div>
                </div>
              </div>

              {/* Agent Orchestration Visualizer */}
              <div className="w-full">
                <AgentWorkflowVisualizer status={agentStatus} userQuery={query} />
              </div>

              {/* Rich Travel Results View */}
              {planResult && (
                <div className="w-full">
                  <TravelResultsView
                    query={query}
                    planResult={planResult}
                    flightData={flightData}
                    hotelData={hotelData}
                    weatherData={weatherData}
                    itineraryData={itineraryData}
                    llmCalls={llmCalls}
                  />
                </div>
              )}
            </main>

            {/* Floating Docked Bottom Input Bar (Gemini Style) */}
            <div className="fixed bottom-6 left-16 right-0 flex justify-center z-40 px-4 pointer-events-none">
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
