"use client";

import React from "react";
import { Marker, MarkerContent, MarkerIcon } from "@/components/ui/marker";
import { Bookmark, RotateCcw } from "lucide-react";

interface CheckpointMarkerProps {
  label?: string;
  turnIndex?: number;
  onRestore?: () => void;
  canRestore?: boolean;
}

export default function CheckpointMarker({
  label = "PostgreSQL Checkpoint Saved",
  turnIndex,
  onRestore,
  canRestore = true,
}: CheckpointMarkerProps) {
  return (
    <Marker variant="separator">
      <MarkerContent>
        <MarkerIcon>
          <Bookmark className="w-3 h-3 text-teal-400" />
        </MarkerIcon>
        <span className="text-white/60 font-sans text-[10px]">
          {label}
        </span>
        {canRestore && onRestore && (
          <button
            type="button"
            onClick={onRestore}
            className="flex items-center gap-1 ml-1 px-2 py-0.5 rounded-full bg-white/5 hover:bg-teal-500/15 border border-white/10 hover:border-teal-500/30 text-[10px] text-white/50 hover:text-teal-300 font-sans font-medium transition-all cursor-pointer"
            title="Restore conversation to this turn checkpoint"
          >
            <RotateCcw className="w-2.5 h-2.5" />
            <span>Restore</span>
          </button>
        )}
      </MarkerContent>
    </Marker>
  );
}
