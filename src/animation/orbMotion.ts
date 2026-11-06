import type { Vector3 } from 'three';
import type { DropParameters } from '../scene/createFountainEffects';
import { orbConfig as config } from '../config/orb';
import { layoutConfig } from '../config/layout';
import { waterConfig } from '../config/water';

const omega = Math.PI * 2 / config.floatPeriod;
export interface OrbPose { y: number; sx: number; sy: number; sz: number; }
export const createOrbPose = (): OrbPose => ({ y: 0, sx: 1, sy: 1, sz: 1 });
export function sampleOrbPose(time: number, out = createOrbPose()) {
  const phase = time * omega;
  out.y = config.centerY + config.floatAmplitude * Math.sin(phase);
  out.sx = 1 + config.shape.x * Math.sin(phase * .73);
  out.sy = config.shape.yRatio * (1 + config.shape.y * Math.sin(phase + .8));
  out.sz = 1 + config.shape.z * Math.cos(phase * .81);
  return out;
}
export function sampleOrbRadius(x: number, y: number, z: number, time: number) {
  return 1 + config.shape.first * Math.sin(x * 3.7 + y * 2.1 + time * omega * .84)
    + config.shape.second * Math.cos(z * 4.4 - y * 1.3 - time * omega * 1.18);
}
export interface OrbFlight {
  birthTime: number; x: number; y: number; z: number;
  vx: number; vy: number; vz: number;
  duration: number; impactX: number; impactZ: number;
}
export const createOrbFlight = (): OrbFlight => ({ birthTime: NaN, x: 0, y: 0, z: 0, vx: 0, vy: 0, vz: 0, duration: 0, impactX: 0, impactZ: 0 });
const scratch = createOrbPose();
/** All fields derive from the birth instant; scratch carries no simulation history. */
export function sampleOrbFlight(drop: DropParameters, birthTime: number, out = createOrbFlight()) {
  const pose = sampleOrbPose(birthTime, scratch);
  const speed = Math.hypot(drop.vx, drop.vz), latitude = config.releaseLatitude;
  const ring = Math.sqrt(1 - latitude * latitude);
  const nx = drop.vx / speed * ring, ny = latitude, nz = drop.vz / speed * ring;
  const radius = config.radius * sampleOrbRadius(nx, ny, nz, birthTime);
  const normalLength = Math.hypot(nx / pose.sx, ny / pose.sy, nz / pose.sz);
  const margin = drop.radius + config.releaseMargin;
  out.birthTime = birthTime;
  out.x = nx * radius * pose.sx + nx / pose.sx / normalLength * margin;
  out.y = pose.y + ny * radius * pose.sy + ny / pose.sy / normalLength * margin;
  out.z = nz * radius * pose.sz + nz / pose.sz / normalLength * margin;
  out.vx = drop.vx;out.vz = drop.vz;
  out.vy = drop.vy + config.floatAmplitude * omega * Math.cos(birthTime * omega);
  const fall = out.y - layoutConfig.fountain.waterHeight - drop.radius;
  out.duration = (out.vy + Math.sqrt(out.vy * out.vy + 2 * waterConfig.drops.gravity * fall)) / waterConfig.drops.gravity;
  out.impactX = out.x + out.vx * out.duration;out.impactZ = out.z + out.vz * out.duration;
  return out;
}
export function sampleOrbDrop(flight: OrbFlight, age: number, out: Vector3) {
  return out.set(flight.x + flight.vx * age, flight.y + flight.vy * age - .5 * waterConfig.drops.gravity * age * age, flight.z + flight.vz * age);
}
