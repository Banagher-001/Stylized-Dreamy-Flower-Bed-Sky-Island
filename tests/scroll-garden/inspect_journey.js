import { Box3, Raycaster, Vector3 } from 'three';
import { createScene } from '../../src/scene/createScene';
import { sampleTour, resolveTourPose, tourPoses, tourStages, tourTotalH, waterHold } from '../../src/tour/route';
import { sampleTourPresentation } from '../../src/tour/presentation';
import { readingStations } from '../../src/tour/reading';
import { filmStations } from '../../src/tour/filmReading';
import { experimentStations, sampleExperimentPresentation } from '../../src/tour/experimentReading';
import { sampleMagic } from '../../src/tour/magicStyle';
import { sampleFilmPresentation } from '../../src/tour/filmReading';

const values = p => [...p.position, ...p.target, p.viewHeight];
const difference = (a,b) => Math.max(...a.map((v,i)=>Math.abs(v-b[i])));
export function inspectJourney(aspects,baselineViews){
 const world=createScene({},'refined','lively');world.update(2);world.scene.updateMatrixWorld(true);
 const solids=world.scene.getObjectsByProperty('isMesh',true).filter(o=>o.castShadow),colliders=solids.map(mesh=>({name:mesh.name,box:new Box3().setFromObject(mesh)}));
 const point=new Vector3(),target=new Vector3(),ray=new Raycaster();let minimumClearance=Infinity,minimumEyeY=Infinity;
 const paths=[['T01',.5,1.3],['T12',3.7,4.4],['T23',8,8.7],['T3W',11.1,waterHold.start],['WIDE',waterHold.end,11.8]],routes=[];
 for(const aspect of aspects)for(const[key,start,end]of paths){
  for(let i=0;i<=1000;i++){
   const pose=resolveTourPose(sampleTour(start+(end-start)*i/1000).pose,aspect);
   if(values(pose).some(v=>!Number.isFinite(v))||pose.viewHeight<=0)throw Error('Invalid pose');point.set(...pose.position);target.set(...pose.target);
   if(point.distanceTo(target)<.5)throw Error('Camera direction degenerates');minimumEyeY=Math.min(minimumEyeY,point.y);
   for(const collider of colliders)minimumClearance=Math.min(minimumClearance,collider.box.distanceToPoint(point));
  }
  routes.push({aspect,path:key,range:[start,end],samples:1001});
 }
 if(minimumClearance<.12||minimumEyeY<.25)throw Error('Camera unsafe');
 const heights=[...new Set([...tourStages.flatMap(s=>[s.start,s.end]),1.94,2.22,2.74,3.02,5.2,5.55,6.2,6.52,7.04,7.32,9.34,9.65,10.3,10.59,waterHold.start,waterHold.stop,waterHold.end])].filter(h=>h>0&&h<tourTotalH),boundaries=[];
 let maximumJump=0,maximumDerivativeDifference=0;
 for(const aspect of aspects)for(const h of heights){
  const at=q=>values(resolveTourPose(sampleTour(q).pose,aspect)),center=at(h),a=at(h-1e-6),b=at(h+1e-6),left=at(h-1e-5),right=at(h+1e-5);
  const jump=difference(a,b),derivative=difference(center.map((v,i)=>(v-left[i])/1e-5),right.map((v,i)=>(v-center[i])/1e-5));maximumJump=Math.max(maximumJump,jump);maximumDerivativeDifference=Math.max(maximumDerivativeDifference,derivative);
  if(jump>1e-4||derivative>1e-3)throw Error('Boundary continuity '+h+' '+jump+' '+derivative);boundaries.push({aspect,h,jump,derivativeDifference:derivative});
 }
 for(let i=0;i<=100;i++)if(JSON.stringify(sampleTour(waterHold.start+(waterHold.end-waterHold.start)*i/100).pose)!==JSON.stringify(tourPoses.W))throw Error('Water hold moves');
 const views=[];
 for(const aspect of aspects)for(const stations of[readingStations,filmStations,experimentStations])for(const station of stations){
  const frame=sampleTour(station.stop),pose=resolveTourPose(frame.pose,aspect);world.camera.position.set(...pose.position);world.camera.lookAt(...pose.target);world.setAspect(aspect);world.setViewHeight(pose.viewHeight);world.camera.updateMatrixWorld(true);
  point.set(...pose.position);target.set(...frame.pose.target);ray.set(point,target.clone().sub(point).normalize());const first=ray.intersectObjects(solids,false)[0];
  const column=station.id[0]==='A'?'columnUpperLeft':station.id[0]==='B'?'columnRight':'columnLower';
  if(!first?.object.name.startsWith(column+'-block-'))throw Error('Reading view blocked '+station.id);
  const ink=frame.reading?sampleMagic(frame.reading):frame.filmReading?sampleFilmPresentation(frame.filmReading):sampleExperimentPresentation(frame.experimentReading);
  if(ink.body!==1)throw Error('Navigation misses full read');views.push({aspect,station:station.id,firstHit:first.object.name,body:ink.body});
 }
 const fixed=new Set(['O','A1','A2','A3','B1','B2','B3','B4','C1','C2','C3','W','S99']),protectedViews=[];
 for(const old of baselineViews.filter(v=>fixed.has(v.key))){
  const stats=JSON.parse(old.scene.rendererStats),aspect=stats.outputWidth/stats.outputHeight;
  const pose=resolveTourPose(sampleTour(Number(old.scene.displayH)).pose,aspect),expected=[...JSON.parse(old.scene.cameraPosition),...JSON.parse(old.scene.cameraTarget),Number(old.scene.viewHeight)];
  if(difference(values(pose).slice(0,7),expected)>1e-6)throw Error('Fixed posture changed '+JSON.stringify({key:old.key,viewport:old.viewport,mode:old.mode,aspect:old.scene.aspect,actual:values(pose),expected}));protectedViews.push({viewport:old.viewport,mode:old.mode,key:old.key,unchanged:true});
 }
 const presentation=[];
 for(const h of [0,.35,.49,.5,.9,1.3,1.74,3.34,3.7,4.05,4.95,7.64,8,8.35,9.14,10.05,10.83,11.1,11.3,11.45,11.5,11.55,11.67,11.8,11.95,12.3]){
  const sample=sampleTour(h),a=sampleTourPresentation(sample),b=sampleTourPresentation(sampleTour(h));if(JSON.stringify(a)!==JSON.stringify(b))throw Error('Presentation history');presentation.push({h,chapter:sample.chapter,...a});
 }
 world.dispose();return{passed:true,totalH:tourTotalH,stageCount:tourStages.length,routes,geometricSamples:routes.length*1001,minimumClearance,minimumEyeY,maximumJump,maximumDerivativeDifference,boundaries,waterHold:{...waterHold,samples:101,exact:true},views,protectedViews,presentation,protectedScene:'all scene/source buffers remain controlled by the baseline file guard; fixed O/W/ten reading poses match actual frozen Step9 data'};
}
