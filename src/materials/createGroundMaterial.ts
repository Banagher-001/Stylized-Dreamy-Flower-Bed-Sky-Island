import { createArtMaterial } from './createArtMaterial';
import type { EnvironmentState } from '../animation/environmentMotion';

export function createGroundMaterial(environment?: EnvironmentState) {
  return createArtMaterial('ground', environment);
}
