"use client";

import React, { useState } from "react";
import { Check, Sparkles, Zap, Building2 } from "lucide-react";
import ScrollReveal from "./ScrollReveal";
import { GlowingEffect } from "./ui/glowing-effect";

export default function PricingSection() {
  const [annual, setAnnual] = useState(false);

  const plans = [
    {
      tier: "Starter",
      tagColor: "text-white/50",
      price: "$0",
      suffix: "",
      desc: "Ideal for discovering AI itinerary orchestration.",
      badge: null,
      features: [
        "10 Autonomous journeys / month",
        "Standard Flight & Hotel search",
        "Shareable travel plans",
        "Basic agent telemetry",
      ],
      cta: "Get Started Free",
      ctaClass: "bg-white/5 hover:bg-white/10 border border-white/12 text-white",
      cardClass: "bg-[#0b0f17]/90 border border-white/10",
      checkColor: "text-teal-400",
    },
    {
      tier: "Pro Traveler",
      tagColor: "text-sky-400",
      price: annual ? "$19" : "$24",
      suffix: "/ mo",
      desc: "Unlimited journeys with priority parallel agent swarms.",
      badge: "Most Popular",
      features: [
        "Unlimited journey plans",
        "Priority AviationStack live routes",
        "Deep Tavily boutique hotel ranking",
        "PostgreSQL persistent trip memory",
        "Day-by-Day AI itinerary builder",
        "Agent telemetry dashboard",
      ],
      cta: "Start 14-Day Free Trial",
      ctaClass: "bg-gradient-to-r from-teal-400 to-sky-400 hover:opacity-90 text-black font-bold shadow-lg shadow-sky-500/25",
      cardClass: "bg-gradient-to-b from-[#0f1d30] to-[#0a1220] border-2 border-sky-400/50 shadow-2xl shadow-sky-500/15",
      checkColor: "text-sky-400",
    },
    {
      tier: "Enterprise API",
      tagColor: "text-white/50",
      price: "Custom",
      suffix: "",
      desc: "Full REST & LangGraph WebSocket access for travel businesses.",
      badge: null,
      features: [
        "Dedicated agent swarms",
        "Custom tool integrations & webhooks",
        "99.9% uptime SLA & 24/7 support",
        "White-label dashboard",
      ],
      cta: "Contact Sales",
      ctaClass: "bg-white/5 hover:bg-white/10 border border-white/12 text-white",
      cardClass: "bg-[#0b0f17]/90 border border-white/10",
      checkColor: "text-teal-400",
    },
  ];

  return (
    <section className="w-full py-28 px-4 relative z-10 scroll-reveal-native" id="pricing">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <ScrollReveal direction="up" durationMs={800}>
          <div className="flex flex-col items-center text-center mb-14">
            <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-xs font-mono text-indigo-400 mb-4">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Simple, Transparent Pricing</span>
            </div>
            <h2 className="text-3xl sm:text-4xl font-bold text-white tracking-tight">
              Transparent, Scalable Pricing
            </h2>
            <p className="text-sm text-white/50 max-w-lg mx-auto mt-3 leading-relaxed">
              From solo globetrotters to enterprise travel networks orchestrating thousands of journeys per day.
            </p>

            {/* Billing Toggle */}
            <div className="flex items-center gap-3 mt-7 text-sm">
              <span className={`font-medium transition-colors ${!annual ? "text-white" : "text-white/35"}`}>Monthly</span>
              <button
                type="button"
                onClick={() => setAnnual(!annual)}
                className="relative w-12 h-6 rounded-full border border-white/15 bg-white/8 transition-all cursor-pointer overflow-hidden"
                aria-label="Toggle billing period"
              >
                <div
                  className="absolute top-1 w-4 h-4 rounded-full bg-gradient-to-r from-teal-400 to-sky-400 shadow-md transition-all duration-300"
                  style={{ left: annual ? "calc(100% - 20px)" : "4px" }}
                />
              </button>
              <span className={`font-medium transition-colors ${annual ? "text-white" : "text-white/35"}`}>
                Annual <span className="text-teal-400 text-xs font-mono ml-1">(Save 20%)</span>
              </span>
            </div>
          </div>
        </ScrollReveal>

        {/* Pricing Cards with staggered reveal */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-stretch pt-4">
          {plans.map((plan, i) => (
            <ScrollReveal
              key={i}
              direction="up"
              delayMs={i * 140}
              durationMs={750}
              className="h-full"
            >
              <div className="relative h-full rounded-2xl p-[1px] group">
                <GlowingEffect
                  spread={45}
                  glow={true}
                  disabled={false}
                  proximity={70}
                  inactiveZone={0.01}
                  borderWidth={2}
                />
                <div
                  className={`relative z-10 rounded-2xl ${plan.badge ? "pt-10" : "pt-7"} pb-7 px-7 flex flex-col justify-between ${plan.cardClass} backdrop-blur-xl transition-all duration-300 hover:translate-y-[-2px] h-full`}
                >
                  {/* Popular Badge */}
                  {plan.badge && (
                    <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 z-20">
                      <span className="px-3.5 py-1 rounded-full bg-gradient-to-r from-teal-400 to-sky-400 text-black text-[10px] font-bold tracking-widest uppercase whitespace-nowrap shadow-md shadow-sky-500/30">
                        {plan.badge}
                      </span>
                    </div>
                  )}

                  {/* Top section */}
                  <div>
                    <div className="flex items-center gap-2 mb-3">
                      {i === 0 && <Zap className="w-4 h-4 text-teal-400" />}
                      {i === 1 && <Sparkles className="w-4 h-4 text-sky-400" />}
                      {i === 2 && <Building2 className="w-4 h-4 text-indigo-400" />}
                      <span className={`text-xs font-mono uppercase tracking-widest font-medium ${plan.tagColor}`}>
                        {plan.tier}
                      </span>
                    </div>

                    <div className="flex items-baseline gap-1.5 mb-2">
                      <span className="text-4xl font-bold text-white tracking-tight">{plan.price}</span>
                      {plan.suffix && <span className="text-sm text-white/40">{plan.suffix}</span>}
                    </div>
                    {annual && plan.suffix && (
                      <div className="text-[11px] font-mono text-teal-400 mb-3">Billed annually ($228/yr)</div>
                    )}
                    <p className="text-xs text-white/50 mt-1 mb-5 leading-relaxed">{plan.desc}</p>

                    {/* Divider */}
                    <div className="h-px bg-white/6 mb-5" />

                    {/* Features */}
                    <ul className="space-y-3">
                      {plan.features.map((feat, j) => (
                        <li key={j} className="flex items-start gap-2.5 text-xs text-white/70">
                          <Check className={`w-4 h-4 mt-0.5 shrink-0 ${plan.checkColor}`} />
                          <span>{feat}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* CTA Button */}
                  <button
                    type="button"
                    className={`w-full mt-8 py-3 rounded-xl text-xs font-semibold transition-all duration-200 cursor-pointer ${plan.ctaClass}`}
                    onClick={() => alert(`Selected tier: ${plan.tier}`)}
                  >
                    {plan.cta}
                  </button>
                </div>
              </div>
            </ScrollReveal>
          ))}
        </div>

        {/* Footer note */}
        <p className="text-center text-xs text-white/30 mt-10">
          All plans include TLS encryption, GDPR compliance, and no hidden fees. Cancel anytime.
        </p>
      </div>
    </section>
  );
}
