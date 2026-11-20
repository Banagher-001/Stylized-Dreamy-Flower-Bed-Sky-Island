import { MathUtils, Vector3 } from 'three';
import type { Points } from 'three';
import { finishOrbFlight, orbFlightTime } from './orbMotion';
import type { OrbFlight } from './orbMotion';
import { samplePeriodicPhase } from './orbSurface';
import { layoutConfig } from '../config/layout';
import { orbConfig, particleOrbDrops, particleOrbWave } from '../config/orb';

export function createParticleOrbDrops(orb: Points) {
  const positions = orb.geometry.getAttribute('position');
  const directions = orb.geometry.getAttribute('orbDirection');
  const layers = orb.geometry.getAttribute('orbLayer');
  const f = layoutConfig.fountain;
  const capTop = f.baseHeight + f.pedestalFootHeight + f.pedestalHeight + f.pedestalCapHeight;
  const { primary, secondary, stemFade } = particleOrbWave;
  const { yRatio } = orbConfig.shape;
  const primaryDirection = new Vector3(...primary.direction);
  const secondaryDirection = new Vector3(...secondary.direction);

  return particleOrbDrops.beads.map((bead) => {
    const hint = new Vector3(...bead.direction);
    const direction = new Vector3();
    let anchorIndex = 0;
    let bestAlignment = -Infinity;
    for (let index = 0; index < positions.count; index++) {
      if (layers.getX(index) !== 0) continue;
      const alignment = direction.fromBufferAttribute(directions, index).dot(hint);
      if (alignment > bestAlignment) {
        bestAlignment = alignment;
        anchorIndex = index;
      }
    }

    direction.fromBufferAttribute(directions, anchorIndex);
    const rest = new Vector3().fromBufferAttribute(positions, anchorIndex);
    const radial = new Vector3(direction.x, direction.y * yRatio, direction.z);
    const normal = new Vector3(direction.x, direction.y / yRatio, direction.z).normalize();
    const outward = new Vector3(normal.x, 0, normal.z).normalize();
    const primaryPhase = direction.dot(primaryDirection);
    const secondaryPhase = direction.dot(secondaryDirection);
    const weight = MathUtils.smoothstep(direction.y, ...stemFade);
    const origin = new Vector3();

    // Sample the same shell vertex and radial wave the vertex shader evaluates.
    function sampleAttached(time: number, growth: number, out: Vector3) {
      const wave = primary.amplitude * Math.cos(primaryPhase + samplePeriodicPhase(time, primary.period))
        + secondary.amplitude * Math.sin(secondaryPhase + samplePeriodicPhase(time, secondary.period));
      return out.copy(rest).addScaledVector(radial, wave * weight).add(orb.position)
        .addScaledVector(normal, bead.radius * growth);
    }

    function sampleFlight(birthTime: number, out: OrbFlight) {
      sampleAttached(birthTime, 1, origin);
      // The bead's bottom reaches cap height after its center clears a side of the square.
      const atCap = orbFlightTime(origin.y - capTop - bead.radius, bead.vy);
      const edge = f.pedestalCapSize / 2 + bead.radius + particleOrbDrops.clearance;
      const distanceToEdge = Math.min(
        (edge - Math.sign(outward.x) * origin.x) / Math.abs(outward.x),
        (edge - Math.sign(outward.z) * origin.z) / Math.abs(outward.z),
      );
      const speed = Math.max(bead.speed, distanceToEdge / atCap);
      out.birthTime = birthTime;
      out.x = origin.x;
      out.y = origin.y;
      out.z = origin.z;
      out.vx = outward.x * speed;
      out.vy = bead.vy;
      out.vz = outward.z * speed;
      return finishOrbFlight(out, bead.radius);
    }

    return { ...bead, anchorIndex, sampleAttached, sampleFlight };
  });
}
