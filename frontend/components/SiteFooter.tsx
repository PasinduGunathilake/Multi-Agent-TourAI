"use client";

import React from "react";
import { Sparkles } from "lucide-react";

export default function SiteFooter() {
  const footerLinks = {
    pages: [
      { label: "All Agents", href: "#features" },
      { label: "Architecture", href: "#architecture" },
      { label: "Flight Engine", href: "#features" },
      { label: "Pricing", href: "#pricing" },
      { label: "Documentation", href: "http://localhost:8000/docs", isExternal: true },
    ],
    socials: [
      { label: "GitHub", href: "https://github.com", isExternal: true },
      { label: "Discord", href: "https://discord.com", isExternal: true },
      { label: "Twitter / X", href: "https://twitter.com", isExternal: true },
      { label: "LinkedIn", href: "https://linkedin.com", isExternal: true },
    ],
    legal: [
      { label: "Privacy Policy", href: "#" },
      { label: "Terms of Service", href: "#" },
      { label: "Cookie Policy", href: "#" },
      { label: "Security & SLA", href: "#" },
    ],
    register: [
      { label: "Sign Up", href: "#pricing" },
      { label: "Login", href: "#" },
      { label: "API Keys", href: "http://localhost:8000/docs", isExternal: true },
      { label: "Forgot Password", href: "#" },
    ],
  };

  return (
    <footer className="w-full bg-[#000000] border-t border-white/[0.08] relative z-10 pt-20 pb-12 overflow-hidden">
      {/* Top Main Section with Columns */}
      <div className="max-w-7xl mx-auto px-6 sm:px-10 lg:px-12 relative z-20">
        <div className="grid grid-cols-2 md:grid-cols-6 lg:grid-cols-12 gap-10 lg:gap-8 pb-16">
          {/* Brand & Copyright Column (Takes 4 cols on lg) */}
          <div className="col-span-2 md:col-span-6 lg:col-span-4 flex flex-col justify-start">
            <div className="flex items-center gap-2.5 mb-4">
              {/* Modern Square Brand Icon */}
              <div className="w-8 h-8 rounded-lg bg-white flex items-center justify-center shadow-md">
                <span className="text-black font-black text-base tracking-tighter">\\</span>
              </div>
              <span className="text-xl font-bold text-white tracking-tight flex items-center gap-1">
                TourAI<span className="text-teal-400">.ai</span>
              </span>
            </div>

            <p className="text-xs text-white/45 max-w-xs leading-relaxed mb-6">
              Autonomous multi-agent intelligence orchestrating live flight routes, boutique hotels, and synthesis graphs in real-time.
            </p>

            <div className="text-xs text-white/40">
              © copyright TourAI 2026. <br />
              All rights reserved.<br />
              Developed By Pasindu Gunathilake
            </div>
          </div>

          {/* Pages Column (2 cols) */}
          <div className="col-span-1 md:col-span-2 lg:col-span-2">
            <h4 className="text-sm font-semibold text-white tracking-tight mb-4">Pages</h4>
            <ul className="space-y-3 text-xs text-white/55">
              {footerLinks.pages.map((link, idx) => (
                <li key={idx}>
                  <a
                    href={link.href}
                    target={link.isExternal ? "_blank" : undefined}
                    rel={link.isExternal ? "noreferrer" : undefined}
                    className="hover:text-white transition-colors duration-150 inline-block"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Socials Column (2 cols) */}
          <div className="col-span-1 md:col-span-2 lg:col-span-2">
            <h4 className="text-sm font-semibold text-white tracking-tight mb-4">Socials</h4>
            <ul className="space-y-3 text-xs text-white/55">
              {footerLinks.socials.map((link, idx) => (
                <li key={idx}>
                  <a
                    href={link.href}
                    target={link.isExternal ? "_blank" : undefined}
                    rel={link.isExternal ? "noreferrer" : undefined}
                    className="hover:text-white transition-colors duration-150 inline-block"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Legal Column (2 cols) */}
          <div className="col-span-1 md:col-span-2 lg:col-span-2">
            <h4 className="text-sm font-semibold text-white tracking-tight mb-4">Legal</h4>
            <ul className="space-y-3 text-xs text-white/55">
              {footerLinks.legal.map((link, idx) => (
                <li key={idx}>
                  <a
                    href={link.href}
                    className="hover:text-white transition-colors duration-150 inline-block"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Register Column (2 cols) */}
          <div className="col-span-1 md:col-span-2 lg:col-span-2">
            <h4 className="text-sm font-semibold text-white tracking-tight mb-4">Register</h4>
            <ul className="space-y-3 text-xs text-white/55">
              {footerLinks.register.map((link, idx) => (
                <li key={idx}>
                  <a
                    href={link.href}
                    target={link.isExternal ? "_blank" : undefined}
                    rel={link.isExternal ? "noreferrer" : undefined}
                    className="hover:text-white transition-colors duration-150 inline-block"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Massive Brand Watermark Typography (as in reference image) */}
      <div 
        className="w-full overflow-hidden select-none pointer-events-none relative -mb-6 md:-mb-10 lg:-mb-14"
        aria-hidden="true"
      >
        <div className="max-w-7xl mx-auto px-6 sm:px-10 lg:px-12">
          <h2 className="text-[17vw] lg:text-[18vw] font-black tracking-tighter leading-none text-white/[0.06] whitespace-nowrap -ml-2 select-none">
            Tour<span className="text-[17vw] lg:text-[18vw] font-black tracking-tighter leading-none text-white/20 whitespace-nowrap -ml-2 select-none">AI</span>
          </h2>
        </div>
      </div>
    </footer>
  );
}
