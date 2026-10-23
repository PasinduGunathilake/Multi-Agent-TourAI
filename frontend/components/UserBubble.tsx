"use client";

import React from "react";
import { Message, MessageContent } from "@/components/ui/message";
import { Bubble, BubbleContent } from "@/components/ui/bubble";

interface UserBubbleProps {
  content: string;
  timestamp: string;
}

export default function UserBubble({ content, timestamp }: UserBubbleProps) {
  return (
    <Message align="end" className="group">
      <MessageContent align="end">
        <Bubble align="end" variant="muted">
          <BubbleContent>{content}</BubbleContent>
        </Bubble>
        <span className="text-[11px] text-neutral-500 pr-1 mt-1 opacity-0 group-hover:opacity-100 transition-opacity font-mono">
          {timestamp}
        </span>
      </MessageContent>
      <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-teal-500/30 to-sky-500/30 border border-white/15 flex items-center justify-center text-xs font-semibold text-teal-300 uppercase shrink-0 mb-4 shadow-sm">
        {content.slice(0, 2).toLowerCase()}
      </div>
    </Message>
  );
}
