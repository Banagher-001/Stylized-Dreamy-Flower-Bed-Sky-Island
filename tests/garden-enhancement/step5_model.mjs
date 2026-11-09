// Controller-independent real scene/material inspection; no browser-time claims.
import { createServer } from 'vite';
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
import { Mesh, MeshBasicMaterial, Scene, ShaderLib, UniformsUtils } from 'three';

const root=fileURLToPath(new URL('../../',import.meta.url)),out=resolve(root,'docs/evidence/garden-enhancement-step-5');
const build=JSON.parse(readFileSync(resolve(out,'build-verification.json'),'utf8'));
const sha=b=>createHash('sha256').update(b).digest('hex');
const assert=(v,label)=>{if(!v)throw Error(label)};
const server=await createServer({root,configFile:false,server:{middlewareMode:true,hmr:false,ws:false,watch:null}});
const cases=[];const record=(name,evidence)=>{cases.push({name,passed:true,evidence});process.stdout.write('model '+name+'\n')};
try {
  const m=await server.ssrLoadModule('/src/animation/cloudShadows.ts');
  const {cloudShadowConfig:c}=await server.ssrLoadModule('/src/config/cloudShadows.ts');
  const {createScene}=await server.ssrLoadModule('/src/scene/createScene.ts');
  const {createPillarAppearance}=await server.ssrLoadModule('/src/tour/createPillarAppearance.ts');
  const {createCloudShadowBinding}=await server.ssrLoadModule('/src/materials/applyCloudShadows.ts');
  const sample=m.sampleCloudCoverage;let maximum=0,minimum=1,translationError=0,heightError=0,periodError=0,seamError=0;
  const coverage=[];
  for(const time of [0,2,10,18,40,64,96,132,145.4545454545,86400]){
    let covered=0,total=0;
    for(let x=-7;x<=7;x+=.25)for(let z=-5;z<=6;z+=.25){
      const v=sample(x,0,z,time);maximum=Math.max(maximum,v);minimum=Math.min(minimum,v);covered+=v>.25?1:0;total++;
      assert(v>=0&&v<=1,'Unbounded field');
      heightError=Math.max(heightError,Math.abs(sample(x,3.1,z,time)-sample(x-3.1*m.cloudProjection[0],0,z-3.1*m.cloudProjection[1],time)));
      periodError=Math.max(periodError,Math.abs(v-sample(x,0,z,time+m.cloudRepeatSeconds)));
      translationError=Math.max(translationError,Math.abs(v-sample(x+m.cloudDirection[0]*c.speed*7.3,0,z+m.cloudDirection[1]*c.speed*7.3,time+7.3)));
      seamError=Math.max(seamError,Math.abs(sample(x,0,z,m.cloudRepeatSeconds-.0001)-sample(x,0,z,m.cloudRepeatSeconds+.0001)));
    }
    coverage.push({time,worldGroundGrid:[-7,7,-5,6],threshold:.25,coveredFraction:covered/total});
  }
  assert(heightError<1e-12&&periodError<1e-10&&translationError<1e-10&&seamError<.0001,'Projection/translation/period discontinuity');
  record('bounded field, height-correct sunlight projection, wind translation and wrap continuity',{minimum,maximum,heightError,periodError,translationError,seamError,coverage,groundCrossingSeconds:13/c.speed,repeatSeconds:m.cloudRepeatSeconds});
  const before=createScene({},'refined','lively',false),after=createScene({},'refined','lively',true);
  const appearances=[];
  for(const w of [before,after])for(const column of ['columnUpperLeft','columnRight','columnLower'])appearances.push(createPillarAppearance(w.scene,column));
  before.cloudShadows.bind(before.scene);after.cloudShadows.bind(after.scene);
  const snapshot=w=>{
    w.scene.updateMatrixWorld(true);const meshes=[];
    w.scene.traverse(o=>{if(o instanceof Mesh){const geometry=o.geometry;meshes.push({name:o.name,matrix:o.matrixWorld.elements,
      geometry:Object.fromEntries(Object.entries(geometry.attributes).map(([k,a])=>[k,sha(Buffer.from(a.array.buffer,a.array.byteOffset,a.array.byteLength))])),
      index:geometry.index?sha(Buffer.from(geometry.index.array.buffer,geometry.index.array.byteOffset,geometry.index.array.byteLength)):null,
      count:o.count??null,instances:o.instanceMatrix?sha(Buffer.from(o.instanceMatrix.array.buffer)):null});}});
    return {meshes,impacts:w.waterState.impacts.value.map(v=>v.toArray()),environmentTime:w.environmentState.time.value};
  };
  const times=[];
  for(const time of [2,18,60,300]){before.update(time);after.update(time);assert(JSON.stringify(snapshot(before))===JSON.stringify(snapshot(after)),'Clouds changed physical scene');times.push(time);}
  record('all mesh geometry, instancing, world transforms, water events and time unchanged',{times,meshCount:snapshot(after).meshes.length});
  const count=after.cloudShadows.metadata.materials.length;
  for(let i=0;i<20;i++)after.cloudShadows.bind(after.scene);
  assert(after.cloudShadows.metadata.materials.length===count,'Repeated bind growth');
  assert(!before.cloudShadows.metadata.enabled&&before.cloudShadows.metadata.materials.length===0,'Disabled path mutated');
  const materials=new Set();after.scene.traverse(o=>{if(o instanceof Mesh)for(const a of Array.isArray(o.material)?o.material:[o.material])materials.add(a)});
  let sharedDrift,sharedActive;const shaders=[];mkdirSync(resolve(out,'material-shaders'),{recursive:true});
  for(const material of materials){
    if(!material.userData.artSurface)continue;
    const shader={vertexShader:ShaderLib.lambert.vertexShader,fragmentShader:ShaderLib.lambert.fragmentShader,uniforms:UniformsUtils.clone(ShaderLib.lambert.uniforms)};
    material.onBeforeCompile(shader,undefined);
    assert(shader.fragmentShader.includes('CLOUD_SHADOW_FINISH')&&material.userData.cloudShadow,'Receiver missing');
    if(!sharedDrift){sharedDrift=shader.uniforms.uCloudDrift;sharedActive=shader.uniforms.uCloudActive;}
    assert(sharedDrift===shader.uniforms.uCloudDrift&&sharedActive===shader.uniforms.uCloudActive,'Separate material cloud states');
    const marker=shader.fragmentShader.indexOf('CLOUD_SHADOW_FINISH');
    for(const finish of ['float wetLine =','float movingHighlight =','float white ='])if(shader.fragmentShader.includes(finish))assert(shader.fragmentShader.indexOf(finish)<marker,'Cloud injection before final finish');
    const name=`${shaders.length}-${material.name}.frag.glsl`;writeFileSync(resolve(out,'material-shaders',name),shader.fragmentShader);
    shaders.push({name:material.name,...material.userData.cloudShadow,file:name,fragmentSha256:sha(shader.fragmentShader)});
  }
  assert(shaders.length===count&&after.cloudShadows.metadata.active===1&&!after.cloudShadows.metadata.failures.length,'Material binding count/fault');
  record('one shared field after every existing art finish; twenty idempotent binds',{materials:shaders,sharedUniformObjects:true,bindingCycles:20});
  const basic=new MeshBasicMaterial(),mesh=new Mesh([...materials][0].isMaterial?after.scene.getObjectByName('courtyard-ground').geometry:undefined,basic);
  const fixture=new Scene();fixture.add(mesh);const state=m.createCloudShadowState(true,2),binding=createCloudShadowBinding(state);
  const original=basic.onBeforeCompile;binding.bind(fixture);assert(original===basic.onBeforeCompile&&!basic.userData.cloudShadow,'Unlit/magic material modified');
  binding.dispose();binding.dispose();basic.dispose();record('unlit magic/emissive class excluded and dispose idempotent',{unlitUnchanged:true});
  const sourceMaterial=[...materials].find(a=>a.userData.artSurface==='ground');
  const invalid={vertexShader:ShaderLib.lambert.vertexShader,fragmentShader:ShaderLib.lambert.fragmentShader.replace('#include <opaque_fragment>',''),uniforms:UniformsUtils.clone(ShaderLib.lambert.uniforms)};
  const warnings=[],warn=console.warn;console.warn=(...a)=>warnings.push(a.map(String).join(' '));
  try{sourceMaterial.onBeforeCompile(invalid,undefined)}finally{console.warn=warn}
  assert(sharedActive.value===0&&after.cloudShadows.metadata.failures.length===1&&!invalid.fragmentShader.includes('CLOUD_SHADOW_FINISH'),'Cloud anchor fallback failed');
  record('explicit shader-anchor fault disables shared shade and retains original finish',{method:'intentional missing shader anchor fixture; not a real production compile error',active:sharedActive.value,warnings});
  for(const a of appearances)a.dispose();before.dispose();after.dispose();after.dispose();
  writeFileSync(resolve(out,'model-and-materials.json'),JSON.stringify({passed:true,candidateId:build.candidateId,method:'actual source scene/material objects through Vite SSR; CPU field reference and shader composition checks, not GPU pixels or real-time browser proof',cases,sourceSha256:Object.fromEntries(build.changedRuntimeSources.map(n=>[n,sha(readFileSync(resolve(root,n)))]))},null,2)+'\n');
  process.stdout.write(`PASS ${cases.length} scene/material/field groups\n`);
} finally {await server.close()}
