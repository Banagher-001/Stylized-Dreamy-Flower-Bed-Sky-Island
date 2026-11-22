import { Mesh } from 'three';
import type { Material, Scene } from 'three';
import { createStoneMaterial } from '../materials/createStoneMaterial';
import { pillarMasonry } from '../config/pillarMasonry';
import type { PillarName } from '../config/pillarMasonry';
import { magicStyle } from './magicStyle';

export function createPillarAppearance(scene: Scene, column: PillarName = 'columnUpperLeft') {
  const shaft = scene.getObjectByName(`${column}-shaft`);
  if (!shaft) throw new Error(`Missing shaft for ${column}.`);
  const body = createStoneMaterial(pillarMasonry[column].colors);
  const joint = createStoneMaterial(magicStyle.joint);
  body.name = 'reading-pillar-stone';joint.name = 'reading-pillar-joint';
  const originals = new Map<Mesh, Material | Material[]>();
  shaft.traverse((object) => {
    if (!(object instanceof Mesh) || !new RegExp(`^${column}-(block|joint)-\\d+$`).test(object.name)) return;
    originals.set(object, object.material);
    object.material = object.name.includes('-joint-') ? joint : body;
  });
  let disposed = false;
  return {
    get bindings() { return [...originals.keys()].map((mesh) => ({ object: mesh.name, material: (mesh.material as Material).name })); },
    dispose() {
      if (disposed) return;disposed = true;
      for (const [mesh, material] of originals) mesh.material = material;
      originals.clear();body.dispose();joint.dispose();
    },
  };
}
