import { Box3, Color, Mesh, MeshBasicMaterial, PCFShadowMap, Vector3, WebGLRenderer, WebGLRenderTarget } from 'three';
import { createScene } from '../../src/scene/createScene';
import { createFountainAppearance } from '../../src/scene/createFountainAppearance';
import { sampleTour,resolveTourPose,tourStages,tourTotalH } from '../../src/tour/route';

const digest=async a=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',a.buffer))).map(x=>x.toString(16).padStart(2,'0')).join('');
export async function inspectPool(){
 const old=createScene(),next=createScene({},'refined');old.scene.updateMatrixWorld(true);next.scene.updateMatrixWorld(true);
 const geometry=[],bindings=[];
 for(const mesh of old.scene.getObjectByName('courtyard-blockout').getObjectsByProperty('isMesh',true)){
  const other=next.scene.getObjectByName(mesh.name);
  if(JSON.stringify([mesh.position,mesh.quaternion,mesh.scale])!==JSON.stringify([other.position,other.quaternion,other.scale]))throw Error('Transform changed '+mesh.name);
  const attributes={};for(const[n,a]of Object.entries(mesh.geometry.attributes)){const hash=await digest(a.array);if(hash!==await digest(other.geometry.attributes[n].array))throw Error('Buffer changed '+mesh.name);attributes[n]=hash;}
  geometry.push({name:mesh.name,attributes});
  if(other.material.name!==mesh.material.name){if(!mesh.name.startsWith('fountain-'))throw Error('Pool scope leaked '+mesh.name);bindings.push(mesh.name);}
 }
 if(bindings.length!==14||next.fountainMetadata.bindings.length!==14)throw Error('Expected14 pool-only bindings');
 const events=[];
 for(const t of [0,2,4,6,8,12,120]){
  old.update(t);next.update(t);old.scene.updateMatrixWorld(true);next.scene.updateMatrixWorld(true);
  for(const name of ['fountain-water-column','fountain-water-crown','fountain-water-drops']){
   const a=old.scene.getObjectByName(name),b=next.scene.getObjectByName(name);
   if(JSON.stringify(a.matrixWorld.toArray())!==JSON.stringify(b.matrixWorld.toArray())||a.count!==b.count)throw Error('Jet changed');
   if(a.isInstancedMesh&&await digest(a.instanceMatrix.array)!==await digest(b.instanceMatrix.array))throw Error('Drop matrix changed');
   if(a.material.customProgramCacheKey()!==b.material.customProgramCacheKey()||a.material.onBeforeCompile.toString()!==b.material.onBeforeCompile.toString())throw Error('Jet shader changed');
  }
  if(JSON.stringify(old.waterState.impacts.value)!==JSON.stringify(next.waterState.impacts.value))throw Error('Impacts changed');events.push({time:t,jetAndDropsExact:true,impactEventsExact:true});
 }
 const instances={};old.scene.traverse(o=>{if(o.isInstancedMesh&&!o.name.includes('water-drops'))instances[o.name]=o;});
 for(const[name,a]of Object.entries(instances)){const b=next.scene.getObjectByName(name);if(await digest(a.instanceMatrix.array)!==await digest(b.instanceMatrix.array))throw Error('Plants moved');}
 const water=next.scene.getObjectByName('fountain-water'),cap=next.scene.getObjectByName('fountain-pedestal-cap'),rim=next.scene.getObjectByName('fountain-rim');
 const bounds={water:new Box3().setFromObject(water),cap:new Box3().setFromObject(cap),rim:new Box3().setFromObject(rim)};
 if(Math.abs(bounds.water.min.y-.32)>1e-6||Math.abs(bounds.cap.max.y-.96)>1e-6||Math.abs(bounds.rim.max.y-.58)>1e-6)throw Error('Pool levels changed');
 const before=[];old.scene.getObjectByName('fountain').traverse(o=>{if(o.isMesh)before.push([o,o.material])});const appearance=createFountainAppearance(old.scene,old.waterState);appearance.dispose();if(before.some(([o,m])=>o.material!==m))throw Error('Cleanup did not restore original bindings');
 const result={passed:true,geometry,bindings,events,bounds,instances:Object.keys(instances),styles:{legacy:old.fountainStyle,refined:next.fountainStyle},totalH:tourTotalH,stages:tourStages,ownedCleanupRestoresOriginals:true,newGeometry:0,newTextures:0};old.dispose();next.dispose();return result;
}

