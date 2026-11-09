import { Color, LinearSRGBColorSpace, Mesh, MeshBasicMaterial, PCFShadowMap, Vector3, Vector4, WebGLRenderer, WebGLRenderTarget } from 'three';
import { createScene } from '../../src/scene/createScene';
import { sampleOrbPhases, sampleOrbSurfaceNormal, sampleOrbSurfaceRadius } from '../../src/animation/orbSurface';
import { orbConfig } from '../../src/config/orb';
import { resolveTourPose, tourPoses } from '../../src/tour/route';

export function inspectFlowField() {
  const phases = new Vector4(), normal = new Vector3(), p = new Vector3(), u = new Vector3(), v = new Vector3(), surfaceU = new Vector3(), surfaceV = new Vector3();
  let maxNormalError = 0, maxRadiusJump = 0, maxCircularPhaseJump = 0, samples = 0;
  const epsilon = 1e-5;
  const times = [0, 2, 6, 60, 600, 3600, 86400];
  for (const period of [orbConfig.flow.mainPeriod, orbConfig.flow.detailPeriod, orbConfig.flow.turnPeriod])
    for (const cycle of [1, 19, Math.floor(86400 / period)]) times.push(period * cycle - epsilon, period * cycle + epsilon);
  for (const time of times) {
    sampleOrbPhases(time, phases);
    if (Math.abs(phases.x) > 1 || Math.abs(phases.y) > 1 || phases.z < 0 || phases.z > 2 * Math.PI || phases.w < 0 || phases.w > 2 * Math.PI) throw Error('Unbounded phase');
    const before = sampleOrbPhases(time - epsilon), after = sampleOrbPhases(time + epsilon);
    for (const [a, b] of [[before.z, after.z], [before.w, after.w]]) maxCircularPhaseJump = Math.max(maxCircularPhaseJump, Math.hypot(Math.cos(a) - Math.cos(b), Math.sin(a) - Math.sin(b)));
    for (let i = 0; i <= 64; i++) {
      const latitude = (i / 64) * 2 - 1, ring = Math.sqrt(1 - latitude * latitude);
      p.set(ring * Math.cos(i * 2.39996323), latitude, ring * Math.sin(i * 2.39996323));
      u.set(Math.abs(p.y) > .9 ? 1 : 0, Math.abs(p.y) > .9 ? 0 : 1, 0).cross(p).normalize();v.crossVectors(p, u);
      const radius = sampleOrbSurfaceRadius(p.x, p.y, p.z, phases);
      sampleOrbSurfaceNormal(p.x, p.y, p.z, phases, normal);
      const point = p.clone().multiplyScalar(radius);
      for (const [tangent, result] of [[u, surfaceU], [v, surfaceV]]) {
        const n = p.clone().addScaledVector(tangent, epsilon).normalize();
        result.copy(n).multiplyScalar(sampleOrbSurfaceRadius(n.x, n.y, n.z, phases)).sub(point).divideScalar(epsilon);
      }
      const numerical = surfaceU.clone().cross(surfaceV).normalize();
      maxNormalError = Math.max(maxNormalError, 1 - normal.dot(numerical));
      maxRadiusJump = Math.max(maxRadiusJump, Math.abs(sampleOrbSurfaceRadius(p.x, p.y, p.z, before) - sampleOrbSurfaceRadius(p.x, p.y, p.z, after)));
      if (radius < .966 - 1e-12 || radius > 1.034 + 1e-12 || normal.dot(p) < .9) throw Error('Bad surface or normal');
      samples++;
    }
  }
  if (maxNormalError > 1e-8 || maxRadiusJump > 1e-5 || maxCircularPhaseJump > .0001) throw Error('Field continuity or normal disagreement');
  const world = createScene({}, 'refined', 'lively'), orb = world.scene.getObjectByName('fountain-water-crown');
  const positions = orb.geometry.attributes.position, rest = orb.geometry.attributes.orbRest;
  let seamChecks = 0, maxSeamGap = 0;
  for (const time of times) {
    world.update(time);
    for (let row = 0; row <= orbConfig.sphereSegments[1]; row++) {
      const left = row * (orbConfig.sphereSegments[0] + 1), right = left + orbConfig.sphereSegments[0];
      p.fromBufferAttribute(positions, left);u.fromBufferAttribute(positions, right);maxSeamGap = Math.max(maxSeamGap, p.distanceTo(u));seamChecks++;
    }
    for (const row of [0, orbConfig.sphereSegments[1]]) {
      const first = row * (orbConfig.sphereSegments[0] + 1);p.fromBufferAttribute(positions, first);
      for (let i = 1; i <= orbConfig.sphereSegments[0]; i++) { u.fromBufferAttribute(positions, first + i);maxSeamGap = Math.max(maxSeamGap, p.distanceTo(u));seamChecks++; }
    }
  }
  if (maxSeamGap > 1e-6 || rest.usage !== 35044) throw Error('Cracked seam/pole or nonstatic rest attribute');
  world.dispose();
  return { passed: true, times, directionSamples: samples, includesNorthSouthPoles: true, seamAndPoleChecks: seamChecks, maxSeamAndPoleGap: maxSeamGap, staticRestAttribute: true, maxNormalError, maxRadiusJumpAcross20Microseconds: maxRadiusJump,
    maxCircularPhaseJumpAcross20Microseconds: maxCircularPhaseJump, radialEnvelope: [.966, 1.034],
    method: 'independent finite-difference surface tangent normals; separate phase-wrap neighborhoods through 24h; no longitude/latitude UV' };
}

