import { Color } from 'three';
import type { Vector4 } from 'three';
import { createArtMaterial } from './createArtMaterial';
import { orbConfig } from '../config/orb';

/** Opaque low-poly volume. Flat-shading derivatives follow the actual deformed faces. */
export function createOrbMaterial(phases: Vector4) {
  const material = createArtMaterial('water');
  material.name = 'courtyard-living-orb';material.flatShading = true;
  material.customProgramCacheKey = () => 'courtyard-living-orb-flow-v2';
  const baseCompile = material.onBeforeCompile.bind(material);
  material.onBeforeCompile = (shader, renderer) => {
    baseCompile(shader, renderer);
    Object.assign(shader.uniforms, {
      uOrbPhases: { value: phases },
      uOrbBase: { value: new Color(orbConfig.colors.base) }, uOrbLight: { value: new Color(orbConfig.colors.light) },
      uOrbSide: { value: new Color(orbConfig.colors.side) }, uOrbShade: { value: new Color(orbConfig.colors.shade) },
      uOrbWhite: { value: new Color(orbConfig.colors.white) },
    });
    const declarations = /* glsl */`
      varying vec3 vOrbRest;
      uniform vec4 uOrbPhases;
      uniform vec3 uOrbBase; uniform vec3 uOrbLight; uniform vec3 uOrbSide; uniform vec3 uOrbShade; uniform vec3 uOrbWhite;
    `;
    const vector = (values: readonly number[]) => `vec3(${values.map(value => value.toFixed(6)).join(', ')})`;
    const flow = orbConfig.flow;
    const response = /* glsl */`
      // Rest coordinates interpolate across faces; normalize only per fragment.
      // No atan/UV wrapping, screen coordinates or independently running clock.
      vec3 rest = normalize(vOrbRest);
      vec3 q = vec3(uOrbPhases.x * rest.x - uOrbPhases.y * rest.z, rest.y,
                    uOrbPhases.y * rest.x + uOrbPhases.x * rest.z);
      float bend = dot(q, ${vector(flow.bend)}) + uOrbPhases.w;
      float mainPhase = dot(q, ${vector(flow.main)}) + ${flow.bendStrength.toFixed(6)} * sin(bend) + uOrbPhases.z;
      float detailPhase = dot(q, ${vector(flow.detail)}) - uOrbPhases.w;
      float wave = cos(mainPhase);
      // Derivative filtering broadens the crest at the original 384px sampling.
      // Unresolvable secondary ripples fade out instead of flashing single pixels.
      float aa = clamp(fwidth(wave) * .65, .035, .38);
      float flowBand = smoothstep(-.45 - aa, .45 + aa, wave);
      float crest = smoothstep(.76 - aa, .96 + aa, wave);
      float detailVisibility = 1.0 - smoothstep(.55, 1.6, fwidth(detailPhase));
      float detailWave = sin(detailPhase);
      float shortCrest = smoothstep(.72 - aa, .98 + aa, detailWave) * detailVisibility;
      vec3 orbNormal = inverseTransformDirection(normal, viewMatrix);
      float sunFace = .5;
      #if NUM_DIR_LIGHTS > 0
        sunFace = max(dot(normal, directionalLights[0].direction), 0.0);
      #endif
      float volume = smoothstep(-.6, .7, orbNormal.y) * .6 + sunFace * .4;
      vec3 orbColor = mix(uOrbSide, uOrbBase, smoothstep(.08, .92, volume));
      orbColor = mix(orbColor, uOrbLight, flowBand * .46);
      orbColor = mix(orbColor, uOrbSide, (1.0 - flowBand) * .20);
      float edge = pow(1.0 - clamp(dot(normal, normalize(vViewPosition)), 0.0, 1.0), 2.6);
      float litCrest = mix(.52, 1.0, sunFace) * mix(.65, 1.0, smoothstep(-.7, .55, orbNormal.y));
      float rim = smoothstep(.35, .85, edge) * smoothstep(-.15, .6, orbNormal.y);
      float movingHighlight = crest * litCrest * .85 + shortCrest * flowBand * .12;
      orbColor = mix(orbColor, uOrbWhite, clamp(movingHighlight + rim * .13, 0.0, .86));
      outgoingLight = mix(uOrbShade, orbColor, getShadowMask());
    `;
    const anchor = 'outgoingLight = mix(uArtWaterShade, uArtWater, getShadowMask());';
    if (!shader.fragmentShader.includes(anchor)) throw new Error('Orb shader extension anchor changed.');
    if (!shader.vertexShader.includes('#include <begin_vertex>')) throw new Error('Orb rest-position anchor changed.');
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nattribute vec3 orbRest; varying vec3 vOrbRest;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvOrbRest = orbRest;');
    shader.fragmentShader = shader.fragmentShader.replace('void main() {', `${declarations}\nvoid main() {`).replace(anchor, response);
  };
  return material;
}
