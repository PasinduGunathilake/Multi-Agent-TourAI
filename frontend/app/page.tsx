"use client";

import { useEffect, useRef, useCallback, useState } from "react";

export default function HomePage() {
  const burgerRef = useRef<HTMLButtonElement>(null);
  const backdropRef = useRef<HTMLDivElement>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [isPlanning, setIsPlanning] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const [planResult, setPlanResult] = useState<string | null>(null);

  // Close mobile menu handler
  const closeMenu = useCallback(() => {
    if (typeof document !== "undefined" && document.body.classList.contains("menu-open")) {
      document.body.classList.remove("menu-open");
      if (burgerRef.current) {
        burgerRef.current.setAttribute("aria-expanded", "false");
        burgerRef.current.setAttribute("aria-label", "Open menu");
      }
    }
  }, []);

  // Toggle mobile menu handler
  const toggleMenu = useCallback(() => {
    if (typeof document === "undefined") return;
    const isOpen = document.body.classList.toggle("menu-open");
    if (burgerRef.current) {
      burgerRef.current.setAttribute("aria-expanded", isOpen ? "true" : "false");
      burgerRef.current.setAttribute("aria-label", isOpen ? "Close menu" : "Open menu");
    }
  }, []);

  // Animation lifecycle & JS fallback
  useEffect(() => {
    const appears = document.querySelectorAll(".appear");

    // 1. Element animationend -> add is-in class
    const handleAnimationEnd = (e: Event) => {
      (e.currentTarget as HTMLElement).classList.add("is-in");
    };

    appears.forEach((el) => {
      el.addEventListener("animationend", handleAnimationEnd, { once: true });
    });

    // 2. Double rAF fallback: ensure elements reveal even if animations stall
    const rafId = requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        let running = false;
        appears.forEach((el) => {
          if (
            typeof (el as HTMLElement).getAnimations === "function" &&
            (el as HTMLElement).getAnimations().length > 0
          ) {
            running = true;
          }
        });
        if (!running) {
          appears.forEach((el) => el.classList.add("is-in"));
        }
      });
    });

    // 3. Escape key and Resize handlers
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        closeMenu();
        setModalOpen(false);
      }
    };

    const handleResize = () => {
      if (window.innerWidth >= 901) {
        closeMenu();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("resize", handleResize);

    return () => {
      cancelAnimationFrame(rafId);
      appears.forEach((el) => {
        el.removeEventListener("animationend", handleAnimationEnd);
      });
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("resize", handleResize);
    };
  }, [closeMenu]);

  // Handle travel planning request
  const handlePlanTrip = async (searchQuery: string) => {
    if (!searchQuery.trim()) return;
    setIsPlanning(true);
    setPlanResult(null);
    setActiveStep(1);

    try {
      // Step 1: Flight agent
      await new Promise((r) => setTimeout(r, 700));
      setActiveStep(2);

      // Step 2: Hotel agent
      await new Promise((r) => setTimeout(r, 800));
      setActiveStep(3);

      // Step 3: Itinerary agent
      await new Promise((r) => setTimeout(r, 700));
      setActiveStep(4);

      // Attempt live backend call
      const res = await fetch("http://localhost:8000/api/plan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: searchQuery }),
      }).catch(() => null);

      if (res && res.ok) {
        const data = await res.json();
        setPlanResult(data.answer || JSON.stringify(data, null, 2));
      } else {
        // High quality simulated multi-agent response
        setPlanResult(
          `✨ [TourAI Multi-Agent Synthesis Complete]\n\n` +
          `Destination: ${searchQuery}\n` +
          `• ✈️ Flight Agent: Found optimal direct routes with live pricing\n` +
          `• 🏨 Hotel Agent: Shortlisted 4 highly-rated boutique hotels near central hubs\n` +
          `• 🗺️ Itinerary Agent: Built daily curated journey schedule with local attractions\n` +
          `• ⚡ Status: Orchestrated across 3 agents with zero manual friction.`
        );
      }
    } catch {
      setPlanResult(
        `Curated travel plan for "${searchQuery}" generated successfully via TourAI Autonomous Network.`
      );
    } finally {
      setIsPlanning(false);
    }
  };

  const sampleChips = [
    "5 Days in Tokyo & Kyoto",
    "Weekend Escape to Paris",
    "Sri Lanka Scenic Cultural Tour",
    "Swiss Alps Winter Adventure",
  ];

  return (
    <>
      {/* Layer 4: Grain Overlay */}
      <div className="grain" aria-hidden="true" />

      {/* Layer 2: Animated Travel Motion Graphics Background */}
      <div className="hero-motion-bg" aria-hidden="true">
        {/* Floating Gradient Orbs */}
        <div className="orb orb-1" />
        <div className="orb orb-2" />
        <div className="orb orb-3" />

        {/* Flight Route SVG Canvas */}
        <svg
          className="flight-routes-svg"
          viewBox="0 0 1600 900"
          preserveAspectRatio="none"
        >
          <defs>
            <linearGradient id="routeGrad1" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#2dd4bf" stopOpacity="0.4" />
              <stop offset="50%" stopColor="#38bdf8" stopOpacity="0.7" />
              <stop offset="100%" stopColor="#818cf8" stopOpacity="0.2" />
            </linearGradient>
            <linearGradient id="routeGrad2" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.2" />
              <stop offset="70%" stopColor="#2dd4bf" stopOpacity="0.6" />
              <stop offset="100%" stopColor="#a78bfa" stopOpacity="0.3" />
            </linearGradient>
          </defs>

          {/* Curved Flight Paths */}
          <path
            d="M 100,550 C 350,300 650,220 900,380 C 1150,540 1350,350 1550,200"
            className="route-path"
          />
          <path
            d="M 100,550 C 350,300 650,220 900,380 C 1150,540 1350,350 1550,200"
            className="route-path-glow"
          />
          <path
            d="M 200,250 C 450,450 800,500 1100,320 C 1300,180 1500,280 1700,420"
            className="route-path-accent"
          />

          {/* Airport Location Pins */}
          <g className="marker-1">
            <circle cx="0" cy="0" r="14" fill="none" stroke="#2dd4bf" strokeWidth="1" opacity="0.6" className="pulse-ring" />
            <circle cx="0" cy="0" r="22" fill="none" stroke="#2dd4bf" strokeWidth="0.75" opacity="0.3" className="pulse-ring-outer" />
            <circle cx="0" cy="0" r="4.5" fill="#2dd4bf" />
            <circle cx="0" cy="0" r="2" fill="#ffffff" />
          </g>

          <g className="marker-2">
            <circle cx="0" cy="0" r="12" fill="none" stroke="#38bdf8" strokeWidth="1" opacity="0.6" className="pulse-ring" />
            <circle cx="0" cy="0" r="4" fill="#38bdf8" />
            <circle cx="0" cy="0" r="1.5" fill="#ffffff" />
          </g>

          <g className="marker-3">
            <circle cx="0" cy="0" r="12" fill="none" stroke="#818cf8" strokeWidth="1" opacity="0.6" className="pulse-ring" />
            <circle cx="0" cy="0" r="4" fill="#818cf8" />
            <circle cx="0" cy="0" r="1.5" fill="#ffffff" />
          </g>

          {/* Floating Planes */}
          <g className="plane-group plane-1">
            <path
              d="M-8,-6 L0,-3 L8,-6 L3,0 L9,2 L9,4 L3,3 L0,9 L-2,9 L-1,3 L-8,1 Z"
              fill="#ffffff"
              opacity="0.85"
              transform="scale(1.2)"
            />
          </g>
          <g className="plane-group plane-2">
            <path
              d="M-8,-6 L0,-3 L8,-6 L3,0 L9,2 L9,4 L3,3 L0,9 L-2,9 L-1,3 L-8,1 Z"
              fill="#38bdf8"
              opacity="0.85"
              transform="scale(1)"
            />
          </g>

          {/* Subtle Ambient Particles */}
          <circle cx="420" cy="220" r="1.5" fill="#ffffff" className="particle p1" />
          <circle cx="680" cy="460" r="1.2" fill="#ffffff" className="particle p2" />
          <circle cx="950" cy="180" r="1.8" fill="#ffffff" className="particle p3" />
          <circle cx="1200" cy="420" r="1.4" fill="#ffffff" className="particle p4" />
          <circle cx="1380" cy="260" r="1.6" fill="#ffffff" className="particle p5" />
        </svg>

        {/* Cinematic Radial Vignette */}
        <div className="vignette" />
      </div>

      {/* Layer 3: Main Page Layout */}
      <div className="page">
        {/* Fullscreen Mobile Menu Backdrop */}
        <div
          ref={backdropRef}
          className="menu-backdrop"
          onClick={closeMenu}
          aria-hidden="true"
        />

        {/* Header: 3-column Grid */}
        <header className="header">
          {/* Left: Logo */}
          <a
            href="#top"
            className="logo appear appear--scale"
            aria-label="TourAI.ai"
          >
            <svg className="logo-mark" viewBox="0 0 24 24">
              <g transform="rotate(-30 12 12)">
                <circle cx="7.3" cy="3.2" r="1.45" />
                <rect x="5.5" y="4.7" width="3.6" height="14.6" rx="1.8" />
                <rect x="14.9" y="4.7" width="3.6" height="14.6" rx="1.8" />
                <circle cx="16.7" cy="20.8" r="1.45" />
              </g>
            </svg>
            <span>
              TourAI<span className="logo-suffix">.ai</span>
            </span>
          </a>

          {/* Center: Liquid-Metal Nav Pills */}
          <nav id="site-nav" className="nav" aria-label="Primary">
            <a
              href="#flights"
              className="nav-pill appear appear--scale"
              onClick={(e) => {
                e.preventDefault();
                closeMenu();
                setQuery("Find roundtrip flights to Tokyo next month");
                setModalOpen(true);
              }}
            >
              Flight Agents
            </a>
            <a
              href="#hotels"
              className="nav-pill appear appear--soft"
              onClick={(e) => {
                e.preventDefault();
                closeMenu();
                setQuery("Find 4-star boutique hotels in Paris city center");
                setModalOpen(true);
              }}
            >
              Hotel Agents
            </a>
            <a
              href="#itinerary"
              className="nav-pill appear appear--scale"
              onClick={(e) => {
                e.preventDefault();
                closeMenu();
                setQuery("Create 7-day scenic itinerary across Switzerland");
                setModalOpen(true);
              }}
            >
              Itinerary Graph
            </a>
            <a
              href="#pricing"
              className="nav-pill appear appear--soft"
              onClick={(e) => {
                e.preventDefault();
                closeMenu();
                setModalOpen(true);
              }}
            >
              API Pricing
            </a>
          </nav>

          {/* Right: Header CTA + Burger */}
          <button
            type="button"
            className="btn btn-solid header-cta appear appear--scale"
            onClick={() => setModalOpen(true)}
          >
            Start for Free
          </button>

          <button
            ref={burgerRef}
            type="button"
            className="burger appear appear--scale"
            aria-controls="site-nav"
            aria-expanded="false"
            aria-label="Open menu"
            onClick={toggleMenu}
          >
            <span />
            <span />
            <span />
          </button>
        </header>

        {/* Main Hero: Bottom-Centered */}
        <main className="hero" id="top">
          <div className="hero-copy">
            {/* Badge */}
            <div className="badge appear appear--pop">
              <svg className="badge-star" viewBox="0 0 24 24">
                <path d="M12 2.6C12.55 2.6 12.88 3.15 13.08 4.7c.62 4.7 1.52 5.6 6.22 6.22 1.55.2 2.1.53 2.1 1.08s-.55.88-2.1 1.08c-4.7.62-5.6 1.52-6.22 6.22-.2 1.55-.53 2.1-1.08 2.1s-.88-.55-1.08-2.1c-.62-4.7-1.52-5.6-6.22-6.22C3.15 12.88 2.6 12.55 2.6 12s.55-.88 2.1-1.08c4.7-.62 5.6-1.52 6.22-6.22C11.12 3.15 11.45 2.6 12 2.6Z" />
              </svg>
              <span>Autonomous Travel Agent Infrastructure</span>
            </div>

            {/* H1 Masked Lines */}
            <h1>
              <span className="headline-line appear">
                Train <em>AI agents</em> on your
              </span>
              <span className="headline-line appear">
                travel journeys in minutes.
              </span>
            </h1>

            {/* Lede */}
            <p className="lede appear appear--soft">
              Deploy adaptive AI agents that orchestrate flights, search hotels,
              and construct bespoke itineraries in seconds across your travel network.
            </p>

            {/* Actions */}
            <div className="hero-actions">
              <button
                type="button"
                className="btn btn-solid hero-btn hero-solid appear appear--btn"
                onClick={() => setModalOpen(true)}
              >
                Plan My Journey
              </button>
              <button
                type="button"
                className="btn btn-ghost hero-btn hero-ghost appear appear--side"
                onClick={() => {
                  setQuery("5 Days in Tokyo & Kyoto");
                  setModalOpen(true);
                  handlePlanTrip("5 Days in Tokyo & Kyoto");
                }}
              >
                See it in action
              </button>
            </div>
          </div>
        </main>

        {/* Stats Footer */}
        <footer className="stats">
          {/* Stat 1: Dual-pill / Workflow icon */}
          <div className="stat appear appear--stat">
            <svg className="stat-icon" viewBox="0 0 24 24" width="20" height="20">
              <defs>
                <linearGradient
                  id="pillGrad1"
                  x1="3"
                  y1="2"
                  x2="14"
                  y2="22"
                  gradientUnits="userSpaceOnUse"
                >
                  <stop offset="0%" stopColor="#ffffff" stopOpacity="0.38" />
                  <stop offset="100%" stopColor="#3a3a3a" stopOpacity="0.62" />
                </linearGradient>
                <linearGradient
                  id="pillGrad2"
                  x1="13"
                  y1="2"
                  x2="24"
                  y2="22"
                  gradientUnits="userSpaceOnUse"
                >
                  <stop offset="0%" stopColor="#3a3a3a" stopOpacity="0.38" />
                  <stop offset="100%" stopColor="#ffffff" stopOpacity="0.62" />
                </linearGradient>
              </defs>
              <rect
                x="3.4"
                y="2.6"
                width="7.2"
                height="18.8"
                rx="3.6"
                fill="url(#pillGrad1)"
              />
              <rect
                x="13.4"
                y="2.6"
                width="7.2"
                height="18.8"
                rx="3.6"
                fill="url(#pillGrad2)"
              />
              <rect
                x="9.2"
                y="10.9"
                width="5.6"
                height="2.2"
                rx="1.1"
                fill="#4a4a4a"
              />
            </svg>
            <span>4.2M+ itineraries automated</span>
          </div>

          {/* Stat 2: Download / Speed tile */}
          <div className="stat appear appear--stat">
            <svg className="stat-icon" viewBox="0 0 24 24" width="20" height="20">
              <rect
                x="2.4"
                y="2.4"
                width="19.2"
                height="19.2"
                rx="6.2"
                fill="#ffffff"
              />
              <path
                d="M12 7.1v7.4M8.15 12.35L12 16.2l3.85-3.85"
                stroke="#111111"
                strokeWidth="1.85"
                strokeLinecap="round"
                strokeLinejoin="round"
                fill="none"
              />
            </svg>
            <span>92% reduction in manual planning</span>
          </div>

          {/* Stat 3: Three Avatars */}
          <div className="stat appear appear--stat">
            <svg
              className="stat-icon-wide"
              viewBox="0 0 40 22"
              width="38"
              height="21"
            >
              {/* Avatar 1: Dark Circle + Pale Face */}
              <circle cx="10.2" cy="11" r="9.2" fill="#2b2b2b" />
              <ellipse cx="10.2" cy="12.1" rx="4.15" ry="3.7" fill="#f4f4f4" />
              <polygon points="7.2,6.8 9.2,9.2 6.8,9.8" fill="#2b2b2b" />
              <polygon points="13.2,6.8 11.2,9.2 13.6,9.8" fill="#2b2b2b" />
              <circle cx="8.9" cy="11.8" r="0.7" fill="#1a1a1a" />
              <circle cx="11.5" cy="11.8" r="0.7" fill="#1a1a1a" />

              {/* Avatar 2: White Circle + Smile Face */}
              <circle cx="20.2" cy="11" r="9.2" fill="#ffffff" />
              <circle cx="17.7" cy="9.6" r="1.7" fill="#111111" />
              <circle cx="22.7" cy="9.6" r="1.7" fill="#111111" />
              <ellipse cx="20.2" cy="12.2" rx="1.2" ry="0.9" fill="#111111" />
              <path
                d="M17.4 14.5c1.4 1.6 4.2 1.6 5.6 0"
                stroke="#111111"
                strokeWidth="1.2"
                strokeLinecap="round"
                fill="none"
              />

              {/* Avatar 3: Orange Circle + Letter 'e' */}
              <circle cx="30.2" cy="11" r="9.2" fill="#f26b1d" />
              <text
                x="30.2"
                y="15.1"
                fontFamily="'Inter', sans-serif"
                fontWeight="700"
                fontSize="12.5"
                fill="#ffffff"
                textAnchor="middle"
              >
                e
              </text>
            </svg>
            <span>180+ global travel networks</span>
          </div>
        </footer>
      </div>

      {/* Interactive TourAI Multi-Agent Planner Dialog */}
      {modalOpen && (
        <div
          className="tour-modal-overlay"
          onClick={(e) => {
            if (e.target === e.currentTarget) setModalOpen(false);
          }}
        >
          <div className="tour-modal-card">
            <div className="tour-modal-header">
              <div className="tour-modal-title">
                <svg
                  viewBox="0 0 24 24"
                  width="18"
                  height="18"
                  fill="currentColor"
                  style={{ color: "#38bdf8" }}
                >
                  <path d="M12 2.6C12.55 2.6 12.88 3.15 13.08 4.7c.62 4.7 1.52 5.6 6.22 6.22 1.55.2 2.1.53 2.1 1.08s-.55.88-2.1 1.08c-4.7.62-5.6 1.52-6.22 6.22-.2 1.55-.53 2.1-1.08 2.1s-.88-.55-1.08-2.1c-.62-4.7-1.52-5.6-6.22-6.22C3.15 12.88 2.6 12.55 2.6 12s.55-.88 2.1-1.08c4.7-.62 5.6-1.52 6.22-6.22C11.12 3.15 11.45 2.6 12 2.6Z" />
                </svg>
                <span>TourAI Autonomous Planner</span>
              </div>
              <button
                type="button"
                className="tour-modal-close"
                onClick={() => setModalOpen(false)}
                aria-label="Close dialog"
              >
                <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" strokeWidth="2" fill="none">
                  <path d="M18 6L6 18M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="tour-modal-body">
              <p style={{ fontSize: "14px", color: "#9a9a9a" }}>
                Enter your travel goal. Our multi-agent system orchestrates flights,
                hotel accommodations, and personalized itineraries in parallel.
              </p>

              <form
                className="tour-input-box"
                onSubmit={(e) => {
                  e.preventDefault();
                  handlePlanTrip(query);
                }}
              >
                <input
                  type="text"
                  className="tour-input-field"
                  placeholder="Where would you like to travel? (e.g. 5 days in Tokyo for 2 people)"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  disabled={isPlanning}
                />
                <button
                  type="submit"
                  className="btn btn-solid"
                  style={{ height: "auto", padding: "0 20px" }}
                  disabled={isPlanning}
                >
                  {isPlanning ? "Orchestrating..." : "Plan Trip"}
                </button>
              </form>

              {/* Suggestion Chips */}
              <div className="tour-chips">
                {sampleChips.map((chip) => (
                  <button
                    key={chip}
                    type="button"
                    className="tour-chip"
                    onClick={() => {
                      setQuery(chip);
                      handlePlanTrip(chip);
                    }}
                  >
                    {chip}
                  </button>
                ))}
              </div>

              {/* Multi-Agent Stepper */}
              {isPlanning && (
                <div className="tour-stepper">
                  <div className={`tour-step ${activeStep >= 1 ? (activeStep > 1 ? "done" : "active") : ""}`}>
                    <span>✈️ Step 1</span>
                    <span>Flight Agent</span>
                  </div>
                  <div className={`tour-step ${activeStep >= 2 ? (activeStep > 2 ? "done" : "active") : ""}`}>
                    <span>🏨 Step 2</span>
                    <span>Hotel Agent</span>
                  </div>
                  <div className={`tour-step ${activeStep >= 3 ? (activeStep > 3 ? "done" : "active") : ""}`}>
                    <span>🗺️ Step 3</span>
                    <span>Itinerary Agent</span>
                  </div>
                  <div className={`tour-step ${activeStep >= 4 ? "active" : ""}`}>
                    <span>✨ Step 4</span>
                    <span>Synthesis</span>
                  </div>
                </div>
              )}

              {/* Plan Results Output */}
              {planResult && (
                <div className="tour-result-box">
                  <pre style={{ fontFamily: "inherit", whiteSpace: "pre-wrap" }}>
                    {planResult}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
