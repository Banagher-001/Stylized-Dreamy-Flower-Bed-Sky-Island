import { Box3, Mesh, Raycaster, Vector3 } from 'three';
import { createScene } from '../../src/scene/createScene';
import { createPillarAppearance } from '../../src/tour/createPillarAppearance';
import { createPillarMagic } from '../../src/tour/createPillarMagic';
import { filmStations, sampleFilmPresentation } from '../../src/tour/filmReading';
import { tourPoses, sampleTour, resolveTourPose } from '../../src/tour/route';
import { inspectMagic } from './inspect_magic';

export async function inspectFilm(aspects, aboutStations) {
  const prior = await inspectMagic(aspects, aboutStations);
  const world = createScene();world.update(2);world.scene.updateMatrixWorld(true);
  const originals = [];
  const digest = async a => Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', a.buffer))).map(x=>x.toString(16).padStart(2,'0')).join('');
  const meshes=[];world.scene.traverse(o=>{if(o.isMesh)meshes.push(o)});
  for(const mesh of meshes){const attrs={};for(const[n,a]of Object.entries(mesh.geometry.attributes))attrs[n]=await digest(a.array);originals.push({mesh,material:mesh.material,geometry:mesh.geometry,transform:JSON.stringify([mesh.position,mesh.quaternion,mesh.scale]),attrs});}
  const aAppearance=createPillarAppearance(world.scene),bAppearance=createPillarAppearance(world.scene,'columnRight');
  const aMagic=createPillarMagic(world.scene),bMagic=createPillarMagic(world.scene,{column:'columnRight',number:'02',stations:filmStations,poses:[tourPoses.B,tourPoses.B2,tourPoses.B3,tourPoses.B4]});
  if(!aMagic||!bMagic)throw new Error('Decoration unavailable');
  let changed=0;
  for(const o of originals){if(o.mesh.geometry!==o.geometry||JSON.stringify([o.mesh.position,o.mesh.quaternion,o.mesh.scale])!==o.transform)throw new Error('Original transform/geometry changed');for(const[n,h]of Object.entries(o.attrs))if(await digest(o.mesh.geometry.attributes[n].array)!==h)throw new Error('Original buffer changed');if(o.mesh.material!==o.material){changed++;if(!/^column(UpperLeft|Right)-(block|joint)-\d+$/.test(o.mesh.name))throw new Error('Material scope leaked');}}
  if(changed!==14)throw new Error('Expected 14 shaft bindings');
  const faces=[];const ray=new Raycaster();
  for(const entry of bMagic.metadata.anchors){
    const glyph=world.scene.getObjectByName('pillar-sigil-'+entry.station),stone=world.scene.getObjectByName(entry.stone),half=entry.size/2,[min,max]=entry.faceBounds;
    if(!(glyph instanceof Mesh)||entry.local[0]-half<min[0]+.049999||entry.local[0]+half>max[0]-.049999||entry.local[1]-half<min[1]+.049999||entry.local[1]+half>max[1]-.049999||Math.abs(entry.local[2]-max[2]-.008)>1e-8)throw new Error('Unsafe inscription face');
    if(!glyph.material.depthTest||glyph.material.depthWrite||glyph.castShadow)throw new Error('Wrong depth/shadow flags');
    const p=bMagic.getAnchor(entry.station);ray.set(p.clone().add(new Vector3(0,0,1)),new Vector3(0,0,-1));const front=ray.intersectObjects([glyph,stone],false)[0];ray.set(p.clone().add(new Vector3(0,0,-1)),new Vector3(0,0,1));const back=ray.intersectObjects([glyph,stone],false)[0];
    if(front?.object!==glyph||back?.object!==stone)throw new Error('Occlusion wrong');faces.push({...entry,worldAnchor:p.toArray(),frontFirst:front.object.name,backFirst:back.object.name});
  }
  const solids=originals.filter(o=>o.mesh.castShadow).map(o=>o.mesh),views=[],plateaus=[],envelopes=[];
  const anchor=new Vector3();
  for(const aspect of aspects)for(const s of filmStations){
    const frame=sampleTour(s.stop),pose=resolveTourPose(frame.pose,aspect);world.setAspect(aspect);world.setViewHeight(pose.viewHeight);world.camera.position.set(...pose.position);world.camera.lookAt(...pose.target);world.camera.updateMatrixWorld(true);
    anchor.set(4.41,s.y,-1);const projected=anchor.clone().project(world.camera);ray.set(new Vector3(...pose.position),anchor.clone().sub(world.camera.position).normalize());const hit=ray.intersectObjects(solids,false)[0];
    if(!hit?.object.name.startsWith('columnRight-block-')||Math.abs((projected.x+1)/2-.28)>1e-6||Math.abs(projected.y)>1e-6||frame.filmReading?.station.id!==s.id)throw new Error('Wrong film station view');
    const samples=Array.from({length:5},(_,i)=>sampleTour(s.start+(s.end-s.start)*(.32+i*.11)));
    if(samples.some(p=>JSON.stringify(p.pose)!==JSON.stringify(samples[0].pose)||sampleFilmPresentation(p.filmReading).body!==1))throw new Error('Film plateau moves');
    views.push({station:s.id,aspect,firstHit:hit.object.name,pose});plateaus.push({station:s.id,aspect,samples:5,stationary:true});
    bMagic.update(frame.filmReading,world.camera,2,false,'pixel');
  }
  let prev=Infinity;
  for(let i=0;i<=1000;i++){const p=sampleTour(4.4+i/1000*3.6);if(p.pose.target[1]>prev+1e-10)throw new Error('Descent reverses');prev=p.pose.target[1];if(p.pose.viewHeight!==3.8||p.pose.position.some((v,j)=>Math.abs(v-p.pose.target[j]-[1.2,4.2,9][j])>1e-9))throw new Error('Reading angle changed');}
  const boundaries=[];
  for(const h of [4.4,4.55,4.7,5.2,5.4,5.55,5.7,6.2,6.4,6.52,6.64,7.04,7.2,7.32,7.44,7.84,8,8.7]){const a=sampleTour(h-1e-7),b=sampleTour(h+1e-7),delta=Math.max(...a.pose.position.map((v,i)=>Math.abs(v-b.pose.position[i])),...a.pose.target.map((v,i)=>Math.abs(v-b.pose.target[i])),Math.abs(a.pose.viewHeight-b.pose.viewHeight));if(delta>1e-4)throw new Error('Boundary jump');boundaries.push({h,delta});}
  for(const s of filmStations)for(const u of [.1,.18,.25,.55,.9,.97])envelopes.push({station:s.id,u,...sampleFilmPresentation(sampleTour(s.start+u*(s.end-s.start)).filmReading)});
  const names=[...aMagic.metadata.anchors,...bMagic.metadata.anchors].map(a=>a.station);aMagic.dispose();bMagic.dispose();aAppearance.dispose();bAppearance.dispose();
  if(originals.some(o=>o.mesh.material!==o.material)||names.some(n=>world.scene.getObjectByName('pillar-sigil-'+n)))throw new Error('Cleanup incomplete');world.dispose();
  return {...prior,film:{views,plateaus,faces,boundaries,envelopes,monotonicDescentSamples:1001,shaftBindings:14,originalBuffersTransformsUnchanged:true,ownedCleanupRestoresBindings:true,b4JoinsT23:true}};
}
