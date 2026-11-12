import { createArtMaterial } from './createArtMaterial';
import type { StoneColors } from './createArtMaterial';

export function createStoneMaterial(colors?: StoneColors) {
  return createArtMaterial('stone', undefined, colors);
}
