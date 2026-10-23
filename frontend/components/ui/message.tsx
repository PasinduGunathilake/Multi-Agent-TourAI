"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

// ── Message Root ────────────────────────────────────────────────────────────
interface MessageProps extends React.HTMLAttributes<HTMLDivElement> {
  align?: "start" | "end";
}

export function Message({
  align = "start",
  className,
  children,
  ...props
}: MessageProps) {
  return (
    <div
      data-align={align}
      className={cn(
        "w-full flex gap-3 text-sm font-sans transition-all",
        align === "end" ? "justify-end items-end" : "justify-start items-start",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

// ── Message Content ─────────────────────────────────────────────────────────
interface MessageContentProps extends React.HTMLAttributes<HTMLDivElement> {
  align?: "start" | "end";
}

export function MessageContent({
  align = "start",
  className,
  children,
  ...props
}: MessageContentProps) {
  return (
    <div
      data-align={align}
      className={cn(
        "flex flex-col min-w-0 max-w-full",
        align === "end" ? "items-end max-w-xl" : "items-start flex-1 max-w-3xl",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

// ── Message Footer (Actions Bar) ────────────────────────────────────────────
interface MessageFooterProps extends React.HTMLAttributes<HTMLDivElement> {
  align?: "start" | "end";
}

export function MessageFooter({
  align = "start",
  className,
  children,
  ...props
}: MessageFooterProps) {
  return (
    <div
      className={cn(
        "flex items-center gap-1.5 pt-2 text-xs text-white/50",
        align === "end" ? "justify-end" : "justify-start",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

// ── Message Action Button ───────────────────────────────────────────────────
interface MessageActionProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  tooltip?: string;
  isActive?: boolean;
}

export function MessageAction({
  tooltip,
  isActive,
  className,
  children,
  ...props
}: MessageActionProps) {
  return (
    <button
      type="button"
      title={tooltip}
      aria-pressed={isActive}
      className={cn(
        "flex items-center justify-center p-1.5 rounded-lg text-white/40 hover:text-white hover:bg-white/10 transition-colors cursor-pointer",
        isActive && "text-teal-400 bg-teal-500/10 hover:text-teal-300",
        className
      )}
      {...props}
    >
      {children}
      {tooltip && <span className="sr-only">{tooltip}</span>}
    </button>
  );
}
