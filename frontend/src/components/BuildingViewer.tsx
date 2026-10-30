import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { BuildingParams, InterventionId } from '../types/building';
import { BuildingModelDetail, BuildingElement } from '../types/digital_twin';
import { RotateCw, Maximize2, Layers, X } from 'lucide-react';

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
  const [wireframeMode, setWireframeMode] = useState(false);

  // Active interventions to show (parametric mode)
  const activeInterventions: InterventionId[] = (showInterventions && !isBaseline)
    ? params.selected_interventions
    : [];

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
    controls.maxPolarAngle = Math.PI / 2 - 0.02;
    controls.minDistance = 2;
    controls.maxDistance = 350;
    controls.target.set(0, 5, 0);
    controlsRef.current = controls;

    // 5. Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
    scene.add(ambientLight);

    const hemiLight = new THREE.HemisphereLight(0xffffff, 0xdfe2e5, 0.4);
    hemiLight.position.set(0, 50, 0);
    scene.add(hemiLight);

    const sunLight = new THREE.DirectionalLight(0xfffbf2, 1.2);
    sunLight.position.set(40, 60, 30);
    sunLight.castShadow = true;
    sunLight.shadow.mapSize.width = 1024;
    sunLight.shadow.mapSize.height = 1024;
    sunLight.shadow.camera.near = 10;
    sunLight.shadow.camera.far = 180;
    const d = 50;
    sunLight.shadow.camera.left = -d;
    sunLight.shadow.camera.right = d;
    sunLight.shadow.camera.top = d;
    sunLight.shadow.camera.bottom = -d;
    sunLight.shadow.bias = -0.0005;
    scene.add(sunLight);
    sunLightRef.current = sunLight;

    // 6. Ground Plane with subtle grid
    const groundGeo = new THREE.PlaneGeometry(200, 200);
    const groundMat = new THREE.MeshStandardMaterial({
      color: 0xebedf0,
      roughness: 0.9,
      metalness: 0.05,
    });
    const ground = new THREE.Mesh(groundGeo, groundMat);
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.02;
    ground.receiveShadow = true;
    scene.add(ground);
    groundRef.current = ground;

    const gridHelper = new THREE.GridHelper(120, 60, 0xb0b8c1, 0xd0d7de);
    gridHelper.position.y = 0.0;
    scene.add(gridHelper);
    gridHelperRef.current = gridHelper;

    // 7. Group for building geometry
    const buildingGroup = new THREE.Group();
    scene.add(buildingGroup);
    buildingGroupRef.current = buildingGroup;

    // 8. Animation loop
    const animate = () => {
      animFrameIdRef.current = requestAnimationFrame(animate);
      if (controlsRef.current) {
        controlsRef.current.autoRotate = isRotating;
        controlsRef.current.autoRotateSpeed = 1.5;
        controlsRef.current.update();
      }
      renderer.render(scene, camera);
    };
    animate();

    // 9. Resize Observer
    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        if (width > 0 && height > 0 && cameraRef.current && rendererRef.current) {
          cameraRef.current.aspect = width / height;
          cameraRef.current.updateProjectionMatrix();
          rendererRef.current.setSize(width, height);
        }
      }
    });
    resizeObserver.observe(container);

    // 10. Pointer click listener for Raycasting element selection
    const handleCanvasClick = (event: MouseEvent) => {
      if (!onSelectElement || !cameraRef.current || !buildingGroupRef.current) return;
      const rect = renderer.domElement.getBoundingClientRect();
      mouseRef.current.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouseRef.current.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      raycasterRef.current.setFromCamera(mouseRef.current, cameraRef.current);
      const intersects = raycasterRef.current.intersectObjects(buildingGroupRef.current.children, true);

      if (intersects.length > 0) {
        let hitObj: THREE.Object3D | null = intersects[0].object;
        while (hitObj && hitObj !== buildingGroupRef.current) {
          if (hitObj.userData && hitObj.userData.element) {
            onSelectElement(hitObj.userData.element as BuildingElement);
            return;
          }
          hitObj = hitObj.parent;
        }
      }
      onSelectElement(null);
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
      // In IFC coordinates: X is width, Y is plan depth, Z is elevation/height
      // In Three.js with ifcGroup rotated by -90deg on X:
      // Three.js X = IFC X (width: b.width)
      // Three.js Y = IFC Z (height: b.depth)
      // Three.js Z = -IFC Y (plan depth: b.height)
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

  // Rebuild building geometry whenever importedModel, parameters, filters, or selected element change
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

      // Group containing all IFC elements with coordinate conversion
      const ifcGroup = new THREE.Group();
      ifcGroup.name = 'ifcModelGroup';

      // 1. Convert IFC Z-up to Three.js Y-up by rotating -90 deg around X-axis
      // Maps: IFC X -> Three.js X (Width)
      //       IFC Y -> Three.js -Z (Depth)
      //       IFC Z -> Three.js Y (Height / Elevation)
      ifcGroup.rotation.x = -Math.PI / 2;

      // 2. Position ifcGroup so the building is horizontally centered at (0, 0)
      // and its lowest elevation (min_z) sits at ground level Y = 0
      if (bounding_box) {
        ifcGroup.position.set(
          -bounding_box.center_x,
          -bounding_box.min_z,
          bounding_box.center_y
        );

        // Adapt environment grid & shadow frustum to building dimensions
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
        // 1. Filter by element type
        if (visibleTypes && visibleTypes.length > 0 && !visibleTypes.includes(elem.element_type)) {
          return;
        }

        // 2. Filter by storey
        if (selectedStoreyId && elem.storey_id && elem.storey_id !== selectedStoreyId) {
          return;
        }

        // 3. Render real triangulated geometry if available
        if (elem.geometry && elem.geometry.vertices && elem.geometry.vertices.length >= 9 && elem.geometry.faces) {
          const geom = new THREE.BufferGeometry();
          geom.setAttribute('position', new THREE.Float32BufferAttribute(elem.geometry.vertices, 3));
          geom.setIndex(elem.geometry.faces);
          geom.computeVertexNormals();

          const style = ELEMENT_COLOR_MAP[elem.element_type] || { color: 0x0d9488, roughness: 0.6 };
          const isSelected = elem.element_id === selectedElementId;
          const isHighlighted = Boolean(highlightedElementIds && highlightedElementIds.includes(elem.element_id));

          let elemColor = style.color;
          let elemEmissive = 0x000000;
          let elemEmissiveIntensity = 0.0;
          let elemOpacity = style.opacity !== undefined ? style.opacity : 1.0;
          let elemTransparent = style.transparent || false;

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
          } else if (isSelected) {
            elemColor = 0xf59e0b;
            elemEmissive = 0xd97706;
            elemEmissiveIntensity = 0.5;
            elemTransparent = false;
            elemOpacity = 1.0;
          }

          const material = new THREE.MeshStandardMaterial({
            color: elemColor,
            roughness: style.roughness || 0.6,
            metalness: style.metalness || 0.1,
            transparent: elemTransparent,
            opacity: elemOpacity,
            wireframe: wireframeMode,
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
          const isSelected = elem.element_id === selectedElementId;
          const isHighlighted = Boolean(highlightedElementIds && highlightedElementIds.includes(elem.element_id));

          let boxColor = 0xa1a1aa;
          let boxEmissive = 0x000000;
          let boxEmissiveIntensity = 0.0;

          if (isHighlighted) {
            if (highlightSeverity === 'High') {
              boxColor = 0xf43f5e;
              boxEmissive = 0xe11d48;
              boxEmissiveIntensity = 0.7;
            } else if (highlightSeverity === 'Warning') {
              boxColor = 0xf59e0b;
              boxEmissive = 0xd97706;
              boxEmissiveIntensity = 0.6;
            } else {
              boxColor = 0x0284c7;
              boxEmissive = 0x0369a1;
              boxEmissiveIntensity = 0.5;
            }
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

      // Auto-fit camera framing to the imported IFC digital twin
      fitCameraToModel(true, false);
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

    const { width_m, length_m, floor_height_m, floors, window_count } = params;
    if (width_m <= 0 || length_m <= 0 || floor_height_m <= 0 || floors <= 0) return;

    const totalHeight = floors * floor_height_m;
    const hasShading = activeInterventions.includes('external_shading');
    const hasReflectiveRoof = activeInterventions.includes('reflective_roof');
    const hasRoofInsulation = activeInterventions.includes('roof_insulation');
    const hasSolar = activeInterventions.includes('solar_pv');

    // Plinth
    const plinthHeight = 0.3;
    const plinthGeo = new THREE.BoxGeometry(width_m + 0.6, plinthHeight, length_m + 0.6);
    const plinthMat = new THREE.MeshStandardMaterial({ color: 0x5a626d, roughness: 0.8, wireframe: wireframeMode });
    const plinth = new THREE.Mesh(plinthGeo, plinthMat);
    plinth.position.set(0, plinthHeight / 2, 0);
    plinth.receiveShadow = true;
    buildingGroup.add(plinth);

    // Floor Slabs & Exterior Wall Mass
    const slabThickness = 0.25;
    const wallMat = new THREE.MeshStandardMaterial({ color: 0xf0f2f5, roughness: 0.65, metalness: 0.05, wireframe: wireframeMode });
    const slabMat = new THREE.MeshStandardMaterial({ color: 0xd5d9df, roughness: 0.75, wireframe: wireframeMode });

    for (let f = 0; f < floors; f++) {
      const floorBaseY = plinthHeight + f * floor_height_m;
      const wallHeight = floor_height_m - slabThickness;
      const floorGeo = new THREE.BoxGeometry(width_m, wallHeight, length_m);
      const floorMesh = new THREE.Mesh(floorGeo, wallMat);
      floorMesh.position.set(0, floorBaseY + wallHeight / 2, 0);
      floorMesh.castShadow = true;
      floorMesh.receiveShadow = true;
      buildingGroup.add(floorMesh);

      const slabGeo = new THREE.BoxGeometry(width_m + 0.2, slabThickness, length_m + 0.2);
      const slabMesh = new THREE.Mesh(slabGeo, slabMat);
      slabMesh.position.set(0, floorBaseY + wallHeight + slabThickness / 2, 0);
      slabMesh.castShadow = true;
      slabMesh.receiveShadow = true;
      buildingGroup.add(slabMesh);
    }

    // Roof & Parapets
    const roofTopY = plinthHeight + totalHeight;
    const parapetHeight = 0.8;
    const parapetThickness = 0.3;

    const roofMaterial = new THREE.MeshStandardMaterial({
      color: hasReflectiveRoof ? 0xfdfdfd : 0x484f58,
      roughness: hasReflectiveRoof ? 0.15 : 0.9,
      metalness: hasReflectiveRoof ? 0.3 : 0.05,
      wireframe: wireframeMode,
    });
    const roofDeckGeo = new THREE.BoxGeometry(width_m, 0.1, length_m);
    const roofDeckMesh = new THREE.Mesh(roofDeckGeo, roofMaterial);
    roofDeckMesh.position.set(0, roofTopY + 0.05, 0);
    roofDeckMesh.receiveShadow = true;
    buildingGroup.add(roofDeckMesh);

    // Parapet
    const parapetMat = new THREE.MeshStandardMaterial({ color: 0xd8dde3, roughness: 0.7, wireframe: wireframeMode });
    const pFrontGeo = new THREE.BoxGeometry(width_m + 0.2, parapetHeight, parapetThickness);
    const pFront = new THREE.Mesh(pFrontGeo, parapetMat);
    pFront.position.set(0, roofTopY + parapetHeight / 2, length_m / 2 + parapetThickness / 2);
    pFront.castShadow = true;
    buildingGroup.add(pFront);

    const pBack = pFront.clone();
    pBack.position.set(0, roofTopY + parapetHeight / 2, -length_m / 2 - parapetThickness / 2);
    buildingGroup.add(pBack);

    const pSideGeo = new THREE.BoxGeometry(parapetThickness, parapetHeight, length_m);
    const pLeft = new THREE.Mesh(pSideGeo, parapetMat);
    pLeft.position.set(-width_m / 2 - parapetThickness / 2, roofTopY + parapetHeight / 2, 0);
    pLeft.castShadow = true;
    buildingGroup.add(pLeft);

    const pRight = pLeft.clone();
    pRight.position.set(width_m / 2 + parapetThickness / 2, roofTopY + parapetHeight / 2, 0);
    buildingGroup.add(pRight);

    // Roof Insulation
    if (hasRoofInsulation) {
      const insulThickness = 0.25;
      const insulGeo = new THREE.BoxGeometry(width_m - 0.2, insulThickness, length_m - 0.2);
      const insulMat = new THREE.MeshStandardMaterial({
        color: 0x3b82f6,
        roughness: 0.4,
        transparent: true,
        opacity: 0.85,
        wireframe: wireframeMode,
      });
      const insulMesh = new THREE.Mesh(insulGeo, insulMat);
      insulMesh.position.set(0, roofTopY + insulThickness / 2 + 0.05, 0);
      insulMesh.castShadow = true;
      buildingGroup.add(insulMesh);
    }

    // Windows & Shading Louvers
    if (window_count > 0) {
      const windowWidth = 1.4;
      const windowHeight = 1.8;
      const windowDepth = 0.08;
      const windowGlassMat = new THREE.MeshStandardMaterial({ color: 0x223545, roughness: 0.1, metalness: 0.85, wireframe: wireframeMode });
      const frameMat = new THREE.MeshStandardMaterial({ color: 0x2b3038, roughness: 0.5, wireframe: wireframeMode });
      const louverMat = new THREE.MeshStandardMaterial({ color: 0xa87747, roughness: 0.4, metalness: 0.2, wireframe: wireframeMode });

      const windowsPerFloor = Math.ceil(window_count / floors);
      let placedCount = 0;

      for (let f = 0; f < floors && placedCount < window_count; f++) {
        const floorCenterY = plinthHeight + f * floor_height_m + floor_height_m / 2;
        const currentFloorTarget = Math.min(windowsPerFloor, window_count - placedCount);

        for (let w = 0; w < currentFloorTarget && placedCount < window_count; w++) {
          const side = w % 4;
          const sideSlot = Math.floor(w / 4);
          const slotsOnSide = Math.max(1, Math.ceil(currentFloorTarget / 4));
          const offsetRatio = (sideSlot + 1) / (slotsOnSide + 1) - 0.5;

          const winGroup = new THREE.Group();
          const glassGeo = new THREE.BoxGeometry(windowWidth, windowHeight, windowDepth);
          const glassMesh = new THREE.Mesh(glassGeo, windowGlassMat);
          winGroup.add(glassMesh);

          const frameGeo = new THREE.BoxGeometry(windowWidth + 0.15, windowHeight + 0.15, windowDepth * 0.8);
          const frameMesh = new THREE.Mesh(frameGeo, frameMat);
          frameMesh.position.z = -0.01;
          winGroup.add(frameMesh);

          if (hasShading) {
            const hoodGeo = new THREE.BoxGeometry(windowWidth + 0.35, 0.08, 0.65);
            const hoodMesh = new THREE.Mesh(hoodGeo, louverMat);
            hoodMesh.position.set(0, windowHeight / 2 + 0.12, 0.32);
            hoodMesh.castShadow = true;
            winGroup.add(hoodMesh);

            for (let l = 0; l < 3; l++) {
              const louverGeo = new THREE.BoxGeometry(windowWidth + 0.2, 0.04, 0.35);
              const lMesh = new THREE.Mesh(louverGeo, louverMat);
              const lY = windowHeight / 2 - 0.2 - l * (windowHeight / 3.2);
              lMesh.position.set(0, lY, 0.2);
              lMesh.rotation.x = 0.35;
              lMesh.castShadow = true;
              winGroup.add(lMesh);
            }
          }

          if (side === 0) {
            winGroup.position.set(offsetRatio * (width_m * 0.8), floorCenterY, length_m / 2 + windowDepth / 2);
          } else if (side === 1) {
            winGroup.position.set(width_m / 2 + windowDepth / 2, floorCenterY, offsetRatio * (length_m * 0.8));
            winGroup.rotation.y = Math.PI / 2;
          } else if (side === 2) {
            winGroup.position.set(-offsetRatio * (width_m * 0.8), floorCenterY, -length_m / 2 - windowDepth / 2);
            winGroup.rotation.y = Math.PI;
          } else {
            winGroup.position.set(-width_m / 2 - windowDepth / 2, floorCenterY, -offsetRatio * (length_m * 0.8));
            winGroup.rotation.y = -Math.PI / 2;
          }

          buildingGroup.add(winGroup);
          placedCount++;
        }
      }
    }

    // Solar PV Array
    if (hasSolar) {
      const panelWidth = 1.1;
      const panelLength = 1.9;
      const panelTilt = 0.35;
      const usableWidth = width_m * 0.75;
      const usableLength = length_m * 0.75;
      const cols = Math.max(1, Math.floor(usableWidth / (panelWidth + 0.4)));
      const rows = Math.max(1, Math.floor(usableLength / (panelLength + 0.7)));

      const panelMat = new THREE.MeshStandardMaterial({ color: 0x14223b, roughness: 0.15, metalness: 0.8, wireframe: wireframeMode });
      const pvBaseY = roofTopY + (hasRoofInsulation ? 0.35 : 0.1);

      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          const pvGroup = new THREE.Group();
          const panelGeo = new THREE.BoxGeometry(panelWidth, 0.04, panelLength);
          const panelMesh = new THREE.Mesh(panelGeo, panelMat);
          panelMesh.rotation.x = panelTilt;
          panelMesh.castShadow = true;
          pvGroup.add(panelMesh);

          const startX = -((cols - 1) * (panelWidth + 0.4)) / 2;
          const startZ = -((rows - 1) * (panelLength + 0.7)) / 2;
          pvGroup.position.set(startX + c * (panelWidth + 0.4), pvBaseY + 0.4, startZ + r * (panelLength + 0.7));
          buildingGroup.add(pvGroup);
        }
      }
    }

    // Auto-fit camera framing for parametric model if mode switched
    fitCameraToModel(false, false);
  }, [params, activeInterventions, wireframeMode, importedModel, visibleTypes, selectedStoreyId, selectedElementId, highlightedElementIds, highlightSeverity]);

  // Camera Reset / Fit to Model
  const handleResetCamera = () => {
    fitCameraToModel(isDigitalTwinMode, true);
  };

  const isDigitalTwinMode = Boolean(importedModel && importedModel.elements && importedModel.elements.length > 0);

  return (
    <div className={`relative flex flex-col bg-charcoal-50 rounded-xl border border-charcoal-200 overflow-hidden shadow-sm ${className}`}>
      {/* Top Header Controls Bar */}
      <div className="absolute top-3 left-3 right-3 z-10 flex items-center justify-between pointer-events-none">
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
          {isDigitalTwinMode ? (
            <div className="flex items-center space-x-1.5">
              <span className="px-2.5 py-0.5 rounded-full text-xs bg-emerald-800 text-white font-medium shadow-xs flex items-center space-x-1">
                <span>{importedModel?.total_element_count} IFC Elements</span>
              </span>
              <span className="px-2 py-0.5 rounded-full text-[11px] bg-stone-100 text-stone-700 font-mono border border-stone-300 hidden md:inline-block">
                {importedModel?.schema_version || 'IFC'}
              </span>
            </div>
          ) : activeInterventions.length > 0 && !isBaseline && (
            <span className="px-2 py-0.5 rounded-full text-xs bg-charcoal-900 text-white font-medium shadow-xs">
              {activeInterventions.length} active upgrade{activeInterventions.length > 1 ? 's' : ''}
            </span>
          )}
        </div>

        {/* Viewport Control Buttons */}
        <div className="flex items-center space-x-1.5 bg-white/90 backdrop-blur-xs p-1 rounded-lg border border-charcoal-200 shadow-xs pointer-events-auto">
          {(selectedElementId || (highlightedElementIds && highlightedElementIds.length > 0)) && (
            <button
              onClick={() => {
                onSelectElement?.(null);
                onClearHighlight?.();
              }}
              title="Clear selected element & highlights"
              className="px-2 py-1 rounded bg-rose-50 text-rose-700 hover:bg-rose-100 border border-rose-200 text-xs font-semibold flex items-center space-x-1 transition-colors"
            >
              <X className="w-3.5 h-3.5" />
              <span>Clear Highlight</span>
            </button>
          )}
          <button
            onClick={() => setIsRotating(!isRotating)}
            title={isRotating ? 'Pause rotation' : 'Auto-rotate'}
            className={`p-1.5 rounded hover:bg-charcoal-100 transition-colors text-charcoal-700 ${
              isRotating ? 'bg-charcoal-200 text-charcoal-900' : ''
            }`}
          >
            <RotateCw className="w-4 h-4" />
          </button>
          <button
            onClick={() => setWireframeMode(!wireframeMode)}
            title={wireframeMode ? 'Solid shaded mode' : 'Wireframe structure mode'}
            className={`p-1.5 rounded hover:bg-charcoal-100 transition-colors text-charcoal-700 ${
              wireframeMode ? 'bg-charcoal-200 text-charcoal-900' : ''
            }`}
          >
            <Layers className="w-4 h-4" />
          </button>
          <button
            onClick={handleResetCamera}
            title="Fit to model / Reset camera"
            className="p-1.5 rounded hover:bg-charcoal-100 transition-colors text-charcoal-700"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* 3D Canvas Container */}
      <div
        ref={containerRef}
        className="w-full h-full min-h-[380px] cursor-grab active:cursor-grabbing focus:outline-none"
        tabIndex={0}
        aria-label="Interactive 3D building digital twin viewer"
      />

      {/* Bottom Architectural Scale & Guidance Badge */}
      <div className="absolute bottom-3 left-3 right-3 z-10 flex items-center justify-between text-[11px] text-charcoal-500 pointer-events-none px-2">
        <div className="bg-white/85 backdrop-blur-xs px-2.5 py-1 rounded border border-charcoal-200/80 pointer-events-auto">
          {isDigitalTwinMode && importedModel?.bounding_box ? (
            <span className="flex items-center space-x-2">
              <span className="inline-block w-2 h-2 rounded-full bg-emerald-500"></span>
              <strong className="text-charcoal-700">Imported IFC Twin:</strong>
              <span>
                {importedModel.bounding_box.width}m (W) × {importedModel.bounding_box.height}m (D) × {importedModel.bounding_box.depth}m (H) | {importedModel.storeys.length} Storeys | {importedModel.total_element_count} Elements
              </span>
            </span>
          ) : (
            <span className="flex items-center space-x-2">
              <span className="inline-block w-2 h-2 rounded-full bg-blue-500"></span>
              <strong className="text-charcoal-700">Parametric Massing:</strong>
              <span>
                {params.width_m}m × {params.length_m}m × {(params.floors * params.floor_height_m).toFixed(1)}m | {params.floors} Fl | {params.window_count} Win
              </span>
            </span>
          )}
        </div>
        <div className="bg-white/85 backdrop-blur-xs px-2.5 py-1 rounded text-[10px] pointer-events-auto hidden sm:flex items-center space-x-1.5 border border-charcoal-200/80">
          <span className="font-semibold text-charcoal-700">
            {isDigitalTwinMode ? 'Source: Real IFC Mesh (IfcOpenShell)' : 'Source: Procedural Three.js Synthesis'}
          </span>
          <span className="text-charcoal-400">|</span>
          <span>{isDigitalTwinMode ? 'Click any element to inspect properties' : 'Click & drag to rotate | Scroll to zoom'}</span>
        </div>
      </div>
    </div>
  );
};
