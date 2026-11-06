import { Box3, Color, Matrix4, Mesh, MeshBasicMaterial, PCFShadowMap, Ray, Triangle, Vector3, WebGLRenderer, WebGLRenderTarget } from 'three';
import { createScene } from '../../src/scene/createScene';
import { createDropParameters } from '../../src/scene/createFountainEffects';
import { createOrbFlight,sampleOrbFlight,sampleOrbDrop } from '../../src/animation/orbMotion';
import { orbConfig } from '../../src/config/orb';
import { waterConfig } from '../../src/config/water';
import { layoutConfig } from '../../src/config/layout';
import { resolveTourPose,tourPoses,tourTotalH,tourStages } from '../../src/tour/route';

const digest=async a=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',a.buffer))).map(x=>x.toString(16).padStart(2,'0')).join('');
export async function inspectOrb(aspects){
 const world=createScene({},'refined','lively'),legacy=createScene({},'refined');world.scene.updateMatrixWorld(true);legacy.scene.updateMatrixWorld(true);
 const protectedMeshes=[];
 for(const mesh of legacy.scene.getObjectByName('courtyard-blockout').getObjectsByProperty('isMesh',true)){
  const next=world.scene.getObjectByName(mesh.name);
  if(JSON.stringify([mesh.position,mesh.quaternion,mesh.scale])!==JSON.stringify([next.position,next.quaternion,next.scale]))throw Error('Protected transform '+mesh.name);
  for(const[n,a]of Object.entries(mesh.geometry.attributes))if(await digest(a.array)!==await digest(next.geometry.attributes[n].array))throw Error('Protected buffer '+mesh.name);
  if(mesh.material.customProgramCacheKey()!==next.material.customProgramCacheKey()||mesh.material.name!==next.material.name)throw Error('Pool appearance changed '+mesh.name);
  protectedMeshes.push(mesh.name);
 }
 const instances=[];for(const mesh of legacy.scene.getObjectsByProperty('isInstancedMesh',true))if(mesh.name!=='fountain-water-drops'){
  const next=world.scene.getObjectByName(mesh.name);if(await digest(mesh.instanceMatrix.array)!==await digest(next.instanceMatrix.array))throw Error('Vegetation changed');instances.push(mesh.name);
 }
 const root=world.scene.getObjectByName('fountain-effects'),ball=world.scene.getObjectByName('fountain-water-crown'),stem=world.scene.getObjectByName('fountain-water-column'),drops=world.scene.getObjectByName('fountain-water-drops');
 const capTop=.96,positions=ball.geometry.attributes.position;
 if(!ball.material.flatShading||ball.material.transparent||!ball.material.depthTest||!ball.material.depthWrite||ball.castShadow||stem.castShadow||drops.castShadow)throw Error('Wrong orb normal/depth/shadow flags');
 let minGap=Infinity,maxY=-Infinity,minY=Infinity,maxExtent=0,minStemOverlap=Infinity;
 const analyticMinGap=orbConfig.centerY-orbConfig.floatAmplitude-orbConfig.radius*orbConfig.shape.yRatio*(1+orbConfig.shape.y)*(1+orbConfig.shape.first+orbConfig.shape.second)-capTop;
 if(analyticMinGap<.08)throw Error('All-phase conservative gap fails');
 // All motion frequencies have two-decimal rational ratios: 600s is a full joint cycle.
 for(let i=0;i<=30000;i++){
  const t=i*.02;world.update(t);root.updateMatrixWorld(true);let bottom=Infinity;
  for(let v=0;v<positions.count;v++){
   const x=positions.getX(v),y=positions.getY(v),z=positions.getZ(v),length=Math.hypot(x,y,z);
   if(!Number.isFinite(length)||length>orbConfig.shape.envelope+1e-6)throw Error('Orb outside bound');maxExtent=Math.max(maxExtent,length);bottom=Math.min(bottom,y*orbConfig.radius+ball.position.y);
  }
  minGap=Math.min(minGap,bottom-capTop);minY=Math.min(minY,ball.position.y);maxY=Math.max(maxY,ball.position.y);
  const low=stem.position.y-stem.scale.y/2,high=stem.position.y+stem.scale.y/2;
  if(Math.abs(low-capTop)>1e-8||high<bottom+.02||high>bottom+.04)throw Error('Water thread disconnects');minStemOverlap=Math.min(minStemOverlap,high-bottom);
  if(drops.count>32||root.userData.activeRipples>8)throw Error('Unbounded effects');
  for(const impact of world.waterState.impacts.value)if(impact.w>0){
   if(impact.z<0||impact.z>=waterConfig.ripples.lifetime)throw Error('Bad impact age');
   const event=root.userData.impactEvents.find(e=>Math.abs(e.flight.impactX-impact.x)<1e-10&&Math.abs(e.flight.impactZ-impact.y)<1e-10&&Math.abs(e.age-impact.z)<1e-10);
   if(!event||Math.abs(t-event.flight.birthTime-event.flight.duration-impact.z)>1e-10)throw Error('Ripple without actual impact');
  }
 }
 if(minGap<.08)throw Error('Orb hits pedestal');
 let minWall=Infinity,minStone=Infinity,maxContactError=0,flightSamples=0,minBallGap=Infinity;
 const parameters=createDropParameters(),flight=createOrbFlight(),p=new Vector3(),query=new Vector3(),closest=new Vector3(),a=new Vector3(),b=new Vector3(),c=new Vector3(),hit=new Vector3(),ray=new Ray(new Vector3(),new Vector3());
 const stones=[new Box3(new Vector3(-.41,.86,-.41),new Vector3(.41,.96,.41)),new Box3(new Vector3(-.32,.24,-.32),new Vector3(.32,.86,.32))];
 for(let phase=0;phase<12;phase++)for(const drop of parameters){
  // 48s advances shape phase while preserving each half-second bob phase.
  const birth=phase*48.5+drop.phase;sampleOrbFlight(drop,birth,flight);
  maxContactError=Math.max(maxContactError,Math.abs(flight.y+flight.vy*flight.duration-.5*waterConfig.drops.gravity*flight.duration**2-drop.radius-layoutConfig.fountain.waterHeight));
  for(let j=0;j<=20;j++){
   const age=flight.duration*j/20;sampleOrbDrop(flight,age,p);
   for(let side=0;side<8;side++){const angle=(side+.5)*Math.PI/4;minWall=Math.min(minWall,layoutConfig.fountain.innerRadius*Math.cos(Math.PI/8)-p.x*Math.cos(angle)+p.z*Math.sin(angle)-drop.radius);}
   for(const stone of stones)minStone=Math.min(minStone,stone.distanceToPoint(p)-drop.radius);flightSamples++;
  }
  for(const age of [.002,.02,.07,.15,.45,.8,flight.duration-.001]){
   world.update(birth+age);sampleOrbDrop(flight,age,p);query.copy(p).sub(ball.position).divideScalar(orbConfig.radius);ray.direction.copy(query).normalize();
   const index=ball.geometry.index;let nearest=Infinity,surfaceRadius=Infinity;
   for(let k=0;k<index.count;k+=3){
    a.fromBufferAttribute(positions,index.getX(k));b.fromBufferAttribute(positions,index.getX(k+1));c.fromBufferAttribute(positions,index.getX(k+2));
    Triangle.prototype.closestPointToPoint.call(new Triangle(a,b,c),query,closest);nearest=Math.min(nearest,query.distanceTo(closest));
    if(ray.intersectTriangle(a,b,c,false,hit))surfaceRadius=Math.min(surfaceRadius,hit.length());
   }
   if(query.length()<surfaceRadius-1e-6)throw Error('Drop center inside orb');
   const gap=nearest*orbConfig.radius-drop.radius;minBallGap=Math.min(minBallGap,gap);if(gap<-.00001)throw Error('Drop intersects orb '+gap);
  }
 }
 if(minWall<.05||minStone<0||maxContactError>1e-8)throw Error('Unsafe analytic drops');
 const jumps=[];
 const snapshot=w=>{const r=w.scene.getObjectByName('fountain-effects'),o=w.scene.getObjectByName('fountain-water-crown'),d=w.scene.getObjectByName('fountain-water-drops');return JSON.stringify({positions:Array.from(o.geometry.attributes.position.array),y:o.position.y,stem:r.userData.stemTop,drops:Array.from(d.instanceMatrix.array),count:d.count,impacts:w.waterState.impacts.value});};
 for(const time of [0,.0625-1e-7,.0625+1e-7,2-1e-7,2+1e-7,4,6,8,120,86400,2]){
  world.update(time);const fresh=createScene({},'refined','lively');fresh.update(time);if(snapshot(world)!==snapshot(fresh))throw Error('Jump depends on history '+time);fresh.dispose();jumps.push(time);
 }
 const frames=[],baselineFrames=[];
 for(const viewport of aspects)for(const key of ['O','W']){
  const pose=resolveTourPose(tourPoses[key],viewport.aspect);world.setAspect(viewport.aspect);world.setViewHeight(pose.viewHeight);world.camera.position.set(...pose.position);world.camera.lookAt(...pose.target);world.camera.updateMatrixWorld(true);let minimum=Infinity;
  for(let i=0;i<=3000;i++){
   world.update(i*.2);root.updateMatrixWorld(true);let left=Infinity,right=-Infinity;
   for(let v=0;v<positions.count;v++){p.fromBufferAttribute(positions,v).applyMatrix4(ball.matrixWorld).project(world.camera);if(Math.abs(p.x)>1||Math.abs(p.y)>1)throw Error('Orb cropped');left=Math.min(left,p.x);right=Math.max(right,p.x);}
   minimum=Math.min(minimum,(right-left)*viewport.sampleWidth/2);
  }
  if(minimum<(key==='O'?8:12))throw Error('Orb too small '+minimum);frames.push({viewport:viewport.viewport,pose:key,minSamplePixelDiameter:minimum});
  legacy.setAspect(viewport.aspect);legacy.setViewHeight(pose.viewHeight);legacy.camera.position.set(...pose.position);legacy.camera.lookAt(...pose.target);legacy.camera.updateMatrixWorld(true);
  const oldBall=legacy.scene.getObjectByName('fountain-water-crown'),oldPoints=oldBall.geometry.attributes.position;let oldMinimum=Infinity;
  for(let i=0;i<=3000;i++){
   legacy.update(i*.2);legacy.scene.updateMatrixWorld(true);let left=Infinity,right=-Infinity;
   for(let v=0;v<oldPoints.count;v++){p.fromBufferAttribute(oldPoints,v).applyMatrix4(oldBall.matrixWorld).project(legacy.camera);left=Math.min(left,p.x);right=Math.max(right,p.x);}
   oldMinimum=Math.min(oldMinimum,(right-left)*viewport.sampleWidth/2);
  }
  baselineFrames.push({viewport:viewport.viewport,pose:key,minSamplePixelDiameter:oldMinimum,source:'unchanged legacy effects; Step8 equivalence checked by paired pixels'});
 }
 const result={passed:true,protectedMeshes,protectedVegetation:instances,geometrySamples:30001,sampledRangeSeconds:[0,600],analyticMinPedestalGap:analyticMinGap,minPedestalGap:minGap,minCenterY:minY,maxCenterY:maxY,maxUnitExtent:maxExtent,minStemOverlap,flightSamples,birthCases:384,birthSampling:'12 half-second bob phases stratified by 48s offsets across the 600s joint shape cycle',minWallClearance:minWall,minStoneClearance:minStone,minOrbDropClearance:minBallGap,maxContactEquationError:maxContactError,jumpTimes:jumps,frames,baselineFrames,dropCapacity:32,rippleCapacity:8,route:{totalH:tourTotalH,stages:tourStages},normalMethod:'actual flat-face derivatives follow deformed geometry',ownedGeometryCount:3,addedGeometryCount:0};
 const owned=[stem.geometry,ball.geometry,drops.geometry,stem.material,ball.material,drops];
 const disposal=owned.map(o=>{const receipt={type:o.type,events:0};o.addEventListener('dispose',()=>receipt.events++);return receipt;});
 world.dispose();world.dispose();if(disposal.some(r=>r.events!==1))throw Error('Owned GPU resource not disposed exactly once');
 result.disposal=disposal;legacy.dispose();return result;
}

