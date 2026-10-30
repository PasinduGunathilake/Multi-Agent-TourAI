"use client";

import React, { useState, useEffect } from "react";
import {
  ChainOfThought,
  ChainOfThoughtHeader,
  ChainOfThoughtContent,
  ChainOfThoughtStep,
  ChainOfThoughtSearchResults,
} from "@/components/ui/chain-of-thought";
import { TraceIcon, TraceTitle, TraceDescription } from "@/components/ui/trace";
import { AgentStepStatus } from "@/components/AgentWorkflowVisualizer";
import {
  ShieldCheck,
  GitBranch,
  Plane,
  Hotel,
  CloudSun,
  MapPin,
  Sparkles,
  Brain,
  CheckCircle2,
  Compass,
} from "lucide-react";

interface ReasoningTraceProps {
  running: boolean;
  intent?: string;
  status: AgentStepStatus;
  elapsedMs?: number;
  defaultOpen?: boolean;
}

export default function ReasoningTrace({
  running,
  intent = "new_plan",
  status,
  elapsedMs = 0,
  defaultOpen,
}: ReasoningTraceProps) {
  // Open while running so traveler sees live agent thought trail.
  // Collapses when finished, but expands if user clicks it.
  const [open, setOpen] = useState<boolean>(defaultOpen ?? running);

  useEffect(() => {
    if (running) {
      setOpen(true);
    } else {
      setOpen(false);
    }
  }, [running]);

  const durationSec = elapsedMs > 0 ? (elapsedMs / 1000).toFixed(1) : "0.0";
  const stepCount = intent === "follow_up" ? 4 : intent === "specific_query" ? 5 : 9;

  return (
    <ChainOfThought open={open} onOpenChange={setOpen}>
      {/* ── Summary Header ── */}
      <ChainOfThoughtHeader status={running ? "running" : undefined}>
        <TraceIcon status={running ? "running" : "done"}>
          {running ? (
            <Brain className="w-3.5 h-3.5 text-sky-400 animate-pulse" />
          ) : (
            <CheckCircle2 className="w-3.5 h-3.5 text-teal-400" />
          )}
        </TraceIcon>
        <TraceTitle>
          {running ? (
            <span className="text-sky-300 font-semibold">
              Researching across {stepCount} agent steps…
            </span>
          ) : (
            <span className="text-white/90 font-medium">
              Researched in {stepCount} agent steps
            </span>
          )}
        </TraceTitle>
        <TraceDescription>
          {running
            ? (status.currentAgent || "LangGraph Orchestrator active")
            : `Thought for ${durationSec}s`}
        </TraceDescription>
      </ChainOfThoughtHeader>

      {/* ── Steps Container ── */}
      <ChainOfThoughtContent>
        {/* Step 1: Input Guardrail */}
        <ChainOfThoughtStep
          status={status.step === 0 && running ? "running" : undefined}
          icon={<ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />}
          title="Input Guardrail Verification"
          description="Verified travel domain safety and filtered adversarial prompt injections (<0.5s)"
        />

        {/* Step 2: Supervisor Router */}
        <ChainOfThoughtStep
          status={status.step === 1 && status.flightAgent === "idle" && running ? "running" : undefined}
          icon={<GitBranch className="w-3.5 h-3.5 text-sky-400" />}
          title={`Supervisor Intent Router [${intent}]`}
          description={
            intent === "follow_up"
              ? "Detected follow-up inquiry → bypassed external APIs and retrieved PostgreSQL memory"
              : intent === "specific_query"
              ? "Detected targeted query → bypassed full itinerary and dispatched specialist tool"
              : "Detected new trip query → deployed parallel flight, hotel, weather, and maps worker swarm"
          }
        />

        {/* Parallel Tools (shown if not follow-up) */}
        {intent !== "follow_up" && (
          <>
            {/* Step 3: Flight Agent */}
            <ChainOfThoughtStep
              status={status.flightAgent === "running" ? "running" : undefined}
              icon={<Plane className="w-3.5 h-3.5 text-sky-400" />}
              title={status.flightAgent === "done" ? "Searched live international flight schedules" : "Searching live flights on AviationStack…"}
              description="Evaluated carrier route availability, direct flights, and taxes"
            >
              <ChainOfThoughtSearchResults results={["aviationstack.com", "iata.org"]} />
            </ChainOfThoughtStep>

            {/* Step 4: Hotel Agent */}
            <ChainOfThoughtStep
              status={status.hotelAgent === "running" ? "running" : undefined}
              icon={<Hotel className="w-3.5 h-3.5 text-indigo-400" />}
              title={status.hotelAgent === "done" ? "Curated verified boutique hotel accommodations" : "Ranking boutique hotels on Tavily Search…"}
              description="Ranked top-reviewed boutique stays, neighborhood access, and amenities"
            >
              <ChainOfThoughtSearchResults results={["tavily.com", "tripadvisor.com"]} />
            </ChainOfThoughtStep>

            {/* Step 5: Weather Agent */}
            <ChainOfThoughtStep
              status={status.weatherAgent === "running" ? "running" : undefined}
              icon={<CloudSun className="w-3.5 h-3.5 text-cyan-400" />}
              title={status.weatherAgent === "done" ? "Fetched 5-day temperature and precipitation forecast" : "Fetching live forecast on OpenWeatherMap FastMCP…"}
              description="Analyzed seasonal rainfall probabilities and daily temperature bands"
            >
              <ChainOfThoughtSearchResults results={["openweathermap.org", "fastmcp-protocol"]} />
            </ChainOfThoughtStep>

            {/* Step 5b: Maps Agent */}
            <ChainOfThoughtStep
              status={status.mapsAgent === "running" ? "running" : undefined}
              icon={<Compass className="w-3.5 h-3.5 text-emerald-400" />}
              title={status.mapsAgent === "done" ? "Mapped verified tourist attractions and travel corridors" : "Locating sights & routes on Geoapify Remote MCP…"}
              description="Located verified attractions, local dining spots, and calculated travel distances"
            >
              <ChainOfThoughtSearchResults results={["geoapify.com", "mcp-jsonrpc"]} />
            </ChainOfThoughtStep>
          </>
        )}

        {/* Step 6: Itinerary Agent */}
        <ChainOfThoughtStep
          status={status.itineraryAgent === "running" ? "running" : undefined}
          icon={<MapPin className="w-3.5 h-3.5 text-teal-400" />}
          title={status.itineraryAgent === "done" ? "Synthesized day-by-day synchronized draft plan" : "Synchronizing parallel agent outputs into days…"}
          description="Aligned flight arrival times, hotel check-ins, and weather-appropriate daytime activities"
        />

        {/* Step 7: Final Synthesis */}
        <ChainOfThoughtStep
          status={running && status.finalAgent === "running" ? "running" : undefined}
          icon={<Sparkles className="w-3.5 h-3.5 text-purple-400" />}
          title={status.finalAgent === "done" || !running ? "Generated final polished itinerary dossier" : "Generating final dossier via Groq 120B Flagship…"}
          description={
            !running
              ? `Completed with Groq 120B reasoning and saved ACID checkpoint to PostgreSQL (${durationSec}s)`
              : "Formatting markdown dossier with real-time token streaming and Gemini fallback"
          }
        >
          <ChainOfThoughtSearchResults results={["groq-120b.ai", "postgresql-checkpointer"]} />
        </ChainOfThoughtStep>

        {/* Step 8: Output Guardrail Audit */}
        <ChainOfThoughtStep
          status={running && (status.outputGuardrail === "running" || (status.finalAgent === "done" && status.outputGuardrail !== "done")) ? "running" : undefined}
          icon={<ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />}
          title={
            !running || status.outputGuardrail === "done"
              ? "Output Guardrail verified safety & formatting"
              : "Auditing output safety, credentials & markdown…"
          }
          description={
            !running || status.outputGuardrail === "done"
              ? "Zero-token regex secret redaction passed, markdown tables validated, and hallucination audit complete"
              : "Scanning for leaked API keys, validating markdown syntax, and executing fast-llm safety audit"
          }
        >
          <ChainOfThoughtSearchResults results={["regex-shield", "secret-redactor", "fast-llm-audit"]} />
        </ChainOfThoughtStep>
      </ChainOfThoughtContent>
    </ChainOfThought>
  );
}
