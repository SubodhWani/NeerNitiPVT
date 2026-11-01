"use client";

import React from "react";
import { useMapStore } from "@/store/map-store";
import { RecommendationFeature } from "@/lib/types";
import {
  Layers,
  Cpu,
  Zap,
  Filter,
  Eye,
  EyeOff,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  Clock,
  ListFilter,
  CheckCircle2,
  Droplet,
  Landmark,
} from "lucide-react";

interface SidebarProps {
  recommendations?: RecommendationFeature[];
}

export const Sidebar: React.FC<SidebarProps> = ({ recommendations = [] }) => {
  const {
    showRegions,
    showWells,
    showRecommendations,
    showStructures,
    toggleLayer,
    renderEngine,
    setRenderEngine,
    sidebarOpen,
    setSidebarOpen,
    setDataFreshnessOpen,
    setViewport,
  } = useMapStore();

  return (
    <aside
      className={`fixed top-0 left-0 h-full z-[1500] transition-all duration-300 flex select-none ${
        sidebarOpen ? "w-84" : "w-14"
      }`}
    >
      {/* Government Portal Sidebar Panel */}
      <div className="w-full h-full bg-slate-900 text-slate-100 border-r border-slate-800 flex flex-col shadow-xl overflow-hidden font-sans">
        
        {/* National Tricolor Civic Accent Strip */}
        <div className="w-full h-1 flex flex-row">
          <div className="flex-1 bg-[#FF9933]"></div>
          <div className="flex-1 bg-[#FFFFFF]"></div>
          <div className="flex-1 bg-[#138808]"></div>
        </div>

        {/* Institutional Header */}
        <div className="p-3.5 border-b border-slate-800 bg-slate-950/70 flex items-center justify-between min-h-[64px]">
          {sidebarOpen ? (
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-blue-900/60 border border-blue-700 flex items-center justify-center text-blue-300 font-bold shadow-sm">
                <Droplet size={18} className="text-blue-400 fill-blue-400/20" />
              </div>
              <div>

                <h1 className="font-black text-sm text-white tracking-tight leading-tight mt-0.5">
                  NeerNiti <span className="text-amber-400 font-serif font-normal text-xs">(नीर नीति)</span>
                </h1>
                <p className="text-[9.5px] text-slate-400 font-medium leading-none mt-0.5">
                  National MAR Decision Portal
                </p>
              </div>
            </div>
          ) : (
            <div className="w-8 h-8 rounded-lg bg-blue-900/60 border border-blue-700 flex items-center justify-center text-blue-300 font-bold mx-auto">
              <Droplet size={18} className="text-blue-400" />
            </div>
          )}

          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors cursor-pointer border border-slate-700/60"
            title={sidebarOpen ? "Collapse Sidebar" : "Expand Sidebar"}
          >
            {sidebarOpen ? <ChevronLeft size={15} /> : <ChevronRight size={15} />}
          </button>
        </div>

        {/* Scrollable Body */}
        {sidebarOpen && (
          <div className="flex-1 overflow-y-auto p-3.5 space-y-4 scrollbar-thin scrollbar-thumb-slate-800 text-xs">
            
            {/* 1. Rendering Engine Segmented Control */}
            <div className="space-y-2">
              <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <Cpu size={12} className="text-blue-400" /> Rendering Engine
              </div>
              <div className="grid grid-cols-2 gap-1.5 bg-slate-950 p-1 rounded-lg border border-slate-800">
                <button
                  onClick={() => setRenderEngine("deckgl")}
                  className={`py-1.5 px-2 rounded-md text-[11px] font-bold flex items-center justify-center gap-1.5 transition-all cursor-pointer ${
                    renderEngine === "deckgl"
                      ? "bg-blue-600 text-white shadow-sm font-extrabold"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <Zap size={12} /> GPU (Deck.gl)
                </button>
                <button
                  onClick={() => setRenderEngine("leaflet")}
                  className={`py-1.5 px-2 rounded-md text-[11px] font-bold flex items-center justify-center gap-1.5 transition-all cursor-pointer ${
                    renderEngine === "leaflet"
                      ? "bg-blue-600 text-white shadow-sm font-extrabold"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <Cpu size={12} /> CPU (Leaflet)
                </button>
              </div>
            </div>

            {/* 2. Official Thematic Map Layers */}
            <div className="space-y-2">
              <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <Layers size={12} className="text-emerald-400" /> Map Layers
              </div>

              <div className="space-y-1.5">
                {/* District Boundaries */}
                <button
                  onClick={() => toggleLayer("showRegions")}
                  className="w-full flex items-center justify-between p-2 rounded-lg bg-slate-950/70 border border-slate-800 text-[11px] font-semibold hover:bg-slate-800/80 transition-colors cursor-pointer"
                >
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 border border-emerald-400"></span>
                    <span className="text-slate-200">District Boundaries</span>
                  </div>
                  {showRegions ? <Eye size={14} className="text-emerald-400" /> : <EyeOff size={14} className="text-slate-500" />}
                </button>

                {/* Monitoring Wells */}
                <button
                  onClick={() => toggleLayer("showWells")}
                  className="w-full flex items-center justify-between p-2 rounded-lg bg-slate-950/70 border border-slate-800 text-[11px] font-semibold hover:bg-slate-800/80 transition-colors cursor-pointer"
                >
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-blue-500 border border-blue-400"></span>
                    <span className="text-slate-200">Monitoring Wells (CGWB)</span>
                  </div>
                  {showWells ? <Eye size={14} className="text-blue-400" /> : <EyeOff size={14} className="text-slate-500" />}
                </button>

                {/* AI Recommendations */}
                <button
                  onClick={() => toggleLayer("showRecommendations")}
                  className="w-full flex items-center justify-between p-2 rounded-lg bg-slate-950/70 border border-slate-800 text-[11px] font-semibold hover:bg-slate-800/80 transition-colors cursor-pointer"
                >
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-amber-400 border border-amber-300"></span>
                    <span className="text-slate-200">AI Recommendations (&gt;0.30)</span>
                  </div>
                  {showRecommendations ? <Eye size={14} className="text-amber-400" /> : <EyeOff size={14} className="text-slate-500" />}
                </button>

                {/* Built Structures */}
                <button
                  onClick={() => toggleLayer("showStructures")}
                  className="w-full flex items-center justify-between p-2 rounded-lg bg-slate-950/70 border border-slate-800 text-[11px] font-semibold hover:bg-slate-800/80 transition-colors cursor-pointer"
                >
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 border border-cyan-300"></span>
                    <span className="text-slate-200">Built Structures (Jal Shakti)</span>
                  </div>
                  {showStructures ? <Eye size={14} className="text-cyan-400" /> : <EyeOff size={14} className="text-slate-500" />}
                </button>
              </div>
            </div>


          </div>
        )}


      </div>
    </aside>
  );
};
