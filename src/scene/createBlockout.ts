import {
  CircleGeometry,
  Group,
  Mesh,
} from 'three';
import type { BufferGeometry } from 'three';
import { layoutConfig } from '../config/layout';
import { pavingMoss } from '../config/pavingMoss';
import { stoneConfig } from '../config/stone';
import { createPavingMossGeometry } from '../geometry/createPavingMossGeometry';
import { createStoneBlockGeometry, createStonePrismGeometry } from '../geometry/createStoneBlockGeometry';
import type { StoneGeometryOptions } from '../geometry/createStoneBlockGeometry';
import { createStoneMaterial } from '../materials/createStoneMaterial';
import { createWaterMaterial } from '../materials/createWaterMaterial';
import type { WaterState } from '../materials/createWaterMaterial';
import { pathStones } from './pathLayout';
import { createMasonryPillar } from './createMasonryPillar';
import { createPoolMasonry } from './createPoolMasonry';
import { createPoolStoneDetail } from './createPoolStoneDetail';

/** Approved composition with shared, deterministic low-poly stone details. */
export function createBlockout(waterState?: WaterState) {
  const root = new Group();
  root.name = 'courtyard-blockout';
  const geometries = new Set<BufferGeometry>();
  function own<T extends BufferGeometry>(geometry: T): T {
    geometries.add(geometry);
    return geometry;
  }

  const blockGeometries = new Map<string, BufferGeometry>();
  const stoneMaterial = createStoneMaterial();
  const exposedStone = createStoneMaterial({ top: '#557282', side: '#637E8B', shade: '#36546A' });
  const mossMaterial = createStoneMaterial({ top: '#FFFFFF', side: '#E5EBDC', shade: '#88A29A' });
  mossMaterial.name = 'courtyard-stone-moss';
  mossMaterial.vertexColors = true;
  const waterMaterial = createWaterMaterial(waterState);

  function box(parent: Group, name: string, width: number, height: number, depth: number, bottom: number, x = 0, z = 0, options: Partial<StoneGeometryOptions> = {}) {
    const style = { bevel: stoneConfig.bevel, cornerCut: stoneConfig.cornerCut, seed: 11, ...options };
    const key = JSON.stringify([width, height, depth, style]);
    let geometry = blockGeometries.get(key);
    if (!geometry) {
      geometry = own(createStoneBlockGeometry(width, height, depth, style));
      blockGeometries.set(key, geometry);
    }
    const mesh = new Mesh(geometry, stoneMaterial);
    mesh.name = name;
    mesh.position.set(x, bottom + height / 2, z);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    parent.add(mesh);
    return mesh;
  }

  const f = layoutConfig.fountain;
  const fountain = new Group();
  fountain.name = 'fountain';
  fountain.position.set(...f.position);
  fountain.rotation.y = f.rotationY;
  root.add(fountain);
  createPoolMasonry(fountain, stoneMaterial, own);

  const water = new Mesh(own(new CircleGeometry(f.innerRadius, 8)), waterMaterial);
  water.name = 'fountain-water';
  water.rotation.x = -Math.PI / 2;
  water.position.y = f.waterHeight;
  water.receiveShadow = true;
  fountain.add(water);

  createPoolStoneDetail(fountain, stoneMaterial, mossMaterial, own);

  layoutConfig.columns.forEach((placement, index) => {
    root.add(createMasonryPillar(placement, index, { stone: stoneMaterial, exposedStone, moss: mossMaterial }, own));
  });

  const w = layoutConfig.wall;
  const wall = new Group();
  wall.name = 'wallLeft';
  wall.position.set(...w.position);
  wall.rotation.y = w.rotationY;
  box(wall, 'wallLeft-base', w.length + w.endSize, w.baseHeight, w.baseDepth, 0);
  const body = new Group();
  body.name = 'wallLeft-body';
  wall.add(body);
  const bodyCount = stoneConfig.wall.bodyBlocks;
  const joint = stoneConfig.joints.width;
  const bodyWidth = (w.length - (bodyCount - 1) * joint) / bodyCount;
  for (let i = 0; i < bodyCount; i++) {
    const x = -w.length / 2 + bodyWidth / 2 + i * (bodyWidth + joint);
    box(body, `wallLeft-body-${i}`, bodyWidth, w.height, w.depth, w.baseHeight, x, 0,
      { seed: 11 + i * 18, chipSize: i === bodyCount - 1 ? 0.075 : 0, chipCorner: 2 });
    if (i < bodyCount - 1) {
      box(body, `wallLeft-body-joint-${i}`, joint, w.height, w.depth - stoneConfig.joints.recess * 2,
        w.baseHeight, x + bodyWidth / 2 + joint / 2, 0, { bevel: 0, cornerCut: 0, seed: 47 });
    }
  }
  const cap = new Group();
  cap.name = 'wallLeft-cap';
  wall.add(cap);
  const capCount = stoneConfig.wall.capBlocks;
  const capWidth = (w.length - (capCount - 1) * joint) / capCount;
  for (let i = 0; i < capCount; i++) {
    const x = -w.length / 2 + capWidth / 2 + i * (capWidth + joint);
    box(cap, `wallLeft-cap-${i}`, capWidth, w.capHeight, w.capDepth, w.baseHeight + w.height, x, 0,
      { bevel: 0.018, seed: 29 + i * 18, chipSize: i === capCount - 1 ? 0.065 : 0, chipCorner: 2 });
    if (i < capCount - 1) {
      box(cap, `wallLeft-cap-joint-${i}`, joint, w.capHeight * 0.65, w.capDepth - stoneConfig.joints.recess * 2,
        w.baseHeight + w.height, x + capWidth / 2 + joint / 2, 0, { bevel: 0, cornerCut: 0, seed: 47 });
    }
  }
  box(wall, 'wallLeft-end', w.endSize, w.endHeight, w.endSize, w.baseHeight, w.length / 2, 0,
    { chipSize: 0.095, chipCorner: 2, seed: 29 });
  root.add(wall);

  const p = layoutConfig.path;
  const path = new Group();
  path.name = 'pathRight';
  path.position.set(...p.position);
  path.rotation.y = p.rotationY;
  pathStones.forEach((stone, index) => {
    const { outline, profile } = stone;
    const { exposedHeight: top, embeddedDepth, bevel, chipVertex, chipSize } = profile;
    const bottom = -embeddedDepth;
    const geometry = own(createStonePrismGeometry(outline, top - bottom, {
      bevel,
      cornerCut: 0,
      seed: 11 + 9 * index,
      // The prism builder reverses the XZ outline to wind its top face.
      chipCorner: outline.length - 1 - chipVertex,
      chipSize,
    }));
    const slab = new Mesh(geometry, stoneMaterial);
    slab.name = `pathRight-slab-${stone.id}`;
    slab.position.set(stone.center[0], (top + bottom) / 2, stone.center[1]);
    slab.rotation.y = stone.rotationY;
    slab.castShadow = true;
    slab.receiveShadow = true;
    path.add(slab);
    const mossPatch = pavingMoss[stone.id];
    const mossGeometry = mossPatch && createPavingMossGeometry(geometry, mossPatch);
    if (mossGeometry) {
      const moss = new Mesh(own(mossGeometry), mossMaterial);
      moss.name = `pathRight-moss-${stone.id}`;
      moss.castShadow = true;
      moss.receiveShadow = true;
      slab.add(moss);
    }
  });
  root.add(path);

  let disposed = false;
  return {
    root,
    dispose() {
      if (disposed) return;
      disposed = true;
      root.removeFromParent();
      root.clear();
      for (const geometry of geometries) geometry.dispose();
      stoneMaterial.dispose();
      exposedStone.dispose();
      mossMaterial.dispose();
      waterMaterial.dispose();
    },
  };
}
