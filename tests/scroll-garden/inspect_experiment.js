import { Box3, Mesh, Raycaster, Vector3 } from 'three';
import { createScene } from '../../src/scene/createScene';
import { createPillarAppearance } from '../../src/tour/createPillarAppearance';
import { createPillarMagic } from '../../src/tour/createPillarMagic';
import { experimentStations, sampleExperimentPresentation } from '../../src/tour/experimentReading';
import { sampleTour, resolveTourPose, tourPoses } from '../../src/tour/route';
import { inspectFilm } from './inspect_film';

export async function inspectExperiment(aspects, aboutStations) {
  const previous = await inspectFilm(aspects, aboutStations);
  const world = createScene();world.update(2);world.scene.updateMatrixWorld(true);
  const originals=[];world.scene.traverse(o=>{if(o.isMesh)originals.push({mesh:o,material:o.material,geometry:o.geometry,transform:JSON.stringify([o.position,o.quaternion,o.scale])})});
  const appearance=createPillarAppearance(world.scene,'columnLower');
  const magic=createPillarMagic(world.scene,{column:'columnLower',number:'03',stations:experimentStations,poses:[tourPoses.C,tourPoses.C2,tourPoses.C3]});
  if(!magic)throw Error('Missing C decoration');
  const changed=originals.filter(o=>o.mesh.material!==o.material);
  if(changed.length!==7||changed.some(o=>!/^columnLower-(block|joint)-\d+$/.test(o.mesh.name)))throw Error('C material scope');
  if(originals.some(o=>o.geometry!==o.mesh.geometry||o.transform!==JSON.stringify([o.mesh.position,o.mesh.quaternion,o.mesh.scale])))throw Error('Original structure mutated');
  const solids=originals.filter(o=>o.mesh.castShadow).map(o=>o.mesh),ray=new Raycaster(),faces=[],views=[],plateaus=[];
  for(const entry of magic.metadata.anchors){
    const glyph=world.scene.getObjectByName('pillar-sigil-'+entry.station),stone=world.scene.getObjectByName(entry.stone),half=entry.size/2,[min,max]=entry.faceBounds;
    if(!(glyph instanceof Mesh)||entry.local[0]-half<min[0]+.049999||entry.local[0]+half>max[0]-.049999||entry.local[1]-half<min[1]+.049999||entry.local[1]+half>max[1]-.049999||Math.abs(entry.local[2]-max[2]-.008)>1e-8)throw Error('Unsafe C face');
    if(!glyph.material.depthTest||glyph.material.depthWrite||glyph.castShadow)throw Error('C depth flags');
    const p=magic.getAnchor(entry.station);ray.set(p.clone().add(new Vector3(0,0,1)),new Vector3(0,0,-1));const front=ray.intersectObjects([glyph,stone],false)[0];ray.set(p.clone().add(new Vector3(0,0,-1)),new Vector3(0,0,1));const back=ray.intersectObjects([glyph,stone],false)[0];
    if(front?.object!==glyph||back?.object!==stone)throw Error('C occlusion');faces.push({...entry,worldAnchor:p.toArray(),frontFirst:front.object.name,backFirst:back.object.name});
  }
  for(const aspect of aspects)for(const station of experimentStations){
    const frame=sampleTour(station.stop),pose=resolveTourPose(frame.pose,aspect);world.setAspect(aspect);world.setViewHeight(pose.viewHeight);world.camera.position.set(...pose.position);world.camera.lookAt(...pose.target);world.camera.updateMatrixWorld(true);
    const anchor=new Vector3(2.96,station.y,5.09),projected=anchor.clone().project(world.camera);ray.set(world.camera.position,anchor.clone().sub(world.camera.position).normalize());const hit=ray.intersectObjects(solids,false)[0];
    if(!hit?.object.name.startsWith('columnLower-block-')||Math.abs((projected.x+1)/2-.34)>1e-6||Math.abs(projected.y)>1e-6||frame.experimentReading?.station.id!==station.id)throw Error('C framing/visibility');
    const samples=Array.from({length:5},(_,i)=>sampleTour(station.start+(station.end-station.start)*(.32+i*.11)));
    if(samples.some(s=>JSON.stringify(s.pose)!==JSON.stringify(samples[0].pose)||sampleExperimentPresentation(s.experimentReading).body<1-1e-10))throw Error('C reading plateau');
    views.push({station:station.id,aspect,pose,firstHit:hit.object.name});plateaus.push({station:station.id,aspect,samples:5,stationary:true});
  }
  let prior=Infinity;for(let i=0;i<=1000;i++){const s=sampleTour(8.7+i/1000*2.4);if(s.pose.target[1]>prior+1e-9)throw Error('C reverses');prior=s.pose.target[1];if(s.pose.position.some((v,i)=>Math.abs(v-s.pose.target[i]-[1.2,4.2,9][i])>1e-8))throw Error('C angle changes');}
  const boundaries=[8.7,8.82,8.94,9.34,9.5,9.65,9.8,10.3,10.5,10.59,10.68,10.98,11.1,11.5,11.8].map(h=>{const a=sampleTour(h-1e-7),b=sampleTour(h+1e-7),delta=Math.max(...a.pose.position.map((v,i)=>Math.abs(v-b.pose.position[i])),...a.pose.target.map((v,i)=>Math.abs(v-b.pose.target[i])),Math.abs(a.pose.viewHeight-b.pose.viewHeight));if(delta>1e-4)throw Error('C boundary '+h);return{h,delta};});
  magic.dispose();appearance.dispose();if(originals.some(o=>o.mesh.material!==o.material)||world.scene.getObjectByName('pillar-sigil-C2'))throw Error('C ownership cleanup');world.dispose();
  return {...previous,experiment:{views,plateaus,faces,boundaries,monotonicSamples:1001,shaftBindings:7,originalStructureUnchanged:true,ownedCleanupRestoresBindings:true,c3JoinsT3W:true}};
}

