"use client";

import React, { useEffect, useRef, useState } from "react";

interface ScrollRevealProps {
  children: React.ReactNode;
  direction?: "up" | "down" | "left" | "right" | "scale" | "fade";
  delayMs?: number;
  durationMs?: number;
  className?: string;
  threshold?: number;
  repeat?: boolean;
}

export default function ScrollReveal({
  children,
  direction = "up",
  delayMs = 0,
  durationMs = 700,
  className = "",
  threshold = 0.12,
  repeat = true, // Re-animate both when scrolling UP and DOWN
}: ScrollRevealProps) {
  const [isVisible, setIsVisible] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    // Bi-directional Scroll-Triggered Reveal Observer
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          if (!repeat) observer.unobserve(el);
        } else if (repeat) {
          // Reset when out of view so it triggers every time you scroll up or down
          setIsVisible(false);
        }
      },
      {
        threshold,
        rootMargin: "10px 0px -30px 0px", // Snappy detection when scrolling up or down
      }
    );

    observer.observe(el);

    return () => {
      observer.disconnect();
    };
  }, [threshold, repeat]);

  const getTransform = () => {
    if (isVisible) return "none";
    switch (direction) {
      case "up":
        return "translateY(32px)";
      case "down":
        return "translateY(-32px)";
      case "left":
        return "translateX(36px)";
      case "right":
        return "translateX(-36px)";
      case "scale":
        return "scale(0.94) translateY(18px)";
      case "fade":
      default:
        return "none";
    }
  };

  return (
    <div
      ref={ref}
      className={`transition-all ${className}`}
      style={{
        opacity: isVisible ? 1 : 0,
        transform: getTransform(),
        filter: isVisible ? "blur(0px)" : "blur(3px)",
        transitionDuration: `${durationMs}ms`,
        transitionDelay: isVisible ? `${delayMs}ms` : "0ms", // Instantly ready when leaving view
        transitionTimingFunction: "cubic-bezier(0.16, 1, 0.3, 1)", // Snappy luxury ease-out
        willChange: "opacity, transform, filter",
      }}
    >
      {children}
    </div>
  );
}
