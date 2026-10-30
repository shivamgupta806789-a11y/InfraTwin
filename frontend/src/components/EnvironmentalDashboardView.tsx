import React, { useState, useEffect, useRef, useCallback } from 'react';
import L from 'leaflet';
import {
  EnvironmentalAnalysisResponse,
  LocationPreset,
  EnvironmentalRecommendation,
} from '../types/environmental';
import { BuildingModelDetail } from '../types/digital_twin';
import {
  analyzeEnvironmentalSuitabilityApi,
  searchLocationsApi,
  getLocationPresetsApi,
} from '../lib/api';
import {
  MapPin,
  Compass,
  Sun,
  Wind,
  Droplets,
  Mountain,
  Trees,
  Building,
  ShieldAlert,
  Search,
  RotateCw,
  AlertTriangle,
  Info,
  Zap,
  Gauge,
  ChevronDown,
  ChevronUp,
  Flame,
  CloudRain,
  Eye,
} from 'lucide-react';

interface EnvironmentalDashboardViewProps {
  modelDetail?: BuildingModelDetail | null;
  className?: string;
}

// Fallback presets if network is offline
const FALLBACK_PRESETS: LocationPreset[] = [
  {
    display_name: 'New Delhi, India',
    latitude: 28.6139,
    longitude: 77.2090,
    city: 'New Delhi',
    state: 'Delhi',
    country: 'India',
    climate_hint: 'Cwa - Composite / Monsoon Subtropical',
  },
  {
    display_name: 'Mumbai, Maharashtra, India',
    latitude: 19.0760,
    longitude: 72.8777,
    city: 'Mumbai',
    state: 'Maharashtra',
    country: 'India',
    climate_hint: 'Aw - Tropical Wet & Dry / Coastal High Humidity',
  },
  {
    display_name: 'Bengaluru, Karnataka, India',
    latitude: 12.9716,
    longitude: 77.5946,
    city: 'Bengaluru',
    state: 'Karnataka',
    country: 'India',
    climate_hint: 'Aw - Moderate Tropical Savanna',
  },
  {
    display_name: 'Leh, Ladakh, India',
    latitude: 34.1526,
    longitude: 77.5771,
    city: 'Leh',
    state: 'Ladakh',
    country: 'India',
    climate_hint: 'BWk - Cold Arid High-Altitude Desert',
  },
  {
    display_name: 'London, Greater London, United Kingdom',
    latitude: 51.5074,
    longitude: -0.1278,
    city: 'London',
    state: 'England',
    country: 'United Kingdom',
    climate_hint: 'Cfb - Temperate Oceanic',
  },
  {
    display_name: 'Dubai, United Arab Emirates',
    latitude: 25.2048,
    longitude: 55.2708,
    city: 'Dubai',
    state: 'Dubai',
    country: 'United Arab Emirates',
    climate_hint: 'BWh - Hot Hyper-Arid Desert',
  },
  {
    display_name: 'Singapore',
    latitude: 1.3521,
    longitude: 103.8198,
    city: 'Singapore',
    state: 'Singapore',
    country: 'Singapore',
    climate_hint: 'Af - Equatorial Rainforest',
  },
];

