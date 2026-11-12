import { Vector3 } from 'three';
import { environmentConfig as config, resolveEnvironmentOptions } from '../config/environment';
import type { EnvironmentOptions } from '../config/environment';
import { waterConfig } from '../config/water';

export function createEnvironmentState(options: Partial<EnvironmentOptions> = {}) {
  const settings = { ...resolveEnvironmentOptions(new URLSearchParams()), ...options };
  return {
    options: settings,
    time: { value: waterConfig.initialTime as number },
    wind: { value: settings.enabled && settings.wind ? 1 : 0 },
    canopy: { value: settings.enabled && settings.canopy ? 1 : 0 },
  };
}
export type EnvironmentState = ReturnType<typeof createEnvironmentState>;

/** Independent position hash: never advances the vegetation placement RNG. */
export function plantWindPhase(x: number, z: number) {
  const value = Math.sin(x * 12.9898 + z * 78.233 + config.seed) * 43758.5453;
  return x * 0.42 + z * 0.29 + (value - Math.floor(value) - 0.5) * 0.42;
}

export function sampleWindAngle(time: number, phase: number, maximum: number) {
  const tau = Math.PI * 2;
  const gust = 0.68 + 0.32 * Math.sin(tau * time / config.wind.gustPeriod + phase * 0.23);
  return maximum * gust * (0.78 * Math.sin(tau * time / config.wind.periods[0] + phase)
    + 0.22 * Math.sin(tau * time / config.wind.periods[1] + phase * 1.3));
}

const directionLength = Math.hypot(...config.wind.direction);
export const windDirection = [config.wind.direction[0] / directionLength, config.wind.direction[1] / directionLength] as const;

/** Circular-arc centerline, with a rigid flower head at its tangent. No allocation. */
export function bendPlantPoint(
  rest: Vector3, root: Vector3, height: number, angle: number, head: boolean, result: Vector3,
) {
  const y = head ? height : Math.max(0, Math.min(height, rest.y - root.y));
  const turn = angle * y / height;
  const turn2 = turn * turn;
  const sinc = Math.abs(turn) < 0.01 ? 1 - turn2 / 6 + turn2 * turn2 / 120 : Math.sin(turn) / turn;
  const cosc = Math.abs(turn) < 0.01 ? turn * (0.5 - turn2 / 24 + turn2 * turn2 / 720) : (1 - Math.cos(turn)) / turn;
  const qx = rest.x - root.x, qz = rest.z - root.z;
  const qy = rest.y - root.y - y;
  const along = qx * windDirection[0] + qz * windDirection[1];
  const delta = along * (Math.cos(turn) - 1) + qy * Math.sin(turn);
  return result.set(
    root.x + qx + windDirection[0] * (y * cosc + delta),
    root.y + y * sinc + qy * Math.cos(turn) - along * Math.sin(turn),
    root.z + qz + windDirection[1] * (y * cosc + delta),
  );
}
