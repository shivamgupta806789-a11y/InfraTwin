import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { CityModel, CityBuildingSummary } from '../types/city';
import {
  Boxes,
  Building2,
  Search,
  Maximize2,
  RotateCw,
  Compass,
  ArrowRight,
  Zap,
  X,
} from 'lucide-react';

interface CityViewerProps {
  cityModel: CityModel | null;
  isLoading: boolean;
  onSelectBuildingForBim?: (buildingId: string) => void;
  className?: string;
}

const TYPOLOGY_COLORS: Record<string, number> = {
  Commercial: 0x38bdf8,   // Sky blue
  Residential: 0x10b981,  // Emerald green
  Transit: 0xf59e0b,      // Amber
  Civic: 0x8b5cf6,        // Purple
  'Mixed-Use': 0xec4899,  // Pink
};

export const CityViewer: React.FC<CityViewerProps> = ({
  cityModel,
  isLoading,
  onSelectBuildingForBim,
  className = '',
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const cityGroupRef = useRef<THREE.Group | null>(null);
  const animFrameIdRef = useRef<number | null>(null);
  const raycasterRef = useRef<THREE.Raycaster>(new THREE.Raycaster());
  const mouseRef = useRef<THREE.Vector2>(new THREE.Vector2());

  const [selectedDistrictId, setSelectedDistrictId] = useState<string | null>(null);
  const [selectedSiteId, setSelectedSiteId] = useState<string | null>(null);
  const [selectedBuilding, setSelectedBuilding] = useState<CityBuildingSummary | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedTypology, setSelectedTypology] = useState<string>('all');
  const [showInfrastructure, setShowInfrastructure] = useState<boolean>(true);
  const [isRotating, setIsRotating] = useState<boolean>(false);

  // Initialize Three.js scene
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf6f7f8);
    scene.fog = new THREE.FogExp2(0xf6f7f8, 0.0035);
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(
      45,
      container.clientWidth / (container.clientHeight || 1),
      0.5,
      2500
    );
    camera.position.set(160, 180, 240);
    camera.up.set(0, 1, 0);
    cameraRef.current = camera;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    rendererRef.current = renderer;

    while (container.firstChild) {
      container.removeChild(container.firstChild);
    }
    container.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.target.set(45, 0, 0);
    controls.maxPolarAngle = Math.PI / 2 - 0.05;
    controls.minDistance = 20;
    controls.maxDistance = 800;
    controlsRef.current = controls;

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.75);
    scene.add(ambientLight);

    const hemiLight = new THREE.HemisphereLight(0xffffff, 0x94a3b8, 0.45);
    hemiLight.position.set(0, 200, 0);
    scene.add(hemiLight);

    const sunLight = new THREE.DirectionalLight(0xffffff, 1.35);
    sunLight.position.set(220, 260, 160);
    sunLight.castShadow = true;
    sunLight.shadow.mapSize.width = 2048;
    sunLight.shadow.mapSize.height = 2048;
    sunLight.shadow.camera.left = -200;
    sunLight.shadow.camera.right = 200;
    sunLight.shadow.camera.top = 200;
    sunLight.shadow.camera.bottom = -200;
    sunLight.shadow.camera.far = 700;
    scene.add(sunLight);

    // Ground Plane & Grid
    const groundGeo = new THREE.PlaneGeometry(600, 600);
    const groundMat = new THREE.MeshStandardMaterial({
      color: 0xeeeeef,
      roughness: 0.95,
      metalness: 0.0,
      depthWrite: true,
    });
    const ground = new THREE.Mesh(groundGeo, groundMat);
    ground.rotation.x = -Math.PI / 2;
    ground.receiveShadow = true;
    scene.add(ground);

    const grid = new THREE.GridHelper(500, 50, 0xc4c7cc, 0xe2e5e9);
    grid.position.y = 0.02;
    scene.add(grid);

    // City Group container
    const cityGroup = new THREE.Group();
    cityGroup.name = 'cityGroup';
    scene.add(cityGroup);
    cityGroupRef.current = cityGroup;

    // Animation Loop
    const animate = () => {
      animFrameIdRef.current = requestAnimationFrame(animate);
      if (isRotating && cityGroupRef.current) {
        cityGroupRef.current.rotation.y += 0.0015;
      }
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    // Resize Observer
    const resizeObserver = new ResizeObserver(() => {
      if (!container || !rendererRef.current || !cameraRef.current) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      if (w > 0 && h > 0) {
        cameraRef.current.aspect = w / h;
        cameraRef.current.updateProjectionMatrix();
        rendererRef.current.setSize(w, h);
      }
    });
    resizeObserver.observe(container);

    // Click Raycasting
    const handleCanvasClick = (event: MouseEvent) => {
      if (!cameraRef.current || !cityGroupRef.current) return;
      const rect = renderer.domElement.getBoundingClientRect();
      mouseRef.current.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouseRef.current.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      raycasterRef.current.setFromCamera(mouseRef.current, cameraRef.current);
      const intersects = raycasterRef.current.intersectObjects(cityGroupRef.current.children, true);

      if (intersects.length > 0) {
        let hitObj: THREE.Object3D | null = intersects[0].object;
        while (hitObj && hitObj !== cityGroupRef.current) {
          if (hitObj.userData && hitObj.userData.building) {
            setSelectedBuilding(hitObj.userData.building);
            return;
          }
          hitObj = hitObj.parent;
        }
      }
    };
    renderer.domElement.addEventListener('click', handleCanvasClick);

    return () => {
      if (animFrameIdRef.current) cancelAnimationFrame(animFrameIdRef.current);
      resizeObserver.disconnect();
      renderer.domElement.removeEventListener('click', handleCanvasClick);
      renderer.dispose();
      while (scene.children.length > 0) {
        scene.remove(scene.children[0]);
      }
    };
  }, []);

  // Rebuild 3D City Geometry when cityModel, filter, or selection changes
  useEffect(() => {
    const cityGroup = cityGroupRef.current;
    if (!cityGroup || !cityModel) return;

    // Dispose old children
    while (cityGroup.children.length > 0) {
      const child = cityGroup.children[0] as THREE.Mesh;
      cityGroup.remove(child);
      if (child.geometry) child.geometry.dispose();
      if (child.material) {
        if (Array.isArray(child.material)) child.material.forEach((m) => m.dispose());
        else child.material.dispose();
      }
    }

    // 1. Build Buildings
    cityModel.districts.forEach((district) => {
      if (selectedDistrictId && district.district_id !== selectedDistrictId) return;

      district.sites.forEach((site) => {
        if (selectedSiteId && site.site_id !== selectedSiteId) return;

        // Draw Site Boundary outline
        if (site.boundary_polygon && site.boundary_polygon.length >= 3) {
          const siteShape = new THREE.Shape();
          site.boundary_polygon.forEach((pt, idx) => {
            if (idx === 0) siteShape.moveTo(pt[0], pt[1]);
            else siteShape.lineTo(pt[0], pt[1]);
          });
          siteShape.closePath();
          const siteGeo = new THREE.ShapeGeometry(siteShape);
          const siteMat = new THREE.MeshStandardMaterial({
            color: 0xe5e7eb,
            roughness: 0.9,
            metalness: 0.0,
            transparent: true,
            opacity: 0.6,
          });
          const siteMesh = new THREE.Mesh(siteGeo, siteMat);
          siteMesh.rotation.x = -Math.PI / 2;
          siteMesh.position.y = 0.03;
          siteMesh.receiveShadow = true;
          cityGroup.add(siteMesh);
        }

        // Draw Buildings
        site.buildings.forEach((bld) => {
          // Typology filter
          if (selectedTypology !== 'all' && bld.typology.toLowerCase() !== selectedTypology.toLowerCase()) {
            return;
          }

          // Search query filter
          if (searchQuery.trim()) {
            const q = searchQuery.toLowerCase();
            const match = bld.building_id.toLowerCase().includes(q) || bld.name.toLowerCase().includes(q);
            if (!match) return;
          }

          const isSelected = selectedBuilding?.building_id === bld.building_id;
          const baseColor = TYPOLOGY_COLORS[bld.typology] || 0x64748b;

          // Building Box Geometry
          const geo = new THREE.BoxGeometry(bld.width_m, bld.height_m, bld.length_m);
          const mat = new THREE.MeshStandardMaterial({
            color: isSelected ? 0x10b981 : baseColor,
            roughness: 0.55,
            metalness: 0.15,
            emissive: isSelected ? 0x059669 : 0x000000,
            emissiveIntensity: isSelected ? 0.6 : 0.0,
          });

          const mesh = new THREE.Mesh(geo, mat);
          // Center Y is half the building height above ground
          mesh.position.set(bld.center_x, bld.height_m / 2, bld.center_y);
          mesh.castShadow = true;
          mesh.receiveShadow = true;
          mesh.userData = { building: bld };
          cityGroup.add(mesh);

          // Building outline edges
          const edges = new THREE.EdgesGeometry(geo);
          const line = new THREE.LineSegments(
            edges,
            new THREE.LineBasicMaterial({
              color: isSelected ? 0xffffff : 0x1e293b,
              linewidth: 1,
            })
          );
          line.position.copy(mesh.position);
          cityGroup.add(line);

          // Storey floor slabs lines inside building for architectural realism
          for (let f = 1; f < bld.storeys_count; f++) {
            const floorY = (bld.height_m / bld.storeys_count) * f;
            const floorGeo = new THREE.PlaneGeometry(bld.width_m + 0.1, bld.length_m + 0.1);
            const floorMat = new THREE.MeshBasicMaterial({ color: 0x334155, wireframe: true });
            const floorMesh = new THREE.Mesh(floorGeo, floorMat);
            floorMesh.rotation.x = -Math.PI / 2;
            floorMesh.position.set(bld.center_x, floorY, bld.center_y);
            cityGroup.add(floorMesh);
          }
        });
      });
    });

    // 2. Build Infrastructure Networks (Roads, Power, Drainage)
    if (showInfrastructure && cityModel.infrastructure_networks) {
      cityModel.infrastructure_networks.forEach((net) => {
        net.line_segments.forEach((seg) => {
          if (seg.length < 2) return;
          const points = seg.map((pt) => new THREE.Vector3(pt[0], pt[2] || 0.06, pt[1]));
          const lineGeo = new THREE.BufferGeometry().setFromPoints(points);
          const lineMat = new THREE.LineBasicMaterial({
            color: new THREE.Color(net.color_hex),
            linewidth: net.network_type === 'Roads' ? 4 : 2,
          });
          const line = new THREE.Line(lineGeo, lineMat);
          cityGroup.add(line);
        });
      });
    }
  }, [cityModel, selectedDistrictId, selectedSiteId, selectedBuilding, selectedTypology, searchQuery, showInfrastructure]);

  const handleResetCamera = () => {
    if (!cameraRef.current || !controlsRef.current) return;
    cameraRef.current.position.set(160, 180, 240);
    controlsRef.current.target.set(45, 0, 0);
    controlsRef.current.update();
  };

  if (isLoading || !cityModel) {
    return (
      <div className={`bg-white rounded-2xl border border-charcoal-200 p-8 flex flex-col items-center justify-center space-y-3 min-h-[480px] ${className}`}>
        <div className="w-8 h-8 border-2 border-charcoal-200 border-t-charcoal-800 rounded-full animate-spin" />
        <p className="text-xs text-charcoal-600 font-medium">Loading 3D City Infrastructure District...</p>
      </div>
    );
  }

  return (
    <div className={`relative bg-stone-100 rounded-2xl overflow-hidden border border-charcoal-200 ${className}`}>
      {/* 3D Canvas Viewport */}
      <div ref={containerRef} className="w-full h-[580px] cursor-grab active:cursor-grabbing" />

      {/* Top Floating Controls Bar */}
      <div className="absolute top-4 left-4 right-4 z-10 flex flex-wrap items-center justify-between gap-3 pointer-events-none">
        {/* District & Site Hierarchy Selector */}
        <div className="flex items-center space-x-2 bg-white/95 backdrop-blur-md p-1.5 rounded-xl border border-charcoal-200 shadow-md pointer-events-auto text-xs">
          <span className="font-bold text-charcoal-800 flex items-center space-x-1 pl-1">
            <Boxes className="w-4 h-4 text-emerald-800" />
            <span>District:</span>
          </span>
          <select
            value={selectedDistrictId || ''}
            onChange={(e) => {
              setSelectedDistrictId(e.target.value || null);
              setSelectedSiteId(null);
            }}
            className="bg-stone-50 border border-charcoal-200 rounded-lg px-2.5 py-1 text-xs text-charcoal-900 font-medium focus:outline-none"
          >
            <option value="">All Districts ({cityModel?.districts.length || 0})</option>
            {cityModel?.districts.map((d) => (
              <option key={d.district_id} value={d.district_id}>
                {d.name} ({d.total_buildings_count} blds)
              </option>
            ))}
          </select>

          {/* Typology Filter */}
          <select
            value={selectedTypology}
            onChange={(e) => setSelectedTypology(e.target.value)}
            className="bg-stone-50 border border-charcoal-200 rounded-lg px-2.5 py-1 text-xs text-charcoal-900 font-medium focus:outline-none"
          >
            <option value="all">All Typologies</option>
            <option value="commercial">Commercial</option>
            <option value="residential">Residential</option>
            <option value="transit">Transit</option>
            <option value="civic">Civic</option>
            <option value="mixed-use">Mixed-Use</option>
          </select>
        </div>

        {/* Search Input & Action Buttons */}
        <div className="flex items-center space-x-2 pointer-events-auto">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-charcoal-400 absolute left-2.5 top-2.5" />
            <input
              type="text"
              placeholder="Search building ID / name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 pr-3 py-1 bg-white/95 backdrop-blur-md border border-charcoal-200 rounded-xl text-xs text-charcoal-800 placeholder:text-charcoal-400 focus:outline-none shadow-xs w-48 sm:w-56"
            />
          </div>

          <div className="flex items-center space-x-1 bg-white/95 backdrop-blur-md p-1 rounded-xl border border-charcoal-200 shadow-xs">
            <button
              onClick={() => setShowInfrastructure(!showInfrastructure)}
              title="Toggle Infrastructure Networks"
              className={`p-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1 transition-colors ${
                showInfrastructure ? 'bg-charcoal-900 text-white' : 'text-charcoal-600 hover:text-black'
              }`}
            >
              <Zap className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Infra</span>
            </button>

            <button
              onClick={() => setIsRotating(!isRotating)}
              title="Auto-rotate city view"
              className={`p-1.5 rounded-lg text-charcoal-600 hover:text-black ${isRotating ? 'bg-charcoal-200' : ''}`}
            >
              <RotateCw className="w-4 h-4" />
            </button>

            <button
              onClick={handleResetCamera}
              title="Reset camera framing"
              className="p-1.5 rounded-lg text-charcoal-600 hover:text-black"
            >
              <Maximize2 className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Selected Building Detail Drawer (Right side) */}
      {selectedBuilding && (
        <div className="absolute top-20 right-4 z-20 w-80 bg-white/95 backdrop-blur-md rounded-2xl border border-charcoal-200 p-5 shadow-xl space-y-4 animate-in slide-in-from-right-4 duration-200">
          <div className="flex items-start justify-between">
            <div>
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200">
                {selectedBuilding.typology.toUpperCase()}
              </span>
              <h3 className="text-sm font-bold text-charcoal-900 mt-1">
                {selectedBuilding.name}
              </h3>
              <p className="text-[11px] font-mono text-charcoal-500">
                ID: {selectedBuilding.building_id}
              </p>
            </div>
            <button
              onClick={() => setSelectedBuilding(null)}
              className="p-1 rounded-lg hover:bg-stone-100 text-charcoal-400 hover:text-charcoal-700"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="p-2.5 bg-stone-50 rounded-lg border border-charcoal-100">
              <span className="text-charcoal-500 text-[10px]">Gross Floor Area</span>
              <div className="font-bold font-mono text-charcoal-900 mt-0.5">
                {selectedBuilding.gross_floor_area_m2.toLocaleString()} m²
              </div>
            </div>
            <div className="p-2.5 bg-stone-50 rounded-lg border border-charcoal-100">
              <span className="text-charcoal-500 text-[10px]">Storeys / Height</span>
              <div className="font-bold font-mono text-charcoal-900 mt-0.5">
                {selectedBuilding.storeys_count} Fl ({selectedBuilding.height_m}m)
              </div>
            </div>
            <div className="p-2.5 bg-stone-50 rounded-lg border border-charcoal-100">
              <span className="text-charcoal-500 text-[10px]">Solar PV Potential</span>
              <div className="font-bold font-mono text-charcoal-900 mt-0.5">
                {selectedBuilding.solar_pv_capacity_kw} kWp
              </div>
            </div>
            <div className="p-2.5 bg-stone-50 rounded-lg border border-charcoal-100">
              <span className="text-charcoal-500 text-[10px]">Embodied Carbon</span>
              <div className="font-bold font-mono text-charcoal-900 mt-0.5">
                {selectedBuilding.embodied_carbon_kg_co2e_m2} kg/m²
              </div>
            </div>
          </div>

          {/* Detailed BIM Linkage Button */}
          {selectedBuilding.has_detailed_bim && selectedBuilding.bim_model_id && (
            <button
              onClick={() => onSelectBuildingForBim?.(selectedBuilding.bim_model_id!)}
              className="w-full bg-charcoal-900 hover:bg-black text-white font-semibold text-xs py-2.5 rounded-xl shadow-xs transition-all flex items-center justify-center space-x-1.5"
            >
              <Building2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>Inspect Detailed BIM Model</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      )}

      {/* Bottom Architectural Legend Bar */}
      <div className="absolute bottom-3 left-3 right-3 z-10 flex flex-wrap items-center justify-between gap-2 pointer-events-none text-[11px] text-charcoal-600 px-2">
        <div className="bg-white/90 backdrop-blur-xs px-3 py-1.5 rounded-xl border border-charcoal-200 pointer-events-auto flex items-center space-x-3">
          <span className="font-semibold text-charcoal-900">Typologies:</span>
          {Object.entries(TYPOLOGY_COLORS).map(([type, color]) => (
            <div key={type} className="flex items-center space-x-1">
              <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: `#${color.toString(16).padStart(6, '0')}` }} />
              <span>{type}</span>
            </div>
          ))}
        </div>

        <div className="bg-white/90 backdrop-blur-xs px-3 py-1.5 rounded-xl border border-charcoal-200 pointer-events-auto text-[10px] hidden sm:flex items-center space-x-2">
          <Compass className="w-3.5 h-3.5 text-blue-600" />
          <span>Click any building to view metrics or drill into detailed BIM geometry</span>
        </div>
      </div>
    </div>
  );
};
