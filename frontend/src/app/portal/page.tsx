"use client";

import React from "react";
import Link from "next/link";
import { useRegions, useWells, useRecommendations, useStructures } from "@/lib/hooks/useData";
import { useMapStore } from "@/store/map-store";
import { MapContainerWrapper } from "@/components/map/MapContainerWrapper";
import { Sidebar } from "@/components/dashboard/Sidebar";
import { RegionSelector } from "@/components/dashboard/RegionSelector";
import { SiteDetailPanel } from "@/components/dashboard/SiteDetailPanel";
import { MarkAsBuiltModal } from "@/components/dashboard/MarkAsBuiltModal";
import { FaqModal } from "@/components/dashboard/FaqModal";
import { WaterLevelChart } from "@/components/charts/WaterLevelChart";
import { VerificationChart } from "@/components/charts/VerificationChart";
import { Settings, HelpCircle, Clock } from "lucide-react";

export default function HomePage() {
  const {
    sidebarOpen,
    selectedFeature,
    setFaqOpen,
    siteDetailOpen,
    selectedRegionId,
  } = useMapStore();

  const queryParams = selectedRegionId ? { region_id: selectedRegionId } : undefined;

  const { data: regionsData, isLoading: regionsLoading } = useRegions();
  const { data: wellsData } = useWells(queryParams);
  const { data: recommendationsData } = useRecommendations(queryParams);
  const { data: structuresData } = useStructures(queryParams);

  const allRegions: any[] = regionsData?.features || [];
  const mapRegions = selectedRegionId 
    ? allRegions.filter(r => r.properties.region_id === selectedRegionId) 
    : allRegions;

  const wells: any[] = wellsData?.features || [];
  const recommendations: any[] = recommendationsData?.features || [];
  const structures: any[] = structuresData?.features || [];

  return (
    <main className="relative w-screen h-screen overflow-hidden bg-slate-950 font-sans">
      {/* Government Portal Sidebar Control Panel */}
      <Sidebar recommendations={recommendations} />

      {/* Main Map Visualization Viewport */}
      <div className="w-full h-full">
        <MapContainerWrapper
          regions={mapRegions}
          wells={wells}
          recommendations={recommendations}
          structures={structures}
        />
      </div>

      {/* Top Floating Dashboard Header & Pan-India Region Selector Overlay */}
      <div
        className={`absolute top-4 transition-all duration-300 z-[1000] flex flex-wrap items-center justify-between gap-3 right-4 ${
          sidebarOpen ? "left-84" : "left-18"
        }`}
      >
        <RegionSelector regions={allRegions} isLoading={regionsLoading} />

        {/* Top Right Institutional Action Tools */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setFaqOpen(true)}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-900/95 border border-slate-700 text-slate-200 hover:text-white hover:bg-slate-800 shadow-md backdrop-blur-md text-xs font-semibold transition-all cursor-pointer"
            title="System Methodology & Standards"
          >
            <HelpCircle size={14} className="text-amber-400" />
            <span className="hidden sm:inline">Methodology</span>
          </button>


        </div>
      </div>

      {/* Bottom Floating Analytics Chart Drawer */}
      {selectedFeature && !siteDetailOpen && (
        <div
          className={`absolute bottom-4 transition-all duration-300 z-[1000] right-4 ${
            sidebarOpen ? "left-84" : "left-18"
          }`}
        >
          <div className="max-w-xl">
            {selectedFeature.type === "well" && (
              <WaterLevelChart
                data={selectedFeature.data.properties.reading_history}
                stationCode={selectedFeature.data.properties.station_code}
              />
            )}
            {selectedFeature.type === "structure" && (
              <VerificationChart
                logs={selectedFeature.data.properties.verification_logs}
                structureType={selectedFeature.data.properties.structure_type}
              />
            )}
          </div>
        </div>
      )}

      {/* Interactive Overlays and Modals */}
      <SiteDetailPanel />
      <MarkAsBuiltModal />
      <FaqModal />
    </main>
  );
}
