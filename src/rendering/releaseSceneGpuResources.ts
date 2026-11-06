import { DirectionalLight, InstancedMesh, Mesh, Points, ShaderMaterial, Texture } from 'three';
import type { BufferGeometry, Material, Scene } from 'three';

/** Detach the lost GPU generation while retaining all CPU scene/instance data. */
export function releaseSceneGpuResources(scene: Scene) {
  const geometries = new Set<BufferGeometry>();
  const materials = new Set<Material>();
  const textures = new Set<Texture>();
  scene.traverse((object) => {
    if (object instanceof Mesh || object instanceof Points) {
      geometries.add(object.geometry);
      for (const material of Array.isArray(object.material) ? object.material : [object.material]) {
        materials.add(material);
      }
    }
    if (object instanceof InstancedMesh) object.dispose();
    if (object instanceof DirectionalLight) {
      object.shadow.map?.dispose();
      object.shadow.mapPass?.dispose();
    }
  });
  for (const geometry of geometries) geometry.dispose();
  for (const material of materials) {
    for (const value of Object.values(material)) if (value instanceof Texture) textures.add(value);
    if (material instanceof ShaderMaterial) for (const uniform of Object.values(material.uniforms)) {
      const values = Array.isArray(uniform.value) ? uniform.value : [uniform.value];
      for (const value of values) if (value instanceof Texture) textures.add(value);
    }
    material.dispose();
  }
  for (const texture of textures) texture.dispose();
}
