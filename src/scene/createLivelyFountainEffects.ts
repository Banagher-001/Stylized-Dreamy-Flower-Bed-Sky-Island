import { Box3, BufferAttribute, CylinderGeometry, DynamicDrawUsage, Group, InstancedMesh, MathUtils, Matrix4, Mesh, OctahedronGeometry, Quaternion, Sphere, SphereGeometry, Vector3, Vector4 } from 'three';
import { layoutConfig } from '../config/layout';
import { waterConfig } from '../config/water';
import { orbConfig, particleOrbWave, type OrbStyle } from '../config/orb';
import { createOrbFlight, createOrbPose, sampleOrbDrop, sampleOrbFlight, sampleOrbPose } from '../animation/orbMotion';
import { sampleOrbPhases, sampleOrbSurfaceRadius } from '../animation/orbSurface';
import { createParticleOrbDrops } from '../animation/particleOrbDrops';
import { createWaterMaterial } from '../materials/createWaterMaterial';
import { createOrbMaterial } from '../materials/createOrbMaterial';
import { createParticleOrb } from './createParticleOrb';
import type { WaterState } from '../materials/createWaterMaterial';
import type { DropParameters } from './createFountainEffects';

function createLivelyOrb() {
  const phases = new Vector4();
  const pose = createOrbPose();
  const orbMaterial = createOrbMaterial(phases);
  const orbGeometry = new SphereGeometry(1, ...orbConfig.sphereSegments);
  const points = orbGeometry.getAttribute('position') as BufferAttribute;points.setUsage(DynamicDrawUsage);
  const originalPoints = new Float32Array(points.array);
  orbGeometry.setAttribute('orbRest', new BufferAttribute(originalPoints, 3));
  orbGeometry.boundingSphere = new Sphere(new Vector3(), orbConfig.shape.envelope);
  orbGeometry.boundingBox = new Box3(new Vector3().setScalar(-orbConfig.shape.envelope), new Vector3().setScalar(orbConfig.shape.envelope));
  const bulb = new Mesh(orbGeometry, orbMaterial);bulb.name = 'fountain-water-crown';bulb.receiveShadow = true;bulb.scale.setScalar(orbConfig.radius);
  return {
    object: bulb,
    phases,
    pose,
    metadata: { radius: orbConfig.radius, centerY: orbConfig.centerY, amplitude: orbConfig.floatAmplitude, period: orbConfig.floatPeriod, envelope: orbConfig.shape.envelope, replacedGeometries: 2, addedGeometries: 0, addedTextures: 0, addedPasses: 0, flow: 'curved-rest-sphere-v2', vertices: points.count, triangles: orbGeometry.index!.count / 3, restAttributeBytes: originalPoints.byteLength },
    update(time: number) {
      sampleOrbPose(time, pose);sampleOrbPhases(time, phases);
      let lowest = Infinity;
      for (let i = 0; i < points.count; i++) {
        const j = i * 3, x = originalPoints[j]!, y = originalPoints[j + 1]!, z = originalPoints[j + 2]!;
        const radial = sampleOrbSurfaceRadius(x, y, z, phases);
        const py = y * radial * pose.sy;
        points.setXYZ(i, x * radial * pose.sx, py, z * radial * pose.sz);lowest = Math.min(lowest, py);
      }
      points.needsUpdate = true;bulb.position.y = pose.y;
      return pose.y + lowest * orbConfig.radius;
    },
    dispose() { orbGeometry.dispose();orbMaterial.dispose(); },
  };
}

