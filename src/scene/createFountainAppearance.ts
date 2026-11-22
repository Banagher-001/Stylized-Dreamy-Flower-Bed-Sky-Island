import { Mesh } from 'three';
import type { Material, Scene } from 'three';
import { createFountainStoneMaterial } from '../materials/createFountainStoneMaterial';
import { createRefinedWaterMaterial } from '../materials/createRefinedWaterMaterial';
import type { WaterState } from '../materials/createWaterMaterial';

/** Reversible bindings for the lining, masonry courses, pedestal and water. */
export function createFountainAppearance(scene: Scene, state: WaterState) {
  const fountain = scene.getObjectByName('fountain');
  const surface = fountain?.getObjectByName('fountain-water');
  const rim = fountain?.getObjectByName('fountain-rim');
  if (!fountain || !rim || !(surface instanceof Mesh)) throw new Error('Pool finish requires a complete fountain.');
  const stones: Mesh[] = [];
  for (const name of ['base', 'rim-wall', 'pedestal-foot', 'pedestal', 'pedestal-cap']) {
    const mesh = fountain.getObjectByName(`fountain-${name}`);
    if (!(mesh instanceof Mesh)) throw new Error(`Missing fountain ${name}.`);
    stones.push(mesh);
  }
  rim.traverse((object) => {
    if (object instanceof Mesh && typeof object.userData.poolEdge === 'number') stones.push(object);
  });
  const water = createRefinedWaterMaterial(state), stone = createFountainStoneMaterial();
  const dampStone = createFountainStoneMaterial('damp');
  const shelfStone = createFountainStoneMaterial('shelf');
  const originals = new Map<Mesh, Material | Material[]>();
  for (const mesh of [...stones, surface]) {
    originals.set(mesh, mesh.material);
    const damp = mesh.name.startsWith('fountain-pedestal') || mesh.userData.poolBand === 'lining';
    if (mesh === surface) mesh.material = water;
    else if (mesh.userData.poolBand === 'shelf') mesh.material = shelfStone;
    else mesh.material = damp ? dampStone : stone;
  }
  let disposed = false;
  return {
    metadata: { bindings: [...originals.keys()].map((m) => ({ object: m.name, material: (m.material as Material).name })), newGeometries: 0, newTextures: 0, extraPasses: 0 },
    dispose() {
      if (disposed) return;
      disposed = true;
      for (const [mesh, material] of originals) mesh.material = material;
      originals.clear();
      water.dispose();
      stone.dispose();
      dampStone.dispose();
      shelfStone.dispose();
    },
  };
}
