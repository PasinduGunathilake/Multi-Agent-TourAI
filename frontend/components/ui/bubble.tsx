"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

// ── Bubble Container ────────────────────────────────────────────────────────
interface BubbleProps extends React.HTMLAttributes<HTMLDivElement> {
  align?: "start" | "end";
  variant?: "default" | "muted" | "primary";
}

export function Bubble({
  align = "end",
  variant = "muted",
  className,
  children,
  ...props
}: BubbleProps) {
  return (
    <div
      data-align={align}
      data-variant={variant}
      className={cn(
        "rounded-2xl text-[15px] leading-relaxed transition-all shadow-sm",
        align === "end" && "rounded-br-sm ml-auto",
        align === "start" && "rounded-bl-sm mr-auto",
        variant === "muted" && "bg-[#1b1e28] border border-white/10 text-neutral-100 px-4 py-2.5",
        variant === "default" && "bg-[#141822] border border-white/10 text-white px-4 py-2.5",
        variant === "primary" && "bg-teal-500/20 border border-teal-500/30 text-teal-100 px-4 py-2.5",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

// ── Bubble Content ──────────────────────────────────────────────────────────
export function BubbleContent({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("break-words font-sans text-[14px] sm:text-[15px]", className)} {...props}>
      {children}
    </div>
  );
}