/** Diagnostics use the actual production white-mix expression, original depth,
 * shader and CPU shape. Temporary renderer/target are outside the app and disposed.
 */
export function inspectFlowHighlights() {
  const world = createScene({}, 'refined', 'lively'), ball = world.scene.getObjectByName('fountain-water-crown');
  const originals = [], black = new MeshBasicMaterial({ color: 0 });world.scene.background = new Color(0);
  world.scene.traverse(object => { if (object instanceof Mesh && object !== ball) { originals.push([object, object.material]);object.material = black; } });
  const compile = ball.material.onBeforeCompile.bind(ball.material);
  ball.material.onBeforeCompile = (shader, renderer) => {
    compile(shader, renderer);
    shader.fragmentShader = shader.fragmentShader.replace('outgoingLight = mix(uOrbShade, orbColor, getShadowMask());', 'outgoingLight = vec3(step(.5, clamp(movingHighlight + rim * .13, 0.0, .86)), 1.0, 0.0);');
  };
  ball.material.customProgramCacheKey = () => 'step3-test-only-highlight-factor-v2';
  const renderer = new WebGLRenderer({ antialias: false });renderer.outputColorSpace = LinearSRGBColorSpace;renderer.shadowMap.enabled = true;renderer.shadowMap.type = PCFShadowMap;
  const samples = [];
  for (const width of [384, 1024]) {
    const height = Math.round(width * 793 / 1440), target = new WebGLRenderTarget(width, height), pixels = new Uint8Array(width * height * 4);
    renderer.setSize(width, height, false);renderer.setRenderTarget(target);
    for (const key of ['O', 'W']) {
      const pose = resolveTourPose(tourPoses[key], 1440 / 793);world.setAspect(1440 / 793);world.setViewHeight(pose.viewHeight);world.camera.position.set(...pose.position);world.camera.lookAt(...pose.target);world.camera.updateMatrixWorld(true);
      for (let tick = 0; tick <= 48; tick++) {
        const time = tick / 4;world.update(time);renderer.render(world.scene, world.camera);renderer.readRenderTargetPixels(target, 0, 0, width, height, pixels);
        let area = 0, white = 0;
        for (let i = 0; i < pixels.length; i += 4) if (pixels[i + 1] > 250) { area++;if (pixels[i] > 250) white++; }
        if (!area || white / area > .5) throw Error('Missing orb or excessive white area ' + white / area);
        samples.push({ width, height, pose: key, time, orbPixels: area, whiteDominantPixels: white, whiteDominantPercent: 100 * white / area });
      }
    }
    renderer.setRenderTarget(null);target.dispose();
  }
  renderer.dispose();renderer.forceContextLoss();for (const [object, material] of originals) object.material = material;black.dispose();world.dispose();
  return { passed: true, method: 'actual original shader white-mix >= .5; green=visible orb with real depth, red=white-dominant surface; two sampling widths, 12-second quarter-second sweep; NOT production render passes or hardware FPS', samples };
}
