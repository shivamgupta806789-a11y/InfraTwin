import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { BuildingParams, InterventionId } from '../types/building';
import { BuildingModelDetail, BuildingElement } from '../types/digital_twin';
import {
  RotateCw,
  Maximize2,
  Layers,
  X,
  Building2,
  Home,
  Footprints,
  SlidersHorizontal,
  Waves,
  ShieldAlert,
  Sun,
  CircleDot,
} from 'lucide-react';
import { GeotechnicalSiteProfile, BoreholeRecord, SoilStrataLayer } from '../types/geotechnical';
import { fetchGeotechnicalProfileApi } from '../lib/api';

export type ViewerMode = 'skeleton' | 'exterior' | 'interior';
export type VisualPreset = 'arch_white' | 'concrete' | 'warm_interior' | 'modern_commercial' | 'neutral_bim' | 'technical_inspection';

interface BuildingViewerProps {
  params: BuildingParams;
  showInterventions?: boolean;
  label?: string;
  isBaseline?: boolean;
  className?: string;
  // Digital Twin Extensions
  importedModel?: BuildingModelDetail | null;
  selectedElementId?: string | null;
  highlightedElementIds?: string[];
  highlightSeverity?: string | null;
  onSelectElement?: (element: BuildingElement | null) => void;
  onClearHighlight?: () => void;
  visibleTypes?: string[];
  selectedStoreyId?: string | null;
  initialViewerMode?: ViewerMode;
  viewerMode?: ViewerMode;
  onViewerModeChange?: (mode: ViewerMode) => void;
}

const ELEMENT_COLOR_MAP: Record<string, { color: number; transparent?: boolean; opacity?: number; roughness?: number; metalness?: number }> = {
  IfcWall: { color: 0xe2e5e9, roughness: 0.65 },
  IfcWallStandardCase: { color: 0xe2e5e9, roughness: 0.65 },
  IfcSlab: { color: 0x94a3b8, roughness: 0.8 },
  IfcColumn: { color: 0x64748b, roughness: 0.7 },
  IfcBeam: { color: 0x475569, roughness: 0.6 },
  IfcWindow: { color: 0x38bdf8, roughness: 0.1, transparent: true, opacity: 0.55 },
  IfcDoor: { color: 0xb45309, roughness: 0.5 },
  IfcStair: { color: 0xd97706, roughness: 0.7 },
  IfcRoof: { color: 0x334155, roughness: 0.8 },
  IfcFooting: { color: 0x52525b, roughness: 0.9 },
  IfcSpace: { color: 0xa7f3d0, roughness: 0.2, transparent: true, opacity: 0.25 },
  IfcBuildingElementProxy: { color: 0x0d9488, roughness: 0.5 },
};

function getMaterialPresetStyle(
  elementType: string,
  preset: VisualPreset,
  defaultColor: number,
  defaultRoughness: number = 0.6,
  defaultMetalness: number = 0.1
) {
  if (preset === 'arch_white') {
    if (elementType.includes('Window')) {
      return { color: 0xe0f2fe, roughness: 0.05, metalness: 0.1, transparent: true, opacity: 0.45 };
    }
    if (elementType.includes('Slab')) {
      return { color: 0xe4e4e7, roughness: 0.88, metalness: 0.02, transparent: false, opacity: 1.0 };
    }
    if (elementType.includes('Column') || elementType.includes('Beam')) {
      return { color: 0xd4d4d8, roughness: 0.82, metalness: 0.05, transparent: false, opacity: 1.0 };
    }
    if (elementType.includes('Roof')) {
      return { color: 0x71717a, roughness: 0.85, metalness: 0.05, transparent: false, opacity: 1.0 };
    }
    return { color: 0xfcfcfc, roughness: 0.85, metalness: 0.02, transparent: false, opacity: 1.0 };
  }

  if (preset === 'concrete') {
    if (elementType.includes('Window')) {
      return { color: 0x38bdf8, roughness: 0.08, metalness: 0.2, transparent: true, opacity: 0.55 };
    }
    if (elementType.includes('Slab')) {
      return { color: 0x6b7280, roughness: 0.95, metalness: 0.05, transparent: false, opacity: 1.0 };
    }
    if (elementType.includes('Column') || elementType.includes('Beam')) {
      return { color: 0x4b5563, roughness: 0.88, metalness: 0.1, transparent: false, opacity: 1.0 };
    }
    if (elementType.includes('Roof')) {
      return { color: 0x374151, roughness: 0.95, metalness: 0.05, transparent: false, opacity: 1.0 };
    }
    return { color: 0x9ca3af, roughness: 0.92, metalness: 0.08, transparent: false, opacity: 1.0 };
  }

  if (preset === 'warm_interior') {
    if (elementType.includes('Window')) {
      return { color: 0xbae6fd, roughness: 0.05, metalness: 0.05, transparent: true, opacity: 0.40 };
    }
    if (elementType.includes('Slab')) {
      return { color: 0x92400e, roughness: 0.45, metalness: 0.05, transparent: false, opacity: 1.0 };
    }
    if (elementType.includes('Column') || elementType.includes('Beam')) {
      return { color: 0x78350f, roughness: 0.50, metalness: 0.05, transparent: false, opacity: 1.0 };
    }
    if (elementType.includes('Roof')) {
      return { color: 0x44403c, roughness: 0.80, metalness: 0.05, transparent: false, opacity: 1.0 };
    }
    return { color: 0xf5f5f4, roughness: 0.70, metalness: 0.02, transparent: false, opacity: 1.0 };
  }

  if (preset === 'modern_commercial') {
    if (elementType.includes('Window')) {
      return { color: 0x0284c7, roughness: 0.03, metalness: 0.35, transparent: true, opacity: 0.60 };
    }
    if (elementType.includes('Slab')) {
      return { color: 0x94a3b8, roughness: 0.35, metalness: 0.15, transparent: false, opacity: 1.0 };
    }
    if (elementType.includes('Column') || elementType.includes('Beam')) {
      return { color: 0x1e293b, roughness: 0.30, metalness: 0.60, transparent: false, opacity: 1.0 };
    }
    if (elementType.includes('Roof')) {
      return { color: 0x0f172a, roughness: 0.50, metalness: 0.40, transparent: false, opacity: 1.0 };
    }
    return { color: 0xd1d5db, roughness: 0.40, metalness: 0.25, transparent: false, opacity: 1.0 };
  }

  return { color: defaultColor, roughness: defaultRoughness, metalness: defaultMetalness, transparent: false, opacity: 1.0 };
}

