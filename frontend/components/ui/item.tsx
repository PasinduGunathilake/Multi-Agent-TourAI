"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

// ── Item Container ──────────────────────────────────────────────────────────
interface ItemProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "outline" | "default" | "muted";
  size?: "sm" | "md" | "lg";
}

export function Item({
  variant = "outline",
  size = "sm",
  className,
  children,
  ...props
}: ItemProps) {
  return (
    <div
      data-variant={variant}
      data-size={size}
      className={cn(
        "w-full rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 transition-all",
        variant === "outline" && "border border-amber-500/25 bg-gradient-to-b from-amber-500/8 to-amber-950/10 shadow-lg shadow-amber-950/20 backdrop-blur-md",
        variant === "default" && "bg-white/[0.04] border border-white/10",
        variant === "muted" && "bg-black/30 border border-white/5 text-white/50",
        size === "sm" && "p-3.5 sm:p-4 text-xs",
        size === "md" && "p-5 text-sm",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

// ── Item Media ──────────────────────────────────────────────────────────────
interface ItemMediaProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "icon" | "avatar";
}

export function ItemMedia({
  variant = "icon",
  className,
  children,
  ...props
}: ItemMediaProps) {
  return (
    <div
      className={cn(
        "shrink-0 flex items-center justify-center",
        variant === "icon" && "w-8 h-8 rounded-xl bg-amber-500/15 border border-amber-500/25 text-amber-300 shadow-sm",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

// ── Item Content ────────────────────────────────────────────────────────────
export function ItemContent({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("flex-1 min-w-0 flex flex-col gap-0.5", className)}
      {...props}
    >
      {children}
    </div>
  );
}

// ── Item Title ──────────────────────────────────────────────────────────────
export function ItemTitle({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h4
      className={cn("text-xs sm:text-sm font-semibold text-amber-200 tracking-tight", className)}
      {...props}
    >
      {children}
    </h4>
  );
}

// ── Item Description ────────────────────────────────────────────────────────
export function ItemDescription({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p
      className={cn("text-[11px] sm:text-xs text-neutral-400 leading-relaxed font-sans", className)}
      {...props}
    >
      {children}
    </p>
  );
}

// ── Item Actions ────────────────────────────────────────────────────────────
export function ItemActions({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("flex items-center gap-2 shrink-0 flex-wrap sm:flex-nowrap mt-2 sm:mt-0", className)}
      {...props}
    >
      {children}
    </div>
  );
}
