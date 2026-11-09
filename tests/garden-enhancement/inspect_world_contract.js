import { Vector3 } from 'three';
import { createScene } from '../../src/scene/createScene';
import { tourStages, tourTotalH, tourPoses, resolveTourPose } from '../../src/tour/route';

const sha = async data => [...new Uint8Array(await crypto.subtle.digest('SHA-256', data))].map(v => v.toString(16).padStart(2, '0')).join('');
const buffer = async attribute => ({ count: attribute.count, itemSize: attribute.itemSize, bytes: attribute.array.byteLength, sha256: await sha(attribute.array.buffer) });

/** Run the identical inspector separately against the Step2 archive and candidate.
 * Exclude only the three allowed fountain effect meshes, not the entire pool.
 */
export async function inspectWorldContract() {
  const world = createScene({}, 'refined', 'lively');
  world.update(2);world.scene.updateMatrixWorld(true);
  const objects = [], geometry = new Set(), materials = new Set();
  const walk = async (object, path) => {
    if (object.name === 'fountain-effects') return;
    const item = { path, type: object.type, name: object.name, matrix: [...object.matrix.elements], visible: object.visible,
      castShadow: object.castShadow, receiveShadow: object.receiveShadow };
    if (object.geometry) {
      geometry.add(object.geometry);
      item.attributes = {};
      for (const key of Object.keys(object.geometry.attributes).sort()) item.attributes[key] = await buffer(object.geometry.attributes[key]);
      if (object.geometry.index) item.index = await buffer(object.geometry.index);
      if (object.instanceMatrix) item.instanceMatrix = await buffer(object.instanceMatrix);
      if (object.instanceColor) item.instanceColor = await buffer(object.instanceColor);
      item.count = object.count;
      item.materials = (Array.isArray(object.material) ? object.material : [object.material]).map(m => {
        materials.add(m);
        return { type: m.type, name: m.name, color: m.color?.getHexString(), opacity: m.opacity, transparent: m.transparent,
          depthTest: m.depthTest, depthWrite: m.depthWrite, flatShading: m.flatShading,
          cacheKey: m.customProgramCacheKey(), compile: m.onBeforeCompile.toString() };
      });
    }
    if (object.isLight) item.light = { color: object.color.getHexString(), intensity: object.intensity,
      groundColor: object.groundColor?.getHexString(), shadow: object.shadow ? { mapSize: object.shadow.mapSize.toArray(), bias: object.shadow.bias,
        normalBias: object.shadow.normalBias, camera: [object.shadow.camera.left, object.shadow.camera.right, object.shadow.camera.top,
          object.shadow.camera.bottom, object.shadow.camera.near, object.shadow.camera.far] } : null };
    objects.push(item);
    for (let i = 0; i < object.children.length; i++) await walk(object.children[i], path + '/' + i + ':' + object.children[i].name);
  };
  await walk(world.scene, 'scene');
  const effects = [];
  for (const name of ['fountain-water-column', 'fountain-water-crown', 'fountain-water-drops']) {
    const mesh = world.scene.getObjectByName(name), attributes = {};
    for (const key of Object.keys(mesh.geometry.attributes)) attributes[key] = await buffer(mesh.geometry.attributes[key]);
    effects.push({ name, attributes, vertices: mesh.geometry.attributes.position.count, triangles: mesh.geometry.index?.count / 3 || mesh.geometry.attributes.position.count / 3,
      materialCacheKey: mesh.material.customProgramCacheKey(), materialName: mesh.material.name });
  }
  const result = { objects, protectedObjectCount: objects.length, protectedGeometryCount: geometry.size, protectedMaterialCount: materials.size,
    protectedSha256: await sha(new TextEncoder().encode(JSON.stringify(objects))), effects,
    fountainRootMatrix: [...world.scene.getObjectByName('fountain-effects').matrix.elements],
    route: { totalH: tourTotalH, stages: tourStages, poses: tourPoses },
    routeSha256: await sha(new TextEncoder().encode(JSON.stringify([tourTotalH, tourStages, tourPoses]))) };
  world.dispose();return result;
}

export function projectOrb(aspect, sampleWidth, key = 'W', time = 2) {
  const world = createScene({}, 'refined', 'lively'), pose = resolveTourPose(tourPoses[key], aspect);
  world.update(time);world.setAspect(aspect);world.setViewHeight(pose.viewHeight);world.camera.position.set(...pose.position);world.camera.lookAt(...pose.target);
  world.scene.updateMatrixWorld(true);world.camera.updateMatrixWorld(true);
  const orb = world.scene.getObjectByName('fountain-water-crown'), positions = orb.geometry.attributes.position, p = new Vector3();
  let x0 = 1, y0 = 1, x1 = -1, y1 = -1;
  for (let i = 0; i < positions.count; i++) {
    p.fromBufferAttribute(positions, i).applyMatrix4(orb.matrixWorld).project(world.camera);
    x0 = Math.min(x0, p.x);x1 = Math.max(x1, p.x);y0 = Math.min(y0, p.y);y1 = Math.max(y1, p.y);
  }
  world.dispose();return { left: (x0 + 1) / 2, right: (x1 + 1) / 2, top: (1 - y1) / 2, bottom: (1 - y0) / 2, diameterSamplePixels: (x1 - x0) * sampleWidth / 2 };
}
