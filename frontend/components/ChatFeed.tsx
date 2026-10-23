"use client";

import React, { useEffect, useRef } from "react";
import UserBubble from "@/components/UserBubble";
import AgentTurnContainer, { ChatTurn } from "@/components/AgentTurnContainer";
import CheckpointMarker from "@/components/CheckpointMarker";

interface ChatFeedProps {
  turns: ChatTurn[];
  onApprove: (turnId: string) => void;
  onRevise: (turnId: string, feedback: string) => void;
  onRestoreCheckpoint?: (targetTurnId: string) => void;
}

export default function ChatFeed({
  turns,
  onApprove,
  onRevise,
  onRestoreCheckpoint,
}: ChatFeedProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new turns or streaming updates
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns]);

  // Group consecutive turns: user turn followed by its paired assistant turn
  const paired: ChatTurn[][] = [];
  let i = 0;
  while (i < turns.length) {
    if (turns[i].role === "user") {
      const group: ChatTurn[] = [turns[i]];
      if (i + 1 < turns.length && turns[i + 1].role === "assistant") {
        group.push(turns[i + 1]);
        i += 2;
      } else {
        i += 1;
      }
      paired.push(group);
    } else {
      paired.push([turns[i]]);
      i += 1;
    }
  }

  return (
    <div className="flex-1 w-full max-w-3xl mx-auto px-4 py-8 pb-36 flex flex-col gap-6">
      {paired.map((group, groupIdx) => {
        const assistantTurn = group.find((t) => t.role === "assistant");
        const isComplete = assistantTurn && !assistantTurn.isStreaming && assistantTurn.planResult;
        const hasSubsequentTurns = groupIdx < paired.length - 1;
        const lastTurnId = group[group.length - 1].id;

        return (
          <div key={group[0].id} className="flex flex-col gap-4">
            {group.map((turn) =>
              turn.role === "user" ? (
                <UserBubble
                  key={turn.id}
                  content={turn.userContent || ""}
                  timestamp={turn.timestamp}
                />
              ) : (
                <AgentTurnContainer
                  key={turn.id}
                  turn={turn}
                  onApprove={onApprove}
                  onRevise={onRevise}
                />
              )
            )}

            {/* Checkpoint Marker rendered after completed turn pair */}
            {isComplete && (
              <CheckpointMarker
                label={`Checkpoint #${groupIdx + 1} Saved`}
                turnIndex={groupIdx + 1}
                canRestore={hasSubsequentTurns}
                onRestore={() => onRestoreCheckpoint?.(lastTurnId)}
              />
            )}
          </div>
        );
      })}

      {/* Scroll anchor */}
      <div ref={bottomRef} />
    </div>
  );
}
