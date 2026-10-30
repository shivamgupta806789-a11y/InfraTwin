import React, { useState, useEffect } from 'react';
import {
  Compass,
  AlertTriangle,
  ShieldAlert,
  Layers,
  MapPin,
  Waves,
  CircleDot,
} from 'lucide-react';
import { GeotechnicalSiteProfile, BoreholeRecord } from '../types/geotechnical';
import { fetchGeotechnicalProfileApi } from '../lib/api';

interface GeotechnicalIntelligenceViewProps {
  latitude?: number;
  longitude?: number;
  siteId?: string;
  className?: string;
}

export const GeotechnicalIntelligenceView: React.FC<GeotechnicalIntelligenceViewProps> = ({
  latitude = 28.6139,
  longitude = 77.2090,
  siteId = 'site-001',
  className = '',
}) => {
  const [profile, setProfile] = useState<GeotechnicalSiteProfile | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [selectedBorehole, setSelectedBorehole] = useState<BoreholeRecord | null>(null);

  useEffect(() => {
    setIsLoading(true);
    fetchGeotechnicalProfileApi(latitude, longitude, siteId)
      .then((data) => {
        setProfile(data);
        if (data.boreholes.length > 0) {
          setSelectedBorehole(data.boreholes[0]);
        }
        setIsLoading(false);
      })
      .catch(() => setIsLoading(false));
  }, [latitude, longitude, siteId]);

  if (isLoading || !profile) {
    return (
      <div className={`bg-white rounded-2xl border border-charcoal-200 p-8 flex flex-col items-center justify-center space-y-3 min-h-[350px] ${className}`}>
        <div className="w-8 h-8 border-2 border-charcoal-200 border-t-charcoal-800 rounded-full animate-spin" />
        <p className="text-xs text-charcoal-600 font-medium">Retrieving site geotechnical stratigraphy & borehole records...</p>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Top Header Card */}
      <div className="bg-white p-5 rounded-2xl border border-charcoal-200 shadow-2xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Compass className="w-4 h-4 text-blue-700" />
            <h2 className="text-base font-bold text-charcoal-900 tracking-tight">
              Site Geotechnical & Subsurface Stratigraphy Intelligence
            </h2>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-50 text-blue-800 border border-blue-200 font-semibold">
              IS 1892 / IS 1893 Standards
            </span>
          </div>
          <p className="text-xs text-charcoal-500 mt-0.5">
            Lithological strata profile, borehole core logs, groundwater table depth, and seismic hazard screening.
          </p>
        </div>

        <div className="flex items-center space-x-2 text-xs font-mono bg-stone-100 px-3 py-1.5 rounded-xl border border-charcoal-200 text-charcoal-700">
          <MapPin className="w-3.5 h-3.5 text-rose-600" />
          <span>{latitude.toFixed(4)}°N, {longitude.toFixed(4)}°E • {profile.crs}</span>
        </div>
      </div>

      {/* Geotechnical Key Parameters Strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-charcoal-200 shadow-2xs space-y-1">
          <div className="flex items-center justify-between text-charcoal-500 text-xs font-medium">
            <span>Dominant Lithology</span>
            <Layers className="w-4 h-4 text-charcoal-600" />
          </div>
          <div className="text-sm font-bold text-charcoal-900 line-clamp-1">{profile.dominant_soil_type}</div>
          <div className="text-[11px] text-charcoal-500">Quaternary Alluvium deposit</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-charcoal-200 shadow-2xs space-y-1">
          <div className="flex items-center justify-between text-charcoal-500 text-xs font-medium">
            <span>Seismic Hazard Zone</span>
            <ShieldAlert className="w-4 h-4 text-amber-600" />
          </div>
          <div className="text-sm font-bold text-charcoal-900">{profile.seismic_zone.split(' - ')[0]}</div>
          <div className="text-[11px] text-amber-700 font-medium font-mono">PGA: {profile.peak_ground_acceleration_g}g</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-charcoal-200 shadow-2xs space-y-1">
          <div className="flex items-center justify-between text-charcoal-500 text-xs font-medium">
            <span>Groundwater Table</span>
            <Waves className="w-4 h-4 text-blue-600" />
          </div>
          <div className="text-lg font-bold font-mono text-charcoal-900">-{profile.groundwater_table_m} m</div>
          <div className="text-[11px] text-blue-700 font-medium">Below finished grade level</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-charcoal-200 shadow-2xs space-y-1">
          <div className="flex items-center justify-between text-charcoal-500 text-xs font-medium">
            <span>100-Yr Flood Elevation</span>
            <AlertTriangle className="w-4 h-4 text-rose-500" />
          </div>
          <div className="text-lg font-bold font-mono text-charcoal-900">+{profile.flood_hazard_level_100yr_m} m</div>
          <div className="text-[11px] text-rose-700 font-medium">Regulatory plinth clearance required</div>
        </div>
      </div>

      {/* Main Grid: Soil Strata Table & Borehole Core Viewer */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Strata Profile Table (7 Cols) */}
        <div className="lg:col-span-7 bg-white rounded-2xl border border-charcoal-200 p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-charcoal-100">
            <div>
              <h3 className="text-sm font-bold text-charcoal-900 tracking-tight">
                Subsurface Geological Strata Profile (0 to -22.0m)
              </h3>
              <p className="text-[11px] text-charcoal-500">
                Calibrated against core recovery logs from on-site investigation.
              </p>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-stone-100 text-charcoal-700">
              4 Layers Identified
            </span>
          </div>

          <div className="space-y-3">
            {profile.regional_strata_summary.map((layer) => (
              <div
                key={layer.layer_id}
                className="p-3.5 rounded-xl border border-charcoal-200/90 bg-stone-50/50 space-y-2"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span
                      className="w-3.5 h-3.5 rounded-md border border-charcoal-300"
                      style={{ backgroundColor: layer.color_hex }}
                    />
                    <h4 className="text-xs font-bold text-charcoal-900">
                      {layer.layer_name}
                    </h4>
                  </div>
                  <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-stone-200 text-charcoal-800">
                    USCS: {layer.uscs_classification}
                  </span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] font-mono text-charcoal-600">
                  <div>
                    <span className="text-charcoal-400 block text-[10px]">Depth Range:</span>
                    <span className="font-semibold text-charcoal-900">
                      -{layer.depth_top_m}m to -{layer.depth_bottom_m}m
                    </span>
                  </div>
                  <div>
                    <span className="text-charcoal-400 block text-[10px]">SPT N-Value:</span>
                    <span className="font-semibold text-charcoal-900">
                      {layer.spt_n_value_avg ? `${layer.spt_n_value_avg} blows/300mm` : 'N/A'}
                    </span>
                  </div>
                  <div>
                    <span className="text-charcoal-400 block text-[10px]">Internal Friction:</span>
                    <span className="font-semibold text-charcoal-900">
                      {layer.friction_angle_deg ? `${layer.friction_angle_deg}°` : 'N/A'}
                    </span>
                  </div>
                  <div>
                    <span className="text-charcoal-400 block text-[10px]">Indicative Bearing:</span>
                    <span className="font-semibold text-emerald-800">
                      {layer.allowable_bearing_capacity_kpa ? `${layer.allowable_bearing_capacity_kpa} kPa` : 'N/A'}
                    </span>
                  </div>
                </div>

                <p className="text-[11px] text-charcoal-600 leading-relaxed pt-1 border-t border-charcoal-100">
                  {layer.geological_description}
                </p>
              </div>
            ))}
          </div>

          {/* Statutory Screening Disclaimer */}
          <div className="p-3 bg-amber-50 rounded-xl border border-amber-200/80 text-[11px] text-amber-900 leading-relaxed space-y-1">
            <div className="font-bold flex items-center space-x-1">
              <ShieldAlert className="w-3.5 h-3.5 text-amber-700" />
              <span>Engineering Disclaimers & Code Notice</span>
            </div>
            <p>{profile.screening_disclaimer}</p>
          </div>
        </div>

        {/* Right Column: Borehole Log Records (5 Cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-white rounded-2xl border border-charcoal-200 p-5 shadow-xs space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-charcoal-900 tracking-tight flex items-center space-x-1.5">
                <CircleDot className="w-4 h-4 text-emerald-700" />
                <span>Investigation Core Boreholes</span>
              </h3>
              <span className="text-xs text-charcoal-500 font-mono">
                {profile.boreholes.length} Drilled Logs
              </span>
            </div>

            {/* Borehole Selection Pills */}
            <div className="grid grid-cols-3 gap-1.5 bg-stone-100 p-1 rounded-xl border border-charcoal-200 text-xs">
              {profile.boreholes.map((bh) => (
                <button
                  key={bh.borehole_id}
                  onClick={() => setSelectedBorehole(bh)}
                  className={`py-1.5 px-2 rounded-lg font-bold text-center transition-all ${
                    selectedBorehole?.borehole_id === bh.borehole_id
                      ? 'bg-charcoal-900 text-white shadow-2xs'
                      : 'text-charcoal-600 hover:text-black'
                  }`}
                >
                  {bh.borehole_id}
                </button>
              ))}
            </div>

            {/* Selected Borehole Core Details */}
            {selectedBorehole && (
              <div className="space-y-3 pt-2">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-charcoal-900">
                    {selectedBorehole.name}
                  </h4>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 font-bold">
                    VERIFIED CORE
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="p-2.5 bg-stone-50 rounded-lg border border-charcoal-100">
                    <span className="text-charcoal-500 text-[10px]">Total Core Depth</span>
                    <div className="font-bold font-mono text-charcoal-900 mt-0.5">
                      {selectedBorehole.total_depth_m} m
                    </div>
                  </div>
                  <div className="p-2.5 bg-stone-50 rounded-lg border border-charcoal-100">
                    <span className="text-charcoal-500 text-[10px]">Water Table Encountered</span>
                    <div className="font-bold font-mono text-blue-700 mt-0.5">
                      -{selectedBorehole.water_table_depth_m} m
                    </div>
                  </div>
                  <div className="p-2.5 bg-stone-50 rounded-lg border border-charcoal-100">
                    <span className="text-charcoal-500 text-[10px]">Surface Elevation</span>
                    <div className="font-bold font-mono text-charcoal-900 mt-0.5">
                      {selectedBorehole.ground_elevation_m} m AMSL
                    </div>
                  </div>
                  <div className="p-2.5 bg-stone-50 rounded-lg border border-charcoal-100">
                    <span className="text-charcoal-500 text-[10px]">Drilling Date</span>
                    <div className="font-bold font-mono text-charcoal-900 mt-0.5">
                      {selectedBorehole.drilling_date}
                    </div>
                  </div>
                </div>

                <div className="p-3 bg-stone-50 rounded-xl border border-charcoal-100 text-xs text-charcoal-600 space-y-1">
                  <span className="font-semibold text-charcoal-800">Contractor & Provenance:</span>
                  <p className="text-[11px] leading-relaxed">
                    {selectedBorehole.contractor} • {selectedBorehole.data_source}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
