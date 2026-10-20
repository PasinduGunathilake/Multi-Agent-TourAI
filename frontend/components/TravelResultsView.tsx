"use client";

import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import { Sparkles, Copy, Check, Share2, ChevronDown, ChevronUp, Bot, Plane, Hotel, CloudSun, MapPin } from "lucide-react";

interface TravelResultsViewProps {
  query: string;
  planResult: string;
  flightData?: string;
  hotelData?: string;
  weatherData?: string;
  itineraryData?: string;
  llmCalls?: number;
  isStreaming?: boolean;
}

export default function TravelResultsView({
  query,
  planResult,
  flightData,
  hotelData,
  weatherData,
  itineraryData,
  llmCalls = 4,
  isStreaming = false,
}: TravelResultsViewProps) {
  const [copied, setCopied] = useState(false);
  const [showRawAgents, setShowRawAgents] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(planResult);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleShare = () => {
    if (navigator.share) {
      navigator.share({ title: `TourAI Plan: ${query}`, text: planResult });
    } else {
      handleCopy();
    }
  };

  const hasAgentArtifacts = Boolean(flightData || hotelData || weatherData || itineraryData);

  return (
    <div className="w-full max-w-3xl mx-auto my-4 text-left transition-all">
      {/* Assistant Header Tag */}
      <div className="flex items-center justify-between gap-3 mb-4 text-xs">
        <div className="flex items-center gap-2 text-neutral-400">
          <div className="w-6 h-6 rounded-full bg-white/10 flex items-center justify-center text-teal-400 border border-white/10 shadow-sm">
            <Sparkles className="w-3.5 h-3.5" />
          </div>
          <span className="font-medium text-white text-sm">TourAI</span>
          <span className="text-neutral-500">•</span>
          <span className="text-neutral-500 font-mono text-[11px]">
            Groq 120B · Multi-Agent Synthesis
          </span>
        </div>

        {/* Action Buttons (Copy / Share) */}
        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={handleCopy}
            className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-neutral-300 hover:text-white text-xs transition-colors cursor-pointer"
            title="Copy response"
          >
            {copied ? (
              <>
                <Check className="w-3 h-3 text-teal-400" />
                <span className="text-teal-400 text-[11px]">Copied</span>
              </>
            ) : (
              <>
                <Copy className="w-3 h-3 text-neutral-400" />
                <span className="text-[11px]">Copy</span>
              </>
            )}
          </button>

          <button
            type="button"
            onClick={handleShare}
            className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-neutral-300 hover:text-white text-xs transition-colors cursor-pointer"
            title="Share response"
          >
            <Share2 className="w-3 h-3 text-neutral-400" />
            <span className="text-[11px]">Share</span>
          </button>
        </div>
      </div>

      {/* Clean Markdown Response Body (Minimalist, readable typography matching user screenshot) */}
      <div className="text-[15px] text-neutral-200 leading-relaxed font-sans space-y-4">
        <ReactMarkdown
          components={{
            h1: ({ children }) => (
              <h1 className="text-xl sm:text-2xl font-bold text-white tracking-tight mt-6 mb-3">
                {children}
              </h1>
            ),
            h2: ({ children }) => (
              <h2 className="text-lg sm:text-xl font-bold text-white tracking-tight mt-6 mb-2.5 pt-2 border-b border-white/8">
                {children}
              </h2>
            ),
            h3: ({ children }) => (
              <h3 className="text-base sm:text-lg font-semibold text-white mt-5 mb-2">
                {children}
              </h3>
            ),
            h4: ({ children }) => (
              <h4 className="text-sm sm:text-base font-semibold text-teal-300 mt-4 mb-1.5">
                {children}
              </h4>
            ),
            p: ({ children }) => (
              <p className="text-[15px] text-neutral-200 leading-7 my-2.5 font-normal">
                {children}
              </p>
            ),
            ul: ({ children }) => (
              <ul className="my-3 space-y-2.5 pl-1 list-none">
                {children}
              </ul>
            ),
            ol: ({ children }) => (
              <ol className="my-3 space-y-2.5 pl-6 list-decimal text-neutral-200 leading-7">
                {children}
              </ol>
            ),
            li: ({ children }) => (
              <li className="text-[15px] text-neutral-200 leading-7 relative pl-5 before:content-['○'] before:absolute before:left-0 before:top-0 before:text-neutral-400 before:font-bold before:text-xs">
                {children}
              </li>
            ),
            strong: ({ children }) => (
              <strong className="font-semibold text-white">
                {children}
              </strong>
            ),
            blockquote: ({ children }) => (
              <blockquote className="border-l-2 border-teal-500/50 pl-4 py-1 italic text-neutral-400 my-3 bg-white/[0.02] rounded-r">
                {children}
              </blockquote>
            ),
            code: ({ children }) => (
              <code className="font-mono text-xs px-1.5 py-0.5 rounded bg-white/10 text-teal-300">
                {children}
              </code>
            ),
          }}
        >
          {planResult}
        </ReactMarkdown>
        {isStreaming && (
          <span className="inline-block w-2 h-4 ml-1 bg-teal-400 animate-pulse align-middle" />
        )}
      </div>

      {/* Optional Subtle Expandable Raw Agent Data (Hidden by default, zero clutter) */}
      {hasAgentArtifacts && (
        <div className="mt-8 pt-4 border-t border-white/8">
          <button
            type="button"
            onClick={() => setShowRawAgents(!showRawAgents)}
            className="flex items-center gap-1.5 text-xs text-neutral-500 hover:text-neutral-300 transition-colors cursor-pointer"
          >
            {showRawAgents ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            <span>{showRawAgents ? "Hide" : "View"} raw agent feeds ({llmCalls} LangGraph calls)</span>
          </button>

          {showRawAgents && (
            <div className="mt-4 space-y-3">
              {flightData && (
                <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5">
                  <div className="flex items-center gap-1.5 text-xs font-medium text-sky-400 mb-1">
                    <Plane className="w-3.5 h-3.5" />
                    <span>Flight Agent Feed (AviationStack)</span>
                  </div>
                  <pre className="text-xs text-neutral-400 whitespace-pre-wrap font-sans">
                    {flightData}
                  </pre>
                </div>
              )}

              {hotelData && (
                <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5">
                  <div className="flex items-center gap-1.5 text-xs font-medium text-indigo-400 mb-1">
                    <Hotel className="w-3.5 h-3.5" />
                    <span>Hotel Agent Feed (Tavily Search)</span>
                  </div>
                  <pre className="text-xs text-neutral-400 whitespace-pre-wrap font-sans">
                    {hotelData}
                  </pre>
                </div>
              )}

              {weatherData && (
                <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5">
                  <div className="flex items-center gap-1.5 text-xs font-medium text-cyan-400 mb-1">
                    <CloudSun className="w-3.5 h-3.5" />
                    <span>Weather Agent Feed (OpenWeatherMap FastMCP)</span>
                  </div>
                  <pre className="text-xs text-neutral-400 whitespace-pre-wrap font-sans">
                    {weatherData}
                  </pre>
                </div>
              )}

              {itineraryData && (
                <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5">
                  <div className="flex items-center gap-1.5 text-xs font-medium text-teal-400 mb-1">
                    <MapPin className="w-3.5 h-3.5" />
                    <span>Itinerary Agent Synthesizer</span>
                  </div>
                  <pre className="text-xs text-neutral-400 whitespace-pre-wrap font-sans">
                    {itineraryData}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
