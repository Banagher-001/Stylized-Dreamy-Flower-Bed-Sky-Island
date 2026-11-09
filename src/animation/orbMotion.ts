import { Vector3, Vector4 } from 'three';
import type { DropParameters } from '../scene/createFountainEffects';
import { orbConfig as config } from '../config/orb';
import { layoutConfig } from '../config/layout';
import { waterConfig } from '../config/water';
import { sampleOrbPhases, sampleOrbSurfaceNormal, sampleOrbSurfaceRadius } from './orbSurface';

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
  return sampleOrbSurfaceRadius(x, y, z, sampleOrbPhases(time, surfacePhases));
}
export interface OrbFlight {
  birthTime: number; x: number; y: number; z: number;
  vx: number; vy: number; vz: number;
  duration: number; impactX: number; impactZ: number;
}
export const createOrbFlight = (): OrbFlight => ({ birthTime: NaN, x: 0, y: 0, z: 0, vx: 0, vy: 0, vz: 0, duration: 0, impactX: 0, impactZ: 0 });
const scratch = createOrbPose();
const surfacePhases = new Vector4(), surfaceNormal = new Vector3();
/** All fields derive from the birth instant; scratch carries no simulation history. */
export function sampleOrbFlight(drop: DropParameters, birthTime: number, out = createOrbFlight()) {
  const pose = sampleOrbPose(birthTime, scratch);
  const speed = Math.hypot(drop.vx, drop.vz), latitude = config.releaseLatitude;
  const ring = Math.sqrt(1 - latitude * latitude);
  const nx = drop.vx / speed * ring, ny = latitude, nz = drop.vz / speed * ring;
  sampleOrbPhases(birthTime, surfacePhases);
  const radius = config.radius * sampleOrbSurfaceRadius(nx, ny, nz, surfacePhases);
  sampleOrbSurfaceNormal(nx, ny, nz, surfacePhases, surfaceNormal);
  surfaceNormal.set(surfaceNormal.x / pose.sx, surfaceNormal.y / pose.sy, surfaceNormal.z / pose.sz).normalize();
  const margin = drop.radius + config.releaseMargin;
  out.birthTime = birthTime;
  out.x = nx * radius * pose.sx + surfaceNormal.x * margin;
  out.y = pose.y + ny * radius * pose.sy + surfaceNormal.y * margin;
  out.z = nz * radius * pose.sz + surfaceNormal.z * margin;
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