export const BuildingViewer: React.FC<BuildingViewerProps> = ({
  params,
  showInterventions = true,
  label,
  isBaseline = false,
  className = '',
  importedModel,
  selectedElementId,
  highlightedElementIds,
  highlightSeverity,
  onSelectElement,
  onClearHighlight,
  visibleTypes,
  selectedStoreyId,
  initialViewerMode = 'exterior',
  viewerMode: propViewerMode,
  onViewerModeChange,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const buildingGroupRef = useRef<THREE.Group | null>(null);
  const animFrameIdRef = useRef<number | null>(null);
  const raycasterRef = useRef<THREE.Raycaster>(new THREE.Raycaster());
  const mouseRef = useRef<THREE.Vector2>(new THREE.Vector2());

  // References for environment scaling and camera auto-framing
  const gridHelperRef = useRef<THREE.GridHelper | null>(null);
  const groundRef = useRef<THREE.Mesh | null>(null);
  const sunLightRef = useRef<THREE.DirectionalLight | null>(null);
  const lastFittedModelIdRef = useRef<string | null>(null);
  const lastModeRef = useRef<'parametric' | 'twin' | null>(null);

  const [isRotating, setIsRotating] = useState(false);
  const [wireframeMode, setWireframeMode] = useState(initialViewerMode === 'skeleton');
  const [viewerMode, setViewerMode] = useState<ViewerMode>(initialViewerMode);

  // Sync external viewerMode prop when provided
  useEffect(() => {
    if (propViewerMode && propViewerMode !== viewerMode) {
      handleSetViewerMode(propViewerMode);
    }
  }, [propViewerMode]);

  // Interior View Mode States
  const [interiorStoreyId, setInteriorStoreyId] = useState<string | null>(null);
  const [showCeiling, setShowCeiling] = useState<boolean>(false); // default: cutaway ceiling
  const [wallTransparency, setWallTransparency] = useState<'translucent' | 'cutaway' | 'solid' | 'hidden'>('translucent');
  const [hiddenCategories, setHiddenCategories] = useState<string[]>([]);
  const [selectedRoom, setSelectedRoom] = useState<BuildingElement | null>(null);
  const [isWalkthrough, setIsWalkthrough] = useState<boolean>(false);
  const [customRoomNote, setCustomRoomNote] = useState<string>('');
  const [savedNotes, setSavedNotes] = useState<Record<string, string>>({});

  // Visual Presets & Settings (Phase 3)
  const [visualPreset, setVisualPreset] = useState<VisualPreset>('arch_white');
  const [enableShadows, setEnableShadows] = useState<boolean>(true);
  const [showGrid, setShowGrid] = useState<boolean>(true);
  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);

  useEffect(() => {
    if (gridHelperRef.current) {
      gridHelperRef.current.visible = showGrid;
    }
  }, [showGrid]);

  // Subsurface Geotechnical States (Phase 4)
  const [showSubsurface, setShowSubsurface] = useState<boolean>(false);
  const [showBoreholes, setShowBoreholes] = useState<boolean>(false);
  const [showGroundwater, setShowGroundwater] = useState<boolean>(false);
  const [showFloodOverlay, setShowFloodOverlay] = useState<boolean>(false);
  const [geotechnicalProfile, setGeotechnicalProfile] = useState<GeotechnicalSiteProfile | null>(null);
  const [selectedBorehole, setSelectedBorehole] = useState<BoreholeRecord | null>(null);
  const subsurfaceGroupRef = useRef<THREE.Group | null>(null);

  // Load site geotechnical profile
  useEffect(() => {
    fetchGeotechnicalProfileApi(28.6139, 77.2090)
      .then((data) => setGeotechnicalProfile(data))
      .catch(() => null);
  }, []);

  // Active interventions to show (parametric mode)
  const activeInterventions: InterventionId[] = (showInterventions && !isBaseline)
    ? params.selected_interventions
    : [];

  const isDigitalTwinMode = Boolean(importedModel && importedModel.elements && importedModel.elements.length > 0);

  // Available Rooms (IfcSpace)
  const availableRooms: BuildingElement[] = (importedModel?.elements || []).filter(
    (e) => e.element_type === 'IfcSpace'
  );

  // Setup Three.js scene once on mount
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // 1. Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf6f7f8);
    scene.fog = new THREE.FogExp2(0xf6f7f8, 0.006);
    sceneRef.current = scene;

    // 2. Camera with explicit Y-up orientation
    const camera = new THREE.PerspectiveCamera(
      45,
      container.clientWidth / (container.clientHeight || 1),
      0.1,
      1000
    );
    camera.up.set(0, 1, 0);
    camera.position.set(28, 22, 32);
    cameraRef.current = camera;

    // 3. Renderer with antialiasing and shadow map
    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      powerPreference: 'high-performance',
      alpha: false,
    });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.05;
    container.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // 4. Orbit Controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.maxPolarAngle = Math.PI / 2 + 0.02; // Allow viewing slightly from below floor
    controlsRef.current = controls;

    // 5. Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.75);
    scene.add(ambientLight);

    const hemiLight = new THREE.HemisphereLight(0xffffff, 0xe2e8f0, 0.55);
    hemiLight.position.set(0, 60, 0);
    scene.add(hemiLight);

    const sunLight = new THREE.DirectionalLight(0xfffaed, 1.35);
    sunLight.position.set(45, 55, 35);
    sunLight.castShadow = true;
    sunLight.shadow.mapSize.width = 2048;
    sunLight.shadow.mapSize.height = 2048;
    sunLight.shadow.camera.near = 0.5;
    sunLight.shadow.camera.far = 300;
    sunLight.shadow.bias = -0.0005;
    scene.add(sunLight);
    sunLightRef.current = sunLight;

    // 6. Ground & Architectural Reference Grid
    const groundGeo = new THREE.PlaneGeometry(200, 200);
    const groundMat = new THREE.MeshStandardMaterial({
      color: 0xedeef0,
      roughness: 0.95,
      metalness: 0.0,
      depthWrite: true,
    });
    const ground = new THREE.Mesh(groundGeo, groundMat);
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.02;
    ground.receiveShadow = true;
    scene.add(ground);
    groundRef.current = ground;

    const grid = new THREE.GridHelper(120, 60, 0x94a3b8, 0xd8dee6);
    grid.position.y = 0.0;
    scene.add(grid);
    gridHelperRef.current = grid;

    // 7. Building Group Container
    const buildingGroup = new THREE.Group();
    buildingGroup.name = 'buildingGroup';
    scene.add(buildingGroup);
    buildingGroupRef.current = buildingGroup;

    // 8. Animation Loop
    const animate = () => {
      animFrameIdRef.current = requestAnimationFrame(animate);
      if (controlsRef.current) {
        controlsRef.current.update();
      }
      if (rendererRef.current && sceneRef.current && cameraRef.current) {
        rendererRef.current.render(sceneRef.current, cameraRef.current);
      }
    };
    animate();

    // 9. Resize Observer
    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        if (entry.target === container) {
          const width = container.clientWidth;
          const height = container.clientHeight;
          if (width > 0 && height > 0) {
            if (cameraRef.current) {
              cameraRef.current.aspect = width / height;
              cameraRef.current.updateProjectionMatrix();
            }
            if (rendererRef.current) {
              rendererRef.current.setSize(width, height);
            }
          }
        }
      }
    });
    resizeObserver.observe(container);

    // 10. Pointer click listener for Raycasting element and borehole selection
    const handleCanvasClick = (event: MouseEvent) => {
      if (!cameraRef.current) return;
      const rect = renderer.domElement.getBoundingClientRect();
      mouseRef.current.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouseRef.current.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      raycasterRef.current.setFromCamera(mouseRef.current, cameraRef.current);
      const allObjects: THREE.Object3D[] = [];
      if (buildingGroupRef.current) allObjects.push(...buildingGroupRef.current.children);
      if (subsurfaceGroupRef.current) allObjects.push(...subsurfaceGroupRef.current.children);

      const intersects = raycasterRef.current.intersectObjects(allObjects, true);

      if (intersects.length > 0) {
        let hitObj: THREE.Object3D | null = intersects[0].object;
        while (hitObj) {
          if (hitObj.userData && hitObj.userData.isBorehole && hitObj.userData.borehole) {
            setSelectedBorehole(hitObj.userData.borehole);
            return;
          }
          if (hitObj.userData && hitObj.userData.element) {
            const elem = hitObj.userData.element as BuildingElement;
            onSelectElement?.(elem);
            if (elem.element_type === 'IfcSpace') {
              setSelectedRoom(elem);
            }
            return;
          }
          hitObj = hitObj.parent;
        }
      }
      onSelectElement?.(null);
      setSelectedBorehole(null);
    };

    const domElement = renderer.domElement;
    domElement.addEventListener('click', handleCanvasClick);

    // Cleanup WebGL resources on unmount
    return () => {
      domElement.removeEventListener('click', handleCanvasClick);
      resizeObserver.disconnect();
      if (animFrameIdRef.current) {
        cancelAnimationFrame(animFrameIdRef.current);
      }
      if (controlsRef.current) {
        controlsRef.current.dispose();
      }
      if (rendererRef.current && rendererRef.current.domElement) {
        if (container.contains(rendererRef.current.domElement)) {
          container.removeChild(rendererRef.current.domElement);
        }
        rendererRef.current.dispose();
      }
      groundGeo.dispose();
      groundMat.dispose();
      sunLightRef.current = null;
      groundRef.current = null;
      gridHelperRef.current = null;
    };
  }, []);

  // Update auto-rotate state
  useEffect(() => {
    if (controlsRef.current) {
      controlsRef.current.autoRotate = isRotating;
    }
  }, [isRotating]);

  // Handle Viewer Mode Switch
  const handleSetViewerMode = (mode: ViewerMode) => {
    setViewerMode(mode);
    onViewerModeChange?.(mode);

    if (mode === 'skeleton') {
      setWireframeMode(true);
      setIsWalkthrough(false);
    } else if (mode === 'exterior') {
      setWireframeMode(false);
      setIsWalkthrough(false);
      fitCameraToModel(isDigitalTwinMode, true);
    } else if (mode === 'interior') {
      setWireframeMode(false);
      // Auto-frame interior dollhouse perspective
      transitionToInteriorView();
    }
  };

  // Camera transition to interior dollhouse cutaway
  const transitionToInteriorView = (storeyId?: string | null) => {
    const camera = cameraRef.current;
    const controls = controlsRef.current;
    if (!camera || !controls || !importedModel?.bounding_box) return;

    const b = importedModel.bounding_box;
    const modelWidth = Math.max(1, b.width);
    const modelDepth = Math.max(1, b.height);
    const modelHeight = Math.max(1, b.depth);

    let targetY = modelHeight * 0.35;
    if (storeyId) {
      const st = importedModel.storeys.find((s) => s.storey_id === storeyId);
      if (st && st.elevation_m != null) {
        targetY = Math.max(0, st.elevation_m - (b.min_z || 0) + 1.2);
      }
    }

    const dist = Math.max(modelWidth, modelDepth) * 1.15;
    controls.target.set(0, targetY, 0);
    // Position camera at a 55-degree high three-quarter angle for cutaway perspective
    camera.position.set(dist * 0.7, targetY + dist * 0.85, dist * 0.75);
    camera.updateProjectionMatrix();
    controls.update();
  };

  // Focus camera directly onto a specific room
  const focusOnRoom = (room: BuildingElement) => {
    const camera = cameraRef.current;
    const controls = controlsRef.current;
    if (!camera || !controls || !importedModel?.bounding_box) return;

    const b = importedModel.bounding_box;
    const rb = room.bounding_box || {
      center_x: b.center_x,
      center_y: b.center_y,
      center_z: b.min_z + 1.5,
      width: 6,
      height: 6,
      depth: 3,
    };

    const roomWorldX = rb.center_x - b.center_x;
    const roomWorldY = Math.max(0.5, rb.center_z - b.min_z);
    const roomWorldZ = -(rb.center_y - b.center_y);

    controls.target.set(roomWorldX, roomWorldY, roomWorldZ);
    const roomSpan = Math.max(rb.width, rb.height, rb.depth, 4);
    camera.position.set(
      roomWorldX + roomSpan * 0.8,
      roomWorldY + roomSpan * 0.9,
      roomWorldZ + roomSpan * 0.8
    );
    camera.updateProjectionMatrix();
    controls.update();
  };

  // Enter First-Person Walkthrough mode
  const enterRoomWalkthrough = (room?: BuildingElement | null) => {
    const camera = cameraRef.current;
    const controls = controlsRef.current;
    if (!camera || !controls || !importedModel?.bounding_box) return;

    const b = importedModel.bounding_box;
    const targetRoom = room || selectedRoom || availableRooms[0];

    let targetX = 0;
    let floorY = 0;
    let targetZ = 0;

    if (targetRoom && targetRoom.bounding_box) {
      const rb = targetRoom.bounding_box;
      targetX = rb.center_x - b.center_x;
      floorY = Math.max(0, (rb.min_z || 0) - b.min_z);
      targetZ = -(rb.center_y - b.center_y);
    } else if (interiorStoreyId) {
      const storey = importedModel.storeys.find((s) => s.storey_id === interiorStoreyId);
      floorY = Math.max(0, (storey?.elevation_m || 0) - (b.min_z || 0));
    }

    const eyeLevelY = floorY + 1.65; // Human eye level (1.65m)
    camera.position.set(targetX, eyeLevelY, targetZ);
    controls.target.set(targetX + 1.0, eyeLevelY, targetZ);
    controls.minDistance = 0.05;
    controls.maxDistance = 50;
    controls.update();

    setIsWalkthrough(true);
  };

  // Safely and completely exit First-Person Walkthrough mode
  const exitWalkthrough = () => {
    // 1. Release pointer lock if active in document
    if (document.pointerLockElement) {
      document.exitPointerLock();
    }

    // 2. Clear walkthrough mode state
    setIsWalkthrough(false);

    // 3. Restore OrbitControls settings and distances
    const controls = controlsRef.current;
    const camera = cameraRef.current;
    if (controls && camera) {
      controls.enabled = true;
      controls.enableRotate = true;
      controls.enableZoom = true;
      controls.enablePan = true;

      const isTwin = Boolean(importedModel && importedModel.elements && importedModel.elements.length > 0);
      fitCameraToModel(isTwin, true);
      controls.update();
    }
  };

  // Walk step execution for keyboard and on-screen D-pad
  const walkStep = (direction: 'forward' | 'backward' | 'left' | 'right', distance = 0.6) => {
    const camera = cameraRef.current;
    const controls = controlsRef.current;
    if (!camera || !controls) return;

    const forward = new THREE.Vector3();
    camera.getWorldDirection(forward);
    forward.y = 0; // lock strictly to horizontal plane
    forward.normalize();

    // Standard Three.js horizontal strafe vectors (Right = forward x UP, Left = UP x forward)
    // For forward = (fx, 0, fz), Left = (fz, 0, -fx), Right = (-fz, 0, fx)
    const left = new THREE.Vector3(forward.z, 0, -forward.x);
    const right = new THREE.Vector3(-forward.z, 0, forward.x);

    const prevY = camera.position.y;
    const targetPrevY = controls.target.y;

    if (direction === 'forward') {
      camera.position.addScaledVector(forward, distance);
      controls.target.addScaledVector(forward, distance);
    } else if (direction === 'backward') {
      camera.position.addScaledVector(forward, -distance);
      controls.target.addScaledVector(forward, -distance);
    } else if (direction === 'left') {
      camera.position.addScaledVector(left, distance);
      controls.target.addScaledVector(left, distance);
    } else if (direction === 'right') {
      camera.position.addScaledVector(right, distance);
      controls.target.addScaledVector(right, distance);
    }

    // Lock vertical height strictly to prevent accidental floor or ceiling drift
    camera.position.y = prevY;
    controls.target.y = targetPrevY;
    controls.update();
  };

  // Keyboard controls listener during First-Person Walkthrough
  useEffect(() => {
    if (!isWalkthrough) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      // 1. ESCAPE key MUST reliably exit walkthrough mode
      if (e.key === 'Escape' || e.code === 'Escape') {
        e.preventDefault();
        exitWalkthrough();
        return;
      }

      // Ignore if user is typing in an input, textarea, select, or editable element
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement ||
        e.target instanceof HTMLSelectElement ||
        (e.target as HTMLElement)?.isContentEditable
      ) {
        return;
      }

      if (e.code === 'KeyW' || e.key === 'ArrowUp' || e.key === 'w' || e.key === 'W') {
        e.preventDefault();
        walkStep('forward');
      } else if (e.code === 'KeyS' || e.key === 'ArrowDown' || e.key === 's' || e.key === 'S') {
        e.preventDefault();
        walkStep('backward');
      } else if (e.code === 'KeyA' || e.key === 'ArrowLeft' || e.key === 'a' || e.key === 'A') {
        e.preventDefault();
        walkStep('left');
      } else if (e.code === 'KeyD' || e.key === 'ArrowRight' || e.key === 'd' || e.key === 'D') {
        e.preventDefault();
        walkStep('right');
      }
    };

    const handlePointerLockChange = () => {
      if (!document.pointerLockElement && isWalkthrough) {
        exitWalkthrough();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    document.addEventListener('pointerlockchange', handlePointerLockChange);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('pointerlockchange', handlePointerLockChange);
    };
  }, [isWalkthrough]);

  // Fit camera with proper perspective framing
  const fitCameraToModel = (isTwin: boolean, force = false) => {
    const camera = cameraRef.current;
    const controls = controlsRef.current;
    const container = containerRef.current;
    if (!camera || !controls || !container) return;

    if (isTwin && importedModel && importedModel.bounding_box) {
      if (!force && lastFittedModelIdRef.current === importedModel.model_id && lastModeRef.current === 'twin') {
        return;
      }

      const b = importedModel.bounding_box;
      const modelWidth = Math.max(1, b.width);
      const modelHeight = Math.max(1, b.depth);
      const modelDepth = Math.max(1, b.height);

      const aspect = container.clientWidth / (container.clientHeight || 1);
      const fovRad = (camera.fov * Math.PI) / 180;
      const fitHeightDist = (modelHeight / 2) / Math.tan(fovRad / 2);
      const fitWidthDist = (modelWidth / 2) / (Math.tan(fovRad / 2) * aspect);
      const fitDepthDist = (modelDepth / 2) / (Math.tan(fovRad / 2) * aspect);
      const baseDist = Math.max(fitHeightDist, fitWidthDist, fitDepthDist);
      const dist = Math.max(12, baseDist * 1.55);

      const targetY = modelHeight / 2;
      controls.target.set(0, targetY, 0);
      camera.position.set(dist * 0.85, targetY + dist * 0.55, dist * 0.95);
      camera.up.set(0, 1, 0);
      camera.near = 0.1;
      camera.far = Math.max(1000, dist * 10);
      camera.updateProjectionMatrix();

      controls.minDistance = Math.max(0.5, Math.min(modelWidth, modelDepth, modelHeight) * 0.05);
      controls.maxDistance = Math.max(350, dist * 6);
      controls.update();

      lastFittedModelIdRef.current = importedModel.model_id;
      lastModeRef.current = 'twin';
      return;
    }

    // Parametric Mode Fitting
    if (!force && lastModeRef.current === 'parametric') {
      return;
    }

    const { width_m, length_m, floor_height_m, floors } = params;
    const totalHeight = Math.max(1, floors * floor_height_m);
    const modelWidth = Math.max(1, width_m);
    const modelDepth = Math.max(1, length_m);

    const aspect = container.clientWidth / (container.clientHeight || 1);
    const fovRad = (camera.fov * Math.PI) / 180;
    const fitHeightDist = (totalHeight / 2) / Math.tan(fovRad / 2);
    const fitWidthDist = (modelWidth / 2) / (Math.tan(fovRad / 2) * aspect);
    const fitDepthDist = (modelDepth / 2) / (Math.tan(fovRad / 2) * aspect);
    const baseDist = Math.max(fitHeightDist, fitWidthDist, fitDepthDist);
    const dist = Math.max(25, baseDist * 1.6);

    const targetY = totalHeight / 2;
    controls.target.set(0, targetY, 0);
    camera.position.set(dist * 0.85, targetY + dist * 0.55, dist * 0.95);
    camera.up.set(0, 1, 0);
    camera.near = 0.1;
    camera.far = Math.max(1000, dist * 10);
    camera.updateProjectionMatrix();

    controls.minDistance = 2;
    controls.maxDistance = 350;
    controls.update();

    lastModeRef.current = 'parametric';
    lastFittedModelIdRef.current = null;
  };

  // Rebuild building geometry whenever importedModel, parameters, filters, viewerMode, or interior settings change
  useEffect(() => {
    const buildingGroup = buildingGroupRef.current;
    if (!buildingGroup) return;

    // Dispose old children in building group
    while (buildingGroup.children.length > 0) {
      const child = buildingGroup.children[0] as THREE.Mesh;
      buildingGroup.remove(child);
      if (child.geometry) child.geometry.dispose();
      if (child.material) {
        if (Array.isArray(child.material)) {
          child.material.forEach((m) => m.dispose());
        } else {
          child.material.dispose();
        }
      }
    }

    // =========================================================================
    // BRANCH A: IMPORTED IFC DIGITAL TWIN RENDERING
    // =========================================================================
    if (importedModel && importedModel.elements && importedModel.elements.length > 0) {
      const { elements, bounding_box } = importedModel;

      const ifcGroup = new THREE.Group();
      ifcGroup.name = 'ifcModelGroup';

      // 1. Convert IFC Z-up to Three.js Y-up by rotating -90 deg around X-axis
      ifcGroup.rotation.x = -Math.PI / 2;

      // 2. Position ifcGroup so the building is horizontally centered at (0, 0)
      if (bounding_box) {
        ifcGroup.position.set(
          -bounding_box.center_x,
          -bounding_box.min_z,
          bounding_box.center_y
        );

        // Adapt environment grid & shadow frustum
        const footprint = Math.max(bounding_box.width, bounding_box.height, 40);
        const gridDimension = Math.max(100, Math.ceil((footprint * 2.8) / 20) * 20);
        if (gridHelperRef.current) {
          const factor = gridDimension / 120;
          gridHelperRef.current.scale.set(factor, 1, factor);
        }
        if (groundRef.current) {
          const factor = gridDimension / 200;
          groundRef.current.scale.set(factor, factor, 1);
        }
        if (sunLightRef.current) {
          const shadowSize = Math.max(bounding_box.width, bounding_box.height, bounding_box.depth) * 1.3;
          sunLightRef.current.shadow.camera.left = -shadowSize;
          sunLightRef.current.shadow.camera.right = shadowSize;
          sunLightRef.current.shadow.camera.top = shadowSize;
          sunLightRef.current.shadow.camera.bottom = -shadowSize;
          sunLightRef.current.shadow.camera.far = Math.max(250, shadowSize * 5);
          sunLightRef.current.position.set(shadowSize * 1.3, shadowSize * 1.6, shadowSize * 0.9);
          sunLightRef.current.shadow.camera.updateProjectionMatrix();
        }
      }

      elements.forEach((elem) => {
        // 1. Filter by category
        if (hiddenCategories.includes(elem.element_type)) {
          return;
        }
        if (visibleTypes && visibleTypes.length > 0 && !visibleTypes.includes(elem.element_type)) {
          return;
        }

        // 2. Filter by Storey in Interior View or Slicing
        const activeStorey = viewerMode === 'interior' ? interiorStoreyId : selectedStoreyId;
        if (activeStorey && elem.storey_id && elem.storey_id !== activeStorey) {
          // If a specific floor is selected in Interior View, hide elements belonging to other storeys
          if (viewerMode === 'interior') {
            return;
          }
        }

        // 3. Ceiling Cutaway Mode (Interior View)
        if (viewerMode === 'interior' && !showCeiling) {
          if (elem.element_type === 'IfcRoof') {
            return; // Hide roof structure in cutaway mode
          }
          if (elem.element_type === 'IfcSlab') {
            // If viewing a specific floor, hide slab above it
            if (interiorStoreyId) {
              const currentSt = importedModel.storeys.find((s) => s.storey_id === interiorStoreyId);
              if (currentSt && currentSt.elevation_m != null && elem.bounding_box) {
                // Slab positioned at or above current ceiling
                if (elem.bounding_box.min_z >= currentSt.elevation_m + 2.4) {
                  return;
                }
              }
            }
          }
        }

        // 4. Wall Transparency & Visibility (Interior View)
        let isExteriorWall = false;
        if (elem.element_type === 'IfcWall' || elem.element_type === 'IfcWallStandardCase') {
          const wType = String(elem.source_properties?.WallType || '').toLowerCase();
          const isExtProp = elem.source_properties?.Pset_WallCommon?.IsExternal;
          isExteriorWall = wType.includes('exterior') || isExtProp === true || elem.name.toLowerCase().includes('exterior');

          if (viewerMode === 'interior') {
            if (wallTransparency === 'hidden') {
              return; // Hide all walls
            }
            if (wallTransparency === 'cutaway' && isExteriorWall) {
              return; // Hide exterior walls for completely open dollhouse view
            }
          }
        }

        // 5. Render triangulated geometry
        if (elem.geometry && elem.geometry.vertices && elem.geometry.vertices.length >= 9 && elem.geometry.faces) {
          const geom = new THREE.BufferGeometry();
          geom.setAttribute('position', new THREE.Float32BufferAttribute(elem.geometry.vertices, 3));
          geom.setIndex(elem.geometry.faces);
          geom.computeVertexNormals();

          const baseStyle = ELEMENT_COLOR_MAP[elem.element_type] || { color: 0x0d9488, roughness: 0.6 };
          const style = getMaterialPresetStyle(
            elem.element_type,
            visualPreset,
            baseStyle.color,
            baseStyle.roughness,
            baseStyle.metalness
          );
          const isSelected = elem.element_id === selectedElementId || (selectedRoom && elem.element_id === selectedRoom.element_id);
          const isHighlighted = Boolean(highlightedElementIds && highlightedElementIds.includes(elem.element_id));

          let elemColor = style.color;
          let elemEmissive = 0x000000;
          let elemEmissiveIntensity = 0.0;
          let elemOpacity = style.opacity !== undefined ? style.opacity : 1.0;
          let elemTransparent = style.transparent || false;

          // Interior View Custom Wall Transparency
          if (viewerMode === 'interior') {
            if ((elem.element_type === 'IfcWall' || elem.element_type === 'IfcWallStandardCase') && isExteriorWall) {
              if (wallTransparency === 'translucent') {
                elemTransparent = true;
                elemOpacity = 0.22;
              } else if (wallTransparency === 'solid') {
                elemTransparent = false;
                elemOpacity = 1.0;
              }
            }

            // Room (IfcSpace) Highlighting in Interior View
            if (elem.element_type === 'IfcSpace') {
              if (isSelected) {
                elemColor = 0x10b981; // Vibrant emerald
                elemEmissive = 0x059669;
                elemEmissiveIntensity = 0.65;
                elemOpacity = 0.45;
                elemTransparent = true;
              } else {
                elemColor = 0x6ee7b7; // Mint green translucent
                elemOpacity = 0.18;
                elemTransparent = true;
              }
            }
          }

          if (isHighlighted) {
            if (highlightSeverity === 'High') {
              elemColor = 0xf43f5e;
              elemEmissive = 0xe11d48;
              elemEmissiveIntensity = 0.7;
            } else if (highlightSeverity === 'Warning') {
              elemColor = 0xf59e0b;
              elemEmissive = 0xd97706;
              elemEmissiveIntensity = 0.6;
            } else {
              elemColor = 0x0284c7;
              elemEmissive = 0x0369a1;
              elemEmissiveIntensity = 0.5;
            }
            elemTransparent = false;
            elemOpacity = 1.0;
          } else if (isSelected && elem.element_type !== 'IfcSpace') {
            elemColor = 0xf59e0b;
            elemEmissive = 0xd97706;
            elemEmissiveIntensity = 0.5;
            elemTransparent = false;
            elemOpacity = 1.0;
          }

          const material = new THREE.MeshStandardMaterial({
            color: elemColor,
            roughness: style.roughness !== undefined ? style.roughness : 0.6,
            metalness: style.metalness !== undefined ? style.metalness : 0.1,
            transparent: elemTransparent,
            opacity: elemOpacity,
            wireframe: visualPreset === 'technical_inspection' ? true : wireframeMode,
            emissive: elemEmissive,
            emissiveIntensity: elemEmissiveIntensity,
            side: THREE.DoubleSide,
          });

          const mesh = new THREE.Mesh(geom, material);
          mesh.castShadow = true;
          mesh.receiveShadow = true;
          mesh.userData = { element: elem, elementId: elem.element_id };
          ifcGroup.add(mesh);
        } else if (elem.bounding_box) {
          // Fallback box for entities without tessellated mesh
          const b = elem.bounding_box;
          const boxGeo = new THREE.BoxGeometry(b.width || 1, b.height || 1, b.depth || 1);
          const isSelected = elem.element_id === selectedElementId || (selectedRoom && elem.element_id === selectedRoom.element_id);
          const isHighlighted = Boolean(highlightedElementIds && highlightedElementIds.includes(elem.element_id));

          let boxColor = 0xa1a1aa;
          let boxEmissive = 0x000000;
          let boxEmissiveIntensity = 0.0;
          let boxOpacity = 1.0;
          let boxTransparent = false;

          if (viewerMode === 'interior' && elem.element_type === 'IfcSpace') {
            boxColor = isSelected ? 0x10b981 : 0x6ee7b7;
            boxEmissive = isSelected ? 0x059669 : 0x000000;
            boxEmissiveIntensity = isSelected ? 0.6 : 0.0;
            boxOpacity = isSelected ? 0.45 : 0.18;
            boxTransparent = true;
          } else if (isHighlighted) {
            boxColor = 0xf43f5e;
            boxEmissive = 0xe11d48;
            boxEmissiveIntensity = 0.7;
          } else if (isSelected) {
            boxColor = 0xf59e0b;
            boxEmissive = 0xd97706;
            boxEmissiveIntensity = 0.5;
          }

          const material = new THREE.MeshStandardMaterial({
            color: boxColor,
            roughness: 0.7,
            wireframe: wireframeMode,
            emissive: boxEmissive,
            emissiveIntensity: boxEmissiveIntensity,
            transparent: boxTransparent,
            opacity: boxOpacity,
          });
          const boxMesh = new THREE.Mesh(boxGeo, material);
          boxMesh.position.set(b.center_x, b.center_y, b.center_z);
          boxMesh.castShadow = true;
          boxMesh.receiveShadow = true;
          boxMesh.userData = { element: elem, elementId: elem.element_id };
          ifcGroup.add(boxMesh);
        }
      });

      buildingGroup.add(ifcGroup);

      if (viewerMode === 'interior') {
        transitionToInteriorView(interiorStoreyId);
      } else {
        fitCameraToModel(true, false);
      }
      return;
    }

    // =========================================================================
    // BRANCH B: PARAMETRIC BUILDING MASSING & INTERVENTIONS
    // =========================================================================
    if (gridHelperRef.current) {
      gridHelperRef.current.scale.set(1, 1, 1);
    }
    if (groundRef.current) {
      groundRef.current.scale.set(1, 1, 1);
    }

    const { width_m, length_m, floor_height_m, floors } = params;
    if (width_m <= 0 || length_m <= 0 || floor_height_m <= 0 || floors <= 0) return;

    const totalHeight = floors * floor_height_m;

    // Plinth
    const plinthHeight = 0.3;
    const plinthGeo = new THREE.BoxGeometry(width_m + 0.6, plinthHeight, length_m + 0.6);
    const plinthMat = new THREE.MeshStandardMaterial({ color: 0x5a626d, roughness: 0.8, wireframe: wireframeMode });
    const plinth = new THREE.Mesh(plinthGeo, plinthMat);
    plinth.position.set(0, plinthHeight / 2, 0);
    plinth.receiveShadow = true;
    buildingGroup.add(plinth);

    // Floor Slabs & Walls
    const slabThickness = 0.25;
    const isTranslucentWall = viewerMode === 'interior' && wallTransparency === 'translucent';
    const wallOpacity = isTranslucentWall ? 0.22 : 1.0;
    const wallTransparent = isTranslucentWall;

    const wallMat = new THREE.MeshStandardMaterial({
      color: 0xf0f2f5,
      roughness: 0.65,
      metalness: 0.05,
      wireframe: wireframeMode,
      transparent: wallTransparent,
      opacity: wallOpacity,
    });
    const slabMat = new THREE.MeshStandardMaterial({ color: 0xd5d9df, roughness: 0.75, wireframe: wireframeMode });

    for (let f = 0; f < floors; f++) {
      const floorBaseY = plinthHeight + f * floor_height_m;
      const wallHeight = floor_height_m - slabThickness;

      if (viewerMode !== 'interior' || wallTransparency !== 'hidden') {
        const floorGeo = new THREE.BoxGeometry(width_m, wallHeight, length_m);
        const floorMesh = new THREE.Mesh(floorGeo, wallMat);
        floorMesh.position.set(0, floorBaseY + wallHeight / 2, 0);
        floorMesh.castShadow = true;
        floorMesh.receiveShadow = true;
        buildingGroup.add(floorMesh);
      }

      const slabGeo = new THREE.BoxGeometry(width_m + 0.2, slabThickness, length_m + 0.2);
      const slabMesh = new THREE.Mesh(slabGeo, slabMat);
      slabMesh.position.set(0, floorBaseY + wallHeight + slabThickness / 2, 0);
      slabMesh.castShadow = true;
      slabMesh.receiveShadow = true;
      buildingGroup.add(slabMesh);
    }

    // Roof (hidden in interior cutaway if showCeiling is false)
    if (viewerMode !== 'interior' || showCeiling) {
      const roofTopY = plinthHeight + totalHeight;
      const roofGeo = new THREE.BoxGeometry(width_m + 0.4, 0.35, length_m + 0.4);
      const roofMat = new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.8, wireframe: wireframeMode });
      const roofMesh = new THREE.Mesh(roofGeo, roofMat);
      roofMesh.position.set(0, roofTopY + 0.35 / 2, 0);
      buildingGroup.add(roofMesh);
    }

    fitCameraToModel(false, false);
  }, [
    params,
    activeInterventions,
    wireframeMode,
    viewerMode,
    visualPreset,
    interiorStoreyId,
    showCeiling,
    wallTransparency,
    hiddenCategories,
    selectedRoom,
    importedModel,
    visibleTypes,
    selectedStoreyId,
    selectedElementId,
    highlightedElementIds,
    highlightSeverity,
  ]);

  // Subsurface Geotechnical 3D Visualization (Phase 4)
  useEffect(() => {
    const scene = sceneRef.current;
    if (!scene) return;

    if (!subsurfaceGroupRef.current) {
      const group = new THREE.Group();
      group.name = 'subsurfaceGroup';
      scene.add(group);
      subsurfaceGroupRef.current = group;
    }

    const subGroup = subsurfaceGroupRef.current;
    while (subGroup.children.length > 0) {
      const child = subGroup.children[0] as THREE.Mesh;
      subGroup.remove(child);
      if (child.geometry) child.geometry.dispose();
      if (child.material) {
        if (Array.isArray(child.material)) child.material.forEach((m) => m.dispose());
        else child.material.dispose();
      }
    }

    if (!showSubsurface && !showBoreholes && !showGroundwater && !showFloodOverlay) {
      return;
    }

    // 1. Soil Strata Slabs (4 continuous geological layers)
    if (showSubsurface && geotechnicalProfile) {
      const strata = geotechnicalProfile.regional_strata_summary;
      const slabWidth = 55.0;
      const slabDepth = 55.0;

      strata.forEach((layer) => {
        const thickness = Math.max(0.8, layer.thickness_m);
        const centerY = -layer.depth_top_m - (thickness / 2);
        const geo = new THREE.BoxGeometry(slabWidth, thickness, slabDepth);
        const mat = new THREE.MeshStandardMaterial({
          color: new THREE.Color(layer.color_hex),
          roughness: 0.9,
          metalness: 0.05,
          transparent: true,
          opacity: 0.75,
          depthWrite: false,
        });
        const mesh = new THREE.Mesh(geo, mat);
        mesh.position.set(0, centerY, 0);
        mesh.userData = { isStrata: true, layer };
        subGroup.add(mesh);

        // Edge wireframe for clean strata boundary definition
        const edges = new THREE.EdgesGeometry(geo);
        const line = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({ color: 0x333333, transparent: true, opacity: 0.35 }));
        line.position.copy(mesh.position);
        subGroup.add(line);
      });
    }

    // 2. 3D Borehole Columns
    if (showBoreholes && geotechnicalProfile) {
      geotechnicalProfile.boreholes.forEach((bh) => {
        const colRadius = 0.45;
        const colDepth = Math.max(10, bh.total_depth_m);
        const geo = new THREE.CylinderGeometry(colRadius, colRadius, colDepth, 16);
        const isSelectedBh = selectedBorehole?.borehole_id === bh.borehole_id;
        const mat = new THREE.MeshStandardMaterial({
          color: isSelectedBh ? 0x10b981 : 0xd97706,
          roughness: 0.4,
          metalness: 0.2,
          emissive: isSelectedBh ? 0x059669 : 0x000000,
          emissiveIntensity: isSelectedBh ? 0.5 : 0.0,
        });
        const mesh = new THREE.Mesh(geo, mat);
        mesh.position.set(bh.local_x, -colDepth / 2, bh.local_z);
        mesh.userData = { isBorehole: true, borehole: bh, boreholeId: bh.borehole_id };
        subGroup.add(mesh);

        // Floating top cap marker
        const capGeo = new THREE.SphereGeometry(0.8, 16, 16);
        const capMat = new THREE.MeshStandardMaterial({
          color: isSelectedBh ? 0x10b981 : 0xf59e0b,
          roughness: 0.3,
        });
        const capMesh = new THREE.Mesh(capGeo, capMat);
        capMesh.position.set(bh.local_x, 0.4, bh.local_z);
        capMesh.userData = { isBorehole: true, borehole: bh, boreholeId: bh.borehole_id };
        subGroup.add(capMesh);
      });
    }

    // 3. Groundwater Table Plane
    if (showGroundwater && geotechnicalProfile) {
      const gwDepth = -geotechnicalProfile.groundwater_table_m;
      const gwGeo = new THREE.PlaneGeometry(65, 65);
      const gwMat = new THREE.MeshStandardMaterial({
        color: 0x0284c7,
        roughness: 0.1,
        metalness: 0.1,
        transparent: true,
        opacity: 0.38,
        side: THREE.DoubleSide,
      });
      const gwMesh = new THREE.Mesh(gwGeo, gwMat);
      gwMesh.rotation.x = -Math.PI / 2;
      gwMesh.position.set(0, gwDepth, 0);
      subGroup.add(gwMesh);
    }

    // 4. Flood Inundation Plane
    if (showFloodOverlay && geotechnicalProfile) {
      const floodY = geotechnicalProfile.flood_hazard_level_100yr_m;
      const fGeo = new THREE.PlaneGeometry(60, 60);
      const fMat = new THREE.MeshStandardMaterial({
        color: 0x38bdf8,
        roughness: 0.2,
        transparent: true,
        opacity: 0.28,
        side: THREE.DoubleSide,
      });
      const fMesh = new THREE.Mesh(fGeo, fMat);
      fMesh.rotation.x = -Math.PI / 2;
      fMesh.position.set(0, floodY, 0);
      subGroup.add(fMesh);
    }
  }, [showSubsurface, showBoreholes, showGroundwater, showFloodOverlay, geotechnicalProfile, selectedBorehole]);

  // Camera Reset / Fit to Model
  const handleResetCamera = () => {
    if (viewerMode === 'interior') {
      transitionToInteriorView(interiorStoreyId);
    } else {
      fitCameraToModel(isDigitalTwinMode, true);
    }
  };

  // Toggle Category Filter in Interior View
  const toggleCategory = (cat: string) => {
    setHiddenCategories((prev) =>
      prev.includes(cat) ? prev.filter((c) => c !== cat) : [...prev, cat]
    );
  };

  // Handle saving custom room note
  const handleSaveRoomNote = (roomId: string) => {
    if (!customRoomNote.trim()) return;
    setSavedNotes((prev) => ({
      ...prev,
      [roomId]: customRoomNote.trim(),
    }));
    setCustomRoomNote('');
  };

  // Extract selected room details for the inspector panel
  const currentRoom = selectedRoom || (availableRooms.length > 0 && viewerMode === 'interior' ? availableRooms[0] : null);
  const pset = currentRoom?.source_properties?.Pset_SpaceCommon || currentRoom?.source_properties || {};
  const roomName = currentRoom?.name || pset.RoomName || currentRoom?.element_id || 'Interior Space';
  const roomFloor = currentRoom?.storey_name || (pset.FloorNumber ? `Floor ${pset.FloorNumber}` : 'Ground Floor');
  const roomArea = pset.NetFloorArea || pset.Area_m2 || (currentRoom?.bounding_box ? (currentRoom.bounding_box.width * currentRoom.bounding_box.height).toFixed(1) : 'N/A');
  const roomDimensions = pset.Dimensions || (currentRoom?.bounding_box ? `${currentRoom.bounding_box.width.toFixed(1)}m × ${currentRoom.bounding_box.height.toFixed(1)}m` : 'N/A');
  const connectedDoors: string[] = pset.ConnectedDoors || currentRoom?.relationships?.connected_doors || [];
  const associatedWindows: string[] = pset.AssociatedWindows || currentRoom?.relationships?.associated_windows || [];
  const materialsList = currentRoom?.materials && currentRoom.materials.length > 0
    ? currentRoom.materials.join(', ')
    : 'Commercial Carpet / Tile, Acoustic Drop Ceiling, Drywall';

  return (
    <div className={`relative flex flex-col bg-charcoal-50 rounded-xl border border-charcoal-200 overflow-hidden shadow-sm ${className}`}>
      {/* ===================================================================== */}
      {/* TOP HEADER CONTROLS BAR */}
      {/* ===================================================================== */}
      <div className="absolute top-3 left-3 right-3 z-20 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 pointer-events-none">
        {/* Left: Label & Twin Status */}
        <div className="flex items-center space-x-2 pointer-events-auto">
          {label && (
            <span
              className={`px-3 py-1 rounded-full text-xs font-semibold tracking-wide shadow-sm border ${
                isBaseline
                  ? 'bg-stone-100 text-stone-700 border-stone-300'
                  : 'bg-emerald-50 text-emerald-800 border-emerald-300'
              }`}
            >
              {label}
            </span>
          )}
          {isDigitalTwinMode && (
            <div className="flex items-center space-x-1.5">
              <span className="px-2.5 py-0.5 rounded-full text-xs bg-emerald-800 text-white font-medium shadow-xs flex items-center space-x-1">
                <span>{importedModel?.total_element_count} IFC Elements</span>
              </span>
            </div>
          )}
        </div>

        {/* Center: Viewer Mode Selector (Skeleton View | Exterior View | Interior View) */}
        <div className="flex items-center bg-white/95 backdrop-blur-md p-1 rounded-xl border border-charcoal-200 shadow-md pointer-events-auto text-xs">
          <button
            onClick={() => handleSetViewerMode('skeleton')}
            title="Skeleton View: structural wireframe mesh view"
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg font-semibold transition-all ${
              viewerMode === 'skeleton'
                ? 'bg-charcoal-900 text-white shadow-2xs'
                : 'text-charcoal-600 hover:text-charcoal-900'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Skeleton View</span>
          </button>

          <button
            onClick={() => handleSetViewerMode('exterior')}
            title="Exterior View: solid envelope perspective view"
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg font-semibold transition-all ${
              viewerMode === 'exterior'
                ? 'bg-charcoal-900 text-white shadow-2xs'
                : 'text-charcoal-600 hover:text-charcoal-900'
            }`}
          >
            <Building2 className="w-3.5 h-3.5" />
            <span>Exterior View</span>
          </button>

          <button
            onClick={() => handleSetViewerMode('interior')}
            title="Interior View: enter building, navigate storeys, and inspect rooms"
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg font-semibold transition-all ${
              viewerMode === 'interior'
                ? 'bg-charcoal-900 text-white shadow-2xs'
                : 'text-charcoal-600 hover:text-charcoal-900'
            }`}
          >
            <Home className="w-3.5 h-3.5" />
            <span>Interior View</span>
          </button>
        </div>

        {/* Right: Camera Action Buttons */}
        <div className="flex items-center space-x-1 bg-white/90 backdrop-blur-xs p-1 rounded-lg border border-charcoal-200 shadow-xs pointer-events-auto">
          {(selectedElementId || selectedRoom || (highlightedElementIds && highlightedElementIds.length > 0)) && (
            <button
              onClick={() => {
                onSelectElement?.(null);
                setSelectedRoom(null);
                onClearHighlight?.();
              }}
              title="Clear selected element & highlights"
              className="px-2 py-1 rounded bg-rose-50 text-rose-700 hover:bg-rose-100 border border-rose-200 text-xs font-semibold flex items-center space-x-1 transition-colors"
            >
              <X className="w-3.5 h-3.5" />
              <span>Clear</span>
            </button>
          )}

          <button
            onClick={() => setIsRotating(!isRotating)}
            title={isRotating ? 'Pause auto-rotation' : 'Start auto-rotation'}
            className={`p-1.5 rounded hover:bg-charcoal-100 transition-colors text-charcoal-700 ${
              isRotating ? 'bg-charcoal-200 text-charcoal-900' : ''
            }`}
          >
            <RotateCw className="w-4 h-4" />
          </button>

          <button
            onClick={handleResetCamera}
            title="Fit to model / Reset camera view"
            className="p-1.5 rounded hover:bg-charcoal-100 transition-colors text-charcoal-700"
          >
            <Maximize2 className="w-4 h-4" />
          </button>

          <button
            onClick={() => setIsSettingsOpen(!isSettingsOpen)}
            title="Viewer & Subsurface Settings"
            className={`p-1.5 rounded hover:bg-charcoal-100 transition-colors ${
              isSettingsOpen ? 'bg-charcoal-900 text-white' : 'text-charcoal-700'
            }`}
          >
            <SlidersHorizontal className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* ===================================================================== */}
      {/* INTERIOR VIEW SUB-TOOLBAR (ACTIVE WHEN INTERIOR VIEW IS SELECTED) */}
      {/* ===================================================================== */}
      {viewerMode === 'interior' && (
        <div className="absolute top-16 left-3 right-3 z-10 flex flex-wrap items-center justify-between gap-2 bg-white/95 backdrop-blur-md p-2 rounded-xl border border-charcoal-200 shadow-md text-xs pointer-events-auto animate-in fade-in duration-150">
          <div className="flex flex-wrap items-center gap-2">
            {/* Storey Navigation Pills */}
            <div className="flex items-center space-x-1 bg-stone-100 p-0.5 rounded-lg border border-charcoal-200">
              <button
                onClick={() => {
                  setInteriorStoreyId(null);
                  transitionToInteriorView(null);
                }}
                className={`px-2.5 py-1 rounded-md font-semibold text-[11px] transition-all ${
                  interiorStoreyId === null
                    ? 'bg-charcoal-900 text-white shadow-2xs'
                    : 'text-charcoal-600 hover:text-charcoal-900'
                }`}
              >
                All Levels
              </button>
              {(importedModel?.storeys || []).map((st) => (
                <button
                  key={st.storey_id}
                  onClick={() => {
                    setInteriorStoreyId(st.storey_id);
                    transitionToInteriorView(st.storey_id);
                  }}
                  className={`px-2.5 py-1 rounded-md font-semibold text-[11px] transition-all ${
                    interiorStoreyId === st.storey_id
                      ? 'bg-emerald-800 text-white shadow-2xs'
                      : 'text-charcoal-600 hover:text-charcoal-900'
                  }`}
                >
                  {st.name}
                </button>
              ))}
            </div>

            {/* Ceiling Cutaway Toggle */}
            <button
              onClick={() => setShowCeiling(!showCeiling)}
              title={showCeiling ? 'Hide ceiling and roof for cutaway interior view' : 'Show ceiling and roof'}
              className={`px-2.5 py-1 rounded-lg border text-[11px] font-semibold flex items-center space-x-1.5 transition-colors ${
                !showCeiling
                  ? 'bg-amber-500/10 border-amber-400 text-amber-900 font-bold'
                  : 'bg-stone-100 border-charcoal-200 text-charcoal-700'
              }`}
            >
              <span>{showCeiling ? 'Ceiling: Visible' : 'Ceiling: Cutaway (Hidden)'}</span>
            </button>

            {/* Wall Transparency Control */}
            <div className="flex items-center space-x-1 bg-stone-100 p-0.5 rounded-lg border border-charcoal-200 text-[11px]">
              <span className="text-[10px] text-charcoal-500 uppercase font-bold px-1.5">Walls:</span>
              {(['translucent', 'cutaway', 'solid', 'hidden'] as const).map((mode) => (
                <button
                  key={mode}
                  onClick={() => setWallTransparency(mode)}
                  className={`px-2 py-0.5 rounded capitalize font-semibold transition-all ${
                    wallTransparency === mode
                      ? 'bg-charcoal-900 text-white shadow-2xs'
                      : 'text-charcoal-600 hover:text-charcoal-900'
                  }`}
                >
                  {mode}
                </button>
              ))}
            </div>

            {/* Quick Category Toggles */}
            <div className="hidden lg:flex items-center space-x-1 bg-stone-100 p-0.5 rounded-lg border border-charcoal-200 text-[10px]">
              <span className="text-[9px] text-charcoal-500 uppercase font-bold px-1">Hide:</span>
              {[
                { type: 'IfcWall', label: 'Walls' },
                { type: 'IfcSlab', label: 'Slabs' },
                { type: 'IfcDoor', label: 'Doors' },
                { type: 'IfcWindow', label: 'Windows' },
                { type: 'IfcSpace', label: 'Rooms' },
              ].map(({ type, label: catLabel }) => {
                const isHidden = hiddenCategories.includes(type);
                return (
                  <button
                    key={type}
                    onClick={() => toggleCategory(type)}
                    className={`px-1.5 py-0.5 rounded font-semibold transition-all ${
                      isHidden
                        ? 'bg-rose-100 text-rose-800 line-through'
                        : 'text-charcoal-600 hover:text-charcoal-900'
                    }`}
                  >
                    {catLabel}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {/* Room Selector Dropdown */}
            {availableRooms.length > 0 && (
              <select
                value={selectedRoom?.element_id || ''}
                onChange={(e) => {
                  const rm = availableRooms.find((r) => r.element_id === e.target.value) || null;
                  setSelectedRoom(rm);
                  if (rm) {
                    onSelectElement?.(rm);
                    focusOnRoom(rm);
                  }
                }}
                className="bg-white border border-charcoal-200 rounded-lg px-2.5 py-1 text-[11px] font-semibold text-charcoal-800"
              >
                <option value="">Select Room ({availableRooms.length} detected)...</option>
                {availableRooms.map((rm) => (
                  <option key={rm.element_id} value={rm.element_id}>
                    {rm.name || rm.element_id}
                  </option>
                ))}
              </select>
            )}

            {/* First-Person Walkthrough Button */}
            <button
              onClick={() => {
                if (isWalkthrough) {
                  setIsWalkthrough(false);
                } else {
                  enterRoomWalkthrough(selectedRoom);
                }
              }}
              className={`px-3 py-1 rounded-lg text-[11px] font-semibold flex items-center space-x-1.5 transition-colors shadow-2xs ${
                isWalkthrough
                  ? 'bg-rose-600 hover:bg-rose-700 text-white'
                  : 'bg-emerald-800 hover:bg-emerald-900 text-white'
              }`}
            >
              <Footprints className="w-3.5 h-3.5" />
              <span>{isWalkthrough ? 'Exit Walk' : 'Walk Inside (FPS)'}</span>
            </button>
          </div>
        </div>
      )}

      {/* ===================================================================== */}
      {/* ROOM INFORMATION INSPECTOR CARD (FLOATING IN INTERIOR VIEW) */}
      {/* ===================================================================== */}
      {viewerMode === 'interior' && currentRoom && (
        <div className="absolute top-32 left-3 z-20 bg-white/95 backdrop-blur-md rounded-2xl border border-charcoal-200 shadow-2xl p-4 max-w-xs w-full space-y-3 pointer-events-auto animate-in slide-in-from-left-3 duration-200">
          <div className="flex items-center justify-between pb-2 border-b border-charcoal-100">
            <div className="flex items-center space-x-2">
              <div className="p-1.5 bg-emerald-100 text-emerald-800 rounded-lg border border-emerald-200">
                <Home className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-charcoal-900 tracking-tight">{roomName}</h4>
                <span className="text-[10px] text-charcoal-500 font-mono">{roomFloor}</span>
              </div>
            </div>
            <button
              onClick={() => {
                setSelectedRoom(null);
                onSelectElement?.(null);
              }}
              className="text-charcoal-400 hover:text-charcoal-700 p-0.5 rounded"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Room Area & Dimensions */}
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="bg-stone-50 p-2 rounded-xl border border-charcoal-100">
              <span className="text-[10px] text-charcoal-500 uppercase font-semibold">Net Floor Area</span>
              <div className="font-bold text-charcoal-900 text-sm">{roomArea} m²</div>
            </div>
            <div className="bg-stone-50 p-2 rounded-xl border border-charcoal-100">
              <span className="text-[10px] text-charcoal-500 uppercase font-semibold">Dimensions</span>
              <div className="font-bold text-charcoal-900 text-sm">{roomDimensions}</div>
            </div>
          </div>

          {/* Connected Openings */}
          <div className="space-y-1 text-xs">
            <div className="flex items-center justify-between text-[11px] text-charcoal-700">
              <span className="font-semibold">Connected Doors:</span>
              <span className="font-mono font-bold text-amber-800">
                {Array.isArray(connectedDoors) ? connectedDoors.length : 1} Door(s)
              </span>
            </div>
            <div className="flex items-center justify-between text-[11px] text-charcoal-700">
              <span className="font-semibold">Associated Windows:</span>
              <span className="font-mono font-bold text-sky-800">
                {Array.isArray(associatedWindows) ? associatedWindows.length : 2} Window(s)
              </span>
            </div>
          </div>

          {/* Finishes & Materials */}
          <div className="text-xs bg-stone-50 p-2.5 rounded-xl border border-charcoal-100">
            <span className="text-[10px] text-charcoal-500 uppercase font-semibold block mb-0.5">Finishes & Materials</span>
            <p className="text-[11px] text-charcoal-700 leading-snug">{materialsList}</p>
          </div>

          {/* Saved User Notes if present */}
          {savedNotes[currentRoom.element_id] && (
            <div className="bg-emerald-50 border border-emerald-200 p-2 rounded-lg text-emerald-900 text-[11px]">
              <span className="font-semibold">Room Note:</span> {savedNotes[currentRoom.element_id]}
            </div>
          )}

          {/* Add / Edit Custom Note Input */}
          <div className="flex items-center space-x-1.5 pt-1">
            <input
              type="text"
              placeholder="Add room note / tag..."
              value={customRoomNote}
              onChange={(e) => setCustomRoomNote(e.target.value)}
              className="flex-1 bg-stone-50 border border-charcoal-200 rounded-lg px-2 py-1 text-[11px]"
            />
            <button
              onClick={() => handleSaveRoomNote(currentRoom.element_id)}
              disabled={!customRoomNote.trim()}
              className="bg-charcoal-900 hover:bg-charcoal-800 disabled:opacity-40 text-white text-[11px] font-semibold px-2.5 py-1 rounded-lg transition-colors"
            >
              Save
            </button>
          </div>

          {/* Actions */}
          <div className="flex items-center space-x-2 pt-1">
            <button
              onClick={() => focusOnRoom(currentRoom)}
              className="flex-1 bg-stone-100 hover:bg-stone-200 text-charcoal-800 py-1.5 rounded-lg text-xs font-semibold flex items-center justify-center space-x-1 transition-colors"
            >
              <Maximize2 className="w-3.5 h-3.5" />
              <span>Focus Room</span>
            </button>
            <button
              onClick={() => enterRoomWalkthrough(currentRoom)}
              className="flex-1 bg-emerald-800 hover:bg-emerald-900 text-white py-1.5 rounded-lg text-xs font-semibold flex items-center justify-center space-x-1 transition-colors shadow-2xs"
            >
              <Footprints className="w-3.5 h-3.5" />
              <span>Walk Inside</span>
            </button>
          </div>
        </div>
      )}

      {/* Notice if uploaded model lacks explicit IfcSpace elements */}
      {viewerMode === 'interior' && availableRooms.length === 0 && (
        <div className="absolute top-32 left-3 z-20 bg-white/95 backdrop-blur-md rounded-2xl border border-amber-200 shadow-xl p-3.5 max-w-xs text-xs pointer-events-auto space-y-2">
          <div className="flex items-center space-x-2 text-amber-900 font-semibold">
            <Home className="w-4 h-4 text-amber-600 shrink-0" />
            <span>Interior Geometry Available</span>
          </div>
          <p className="text-[11px] text-charcoal-600 leading-relaxed">
            This model contains physical interior walls, slabs, doors, and windows, but no explicit <code className="font-mono text-amber-800">IfcSpace</code> boundary definitions. Use the cutaway and walkthrough controls to inspect the interior structure.
          </p>
        </div>
      )}

      {/* ===================================================================== */}
      {/* FIRST-PERSON WALKTHROUGH HUD & CONTROLS */}
      {/* ===================================================================== */}
      {isWalkthrough && (
        <div className="absolute bottom-12 right-4 z-20 bg-charcoal-950/85 backdrop-blur-md text-white p-3 rounded-2xl border border-charcoal-700 shadow-2xl flex flex-col items-center space-y-2 pointer-events-auto animate-in fade-in">
          <div className="text-[10px] uppercase font-bold tracking-wider text-emerald-400 flex items-center space-x-1">
            <Footprints className="w-3.5 h-3.5" />
            <span>Walkthrough Mode • Eye Level 1.65m</span>
          </div>

          <div className="text-[10px] text-stone-300 text-center font-mono">
            W / A / S / D or Arrow Keys to Walk
          </div>

          {/* D-Pad Buttons */}
          <div className="grid grid-cols-3 gap-1 pt-1">
            <div />
            <button
              onClick={() => walkStep('forward')}
              className="p-2 bg-charcoal-800 hover:bg-charcoal-700 active:bg-emerald-700 rounded-lg text-xs font-bold text-center"
              title="Step Forward"
            >
              ▲
            </button>
            <div />
            <button
              onClick={() => walkStep('left')}
              className="p-2 bg-charcoal-800 hover:bg-charcoal-700 active:bg-emerald-700 rounded-lg text-xs font-bold text-center"
              title="Strafe Left"
            >
              ◀
            </button>
            <button
              onClick={() => walkStep('backward')}
              className="p-2 bg-charcoal-800 hover:bg-charcoal-700 active:bg-emerald-700 rounded-lg text-xs font-bold text-center"
              title="Step Backward"
            >
              ▼
            </button>
            <button
              onClick={() => walkStep('right')}
              className="p-2 bg-charcoal-800 hover:bg-charcoal-700 active:bg-emerald-700 rounded-lg text-xs font-bold text-center"
              title="Strafe Right"
            >
              ▶
            </button>
          </div>

          <button
            onClick={exitWalkthrough}
            className="w-full bg-rose-600 hover:bg-rose-700 text-white font-semibold py-1 rounded-lg text-[11px] transition-colors mt-1"
          >
            Exit Walk
          </button>
        </div>
      )}

      {/* Prominent Floating Exit Walkthrough Banner (Top Right) */}
      {isWalkthrough && (
        <div className="absolute top-4 right-4 z-50 pointer-events-auto animate-in fade-in">
          <button
            onClick={exitWalkthrough}
            className="px-4 py-2 bg-rose-600 hover:bg-rose-700 active:bg-rose-800 text-white font-bold text-xs rounded-xl shadow-2xl flex items-center space-x-2 border border-rose-500 transition-all cursor-pointer"
          >
            <X className="w-4 h-4" />
            <span>Exit Walkthrough (Esc)</span>
          </button>
        </div>
      )}

      {/* Settings Slide-Out Drawer (Phase 2 & Phase 3 & Phase 4) */}
      {isSettingsOpen && (
        <div className="absolute top-16 right-3 z-30 w-80 bg-white/95 backdrop-blur-md rounded-2xl border border-charcoal-200 shadow-2xl p-4 text-xs space-y-4 pointer-events-auto animate-in slide-in-from-right-3 duration-200 max-h-[85vh] overflow-y-auto">
          <div className="flex items-center justify-between pb-2 border-b border-charcoal-100">
            <div className="flex items-center space-x-2">
              <SlidersHorizontal className="w-4 h-4 text-charcoal-800" />
              <h4 className="font-bold text-charcoal-900 text-sm">Viewer & Subsurface Settings</h4>
            </div>
            <button
              onClick={() => setIsSettingsOpen(false)}
              className="text-charcoal-400 hover:text-charcoal-700 p-1 rounded-lg hover:bg-stone-100"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Visual Presets */}
          <div className="space-y-2">
            <span className="text-[10px] text-charcoal-500 uppercase font-bold tracking-wider block">
              Color Grading & Material Preset
            </span>
            <div className="grid grid-cols-2 gap-1.5">
              {[
                { id: 'arch_white', label: 'Arch White' },
                { id: 'concrete', label: 'Concrete' },
                { id: 'warm_interior', label: 'Warm Interior' },
                { id: 'modern_commercial', label: 'Commercial' },
                { id: 'neutral_bim', label: 'Neutral BIM' },
                { id: 'technical_inspection', label: 'Technical' },
              ].map((p) => (
                <button
                  key={p.id}
                  onClick={() => setVisualPreset(p.id as VisualPreset)}
                  className={`px-2.5 py-1.5 rounded-lg border text-[11px] font-semibold text-left transition-all ${
                    visualPreset === p.id
                      ? 'bg-charcoal-900 border-charcoal-900 text-white shadow-2xs'
                      : 'bg-stone-50 border-charcoal-200 text-charcoal-700 hover:bg-stone-100'
                  }`}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          {/* Geotechnical & Subsurface Visualizations */}
          <div className="space-y-2 pt-2 border-t border-charcoal-100">
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-charcoal-500 uppercase font-bold tracking-wider">
                Subsurface Geotechnical Layers
              </span>
              <span className="text-[10px] font-mono text-emerald-800 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200">
                WGS84 Synced
              </span>
            </div>

            <div className="space-y-1.5">
              <label className="flex items-center justify-between p-2 bg-stone-50 rounded-xl border border-charcoal-100 cursor-pointer hover:bg-stone-100 transition-colors">
                <div className="flex items-center space-x-2">
                  <Layers className="w-3.5 h-3.5 text-stone-600" />
                  <span className="text-[11px] font-semibold text-charcoal-800">3D Soil Strata Slabs</span>
                </div>
                <input
                  type="checkbox"
                  checked={showSubsurface}
                  onChange={(e) => setShowSubsurface(e.target.checked)}
                  className="rounded text-charcoal-900 focus:ring-charcoal-900 h-3.5 w-3.5"
                />
              </label>

              <label className="flex items-center justify-between p-2 bg-stone-50 rounded-xl border border-charcoal-100 cursor-pointer hover:bg-stone-100 transition-colors">
                <div className="flex items-center space-x-2">
                  <CircleDot className="w-3.5 h-3.5 text-amber-600" />
                  <span className="text-[11px] font-semibold text-charcoal-800">Core Borehole Columns</span>
                </div>
                <input
                  type="checkbox"
                  checked={showBoreholes}
                  onChange={(e) => setShowBoreholes(e.target.checked)}
                  className="rounded text-charcoal-900 focus:ring-charcoal-900 h-3.5 w-3.5"
                />
              </label>

              <label className="flex items-center justify-between p-2 bg-stone-50 rounded-xl border border-charcoal-100 cursor-pointer hover:bg-stone-100 transition-colors">
                <div className="flex items-center space-x-2">
                  <Waves className="w-3.5 h-3.5 text-blue-600" />
                  <span className="text-[11px] font-semibold text-charcoal-800">Groundwater Table (-4.2m)</span>
                </div>
                <input
                  type="checkbox"
                  checked={showGroundwater}
                  onChange={(e) => setShowGroundwater(e.target.checked)}
                  className="rounded text-charcoal-900 focus:ring-charcoal-900 h-3.5 w-3.5"
                />
              </label>

              <label className="flex items-center justify-between p-2 bg-stone-50 rounded-xl border border-charcoal-100 cursor-pointer hover:bg-stone-100 transition-colors">
                <div className="flex items-center space-x-2">
                  <ShieldAlert className="w-3.5 h-3.5 text-rose-600" />
                  <span className="text-[11px] font-semibold text-charcoal-800">Flood Hazard Plane (+0.75m)</span>
                </div>
                <input
                  type="checkbox"
                  checked={showFloodOverlay}
                  onChange={(e) => setShowFloodOverlay(e.target.checked)}
                  className="rounded text-charcoal-900 focus:ring-charcoal-900 h-3.5 w-3.5"
                />
              </label>
            </div>
          </div>

          {/* Rendering Options */}
          <div className="space-y-2 pt-2 border-t border-charcoal-100">
            <span className="text-[10px] text-charcoal-500 uppercase font-bold tracking-wider block">
              Lighting & Viewport
            </span>

            <div className="space-y-1.5">
              <label className="flex items-center justify-between p-2 bg-stone-50 rounded-xl border border-charcoal-100 cursor-pointer hover:bg-stone-100 transition-colors">
                <div className="flex items-center space-x-2">
                  <Sun className="w-3.5 h-3.5 text-amber-500" />
                  <span className="text-[11px] font-semibold text-charcoal-800">PCF Soft Shadows</span>
                </div>
                <input
                  type="checkbox"
                  checked={enableShadows}
                  onChange={(e) => setEnableShadows(e.target.checked)}
                  className="rounded text-charcoal-900 focus:ring-charcoal-900 h-3.5 w-3.5"
                />
              </label>

              <label className="flex items-center justify-between p-2 bg-stone-50 rounded-xl border border-charcoal-100 cursor-pointer hover:bg-stone-100 transition-colors">
                <div className="flex items-center space-x-2">
                  <Layers className="w-3.5 h-3.5 text-stone-500" />
                  <span className="text-[11px] font-semibold text-charcoal-800">Ground Grid</span>
                </div>
                <input
                  type="checkbox"
                  checked={showGrid}
                  onChange={(e) => setShowGrid(e.target.checked)}
                  className="rounded text-charcoal-900 focus:ring-charcoal-900 h-3.5 w-3.5"
                />
              </label>
            </div>
          </div>

          <div className="pt-2 border-t border-charcoal-100 text-[10px] text-charcoal-500 leading-relaxed">
            Tip: Click directly on any 3D borehole column in the viewport to inspect layer-by-layer soil logs and bearing capacities.
          </div>
        </div>
      )}

      {/* Selected Borehole Inspector Drawer (Phase 4) */}
      {selectedBorehole && (
        <div className="absolute top-20 right-3 z-30 w-88 bg-white/95 backdrop-blur-md rounded-2xl border border-charcoal-200 shadow-2xl p-4 text-xs space-y-3 pointer-events-auto animate-in slide-in-from-right-3 duration-200 max-h-[85vh] overflow-y-auto">
          <div className="flex items-center justify-between pb-2 border-b border-charcoal-100">
            <div className="flex items-center space-x-2">
              <div className="p-1.5 bg-amber-100 text-amber-800 rounded-lg border border-amber-200">
                <CircleDot className="w-4 h-4" />
              </div>
              <div>
                <h4 className="font-bold text-charcoal-900 text-xs">{selectedBorehole.borehole_id} - {selectedBorehole.name}</h4>
                <span className="text-[10px] text-charcoal-500 font-mono">
                  {selectedBorehole.latitude.toFixed(4)}°N, {selectedBorehole.longitude.toFixed(4)}°E
                </span>
              </div>
            </div>
            <button
              onClick={() => setSelectedBorehole(null)}
              className="text-charcoal-400 hover:text-charcoal-700 p-1 rounded-lg hover:bg-stone-100"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Quick Metrics */}
          <div className="grid grid-cols-2 gap-2 text-[11px]">
            <div className="bg-stone-50 p-2 rounded-xl border border-charcoal-100">
              <span className="text-[10px] text-charcoal-500 block">Total Depth</span>
              <strong className="text-charcoal-900 text-sm">{selectedBorehole.total_depth_m} m</strong>
            </div>
            <div className="bg-blue-50 p-2 rounded-xl border border-blue-100">
              <span className="text-[10px] text-blue-600 block">Water Strike</span>
              <strong className="text-blue-900 text-sm">{selectedBorehole.water_table_depth_m ?? 4.2} m bgl</strong>
            </div>
          </div>

          {/* Metadata */}
          <div className="text-[10px] text-charcoal-600 bg-stone-50 p-2 rounded-xl border border-charcoal-100 space-y-0.5">
            <div><strong className="text-charcoal-700">Contractor:</strong> {selectedBorehole.contractor} ({selectedBorehole.drilling_date})</div>
            <div><strong className="text-charcoal-700">Source:</strong> {selectedBorehole.data_source}</div>
          </div>

          {/* Stratigraphic Layers Table */}
          <div className="space-y-1.5">
            <span className="text-[10px] text-charcoal-500 uppercase font-bold tracking-wider block">
              Stratigraphic Intervals & Soil Mechanics
            </span>
            <div className="space-y-2">
              {selectedBorehole.strata.map((l: SoilStrataLayer) => (
                <div
                  key={l.layer_id}
                  className="p-2.5 rounded-xl border border-charcoal-200 bg-white shadow-2xs space-y-1"
                >
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-charcoal-900">{l.layer_name}</span>
                    <span className="font-mono text-[10px] bg-stone-100 px-1.5 py-0.5 rounded border border-charcoal-200">
                      {l.depth_top_m}m - {l.depth_bottom_m}m
                    </span>
                  </div>
                  <p className="text-[11px] text-charcoal-600 leading-tight">{l.geological_description}</p>
                  <div className="grid grid-cols-3 gap-1 pt-1 text-[10px] font-mono text-charcoal-700">
                    <div className="bg-stone-50 p-1 rounded text-center">
                      <span className="text-[9px] text-charcoal-400 block">USCS</span>
                      <strong>{l.uscs_classification}</strong>
                    </div>
                    <div className="bg-stone-50 p-1 rounded text-center">
                      <span className="text-[9px] text-charcoal-400 block">SPT N</span>
                      <strong>{l.spt_n_value_avg ?? 'N/A'}</strong>
                    </div>
                    <div className="bg-emerald-50 text-emerald-900 p-1 rounded text-center border border-emerald-100">
                      <span className="text-[9px] text-emerald-600 block">qa (kPa)</span>
                      <strong>{l.allowable_bearing_capacity_kpa ?? 'N/A'}</strong>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="text-[9px] text-charcoal-400 leading-tight border-t border-charcoal-100 pt-2">
            Engineering Screening Notice: Geotechnical values derived from certified regional borehole exploratory logs. Confirmatory plate load tests and geotechnical boreholes required for foundation engineering design.
          </div>
        </div>
      )}

      {/* 3D Canvas Container */}
      <div
        ref={containerRef}
        className="w-full h-full min-h-[420px] cursor-grab active:cursor-grabbing focus:outline-none"
        tabIndex={0}
        aria-label="Interactive 3D building digital twin viewer"
      />

      {/* Bottom Architectural Scale & Mode Guidance Badge */}
      <div className="absolute bottom-3 left-3 right-3 z-10 flex items-center justify-between text-[11px] text-charcoal-500 pointer-events-none px-2">
        <div className="bg-white/85 backdrop-blur-xs px-2.5 py-1 rounded border border-charcoal-200/80 pointer-events-auto">
          {isDigitalTwinMode && importedModel?.bounding_box ? (
            <span className="flex items-center space-x-2">
              <span className={`inline-block w-2 h-2 rounded-full ${viewerMode === 'interior' ? 'bg-emerald-600' : viewerMode === 'skeleton' ? 'bg-amber-500' : 'bg-blue-600'}`}></span>
              <strong className="text-charcoal-700">Mode: {viewerMode === 'skeleton' ? 'Skeleton View (Wireframe)' : viewerMode === 'interior' ? 'Interior View' : 'Exterior View'}</strong>
              <span className="hidden sm:inline">|</span>
              <span className="hidden sm:inline">
                {importedModel.bounding_box.width}m (W) × {importedModel.bounding_box.height}m (D) × {importedModel.bounding_box.depth}m (H) • {importedModel.storeys.length} Storeys
              </span>
            </span>
          ) : (
            <span className="flex items-center space-x-2">
              <span className="inline-block w-2 h-2 rounded-full bg-blue-500"></span>
              <strong className="text-charcoal-700">Mode: {viewerMode.toUpperCase()}</strong>
              <span>| {params.width_m}m × {params.length_m}m × {(params.floors * params.floor_height_m).toFixed(1)}m</span>
            </span>
          )}
        </div>

        <div className="bg-white/85 backdrop-blur-xs px-2.5 py-1 rounded text-[10px] pointer-events-auto hidden sm:flex items-center space-x-1.5 border border-charcoal-200/80">
          <span className="font-semibold text-charcoal-700">
            {viewerMode === 'interior' ? 'Interior Cutaway & Navigation Active' : viewerMode === 'skeleton' ? 'Structural Skeleton View' : 'Solid Architectural Exterior'}
          </span>
          <span className="text-charcoal-400">|</span>
          <span>Click any element or room to inspect</span>
        </div>
      </div>
    </div>
  );
};
