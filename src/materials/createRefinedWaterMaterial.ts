import { Color, Vector4 } from 'three';
import { createArtMaterial } from './createArtMaterial';
import type { WaterState } from './createWaterMaterial';
import { layoutConfig } from '../config/layout';
import { waterConfig } from '../config/water';
import { fountainConfig as config } from '../config/fountain';

/** Opaque, world-attached artwork: one existing surface, original shadow/depth path. */
export function createRefinedWaterMaterial(state: WaterState) {
  const material = createArtMaterial('water');
  material.name = 'courtyard-water-refined-surface';material.userData.waterKind = 'refined-surface';
  material.customProgramCacheKey = () => 'courtyard-water-refined-surface-v1';
  const baseCompile = material.onBeforeCompile.bind(material);
  material.onBeforeCompile = (shader, renderer) => {
    baseCompile(shader, renderer);
    const f = layoutConfig.fountain;
    Object.assign(shader.uniforms, {
      uPoolTime: state.time, uPoolImpacts: state.impacts,
      uPoolOrigin: { value: new Vector4(f.position[0], f.position[2], Math.cos(f.rotationY), Math.sin(f.rotationY)) },
      uPoolMotion: { value: new Vector4(config.flowSpeed, config.waveSpeed, config.waveStrength, config.rippleStrength) },
      uPoolBoundary: { value: new Vector4(f.innerRadius * Math.cos(Math.PI / 8), ...config.foamWidth, waterConfig.ripples.lifetime) },
      uPoolShallow: { value: new Color(config.colors.shallow) }, uPoolBase: { value: new Color(config.colors.base) },
      uPoolMiddle: { value: new Color(config.colors.middle) }, uPoolDeep: { value: new Color(config.colors.deep) },
      uPoolShade: { value: new Color(config.colors.shade) }, uPoolWhite: { value: new Color(config.colors.white) },
    });
    const declarations = /* glsl */`
      uniform float uPoolTime;
      uniform vec4 uPoolImpacts[${waterConfig.ripples.capacity}];
      uniform vec4 uPoolOrigin; uniform vec4 uPoolMotion; uniform vec4 uPoolBoundary;
      uniform vec3 uPoolShallow; uniform vec3 uPoolBase; uniform vec3 uPoolMiddle;
      uniform vec3 uPoolDeep; uniform vec3 uPoolShade; uniform vec3 uPoolWhite;
    `;
    const response = /* glsl */`
      vec2 delta = vArtWorldPosition.xz - uPoolOrigin.xy;
      vec2 p = vec2(uPoolOrigin.z * delta.x - uPoolOrigin.w * delta.y,
                    uPoolOrigin.w * delta.x + uPoolOrigin.z * delta.y);
      float t = uPoolTime;
      vec2 drift = vec2(t, -t * .25) * uPoolMotion.x;
      float broad = artNoise(p * vec2(2.2, 1.6) + drift * .5 + vec2(3.7, 6.1));
      float grain = artNoise(p * 18.0 + drift);
      vec2 q = p + vec2((broad - .5) * .20, (artNoise(p * 2.8 + vec2(8.4, 1.7) - drift) - .5) * .18) + drift * .65;
      vec2 leftShape = mat2(.96, -.28, .28, .96) * (q - vec2(-1.3, -.25));
      float leftReflection = length(leftShape / vec2(.36, 1.62));
      vec2 farShape = q - vec2(.30, -1.68);
      farShape.y += sin(farShape.x * 2.0) * .10;
      float farReflection = length(farShape / vec2(1.42, .31));
      vec2 nearShape = mat2(.91, .41, -.41, .91) * (q - vec2(1.12, .95));
      float nearReflection = length(nearShape / vec2(.24, .64));
      float silhouette = min(min(leftReflection, farReflection), nearReflection);
      silhouette += (broad - .5) * .70 + (grain - .5) * .12;
      float aa = clamp(max(fwidth(p.x), fwidth(p.y)), .003, .12);
      float detail = 1.0 - smoothstep(.035, .095, aa);
      float reflection = 1.0 - smoothstep(.93 - aa, 1.04 + aa, silhouette);
      float centerDistance = length(p);
      reflection *= smoothstep(.55, .85, centerDistance);

      float shoreDistance = 10.0;
      for (int i = 0; i < 8; i++) {
        float angle = (float(i) + .5) * PI / 4.0;
        shoreDistance = min(shoreDistance, uPoolBoundary.x - dot(p, vec2(cos(angle), -sin(angle))));
      }
      float shelf = smoothstep(.025, .18, shoreDistance);
      float depth = smoothstep(.28, 1.25, shoreDistance) * .26;
      vec3 clearWater = mix(uPoolShallow, uPoolBase, shelf);
      clearWater = mix(clearWater, uPoolMiddle, depth);
      vec3 litWater = mix(clearWater, uPoolDeep, reflection * .96);

      float wave = smoothstep(.955, .995, sin(centerDistance * 12.0 - t * uPoolMotion.y * 12.0 + broad));
      wave *= smoothstep(.65, .9, centerDistance) * (1.0 - smoothstep(1.5, 1.95, centerDistance));
      wave *= smoothstep(.52, .76, artNoise(p * 7.5 + drift)) * uPoolMotion.z;
      float glint = smoothstep(.78, .94, artNoise(p * 7.0 - drift))
        * smoothstep(.90, .99, sin(p.x * 11.0 + p.y * 6.0 - t * .72 + broad * 3.0)) * .64;
      float foam = (1.0 - smoothstep(uPoolBoundary.y, uPoolBoundary.z + aa * .35, shoreDistance))
        * smoothstep(.71, .88, artNoise(p * 12.0 + drift)) * .48;
      float impacts = 0.0;
      for (int i = 0; i < ${waterConfig.ripples.capacity}; i++) {
        vec4 event = uPoolImpacts[i];
        float radius = .025 + event.z * ${waterConfig.ripples.speed.toFixed(2)};
        float distanceToRing = abs(length(p - event.xy) - radius);
        float ring = 1.0 - smoothstep(.008, .018 + aa * .3, distanceToRing);
        float ageFade = pow(clamp(1.0 - event.z / uPoolBoundary.w, 0.0, 1.0), 2.0);
        float broken = smoothstep(.22, .47, artNoise(p * 9.0 + vec2(float(i) * 3.1, 5.0)));
        impacts = max(impacts, ring * ageFade * event.w * broken * uPoolMotion.w);
      }
      float white = max(max(wave, glint) * mix(.25, 1.0, detail), max(foam, impacts));
      litWater = mix(litWater, uPoolWhite, white);
      vec3 shadedWater = mix(uPoolShade, uPoolDeep * .84, reflection * .78);
      shadedWater = mix(shadedWater, uPoolWhite, white * .13);
      outgoingLight = mix(shadedWater, litWater, getShadowMask());
    `;
    const anchor = 'outgoingLight = mix(uArtWaterShade, uArtWater, getShadowMask());';
    if (!shader.fragmentShader.includes(anchor)) throw new Error('Pool surface extension anchor changed.');
    shader.fragmentShader = shader.fragmentShader.replace('void main() {', `${declarations}\nvoid main() {`).replace(anchor, response);
  };
  return material;
}
