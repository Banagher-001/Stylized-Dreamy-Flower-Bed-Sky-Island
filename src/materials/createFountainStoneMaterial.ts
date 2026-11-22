import { Color, Vector4 } from 'three';
import { createStoneMaterial } from './createStoneMaterial';
import { layoutConfig } from '../config/layout';
import { fountainConfig as config } from '../config/fountain';

/** Bound only to pool stones, never to the shared courtyard stone material. */
export function createFountainStoneMaterial(finishKind: 'rim' | 'damp' | 'shelf' = 'rim') {
  const wetDetail = finishKind === 'damp';
  const shelf = finishKind === 'shelf';
  const material = createStoneMaterial(shelf
    ? { top: config.colors.shelfTop, side: config.colors.shelfSide, shade: config.colors.shelfShade }
    : { top: config.colors.stoneTop, side: config.colors.stoneSide, shade: config.colors.stoneShade });
  material.name = shelf ? 'courtyard-pool-shelf-stone' : wetDetail ? 'courtyard-pool-damp-stone' : 'courtyard-pool-stone';
  material.customProgramCacheKey = () => `${material.name}-v3`;
  const baseCompile = material.onBeforeCompile.bind(material);
  material.onBeforeCompile = (shader, renderer) => {
    baseCompile(shader, renderer);
    const f = layoutConfig.fountain;
    Object.assign(shader.uniforms, {
      uPoolStoneOrigin: { value: new Vector4(f.position[0], f.position[2], Math.cos(f.rotationY), Math.sin(f.rotationY)) },
      uPoolStoneLevels: { value: new Vector4(f.position[1], f.waterHeight, f.baseHeight, f.innerRadius) },
      uPoolStoneWet: { value: new Color(config.colors.wetStone) }, uPoolStoneOld: { value: new Color(config.colors.weathering) },
    });
    const declarations = /* glsl */`
      uniform vec4 uPoolStoneOrigin; uniform vec4 uPoolStoneLevels;
      uniform vec3 uPoolStoneWet; uniform vec3 uPoolStoneOld;
    `;
    const dampBand = /* glsl */`
      float aboveWater = poolY - uPoolStoneLevels.y;
      float tideEdge = .045 + .025 * wetNoise;
      float dampBand = (1.0 - smoothstep(.013, tideEdge + .033, aboveWater)) * side;
      vec3 soakedStone = mix(outgoingLight * .60, uPoolStoneWet * vec3(.73, .86, 1.02), .21);
      outgoingLight = mix(outgoingLight, soakedStone, dampBand * .82);
      float dryStone = smoothstep(.05, .14, aboveWater) * pedestal * side;
      outgoingLight = mix(outgoingLight, outgoingLight * vec3(1.14, 1.04, .90), dryStone * .81);
      float seamContact = (1.0 - smoothstep(.006, .032, aboveWater)) * (1.0 - pedestal) * innerFace * side;
      outgoingLight = mix(outgoingLight, uPoolStoneWet * .62, seamContact * .26);
    `;
    const shelfDamp = /* glsl */`
      float atWater = 1.0 - smoothstep(.004, .027, abs(poolY - uPoolStoneLevels.y));
      outgoingLight = mix(outgoingLight, uPoolStoneWet, .09 + .23 * atWater);
    `;
    const finish = /* glsl */`
      vec2 poolDelta = vArtWorldPosition.xz - uPoolStoneOrigin.xy;
      vec2 poolP = vec2(uPoolStoneOrigin.z * poolDelta.x - uPoolStoneOrigin.w * poolDelta.y,
                       uPoolStoneOrigin.w * poolDelta.x + uPoolStoneOrigin.z * poolDelta.y);
      vec2 poolN = vec2(uPoolStoneOrigin.z * worldNormal.x - uPoolStoneOrigin.w * worldNormal.z,
                       uPoolStoneOrigin.w * worldNormal.x + uPoolStoneOrigin.z * worldNormal.z);
      float poolY = vArtWorldPosition.y - uPoolStoneLevels.x;
      float side = 1.0 - smoothstep(.35, .85, worldNormal.y);
      float innerFace = 1.0 - smoothstep(-.08, .05, dot(poolN, poolP));
      float pedestal = 1.0 - smoothstep(.44, .58, max(abs(poolP.x), abs(poolP.y)));
      float wetNoise = artNoise(poolP * 13.0 + vec2(5.4, 8.1));
      float wetLine = 1.0 - smoothstep(uPoolStoneLevels.y + .018, uPoolStoneLevels.y + .065 + wetNoise * .025, poolY);
      float wet = wetLine * side * max(innerFace, pedestal);
      outgoingLight = mix(outgoingLight, mix(outgoingLight * .73, uPoolStoneWet, .22), wet * .72);
      ${wetDetail ? dampBand : ''}
      ${shelf ? shelfDamp : ''}
      float contact = (1.0 - smoothstep(.005, .062 + .012 * wetNoise, poolY)) * side;
      outgoingLight *= mix(vec3(1.0), vec3(.76, .82, .68), contact);
      float capStep = (1.0 - smoothstep(.004, .018, abs(poolY - .44))) * side;
      outgoingLight *= 1.0 - capStep * .10;
      float chips = max(1.0 - smoothstep(.08, .28, length(poolP - vec2(.935, -2.259))),
                        1.0 - smoothstep(.08, .28, length(poolP + vec2(.935, -2.259))));
      float weather = chips * smoothstep(.48, .72, wetNoise) * smoothstep(.48, .56, poolY);
      outgoingLight = mix(outgoingLight, uPoolStoneOld, weather * .35);
    `;
    const anchor = 'outgoingLight *= 1.0 + vArtStoneTint * uArtStoneVariation;';
    if (!shader.fragmentShader.includes(anchor)) throw new Error('Pool stone extension anchor changed.');
    shader.fragmentShader = shader.fragmentShader.replace('void main() {', `${declarations}\nvoid main() {`).replace(anchor, `${anchor}\n${finish}`);
  };
  return material;
}
