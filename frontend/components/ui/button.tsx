"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { GlowingEffect } from "@/components/ui/glowing-effect";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "outline" | "ghost" | "link" | "secondary";
  size?: "default" | "sm" | "lg" | "icon" | "icon-lg";
  pill?: boolean;
  glowing?: boolean;
  glowSpread?: number;
  glowVariant?: "default" | "white";
  glowProximity?: number;
  glowBorderWidth?: number;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = "default",
      size = "default",
      pill = false,
      glowing = true,
      glowSpread = 30,
      glowVariant = "default",
      glowProximity = 64,
      glowBorderWidth = 1.5,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    const showGlow = glowing && variant !== "link" && !disabled;

    return (
      <button
        ref={ref}
        disabled={disabled}
        className={cn(
          "group relative overflow-hidden inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl text-xs font-bold transition-all focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-teal-400 disabled:pointer-events-none disabled:opacity-50 cursor-pointer select-none",
          pill && "rounded-full",
          variant === "default" &&
            "bg-gradient-to-r from-teal-600 to-sky-600 text-white shadow-md shadow-teal-900/40 hover:from-teal-500 hover:to-sky-500 border border-teal-400/30",
          variant === "outline" &&
            "border border-white/15 bg-white/5 text-white hover:bg-white/10 hover:border-white/25",
          variant === "ghost" &&
            "text-white/70 hover:text-white hover:bg-white/10",
          variant === "link" &&
            "text-teal-400 underline-offset-4 hover:underline",
          variant === "secondary" &&
            "bg-white/10 text-white hover:bg-white/15 border border-white/10",
          size === "default" && "h-10 px-4 py-2",
          size === "sm" && "h-8 rounded-lg px-3 text-xs",
          size === "lg" && "h-12 rounded-xl px-8 text-sm",
          size === "icon" && "h-10 w-10 p-0",
          size === "icon-lg" && "h-11 w-11 p-0",
          className
        )}
        {...props}
      >
        {showGlow && (
          <GlowingEffect
            spread={glowSpread}
            glow={true}
            disabled={false}
            proximity={glowProximity}
            inactiveZone={0.01}
            borderWidth={glowBorderWidth}
            variant={glowVariant}
          />
        )}
        <span className="relative z-10 inline-flex items-center justify-center gap-2 w-full h-full">
          {children}
        </span>
      </button>
    );
  }
);
Button.displayName = "Button";
