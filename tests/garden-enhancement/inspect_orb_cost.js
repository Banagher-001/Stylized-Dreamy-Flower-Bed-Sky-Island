import { SRGBColorSpace, Vector3, WebGLRenderer } from 'three';
import { createScene } from '../../src/scene/createScene';
import { resolveTourPose, tourPoses } from '../../src/tour/route';

const stats = values => ({ count: values.length, meanMs: values.reduce((a,b)=>a+b,0)/values.length,
  p50Ms: [...values].sort((a,b)=>a-b)[Math.floor((values.length-1)*.5)], p95Ms: [...values].sort((a,b)=>a-b)[Math.floor((values.length-1)*.95)], maxMs: Math.max(...values) });

/** Causal diagnostic, NOT an app FPS substitute: same orb pixel footprint,
 * isolated color shader, fixed analytic timestamps, blocking GL completion.
 * All other meshes/shadow passes hidden equally. Production is not modified.
 */
export function inspectOrbCost() {
  const world=createScene({enabled:false},'refined','lively');
  const cpu=[];
  for(let batch=0;batch<300;batch++) {
    const begin=performance.now();
    for(let i=0;i<60;i++)world.update(2+(batch*60+i)/60);
    cpu.push((performance.now()-begin)/60);
  }
  const ball=world.scene.getObjectByName('fountain-water-crown');
  world.scene.traverse(object=>{if(object.isMesh&&object!==ball)object.visible=false;if(object.isLight)object.castShadow=false;});
  const renderer=new WebGLRenderer({antialias:false});renderer.setPixelRatio(1);renderer.setSize(128,128,false);renderer.outputColorSpace=SRGBColorSpace;
  const gl=renderer.getContext(), center=new Vector3(), offset=new Vector3(), cases=[];
  for(const key of ['O','W']) {
    const pose=resolveTourPose(tourPoses[key],1440/793);
    world.update(2);world.scene.updateMatrixWorld(true);ball.getWorldPosition(center);offset.copy(center).sub(new Vector3(...pose.target));
    world.setAspect(1);world.setViewHeight(pose.viewHeight*128/793);world.camera.position.set(...pose.position).add(offset);world.camera.lookAt(center);world.camera.updateMatrixWorld(true);
    for(let i=0;i<32;i++){world.update(2+i/60);renderer.render(world.scene,world.camera);gl.finish();}
    const total=[],submit=[],updates=[];
    for(let i=0;i<180;i++) {
      const begin=performance.now();world.update(2+i/60);const updated=performance.now();renderer.render(world.scene,world.camera);const submitted=performance.now();gl.finish();const end=performance.now();
      total.push(end-begin);submit.push(submitted-updated);updates.push(updated-begin);
    }
    cases.push({pose:key,totalBlockingMs:stats(total),cpuSubmitMs:stats(submit),updateMs:stats(updates),totalSamplesMs:total,submitSamplesMs:submit,updateSamplesMs:updates});
  }
  renderer.dispose();renderer.forceContextLoss();world.dispose();
  return {passed:true,method:'diagnostic only; same projected orb pixel size as1440x793 native O/W;128px tile; other meshes and shadow passes hidden; same analytic 60Hz timestamps;32frame warm,180samples; GL.finish includes actual software GPU completion,not hardware FPS',cpuUpdateBatchAverages:stats(cpu),cpuSamplesMs:cpu,cases};
}
