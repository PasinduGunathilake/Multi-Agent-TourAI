"use client";

import * as React from "react";
import { ChevronDown, LoaderCircle, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";

// ── Context for Collapsible State ───────────────────────────────────────────
interface TraceCollapsibleContextValue {
  open: boolean;
  setOpen: (open: boolean) => void;
}

const TraceCollapsibleContext = React.createContext<TraceCollapsibleContextValue | null>(null);

function useTraceCollapsible() {
  const context = React.useContext(TraceCollapsibleContext);
  if (!context) {
    throw new Error("TraceCollapsible subcomponents must be used within a TraceCollapsible");
  }
  return context;
}

// ── Trace Container ─────────────────────────────────────────────────────────
export function Trace({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("w-full flex flex-col gap-1 text-sm font-sans my-1.5", className)}
      {...props}
    >
      {children}
    </div>
  );
}

// ── Trace Collapsible ───────────────────────────────────────────────────────
interface TraceCollapsibleProps extends React.HTMLAttributes<HTMLDivElement> {
  open?: boolean;
  defaultOpen?: boolean;
  onOpenChange?: (open: boolean) => void;
}

export function TraceCollapsible({
  open: controlledOpen,
  defaultOpen = false,
  onOpenChange,
  className,
  children,
  ...props
}: TraceCollapsibleProps) {
  const [uncontrolledOpen, setUncontrolledOpen] = React.useState(defaultOpen);
  const isControlled = controlledOpen !== undefined;
  const open = isControlled ? controlledOpen : uncontrolledOpen;

  const setOpen = React.useCallback(
    (val: boolean) => {
      if (!isControlled) {
        setUncontrolledOpen(val);
      }
      onOpenChange?.(val);
    },
    [isControlled, onOpenChange]
  );

  return (
    <TraceCollapsibleContext.Provider value={{ open, setOpen }}>
      <div
        data-state={open ? "open" : "closed"}
        className={cn("w-full rounded-xl border border-white/8 bg-white/[0.02] overflow-hidden transition-all", className)}
        {...props}
      >
        {children}
      </div>
    </TraceCollapsibleContext.Provider>
  );
}

// ── Trace Trigger ───────────────────────────────────────────────────────────
export function TraceCollapsibleTrigger({
  className,
  children,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  const { open, setOpen } = useTraceCollapsible();

  return (
    <button
      type="button"
      onClick={() => setOpen(!open)}
      data-state={open ? "open" : "closed"}
      className={cn(
        "w-full flex items-center justify-between px-3.5 py-2 hover:bg-white/[0.04] transition-colors cursor-pointer text-left group",
        className
      )}
      {...props}
    >
      <div className="flex items-center gap-2 flex-1 min-w-0">
        {children}
      </div>
      <ChevronDown
        className={cn(
          "w-3.5 h-3.5 text-white/40 group-hover:text-white/80 transition-transform duration-200 shrink-0 ml-2",
          open && "rotate-180"
        )}
      />
    </button>
  );
}

// ── Trace Content ───────────────────────────────────────────────────────────
export function TraceCollapsibleContent({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  const { open } = useTraceCollapsible();

  if (!open) return null;

  return (
    <div
      className={cn(
        "px-4 py-3 border-t border-white/6 text-xs text-neutral-300 font-mono leading-relaxed bg-black/40 animate-in fade-in-50 duration-150",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

// ── Trace Line ──────────────────────────────────────────────────────────────
interface TraceLineProps extends React.HTMLAttributes<HTMLDivElement> {
  status?: "running" | "done" | "idle";
}

export function TraceLine({
  status,
  className,
  children,
  ...props
}: TraceLineProps) {
  return (
    <div
      data-status={status}
      className={cn(
        "flex items-center gap-2 text-xs",
        status === "running" ? "text-sky-300 font-medium" : "text-white/60",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

// ── Trace Icon ──────────────────────────────────────────────────────────────
interface TraceIconProps extends React.HTMLAttributes<HTMLSpanElement> {
  status?: "running" | "done" | "idle";
}

export function TraceIcon({
  status,
  className,
  children,
  ...props
}: TraceIconProps) {
  return (
    <span
      className={cn("shrink-0 flex items-center justify-center text-xs", className)}
      {...props}
    >
      {children || (
        status === "running" ? (
          <LoaderCircle className="w-3.5 h-3.5 text-sky-400 animate-spin" />
        ) : (
          <CheckCircle2 className="w-3.5 h-3.5 text-teal-400" />
        )
      )}
    </span>
  );
}

// ── Trace Title ─────────────────────────────────────────────────────────────
export function TraceTitle({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn("font-medium tracking-tight text-white/90 text-xs", className)}
      {...props}
    >
      {children}
    </span>
  );
}

// ── Trace Description ───────────────────────────────────────────────────────
export function TraceDescription({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn("text-[11px] font-mono text-white/40 ml-1.5", className)}
      {...props}
    >
      {children}
    </span>
  );
}
