import {
  CircleGeometry,
  ExtrudeGeometry,
  Group,
  Mesh,
  Path,
  Shape,
} from 'three';
import type { BufferGeometry } from 'three';
import { layoutConfig } from '../config/layout';
import { stoneConfig } from '../config/stone';
import { applyStoneTint, createStoneBlockGeometry, createStonePrismGeometry } from '../geometry/createStoneBlockGeometry';
import type { StoneGeometryOptions } from '../geometry/createStoneBlockGeometry';
import { createStoneMaterial } from '../materials/createStoneMaterial';
import { createWaterMaterial } from '../materials/createWaterMaterial';
import type { WaterState } from '../materials/createWaterMaterial';

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

  const base = new Mesh(
    own(createStonePrismGeometry(
      Array.from({ length: 8 }, (_, i): [number, number] => [Math.cos(i * Math.PI / 4) * f.baseRadius, -Math.sin(i * Math.PI / 4) * f.baseRadius]),
      f.baseHeight,
      { bevel: 0.018, cornerCut: 0.025, seed: 11 },
    )),
    stoneMaterial,
  );
  base.name = 'fountain-base';
  base.position.y = f.baseHeight / 2;
  base.castShadow = true;
  base.receiveShadow = true;
  fountain.add(base);

  // An actual hole leaves the lower water plane and inner wall visible.
  const outline = new Shape();
  const hole = new Path();
  for (let i = 0; i < 8; i++) {
    const angle = i * Math.PI / 4;
    const innerAngle = -angle;
    const x = Math.cos(angle) * f.outerRadius;
    const y = Math.sin(angle) * f.outerRadius;
    const innerX = Math.cos(innerAngle) * f.innerRadius;
    const innerY = Math.sin(innerAngle) * f.innerRadius;
    if (i === 0) {
      outline.moveTo(x, y);
      hole.moveTo(innerX, innerY);
    } else {
      outline.lineTo(x, y);
      hole.lineTo(innerX, innerY);
    }
  }
  outline.closePath();
  hole.closePath();
  outline.holes.push(hole);
  const rim = new Group();
  rim.name = 'fountain-rim';
  rim.position.y = f.baseHeight;
  fountain.add(rim);
  const coping = stoneConfig.fountain;
  const coreHeight = f.rimHeight - coping.copingHeight;
  // The continuous wall reaches above the water; coping joints cannot leak through it.
  const core = new Mesh(
    own(applyStoneTint(new ExtrudeGeometry(outline, { depth: coreHeight, bevelEnabled: false, steps: 1, curveSegments: 1 }), 11)),
    stoneMaterial,
  );
  core.name = 'fountain-rim-wall';
  core.rotation.x = -Math.PI / 2;
  core.castShadow = true;
  core.receiveShadow = true;
  rim.add(core);

  function trimmedEdge(radius: number): [[number, number], [number, number]] {
    const endX = Math.cos(Math.PI / 4) * radius;
    const endZ = -Math.sin(Math.PI / 4) * radius;
    const t = coping.jointWidth / (2 * Math.hypot(endX - radius, endZ));
    return [[radius + (endX - radius) * t, endZ * t], [endX + (radius - endX) * t, endZ * (1 - t)]];
  }
  const [outerA, outerB] = trimmedEdge(f.outerRadius);
  const [innerA, innerB] = trimmedEdge(f.innerRadius);
  const copingGeometries = new Map<string, BufferGeometry>();
  for (let i = 0; i < 8; i++) {
    const chipped = coping.chippedSegments.some(index => index === i);
    const variant = chipped ? `chip-${i % 2}` : `plain-${i % 2}`;
    let geometry = copingGeometries.get(variant);
    if (!geometry) {
      geometry = own(createStonePrismGeometry([outerA, outerB, innerB, innerA], coping.copingHeight, {
        bevel: coping.bevel,
        cornerCut: 0.025,
        seed: 29 + i % 2,
        chipSize: chipped ? coping.chipSize : 0,
        chipCorner: i % 2,
      }));
      copingGeometries.set(variant, geometry);
    }
    const segment = new Mesh(geometry, stoneMaterial);
    segment.name = `fountain-coping-${i}`;
    segment.position.y = coreHeight + coping.copingHeight / 2;
    segment.rotation.y = i * Math.PI / 4;
    segment.castShadow = true;
    segment.receiveShadow = true;
    rim.add(segment);
  }

  const water = new Mesh(own(new CircleGeometry(f.innerRadius - 0.008, 8)), waterMaterial);
  water.name = 'fountain-water';
  water.rotation.x = -Math.PI / 2;
  water.position.y = f.waterHeight;
  water.receiveShadow = true;
  fountain.add(water);

  box(fountain, 'fountain-pedestal-foot', f.pedestalFootSize, f.pedestalFootHeight, f.pedestalFootSize, f.baseHeight);
  const pedestalBottom = f.baseHeight + f.pedestalFootHeight;
  box(fountain, 'fountain-pedestal', f.pedestalSize, f.pedestalHeight, f.pedestalSize, pedestalBottom);
  box(fountain, 'fountain-pedestal-cap', f.pedestalCapSize, f.pedestalCapHeight, f.pedestalCapSize, pedestalBottom + f.pedestalHeight,
    0, 0, { bevel: 0.016, chipSize: 0.06, chipCorner: 2, seed: 29 });

  const c = layoutConfig.columnShape;
  for (const [columnIndex, placement] of layoutConfig.columns.entries()) {
    const column = new Group();
    column.name = placement.name;
    const [x, y, z] = placement.position;
    column.position.set(x, y, z);
    column.rotation.y = placement.rotationY;
    const detail = stoneConfig.column;
    const profile = detail.profiles[columnIndex]!;
    box(column, `${placement.name}-base`, c.baseWidth, c.baseHeight, c.baseDepth, 0, 0, 0,
      { bevel: detail.baseBevel, chipSize: 0.04, chipCorner: columnIndex % 2, seed: 29 });
    const shaft = new Group();
    shaft.name = `${placement.name}-shaft`;
    column.add(shaft);
    const joint = stoneConfig.joints.width;
    const ratios = detail.layerRatios;
    const usableHeight = c.shaftHeight - joint * (ratios.length - 1);
    const ratioSum = ratios.reduce((sum, value) => sum + value, 0);
    let bottom = c.baseHeight;
    for (let layer = 0; layer < ratios.length; layer++) {
      const height = usableHeight * ratios[layer]! / ratioSum;
      const variant = profile.layers[layer]!;
      box(shaft, `${placement.name}-block-${layer}`, c.shaftWidth, height, c.shaftDepth, bottom,
        profile.offsets[layer]!, 0,
        { seed: detail.layerSeeds[variant]!, chipSize: detail.layerChips[variant]!, chipCorner: variant });
      bottom += height;
      if (layer < ratios.length - 1) {
        box(shaft, `${placement.name}-joint-${layer}`, c.shaftWidth - stoneConfig.joints.recess * 2, joint,
          c.shaftDepth - stoneConfig.joints.recess * 2, bottom, 0, 0,
          { bevel: 0, cornerCut: 0, seed: 47 });
        bottom += joint;
      }
    }
    box(column, `${placement.name}-cap`, c.capWidth, c.capHeight, c.capDepth, c.baseHeight + c.shaftHeight,
      0, 0, { bevel: detail.capBevel, chipSize: profile.capChip, chipCorner: profile.capCorner, seed: 47 + columnIndex });
    root.add(column);
  }

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
  for (let row = 0; row < p.rows; row++) {
    for (let col = 0; col < p.columns; col++) {
      box(
        path,
        `pathRight-slab-${row}-${col}`,
        p.slabWidth, p.slabHeight, p.slabDepth, 0,
        (col - (p.columns - 1) / 2) * p.stepX,
        (row - (p.rows - 1) / 2) * p.stepZ,
        {
          bevel: stoneConfig.path.bevel,
          cornerCut: stoneConfig.path.cornerCut,
          seed: 11 + (row * p.columns + col) % 3 * 18,
          chipSize: stoneConfig.path.chippedSlabs.some(index => index === row * p.columns + col) ? stoneConfig.path.chipSize : 0,
          chipCorner: (row * p.columns + col) % 4,
        },
      );
    }
  }
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
      waterMaterial.dispose();
    },
  };
}
