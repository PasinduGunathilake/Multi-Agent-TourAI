"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

// ── Marker (Checkpoint Separator) ───────────────────────────────────────────
interface MarkerProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "separator";
}

export function Marker({
  variant = "separator",
  className,
  children,
  ...props
}: MarkerProps) {
  if (variant === "separator") {
    return (
      <div
        className={cn(
          "w-full flex items-center my-6 relative select-none",
          className
        )}
        {...props}
      >
        <div className="flex-1 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />
        <div className="px-3 shrink-0 flex items-center justify-center">
          {children}
        </div>
        <div className="flex-1 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />
      </div>
    );
  }

  return (
    <div
      className={cn("flex items-center gap-2 text-xs text-white/50", className)}
      {...props}
    >
      {children}
    </div>
  );
}

// ── Marker Content ──────────────────────────────────────────────────────────
export function MarkerContent({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#0a0e18] border border-white/10 text-[11px] font-mono text-white/60 shadow-lg backdrop-blur-md",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

// ── Marker Icon ─────────────────────────────────────────────────────────────
export function MarkerIcon({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn("flex items-center justify-center text-teal-400 shrink-0", className)}
      {...props}
    >
      {children}
    </span>
  );
}