export function inspectExperienceFrame({pose,host,area}) {
  const world=createScene();world.scene.updateMatrixWorld(true);world.setAspect(host.width/host.height);world.setViewHeight(Number(pose.viewHeight));world.camera.position.set(...JSON.parse(pose.cameraPosition));world.camera.lookAt(...JSON.parse(pose.cameraTarget));world.camera.updateMatrixWorld(true);
  const result=[];
  for(const name of ['columnUpperLeft','columnRight','columnLower','fountain']){
    const box=new Box3().setFromObject(world.scene.getObjectByName(name)),points=[];
    for(const x of [box.min.x,box.max.x])for(const y of [box.min.y,box.max.y])for(const z of [box.min.z,box.max.z]){
      const p=new Vector3(x,y,z).project(world.camera),sx=host.left+(p.x+1)*host.width/2,sy=host.top+(1-p.y)*host.height/2;
      if(sx<area.left||sx>area.right||sy<area.top||sy>area.bottom)throw Error('Live chrome crops '+name+': '+[sx,sy]);points.push([sx,sy]);
    }result.push({name,allEightCornersInsideLiveArea:true,points});
  }world.dispose();return result;
}

/** Test-only conservative projection of the third shaft's original geometry. */
export function projectShaftBounds({pose,width}) {
  const world=createScene();world.scene.updateMatrixWorld(true);
  const aspect=Number(pose.aspect),height=width/aspect;
  world.setAspect(aspect);world.setViewHeight(Number(pose.viewHeight));
  world.camera.position.set(...JSON.parse(pose.cameraPosition));world.camera.lookAt(...JSON.parse(pose.cameraTarget));world.camera.updateMatrixWorld(true);
  const box=new Box3().setFromObject(world.scene.getObjectByName('columnLower-shaft')),points=[];
  for(const x of [box.min.x,box.max.x])for(const y of [box.min.y,box.max.y])for(const z of [box.min.z,box.max.z]){
    const p=new Vector3(x,y,z).project(world.camera);points.push([(p.x+1)*width/2,(1-p.y)*height/2]);
  }
  const result={left:Math.min(...points.map(p=>p[0])),right:Math.max(...points.map(p=>p[0])),top:Math.min(...points.map(p=>p[1])),bottom:Math.max(...points.map(p=>p[1])),points,hostHeight:height,geometry:'columnLower-shaft original world AABB, eight projected corners'};
  world.dispose();return result;
}
