"use client";

import * as React from "react";
import {
  Trace,
  TraceCollapsible,
  TraceCollapsibleTrigger,
  TraceCollapsibleContent,
  TraceLine,
  TraceIcon,
  TraceTitle,
  TraceDescription,
} from "@/components/ui/trace";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

// ── ChainOfThought Shell ────────────────────────────────────────────────────
interface ChainOfThoughtProps {
  open?: boolean;
  defaultOpen?: boolean;
  onOpenChange?: (open: boolean) => void;
  className?: string;
  children: React.ReactNode;
}

export function ChainOfThought({
  open,
  defaultOpen = false,
  onOpenChange,
  className,
  children,
}: ChainOfThoughtProps) {
  return (
    <Trace className={cn("max-w-3xl", className)}>
      <TraceCollapsible
        open={open}
        defaultOpen={defaultOpen}
        onOpenChange={onOpenChange}
      >
        {children}
      </TraceCollapsible>
    </Trace>
  );
}

// ── ChainOfThought Header (Summary Trigger) ─────────────────────────────────
interface ChainOfThoughtHeaderProps {
  status?: "running" | "done" | "idle";
  children: React.ReactNode;
  className?: string;
}

export function ChainOfThoughtHeader({
  status,
  children,
  className,
}: ChainOfThoughtHeaderProps) {
  return (
    <TraceCollapsibleTrigger className={className}>
      <TraceLine status={status}>{children}</TraceLine>
    </TraceCollapsibleTrigger>
  );
}

// ── ChainOfThought Content (Steps Container) ────────────────────────────────
interface ChainOfThoughtContentProps {
  className?: string;
  children: React.ReactNode;
}

export function ChainOfThoughtContent({
  className,
  children,
}: ChainOfThoughtContentProps) {
  return (
    <TraceCollapsibleContent className={className}>
      <Trace className="gap-2.5 my-0.5">{children}</Trace>
    </TraceCollapsibleContent>
  );
}

// ── ChainOfThought Step (Individual Trace Line) ─────────────────────────────
interface ChainOfThoughtStepProps {
  status?: "running" | "done" | "idle";
  icon?: React.ReactNode;
  title: React.ReactNode;
  description?: React.ReactNode;
  className?: string;
  children?: React.ReactNode;
}

export function ChainOfThoughtStep({
  status,
  icon,
  title,
  description,
  className,
  children,
}: ChainOfThoughtStepProps) {
  return (
    <div className={cn("flex flex-col gap-1 py-1 px-1 rounded-lg transition-colors", className)}>
      <TraceLine status={status}>
        <TraceIcon status={status}>{icon}</TraceIcon>
        <TraceTitle>{title}</TraceTitle>
        {description && <TraceDescription>{description}</TraceDescription>}
      </TraceLine>
      {children}
    </div>
  );
}

// ── ChainOfThought Search Results (Badges for Sources/Hostnames) ────────────
interface SearchResultItem {
  name: string;
  badge?: string;
}

interface ChainOfThoughtSearchResultsProps {
  results: (string | SearchResultItem)[];
  className?: string;
}

export function ChainOfThoughtSearchResults({
  results,
  className,
}: ChainOfThoughtSearchResultsProps) {
  if (!results || results.length === 0) return null;

  return (
    <div className={cn("flex flex-wrap gap-1.5 pl-6 pt-0.5", className)}>
      {results.map((res, idx) => {
        const text = typeof res === "string" ? res : res.name;
        return (
          <Badge key={idx} variant="secondary">
            {text}
          </Badge>
        );
      })}
    </div>
  );
}
