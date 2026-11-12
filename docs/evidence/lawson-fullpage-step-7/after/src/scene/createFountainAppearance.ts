import { Mesh } from 'three';
import type { Material, Scene } from 'three';
import { createFountainStoneMaterial } from '../materials/createFountainStoneMaterial';
import { createRefinedWaterMaterial } from '../materials/createRefinedWaterMaterial';
import type { WaterState } from '../materials/createWaterMaterial';

/** Reversible, instance-local bindings. Geometry, shadows and jet remain original. */
export function createFountainAppearance(scene: Scene, state: WaterState) {
  const fountain = scene.getObjectByName('fountain');
  const surface = fountain?.getObjectByName('fountain-water');
  const stones: Mesh[] = [];
  fountain?.traverse((o) => { if (o instanceof Mesh && /^fountain-(base|rim-wall|coping-\d|pedestal(-foot|-cap)?)$/.test(o.name)) stones.push(o); });
  if (!(surface instanceof Mesh) || stones.length !== 13) throw new Error('Pool finish requires the complete original fountain.');
  const water = createRefinedWaterMaterial(state), stone = createFountainStoneMaterial();
  const originals = new Map<Mesh, Material | Material[]>();
  for (const mesh of [...stones, surface]) { originals.set(mesh, mesh.material);mesh.material = mesh === surface ? water : stone; }
  let disposed = false;
  return {
    metadata: { bindings: [...originals.keys()].map((m) => ({ object: m.name, material: (m.material as Material).name })), newGeometries: 0, newTextures: 0, extraPasses: 0 },
    dispose() { if (disposed) return;disposed = true;for (const [mesh, material] of originals) mesh.material = material;originals.clear();water.dispose();stone.dispose(); },
  };
}
