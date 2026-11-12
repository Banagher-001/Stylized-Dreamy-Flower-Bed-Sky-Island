import { Box3, CylinderGeometry, Group, InstancedMesh, Matrix4, Mesh, OctahedronGeometry, Quaternion, Sphere, SphereGeometry, Vector3 } from 'three';
import { layoutConfig } from '../config/layout';
import { waterConfig } from '../config/water';
import { createWaterMaterial } from '../materials/createWaterMaterial';
import type { WaterState } from '../materials/createWaterMaterial';
import { createLivelyFountainEffects } from './createLivelyFountainEffects';
import type { OrbStyle } from '../config/orb';

export interface DropParameters {
  phase: number;
  vx: number;
  vz: number;
  vy: number;
  radius: number;
  impactTime: number;
  impactX: number;
  impactZ: number;
  strength: number;
}

export function createDropParameters(): DropParameters[] {
  let seed: number = waterConfig.seed;
  function random() {
    seed += 0x6D2B79F5;
    let value = Math.imul(seed ^ seed >>> 15, 1 | seed);
    value ^= value + Math.imul(value ^ value >>> 7, 61 | value);
    return ((value ^ value >>> 14) >>> 0) / 4294967296;
  }
  const d = waterConfig.drops;
  return Array.from({ length: d.capacity }, (_, i) => {
    const angle = i * 2.399963229728653 + random() * 0.15;
    const speed = d.minHorizontalSpeed + random() * (d.maxHorizontalSpeed - d.minHorizontalSpeed);
    const vy = d.minVerticalSpeed + random() * (d.maxVerticalSpeed - d.minVerticalSpeed);
    const radius = d.minRadius + random() * (d.maxRadius - d.minRadius);
    const vx = Math.cos(angle) * speed, vz = Math.sin(angle) * speed;
    const fall = waterConfig.jet.emitterHeight - layoutConfig.fountain.waterHeight - radius;
    const impactTime = (vy + Math.sqrt(vy * vy + 2 * d.gravity * fall)) / d.gravity;
    return { phase: i * d.period / d.capacity, vx, vz, vy, radius, impactTime,
      impactX: vx * impactTime, impactZ: vz * impactTime, strength: 0.7 + random() * 0.3 };
  });
}

export function sampleDrop(drop: DropParameters, age: number, out: Vector3) {
  return out.set(drop.vx * age,
    waterConfig.jet.emitterHeight + drop.vy * age - 0.5 * waterConfig.drops.gravity * age * age,
    drop.vz * age);
}

export function createFountainEffects(state: WaterState, orbStyle: OrbStyle = 'legacy') {
  if (orbStyle === 'lively') {
    try { return createLivelyFountainEffects(state, createDropParameters()); }
    catch (error) { console.warn('Orb detail unavailable; original water effects retained.', error); }
  }
  const root = new Group();
  root.name = 'fountain-effects';
  const f = layoutConfig.fountain;
  root.position.set(...f.position);
  root.rotation.y = f.rotationY;
  const drops = createDropParameters();
  root.userData.dropParameters = drops;
  const material = createWaterMaterial(state, 'jet');
  const capTop = f.baseHeight + f.pedestalFootHeight + f.pedestalHeight + f.pedestalCapHeight;
  const stemHeight = waterConfig.jet.emitterHeight - capTop;
  const stemGeometry = new CylinderGeometry(waterConfig.jet.stemRadius, waterConfig.jet.stemRadius, stemHeight, 8);
  const bulbGeometry = new SphereGeometry(1, 8, 5);
  const dropGeometry = new OctahedronGeometry(1, 0);
  const stem = new Mesh(stemGeometry, material);
  stem.name = 'fountain-water-column';
  stem.position.y = capTop + stemHeight / 2;
  stem.receiveShadow = true;
  const bulb = new Mesh(bulbGeometry, material);
  bulb.name = 'fountain-water-crown';
  bulb.position.y = waterConfig.jet.emitterHeight;
  bulb.receiveShadow = true;
  const particles = new InstancedMesh(dropGeometry, material, drops.length);
  particles.name = 'fountain-water-drops';
  particles.receiveShadow = true;
  particles.boundingBox = new Box3(new Vector3(-1.4, 0.3, -1.4), new Vector3(1.4, 1.45, 1.4));
  particles.boundingSphere = particles.boundingBox.getBoundingSphere(new Sphere());
  root.add(stem, bulb, particles);
  root.visible = waterConfig.enabled;

  const position = new Vector3(), scale = new Vector3(), matrix = new Matrix4(), rotation = new Quaternion();
  const inactiveMatrix = new Matrix4();
  const events = drops.map(drop => ({ drop, age: 0 }));
  const youngestFirst = (a: typeof events[number], b: typeof events[number]) => a.age - b.age;
  const modulo = (value: number, period: number) => (value % period + period) % period;
  function update(time: number) {
    state.time.value = time;
    let active = 0;
    for (const drop of drops) {
      const age = modulo(time - drop.phase, waterConfig.drops.period);
      if (age >= drop.impactTime) continue;
      sampleDrop(drop, age, position);
      const fadeIn = Math.min(1, age / 0.07);
      const fadeOut = Math.min(1, (drop.impactTime - age) / 0.055);
      const size = drop.radius * Math.min(fadeIn, fadeOut);
      if (size < 0.0005) continue;
      scale.setScalar(size);
      matrix.compose(position, rotation, scale);
      particles.setMatrixAt(active++, matrix);
    }
    particles.count = active;
    for (let i = active; i < drops.length; i++) particles.setMatrixAt(i, inactiveMatrix);
    particles.instanceMatrix.needsUpdate = true;
    for (const event of events) event.age = modulo(time - event.drop.phase - event.drop.impactTime, waterConfig.drops.period);
    events.sort(youngestFirst);
    let rippleCount = 0;
    for (let i = 0; i < state.impacts.value.length; i++) {
      const event = events[i]!;
      if (event.age < waterConfig.ripples.lifetime) {
        state.impacts.value[i]!.set(event.drop.impactX, event.drop.impactZ, event.age, event.drop.strength);
        rippleCount++;
      } else state.impacts.value[i]!.set(0, 0, 0, 0);
    }
    const pulse = waterConfig.jet.pulse;
    const radius = waterConfig.jet.radius;
    bulb.scale.set(radius * (1 + pulse * Math.sin(time * 2.1)), radius * 0.9 * (1 + pulse * Math.sin(time * 2.8)), radius * (1 + pulse * Math.cos(time * 2.1)));
    stem.scale.set(1 + pulse * Math.sin(time * 2.1), 1, 1 + pulse * Math.sin(time * 2.1));
    root.userData.time = time;
    root.userData.activeDrops = active;
    root.userData.activeRipples = rippleCount;
  }
  update(waterConfig.initialTime);
  let disposed = false;
  return {
    root,
    update,
    dispose() {
      if (disposed) return;
      disposed = true;
      particles.dispose();
      stemGeometry.dispose(); bulbGeometry.dispose(); dropGeometry.dispose(); material.dispose();
      root.removeFromParent();root.clear();
    },
  };
}