export const EnvironmentalDashboardView: React.FC<EnvironmentalDashboardViewProps> = ({
  modelDetail,
  className = '',
}) => {
  // Coordinates & orientation state
  const [lat, setLat] = useState<number>(28.6139);
  const [lon, setLon] = useState<number>(77.2090);
  const [locationName, setLocationName] = useState<string>('New Delhi, India');
  const [azimuthDeg, setAzimuthDeg] = useState<number>(0); // 0 = North, 90 = East, 180 = South, 270 = West

  // Geocoding & search
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState<boolean>(false);
  const [showSearchResults, setShowSearchResults] = useState<boolean>(false);
  const [presets, setPresets] = useState<LocationPreset[]>(FALLBACK_PRESETS);

  // Analysis state
  const [analysis, setAnalysis] = useState<EnvironmentalAnalysisResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Recommendation category filter & expanded accordion
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [expandedRecId, setExpandedRecId] = useState<string | null>(null);

  // Leaflet map refs
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markerRef = useRef<L.Marker | null>(null);

  // Load presets on mount
  useEffect(() => {
    let isMounted = true;
    getLocationPresetsApi()
      .then((data) => {
        if (isMounted && data && data.length > 0) {
          setPresets(data);
        }
      })
      .catch(() => {
        // Fallback already set
      });
    return () => {
      isMounted = false;
    };
  }, []);

  // Fetch Environmental Analysis from Backend
  const runAnalysis = useCallback(
    async (targetLat: number, targetLon: number, targetAzimuth: number, addressHint?: string) => {
      setIsLoading(true);
      setErrorMsg(null);
      try {
        const cardinal = getCardinalFromAzimuth(targetAzimuth);
        const req = {
          location: {
            latitude: targetLat,
            longitude: targetLon,
            address: addressHint || locationName,
          },
          orientation: {
            azimuth_deg: targetAzimuth,
            cardinal_direction: cardinal,
          },
          model_id: modelDetail?.model_id || null,
          building_params: modelDetail
            ? {
                footprint_width_m: modelDetail.bounding_box
                  ? modelDetail.bounding_box.width
                  : 12.0,
                footprint_length_m: modelDetail.bounding_box
                  ? modelDetail.bounding_box.depth
                  : 16.0,
                total_height_m: modelDetail.bounding_box
                  ? modelDetail.bounding_box.height
                  : 6.0,
                roof_area_sqm: modelDetail.bounding_box
                  ? modelDetail.bounding_box.width * modelDetail.bounding_box.depth
                  : 192.0,
                window_area_sqm: 35.0,
              }
            : null,
        };

        const res = await analyzeEnvironmentalSuitabilityApi(req);
        setAnalysis(res);
        if (res.location.address) {
          setLocationName(res.location.address);
        }
      } catch (err: any) {
        setErrorMsg(err.message || 'Failed to complete environmental analysis.');
      } finally {
        setIsLoading(false);
      }
    },
    [locationName, modelDetail]
  );

  // Trigger analysis when location or orientation changes
  useEffect(() => {
    runAnalysis(lat, lon, azimuthDeg);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lat, lon, azimuthDeg]);

  // Leaflet Map Initialization & Updates
  useEffect(() => {
    if (!mapContainerRef.current) return;

    const pinHtml = `
      <div style="display:flex;align-items:center;justify-content:center;width:34px;height:34px;background:#047857;color:white;border-radius:50%;border:2.5px solid white;box-shadow:0 3px 8px rgba(0,0,0,0.35);cursor:grab;">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
          <circle cx="12" cy="10" r="3"></circle>
        </svg>
      </div>`;

    const customIcon = L.divIcon({
      className: 'infratwin-leaflet-pin',
      html: pinHtml,
      iconSize: [34, 34],
      iconAnchor: [17, 34],
      popupAnchor: [0, -34],
    });

    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: [lat, lon],
        zoom: 12,
        scrollWheelZoom: true,
      });

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19,
      }).addTo(map);

      const marker = L.marker([lat, lon], {
        icon: customIcon,
        draggable: true,
      }).addTo(map);

      marker.bindPopup(`<b>Proposed Building Site</b><br/>${lat.toFixed(4)}°, ${lon.toFixed(4)}°`);

      marker.on('dragend', (e) => {
        const markerPos = e.target.getLatLng();
        setLat(Number(markerPos.lat.toFixed(4)));
        setLon(Number(markerPos.lng.toFixed(4)));
        setLocationName(`Site at ${markerPos.lat.toFixed(4)}°, ${markerPos.lng.toFixed(4)}°`);
      });

      map.on('click', (e) => {
        const { lat: clickLat, lng: clickLng } = e.latlng;
        setLat(Number(clickLat.toFixed(4)));
        setLon(Number(clickLng.toFixed(4)));
        setLocationName(`Site at ${clickLat.toFixed(4)}°, ${clickLng.toFixed(4)}°`);
        marker.setLatLng([clickLat, clickLng]);
        marker.openPopup();
      });

      mapInstanceRef.current = map;
      markerRef.current = marker;

      // Invalidate size to ensure proper tile rendering
      setTimeout(() => {
        map.invalidateSize();
      }, 250);
    } else {
      mapInstanceRef.current.setView([lat, lon], mapInstanceRef.current.getZoom());
      if (markerRef.current) {
        markerRef.current.setLatLng([lat, lon]);
        markerRef.current.setPopupContent(`<b>Proposed Building Site</b><br/>${lat.toFixed(4)}°, ${lon.toFixed(4)}°`);
      }
    }

    return () => {
      // Keep map alive during tab usage or clean on full unmount
    };
  }, [lat, lon]);

  // Clean up map when component unmounts
  useEffect(() => {
    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Search places debounce
  useEffect(() => {
    if (!searchQuery.trim() || searchQuery.length < 2) {
      setSearchResults([]);
      setShowSearchResults(false);
      return;
    }

    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const results = await searchLocationsApi(searchQuery);
        setSearchResults(results);
        setShowSearchResults(true);
      } catch (e) {
        // ignore
      } finally {
        setIsSearching(false);
      }
    }, 400);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  const handleSelectSearchResult = (item: any) => {
    setLat(Number(item.latitude.toFixed(4)));
    setLon(Number(item.longitude.toFixed(4)));
    setLocationName(item.display_name);
    setShowSearchResults(false);
    setSearchQuery('');
  };

  const handleSelectPreset = (p: LocationPreset) => {
    setLat(p.latitude);
    setLon(p.longitude);
    setLocationName(p.display_name);
  };

  // Cardinal direction helper
  function getCardinalFromAzimuth(deg: number): string {
    const normalized = ((deg % 360) + 360) % 360;
    const directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'];
    const index = Math.round(normalized / 22.5) % 16;
    return directions[index];
  }

  // Filter recommendations
  const filteredRecommendations = (analysis?.recommendations || []).filter((rec) => {
    if (selectedCategory === 'all') return true;
    return rec.category === selectedCategory;
  });

  // Score color helper
  const getScoreBadgeColor = (score: number) => {
    if (score >= 80) return 'bg-emerald-100 text-emerald-800 border-emerald-300';
    if (score >= 65) return 'bg-teal-100 text-teal-800 border-teal-300';
    if (score >= 50) return 'bg-amber-100 text-amber-800 border-amber-300';
    return 'bg-rose-100 text-rose-800 border-rose-300';
  };

  const getPriorityBadgeColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'bg-rose-100 text-rose-800 border-rose-200';
      case 'medium':
        return 'bg-amber-100 text-amber-800 border-amber-200';
      case 'low':
      default:
        return 'bg-sky-100 text-sky-800 border-sky-200';
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* 1. Header & Active Site Bar */}
      <div className="bg-white p-5 rounded-xl border border-charcoal-200 shadow-2xs">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex flex-wrap items-center gap-2">
              <div className="p-2 bg-emerald-50 text-emerald-800 rounded-lg border border-emerald-200">
                <MapPin className="w-5 h-5" />
              </div>
              <h2 className="text-base font-bold text-charcoal-900 tracking-tight">
                Geolocation & Environmental Intelligence
              </h2>
              <span className="text-xs px-2.5 py-0.5 rounded-full font-semibold border bg-emerald-50 text-emerald-800 border-emerald-200 flex items-center space-x-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                <span>Open-Meteo & OpenStreetMap Active</span>
              </span>
              {analysis?.cached && (
                <span className="text-[10px] px-2 py-0.5 rounded bg-stone-100 text-charcoal-600 border border-stone-200">
                  Cached Site Baseline
                </span>
              )}
            </div>
            <p className="text-xs text-charcoal-600">
              Selected Site:{' '}
              <span className="font-semibold text-charcoal-800">{locationName}</span> (
              <span className="font-mono">{lat.toFixed(4)}°N, {lon.toFixed(4)}°E</span>)
              {modelDetail && (
                <span className="ml-2 pl-2 border-l border-charcoal-300 text-charcoal-500">
                  Coupled Twin: <span className="font-semibold text-charcoal-700">{modelDetail.building_name || modelDetail.model_id}</span> ({modelDetail.storeys?.length || 1} storeys, {modelDetail.bounding_box?.height ? modelDetail.bounding_box.height.toFixed(1) : '6.0'}m)
                </span>
              )}
            </p>
          </div>

          <div className="flex items-center space-x-2 shrink-0">
            <button
              onClick={() => runAnalysis(lat, lon, azimuthDeg)}
              disabled={isLoading}
              className="flex items-center space-x-1.5 bg-charcoal-900 hover:bg-charcoal-950 text-white text-xs font-semibold px-3.5 py-2 rounded-lg transition-colors shadow-2xs disabled:opacity-50"
            >
              <RotateCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
              <span>{isLoading ? 'Retrieving Climate...' : 'Refresh Environmental Analysis'}</span>
            </button>
          </div>
        </div>

        {errorMsg && (
          <div className="mt-4 p-3 bg-rose-50 border border-rose-200 rounded-lg flex items-start space-x-2 text-rose-800 text-xs">
            <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
            <span>{errorMsg}</span>
          </div>
        )}
      </div>

      {/* 2. Interactive Controls Grid: Map, Search & Compass Dial */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (8 cols): Map and Search */}
        <div className="lg:col-span-8 bg-white p-5 rounded-xl border border-charcoal-200 shadow-2xs space-y-4">
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
            <div className="relative flex-1">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-charcoal-400">
                <Search className="w-4 h-4" />
              </div>
              <input
                type="text"
                placeholder="Search address, landmark, city, or coordinate (e.g. Mumbai, Berlin, 12.97, 77.59)..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onFocus={() => {
                  if (searchResults.length > 0) setShowSearchResults(true);
                }}
                className="w-full pl-9 pr-8 py-2 text-xs bg-stone-50 border border-charcoal-200 rounded-lg text-charcoal-900 focus:outline-none focus:ring-2 focus:ring-emerald-600 focus:bg-white transition-all"
              />
              {isSearching && (
                <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
                  <div className="w-3.5 h-3.5 border-2 border-emerald-600 border-t-transparent rounded-full animate-spin"></div>
                </div>
              )}

              {/* Autocomplete Dropdown */}
              {showSearchResults && searchResults.length > 0 && (
                <div className="absolute z-50 left-0 right-0 mt-1 bg-white border border-charcoal-200 rounded-lg shadow-lg max-h-60 overflow-y-auto divide-y divide-stone-100">
                  {searchResults.map((item, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => handleSelectSearchResult(item)}
                      className="w-full text-left px-3 py-2 text-xs hover:bg-emerald-50 text-charcoal-800 transition-colors flex items-center justify-between"
                    >
                      <div className="truncate pr-2">
                        <span className="font-semibold">{item.city || item.display_name.split(',')[0]}</span>
                        <span className="text-charcoal-500 text-[11px] block truncate">{item.display_name}</span>
                      </div>
                      <span className="text-[10px] font-mono text-charcoal-400 shrink-0">
                        {item.latitude.toFixed(2)}°, {item.longitude.toFixed(2)}°
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Quick Presets Dropdown / Buttons */}
            <div className="flex items-center space-x-1.5 overflow-x-auto pb-1 sm:pb-0 scrollbar-none">
              <span className="text-[11px] font-semibold text-charcoal-500 whitespace-nowrap">Presets:</span>
              {presets.slice(0, 4).map((preset) => (
                <button
                  key={preset.city}
                  type="button"
                  onClick={() => handleSelectPreset(preset)}
                  className={`text-[11px] px-2.5 py-1 rounded-md border font-medium whitespace-nowrap transition-colors ${
                    Math.abs(lat - preset.latitude) < 0.1 && Math.abs(lon - preset.longitude) < 0.1
                      ? 'bg-emerald-800 text-white border-emerald-800'
                      : 'bg-stone-50 hover:bg-stone-100 text-charcoal-700 border-stone-200'
                  }`}
                >
                  {preset.city}
                </button>
              ))}
            </div>
          </div>

          {/* Interactive Leaflet Map Viewport */}
          <div className="relative rounded-xl overflow-hidden border border-charcoal-200 shadow-inner h-80 w-full bg-stone-100">
            <div ref={mapContainerRef} className="w-full h-full z-10" />

            {/* Floating Quick Action Overlay */}
            <div className="absolute top-3 right-3 z-20 bg-white/95 backdrop-blur-xs px-2.5 py-1.5 rounded-lg border border-charcoal-200 shadow-sm text-[11px] text-charcoal-700 flex items-center space-x-1.5 pointer-events-none">
              <Info className="w-3.5 h-3.5 text-emerald-700" />
              <span>Click or drag pin to evaluate any coordinate globally</span>
            </div>
          </div>

          {/* Manual Coordinate Override Inputs */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1 text-xs">
            <div>
              <label className="block text-charcoal-500 font-medium mb-1">Latitude (°N)</label>
              <input
                type="number"
                step="0.0001"
                min="-90"
                max="90"
                value={lat}
                onChange={(e) => setLat(parseFloat(e.target.value) || 0)}
                className="w-full px-2.5 py-1.5 font-mono bg-stone-50 border border-charcoal-200 rounded-lg text-charcoal-800 focus:outline-none focus:ring-1 focus:ring-emerald-600"
              />
            </div>
            <div>
              <label className="block text-charcoal-500 font-medium mb-1">Longitude (°E)</label>
              <input
                type="number"
                step="0.0001"
                min="-180"
                max="180"
                value={lon}
                onChange={(e) => setLon(parseFloat(e.target.value) || 0)}
                className="w-full px-2.5 py-1.5 font-mono bg-stone-50 border border-charcoal-200 rounded-lg text-charcoal-800 focus:outline-none focus:ring-1 focus:ring-emerald-600"
              />
            </div>
            <div>
              <label className="block text-charcoal-500 font-medium mb-1">Elevation</label>
              <div className="px-2.5 py-1.5 font-mono bg-stone-100 border border-stone-200 rounded-lg text-charcoal-700 flex items-center justify-between">
                <span>{analysis?.climate.elevation_m ?? '--'} m MSL</span>
                <Mountain className="w-3.5 h-3.5 text-stone-500" />
              </div>
            </div>
          </div>
        </div>

        {/* Right Column (4 cols): Building Azimuth & Compass Orientation Dial */}
        <div className="lg:col-span-4 bg-white p-5 rounded-xl border border-charcoal-200 shadow-2xs flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-2">
                <Compass className="w-4 h-4 text-emerald-800" />
                <h3 className="text-xs font-bold uppercase tracking-wider text-charcoal-800">
                  Building Orientation
                </h3>
              </div>
              <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200">
                {azimuthDeg}° ({getCardinalFromAzimuth(azimuthDeg)})
              </span>
            </div>
            <p className="text-[11px] text-charcoal-500 leading-relaxed mb-4">
              Rotate the main facade axis to optimize passive solar heat absorption, daylight ingress, and prevailing wind cross-ventilation.
            </p>

            {/* Compass Visualization Dial SVG */}
            <div className="relative w-48 h-48 mx-auto my-2 flex items-center justify-center">
              <svg className="w-full h-full" viewBox="0 0 200 200">
                {/* Dial Outer Ring */}
                <circle cx="100" cy="100" r="90" fill="#fcfcfc" stroke="#e2e8f0" strokeWidth="2.5" />
                <circle cx="100" cy="100" r="75" fill="none" stroke="#f1f5f9" strokeWidth="1" strokeDasharray="3 3" />

                {/* Sun Path Arc (South facing in Northern Hemisphere, North in Southern Hemisphere) */}
                <path
                  d={lat >= 0 ? "M 35 100 A 65 65 0 0 0 165 100" : "M 35 100 A 65 65 0 0 1 165 100"}
                  fill="none"
                  stroke="#fbbf24"
                  strokeWidth="2.5"
                  strokeDasharray="4 2"
                />
                {/* Sun Icon on Sun Path */}
                <circle cx={lat >= 0 ? 100 : 100} cy={lat >= 0 ? 165 : 35} r="6" fill="#f59e0b" />

                {/* Wind Vector Arrow (Incoming prevailing wind direction) */}
                {analysis?.climate && (
                  <g
                    transform={`rotate(${analysis.climate.dominant_wind_direction_deg}, 100, 100)`}
                    opacity="0.85"
                  >
                    <line x1="100" y1="12" x2="100" y2="45" stroke="#0284c7" strokeWidth="3" markerEnd="url(#arrow)" />
                    <polygon points="100,50 96,40 104,40" fill="#0284c7" />
                  </g>
                )}

                {/* Cardinal Tick Marks */}
                <text x="100" y="24" textAnchor="middle" fontSize="11" fontWeight="bold" fill="#0f172a">N</text>
                <text x="182" y="104" textAnchor="middle" fontSize="11" fontWeight="bold" fill="#64748b">E</text>
                <text x="100" y="186" textAnchor="middle" fontSize="11" fontWeight="bold" fill="#0f172a">S</text>
                <text x="18" y="104" textAnchor="middle" fontSize="11" fontWeight="bold" fill="#64748b">W</text>

                {/* Rotatable Building Representation */}
                <g transform={`rotate(${azimuthDeg}, 100, 100)`}>
                  {/* Building Long-Axis Box */}
                  <rect
                    x="75"
                    y="50"
                    width="50"
                    height="100"
                    rx="4"
                    fill="#10b981"
                    fillOpacity="0.25"
                    stroke="#047857"
                    strokeWidth="2"
                  />
                  {/* Front Facade Indicator (North edge of rotated shape) */}
                  <line x1="75" y1="50" x2="125" y2="50" stroke="#047857" strokeWidth="4" />
                  {/* Direction pointer needle */}
                  <polygon points="100,38 95,48 105,48" fill="#047857" />
                  <circle cx="100" cy="100" r="3" fill="#0f172a" />
                </g>
              </svg>

              {/* Legend Badges */}
              <div className="absolute bottom-0 text-[10px] text-charcoal-500 font-mono flex items-center space-x-2">
                <span className="flex items-center space-x-1">
                  <span className="w-2 h-2 rounded-full bg-amber-400"></span>
                  <span>Sun Path</span>
                </span>
                <span className="flex items-center space-x-1">
                  <span className="w-2 h-2 rounded-full bg-sky-500"></span>
                  <span>Wind ({analysis?.climate.dominant_wind_cardinal || 'W'})</span>
                </span>
              </div>
            </div>

            {/* Azimuth Range Slider */}
            <div className="space-y-1.5 mt-3">
              <div className="flex justify-between text-[11px] text-charcoal-600 font-medium">
                <span>0° (North)</span>
                <span>180° (South)</span>
                <span>360°</span>
              </div>
              <input
                type="range"
                min="0"
                max="359"
                value={azimuthDeg}
                onChange={(e) => setAzimuthDeg(parseInt(e.target.value, 10))}
                className="w-full accent-emerald-700 cursor-pointer"
              />
            </div>

            {/* Quick Cardinal Alignment Buttons */}
            <div className="grid grid-cols-4 gap-1.5 mt-3">
              {[
                { label: 'North', deg: 0 },
                { label: 'East', deg: 90 },
                { label: 'South', deg: 180 },
                { label: 'West', deg: 270 },
              ].map((btn) => (
                <button
                  key={btn.label}
                  type="button"
                  onClick={() => setAzimuthDeg(btn.deg)}
                  className={`text-[10px] py-1 rounded font-semibold transition-colors border ${
                    azimuthDeg === btn.deg
                      ? 'bg-charcoal-900 text-white border-charcoal-900'
                      : 'bg-stone-50 hover:bg-stone-100 text-charcoal-700 border-charcoal-200'
                  }`}
                >
                  {btn.label}
                </button>
              ))}
            </div>
          </div>

          {/* Orientation Impact Quick Status */}
          <div className="p-3 bg-stone-50 rounded-lg border border-charcoal-200 text-xs space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-charcoal-600 font-medium">Solar Exposure:</span>
              <span className="font-semibold text-charcoal-900">
                {analysis?.evaluation.solar_exposure_status || 'Calculating...'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-charcoal-600 font-medium">Ventilation Flow:</span>
              <span className="font-semibold text-charcoal-900">
                {analysis?.evaluation.wind_cross_ventilation_status || 'Calculating...'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 3. Climate & Site Indicators Metric Strip */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {/* Metric 1: Köppen Climate Classification */}
        <div className="bg-white p-3.5 rounded-xl border border-charcoal-200 shadow-2xs space-y-1">
          <div className="flex items-center space-x-1.5 text-charcoal-500 text-xs">
            <Flame className="w-3.5 h-3.5 text-amber-500" />
            <span className="font-medium">Climate Zone</span>
          </div>
          <div className="text-sm font-bold text-charcoal-900 truncate" title={analysis?.climate.climate_zone}>
            {analysis?.climate.climate_zone ? analysis.climate.climate_zone.split(' - ')[0] : '--'}
          </div>
          <p className="text-[10px] text-charcoal-500 line-clamp-1" title={analysis?.climate.climate_zone}>
            {analysis?.climate.climate_zone ? analysis.climate.climate_zone.split(' - ')[1] || 'Standard' : 'Loading...'}
          </p>
        </div>

        {/* Metric 2: Temperature Regime */}
        <div className="bg-white p-3.5 rounded-xl border border-charcoal-200 shadow-2xs space-y-1">
          <div className="flex items-center space-x-1.5 text-charcoal-500 text-xs">
            <Sun className="w-3.5 h-3.5 text-amber-600" />
            <span className="font-medium">Temperature</span>
          </div>
          <div className="text-sm font-bold text-charcoal-900">
            {analysis?.climate.mean_temp_c ?? '--'}°C
          </div>
          <p className="text-[10px] text-charcoal-500">
            Range: <span className="font-mono text-emerald-800 font-medium">{analysis?.climate.min_temp_c ?? '--'}°C</span> to{' '}
            <span className="font-mono text-rose-800 font-medium">{analysis?.climate.max_temp_c ?? '--'}°C</span>
          </p>
        </div>

        {/* Metric 3: Solar Insolation (GHI) */}
        <div className="bg-white p-3.5 rounded-xl border border-charcoal-200 shadow-2xs space-y-1">
          <div className="flex items-center space-x-1.5 text-charcoal-500 text-xs">
            <Zap className="w-3.5 h-3.5 text-amber-500" />
            <span className="font-medium">Solar Insolation</span>
          </div>
          <div className="text-sm font-bold text-charcoal-900">
            {analysis?.climate.solar_radiation_kwh_m2_day ?? '--'} <span className="text-[11px] font-normal text-charcoal-500">kWh/m²/d</span>
          </div>
          <p className="text-[10px] text-charcoal-500">
            Peak: {analysis?.climate.peak_solar_radiation_mj_m2 ?? '--'} MJ/m²
          </p>
        </div>

        {/* Metric 4: Dominant Wind Pattern */}
        <div className="bg-white p-3.5 rounded-xl border border-charcoal-200 shadow-2xs space-y-1">
          <div className="flex items-center space-x-1.5 text-charcoal-500 text-xs">
            <Wind className="w-3.5 h-3.5 text-sky-600" />
            <span className="font-medium">Wind Pattern</span>
          </div>
          <div className="text-sm font-bold text-charcoal-900">
            {analysis?.climate.dominant_wind_speed_kmh ?? '--'} <span className="text-[11px] font-normal text-charcoal-500">km/h</span>
          </div>
          <p className="text-[10px] text-charcoal-500">
            Prevailing: <span className="font-mono font-bold text-sky-800">{analysis?.climate.dominant_wind_cardinal || '--'}</span> ({analysis?.climate.dominant_wind_direction_deg ?? '--'}°)
          </p>
        </div>

        {/* Metric 5: Annual Rainfall */}
        <div className="bg-white p-3.5 rounded-xl border border-charcoal-200 shadow-2xs space-y-1">
          <div className="flex items-center space-x-1.5 text-charcoal-500 text-xs">
            <CloudRain className="w-3.5 h-3.5 text-blue-600" />
            <span className="font-medium">Annual Rainfall</span>
          </div>
          <div className="text-sm font-bold text-charcoal-900">
            {analysis?.climate.annual_rainfall_mm ?? '--'} <span className="text-[11px] font-normal text-charcoal-500">mm/yr</span>
          </div>
          <p className="text-[10px] text-charcoal-500">
            RH: {analysis?.climate.relative_humidity_pct ?? '--'}% average
          </p>
        </div>

        {/* Metric 6: Urban & Site Context */}
        <div className="bg-white p-3.5 rounded-xl border border-charcoal-200 shadow-2xs space-y-1">
          <div className="flex items-center space-x-1.5 text-charcoal-500 text-xs">
            <Building className="w-3.5 h-3.5 text-stone-600" />
            <span className="font-medium">Site Context</span>
          </div>
          <div className="text-sm font-bold text-charcoal-900 truncate">
            {analysis?.site_context.urban_density || '--'}
          </div>
          <p className="text-[10px] text-charcoal-500">
            Veg: {analysis?.site_context.nearby_vegetation_pct ?? '--'}% | Slope: {analysis?.site_context.terrain_slope_pct ?? 0}%
          </p>
        </div>
      </div>

      {/* 4. Environmental Suitability Evaluation Panel */}
      <div className="bg-white p-6 rounded-xl border border-charcoal-200 shadow-2xs space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-charcoal-100 gap-3">
          <div>
            <div className="flex items-center space-x-2">
              <Gauge className="w-5 h-5 text-emerald-800" />
              <h3 className="text-sm font-bold text-charcoal-900">
                Design & Environmental Suitability Evaluation
              </h3>
            </div>
            <p className="text-xs text-charcoal-500 mt-0.5">
              Multi-criteria assessment matching building envelope parameters to local microclimate patterns.
            </p>
          </div>

          {/* Overall Score Badge */}
          <div className="flex items-center space-x-3 bg-stone-50 px-4 py-2 rounded-xl border border-charcoal-200 shrink-0">
            <div className="text-right">
              <span className="text-[10px] uppercase font-bold tracking-wider text-charcoal-500 block">
                Overall Suitability
              </span>
              <span className="text-xs font-bold text-charcoal-800">
                {analysis?.evaluation.suitability_rating || 'Evaluating'}
              </span>
            </div>
            <div
              className={`text-xl font-mono font-extrabold px-3 py-1 rounded-lg border ${
                analysis?.evaluation ? getScoreBadgeColor(analysis.evaluation.overall_suitability_score) : 'bg-stone-100 text-charcoal-500'
              }`}
            >
              {analysis?.evaluation ? `${analysis.evaluation.overall_suitability_score}%` : '--'}
            </div>
          </div>
        </div>

        {/* Sub-Scores & Engineering Feasibility Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Solar Orientation */}
          <div className="p-4 rounded-xl border border-charcoal-200 bg-stone-50/50 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-charcoal-800 flex items-center space-x-1.5">
                <Sun className="w-4 h-4 text-amber-500" />
                <span>Solar Exposure Alignment</span>
              </span>
              <span className="text-xs font-mono font-bold text-charcoal-900">
                {analysis?.evaluation.solar_orientation_score ?? '--'}%
              </span>
            </div>
            <div className="w-full bg-stone-200 h-2 rounded-full overflow-hidden">
              <div
                className="bg-amber-500 h-full rounded-full transition-all duration-500"
                style={{ width: `${analysis?.evaluation.solar_orientation_score || 0}%` }}
              />
            </div>
            <p className="text-[11px] text-charcoal-600">
              Status: <span className="font-semibold text-charcoal-800">{analysis?.evaluation.solar_exposure_status || '--'}</span>
            </p>
          </div>

          {/* Daylight Potential */}
          <div className="p-4 rounded-xl border border-charcoal-200 bg-stone-50/50 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-charcoal-800 flex items-center space-x-1.5">
                <Eye className="w-4 h-4 text-emerald-600" />
                <span>Daylight Autonomy Potential</span>
              </span>
              <span className="text-xs font-mono font-bold text-charcoal-900">
                {analysis?.evaluation.daylight_potential_score ?? '--'}%
              </span>
            </div>
            <div className="w-full bg-stone-200 h-2 rounded-full overflow-hidden">
              <div
                className="bg-emerald-600 h-full rounded-full transition-all duration-500"
                style={{ width: `${analysis?.evaluation.daylight_potential_score || 0}%` }}
              />
            </div>
            <p className="text-[11px] text-charcoal-600">
              Window to wall ratio & orientation allows high natural daylight penetration without severe glare.
            </p>
          </div>

          {/* Natural Cross-Ventilation */}
          <div className="p-4 rounded-xl border border-charcoal-200 bg-stone-50/50 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-charcoal-800 flex items-center space-x-1.5">
                <Wind className="w-4 h-4 text-sky-600" />
                <span>Cross-Ventilation Potential</span>
              </span>
              <span className="text-xs font-mono font-bold text-charcoal-900">
                {analysis?.evaluation.natural_ventilation_score ?? '--'}%
              </span>
            </div>
            <div className="w-full bg-stone-200 h-2 rounded-full overflow-hidden">
              <div
                className="bg-sky-600 h-full rounded-full transition-all duration-500"
                style={{ width: `${analysis?.evaluation.natural_ventilation_score || 0}%` }}
              />
            </div>
            <p className="text-[11px] text-charcoal-600">
              Alignment: <span className="font-semibold text-charcoal-800">{analysis?.evaluation.wind_cross_ventilation_status || '--'}</span>
            </p>
          </div>

          {/* Solar Rooftop PV Generation */}
          <div className="p-4 rounded-xl border border-charcoal-200 bg-stone-50/50 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-charcoal-800 flex items-center space-x-1.5">
                <Zap className="w-4 h-4 text-amber-500" />
                <span>Rooftop Solar PV Potential</span>
              </span>
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-amber-100 text-amber-800 border border-amber-200">
                {analysis?.evaluation.solar_pv_feasibility || 'Feasible'}
              </span>
            </div>
            <div className="text-lg font-mono font-bold text-charcoal-900">
              {analysis?.evaluation.annual_solar_pv_kwh?.toLocaleString() ?? '--'}{' '}
              <span className="text-xs font-normal text-charcoal-500">kWh / year</span>
            </div>
            <p className="text-[11px] text-charcoal-600">
              Estimated rooftop yield accounting for local GHI, temperature coefficient, and 70% usable roof plane.
            </p>
          </div>

          {/* Rainwater Harvesting Capacity */}
          <div className="p-4 rounded-xl border border-charcoal-200 bg-stone-50/50 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-charcoal-800 flex items-center space-x-1.5">
                <Droplets className="w-4 h-4 text-blue-600" />
                <span>Rainwater Harvesting Yield</span>
              </span>
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-blue-100 text-blue-800 border border-blue-200">
                {analysis?.evaluation.rainwater_harvesting_feasibility || 'Moderate'}
              </span>
            </div>
            <div className="text-lg font-mono font-bold text-charcoal-900">
              {analysis?.evaluation.annual_rainwater_harvest_liters?.toLocaleString() ?? '--'}{' '}
              <span className="text-xs font-normal text-charcoal-500">Liters / year</span>
            </div>
            <p className="text-[11px] text-charcoal-600">
              Calculated using roof catchment area × annual rainfall with standard 0.85 runoff coefficient.
            </p>
          </div>

          {/* Passive Shading & Microclimate */}
          <div className="p-4 rounded-xl border border-charcoal-200 bg-stone-50/50 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-charcoal-800 flex items-center space-x-1.5">
                <Trees className="w-4 h-4 text-emerald-700" />
                <span>Passive Shading Strategy</span>
              </span>
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 border border-emerald-200">
                Active
              </span>
            </div>
            <p className="text-xs font-semibold text-charcoal-800">
              {analysis?.evaluation.passive_shading_requirement || 'Standard reveals adequate'}
            </p>
            <p className="text-[11px] text-charcoal-600">
              Opportunity: {analysis?.evaluation.green_space_opportunity || 'Vegetation integration recommended.'}
            </p>
          </div>
        </div>
      </div>

      {/* 5. Evidence-Based Recommendations */}
      <div className="bg-white p-6 rounded-xl border border-charcoal-200 shadow-2xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h3 className="text-sm font-bold text-charcoal-900 flex items-center space-x-2">
              <span>Site-Specific Architectural Recommendations</span>
              <span className="text-xs px-2 py-0.5 rounded-full font-bold bg-charcoal-100 text-charcoal-700">
                {filteredRecommendations.length}
              </span>
            </h3>
            <p className="text-xs text-charcoal-500 mt-0.5">
              Prioritized structural, orientation, and envelope modifications backed by empirical climate indicators.
            </p>
          </div>

          {/* Category Filter Pills */}
          <div className="flex flex-wrap items-center gap-1.5 text-xs">
            {[
              { id: 'all', label: 'All' },
              { id: 'orientation', label: 'Orientation' },
              { id: 'solar_pv', label: 'Solar PV' },
              { id: 'natural_ventilation', label: 'Ventilation' },
              { id: 'rainwater_harvesting', label: 'Rainwater' },
              { id: 'shading', label: 'Shading' },
            ].map((cat) => (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat.id)}
                className={`px-2.5 py-1 rounded-lg font-medium transition-colors ${
                  selectedCategory === cat.id
                    ? 'bg-charcoal-900 text-white'
                    : 'bg-stone-100 hover:bg-stone-200 text-charcoal-700'
                }`}
              >
                {cat.label}
              </button>
            ))}
          </div>
        </div>

        {/* Recommendations List */}
        <div className="space-y-3">
          {filteredRecommendations.length === 0 ? (
            <div className="p-8 text-center text-charcoal-500 text-xs border border-dashed border-charcoal-200 rounded-xl">
              No recommendations found for the selected category.
            </div>
          ) : (
            filteredRecommendations.map((rec: EnvironmentalRecommendation) => {
              const isExpanded = expandedRecId === rec.id;
              return (
                <div
                  key={rec.id}
                  className="p-4 rounded-xl border border-charcoal-200 hover:border-emerald-300 transition-all bg-white space-y-3 shadow-2xs"
                >
                  <div
                    onClick={() => setExpandedRecId(isExpanded ? null : rec.id)}
                    className="flex items-start justify-between cursor-pointer gap-3"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2">
                        <span
                          className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded border ${getPriorityBadgeColor(
                            rec.priority
                          )}`}
                        >
                          {rec.priority} Priority
                        </span>
                        <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-stone-100 text-charcoal-600 border border-stone-200">
                          {rec.category.replace('_', ' ')}
                        </span>
                        <h4 className="text-xs font-bold text-charcoal-900">{rec.title}</h4>
                      </div>
                      <p className="text-xs text-charcoal-700 leading-relaxed">{rec.reason}</p>
                    </div>

                    <button
                      type="button"
                      className="p-1 text-charcoal-400 hover:text-charcoal-700 rounded transition-colors shrink-0"
                    >
                      {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                  </div>

                  {/* Expanded Engineering Breakdown */}
                  {isExpanded && (
                    <div className="pt-3 border-t border-charcoal-100 grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                      <div className="p-3 bg-stone-50 rounded-lg space-y-1 border border-charcoal-100">
                        <span className="text-[10px] uppercase font-bold text-charcoal-500 tracking-wider">
                          Environmental Evidence
                        </span>
                        <p className="text-charcoal-800 text-[11px] leading-relaxed">
                          {rec.environmental_evidence}
                        </p>
                      </div>

                      <div className="p-3 bg-emerald-50/50 rounded-lg space-y-1 border border-emerald-100">
                        <span className="text-[10px] uppercase font-bold text-emerald-800 tracking-wider">
                          Expected Benefit
                        </span>
                        <p className="text-charcoal-800 text-[11px] leading-relaxed">
                          {rec.expected_benefit}
                        </p>
                      </div>

                      <div className="p-3 bg-stone-50 rounded-lg space-y-1 border border-charcoal-100">
                        <span className="text-[10px] uppercase font-bold text-charcoal-500 tracking-wider">
                          Data Source & Methodology
                        </span>
                        <p className="text-charcoal-700 font-mono text-[11px]">
                          {rec.data_source}
                        </p>
                      </div>

                      <div className="p-3 bg-amber-50/50 rounded-lg space-y-1 border border-amber-200">
                        <span className="text-[10px] uppercase font-bold text-amber-800 tracking-wider flex items-center space-x-1">
                          <AlertTriangle className="w-3 h-3 text-amber-600" />
                          <span>Engineering Limitations</span>
                        </span>
                        <p className="text-charcoal-700 text-[11px] leading-relaxed">
                          {rec.limitations}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* 6. Mandatory Engineering & Legal Disclaimers Banner */}
      <div className="bg-amber-50/80 border border-amber-200 rounded-xl p-5 space-y-3">
        <div className="flex items-center space-x-2 text-amber-900">
          <ShieldAlert className="w-5 h-5 text-amber-700 shrink-0" />
          <h4 className="text-xs font-bold uppercase tracking-wider">
            Critical Engineering & Geospatial Limitations Notice
          </h4>
        </div>
        <p className="text-xs text-amber-950 leading-relaxed">
          InfraTwinAI integrates verified meteorological and topographical feeds (Open-Meteo ERA5 Reanalysis and OpenStreetMap) to provide indicative bioclimatic design assistance. However, macro-scale satellite and weather data cannot substitute for mandatory on-site physical engineering tests:
        </p>
        <ul className="text-xs text-amber-900 space-y-1.5 list-disc pl-5">
          {analysis?.disclaimers && analysis.disclaimers.length > 0 ? (
            analysis.disclaimers.map((disc, idx) => <li key={idx}>{disc}</li>)
          ) : (
            <>
              <li>
                <b>Geotechnical Ground Truth:</b> A satellite map cannot establish soil bearing capacity, liquefaction susceptibility, or subsurface water table levels. Certified borehole soil investigation remains mandatory.
              </li>
              <li>
                <b>Aerodynamic Effects:</b> Localized wind shear, canyon vortexes, and downdrafts caused by neighboring tall structures require boundary layer wind-tunnel testing or detailed CFD simulations.
              </li>
              <li>
                <b>Preliminary Energy & Water Yields:</b> Solar PV yields and rainwater harvesting volumes are indicative estimates based on regional insolation and precipitation baselines.
              </li>
            </>
          )}
        </ul>
      </div>
    </div>
  );
};