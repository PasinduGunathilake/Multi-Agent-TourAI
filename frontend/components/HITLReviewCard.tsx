"use client";

import React, { useState } from "react";
import { CheckCircle2, MessageSquareDiff, ChevronDown, ChevronUp, Send, Sparkles } from "lucide-react";
import {
  Item,
  ItemMedia,
  ItemContent,
  ItemTitle,
  ItemDescription,
  ItemActions,
} from "@/components/ui/item";

interface HITLReviewCardProps {
  question: string;
  draftItinerary?: string;
  onApprove: () => void;
  onRevise: (feedback: string) => void;
  isSubmitting: boolean;
  resolved?: "approved" | "revised" | null;
}

export default function HITLReviewCard({
  question,
  draftItinerary,
  onApprove,
  onRevise,
  isSubmitting,
  resolved,
}: HITLReviewCardProps) {
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [expandedDraft, setExpandedDraft] = useState(false);

  // If already resolved, show a clean Confirmation status line
  if (resolved) {
    return (
      <div className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-300 w-fit shadow-sm">
        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
        <span className="font-medium">
          {resolved === "approved"
            ? "Itinerary Approved — LangGraph synthesis completed"
            : "Revisions Submitted — agents refined the plan"}
        </span>
      </div>
    );
  }

  return (
    <div className="w-full flex flex-col gap-2.5 my-2">
      {/* ── Confirmation Item Shell ── */}
      <Item variant="outline" size="sm">
        <ItemMedia variant="icon">
          <Sparkles className="w-4 h-4" />
        </ItemMedia>

        <ItemContent>
          <ItemTitle>Human-in-the-Loop Verification Required</ItemTitle>
          <ItemDescription>
            {question || "The multi-agent swarm paused at the draft itinerary. Please approve or request changes before final synthesis."}
          </ItemDescription>
        </ItemContent>

        <ItemActions>
          {/* Deny / Request Changes */}
          {!showFeedback ? (
            <button
              type="button"
              onClick={() => setShowFeedback(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/12 text-neutral-300 hover:text-white text-xs font-medium transition-all cursor-pointer"
            >
              <MessageSquareDiff className="w-3.5 h-3.5" />
              <span>Request Changes</span>
            </button>
          ) : (
            <button
              type="button"
              onClick={() => {
                if (feedback.trim()) onRevise(feedback);
              }}
              disabled={!feedback.trim() || isSubmitting}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-amber-600 hover:bg-amber-500 disabled:opacity-40 text-white text-xs font-semibold transition-all cursor-pointer shadow-sm"
            >
              <Send className="w-3 h-3" />
              <span>Submit Feedback</span>
            </button>
          )}

          {/* Approve Button */}
          <button
            type="button"
            onClick={onApprove}
            disabled={isSubmitting}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-semibold transition-all shadow-md shadow-emerald-900/40 hover:shadow-emerald-500/25 cursor-pointer"
          >
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Approve & Synthesize</span>
          </button>
        </ItemActions>
      </Item>

      {/* ── Expandable Draft Itinerary Preview (Optional toggle) ── */}
      {draftItinerary && (
        <div className="rounded-xl border border-white/8 bg-black/40 overflow-hidden text-xs">
          <button
            type="button"
            onClick={() => setExpandedDraft(!expandedDraft)}
            className="w-full flex items-center justify-between px-4 py-2 hover:bg-white/[0.03] transition-colors cursor-pointer text-white/60 font-sans text-[11px]"
          >
            <span className="flex items-center gap-1.5 text-amber-300">
              <span>🗓️ Draft Itinerary Preview</span>
            </span>
            <div className="flex items-center gap-1 text-[10px] text-white/40">
              <span>{expandedDraft ? "Hide Draft" : "View Draft"}</span>
              {expandedDraft ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </div>
          </button>

          {expandedDraft && (
            <div className="p-4 border-t border-white/6 max-h-52 overflow-y-auto custom-scrollbar text-neutral-300 leading-relaxed font-sans whitespace-pre-line text-xs bg-black/50">
              {draftItinerary}
            </div>
          )}
        </div>
      )}

      {/* ── Feedback Textarea (When Request Changes is active) ── */}
      {showFeedback && (
        <div className="p-3 rounded-xl bg-neutral-900/90 border border-amber-500/25 space-y-2 animate-in fade-in-50 duration-150">
          <textarea
            rows={2}
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="E.g., Day 2 is too packed, replace morning museum with outdoor park, prefer boutique 4-star hotels..."
            className="w-full p-2.5 rounded-lg bg-black/60 border border-white/10 text-white text-xs focus:border-amber-400 focus:outline-none placeholder-white/30 resize-none font-sans"
            autoFocus
          />
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-white/40 font-sans">
              Revisions will be fed back into LangGraph Itinerary Agent.
            </span>
            <button
              type="button"
              onClick={() => {
                setShowFeedback(false);
                setFeedback("");
              }}
              className="text-[11px] text-white/40 hover:text-white transition-colors cursor-pointer"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
