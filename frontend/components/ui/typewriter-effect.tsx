"use client";

import React, { useState, useEffect, useMemo } from "react";
import { cn } from "@/lib/utils";
import { motion } from "motion/react";

export interface TypewriterWord {
  text: string;
  className?: string;
  lineBreakAfter?: boolean;
}

export const TypewriterEffect = ({
  words,
  className,
  cursorClassName,
  repeatIntervalMs = 10000,
}: {
  words: TypewriterWord[];
  className?: string;
  cursorClassName?: string;
  repeatIntervalMs?: number;
}) => {
  // 1. Group words into distinct lines based on lineBreakAfter
  const lines = useMemo(() => {
    const result: TypewriterWord[][] = [[]];
    for (const w of words) {
      result[result.length - 1].push(w);
      if (w.lineBreakAfter) {
        result.push([]);
      }
    }
    return result.filter((l) => l.length > 0);
  }, [words]);

  // 2. Map items with precise character boundary indices
  const items = useMemo(() => {
    const list: {
      lineIdx: number;
      wordIdx: number;
      text: string;
      className?: string;
      startIndex: number;
      endIndex: number;
    }[] = [];

    let count = 0;
    lines.forEach((line, lineIdx) => {
      line.forEach((w, wordIdx) => {
        // Space before word except at the start of a line
        const textWithSpace = (wordIdx > 0 ? " " : "") + w.text;
        const start = count;
        count += textWithSpace.length;
        list.push({
          lineIdx,
          wordIdx,
          text: textWithSpace,
          className: w.className,
          startIndex: start,
          endIndex: count,
        });
      });
    });

    return { list, totalChars: count };
  }, [lines]);

  const [charIndex, setCharIndex] = useState(0);

  // 3. Smooth typing loop repeating every repeatIntervalMs
  useEffect(() => {
    let isMounted = true;
    let stepTimer: NodeJS.Timeout;
    let holdTimer: NodeJS.Timeout;

    const startTyping = () => {
      setCharIndex(0);
      let current = 0;
      const stepSpeed = 50; // Smooth 50ms per character

      const tick = () => {
        if (!isMounted) return;
        current++;
        setCharIndex(current);

        if (current < items.totalChars) {
          stepTimer = setTimeout(tick, stepSpeed);
        } else {
          // Finished typing all lines! Hold so user can comfortably read it
          const typingDuration = items.totalChars * stepSpeed;
          const pauseDuration = Math.max(3000, repeatIntervalMs - typingDuration);
          holdTimer = setTimeout(() => {
            if (isMounted) startTyping();
          }, pauseDuration);
        }
      };

      stepTimer = setTimeout(tick, stepSpeed);
    };

    startTyping();

    return () => {
      isMounted = false;
      clearTimeout(stepTimer);
      clearTimeout(holdTimer);
    };
  }, [items.totalChars, repeatIntervalMs]);

  // Determine which line currently holds the blinking typing cursor
  const activeLineIdx = useMemo(() => {
    if (charIndex >= items.totalChars) return lines.length - 1;
    for (let i = items.list.length - 1; i >= 0; i--) {
      const it = items.list[i];
      if (charIndex >= it.startIndex && charIndex < it.endIndex) {
        return it.lineIdx;
      }
    }
    return 0;
  }, [charIndex, items.totalChars, items.list, lines.length]);

  return (
    <div className={cn("relative w-full text-center select-none", className)}>
      {/* ── Layer 1: Phantom Layout Lock ─────────────────────────────────── */}
      {/* Invisible clone reserves the exact multi-line space so the rest of the */}
      {/* page NEVER jumps, shifts, or jitters during typing cycles. */}
      <div className="invisible pointer-events-none select-none w-full flex flex-col items-center justify-center gap-2 sm:gap-3" aria-hidden="true">
        {lines.map((line, lIdx) => (
          <div key={`phantom-l-${lIdx}`} className="flex items-center justify-center whitespace-nowrap py-1 overflow-visible">
            {line.map((w, wIdx) => (
              <span key={`phantom-w-${wIdx}`} className={cn("inline-block py-0.5", w.className || "text-white")}>
                {wIdx > 0 ? "\u00A0" : ""}
                {w.text.replace(/ /g, "\u00A0")}
              </span>
            ))}
          </div>
        ))}
      </div>

      {/* ── Layer 2: Active Smooth Typewriter ────────────────────────────── */}
      <div className="absolute inset-0 flex flex-col items-center justify-center w-full gap-2 sm:gap-3">
        {lines.map((line, lIdx) => {
          const isLineActive = lIdx === activeLineIdx;

          return (
            <div key={`active-l-${lIdx}`} className="flex items-center justify-center whitespace-nowrap py-1 overflow-visible">
              {line.map((w, wIdx) => {
                const item = items.list.find((it) => it.lineIdx === lIdx && it.wordIdx === wIdx);
                if (!item) return null;

                // Slice the currently revealed portion of this word
                let sliced = "";
                if (charIndex > item.startIndex) {
                  sliced = item.text.slice(0, Math.min(item.text.length, charIndex - item.startIndex));
                }

                // Preserve all spaces using non-breaking spaces (\u00A0) so HTML never collapses them!
                const displaySliced = sliced.replace(/ /g, "\u00A0");

                return (
                  <span
                    key={`active-w-${wIdx}`}
                    className={cn(
                      "inline-block py-0.5",
                      w.className || "text-white"
                    )}
                  >
                    {displaySliced}
                  </span>
                );
              })}

              {/* Smooth blinking cursor tracking the active line */}
              {isLineActive && (
                <span
                  className={cn(
                    "inline-block rounded-sm w-[3px] sm:w-[4px] h-7 sm:h-10 lg:h-12 bg-teal-400 ml-1.5 animate-pulse align-middle",
                    cursorClassName
                  )}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export const TypewriterEffectSmooth = ({
  words,
  className,
  cursorClassName,
}: {
  words: {
    text: string;
    className?: string;
  }[];
  className?: string;
  cursorClassName?: string;
}) => {
  // split text inside of words into array of characters
  const wordsArray = words.map((word) => {
    return {
      ...word,
      text: word.text.split(""),
    };
  });
  const renderWords = () => {
    return (
      <div>
        {wordsArray.map((word, idx) => {
          return (
            <div key={`word-${idx}`} className="inline-block">
              {word.text.map((char, index) => (
                <span
                  key={`char-${index}`}
                  className={cn(`dark:text-white text-black `, word.className)}
                >
                  {char}
                </span>
              ))}
              &nbsp;
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className={cn("flex space-x-1 my-6", className)}>
      <motion.div
        className="overflow-hidden pb-2"
        initial={{
          width: "0%",
        }}
        whileInView={{
          width: "fit-content",
        }}
        transition={{
          duration: 2,
          ease: "linear",
          delay: 1,
        }}
      >
        <div
          className="text-xs sm:text-base md:text-xl lg:text:3xl xl:text-5xl font-bold"
          style={{
            whiteSpace: "nowrap",
          }}
        >
          {renderWords()}{" "}
        </div>{" "}
      </motion.div>
      <motion.span
        initial={{
          opacity: 0,
        }}
        animate={{
          opacity: 1,
        }}
        transition={{
          duration: 0.8,

          repeat: Infinity,
          repeatType: "reverse",
        }}
        className={cn(
          "block rounded-sm w-[4px]  h-4 sm:h-6 xl:h-12 bg-blue-500",
          cursorClassName
        )}
      ></motion.span>
    </div>
  );
};
