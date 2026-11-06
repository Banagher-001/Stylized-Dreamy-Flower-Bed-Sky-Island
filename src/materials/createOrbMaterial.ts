import { Color } from 'three';
import { createArtMaterial } from './createArtMaterial';
import type { WaterState } from './createWaterMaterial';
import { orbConfig } from '../config/orb';

/** Opaque low-poly volume. Flat-shading derivatives follow the actual deformed faces. */
export function createOrbMaterial(state: WaterState) {
  const material = createArtMaterial('water');
  material.name = 'courtyard-living-orb';material.flatShading = true;
  material.customProgramCacheKey = () => 'courtyard-living-orb-v1';
  const baseCompile = material.onBeforeCompile.bind(material);
  material.onBeforeCompile = (shader, renderer) => {
    baseCompile(shader, renderer);
    Object.assign(shader.uniforms, {
      uOrbTime: state.time,
      uOrbBase: { value: new Color(orbConfig.colors.base) }, uOrbLight: { value: new Color(orbConfig.colors.light) },
      uOrbSide: { value: new Color(orbConfig.colors.side) }, uOrbShade: { value: new Color(orbConfig.colors.shade) },
      uOrbWhite: { value: new Color(orbConfig.colors.white) },
    });
    const declarations = /* glsl */`
      uniform float uOrbTime;
      uniform vec3 uOrbBase; uniform vec3 uOrbLight; uniform vec3 uOrbSide; uniform vec3 uOrbShade; uniform vec3 uOrbWhite;
    `;
    const response = /* glsl */`
      vec3 orbNormal = inverseTransformDirection(normal, viewMatrix);
      float sunFace = .5;
      #if NUM_DIR_LIGHTS > 0
        sunFace = max(dot(normal, directionalLights[0].direction), 0.0);
      #endif
      float volume = smoothstep(-.6, .7, orbNormal.y) * .6 + sunFace * .4;
      float band = floor(clamp(volume, 0.0, .999) * 4.0) / 3.0;
      vec3 orbColor = mix(uOrbSide, uOrbBase, band);
      orbColor = mix(orbColor, uOrbLight, smoothstep(.65, .95, volume) * .48);
      float edge = pow(1.0 - clamp(dot(normal, normalize(vViewPosition)), 0.0, 1.0), 2.6);
      float upper = smoothstep(-.12, .55, orbNormal.y);
      float crown = smoothstep(.78, .96, orbNormal.y) * smoothstep(-.25, .3, orbNormal.x + .4);
      float rim = smoothstep(.3, .8, edge) * upper * smoothstep(-.4, .2, orbNormal.z);
      float sheen = .035 * sin(uOrbTime * .55 + orbNormal.x * 4.0 + orbNormal.z * 3.0);
      orbColor = mix(orbColor, uOrbLight, max(sheen, 0.0));
      orbColor = mix(orbColor, uOrbWhite, clamp(max(crown * .82, rim * .75), 0.0, .86));
      outgoingLight = mix(uOrbShade, orbColor, getShadowMask());
    `;
    const anchor = 'outgoingLight = mix(uArtWaterShade, uArtWater, getShadowMask());';
    if (!shader.fragmentShader.includes(anchor)) throw new Error('Orb shader extension anchor changed.');
    shader.fragmentShader = shader.fragmentShader.replace('void main() {', `${declarations}\nvoid main() {`).replace(anchor, response);
  };
  return material;
}