/** Bounds of only the ball, stem, actual visible drops and real impact rings. */
export function orbEffectProjection({pose,width,height}){
 const boxes=[],triangles=[];
 for(const style of ['legacy','lively']){
  const world=createScene({},'refined',style);world.update(Number(pose.sceneTime));world.scene.updateMatrixWorld(true);
  world.setAspect(Number(pose.aspect));world.setViewHeight(Number(pose.viewHeight));world.camera.position.set(...JSON.parse(pose.cameraPosition));world.camera.lookAt(...JSON.parse(pose.cameraTarget));world.camera.updateMatrixWorld(true);
  const root=world.scene.getObjectByName('fountain-effects'),point=new Vector3();
  const projectBox=(box,matrix,label)=>{
   const corners=[];
   for(const x of[box.min.x,box.max.x])for(const y of[box.min.y,box.max.y])for(const z of[box.min.z,box.max.z]){
    point.set(x,y,z);if(matrix)point.applyMatrix4(matrix);point.project(world.camera);corners.push([(point.x+1)*width/2,(1-point.y)*height/2]);
   }
   boxes.push({style,label,left:Math.min(...corners.map(p=>p[0])),right:Math.max(...corners.map(p=>p[0])),top:Math.min(...corners.map(p=>p[1])),bottom:Math.max(...corners.map(p=>p[1]))});
  };
  for(const name of ['fountain-water-column','fountain-water-crown'])projectBox(new Box3().setFromObject(world.scene.getObjectByName(name)),null,name);
  const drops=world.scene.getObjectByName('fountain-water-drops'),matrix=new Matrix4();drops.geometry.computeBoundingBox();
  for(let i=0;i<drops.count;i++){drops.getMatrixAt(i,matrix);matrix.premultiply(drops.matrixWorld);projectBox(drops.geometry.boundingBox,matrix,'visible-drop-'+i);}
  for(const event of world.waterState.impacts.value)if(event.w>0){
   const r=.025+event.z*waterConfig.ripples.speed+.065;
   projectBox(new Box3(new Vector3(event.x-r,layoutConfig.fountain.waterHeight,event.y-r),new Vector3(event.x+r,layoutConfig.fountain.waterHeight,event.y+r)),root.matrixWorld,'actual-impact-ring');
  }
  if(style==='lively'){
   const ball=world.scene.getObjectByName('fountain-water-crown'),attr=ball.geometry.attributes.position,index=ball.geometry.index;
   for(let i=0;i<index.count;i+=3){const vertices=[];for(let j=0;j<3;j++){point.fromBufferAttribute(attr,index.getX(i+j)).applyMatrix4(ball.matrixWorld).project(world.camera);vertices.push([(point.x+1)*width/2,(1-point.y)*height/2]);}triangles.push(vertices);}
  }
  world.dispose();
 }
 return{boxes,ballTriangles:triangles};
}

