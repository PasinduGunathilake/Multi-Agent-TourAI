"use client";

import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import {
  Sparkles,
  Copy,
  Check,
  Share2,
  ChevronDown,
  ChevronUp,
  ThumbsUp,
  ThumbsDown,
  Plane,
  Hotel,
  CloudSun,
  MapPin,
  Compass,
} from "lucide-react";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import { MessageFooter, MessageAction } from "@/components/ui/message";

function cleanMarkdown(text: string): string {
  if (!text) return "";

  // 1. Separate table rows if squashed on one line (e.g. "| col1 | col2 | | row1 | row2 |")
  let cleaned = text.replace(/\|\s*\|\s*(?=[^|\n]+?\|)/g, "|\n| ");
  cleaned = cleaned.replace(/\|\s*\|(?=[\s-:]+\|)/g, "|\n|");

  // 2. Ensure blank line before any table block so CommonMark/GFM triggers parsing
  cleaned = cleaned.replace(/([^\n])\n(\|)/g, "$1\n\n$2");

  // 3. Ensure blank line after table block
  cleaned = cleaned.replace(/(\|\n)([^\n|#])/g, "$1\n\n$2");

  return cleaned;
}

interface TravelResultsViewProps {
  query: string;
  planResult: string;
  flightData?: string;
  hotelData?: string;
  weatherData?: string;
  mapsData?: string;
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
  mapsData,
  itineraryData,
  llmCalls = 4,
  isStreaming = false,
}: TravelResultsViewProps) {
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState<"like" | "dislike" | null>(null);
  const [showRawAgents, setShowRawAgents] = useState(false);

  const cleanedPlan = React.useMemo(() => cleanMarkdown(planResult), [planResult]);

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

  const hasAgentArtifacts = Boolean(flightData || hotelData || weatherData || mapsData || itineraryData);

  return (
    <div className="w-full max-w-3xl mx-auto my-3 text-left transition-all">
      {/* ── Metadata Header ── */}
      <div className="flex items-center justify-between gap-3 mb-2 text-xs">
        <div className="flex items-center gap-2 text-neutral-400">
          <span className="font-semibold text-white/90 text-sm">TourAI</span>
          <span className="text-neutral-600">•</span>
          <span className="text-neutral-500 font-mono text-[11px]">
            Groq 120B · Multi-Agent Synthesis
          </span>
        </div>
      </div>

      {/* ── Markdown Response Body ── */}
      <div className="text-[15px] text-neutral-200 leading-relaxed font-sans space-y-4">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          rehypePlugins={[rehypeRaw]}
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
            table: ({ children }) => (
              <div className="my-5 w-full overflow-x-auto rounded-xl border border-white/10 bg-white/[0.02] shadow-sm">
                <table className="w-full min-w-[500px] border-collapse text-left text-xs sm:text-sm">
                  {children}
                </table>
              </div>
            ),
            thead: ({ children }) => (
              <thead className="border-b border-white/10 bg-white/[0.05] text-[11px] font-semibold uppercase tracking-wider text-teal-300">
                {children}
              </thead>
            ),
            tbody: ({ children }) => (
              <tbody className="divide-y divide-white/5 font-sans">
                {children}
              </tbody>
            ),
            tr: ({ children }) => (
              <tr className="hover:bg-white/[0.02] transition-colors">
                {children}
              </tr>
            ),
            th: ({ children }) => (
              <th className="px-4 py-3 font-medium tracking-wide text-teal-300 whitespace-nowrap">
                {children}
              </th>
            ),
            td: ({ children }) => (
              <td className="px-4 py-3 align-top text-xs sm:text-[13px] text-neutral-300 leading-relaxed">
                {children}
              </td>
            ),
            hr: () => <hr className="my-6 border-white/10" />,
            a: ({ href, children }) => (
              <a
                href={href}
                target="_blank"
                rel="noreferrer"
                className="text-teal-400 hover:text-teal-300 underline underline-offset-2 transition-colors"
              >
                {children}
              </a>
            ),
          }}
        >
          {cleanedPlan}
        </ReactMarkdown>
        {isStreaming && (
          <span className="inline-block w-2 h-4 ml-1 bg-teal-400 animate-pulse align-middle" />
        )}
      </div>

      {/* ── Message Footer (Actions Bar following shadcn Message spec) ── */}
      {!isStreaming && (
        <MessageFooter className="mt-4 border-t border-white/6 pt-2">
          <MessageAction
            tooltip={copied ? "Copied" : "Copy itinerary"}
            onClick={handleCopy}
            className="text-neutral-400 hover:text-white"
          >
            {copied ? (
              <Check className="w-3.5 h-3.5 text-teal-400" />
            ) : (
              <Copy className="w-3.5 h-3.5" />
            )}
          </MessageAction>

          <MessageAction
            tooltip="Good response"
            isActive={feedback === "like"}
            onClick={() => setFeedback(feedback === "like" ? null : "like")}
            className="text-neutral-400 hover:text-emerald-300"
          >
            <ThumbsUp className="w-3.5 h-3.5" />
          </MessageAction>

          <MessageAction
            tooltip="Bad response"
            isActive={feedback === "dislike"}
            onClick={() => setFeedback(feedback === "dislike" ? null : "dislike")}
            className="text-neutral-400 hover:text-red-400"
          >
            <ThumbsDown className="w-3.5 h-3.5" />
          </MessageAction>

          <MessageAction
            tooltip="Share plan"
            onClick={handleShare}
            className="text-neutral-400 hover:text-white"
          >
            <Share2 className="w-3.5 h-3.5" />
          </MessageAction>
        </MessageFooter>
      )}

      {/* ── Optional Subtle Expandable Raw Agent Data ── */}
      {hasAgentArtifacts && (
        <div className="mt-4 pt-3">
          <button
            type="button"
            onClick={() => setShowRawAgents(!showRawAgents)}
            className="flex items-center gap-1.5 text-xs text-neutral-500 hover:text-neutral-300 transition-colors cursor-pointer font-mono"
          >
            {showRawAgents ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            <span>{showRawAgents ? "Hide" : "View"} raw agent feeds ({llmCalls} LangGraph calls)</span>
          </button>

          {showRawAgents && (
            <div className="mt-3 space-y-2.5">
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

              {mapsData && (
                <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5">
                  <div className="flex items-center gap-1.5 text-xs font-medium text-emerald-400 mb-1">
                    <Compass className="w-3.5 h-3.5" />
                    <span>Maps &amp; Places Agent Feed (Geoapify Remote MCP)</span>
                  </div>
                  <pre className="text-xs text-neutral-400 whitespace-pre-wrap font-sans">
                    {mapsData}
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
