import { Mesh, Raycaster, Vector3 } from 'three';
import { createScene } from '../../src/scene/createScene';
import { createPillarAppearance } from '../../src/tour/createPillarAppearance';
import { createPillarMagic } from '../../src/tour/createPillarMagic';
import { sampleTour, resolveTourPose } from '../../src/tour/route';
import { sampleMagic } from '../../src/tour/magicStyle';
import { inspectReading } from './inspect_reading';

export async function inspectMagic(aspects, stations) {
  const route=await inspectReading(aspects,stations);
  const world=createScene();world.update(2);world.scene.updateMatrixWorld(true);
  const originals=[];
  const digest=async values=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',values.buffer))).map(v=>v.toString(16).padStart(2,'0')).join('');
  const meshes=[];world.scene.traverse(o=>{if(o.isMesh)meshes.push(o)});
  for(const mesh of meshes){const attributes={};for(const [name,a]of Object.entries(mesh.geometry.attributes))attributes[name]=await digest(a.array);originals.push({mesh,material:mesh.material,geometry:mesh.geometry,transform:JSON.stringify([mesh.position,mesh.quaternion,mesh.scale]),attributes});}
  const appearance=createPillarAppearance(world.scene),magic=createPillarMagic(world.scene);
  if(!magic)throw new Error('Missing magic');
  let changed=0;
  for(const before of originals){const mesh=before.mesh;if(mesh.geometry!==before.geometry||JSON.stringify([mesh.position,mesh.quaternion,mesh.scale])!==before.transform)throw new Error('Original geometry/transform changed');for(const [name,h]of Object.entries(before.attributes))if(await digest(mesh.geometry.attributes[name].array)!==h)throw new Error('Original buffer changed');if(mesh.material!==before.material){changed++;if(!/^columnUpperLeft-(block|joint)-\d+$/.test(mesh.name))throw new Error('Material leaked beyond first shaft');}}
  if(changed!==7)throw new Error('Unexpected material bindings');
  const faces=[];const ray=new Raycaster();
  for(const entry of magic.metadata.anchors){
    const glyph=world.scene.getObjectByName('pillar-sigil-'+entry.station),stone=world.scene.getObjectByName(entry.stone);if(!(glyph instanceof Mesh))throw new Error('Missing glyph mesh');
    const [min,max]=entry.faceBounds,half=entry.size/2;
    if(entry.local[0]-half<min[0]+.049999||entry.local[0]+half>max[0]-.049999||entry.local[1]-half<min[1]+.049999||entry.local[1]+half>max[1]-.049999||Math.abs(entry.local[2]-max[2]-.008)>1e-8)throw new Error('Glyph crosses bevel/joint');
    if(!glyph.material.depthTest||glyph.material.depthWrite||glyph.castShadow)throw new Error('Incorrect glyph depth/shadow flags');
    const point=magic.getAnchor(entry.station);ray.set(point.clone().add(new Vector3(0,0,1)),new Vector3(0,0,-1));const front=ray.intersectObjects([glyph,stone],false)[0];
    ray.set(point.clone().add(new Vector3(0,0,-1)),new Vector3(0,0,1));const back=ray.intersectObjects([glyph,stone],false)[0];
    if(front?.object!==glyph||back?.object!==stone)throw new Error('Glyph surface/occlusion incorrect');
    faces.push({...entry,worldAnchor:point.toArray(),frontFirst:front.object.name,backFirst:back.object.name});
  }
  const envelopes=[];
  for(const s of stations){
    for(const u of [.1,.18,.25,.3,.55,.8,.94,.97]){
      const frame=sampleTour(s.start+u*.8),state=sampleMagic(frame.reading);if(Object.values(state).some(v=>!Number.isFinite(v)))throw new Error('Invalid magic state');
      if(u===.18&&!(state.glyph>0&&state.title>0&&state.body===0))throw new Error('Title should precede body');
      if(u===.25&&!(state.title===1&&Math.abs(state.body-.5)<1e-10))throw new Error('Body reveal wrong');
      if(u>=.3&&u<=.8&&!(state.title>1-1e-10&&state.body>1-1e-10&&state.glyph>1-1e-10))throw new Error('Reading plateau incomplete');
      if(u===.97&&state.body!==0)throw new Error('Body should leave before title');
      envelopes.push({station:s.id,u,...state});
    }
  }
  for(const h of [0,1.29,3.7,4.95,12.3])if(sampleMagic(sampleTour(h).reading).veil!==0)throw new Error('Magic outside reading region');
  const anchorsBefore=JSON.stringify(magic.metadata.anchors);
  for(const aspect of aspects)for(const s of stations){const frame=sampleTour(s.stop),pose=resolveTourPose(frame.pose,aspect);world.setAspect(aspect);world.setViewHeight(pose.viewHeight);world.camera.position.set(...pose.position);world.camera.lookAt(...pose.target);magic.update(frame.reading,world.camera,2,false,'pixel');}
  if(JSON.stringify(magic.metadata.anchors)!==anchorsBefore)throw new Error('Resizing moved surface anchors');
  const resources=magic.metadata,bindings=appearance.bindings;magic.dispose();appearance.dispose();
  if(originals.some(x=>x.mesh.material!==x.material)||world.scene.getObjectByName('pillar-light-dust'))throw new Error('Owned cleanup incomplete');
  world.dispose();return {...route,materialIsolation:{changedMeshes:changed,bindings,otherMaterialsUnchanged:true,originalBuffersAndTransformsUnchanged:true},inscriptionFaces:faces,magicEnvelopes:envelopes,magicResources:resources,resizeKeepsLocalAnchors:true,ownedCleanupRestoresBindings:true};
}
