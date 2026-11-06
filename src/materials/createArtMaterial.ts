import { Color, MeshLambertMaterial, Vector4 } from 'three';
import { lightingConfig } from '../config/lighting';
import { palette } from '../config/palette';
import { stoneConfig } from '../config/stone';
import { vegetationConfig } from '../config/vegetation';
import { applyEnvironmentMotion } from './applyEnvironmentMotion';
import type { EnvironmentState } from '../animation/environmentMotion';

type ArtSurface = 'ground' | 'stone' | 'water' | 'foliage' | 'flower';
export interface StoneColors { top?: string; side?: string; shade?: string; }

/** Keep Three's geometry, depth and real shadow pipeline; replace only the color response. */
export function createArtMaterial(surface: ArtSurface, environment?: EnvironmentState, stoneColors: StoneColors = {}) {
  const material = new MeshLambertMaterial();
  const plant = surface === 'foliage' || surface === 'flower';
  material.name = `courtyard-${surface}`;
  material.userData.artSurface = surface;
  const environmentEnabled = environment?.options.enabled && (plant || surface === 'ground');
  material.customProgramCacheKey = () => `courtyard-art-${surface}-v3${environmentEnabled ? '-environment-v1' : ''}`;

  material.onBeforeCompile = (shader) => {
    const trees = lightingConfig.treeShadows;
    const ground = vegetationConfig.ground;
    const detail = vegetationConfig.treeDetail;
    Object.assign(shader.uniforms, {
      uArtSunAmount: { value: lightingConfig.sun.intensity },
      uArtFillAmount: { value: lightingConfig.fill.intensity },
      uArtStoneVariation: { value: stoneConfig.colorVariation },
      uArtGrass: { value: new Color(palette.grassBase) },
      uArtGrassLight: { value: new Color(palette.grassLight) },
      uArtGrassDark: { value: new Color(palette.grassDark) },
      uArtGrassShadow: { value: new Color(palette.treeShadow) },
      uArtStoneTop: { value: new Color(stoneColors.top ?? palette.stoneLight) },
      uArtStoneSide: { value: new Color(stoneColors.side ?? palette.stoneSide) },
      uArtStoneShade: { value: new Color(stoneColors.shade ?? palette.stoneShade) },
      uArtWater: { value: new Color(palette.waterBase) },
      uArtWaterShade: { value: new Color(palette.waterShade) },
      uArtPlantShade: { value: new Color(palette.plantShade) },
      uArtFlowerShade: { value: new Color(palette.flowerShade) },
      uArtFlowerCenter: { value: new Color(palette.flowerCenter) },
      uArtGroundEnabled: { value: ground.enabled ? 1 : 0 },
      uArtGroundScales: { value: new Vector4(ground.macroScale, ground.macroStrength, ground.detailScale, ground.detailStrength) },
      uArtGroundDensity: { value: ground.detailDensity },
      uArtQuietRegion: { value: new Vector4(ground.quietCenter[0], ground.quietCenter[1], ground.quietRadius[0], ground.quietRadius[1]) },
      uArtTreeDetailEnabled: { value: detail.enabled ? 1 : 0 },
      uArtTreeDetail: { value: new Vector4(detail.branchScale, detail.leafScale, detail.edgeBreakup, detail.gapStrength) },
      uArtTreesEnabled: { value: trees.enabled ? 1 : 0 },
      uArtTreeNoiseScale: { value: trees.edgeNoiseScale },
      uArtTreeNoiseAmount: { value: trees.edgeNoiseAmount },
      uArtTreeSoftness: { value: trees.edgeSoftness },
      uArtTreePatches: {
        value: trees.patches.map(p => new Vector4(p.center[0], p.center[1], p.radius[0], p.radius[1])),
      },
      uArtTreeRotations: { value: trees.patches.map(p => p.rotation) },
    });

    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', `#include <common>\nvarying vec3 vArtWorldPosition;
        ${surface === 'stone' ? 'attribute float stoneTint; varying float vArtStoneTint;' : ''}
        ${plant ? 'attribute float plantPart; attribute float plantHeight; varying float vArtPlantPart; varying float vArtPlantHeight;' : ''}
      `)
      .replace('#include <worldpos_vertex>', `#include <worldpos_vertex>
        vec4 artPosition = vec4(transformed, 1.0);
        #ifdef USE_BATCHING
          artPosition = batchingMatrix * artPosition;
        #endif
        #ifdef USE_INSTANCING
          artPosition = instanceMatrix * artPosition;
        #endif
        vArtWorldPosition = (modelMatrix * artPosition).xyz;
        ${surface === 'stone' ? 'vArtStoneTint = stoneTint;' : ''}
        ${plant ? 'vArtPlantPart = plantPart; vArtPlantHeight = plantHeight;' : ''}
      `);

    const declarations = /* glsl */`
      varying vec3 vArtWorldPosition;
      ${surface === 'stone' ? 'varying float vArtStoneTint; uniform float uArtStoneVariation;' : ''}
      ${plant ? 'varying float vArtPlantPart; varying float vArtPlantHeight;' : ''}
      uniform float uArtSunAmount;
      uniform float uArtFillAmount;
      uniform vec3 uArtGrass;
      uniform vec3 uArtGrassLight;
      uniform vec3 uArtGrassDark;
      uniform vec3 uArtGrassShadow;
      uniform vec3 uArtStoneTop;
      uniform vec3 uArtStoneSide;
      uniform vec3 uArtStoneShade;
      uniform vec3 uArtWater;
      uniform vec3 uArtWaterShade;
      uniform vec3 uArtPlantShade;
      uniform vec3 uArtFlowerShade;
      uniform vec3 uArtFlowerCenter;
      uniform float uArtGroundEnabled;
      uniform vec4 uArtGroundScales;
      uniform float uArtGroundDensity;
      uniform vec4 uArtQuietRegion;
      uniform float uArtTreeDetailEnabled;
      uniform vec4 uArtTreeDetail;
      uniform float uArtTreesEnabled;
      uniform float uArtTreeNoiseScale;
      uniform float uArtTreeNoiseAmount;
      uniform float uArtTreeSoftness;
      uniform vec4 uArtTreePatches[${trees.patches.length}];
      uniform float uArtTreeRotations[${trees.patches.length}];

      float artHash(vec2 p) {
        return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
      }
      float artNoise(vec2 p) {
        vec2 cell = floor(p);
        vec2 f = fract(p);
        vec2 t = f * f * (3.0 - 2.0 * f);
        return mix(mix(artHash(cell), artHash(cell + vec2(1.0, 0.0)), t.x),
                   mix(artHash(cell + vec2(0.0, 1.0)), artHash(cell + vec2(1.0)), t.x), t.y);
      }
      float artCanopy(vec2 position) {
        float distanceToCanopy = 10.0;
        for (int i = 0; i < ${trees.patches.length}; i++) {
          vec4 canopyBounds = uArtTreePatches[i];
          float c = cos(uArtTreeRotations[i]);
          float s = sin(uArtTreeRotations[i]);
          vec2 local = mat2(c, -s, s, c) * (position - canopyBounds.xy);
          float d = length(local / canopyBounds.zw);
          d += (artNoise(position * uArtTreeNoiseScale) - 0.5) * uArtTreeNoiseAmount;
          distanceToCanopy = min(distanceToCanopy, d);
        }
        float silhouette = 1.0 - smoothstep(1.0 - uArtTreeSoftness, 1.0 + uArtTreeSoftness, distanceToCanopy);
        if (uArtTreeDetailEnabled < 0.5) return silhouette * uArtTreesEnabled;
        float branches = artNoise(position * uArtTreeDetail.x + vec2(8.3, 3.7));
        float leaves = artHash(floor(position * uArtTreeDetail.y));
        float brokenDistance = distanceToCanopy + (branches - 0.5) * uArtTreeDetail.z + (leaves - 0.5) * 0.06;
        float body = 1.0 - smoothstep(1.0 - uArtTreeSoftness, 1.0 + uArtTreeSoftness, brokenDistance);
        float holes = step(0.74, branches) * step(0.68, artNoise(position * 8.5));
        float edge = step(0.68, distanceToCanopy);
        float gaps = max(holes, edge * step(0.78, leaves) * step(0.44, branches)) * uArtTreeDetail.w;
        float fragments = (1.0 - body) * step(distanceToCanopy, 1.12)
          * step(0.76, leaves) * step(0.56, branches);
        return max(body * (1.0 - gaps), fragments) * uArtTreesEnabled;
      }
    `;

    const response: Record<ArtSurface, string> = {
      ground: /* glsl */`
        float daylight = clamp(uArtSunAmount * 0.8 + uArtFillAmount * 0.2, 0.0, 1.0);
        vec3 sunlitGrass = mix(uArtGrassDark, uArtGrass, daylight);
        vec2 groundPosition = vArtWorldPosition.xz;
        float quiet = 1.0 - smoothstep(0.7, 1.2, length((groundPosition - uArtQuietRegion.xy) / uArtQuietRegion.zw));
        float macro = artNoise(groundPosition * uArtGroundScales.x + vec2(4.2, 7.3));
        vec3 groundVariation = mix(uArtGrassDark, uArtGrassLight, smoothstep(0.18, 0.86, macro));
        sunlitGrass = mix(sunlitGrass, groundVariation, uArtGroundScales.y * (1.0 - quiet * 0.65) * uArtGroundEnabled);
        vec2 detailCell = floor(groundPosition * uArtGroundScales.z);
        float speckle = step(1.0 - uArtGroundDensity, artHash(detailCell)) * (artHash(detailCell + vec2(3.2, 9.1)) * 2.0 - 1.0);
        sunlitGrass *= 1.0 + speckle * uArtGroundScales.w * (1.0 - quiet * 0.85) * uArtGroundEnabled;
        float occlusion = max(1.0 - getShadowMask(), artCanopy(vArtWorldPosition.xz));
        outgoingLight = mix(sunlitGrass, uArtGrassShadow, occlusion);
      `,
      stone: /* glsl */`
        vec3 worldNormal = inverseTransformDirection(normal, viewMatrix);
        float sunFacing = 0.0;
        #if NUM_DIR_LIGHTS > 0
          sunFacing = max(dot(normal, directionalLights[0].direction), 0.0);
        #endif
        float sunAmount = clamp(uArtSunAmount, 0.0, 1.0);
        float fillAmount = clamp(uArtFillAmount, 0.0, 1.0);
        vec3 coolFace = uArtStoneShade * mix(0.72, 1.0, fillAmount);
        vec3 sideFace = mix(coolFace, uArtStoneSide, smoothstep(0.02, 0.56, sunFacing) * sunAmount);
        vec3 topFace = mix(uArtStoneSide, uArtStoneTop, sunAmount);
        vec3 litStone = mix(sideFace, topFace, smoothstep(0.65, 0.95, worldNormal.y));
        vec3 shadedStone = mix(coolFace, litStone, 0.12 * fillAmount);
        outgoingLight = mix(shadedStone, litStone, getShadowMask());
        outgoingLight *= 1.0 + vArtStoneTint * uArtStoneVariation;
      `,
      water: /* glsl */`
        outgoingLight = mix(uArtWaterShade, uArtWater, getShadowMask());
      `,
      foliage: /* glsl */`
        float plantOcclusion = max(1.0 - getShadowMask(), artCanopy(vArtWorldPosition.xz));
        vec3 litPlant = diffuseColor.rgb * mix(0.93, 1.0, clamp(vArtPlantHeight, 0.0, 1.0));
        outgoingLight = mix(litPlant, uArtPlantShade, plantOcclusion);
      `,
      flower: /* glsl */`
        float flowerOcclusion = max(1.0 - getShadowMask(), artCanopy(vArtWorldPosition.xz));
        vec3 litFlower = mix(diffuseColor.rgb, uArtFlowerCenter, vArtPlantPart);
        vec3 shadedFlower = mix(uArtFlowerShade, uArtFlowerCenter * 0.65, vArtPlantPart);
        outgoingLight = mix(litFlower, shadedFlower, flowerOcclusion);
      `,
    };

    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', `#include <common>\n${declarations}`)
      .replace('#include <shadowmap_pars_fragment>', '#include <shadowmap_pars_fragment>\n#include <shadowmask_pars_fragment>')
      .replace('#include <opaque_fragment>', `${response[surface]}\n#include <opaque_fragment>`);
    if (environmentEnabled) applyEnvironmentMotion(shader, plant, environment!);
  };

  return material;
}
