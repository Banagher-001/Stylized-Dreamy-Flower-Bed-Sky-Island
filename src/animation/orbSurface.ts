import { Vector3, Vector4 } from 'three';
import { orbConfig } from '../config/orb';

const tau = Math.PI * 2;
const flow = orbConfig.flow;
export const samplePeriodicPhase = (time: number, period: number) => ((time % period) + period) % period / period * tau;

/** Each periodic component is reduced separately, before conversion to GPU float.
 * x/y = cos/sin of the slow turn; z/w = the two wave phases, in radians.
 * Only trigonometric functions consume wrapped phases, so every wrap is continuous.
 */
export function sampleOrbPhases(time: number, out = new Vector4()) {
  const turn = samplePeriodicPhase(time, flow.turnPeriod);
  return out.set(Math.cos(turn), Math.sin(turn), samplePeriodicPhase(time, flow.mainPeriod), samplePeriodicPhase(time, flow.detailPeriod));
}

/** Continuous 3-D field on the rest sphere: no longitude seam or polar UV pinch. */
export function sampleOrbSurfaceRadius(x: number, y: number, z: number, phases: Vector4) {
  const qx = phases.x * x - phases.y * z, qz = phases.y * x + phases.x * z;
  const bend = qx * flow.bend[0] + y * flow.bend[1] + qz * flow.bend[2] + phases.w;
  const main = qx * flow.main[0] + y * flow.main[1] + qz * flow.main[2] + flow.bendStrength * Math.sin(bend) + phases.z;
  const detail = qx * flow.detail[0] + y * flow.detail[1] + qz * flow.detail[2] - phases.w;
  return 1 + orbConfig.shape.first * Math.cos(main) + orbConfig.shape.second * Math.sin(detail);
}

/** Outward normal of the radial field, before the pose's nonuniform scale.
 * Project the Cartesian gradient into the sphere tangent plane, then use
 * n - tangentGradient(radius)/radius. The flight sampler applies inverse scale.
 */
export function sampleOrbSurfaceNormal(x: number, y: number, z: number, phases: Vector4, out = new Vector3()) {
  const qx = phases.x * x - phases.y * z, qz = phases.y * x + phases.x * z;
  const bend = qx * flow.bend[0] + y * flow.bend[1] + qz * flow.bend[2] + phases.w;
  const main = qx * flow.main[0] + y * flow.main[1] + qz * flow.main[2] + flow.bendStrength * Math.sin(bend) + phases.z;
  const detail = qx * flow.detail[0] + y * flow.detail[1] + qz * flow.detail[2] - phases.w;
  const a = -orbConfig.shape.first * Math.sin(main), b = orbConfig.shape.second * Math.cos(detail);
  const warp = flow.bendStrength * Math.cos(bend);
  const gx = a * (flow.main[0] + warp * flow.bend[0]) + b * flow.detail[0];
  const gy = a * (flow.main[1] + warp * flow.bend[1]) + b * flow.detail[1];
  const gz = a * (flow.main[2] + warp * flow.bend[2]) + b * flow.detail[2];
  const dx = phases.x * gx + phases.y * gz, dz = -phases.y * gx + phases.x * gz;
  const radial = 1 + orbConfig.shape.first * Math.cos(main) + orbConfig.shape.second * Math.sin(detail);
  const dot = x * dx + y * gy + z * dz;
  return out.set(x - (dx - x * dot) / radial, y - (gy - y * dot) / radial, z - (dz - z * dot) / radial).normalize();
}
