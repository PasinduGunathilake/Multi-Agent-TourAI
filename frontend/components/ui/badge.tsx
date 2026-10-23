"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "secondary" | "outline" | "destructive" | "teal" | "sky" | "indigo";
}

export function Badge({
  className,
  variant = "default",
  ...props
}: BadgeProps) {
  return (
    <div
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-[10px] font-sans font-medium tracking-wide transition-colors",
        variant === "default" && "bg-white/10 text-white border border-white/15",
        variant === "secondary" && "bg-white/[0.05] hover:bg-white/[0.08] text-white/70 border border-white/10",
        variant === "outline" && "border border-white/20 text-white/80",
        variant === "destructive" && "bg-red-500/10 border border-red-500/25 text-red-400",
        variant === "teal" && "bg-teal-500/10 border border-teal-500/25 text-teal-300",
        variant === "sky" && "bg-sky-500/10 border border-sky-500/25 text-sky-300",
        variant === "indigo" && "bg-indigo-500/10 border border-indigo-500/25 text-indigo-300",
        className
      )}
      {...props}
    />
  );
}
