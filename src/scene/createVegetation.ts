import { Color, Group, InstancedBufferAttribute, InstancedMesh, Matrix4, Quaternion, Vector3 } from 'three';
import type { BufferGeometry, Material, OrthographicCamera } from 'three';
import { layoutConfig } from '../config/layout';
import { vegetationConfig as config } from '../config/vegetation';
import { palette } from '../config/palette';
import { createFlowerGeometry, createGrassGeometry, createStemGeometry } from '../geometry/createFlowerGeometry';
import { createVegetationMaterial } from '../materials/createVegetationMaterial';
import { environmentConfig } from '../config/environment';
import { plantWindPhase } from '../animation/environmentMotion';
import type { EnvironmentState } from '../animation/environmentMotion';
import { isPathPositionClear, pathPointToWorld } from './pathLayout';

interface Plant {
  x: number;
  z: number;
  height: number;
  diameter: number;
  rotation: number;
  color: number;
  radius: number;
  gap: boolean;
}

const plantMargin = 0.035;

function isCourtyardPositionClear(x: number, z: number, radius: number, margin: number) {
  const f = layoutConfig.fountain;
  const c = Math.cos(f.rotationY), s = Math.sin(f.rotationY);
  const dx = x - f.position[0], dz = z - f.position[2];
  const fx = c * dx - s * dz, fz = s * dx + c * dz;
  let inPool = true;
  for (let i = 0; i < 8; i++) {
    const angle = (i + 0.5) * Math.PI / 4;
    if (fx * Math.cos(angle) - fz * Math.sin(angle) > f.baseRadius * Math.cos(Math.PI / 8) + radius + margin) inPool = false;
  }
  if (inPool) return false;

  function inRectangle(px: number, pz: number, cx: number, cz: number, width: number, depth: number, rotation: number) {
    const c = Math.cos(rotation), s = Math.sin(rotation);
    const dx = px - cx, dz = pz - cz;
    return Math.abs(c * dx - s * dz) < width / 2 + radius + margin
      && Math.abs(s * dx + c * dz) < depth / 2 + radius + margin;
  }
  const shape = layoutConfig.columnShape;
  for (const column of layoutConfig.columns) {
    if (inRectangle(x, z, column.position[0], column.position[2], shape.baseWidth, shape.baseDepth, column.rotationY)) return false;
  }
  const wall = layoutConfig.wall;
  if (inRectangle(x, z, wall.position[0], wall.position[2], wall.length + wall.endSize, Math.max(wall.baseDepth, wall.endSize), wall.rotationY)) return false;
  return true;
}

/** Conservative clearance includes the plant's maximum horizontal extent. */
export function isPlantPositionClear(x: number, z: number, radius: number, margin = plantMargin) {
  return isCourtyardPositionClear(x, z, radius, margin) && isPathPositionClear(x, z, radius + margin);
}

function isScatterPositionClear(x: number, z: number, radius: number) {
  const reserve = config.ground.pavingReserve;
  const clearance = radius + plantMargin;
  const inReserve = x > reserve.x[0] - clearance && x < reserve.x[1] + clearance
    && z > reserve.z[0] - clearance && z < reserve.z[1] + clearance;
  return !inReserve && isCourtyardPositionClear(x, z, radius, plantMargin);
}

