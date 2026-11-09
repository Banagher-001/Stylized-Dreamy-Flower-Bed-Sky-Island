import { MeshLambertMaterial } from 'three';

/** One shared single-sided material for solid body/wing pieces. No Art-surface
 * tag: the existing grass/stone cloud shader must not wrap a bird material.
 */
export function createBirdMaterial() {
  const material = new MeshLambertMaterial({ color: 0xffffff, vertexColors: true, flatShading: true,
    transparent: true, depthTest: true, depthWrite: false, alphaTest: .012, toneMapped: false });
  material.name = 'courtyard-birds';material.customProgramCacheKey = () => 'courtyard-birds-hinge-v2';
  // Match the courtyard's art-directed, bright palette while retaining the
  // original sun/fill face response. No emissive glow or extra light/pass.
  material.color.multiplyScalar(1.5);
  material.onBeforeCompile = shader => {
    shader.vertexShader = shader.vertexShader.replace('#include <common>', '#include <common>\nattribute float birdAlpha; attribute float birdWing; attribute float birdPart; varying float vBirdAlpha;')
      .replace('#include <begin_vertex>', `#include <begin_vertex>
vBirdAlpha = birdAlpha;
if (abs(birdPart) > 0.5) {
  float angle = -birdPart * birdWing;
  float c = cos(angle), s = sin(angle);
  transformed.xy = mat2(c, s, -s, c) * transformed.xy;
  transformed += vec3(birdPart * 0.075, 0.0, 0.015);
}`);
    shader.fragmentShader = shader.fragmentShader.replace('#include <common>', '#include <common>\nvarying float vBirdAlpha;')
      .replace('#include <alphatest_fragment>', 'diffuseColor.a *= vBirdAlpha;\n#include <alphatest_fragment>');
  };
  return material;
}