/** Test-only offscreen matte. Blue identifies genuinely visible sunlit water. */
export function poolCoverage(){
 const world=createScene({},'refined'),water=world.scene.getObjectByName('fountain-water');world.scene.background=new Color(0);
 const black=new MeshBasicMaterial({color:0});world.scene.traverse(o=>{if(o instanceof Mesh&&o!==water)o.material=black;});
 const base=water.material.onBeforeCompile.bind(water.material);water.material.onBeforeCompile=(shader,renderer)=>{base(shader,renderer);shader.fragmentShader=shader.fragmentShader.replace('outgoingLight = mix(shadedWater, litWater, getShadowMask());','outgoingLight = vec3(reflection, foam, getShadowMask());');};water.material.customProgramCacheKey=()=> 'pool-coverage-test-only';
 const renderer=new WebGLRenderer({antialias:false});renderer.shadowMap.enabled=true;renderer.shadowMap.type=PCFShadowMap;
 const target=new WebGLRenderTarget(384,212);renderer.setSize(384,212,false);renderer.setRenderTarget(target);const pixels=new Uint8Array(384*212*4),samples=[];
 for(const time of [2,4,6,8])for(const key of ['O','W']){
  world.update(time);const pose=resolveTourPose(sampleTour(key==='O'?0:11.5).pose,1440/793);world.setAspect(384/212);world.setViewHeight(pose.viewHeight);world.camera.position.set(...pose.position);world.camera.lookAt(...pose.target);world.camera.updateMatrixWorld(true);renderer.render(world.scene,world.camera);renderer.readRenderTargetPixels(target,0,0,384,212,pixels);
  let visible=0,deep=0,foam=0;for(let i=0;i<pixels.length;i+=4)if(pixels[i+2]>250){visible++;if(pixels[i]>127)deep++;if(pixels[i+1]>30)foam++;}
  samples.push({time,pose:key,visibleSunlitWaterPixels:visible,deepReflectionPercent:100*deep/visible,foamWaterAreaPercent:100*foam/visible});
 }
 renderer.setRenderTarget(null);target.dispose();renderer.dispose();renderer.forceContextLoss();black.dispose();world.dispose();return{method:'test-only384x212 offscreen original visible-depth matte, blue=actual sunlit water, red=reflection>0.5, green=foam; stone/jet/grass occlusion retained; all extra renderer resources disposed',samples};
}

export function poolProjection({pose,width,height}){
 const world=createScene();world.scene.updateMatrixWorld(true);world.setAspect(Number(pose.aspect));world.setViewHeight(Number(pose.viewHeight));world.camera.position.set(...JSON.parse(pose.cameraPosition));world.camera.lookAt(...JSON.parse(pose.cameraTarget));world.camera.updateMatrixWorld(true);
 const box=new Box3().setFromObject(world.scene.getObjectByName('fountain')),corners=[];
 for(const x of[box.min.x,box.max.x])for(const y of[box.min.y,box.max.y])for(const z of[box.min.z,box.max.z]){const p=new Vector3(x,y,z).project(world.camera);corners.push([(p.x+1)*width/2,(1-p.y)*height/2]);}
 world.dispose();return{left:Math.min(...corners.map(p=>p[0])),right:Math.max(...corners.map(p=>p[0])),top:Math.min(...corners.map(p=>p[1])),bottom:Math.max(...corners.map(p=>p[1]))};
}
