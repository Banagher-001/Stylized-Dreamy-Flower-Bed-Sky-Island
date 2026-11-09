// Actual geometry/instance matrices, deterministic paths, clearance and original
// scene state. CPU/source checks are separate from GPU/browser/video evidence.
import {createServer} from 'vite';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {resolve} from 'node:path';
import {Box3,Matrix4,Mesh,OrthographicCamera,Quaternion,Vector3,ShaderLib,UniformsUtils} from 'three';
const root=fileURLToPath(new URL('../../',import.meta.url)),out=resolve(root,'docs/evidence/garden-enhancement-step-6');
const build=JSON.parse(readFileSync(resolve(out,'build-verification.json'),'utf8'));
const hash=b=>createHash('sha256').update(b).digest('hex'),assert=(v,n)=>{if(!v)throw Error(n)};
const cases=[],record=(name,evidence)=>{cases.push({name,passed:true,evidence});process.stdout.write('model '+name+'\n')};
const server=await createServer({root,configFile:false,server:{middlewareMode:true,hmr:false,ws:false,watch:null}});
try{
 const {birdConfig:c}=await server.ssrLoadModule('/src/config/birds.ts');
 const {createBirdPose,sampleBirdPose}=await server.ssrLoadModule('/src/animation/birdMotion.ts');
 const {createBirds,birdScreenAlpha}=await server.ssrLoadModule('/src/scene/createBirds.ts');
 const {createBirdGeometry}=await server.ssrLoadModule('/src/geometry/createBirdGeometry.ts');
 const {createScene}=await server.ssrLoadModule('/src/scene/createScene.ts');
 const {createPillarAppearance}=await server.ssrLoadModule('/src/tour/createPillarAppearance.ts');
 let minSpeed=Infinity,maxSpeed=0,maxBank=0,minHeight=Infinity,maxHeight=0,maxPositionStep=0,maxWingStep=0,maxRotationStep=0;
 const boundary=[],poses=c.routes.map(()=>createBirdPose());
 for(let index=0;index<3;index++){
  const a=createBirdPose(),b=createBirdPose();let flapCount=0,glideCount=0;
  for(let k=0;k<=12000;k++){
   const t=k*.01;sampleBirdPose(t,index,a);sampleBirdPose(t+.0001,index,b);
   minSpeed=Math.min(minSpeed,a.speed);maxSpeed=Math.max(maxSpeed,a.speed);maxBank=Math.max(maxBank,Math.abs(a.bank));minHeight=Math.min(minHeight,a.position.y);maxHeight=Math.max(maxHeight,a.position.y);
   maxPositionStep=Math.max(maxPositionStep,a.position.distanceTo(b.position));maxWingStep=Math.max(maxWingStep,Math.abs(a.leftWing-b.leftWing));maxRotationStep=Math.max(maxRotationStep,1-Math.abs(a.rotation.dot(b.rotation)));
   flapCount+=a.flap>.8;glideCount+=a.flap<.001;
   assert(Number.isFinite(a.position.lengthSq())&&a.scale>=.22&&a.scale<=.34,'Invalid pose');
  }
  for(const t of [c.routes[index].period*(1-c.routes[index].phase),c.routes[index].flapCycle-index*1.37]){
   sampleBirdPose(t-.000001,index,a);sampleBirdPose(t+.000001,index,b);
   assert(a.position.distanceTo(b.position)<.00001&&Math.abs(a.leftWing-b.leftWing)<.0001&&1-Math.abs(a.rotation.dot(b.rotation))<1e-8,'Cycle discontinuity');
   boundary.push({bird:index,time:t,positionDifference:a.position.distanceTo(b.position),wingDifference:Math.abs(a.leftWing-b.leftWing)});
  }
  assert(flapCount>100&&glideCount>1000,'No real flap/glide alternation');
 }
 assert(maxPositionStep<.001&&maxWingStep<.001&&maxRotationStep<.00001,'Motion jump');
 record('absolute-time routes, wings, glide, heading and all cycle joins continuous',{sampledSeconds:120,stepSeconds:.01,minSpeed,maxSpeed,minHeight,maxHeight,maxBankDegrees:maxBank*180/Math.PI,maxPositionStepAtPoint0001:maxPositionStep,maxWingStep,maxRotationStep,boundary});
 const before=createScene({},'refined','lively',true,false),after=createScene({},'refined','lively',true,true);const appearances=[];
 for(const w of [before,after]){for(const column of ['columnUpperLeft','columnRight','columnLower'])appearances.push(createPillarAppearance(w.scene,column));w.cloudShadows.bind(w.scene)}
 const snapshot=w=>{w.scene.updateMatrixWorld(true);const mesh=[];w.scene.traverse(o=>{if(o instanceof Mesh&&!o.name.startsWith('courtyard-birds'))mesh.push({name:o.name,matrix:o.matrixWorld.elements,
  attributes:Object.fromEntries(Object.entries(o.geometry.attributes).map(([k,a])=>[k,hash(Buffer.from(a.array.buffer,a.array.byteOffset,a.array.byteLength))])),index:o.geometry.index?hash(Buffer.from(o.geometry.index.array.buffer)):null,
  instances:o.instanceMatrix?hash(Buffer.from(o.instanceMatrix.array.buffer)):null,count:o.count??null})});return{mesh,impacts:w.waterState.impacts.value.map(v=>v.toArray()),cloud:w.cloudShadows.metadata,time:w.environmentState.time.value}};
 for(const t of [2,18,60,300]){before.update(t);after.update(t);assert(JSON.stringify(snapshot(before))===JSON.stringify(snapshot(after)),'Original scene changed')}
 record('all prior world geometry, grass distribution, matrices, water events, cloud bindings and time unchanged',{times:[2,18,60,300],cloudReceivers:after.cloudShadows.metadata.materials.length});
 const flock=createBirds(),camera=new OrthographicCamera(-20,20,20,-20,.1,100);camera.position.set(0,20,20);camera.lookAt(0,0,0);camera.updateMatrixWorld(true);
 const view={bounds:{left:0,top:0,right:2000,bottom:2000},avoid:[],margin:0,key:'wide-diagnostic'};
 const matrix=new Matrix4(),point=new Vector3(),referencePoint=new Vector3(),hingeMatrix=new Matrix4(),rotation=new Quaternion(),axis=new Vector3(0,0,1),unit=new Vector3(1,1,1),shoulder=new Vector3();
 const referenceParts=['body','left','right'].map(createBirdGeometry);
 const boxes=[new Box3(),new Box3(),new Box3()],staticBoxes=[];
 before.scene.updateMatrixWorld(true);before.scene.traverse(o=>{if(o instanceof Mesh){o.geometry.computeBoundingBox();staticBoxes.push(o.geometry.boundingBox.clone().applyMatrix4(o.matrixWorld))}});
 const distance=(a,b)=>Math.hypot(Math.max(a.min.x-b.max.x,b.min.x-a.max.x,0),Math.max(a.min.y-b.max.y,b.min.y-a.max.y,0),Math.max(a.min.z-b.max.z,b.min.z-a.max.z,0));
 let staticGap=Infinity,birdGap=Infinity,maxMergedHingeError=0;
 for(let k=0;k<=6000;k++){
  flock.update(k*.1);flock.present(camera,view);assert(flock.snapshot().visible===3,'Wide model camera unexpectedly clipped a bird');for(const b of boxes)b.makeEmpty();
  for(const piece of flock.root.children){const p=piece.geometry.getAttribute('position'),part=piece.geometry.getAttribute('birdPart'),wing=piece.geometry.getAttribute('birdWing');for(let id=0;id<3;id++){
   piece.getMatrixAt(id,matrix);
   for(let v=0;v<p.count;v++){
    point.fromBufferAttribute(p,v);const side=part.getX(v),angle=-side*wing.getX(id);
    if(side){const x=point.x,y=point.y;point.set(Math.cos(angle)*x-Math.sin(angle)*y+side*.075,Math.sin(angle)*x+Math.cos(angle)*y,point.z+.015)}
    point.applyMatrix4(matrix);boxes[id].expandByPoint(point);
   }
   let offset=0;
   for(let j=0;j<3;j++){
    const source=referenceParts[j].getAttribute('position'),side=j===0?0:j===1?-1:1;
    hingeMatrix.compose(shoulder.set(side*.075,0,side?.015:0),rotation.setFromAxisAngle(axis,-side*wing.getX(id)),unit);hingeMatrix.premultiply(matrix);
    for(let v=0;v<source.count;v++){
     referencePoint.fromBufferAttribute(source,v).applyMatrix4(hingeMatrix);point.fromBufferAttribute(p,offset+v);
     if(side){const x=point.x,y=point.y,a=-side*wing.getX(id);point.set(Math.cos(a)*x-Math.sin(a)*y+side*.075,Math.sin(a)*x+Math.cos(a)*y,point.z+.015)}
     point.applyMatrix4(matrix);maxMergedHingeError=Math.max(maxMergedHingeError,point.distanceTo(referencePoint));
    }
    offset+=source.count;
   }
  }}
  for(let i=0;i<3;i++){for(const b of staticBoxes)staticGap=Math.min(staticGap,distance(boxes[i],b));for(let j=i+1;j<3;j++)birdGap=Math.min(birdGap,distance(boxes[i],boxes[j]));}
 }
 assert(staticGap>=c.clearance&&birdGap>=c.clearance&&maxMergedHingeError<.000001,JSON.stringify({staticGap,birdGap,maxMergedHingeError}));
 record('actual transformed body and wings clear every original mesh and each other',{sampledSeconds:600,stepSeconds:.1,staticGap,birdGap,requiredGap:c.clearance,maxMergedHingeError,method:'actual instance matrices, per-vertex part/wing attributes and full posed vertices; conservative3D envelopes; packed hinge positions independently compared to separate reference body/wing Matrix4 transforms; GPU projection/depth/footage separately verified'});
 const state=flock.snapshot(),versions=flock.root.children.map(m=>m.instanceMatrix.version);flock.update(600);flock.present(camera,view);
 assert(JSON.stringify(flock.snapshot())===JSON.stringify(state)&&versions.every((v,i)=>v===flock.root.children[i].instanceMatrix.version),'Paused update/upload drift');
 const shape=flock.root.children[0];const shader={vertexShader:ShaderLib.lambert.vertexShader,fragmentShader:ShaderLib.lambert.fragmentShader,uniforms:UniformsUtils.clone(ShaderLib.lambert.uniforms)};shape.material.onBeforeCompile(shader,undefined);
 assert(shader.vertexShader.includes('birdAlpha')&&shader.fragmentShader.includes('diffuseColor.a *= vBirdAlpha')&&!shape.material.userData.artSurface,'Invalid bird material path');
 assert(shape.material.depthTest&&!shape.material.depthWrite&&shape.material.side===0&&flock.root.children.length===1&&flock.metadata.trianglesPerBird<=64,'Resource/depth budget');
 assert(shader.vertexShader.includes('mat2(c, s, -s, c) * transformed.xy')&&shader.vertexShader.includes('-birdPart * birdWing'),'Invalid GPU hinge');
 for(const piece of flock.root.children){assert(piece.material===shape.material&&!piece.castShadow,'Extra shared material/shadow');}
 const safe={bounds:{left:0,top:0,right:1000,bottom:800},avoid:[{left:400,right:600,top:200,bottom:500}],margin:20,key:'safe'};
 for(let x=0;x<=1000;x+=2)for(let y=0;y<=800;y+=2){const alpha=birdScreenAlpha(x,y,15,safe);assert(alpha>=0&&alpha<=1,'Invalid alpha');if(x>=365&&x<=635&&y>=165&&y<=535)assert(alpha===0,'Safety envelope overlaps UI')}
 record('paused pose/uploads, shared material and full-envelope UI safety',{samePausedMatrixVersions:true,geometries:1,materials:1,colorDrawCalls:1,trianglesPerBird:flock.metadata.trianglesPerBird,castShadow:false,depthTest:true,UIEnvelopeRadius:15,margin:20});
 const expected=JSON.stringify(flock.snapshot());flock.dispose();flock.dispose();flock.update(999);flock.present(camera,view);assert(flock.root.children.length===0&&JSON.stringify(flock.snapshot())===expected,'Dispose revived flock');
 for(const g of referenceParts)g.dispose();for(const a of appearances)a.dispose();before.dispose();after.dispose();
 const disabled=createScene({enabled:false},'refined','lively',true,true);assert(!disabled.birds,'Global environment-off did not disable birds');disabled.dispose();
 record('idempotent release and global environment gate',{noIndependentTimerOrRAF:true,disposedRootEmpty:true,environmentOffCreatesNoBirdResources:true});
 writeFileSync(resolve(out,'motion-geometry-and-safety.json'),JSON.stringify({passed:true,candidateId:build.candidateId,method:'actual source and geometry through SSR; dense absolute-time sampling and actual instance matrices; no GPU or real-time browser claim',cases,sourceSha256:Object.fromEntries(build.changedRuntimeSources.map(n=>[n,hash(readFileSync(resolve(root,n)))]))},null,2)+'\n');
 process.stdout.write(`PASS ${cases.length} bird motion/geometry/protection groups\n`);
}finally{await server.close()}