/** Diagnostic render only: use the actual shader's white-mix factor and visible depth. */
export function orbHighlightCoverage(){
 const world=createScene({},'refined','lively'),ball=world.scene.getObjectByName('fountain-water-crown'),originals=[];
 world.scene.background=new Color(0);const black=new MeshBasicMaterial({color:0});
 world.scene.traverse(o=>{if(o instanceof Mesh&&o!==ball){originals.push([o,o.material]);o.material=black;}});
 const compile=ball.material.onBeforeCompile.bind(ball.material);
 ball.material.onBeforeCompile=(shader,renderer)=>{
  compile(shader,renderer);shader.fragmentShader=shader.fragmentShader.replace('outgoingLight = mix(uOrbShade, orbColor, getShadowMask());','outgoingLight = vec3(step(.5, max(crown * .82, rim * .75)), 1.0, getShadowMask());');
 };
 ball.material.customProgramCacheKey=()=> 'test-only-orb-highlight-coverage';
 const renderer=new WebGLRenderer({antialias:false});renderer.shadowMap.enabled=true;renderer.shadowMap.type=PCFShadowMap;renderer.setSize(1024,564,false);
 const target=new WebGLRenderTarget(1024,564),pixels=new Uint8Array(1024*564*4),samples=[];renderer.setRenderTarget(target);
 for(const time of [2,4,6,8])for(const key of ['O','W']){
  world.update(time);const pose=resolveTourPose(tourPoses[key],1440/793);world.setAspect(1440/793);world.setViewHeight(pose.viewHeight);world.camera.position.set(...pose.position);world.camera.lookAt(...pose.target);world.camera.updateMatrixWorld(true);renderer.render(world.scene,world.camera);renderer.readRenderTargetPixels(target,0,0,1024,564,pixels);
  let area=0,white=0;for(let i=0;i<pixels.length;i+=4)if(pixels[i+1]>250){area++;if(pixels[i]>250)white++;}samples.push({time,pose:key,visibleOrbPixels:area,whiteDominantPixels:white,whiteDominantPercent:100*white/area});
 }
 renderer.setRenderTarget(null);target.dispose();renderer.dispose();renderer.forceContextLoss();for(const[o,m]of originals)o.material=m;black.dispose();world.dispose();
 return{method:'test-only original shader white contribution >=0.5; green=visible orb surface with original depth, red=white-dominant highlight; 1024x564; diagnostic renderer/target disposed; no production render pass',samples};
}
