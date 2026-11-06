import { Color, Vector4 } from 'three';
import { createArtMaterial } from './createArtMaterial';
import { layoutConfig } from '../config/layout';
import { waterConfig } from '../config/water';

export function createWaterState() {
  return {
    time: { value: waterConfig.initialTime as number },
    impacts: { value: Array.from({ length: waterConfig.ripples.capacity }, () => new Vector4(0, 0, 0, 0)) },
  };
}
export type WaterState = ReturnType<typeof createWaterState>;

/** Extend only water's final color; Three.js depth, normals and actual shadows are retained. */
export function createWaterMaterial(state: WaterState = createWaterState(), kind: 'surface' | 'jet' = 'surface') {
  const material = createArtMaterial('water');
  material.name = `courtyard-water-${kind}`;
  material.flatShading = kind === 'jet';
  material.userData.waterKind = kind;
  material.customProgramCacheKey = () => `courtyard-water-${kind}-v1`;
  const baseCompile = material.onBeforeCompile.bind(material);
  material.onBeforeCompile = (shader, renderer) => {
    baseCompile(shader, renderer);
    const f = layoutConfig.fountain;
    Object.assign(shader.uniforms, {
      uWaterTime: state.time,
      uWaterImpacts: state.impacts,
      uWaterEnabled: { value: waterConfig.enabled ? 1 : 0 },
      uWaterBase: { value: new Color(waterConfig.colors.base) },
      uWaterDeep: { value: new Color(waterConfig.colors.deep) },
      uWaterShade: { value: new Color(waterConfig.colors.shade) },
      uWaterWhite: { value: new Color(waterConfig.colors.highlight) },
      uWaterJet: { value: new Color(waterConfig.colors.jet) },
      uWaterOrigin: { value: new Vector4(f.position[0], f.position[2], Math.cos(f.rotationY), Math.sin(f.rotationY)) },
      uWaterSurface: { value: new Vector4(waterConfig.surface.flowSpeed, waterConfig.surface.reflectionThreshold, waterConfig.surface.waveSpeed, waterConfig.surface.waveStrength) },
      uWaterRipple: { value: new Vector4(waterConfig.ripples.lifetime, waterConfig.ripples.speed, waterConfig.ripples.strength, f.innerRadius * Math.cos(Math.PI / 8)) },
    });
    const declarations = /* glsl */`
      uniform float uWaterTime;
      uniform float uWaterEnabled;
      uniform vec4 uWaterImpacts[${waterConfig.ripples.capacity}];
      uniform vec3 uWaterBase;
      uniform vec3 uWaterDeep;
      uniform vec3 uWaterShade;
      uniform vec3 uWaterWhite;
      uniform vec3 uWaterJet;
      uniform vec4 uWaterOrigin;
      uniform vec4 uWaterSurface;
      uniform vec4 uWaterRipple;
    `;
    const surface = /* glsl */`
      vec2 delta = vArtWorldPosition.xz - uWaterOrigin.xy;
      vec2 p = vec2(uWaterOrigin.z * delta.x - uWaterOrigin.w * delta.y,
                    uWaterOrigin.w * delta.x + uWaterOrigin.z * delta.y);
      float t = uWaterTime;
      vec2 drift = vec2(t * uWaterSurface.x, -t * uWaterSurface.x * 0.5);
      float warp = artNoise(p * 4.7 + vec2(-t * 0.022, t * 0.04));
      float field = artNoise(p * 1.8 + vec2(3.1, 6.4) + drift * 0.6);
      float leftBias = 1.0 - smoothstep(-1.6, 0.8, p.x);
      float brokenEdge = (artNoise(p * 22.0 + drift * 2.0) - 0.5) * 0.07;
      float reflection = smoothstep(uWaterSurface.y, uWaterSurface.y + 0.045, field * 0.88 + warp * 0.12 + leftBias * 0.12 + brokenEdge);
      float distanceFromCenter = length(p);
      float wave = smoothstep(0.94, 0.995, sin(distanceFromCenter * 14.0 - t * uWaterSurface.z * 14.0 + warp * 0.5));
      wave *= smoothstep(0.25, 0.5, distanceFromCenter) * (1.0 - smoothstep(1.2, 1.85, distanceFromCenter)) * uWaterSurface.w;
      wave *= smoothstep(0.24, 0.75, artNoise(p * 8.5 + drift));
      float glint = smoothstep(0.80, 0.94, artNoise(p * 9.0 + drift * 1.2))
        * smoothstep(0.72, 0.96, sin((p.x + p.y * 0.7) * 18.0 - t * 1.3 + warp * 7.0)) * 0.8;
      float impactRings = 0.0;
      for (int i = 0; i < ${waterConfig.ripples.capacity}; i++) {
        vec4 impact = uWaterImpacts[i];
        float age = impact.z;
        float radius = 0.025 + age * uWaterRipple.y;
        float ring = 1.0 - smoothstep(0.012, 0.022, abs(length(p - impact.xy) - radius));
        float fade = pow(clamp(1.0 - age / uWaterRipple.x, 0.0, 1.0), 2.0);
        impactRings = max(impactRings, ring * fade * impact.w * uWaterRipple.z);
      }
      float wallDistance = 10.0;
      for (int i = 0; i < 8; i++) {
        float angle = (float(i) + 0.5) * PI / 4.0;
        wallDistance = min(wallDistance, uWaterRipple.w - dot(p, vec2(cos(angle), -sin(angle))));
      }
      float edgeFoam = (1.0 - smoothstep(0.025, 0.07, wallDistance))
        * smoothstep(0.48, 0.72, artNoise(p * 14.0 + drift)) * 0.4;
      float whiteAmount = clamp(max(max(glint, wave), max(impactRings, edgeFoam)), 0.0, 0.85);
      vec3 litWater = mix(uWaterBase, uWaterDeep, reflection);
      litWater = mix(litWater, uWaterWhite, whiteAmount);
      vec3 shadedWater = mix(uWaterShade, uWaterDeep * 0.8, reflection * 0.8);
      shadedWater = mix(shadedWater, uWaterWhite, whiteAmount * 0.18);
      vec3 dynamicWater = mix(shadedWater, litWater, getShadowMask());
      outgoingLight = mix(mix(uArtWaterShade, uArtWater, getShadowMask()), dynamicWater, uWaterEnabled);
    `;
    const jet = /* glsl */`
      vec3 waterNormal = inverseTransformDirection(normal, viewMatrix);
      float lightFace = smoothstep(-0.2, 0.8, waterNormal.y);
      float crownSparkle = pow(max(waterNormal.y, 0.0), 14.0) * 0.25;
      vec3 litJet = mix(uWaterJet, uWaterWhite, lightFace * 0.4 + crownSparkle);
      outgoingLight = mix(uWaterShade, litJet, getShadowMask());
    `;
    const anchor = 'outgoingLight = mix(uArtWaterShade, uArtWater, getShadowMask());';
    if (!shader.fragmentShader.includes(anchor)) throw new Error('Water shader extension anchor changed.');
    shader.fragmentShader = shader.fragmentShader
      .replace('void main() {', `${declarations}\nvoid main() {`)
      .replace(anchor, kind === 'surface' ? surface : jet);
  };
  return material;
}
