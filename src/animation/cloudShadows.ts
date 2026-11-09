import { cloudShadowConfig as config } from '../config/cloudShadows';
import { lightingConfig } from '../config/lighting';
import { windDirection } from './environmentMotion';

const sun = lightingConfig.sun.position;
export const cloudProjection = [sun[0] / sun[1], sun[2] / sun[1]] as const;
export const cloudDirection = windDirection;
export const cloudRepeatSeconds = config.period / config.speed;
export function cloudDrift(time: number) {
  return ((time * config.speed) % config.period + config.period) % config.period;
}
export function createCloudShadowState(enabled: boolean, initialTime: number) {
  let lastTime = initialTime;
  const state = {
    enabled,
    active: { value: enabled ? 1 : 0 },
    drift: { value: cloudDrift(initialTime) },
    failures: [] as string[],
    update(time: number) {
      if (!enabled || time === lastTime) return;
      lastTime = time;state.drift.value = cloudDrift(time);
    },
    snapshot() { return { enabled, active: state.active.value, time: lastTime, drift: state.drift.value, repeatSeconds: cloudRepeatSeconds, failures: [...state.failures] }; },
  };
  return state;
}
export type CloudShadowState = ReturnType<typeof createCloudShadowState>;

const smooth = (a: number, b: number, x: number) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));return t * t * (3 - 2 * t);
};
const softMin = (a: number, b: number) => {
  const h = Math.max(config.unionSoftness - Math.abs(a - b), 0) / config.unionSoftness;
  return Math.min(a, b) - h * h * config.unionSoftness * .25;
};
/** Reference field for placement/continuity diagnostics; not a per-frame CPU raster. */
export function sampleCloudCoverage(x: number, y: number, z: number, time: number) {
  const px = x - y * cloudProjection[0], pz = z - y * cloudProjection[1];
  const along = px * cloudDirection[0] + pz * cloudDirection[1] - cloudDrift(time);
  const across = -px * cloudDirection[1] + pz * cloudDirection[0];
  let clear = 1;
  for (const patch of config.patches) {
    const d = along - patch.along;
    const u = (d - config.period * Math.floor(d / config.period + .5)) / patch.radius[0];
    const v = (across - patch.across) / patch.radius[1];
    const a = u * u + v * v;
    const b = ((u - .48) * 1.3) ** 2 + ((v + .16) * 1.18) ** 2;
    const c = ((u + .44) * 1.15) ** 2 + ((v - .22) * 1.38) ** 2;
    const cover = (1 - smooth(...config.softness, softMin(softMin(a, b), c))) * patch.density;
    clear *= 1 - cover;
  }
  return 1 - clear;
}
