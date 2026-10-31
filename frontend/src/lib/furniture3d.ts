import * as THREE from 'three';
import { FurnitureItem } from '../types/furniture';

/**
 * Procedural 3D Architectural Furniture Geometry Generator.
 * Constructs lightweight, high-fidelity Three.js geometry groups with realistic
 * PBR materials for isometric architectural cutaway and interior views.
 */
export class Furniture3DBuilder {
  /**
   * Builds an interactive THREE.Group representing the furniture item.
   */
  static buildFurnitureObject(item: FurnitureItem): THREE.Group {
    const group = new THREE.Group();
    group.name = item.id;
    group.userData = {
      isFurniture: true,
      furnitureId: item.id,
      roomId: item.room_id,
      storeyId: item.storey_id,
      category: item.category,
      furnitureItem: item,
    };

    const w = Math.max(0.2, item.dimensions_m.width);
    const d = Math.max(0.2, item.dimensions_m.depth);
    const h = Math.max(0.2, item.dimensions_m.height);
    const colorHex = item.color_hex || '#8b5a2b';

    // Base PBR material
    const baseMat = new THREE.MeshStandardMaterial({
      color: new THREE.Color(colorHex),
      roughness: 0.65,
      metalness: 0.1,
    });

    const fabricMat = new THREE.MeshStandardMaterial({
      color: new THREE.Color(colorHex),
      roughness: 0.85,
      metalness: 0.05,
    });

    const woodMat = new THREE.MeshStandardMaterial({
      color: new THREE.Color(colorHex),
      roughness: 0.55,
      metalness: 0.05,
    });

    const metalMat = new THREE.MeshStandardMaterial({
      color: new THREE.Color('#334155'),
      roughness: 0.35,
      metalness: 0.8,
    });

    const glassMat = new THREE.MeshStandardMaterial({
      color: new THREE.Color('#bae6fd'),
      roughness: 0.1,
      metalness: 0.1,
      transparent: true,
      opacity: 0.45,
    });

    const porcelainMat = new THREE.MeshStandardMaterial({
      color: new THREE.Color('#ffffff'),
      roughness: 0.2,
      metalness: 0.05,
    });

    switch (item.category) {
      case 'bed': {
        // Bed base
        const baseH = h * 0.35;
        const baseGeo = new THREE.BoxGeometry(w, baseH, d);
        const baseMesh = new THREE.Mesh(baseGeo, woodMat);
        baseMesh.position.y = baseH / 2;
        baseMesh.castShadow = true;
        baseMesh.receiveShadow = true;
        group.add(baseMesh);

        // Mattress
        const matH = h * 0.3;
        const matGeo = new THREE.BoxGeometry(w * 0.95, matH, d * 0.95);
        const matMesh = new THREE.Mesh(matGeo, fabricMat);
        matMesh.position.y = baseH + matH / 2;
        matMesh.castShadow = true;
        group.add(matMesh);

        // Headboard
        const headH = h * 0.95;
        const headThick = 0.12;
        const headGeo = new THREE.BoxGeometry(w, headH, headThick);
        const headMesh = new THREE.Mesh(headGeo, fabricMat);
        headMesh.position.set(0, headH / 2, -d / 2 + headThick / 2);
        headMesh.castShadow = true;
        group.add(headMesh);

        // Two Pillows
        const pilW = w * 0.38;
        const pilD = d * 0.22;
        const pilH = 0.1;
        const pilGeo = new THREE.BoxGeometry(pilW, pilH, pilD);
        const pilMat = new THREE.MeshStandardMaterial({ color: '#f8fafc', roughness: 0.9 });
        const pil1 = new THREE.Mesh(pilGeo, pilMat);
        pil1.position.set(-w * 0.25, baseH + matH + pilH / 2, -d * 0.3);
        const pil2 = new THREE.Mesh(pilGeo, pilMat);
        pil2.position.set(w * 0.25, baseH + matH + pilH / 2, -d * 0.3);
        group.add(pil1, pil2);
        break;
      }

      case 'sofa': {
        // Seat base & cushions
        const seatH = h * 0.45;
        const seatGeo = new THREE.BoxGeometry(w, seatH, d * 0.85);
        const seatMesh = new THREE.Mesh(seatGeo, fabricMat);
        seatMesh.position.set(0, seatH / 2, d * 0.05);
        seatMesh.castShadow = true;
        group.add(seatMesh);

        // Backrest
        const backH = h * 0.95;
        const backThick = d * 0.25;
        const backGeo = new THREE.BoxGeometry(w, backH, backThick);
        const backMesh = new THREE.Mesh(backGeo, fabricMat);
        backMesh.position.set(0, backH / 2, -d / 2 + backThick / 2);
        backMesh.castShadow = true;
        group.add(backMesh);

        // Armrests
        const armW = w * 0.12;
        const armH = h * 0.65;
        const armGeo = new THREE.BoxGeometry(armW, armH, d);
        const arm1 = new THREE.Mesh(armGeo, fabricMat);
        arm1.position.set(-w / 2 + armW / 2, armH / 2, 0);
        const arm2 = new THREE.Mesh(armGeo, fabricMat);
        arm2.position.set(w / 2 - armW / 2, armH / 2, 0);
        group.add(arm1, arm2);
        break;
      }

      case 'coffee_table': {
        // Tabletop
        const topH = 0.05;
        const topGeo = new THREE.BoxGeometry(w, topH, d);
        const topMesh = new THREE.Mesh(topGeo, woodMat);
        topMesh.position.y = h - topH / 2;
        topMesh.castShadow = true;
        group.add(topMesh);

        // 4 Legs
        const legR = 0.03;
        const legGeo = new THREE.CylinderGeometry(legR, legR * 0.7, h - topH, 8);
        const legMat = metalMat;
        const legOffsets = [
          [-w / 2 + 0.08, -d / 2 + 0.08],
          [w / 2 - 0.08, -d / 2 + 0.08],
          [w / 2 - 0.08, d / 2 - 0.08],
          [-w / 2 + 0.08, d / 2 - 0.08],
        ];
        legOffsets.forEach(([lx, lz]) => {
          const leg = new THREE.Mesh(legGeo, legMat);
          leg.position.set(lx, (h - topH) / 2, lz);
          group.add(leg);
        });
        break;
      }

      case 'tv_unit': {
        // Low console cabinet
        const cabGeo = new THREE.BoxGeometry(w, h * 0.85, d);
        const cabMesh = new THREE.Mesh(cabGeo, woodMat);
        cabMesh.position.y = (h * 0.85) / 2;
        cabMesh.castShadow = true;
        group.add(cabMesh);

        // TV screen on top
        const tvW = w * 0.8;
        const tvH = tvW * 0.55;
        const tvThick = 0.04;
        const tvGeo = new THREE.BoxGeometry(tvW, tvH, tvThick);
        const tvMat = new THREE.MeshStandardMaterial({ color: '#09090b', roughness: 0.2 });
        const tvMesh = new THREE.Mesh(tvGeo, tvMat);
        tvMesh.position.set(0, h * 0.85 + tvH / 2 + 0.08, 0);
        tvMesh.castShadow = true;
        group.add(tvMesh);
        break;
      }

      case 'dining_table':
      case 'meeting_table':
      case 'conference_table': {
        // Table top
        const topH = 0.06;
        const topGeo = new THREE.BoxGeometry(w, topH, d);
        const topMesh = new THREE.Mesh(topGeo, woodMat);
        topMesh.position.y = h - topH / 2;
        topMesh.castShadow = true;
        group.add(topMesh);

        // 4 Legs
        const legW = 0.06;
        const legGeo = new THREE.BoxGeometry(legW, h - topH, legW);
        const offsets = [
          [-w / 2 + 0.1, -d / 2 + 0.1],
          [w / 2 - 0.1, -d / 2 + 0.1],
          [w / 2 - 0.1, d / 2 - 0.1],
          [-w / 2 + 0.1, d / 2 - 0.1],
        ];
        offsets.forEach(([lx, lz]) => {
          const leg = new THREE.Mesh(legGeo, metalMat);
          leg.position.set(lx, (h - topH) / 2, lz);
          group.add(leg);
        });
        break;
      }

      case 'office_desk': {
        // Desktop surface
        const topH = 0.05;
        const topGeo = new THREE.BoxGeometry(w, topH, d);
        const topMesh = new THREE.Mesh(topGeo, woodMat);
        topMesh.position.y = h - topH / 2;
        topMesh.castShadow = true;
        group.add(topMesh);

        // Metal frame legs
        const legW = 0.05;
        const legGeo = new THREE.BoxGeometry(legW, h - topH, d * 0.9);
        const leg1 = new THREE.Mesh(legGeo, metalMat);
        leg1.position.set(-w / 2 + 0.06, (h - topH) / 2, 0);
        const leg2 = new THREE.Mesh(legGeo, metalMat);
        leg2.position.set(w / 2 - 0.06, (h - topH) / 2, 0);
        group.add(leg1, leg2);
        break;
      }

      case 'office_chair':
      case 'conference_chair':
      case 'dining_chair': {
        // Seat cushion
        const seatH = 0.08;
        const seatGeo = new THREE.BoxGeometry(w * 0.9, seatH, d * 0.85);
        const seatMesh = new THREE.Mesh(seatGeo, fabricMat);
        seatMesh.position.y = h * 0.45;
        seatMesh.castShadow = true;
        group.add(seatMesh);

        // Backrest
        const backH = h * 0.48;
        const backGeo = new THREE.BoxGeometry(w * 0.85, backH, 0.06);
        const backMesh = new THREE.Mesh(backGeo, fabricMat);
        backMesh.position.set(0, h * 0.45 + backH / 2, -d * 0.35);
        backMesh.castShadow = true;
        group.add(backMesh);

        // Central swivel stem / base
        const stemGeo = new THREE.CylinderGeometry(0.04, 0.04, h * 0.45, 12);
        const stemMesh = new THREE.Mesh(stemGeo, metalMat);
        stemMesh.position.y = (h * 0.45) / 2;
        group.add(stemMesh);

        // Star base
        const starGeo = new THREE.BoxGeometry(w * 0.8, 0.04, d * 0.8);
        const starMesh = new THREE.Mesh(starGeo, metalMat);
        starMesh.position.y = 0.02;
        group.add(starMesh);
        break;
      }

      case 'credenza': {
        const bodyGeo = new THREE.BoxGeometry(w, h * 0.85, d);
        const bodyMesh = new THREE.Mesh(bodyGeo, woodMat);
        bodyMesh.position.y = (h * 0.85) / 2 + 0.12;
        bodyMesh.castShadow = true;
        group.add(bodyMesh);

        // Metal base frame legs
        const legGeo = new THREE.BoxGeometry(0.04, 0.12, 0.04);
        const legOffsets = [
          [-w / 2 + 0.08, -d / 2 + 0.08],
          [w / 2 - 0.08, -d / 2 + 0.08],
          [w / 2 - 0.08, d / 2 - 0.08],
          [-w / 2 + 0.08, d / 2 - 0.08],
        ];
        legOffsets.forEach(([lx, lz]) => {
          const leg = new THREE.Mesh(legGeo, metalMat);
          leg.position.set(lx, 0.06, lz);
          group.add(leg);
        });
        break;
      }

      case 'wardrobe':
      case 'storage_cabinet': {
        const bodyGeo = new THREE.BoxGeometry(w, h, d);
        const bodyMesh = new THREE.Mesh(bodyGeo, woodMat);
        bodyMesh.position.y = h / 2;
        bodyMesh.castShadow = true;
        group.add(bodyMesh);

        // Center split line indicator
        const slitGeo = new THREE.BoxGeometry(0.01, h * 0.95, 0.02);
        const slitMat = metalMat;
        const slit = new THREE.Mesh(slitGeo, slitMat);
        slit.position.set(0, h / 2, d / 2 + 0.01);
        group.add(slit);
        break;
      }

      case 'kitchen_counter':
      case 'kitchen_island': {
        // Cabinet base
        const cabH = h * 0.92;
        const cabGeo = new THREE.BoxGeometry(w, cabH, d * 0.95);
        const cabMesh = new THREE.Mesh(cabGeo, woodMat);
        cabMesh.position.set(0, cabH / 2, -d * 0.025);
        cabMesh.castShadow = true;
        group.add(cabMesh);

        // Countertop (Stone / Quartz)
        const topH = 0.06;
        const topGeo = new THREE.BoxGeometry(w + 0.04, topH, d + 0.04);
        const topMat = new THREE.MeshStandardMaterial({ color: '#f8fafc', roughness: 0.3 });
        const topMesh = new THREE.Mesh(topGeo, topMat);
        topMesh.position.y = h - topH / 2;
        topMesh.castShadow = true;
        group.add(topMesh);
        break;
      }

      case 'toilet': {
        // Tank
        const tankW = w * 0.85;
        const tankH = h * 0.45;
        const tankD = d * 0.35;
        const tankGeo = new THREE.BoxGeometry(tankW, tankH, tankD);
        const tankMesh = new THREE.Mesh(tankGeo, porcelainMat);
        tankMesh.position.set(0, h - tankH / 2, -d / 2 + tankD / 2);
        group.add(tankMesh);

        // Bowl
        const bowlH = h * 0.55;
        const bowlGeo = new THREE.BoxGeometry(w * 0.8, bowlH, d * 0.7);
        const bowlMesh = new THREE.Mesh(bowlGeo, porcelainMat);
        bowlMesh.position.set(0, bowlH / 2, d * 0.1);
        group.add(bowlMesh);
        break;
      }

      case 'washbasin': {
        // Vanity Base
        const vanH = h * 0.75;
        const vanGeo = new THREE.BoxGeometry(w, vanH, d);
        const vanMesh = new THREE.Mesh(vanGeo, woodMat);
        vanMesh.position.set(0, h - vanH / 2, 0);
        group.add(vanMesh);

        // Sink Bowl
        const sinkGeo = new THREE.BoxGeometry(w * 0.7, 0.15, d * 0.6);
        const sinkMesh = new THREE.Mesh(sinkGeo, porcelainMat);
        sinkMesh.position.set(0, h + 0.075, 0);
        group.add(sinkMesh);
        break;
      }

      case 'shower': {
        // Glass cubicle panels
        const panelGeo = new THREE.BoxGeometry(w, h, d);
        const panelMesh = new THREE.Mesh(panelGeo, glassMat);
        panelMesh.position.y = h / 2;
        group.add(panelMesh);
        break;
      }

      case 'refrigerator': {
        const frGeo = new THREE.BoxGeometry(w, h, d);
        const frMat = new THREE.MeshStandardMaterial({ color: '#cbd5e1', roughness: 0.35, metalness: 0.6 });
        const frMesh = new THREE.Mesh(frGeo, frMat);
        frMesh.position.y = h / 2;
        frMesh.castShadow = true;
        group.add(frMesh);
        break;
      }

      case 'presentation_screen': {
        // Flat screen panel
        const scrGeo = new THREE.BoxGeometry(w, h, 0.06);
        const scrMat = new THREE.MeshStandardMaterial({ color: '#09090b', roughness: 0.1, metalness: 0.9 });
        const scrMesh = new THREE.Mesh(scrGeo, scrMat);
        scrMesh.position.y = h / 2;
        group.add(scrMesh);
        break;
      }

      default: {
        // Generic architectural block
        const genGeo = new THREE.BoxGeometry(w, h, d);
        const genMesh = new THREE.Mesh(genGeo, baseMat);
        genMesh.position.y = h / 2;
        genMesh.castShadow = true;
        group.add(genMesh);
        break;
      }
    }

    // Apply translation and rotation
    group.position.set(item.position_m.x, item.position_m.y, item.position_m.z);
    group.rotation.y = (item.rotation_deg * Math.PI) / 180;
    if (item.scale) {
      group.scale.set(item.scale[0], item.scale[1], item.scale[2]);
    }
    group.visible = item.is_visible !== false;

    return group;
  }
}
