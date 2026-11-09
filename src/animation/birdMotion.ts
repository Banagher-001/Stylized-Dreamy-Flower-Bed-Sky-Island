import { Euler, Quaternion, Vector3 } from 'three';
import { birdConfig } from '../config/birds';

const tau = Math.PI * 2;
const wrap = (n: number, d: number) => ((n % d) + d) % d;
const smooth = (n: number) => { const t = Math.min(1, Math.max(0, n));return t * t * t * (t * (t * 6 - 15) + 10); };
export function createBirdPose() {
  return { position: new Vector3(), tangent: new Vector3(), rotation: new Quaternion(), euler: new Euler(0, 0, 0, 'YXZ'),
    leftWing: 0, rightWing: 0, flap: 0, bank: 0, speed: 0, scale: 1, phase: 0 };
}
export type BirdPose = ReturnType<typeof createBirdPose>;

/** Absolute environmental time, not frame integration. Position and orientation
 * remain continuous across route/wing cycles, including reverse-time diagnostics.
 */
export function sampleBirdPose(time: number, index: number, out: BirdPose) {
  const p = birdConfig.routes[index]!;
  const phase = wrap(time / p.period * p.direction + p.phase, 1), a = tau * phase, rate = tau / p.period * p.direction;
  const c = Math.cos(p.rotation), s = Math.sin(p.rotation);
  const x = p.radii[0] * Math.cos(a) + .35 * Math.sin(2 * a), z = p.radii[1] * Math.sin(a);
  const dx = (-p.radii[0] * Math.sin(a) + .70 * Math.cos(2 * a)) * rate, dz = p.radii[1] * Math.cos(a) * rate;
  const wingTime = wrap(time + index * 1.37, p.flapCycle);
  const flap = smooth(wingTime / .22) * (1 - smooth((wingTime - p.flapDuration + .28) / .28));
  const beat = tau * p.flapRate * time + index * 1.9;
  const wing = .08 + flap * (.54 * Math.sin(beat) - .04);
  out.position.set(p.center[0] + c * x - s * z,
    p.height + .055 * Math.sin(2 * a) + .016 * flap * Math.sin(beat * 2), p.center[1] + s * x + c * z);
  out.tangent.set(c * dx - s * dz, .11 * rate * Math.cos(2 * a), s * dx + c * dz);
  out.speed = out.tangent.length();out.tangent.normalize();
  const yaw = Math.atan2(out.tangent.x, out.tangent.z), pitch = -Math.atan2(out.tangent.y, Math.hypot(out.tangent.x, out.tangent.z));
  const bank = -.18 * p.direction * (.75 + .25 * Math.cos(2 * a));
  out.euler.set(pitch, yaw, bank, 'YXZ');out.rotation.setFromEuler(out.euler);
  out.leftWing = wing;out.rightWing = -wing;out.flap = flap;out.bank = bank;out.scale = p.span;out.phase = phase;
  return out;
}
