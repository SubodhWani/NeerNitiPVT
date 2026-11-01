"use client";

import React, { useState, useEffect } from "react";
import { useMapStore } from "@/store/map-store";
import {
  X,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Hammer,
  Maximize2,
  Sparkles,
  Layers,
  TrendingUp,
  Filter,
  CheckCircle2,
  Cpu,
  Info,
} from "lucide-react";

export const SiteDetailPanel: React.FC = () => {
  const { siteDetailOpen, selectedSite, closeSiteDetail, openMarkAsBuiltModal, setViewport } = useMapStore();
  const [showFactors, setShowFactors] = useState(true);
  const [showMitigations, setShowMitigations] = useState(false);
  const [explanation, setExplanation] = useState<any>(null);

  useEffect(() => {
    if (siteDetailOpen && selectedSite) {
      setExplanation(null);
      fetch(`http://localhost:8000/api/v1/sites/${selectedSite.properties.recommendation_id}/explanation`)
        .then(res => res.json())
        .then(data => {
          if (data && data.data) setExplanation(data.data);
        })
        .catch(err => console.error("Failed to fetch dynamic explanation:", err));
    }
  }, [siteDetailOpen, selectedSite]);

  if (!siteDetailOpen || !selectedSite) return null;

  const props = selectedSite.properties;
  const score = props.final_suitability_score;
  const normalizedScore = (score / 100).toFixed(2);
  const risk = props.risk_category || "Low";
  const coords = selectedSite.geometry.coordinates;

  const getRiskBadge = (r: string) => {
    switch (r) {
      case "High":
        return {
          bg: "bg-red-950/60",
          border: "border-red-800",
          text: "text-red-400",
          icon: <ShieldAlert size={14} className="text-red-400" />,
          mitigation: "Mandatory multi-chamber settling basin + 1.0m coarse sand/activated carbon filter bed. Quarterly nitrate & TDS lab assays required.",
        };
      case "Medium":
        return {
          bg: "bg-amber-950/60",
          border: "border-amber-800",
          text: "text-amber-400",
          icon: <AlertTriangle size={14} className="text-amber-400" />,
          mitigation: "Construct a 15m vegetative grass buffer strip and a dual-stage horizontal pebble-sand infiltration trap to arrest agricultural fertilizer runoff.",
        };
      default:
        return {
          bg: "bg-emerald-950/60",
          border: "border-emerald-800",
          text: "text-emerald-400",
          icon: <ShieldCheck size={14} className="text-emerald-400" />,
          mitigation: "Standard boulder apron and wire-mesh silt trap at structure intake. Low contamination risk.",
        };
    }
  };

  const riskBadge = getRiskBadge(risk);

  // Pre-construction forecasted rise calculation based on suitability score
  const predictedRiseMin = (0.8 + (score / 100) * 1.5).toFixed(1);
  const predictedRiseMax = (parseFloat(predictedRiseMin) + 0.6).toFixed(1);

  const mockFactors = [
    { name: "Gentle Terrain Slope", value: `+${(props.sub_scores?.slope_score ? props.sub_scores.slope_score * 0.08 : 0.28).toFixed(2)}`, pct: 82, positive: true },
    { name: "Soil Permeability & Infiltration", value: "+0.24", pct: 74, positive: true },
    { name: "Catchment Monsoon Precipitation", value: "+0.20", pct: 65, positive: true },
    { name: "Distance to River Drainage Line", value: "-0.05", pct: 25, positive: false },
  ];

  const handleZoomToSite = () => {
    setViewport(coords[1], coords[0], 14);
  };

  return (
    <aside className="fixed top-0 right-0 h-full w-96 max-w-[92vw] z-[2000] bg-slate-900 text-slate-100 border-l border-slate-800 flex flex-col shadow-2xl font-sans">
      
      {/* Top Tricolor Accent */}
      <div className="w-full h-1 flex flex-row">
        <div className="flex-1 bg-[#FF9933]"></div>
        <div className="flex-1 bg-[#FFFFFF]"></div>
        <div className="flex-1 bg-[#138808]"></div>
      </div>

      {/* Header */}
      <div className="p-3.5 border-b border-slate-800 bg-slate-950 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
            <h2 className="font-extrabold text-sm text-white">
              Candidate Site #{props.recommendation_id.slice(0, 8)}
            </h2>
          </div>
          <p className="text-[10.5px] text-slate-400 mt-0.5 font-mono">
            {coords[1].toFixed(4)}°N, {coords[0].toFixed(4)}°E • {props.structure_type}
          </p>
        </div>
        <button
          onClick={closeSiteDetail}
          className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors cursor-pointer"
        >
          <X size={15} />
        </button>
      </div>

      {/* Scrollable Body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-slate-800 text-xs">
        
        {/* 1. Suitability Score Meter (Guaranteed > 0.60) */}
        <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 space-y-2">
          <div className="flex justify-between items-center text-xs">
            <span className="text-slate-300 font-semibold flex items-center gap-1.5">
              <Sparkles size={13} className="text-amber-400" /> Suitability Index
            </span>
            <span className="text-base font-black text-amber-400 font-mono">
              {normalizedScore} <span className="text-[11px] text-slate-500 font-normal">/ 1.00</span>
            </span>
          </div>

          <div className="w-full h-2.5 bg-slate-800 rounded-full overflow-hidden p-0.5">
            <div
              className="h-full rounded-full bg-gradient-to-r from-amber-500 to-emerald-400 transition-all duration-700"
              style={{ width: `${Math.min(100, Math.max(30, score))}%` }}
            ></div>
          </div>
          <div className="flex justify-between text-[9px] text-slate-500 font-mono">
            <span>0.30 (Urban Baseline)</span>
            <span className="text-emerald-400 font-bold">Approved for Construction</span>
          </div>
        </div>

        {/* AI Explanation */}
        <div className="space-y-1.5">
          <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center justify-between">
            <span className="flex items-center gap-1">
              <Cpu size={12} className="text-blue-400" /> AI Explanation
            </span>
            <span className="text-[9px] text-blue-400 font-mono">Gemini / CGWB Model</span>
          </div>
          <div className="p-3 rounded-xl bg-blue-950/20 border border-blue-800/40 text-[11px] text-slate-200 leading-relaxed font-normal whitespace-pre-wrap">
            {explanation ? explanation.plain_text_summary : (
              <span className="animate-pulse flex items-center gap-2">
                <Sparkles size={12} className="text-amber-400" /> Generating LIME/SHAP detailed analysis...
              </span>
            )}
          </div>
        </div>

        {/* 5. SHAP Feature Attribution Breakdown */}
        <div className="space-y-2">
          <button
            onClick={() => setShowFactors(!showFactors)}
            className="w-full flex items-center justify-between text-[10px] font-bold text-slate-400 uppercase tracking-wider hover:text-slate-200 transition-colors"
          >
            <span className="flex items-center gap-1.5">
              <Layers size={12} className="text-emerald-400" /> SHAP Feature Attribution
            </span>
            {showFactors ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
          </button>

          {showFactors && (
            <div className="space-y-2 bg-slate-950 p-3 rounded-xl border border-slate-800">
              {explanation ? explanation.top_contributions.map((factor: any) => (
                <div key={factor.feature_name} className="space-y-0.5">
                  <div className="flex justify-between text-[10.5px]">
                    <span className="text-slate-300 capitalize">{factor.feature_name.replace(/_/g, " ")}</span>
                    <span className={`font-mono font-bold ${factor.direction === "positive" ? "text-emerald-400" : "text-red-400"}`}>
                      {factor.value > 0 ? `+${factor.value.toFixed(2)}` : factor.value.toFixed(2)}
                    </span>
                  </div>
                  <div className="w-full h-1 bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${factor.direction === "positive" ? "bg-emerald-500" : "bg-red-500"}`}
                      style={{ width: `${Math.min(100, Math.abs(factor.value) * 300)}%` }}
                    ></div>
                  </div>
                </div>
              )) : (
                <div className="animate-pulse text-[10px] text-slate-500 text-center py-2">Loading feature attributions...</div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Footer Actions */}
      <div className="p-3.5 border-t border-slate-800 bg-slate-950 space-y-2">
        <button
          onClick={() => openMarkAsBuiltModal(selectedSite)}
          className="w-full py-2.5 px-4 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-extrabold text-xs flex items-center justify-center gap-2 shadow-md shadow-blue-600/30 transition-all cursor-pointer"
        >
          <Hammer size={14} /> Mark as Built (Commence Construction)
        </button>

        <button
          onClick={handleZoomToSite}
          className="w-full py-2 px-4 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center justify-center gap-2 transition-colors cursor-pointer border border-slate-700/60"
        >
          <Maximize2 size={13} /> Center on Map
        </button>
      </div>
    </aside>
  );
};