/** One existing effects group, three owned geometries and the original bounded pools. */
export function createLivelyFountainEffects(state: WaterState, drops: DropParameters[], style: Exclude<OrbStyle, 'legacy'> = 'lively') {
  const root = new Group();root.name = 'fountain-effects';root.userData.orbStyle = style;
  const f = layoutConfig.fountain;root.position.set(...f.position);root.rotation.y = f.rotationY;
  const particleOrb = style === 'lively' ? undefined : createParticleOrb(style);
  const orb = particleOrb ?? createLivelyOrb();
  const beads = style === 'particle-drops' && particleOrb ? createParticleOrbDrops(particleOrb.object) : undefined;
  const releasePeriod = beads ? particleOrbWave.primary.period : waterConfig.drops.period;
  const jetMaterial = createWaterMaterial(state, 'jet');
  const capTop = f.baseHeight + f.pedestalFootHeight + f.pedestalHeight + f.pedestalCapHeight;
  const stemGeometry = new CylinderGeometry(orbConfig.stemRadius, orbConfig.stemRadius, 1, 8);
  const dropGeometry = new OctahedronGeometry(1, beads ? 1 : 0);
  const stem = new Mesh(stemGeometry, jetMaterial);stem.name = 'fountain-water-column';stem.receiveShadow = true;
  const particles = new InstancedMesh(dropGeometry, jetMaterial, drops.length);particles.name = 'fountain-water-drops';particles.receiveShadow = true;
  particles.instanceMatrix.setUsage(DynamicDrawUsage);
  particles.boundingBox = new Box3(new Vector3(-1.75, .3, -1.75), new Vector3(1.75, 1.9, 1.75));particles.boundingSphere = particles.boundingBox.getBoundingSphere(new Sphere());
  root.add(stem, orb.object, particles);root.visible = waterConfig.enabled;
  const position = new Vector3(), scale = new Vector3(), rotation = new Quaternion(), matrix = new Matrix4(), inactive = new Matrix4();
  const records = (beads ?? drops).map((drop, index) => ({ drop, index, current: createOrbFlight(), previous: createOrbFlight() }));
  const events = records.map(record => ({ record, age: 0, flight: record.current }));
  root.userData.flights = records;root.userData.impactEvents = events;
  if ('pose' in orb) {
    root.userData.orbPose = orb.pose;
    root.userData.orbPhases = orb.phases;
  }
  root.userData.orbMetadata = {
    ...orb.metadata,
    dropCapacity: drops.length,
    rippleCapacity: state.impacts.value.length,
    ...(beads && {
      releasePeriod,
      beads: beads.map(({ anchorIndex, phase, formationTime, radius, strength }) => ({ anchorIndex, phase, formationTime, radius, strength })),
    }),
  };
  let lastTime: number | undefined, disposed = false;
  function update(time: number) {
    if (disposed || time === lastTime) return;
    lastTime = time;state.time.value = time;
    const bottom = orb.update(time), stemTop = bottom + orbConfig.stemOverlap;
    stem.position.y = (capTop + stemTop) / 2;stem.scale.y = stemTop - capTop;
    let active = 0;
    for (const record of records) {
      const { drop, current, previous } = record;
      const bead = 'sampleAttached' in drop ? drop : undefined;
      const formation = bead?.formationTime ?? 0;
      const birth = drop.phase + Math.floor((time - drop.phase + formation) / releasePeriod) * releasePeriod;
      if (birth !== current.birthTime) {
        if ('sampleFlight' in drop) {
          drop.sampleFlight(birth, current);
          drop.sampleFlight(birth - releasePeriod, previous);
        } else {
          sampleOrbFlight(drop, birth, current);
          sampleOrbFlight(drop, birth - releasePeriod, previous);
        }
      }
      const age = time - birth;
      let size = drop.radius;
      if (bead && age < 0) {
        const growth = MathUtils.smoothstep(age, -formation, 0);
        bead.sampleAttached(time, growth, position);
        size *= growth;
      } else {
        if (!bead && age >= current.duration) continue;
        sampleOrbDrop(current, age, position);
        // Let the water plane hide the last visible part of the bead after contact.
        if (bead) {
          if (position.y + size <= f.waterHeight) continue;
        } else {
          size *= Math.min(1, age / .07, (current.duration - age) / .055);
        }
      }
      if (size < .0005) continue;
      scale.setScalar(size);matrix.compose(position, rotation, scale);particles.setMatrixAt(active++, matrix);
    }
    particles.count = active;for (let i = active; i < drops.length; i++) particles.setMatrixAt(i, inactive);particles.instanceMatrix.needsUpdate = true;
    for (const event of events) {
      const r = event.record;
      event.flight = time >= r.current.birthTime + r.current.duration ? r.current : r.previous;
      event.age = time - (event.flight.birthTime + event.flight.duration);
    }
    events.sort((a, b) => a.age - b.age || a.record.index - b.record.index);
    let rippleCount = 0;
    for (let i = 0; i < state.impacts.value.length; i++) {
      const event = events[i];
      if (event && event.age >= 0 && event.age < waterConfig.ripples.lifetime) { state.impacts.value[i]!.set(event.flight.impactX, event.flight.impactZ, event.age, event.record.drop.strength);rippleCount++; }
      else state.impacts.value[i]!.set(0, 0, 0, 0);
    }
    root.userData.time = time;root.userData.activeDrops = active;root.userData.activeRipples = rippleCount;
    root.userData.orbBottom = bottom;root.userData.stemTop = stemTop;
  }
  update(waterConfig.initialTime);
  return {
    root, update,
    dispose() { if (disposed) return;disposed = true;particles.dispose();stemGeometry.dispose();orb.dispose();dropGeometry.dispose();jetMaterial.dispose();root.removeFromParent();root.clear(); },
  };
}
