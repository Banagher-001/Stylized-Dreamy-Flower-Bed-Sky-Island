import {
  Box3, BufferGeometry, DoubleSide, Float32BufferAttribute, InstancedMesh,
  Matrix4, MeshBasicMaterial, Quaternion, Sphere, Vector3,
} from 'three';
import { environmentConfig } from '../config/environment';
import { vegetationConfig } from '../config/vegetation';
import { palette } from '../config/palette';
import { isPlantPositionClear } from './createVegetation';

/** Optional visual comparison: a bounded, reusable batch with cleared flight corridors. */
export function createFloatingPetals() {
  const config = environmentConfig.petals;
  let seed: number = environmentConfig.seed + 1;
  function random() {
    seed += 0x6D2B79F5;
    let value = Math.imul(seed ^ seed >>> 15, 1 | seed);
    value ^= value + Math.imul(value ^ value >>> 7, 61 | value);
    return ((value ^ value >>> 14) >>> 0) / 4294967296;
  }
  const parameters = Array.from({ length: config.capacity }, (_, i) => {
    let x = 0, z = 0, clear = false;
    for (let attempt = 0; attempt < 1000; attempt++) {
      const cluster = vegetationConfig.flowers.clusters[Math.floor(random() * vegetationConfig.flowers.clusters.length)]!;
      const angle = random() * Math.PI * 2, radius = random() * cluster.radius;
      x = cluster.center[0] + Math.cos(angle) * radius;
      z = cluster.center[1] + Math.sin(angle) * radius;
      if (isPlantPositionClear(x, z, config.drift * Math.SQRT2 + 0.05)) { clear = true;break; }
    }
    if (!clear) throw new Error('Cannot fit a clear floating-petal corridor.');
    return { x, z, phase: i * config.period / config.capacity, rotation: random() * Math.PI * 2, size: 0.055 + random() * 0.02 };
  });
  const geometry = new BufferGeometry();
  geometry.setAttribute('position', new Float32BufferAttribute([
    0, 0, -0.5, -0.32, 0, 0, 0, 0.035, 0.45,
    0, 0, -0.5, 0, 0.035, 0.45, 0.32, 0, 0,
  ], 3));
  geometry.computeVertexNormals();
  const material = new MeshBasicMaterial({ color: palette.flowerLight, side: DoubleSide, toneMapped: false });
  material.name = 'courtyard-floating-petal';
  const mesh = new InstancedMesh(geometry, material, config.capacity);
  mesh.name = 'courtyard-floating-petals';
  mesh.castShadow = false;
  const box = new Box3();
  for (const p of parameters) {
    box.expandByPoint(new Vector3(p.x - config.drift, config.minHeight, p.z - config.drift));
    box.expandByPoint(new Vector3(p.x + config.drift, config.maxHeight, p.z + config.drift));
  }
  box.expandByScalar(0.05);
  mesh.boundingBox = box;
  mesh.boundingSphere = box.getBoundingSphere(new Sphere());
  mesh.userData.parameters = parameters;
  const matrix = new Matrix4(), position = new Vector3(), scale = new Vector3(), rotation = new Quaternion();
  const inactiveMatrix = new Matrix4();
  const axis = new Vector3(0.25, 1, 0.15).normalize();
  let disposed = false;
  return {
    mesh,
    update(time: number) {
      let visible = 0;
      for (const p of parameters) {
        const age = ((time - p.phase) % config.period + config.period) % config.period;
        if (age >= config.lifetime) continue;
        const progress = age / config.lifetime;
        const envelope = Math.min(1, age / 0.6, (config.lifetime - age) / 0.7);
        position.set(p.x + Math.sin(age * 0.6 + p.rotation) * config.drift,
          config.maxHeight + (config.minHeight - config.maxHeight) * progress,
          p.z + Math.cos(age * 0.5 + p.rotation) * config.drift);
        rotation.setFromAxisAngle(axis, p.rotation + age * 0.25);
        scale.setScalar(p.size * envelope);
        matrix.compose(position, rotation, scale);
        mesh.setMatrixAt(visible++, matrix);
      }
      mesh.count = visible;
      for (let i = visible; i < config.capacity; i++) mesh.setMatrixAt(i, inactiveMatrix);
      mesh.instanceMatrix.needsUpdate = true;
    },
    dispose() {
      if (disposed) return;
      disposed = true;
      mesh.dispose();geometry.dispose();material.dispose();mesh.removeFromParent();
    },
  };
}
