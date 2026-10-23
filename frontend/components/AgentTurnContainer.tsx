"use client";

import React from "react";
import { Sparkles } from "lucide-react";
import ReasoningTrace from "@/components/ReasoningTrace";
import HITLReviewCard from "@/components/HITLReviewCard";
import TravelResultsView from "@/components/TravelResultsView";
import { AgentStepStatus } from "@/components/AgentWorkflowVisualizer";

export interface ChatTurn {
  id: string;
  role: "user" | "assistant";

  // User turn
  userContent?: string;
  timestamp: string;

  // Assistant turn fields
  intent?: "new_plan" | "specific_query" | "follow_up" | string;
  agentStatus?: AgentStepStatus;
  isStreaming?: boolean;

  // HITL
  awaitingApproval?: boolean;
  approvalQuestion?: string;
  draftItinerary?: string;
  approvalResolved?: "approved" | "revised" | null;
  isResuming?: boolean;

  // Result artifacts
  planResult?: string;
  flightData?: string;
  hotelData?: string;
  weatherData?: string;
  mapsData?: string;
  itineraryData?: string;
  llmCalls?: number;
}

interface AgentTurnContainerProps {
  turn: ChatTurn;
  onApprove: (turnId: string) => void;
  onRevise: (turnId: string, feedback: string) => void;
}

// TourAI Avatar
function TourAIAvatar() {
  return (
    <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-teal-500/25 to-sky-500/25 border border-teal-500/30 flex items-center justify-center text-teal-400 shrink-0 mt-0.5 shadow-sm shadow-teal-900/30">
      <Sparkles className="w-3.5 h-3.5" />
    </div>
  );
}

export default function AgentTurnContainer({ turn, onApprove, onRevise }: AgentTurnContainerProps) {
  const defaultStatus: AgentStepStatus = {
    step: 0,
    flightAgent: "idle",
    hotelAgent: "idle",
    weatherAgent: "idle",
    mapsAgent: "idle",
    itineraryAgent: "idle",
    finalAgent: "idle",
    currentAgent: "Researching...",
    elapsedMs: 0,
  };

  const status = turn.agentStatus || defaultStatus;
  const isRunning = !!turn.isStreaming && !turn.awaitingApproval;

  return (
    <div className="flex gap-3 items-start">
      <TourAIAvatar />

      <div className="flex-1 min-w-0 space-y-3 pb-1">
        {/* ── 1. Modern Collapsible Reasoning / Trace Component ── */}
        <ReasoningTrace
          running={isRunning}
          intent={turn.intent}
          status={status}
          elapsedMs={status.elapsedMs}
        />

        {/* ── 2. HITL Approval Gate (embedded in thread) ── */}
        {(turn.awaitingApproval || turn.approvalResolved) && (
          <HITLReviewCard
            question={turn.approvalQuestion || ""}
            draftItinerary={turn.draftItinerary}
            onApprove={() => onApprove(turn.id)}
            onRevise={(feedback) => onRevise(turn.id, feedback)}
            isSubmitting={!!turn.isResuming}
            resolved={turn.approvalResolved || null}
          />
        )}

        {/* ── 3. Final Formatted Travel Dossier Response ── */}
        {turn.planResult && (
          <TravelResultsView
            query={turn.userContent || ""}
            planResult={turn.planResult}
            flightData={turn.flightData}
            hotelData={turn.hotelData}
            weatherData={turn.weatherData}
            mapsData={turn.mapsData}
            itineraryData={turn.itineraryData}
            llmCalls={turn.llmCalls}
            isStreaming={!!turn.isStreaming}
          />
        )}
      </div>
    </div>
  );
}
