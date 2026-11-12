import { Box3, Group, InstancedBufferAttribute, InstancedMesh, Matrix4, Sphere, StreamDrawUsage, Vector3 } from 'three';
import type { Camera } from 'three';
import { birdConfig } from '../config/birds';
import { createBirdPose, sampleBirdPose } from '../animation/birdMotion';
import { createBirdGeometry } from '../geometry/createBirdGeometry';
import { createBirdMaterial } from '../materials/createBirdMaterial';

export interface BirdRect { left: number; top: number; right: number; bottom: number; }
export interface BirdView { bounds: BirdRect; avoid: readonly BirdRect[]; margin: number; key: string; }
const smooth = (n: number) => { const t = Math.min(1, Math.max(0, n));return t * t * (3 - 2 * t); };
export function birdScreenAlpha(x: number, y: number, radius: number, view: BirdView) {
  const edge = Math.min(x - view.bounds.left, view.bounds.right - x, y - view.bounds.top, view.bounds.bottom - y);
  let alpha = smooth((edge + radius) / Math.max(1, radius * 2));
  for (const r of view.avoid) {
    const distance = Math.max(r.left - x, x - r.right, r.top - y, y - r.bottom) - radius - view.margin;
    alpha *= smooth(distance / birdConfig.fadePixels);
  }
  return alpha;
}

/** One bounded instance batch. Vertex hinges use the original sampled wing
 * angles, so each complete bird needs only one matrix and color submission.
 */
export function createBirds() {
  const root = new Group();root.name = 'courtyard-birds';
  const geometry = createBirdGeometry('all'), material = createBirdMaterial();
  const alpha = new InstancedBufferAttribute(new Float32Array(3), 1).setUsage(StreamDrawUsage);
  const wing = new InstancedBufferAttribute(new Float32Array(3), 1).setUsage(StreamDrawUsage);
  geometry.setAttribute('birdAlpha', alpha);geometry.setAttribute('birdWing', wing);
  const mesh = new InstancedMesh(geometry, material, 3);mesh.name = 'courtyard-birds-complete';
  mesh.castShadow = false;mesh.receiveShadow = false;mesh.instanceMatrix.setUsage(StreamDrawUsage);
  mesh.boundingBox = new Box3(new Vector3(-11, 3.8, -10), new Vector3(11, 6.2, 11));mesh.boundingSphere = mesh.boundingBox.getBoundingSphere(new Sphere());root.add(mesh);
  const poses = birdConfig.routes.map(() => createBirdPose());
  const projected = poses.map(() => ({ x: 0, y: 0, radius: 0, alpha: 0 }));
  const point = new Vector3(), scale = new Vector3(), matrix = new Matrix4();
  let lastTime = NaN, presentedTime = NaN, presentedView = '', disposed = false;
  return {
    root,
    metadata: { birds: 3, newGeometries: 1, newTextures: 0, maximumColorDrawCalls: 1, extraPasses: 0, castsShadows: false, trianglesPerBird: geometry.getAttribute('position').count / 3 },
    update(time: number) {
      if (disposed || time === lastTime) return;
      lastTime = time;for (let i = 0; i < poses.length; i++) sampleBirdPose(time, i, poses[i]!);
    },
    present(camera: Camera, view: BirdView) {
      if (disposed || (presentedTime === lastTime && presentedView === view.key)) return;
      presentedTime = lastTime;presentedView = view.key;
      const width = view.bounds.right - view.bounds.left, height = view.bounds.bottom - view.bounds.top;
      let visible = 0;
      for (let i = 0; i < poses.length; i++) {
        const p = poses[i]!, screen = projected[i]!;point.copy(p.position).project(camera);
        screen.x = view.bounds.left + (point.x * .5 + .5) * width;screen.y = view.bounds.top + (.5 - point.y * .5) * height;
        screen.radius = p.scale * birdConfig.bodyRadius * Math.abs(camera.projectionMatrix.elements[5]!) * height * .5;
        screen.alpha = point.z < -1 || point.z > 1 ? 0 : birdScreenAlpha(screen.x, screen.y, screen.radius, view);
        if (screen.alpha < birdConfig.minimumAlpha) continue;
        matrix.compose(p.position, p.rotation, scale.setScalar(p.scale));mesh.setMatrixAt(visible, matrix);
        alpha.setX(visible, screen.alpha);wing.setX(visible, p.leftWing);visible++;
      }
      mesh.count = visible;root.visible = visible > 0;
      if (visible) { mesh.instanceMatrix.needsUpdate = true;alpha.needsUpdate = true;wing.needsUpdate = true; }
    },
    snapshot() { return { time: lastTime, visible: mesh.count, poses: poses.map((p, i) => ({ id: i, position: p.position.toArray(), rotation: p.rotation.toArray(), leftWing: p.leftWing, rightWing: p.rightWing, flap: p.flap, bank: p.bank, scale: p.scale, speed: p.speed, phase: p.phase, screen: { ...projected[i]! } })) }; },
    dispose() { if (disposed) return;disposed = true;mesh.dispose();geometry.dispose();material.dispose();root.removeFromParent();root.clear(); },
  };
}