export function createVegetation(camera: OrthographicCamera, environment?: EnvironmentState) {
  const root = new Group();
  root.name = 'courtyard-vegetation';
  let seed: number = config.seed;
  function random() {
    seed += 0x6D2B79F5;
    let value = Math.imul(seed ^ seed >>> 15, 1 | seed);
    value ^= value + Math.imul(value ^ value >>> 7, 61 | value);
    return ((value ^ value >>> 14) >>> 0) / 4294967296;
  }
  const lerp = (a: number, b: number) => a + (b - a) * random();
  function visible(x: number, z: number) {
    const p = new Vector3(x, 0, z).project(camera);
    return Math.abs(p.x) < 0.98 && Math.abs(p.y) < 0.98;
  }
  function quiet(x: number, z: number) {
    const g = config.ground;
    return Math.hypot((x - g.quietCenter[0]) / g.quietRadius[0], (z - g.quietCenter[1]) / g.quietRadius[1]) < 1;
  }
  const grass: Plant[] = [], flowers: Plant[] = [];
  if (config.enabled) {
    for (let attempt = 0; grass.length < config.grass.count && attempt < config.grass.count * 120; attempt++) {
      let x: number, z: number;
      if (random() < 0.48) {
        const cluster = config.flowers.clusters[Math.floor(random() * config.flowers.clusters.length)]!;
        const angle = random() * Math.PI * 2, r = Math.sqrt(random()) * (cluster.radius + 0.5);
        x = cluster.center[0] + Math.cos(angle) * r;
        z = cluster.center[1] + Math.sin(angle) * r;
      } else { x = lerp(-7.5, 7.4); z = lerp(-8.7, 8.4); }
      if (!visible(x, z) || !isScatterPositionClear(x, z, config.grass.clearance) || (quiet(x, z) && random() < 0.9)) continue;
      grass.push({ x, z, height: lerp(config.grass.minHeight, config.grass.maxHeight), diameter: 0, rotation: random() * Math.PI * 2, color: random(), radius: config.grass.clearance, gap: false });
    }
    for (let attempt = 0; flowers.length < config.flowers.count && attempt < config.flowers.count * 120; attempt++) {
      const cluster = config.flowers.clusters[Math.floor(random() * config.flowers.clusters.length)]!;
      const angle = random() * Math.PI * 2, r = Math.pow(random(), 0.65) * cluster.radius;
      const x = cluster.center[0] + Math.cos(angle) * r, z = cluster.center[1] + Math.sin(angle) * r;
      const diameter = lerp(config.flowers.minDiameter, config.flowers.maxDiameter);
      const radius = diameter * 0.55 + 0.01;
      if (!visible(x, z) || quiet(x, z) || !isScatterPositionClear(x, z, radius)) continue;
      if (flowers.some(p => Math.hypot(p.x - x, p.z - z) < (p.radius + radius) * 0.85)) continue;
      flowers.push({ x, z, height: lerp(config.flowers.minHeight, config.flowers.maxHeight), diameter, rotation: random() * Math.PI * 2, color: random(), radius, gap: false });
    }
    if (grass.length !== config.grass.count || flowers.length !== config.flowers.count) throw new Error('Vegetation regions cannot fit the requested counts.');

    const gapRadius = 0.023;
    const gapMargin = 0.037;
    for (const { center, height } of config.grass.pavingTufts) {
      const [x, z] = pathPointToWorld(center[0], center[1]);
      if (isPlantPositionClear(x, z, gapRadius, gapMargin)) {
        grass.push({
          x, z, height, diameter: 0,
          rotation: random() * Math.PI * 2, color: random(), radius: gapRadius, gap: true,
        });
      }
    }
  }

  const clearsPaving = (plant: Plant) => isPathPositionClear(plant.x, plant.z, plant.radius + plantMargin);
  const groundGrass = grass.filter(plant => plant.gap || clearsPaving(plant));
  const flowerStems = flowers.filter(clearsPaving);
  const geometries: BufferGeometry[] = [];
  const materials: Material[] = [];
  const batches: InstancedMesh[] = [];
  if (config.enabled) {
    const green = createVegetationMaterial('foliage', environment), pink = createVegetationMaterial('flower', environment);
    materials.push(green, pink);
    const grassGeometry = createGrassGeometry(), stemGeometry = createStemGeometry();
    const flowerFour = createFlowerGeometry(4), flowerFive = createFlowerGeometry(5);
    geometries.push(grassGeometry, stemGeometry, flowerFour, flowerFive);
    function batch(name: string, geometry: BufferGeometry, material: Material, plants: Plant[], type: 'grass' | 'stem' | 'flower') {
      const mesh = new InstancedMesh(geometry, material, plants.length);
      mesh.name = name;
      mesh.castShadow = false;
      mesh.receiveShadow = true;
      const matrix = new Matrix4(), rotation = new Quaternion(), up = new Vector3(0, 1, 0);
      const baseColor = new Color(type === 'flower' ? palette.flower : type === 'stem' ? palette.plantStem : palette.grassBlade);
      const lightColor = new Color(type === 'flower' ? palette.flowerLight : palette.grassBladeLight);
      plants.forEach((p, i) => {
        rotation.setFromAxisAngle(up, p.rotation);
        const size = type === 'flower' ? p.diameter : p.height;
        const widthScale = type === 'grass' && p.gap ? config.grass.gapWidthScale : 1;
        matrix.compose(new Vector3(p.x, config.rootHeight + (type === 'flower' ? p.height : 0), p.z), rotation, new Vector3(size * widthScale, size, size * widthScale));
        mesh.setMatrixAt(i, matrix);
        mesh.setColorAt(i, baseColor.clone().lerp(lightColor, type === 'stem' ? p.color * 0.25 : type === 'flower' ? p.color * 0.6 : p.color * 0.85));
      });
      mesh.instanceMatrix.needsUpdate = true;
      if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
      if (environment?.options.enabled) {
        const roots = new Float32Array(plants.length * 3), shapes = new Float32Array(plants.length * 4);
        plants.forEach((p, i) => {
          const angle = type === 'grass' ? p.gap ? environmentConfig.wind.gapAngle : environmentConfig.wind.grassAngle : environmentConfig.wind.flowerAngle;
          roots.set([p.x, config.rootHeight, p.z], i * 3);
          shapes.set([p.height, angle, plantWindPhase(p.x, p.z), type === 'flower' ? 1 : 0], i * 4);
        });
        geometry.setAttribute('windRoot', new InstancedBufferAttribute(roots, 3));
        geometry.setAttribute('windShape', new InstancedBufferAttribute(shapes, 4));
      }
      mesh.computeBoundingBox();
      mesh.computeBoundingSphere();
      if (environment?.options.enabled) {
        // Includes arc shortening and tilted petals; computed once, never per frame.
        mesh.boundingBox!.expandByScalar(0.02);
        mesh.boundingSphere!.radius += 0.02;
      }
      mesh.userData.plants = plants;
      mesh.userData.plantType = type;
      batches.push(mesh);
      root.add(mesh);
    }
    batch('grass-clusters', grassGeometry, green, groundGrass, 'grass');
    batch('flower-stems', stemGeometry, green, flowerStems, 'stem');
    batch('flowers-four-petal', flowerFour, pink, flowers.filter((plant, i) => i % 2 === 0 && clearsPaving(plant)), 'flower');
    batch('flowers-five-petal', flowerFive, pink, flowers.filter((plant, i) => i % 2 === 1 && clearsPaving(plant)), 'flower');
  }
  root.userData.seed = config.seed;
  root.userData.counts = { grass: groundGrass.length, flowers: flowerStems.length, batches: batches.length };
  let disposed = false;
  return {
    root,
    dispose() {
      if (disposed) return;
      disposed = true;
      for (const mesh of batches) mesh.dispose();
      for (const geometry of geometries) geometry.dispose();
      for (const material of materials) material.dispose();
      root.removeFromParent();
      root.clear();
    },
  };
}
