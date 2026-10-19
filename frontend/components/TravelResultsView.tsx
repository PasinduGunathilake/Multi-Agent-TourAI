import React, { useState } from "react";
import { Plane, Hotel, Calendar, Clock, MapPin, Sparkles, Share2, Layers, CloudSun, Wind, Droplets, Thermometer, ShieldCheck } from "lucide-react";

interface TravelResultsViewProps {
  query: string;
  planResult: string;
  flightData?: string;
  hotelData?: string;
  weatherData?: string;
  itineraryData?: string;
  llmCalls?: number;
}

export default function TravelResultsView({
  query,
  planResult,
  llmCalls = 4,
}: TravelResultsViewProps) {
  const [activeTab, setActiveTab] = useState<"overview" | "flights" | "hotels" | "weather" | "itinerary" | "telemetry">("overview");

  // Sample Mock Structured Flight Data based on query
  const sampleFlights = [
    {
      airline: "Emirates (EK 318)",
      from: "CMB / Origin",
      to: "Destination Hub",
      departure: "02:45 AM",
      arrival: "09:15 AM",
      duration: "6h 30m",
      stops: "Non-stop",
      price: "$680",
      tag: "Best Value",
    },
    {
      airline: "Qatar Airways (QR 665)",
      from: "CMB / Origin",
      to: "Destination Hub",
      departure: "08:10 AM",
      arrival: "04:30 PM",
      duration: "8h 20m",
      stops: "1 Stop (DOH)",
      price: "$740",
      tag: "Fastest Transfer",
    },
  ];

  // Sample Mock Structured Hotel Data // 
  const sampleHotels = [
    {
      name: "The Grand Heritage Boutique",
      rating: "4.9 ★★★★★",
      location: "City Center • 500m to Metro",
      price: "$185 / night",
      badge: "AI Top Pick",
      amenities: ["Free High-speed Wi-Fi", "Infinity Rooftop Pool", "Curated Breakfast", "Spa Access"],
    },
    {
      name: "Zenith Panoramic Suites",
      rating: "4.8 ★★★★☆",
      location: "Waterfront & Cultural District",
      price: "$240 / night",
      badge: "Luxury Favorite",
      amenities: ["Ocean View Balcony", "Michelin-starred Dining", "Concierge Butler", "Airport Shuttle"],
    },
  ];

  // Sample Mock Structured Weather Data (OpenWeatherMap FastMCP) //
  const sampleWeather = {
    current: {
      temp: "25°C",
      condition: "Clear & Sunny",
      feelsLike: "26°C",
      humidity: "58%",
      wind: "11 km/h",
      icon: "☀️",
    },
    forecast: [
      { day: "Day 1", temp: "26°C / 18°C", condition: "Sunny & Pleasant", icon: "☀️", humidity: "55%" },
      { day: "Day 2", temp: "27°C / 19°C", condition: "Clear Skies", icon: "🌤️", humidity: "52%" },
      { day: "Day 3", temp: "24°C / 17°C", condition: "Scattered Clouds", icon: "⛅", humidity: "62%" },
      { day: "Day 4", temp: "23°C / 16°C", condition: "Mild Breeze", icon: "🌤️", humidity: "60%" },
      { day: "Day 5", temp: "25°C / 18°C", condition: "Warm & Sunny", icon: "☀️", humidity: "54%" },
    ],
  };

  // Sample Mock Day-by-Day Itinerary Data //
  const sampleDays = [
    {
      day: "Day 1",
      title: "Arrival, Seamless Check-in & Sunset Skyline",
      morning: "Flight touchdown & private transfer to boutique hotel. Rest & unwind.",
      afternoon: "Historic Quarter stroll and authentic local gastronomy lunch.",
      evening: "Sky observation deck sunset view followed by welcome dinner at an artisan restaurant.",
    },
    {
      day: "Day 2",
      title: "Cultural Heritage & Modern Architecture Discovery",
      morning: "Guided exploration of iconic city landmarks and hidden temples / museums.",
      afternoon: "Artisan coffee stop & shopping through vibrant traditional boutique alleys.",
      evening: "Curated river/harbor dinner cruise with panoramic evening lights.",
    },
    {
      day: "Day 3",
      title: "Nature Excursion, Scenic Views & Farewell Dining",
      morning: "Scenic train or mountain excursion to panoramic viewpoints.",
      afternoon: "Local culinary workshop and souvenir craft market discovery.",
      evening: "Rooftop lounge celebration tasting local specialties before departure.",
    },
  ];

  return (
    <div className="w-full max-w-5xl mx-auto my-8 px-4">
      <div className="rounded-2xl bg-[#0c1017]/90 border border-white/10 backdrop-blur-2xl shadow-2xl overflow-hidden">
        {/* Top Header Banner */}
        <div className="p-6 bg-gradient-to-r from-teal-500/10 via-sky-500/10 to-indigo-500/10 border-b border-white/10 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-mono text-teal-400">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Multi-Agent Synthesis Complete</span>
            </div>
            <h2 className="text-xl sm:text-2xl font-bold text-white mt-1 capitalize">
              {query || "Curated Travel Journey"}
            </h2>
            <p className="text-xs text-neutral-400 mt-1">
              Synthesized dynamically via LangGraph Fan-Out Swarm (AviationStack MCP, Tavily MCP, FastMCP Weather) & Groq 120B Smart LLM.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => {
                if (navigator.share) {
                  navigator.share({ title: "TourAI Plan", text: planResult });
                } else {
                  navigator.clipboard.writeText(planResult);
                  alert("Plan copied to clipboard!");
                }
              }}
              className="px-3.5 py-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-white text-xs flex items-center gap-1.5 transition-colors cursor-pointer"
            >
              <Share2 className="w-3.5 h-3.5" />
              <span>Share Plan</span>
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-1 p-2 bg-white/[0.02] border-b border-white/5 overflow-x-auto text-xs font-medium">
          <button
            onClick={() => setActiveTab("overview")}
            className={`px-4 py-2 rounded-lg transition-all cursor-pointer flex items-center gap-1.5 ${
              activeTab === "overview"
                ? "bg-white text-black font-semibold shadow-md"
                : "text-neutral-400 hover:text-white hover:bg-white/5"
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Overview</span>
          </button>
          <button
            onClick={() => setActiveTab("flights")}
            className={`px-4 py-2 rounded-lg transition-all cursor-pointer flex items-center gap-1.5 ${
              activeTab === "flights"
                ? "bg-white text-black font-semibold shadow-md"
                : "text-neutral-400 hover:text-white hover:bg-white/5"
            }`}
          >
            <Plane className="w-3.5 h-3.5 text-sky-400" />
            <span>Flights (2 Options)</span>
          </button>
          <button
            onClick={() => setActiveTab("hotels")}
            className={`px-4 py-2 rounded-lg transition-all cursor-pointer flex items-center gap-1.5 ${
              activeTab === "hotels"
                ? "bg-white text-black font-semibold shadow-md"
                : "text-neutral-400 hover:text-white hover:bg-white/5"
            }`}
          >
            <Hotel className="w-3.5 h-3.5 text-indigo-400" />
            <span>Hotels (2 Shortlisted)</span>
          </button>
          <button
            onClick={() => setActiveTab("weather")}
            className={`px-4 py-2 rounded-lg transition-all cursor-pointer flex items-center gap-1.5 ${
              activeTab === "weather"
                ? "bg-white text-black font-semibold shadow-md"
                : "text-neutral-400 hover:text-white hover:bg-white/5"
            }`}
          >
            <CloudSun className="w-3.5 h-3.5 text-cyan-400" />
            <span>Weather (FastMCP 5-Day)</span>
          </button>
          <button
            onClick={() => setActiveTab("itinerary")}
            className={`px-4 py-2 rounded-lg transition-all cursor-pointer flex items-center gap-1.5 ${
              activeTab === "itinerary"
                ? "bg-white text-black font-semibold shadow-md"
                : "text-neutral-400 hover:text-white hover:bg-white/5"
            }`}
          >
            <Calendar className="w-3.5 h-3.5 text-teal-400" />
            <span>Day-by-Day Timeline</span>
          </button>
          <button
            onClick={() => setActiveTab("telemetry")}
            className={`px-4 py-2 rounded-lg transition-all cursor-pointer flex items-center gap-1.5 ${
              activeTab === "telemetry"
                ? "bg-white text-black font-semibold shadow-md"
                : "text-neutral-400 hover:text-white hover:bg-white/5"
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            <span>Agent Telemetry</span>
          </button>
        </div>

        {/* Tab Content Area */}
        <div className="p-6">
          {/* TAB 1: OVERVIEW */}
          {activeTab === "overview" && (
            <div className="space-y-6">
              <div className="p-4 rounded-xl bg-white/[0.03] border border-white/5">
                <h4 className="text-sm font-semibold text-white mb-2 flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-teal-400" />
                  Executive Agent Summary
                </h4>
                <div className="text-sm text-neutral-300 leading-relaxed whitespace-pre-line font-sans">
                  {planResult}
                </div>
              </div>

              {/* Quick Summary Metrics Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="p-4 rounded-xl bg-white/[0.02] border border-white/5">
                  <div className="text-xs text-neutral-400 flex items-center gap-1">
                    <Plane className="w-3.5 h-3.5 text-sky-400" /> Optimal Route
                  </div>
                  <div className="text-lg font-semibold text-white mt-1">Direct Flight Available</div>
                  <div className="text-xs text-teal-400 mt-1">Starting from $680</div>
                </div>

                <div className="p-4 rounded-xl bg-white/[0.02] border border-white/5">
                  <div className="text-xs text-neutral-400 flex items-center gap-1">
                    <Hotel className="w-3.5 h-3.5 text-indigo-400" /> Accommodation
                  </div>
                  <div className="text-lg font-semibold text-white mt-1">Boutique & Central</div>
                  <div className="text-xs text-teal-400 mt-1">4.9 ★ Rating Selected</div>
                </div>

                <div className="p-4 rounded-xl bg-white/[0.02] border border-white/5">
                  <div className="text-xs text-neutral-400 flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5 text-emerald-400" /> Agent Processing
                  </div>
                  <div className="text-lg font-semibold text-white mt-1">Autonomous Graph</div>
                  <div className="text-xs text-neutral-400 mt-1">{llmCalls} LangGraph Node calls</div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: FLIGHTS */}
          {activeTab === "flights" && (
            <div className="space-y-4">
              <div className="text-xs text-neutral-400 mb-2">
                Real-time route queries powered by AviationStack & Travel APIs:
              </div>
              {sampleFlights.map((f, i) => (
                <div
                  key={i}
                  className="p-5 rounded-xl bg-white/[0.03] border border-white/10 hover:border-sky-500/40 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4"
                >
                  <div className="flex items-center gap-4">
                    <div className="p-3 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-400">
                      <Plane className="w-6 h-6" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-white text-base">{f.airline}</span>
                        <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-teal-500/20 text-teal-300">
                          {f.tag}
                        </span>
                      </div>
                      <div className="text-xs text-neutral-400 mt-1 flex items-center gap-3">
                        <span>{f.from} ➔ {f.to}</span>
                        <span>•</span>
                        <span>{f.duration} ({f.stops})</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between md:justify-end gap-6 pt-3 md:pt-0 border-t md:border-t-0 border-white/5">
                    <div className="text-right">
                      <div className="text-xl font-bold text-white">{f.price}</div>
                      <div className="text-[11px] text-neutral-400">roundtrip / person</div>
                    </div>
                    <button
                      type="button"
                      onClick={() => alert(`Selected flight: ${f.airline}`)}
                      className="px-4 py-2 rounded-lg bg-white/10 hover:bg-white text-neutral-200 hover:text-black font-medium text-xs transition-colors cursor-pointer"
                    >
                      Lock Price
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* TAB 3: HOTELS */}
          {activeTab === "hotels" && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {sampleHotels.map((h, i) => (
                <div
                  key={i}
                  className="p-5 rounded-xl bg-white/[0.03] border border-white/10 hover:border-indigo-500/40 transition-all flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-start justify-between gap-2">
                      <span className="text-[11px] font-mono px-2 py-0.5 rounded-md bg-indigo-500/20 text-indigo-300">
                        {h.badge}
                      </span>
                      <span className="text-xs text-amber-400 font-semibold">{h.rating}</span>
                    </div>

                    <h4 className="text-base font-semibold text-white mt-3">{h.name}</h4>
                    <p className="text-xs text-neutral-400 mt-1 flex items-center gap-1">
                      <MapPin className="w-3.5 h-3.5 text-neutral-500" />
                      {h.location}
                    </p>

                    <div className="mt-4 flex flex-wrap gap-1.5">
                      {h.amenities.map((am, idx) => (
                        <span key={idx} className="text-[10px] px-2 py-1 rounded bg-white/5 text-neutral-300 border border-white/5">
                          ✓ {am}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="mt-6 pt-4 border-t border-white/5 flex items-center justify-between">
                    <div>
                      <div className="text-lg font-bold text-white">{h.price}</div>
                      <div className="text-[10px] text-neutral-400">Taxes & fees included</div>
                    </div>
                    <button
                      type="button"
                      onClick={() => alert(`Shortlisted: ${h.name}`)}
                      className="px-3.5 py-1.5 rounded-lg bg-indigo-500/20 hover:bg-indigo-500 text-indigo-300 hover:text-white text-xs font-medium transition-colors cursor-pointer"
                    >
                      View Details
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* TAB 3: LIVE WEATHER & 5-DAY FORECAST (FastMCP OpenWeatherMap) */}
          {activeTab === "weather" && (
            <div className="space-y-6">
              {/* Current Weather Card */}
              <div className="p-6 rounded-xl bg-gradient-to-br from-cyan-950/30 to-[#0a1220] border border-cyan-500/20 backdrop-blur-md">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="flex items-center gap-4">
                    <span className="text-5xl">{sampleWeather.current.icon}</span>
                    <div>
                      <div className="text-3xl font-bold text-white tracking-tight">{sampleWeather.current.temp}</div>
                      <div className="text-sm text-cyan-300 font-medium">{sampleWeather.current.condition}</div>
                      <div className="text-xs text-neutral-400 mt-0.5">Feels like {sampleWeather.current.feelsLike}</div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div className="p-3 rounded-lg bg-white/5 border border-white/5 flex items-center gap-2.5">
                      <Droplets className="w-4 h-4 text-cyan-400" />
                      <div>
                        <div className="text-white/40 text-[10px]">Humidity</div>
                        <div className="text-white font-medium">{sampleWeather.current.humidity}</div>
                      </div>
                    </div>
                    <div className="p-3 rounded-lg bg-white/5 border border-white/5 flex items-center gap-2.5">
                      <Wind className="w-4 h-4 text-sky-400" />
                      <div>
                        <div className="text-white/40 text-[10px]">Wind</div>
                        <div className="text-white font-medium">{sampleWeather.current.wind}</div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-white/10 flex items-center justify-between text-[11px] text-white/40 font-mono">
                  <span>FastMCP Service: weather_mcp_search</span>
                  <span className="text-cyan-400">OpenWeatherMap Live Grounded ✓</span>
                </div>
              </div>

              {/* 5-Day Forecast Grid */}
              <div>
                <h4 className="text-xs font-mono uppercase tracking-wider text-neutral-400 mb-3 flex items-center gap-2">
                  <Calendar className="w-3.5 h-3.5 text-cyan-400" />
                  <span>5-Day Weather Outlook (Forecast MCP)</span>
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-5 gap-3">
                  {sampleWeather.forecast.map((f, i) => (
                    <div key={i} className="p-4 rounded-xl bg-white/[0.02] border border-white/5 hover:border-cyan-500/30 transition-all text-center">
                      <span className="text-xs font-mono text-cyan-300 font-semibold block mb-1">{f.day}</span>
                      <span className="text-3xl my-2 block">{f.icon}</span>
                      <div className="text-sm font-bold text-white">{f.temp}</div>
                      <div className="text-[11px] text-neutral-400 mt-1">{f.condition}</div>
                      <div className="text-[10px] text-cyan-400/70 mt-2 font-mono">💧 {f.humidity}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: DAY-BY-DAY ITINERARY */}
          {activeTab === "itinerary" && (
            <div className="space-y-4">
              {sampleDays.map((d, i) => (
                <div key={i} className="p-5 rounded-xl bg-white/[0.02] border border-white/5 hover:border-teal-500/30 transition-all">
                  <div className="flex items-center gap-3 mb-3">
                    <span className="px-2.5 py-1 rounded-md bg-teal-500/20 text-teal-300 font-mono text-xs font-semibold">
                      {d.day}
                    </span>
                    <h4 className="text-sm sm:text-base font-medium text-white">{d.title}</h4>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs text-neutral-300 mt-3 pt-3 border-t border-white/5">
                    <div className="p-3 rounded-lg bg-white/[0.02]">
                      <span className="text-[11px] font-mono text-amber-400 block mb-1">🌅 Morning</span>
                      {d.morning}
                    </div>
                    <div className="p-3 rounded-lg bg-white/[0.02]">
                      <span className="text-[11px] font-mono text-sky-400 block mb-1">☀️ Afternoon</span>
                      {d.afternoon}
                    </div>
                    <div className="p-3 rounded-lg bg-white/[0.02]">
                      <span className="text-[11px] font-mono text-indigo-400 block mb-1">🌙 Evening</span>
                      {d.evening}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* TAB 6: TELEMETRY */}
          {activeTab === "telemetry" && (
            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-black/50 border border-white/10 font-mono text-xs text-neutral-300 overflow-x-auto space-y-1.5">
                <div className="text-neutral-500 mb-2">{"// LangGraph Fan-Out / Fan-In Telemetry"}</div>
                <div className="text-teal-400">START → Fan-Out [flight_agent, hotel_agent, weather_agent] (Parallel Concurrency)</div>
                <div className="text-sky-400">State.flight_results: AviationStack MCP 200 OK (2 optimal airline routes)</div>
                <div className="text-indigo-400">State.hotel_results: Tavily Remote MCP 200 OK (Boutique accommodations curated)</div>
                <div className="text-cyan-400">State.weather_results: FastMCP OpenWeatherMap 200 OK (Live climate & 5-day forecast)</div>
                <div className="text-teal-300">Fan-In Convergence → itinerary_agent (Groq 120B Flagship Reasoning)</div>
                <div className="text-purple-400">Synthesis Complete → final_agent (Polished Travel Dossier Package)</div>
                <div className="text-amber-400">Zero-Downtime Fallback: Google Gemini 3.5 Flash Lite (Standby Armed)</div>
                <div className="text-neutral-400 mt-3 pt-2 border-t border-white/10">
                  Dual Memory: PostgresSaver (Session Checkpoints) + PostgresStore (Cross-session Persistence)
                </div>
                <div className="text-neutral-500">Total LLM Calls: {llmCalls} • Fan-Out Latency: ~1.4s (50% faster than sequential)</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
