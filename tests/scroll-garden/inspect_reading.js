import { Raycaster, Vector3 } from 'three';
import { createScene } from '../../src/scene/createScene';
import { sampleTour, resolveTourPose } from '../../src/tour/route';
import { inspectRoute } from './inspect_route';

export async function inspectReading(aspects, stations) {
  const route = await inspectRoute(aspects);
  const world = createScene();
  world.update(2);
  world.scene.updateMatrixWorld(true);
  const stones = [];
  world.scene.traverse((object) => { if (object.isMesh && object.castShadow) stones.push(object); });
  const ray = new Raycaster(), eye = new Vector3(), anchor = new Vector3();
  const views = [], plateaus = [];
  for (const aspect of aspects) for (const station of stations) {
    const sample = sampleTour(station.stop);
    const pose = resolveTourPose(sample.pose, aspect);
    world.setAspect(aspect);
    world.setViewHeight(pose.viewHeight);
    world.camera.position.set(...pose.position);
    world.camera.lookAt(...pose.target);
    world.camera.updateMatrixWorld(true);
    anchor.set(-2.34, station.y, -2.9);
    const screen = anchor.clone().project(world.camera);
    eye.set(...pose.position);
    ray.set(eye, anchor.clone().sub(eye).normalize());
    const hit = ray.intersectObjects(stones, false)[0];
    if (!hit?.object.name.startsWith('columnUpperLeft-block-')) throw new Error(`${station.id} occluded by ${hit?.object.name}`);
    if (Math.abs((screen.x + 1) / 2 - .34) > 1e-6 || Math.abs(screen.y) > 1e-6) throw new Error('Station anchor drift');
    if (Math.abs(sample.pose.target[1] - station.y) > 1e-8 || sample.reading?.station.id !== station.id || sample.reading.opacity !== 1) throw new Error('Station is not fully readable');
    const poses = Array.from({length:5}, (_,i) => sampleTour(station.fullStart + (station.fullEnd-station.fullStart)*(.02+i*.24)));
    if (poses.some((p) => JSON.stringify(p.pose) !== JSON.stringify(poses[0].pose) || p.reading?.opacity !== 1)) throw new Error('Reading plateau moves');
    views.push({ station:station.id, aspect, firstHit:hit.object.name, screenX:(screen.x+1)/2, screenY:(1-screen.y)/2, pose });
    plateaus.push({station:station.id,aspect,sampledPositions:poses.length,stationary:true});
  }
  const crossing = [];
  for (const h of [1.3,1.42,1.54,1.94,2.1,2.22,2.34,2.74,2.9,3.02,3.14,3.54,3.7,4.4]) {
    const a=sampleTour(h-1e-7), b=sampleTour(h+1e-7);
    const poseDelta=Math.max(...a.pose.position.map((v,i)=>Math.abs(v-b.pose.position[i])),...a.pose.target.map((v,i)=>Math.abs(v-b.pose.target[i])),Math.abs(a.pose.viewHeight-b.pose.viewHeight));
    const opacityDelta=Math.abs((a.reading?.opacity??0)-(b.reading?.opacity??0));
    if (poseDelta>1e-4 || opacityDelta>1e-4) throw new Error(`Reading boundary jump at ${h}`);
    crossing.push({h,poseDelta,opacityDelta});
  }
  let previousY=Infinity;
  for (let i=0;i<=1000;i++) {
    const p=sampleTour(1.3+i/1000*2.4);
    if (p.pose.target[1]>previousY+1e-10) throw new Error('Pillar descent reverses');
    previousY=p.pose.target[1];
    const relative=p.pose.position.map((v,i)=>v-p.pose.target[i]);
    if (relative.some((v,i)=>Math.abs(v-[1.2,4.2,9][i])>1e-9) || p.pose.viewHeight!==3.6) throw new Error('Descent changes reading angle or scale');
  }
  world.dispose();
  return {...route, readingViews:views, readingPlateaus:plateaus, readingBoundaries:crossing, monotonicDescentSamples:1001,scope:route.scope+' Extended to all three first-pillar stations and actual text-read windows from the first-step CSV.'};
}
