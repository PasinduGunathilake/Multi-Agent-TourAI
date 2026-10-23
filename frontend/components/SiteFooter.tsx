"use client";

import React from "react";
import { ExternalLink, Terminal } from "lucide-react";

const GithubIcon = ({ className = "w-3.5 h-3.5" }: { className?: string }) => (
  <svg className={className} fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
    <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
  </svg>
);

export default function SiteFooter() {
  const footerLinks = {
    platform: [
      { label: "AI Travel Planner", href: "#" },
      { label: "Agent Architecture", href: "#architecture" },
      { label: "Agentic Engineering", href: "#features" },
      { label: "FastAPI Swagger Docs", href: "http://localhost:8000/docs", isExternal: true },
    ],
    techStack: [
      { label: "LangGraph StateGraph", desc: "Cyclic workflow & HITL" },
      { label: "Groq LPU Inference", desc: "gpt-oss-120b & 20b" },
      { label: "Google Gemini", desc: "Cross-provider failover" },
      { label: "PostgreSQL & Supabase", desc: "Dual memory checkpointing" },
      { label: "MCP Tool Connectors", desc: "AviationStack, Tavily, OpenWeather & Geoapify" },
    ],
    developer: [
      { label: "GitHub Repository", href: "https://github.com/PasinduGunathilake/Multi-Agent-TourAI", isExternal: true },
      { label: "Developer Profile", href: "https://github.com/PasinduGunathilake", isExternal: true },
      { label: "Project Architecture", href: "#architecture" },
    ],
  };

  return (
    <footer className="w-full bg-[#000000] border-t border-white/[0.08] relative z-10 pt-20 pb-12 overflow-hidden">
      {/* Top Main Section with Columns */}
      <div className="max-w-7xl mx-auto px-6 sm:px-10 lg:px-12 relative z-20">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-10 lg:gap-8 pb-16">
          {/* Brand & Project Info (5 cols on lg) */}
          <div className="lg:col-span-5 flex flex-col justify-start">
            <div className="flex items-center gap-2.5 mb-4">
              {/* Modern Square Brand Icon */}
              <div className="w-8 h-8 rounded-lg bg-white flex items-center justify-center shadow-md">
                <span className="text-black font-black text-base tracking-tighter">.\\</span>
              </div>
              <span className="text-xl font-bold text-white tracking-tight flex items-center gap-1">
                TourAI<span className="text-teal-400">.ai</span>
              </span>
            </div>

            <p className="text-xs text-white/50 max-w-sm leading-relaxed mb-5">
              Autonomous multi-agent travel intelligence orchestrating parallel flight lookups, boutique hotel analysis, and Human-in-the-Loop itinerary synthesis in real-time.
            </p>

            <div className="text-xs text-white/40 leading-relaxed">
              Designed &amp; Developed by <strong className="text-white/80 font-medium"> Pasindu Gunathilake</strong>
            </div>
          </div>

          {/* Platform Navigation (2 cols on lg) */}
          <div className="lg:col-span-2">
            <h4 className="text-xs font-mono uppercase tracking-wider text-teal-400/90 mb-4 font-semibold">
              Platform
            </h4>
            <ul className="space-y-3 text-xs text-white/60">
              {footerLinks.platform.map((link, idx) => (
                <li key={idx}>
                  <a
                    href={link.href}
                    target={link.isExternal ? "_blank" : undefined}
                    rel={link.isExternal ? "noreferrer" : undefined}
                    className="hover:text-white transition-colors duration-150 inline-flex items-center gap-1 group cursor-pointer"
                  >
                    <span>{link.label}</span>
                    {link.isExternal && (
                      <ExternalLink className="w-3 h-3 text-white/30 group-hover:text-teal-300 transition-colors" />
                    )}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Technology Stack (3 cols on lg) */}
          <div className="lg:col-span-3">
            <h4 className="text-xs font-mono uppercase tracking-wider text-teal-400/90 mb-4 font-semibold">
              Architecture Stack
            </h4>
            <ul className="space-y-3 text-xs text-white/60">
              {footerLinks.techStack.map((tech, idx) => (
                <li key={idx} className="flex flex-col">
                  <span className="text-white/80 font-medium">{tech.label}</span>
                  <span className="text-[10px] font-mono text-white/35">{tech.desc}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Developer & Links (2 cols on lg) */}
          <div className="lg:col-span-2">
            <h4 className="text-xs font-mono uppercase tracking-wider text-teal-400/90 mb-4 font-semibold">
              Repository
            </h4>
            <ul className="space-y-3 text-xs text-white/60">
              {footerLinks.developer.map((link, idx) => (
                <li key={idx}>
                  <a
                    href={link.href}
                    target={link.isExternal ? "_blank" : undefined}
                    rel={link.isExternal ? "noreferrer" : undefined}
                    className="hover:text-white transition-colors duration-150 inline-flex items-center gap-1.5 group cursor-pointer"
                  >
                    {link.label.includes("GitHub") ? (
                      <GithubIcon className="w-3.5 h-3.5 text-white/40 group-hover:text-white transition-colors" />
                    ) : (
                      <Terminal className="w-3.5 h-3.5 text-white/40 group-hover:text-white transition-colors" />
                    )}
                    <span>{link.label}</span>
                    {link.isExternal && (
                      <ExternalLink className="w-2.5 h-2.5 text-white/30 group-hover:text-teal-300 transition-colors ml-0.5" />
                    )}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Scaled-down elegant TourAI watermark integrated into footer section */}
        <div className="pt-8 pb-4 text-center sm:text-left select-none pointer-events-none">
          <h2 className="text-7xl sm:text-6xl md:text-7xl lg:text-9xl font-black tracking-normal leading-none text-white/[0.07] select-none inline-block">
            .\\ Tour<span className="text-white/20">AI</span>
          </h2>
        </div>

        {/* Bottom Micro Bar */}
        <div className="pt-6 border-t border-white/[0.06] flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-white/40">
          <div>
            © 2026 TourAI. Multi-Agent AI System. All rights reserved.
          </div>
          <div className="text-[11px] font-medium text-white/35 flex items-center gap-3">
            <span>LangGraph</span>
            <span>•</span>
            <span>Groq LPU</span>
            <span>•</span>
            <span>Google Gemini</span>
            <span>•</span>
            <span>PostgreSQL</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
