import { DoubleSide } from 'three';
import { createArtMaterial } from './createArtMaterial';
import type { EnvironmentState } from '../animation/environmentMotion';

export function createVegetationMaterial(surface: 'foliage' | 'flower', environment?: EnvironmentState) {
  const material = createArtMaterial(surface, environment);
  material.side = DoubleSide;
  return material;
}
