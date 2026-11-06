import { Box3, Raycaster, Vector3 } from 'three';
import { createScene } from '../../src/scene/createScene';
import { sampleTour, resolveTourPose, tourPoses, tourStages, tourTotalH } from '../../src/tour/route';

export async function inspectRoute(aspects = [1440 / 794, 1366 / 662, 390 / 738]) {
  const world = createScene();
  world.update(2);
  world.scene.updateMatrixWorld(true);
  const stone = [];
  const colliders = [];
  world.scene.traverse((object) => {
    if (object.isMesh && object.castShadow) {
      stone.push(object);
      colliders.push({ name: object.name, box: new Box3().setFromObject(object).expandByScalar(0.1) });
    }
  });
  const position = new Vector3(), anchor = new Vector3();
  const ray = new Raycaster();
  let minEyeY = Infinity;
  const samples = 1001;
  for (const aspect of aspects) {
    for (let i = 0; i < samples; i++) {
      const sample = sampleTour(i / (samples - 1) * tourTotalH);
      const pose = resolveTourPose(sample.pose, aspect);
      if (![...pose.position, ...pose.target, pose.viewHeight].every(Number.isFinite) || pose.viewHeight <= 0) throw new Error('Invalid camera pose');
      position.set(...pose.position);
      minEyeY = Math.min(minEyeY, position.y);
      if (position.y < 0.25) throw new Error('Camera approaches ground');
      const collision = colliders.find((collider) => collider.box.containsPoint(position));
      if (collision) throw new Error(`Camera inside ${collision.name}`);
    }
  }
  const boundaries = [...new Set([...tourStages.flatMap((stage) => [stage.start, stage.end]), 11.5])].filter((h) => h > 0 && h < tourTotalH);
  let maximumBoundaryDelta = 0;
  for (const h of boundaries) {
    const a = resolveTourPose(sampleTour(h - 0.0000001).pose, aspects[0]);
    const b = resolveTourPose(sampleTour(h + 0.0000001).pose, aspects[0]);
    const delta = Math.max(...a.position.map((v, i) => Math.abs(v - b.position[i])), ...a.target.map((v, i) => Math.abs(v - b.target[i])), Math.abs(a.viewHeight - b.viewHeight));
    maximumBoundaryDelta = Math.max(maximumBoundaryDelta, delta);
    if (delta > 0.0001) throw new Error(`Discontinuity at ${h}`);
  }
  const visibility = [];
  for (const [key, h, column] of [['A', 1.74, 'columnUpperLeft'], ['B', 4.95, 'columnRight'], ['C', 9.14, 'columnLower']]) {
    const sample = sampleTour(h);
    const pose = resolveTourPose(sample.pose, aspects[0]);
    world.camera.position.set(...pose.position);
    world.camera.lookAt(...pose.target);
    world.setAspect(aspects[0]);
    world.setViewHeight(pose.viewHeight);
    world.camera.updateMatrixWorld(true);
    anchor.set(...tourPoses[key].target);
    const projected = anchor.clone().project(world.camera);
    if (Math.abs((projected.x + 1) / 2 - sample.pose.screenX) > 0.000001 || Math.abs(projected.y) > 0.000001) throw new Error('Reading anchor frame incorrect');
    position.set(...pose.position);
    ray.set(position, anchor.clone().sub(position).normalize());
    const hit = ray.intersectObjects(stone, false)[0];
    if (!hit || !hit.object.name.startsWith(column + '-block-')) throw new Error(`Reading shaft occluded: ${column} by ${hit?.object.name}`);
    visibility.push({ column, firstHit: hit.object.name, screenX: (projected.x + 1) / 2, screenY: (-projected.y + 1) / 2 });
  }
  const overview = [];
  for (const aspect of aspects) {
    const pose = resolveTourPose(sampleTour(0).pose, aspect);
    world.camera.position.set(...pose.position);
    world.camera.lookAt(...pose.target);
    world.setAspect(aspect);
    world.setViewHeight(pose.viewHeight);
    world.camera.updateMatrixWorld(true);
    for (const name of ['columnUpperLeft', 'columnRight', 'columnLower', 'fountain']) {
      const box = new Box3().setFromObject(world.scene.getObjectByName(name));
      for (const x of [box.min.x, box.max.x]) for (const y of [box.min.y, box.max.y]) for (const z of [box.min.z, box.max.z]) {
        const p = new Vector3(x, y, z).project(world.camera);
        if (Math.abs(p.x) > 1 || Math.abs(p.y) > 1) throw new Error(`Overview crops ${name} at aspect ${aspect}`);
      }
    }
    overview.push({ aspect, principalObjectsInsideFrame: true });
  }
  const digest = async (values) => Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', values.buffer))).map((x) => x.toString(16).padStart(2, '0')).join('');
  const instances = {};
  const batches = [];
  world.scene.traverse((object) => { if (object.isInstancedMesh) batches.push(object); });
  for (const batch of batches) instances[batch.name] = { matrix: await digest(batch.instanceMatrix.array), color: batch.instanceColor ? await digest(batch.instanceColor.array) : null };
  world.dispose();
  return { geometricSamples: samples * aspects.length, samplesPerAspect: samples, aspects, margin: 0.1, cameraGroundMargin: 0.25, minEyeY, collidingSamples: 0, maximumBoundaryDelta, visibility, overview, instances, totalH: tourTotalH, stages: tourStages, poses: tourPoses, scope: 'Camera eye against conservative static-building bounds, shaft ray visibility at three held poses, and principal object framing; screenshots/review supplement geometry.' };
}
