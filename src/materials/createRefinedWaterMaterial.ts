import { Color, Vector2, Vector3, Vector4 } from 'three';
import { createArtMaterial } from './createArtMaterial';
import type { WaterState } from './createWaterMaterial';
import { layoutConfig } from '../config/layout';
import { waterConfig } from '../config/water';
import { fountainConfig as config, fountainShelf } from '../config/fountain';

/** Opaque, world-attached artwork: one existing surface, original shadow/depth path. */
export function createRefinedWaterMaterial(state: WaterState) {
  const material = createArtMaterial('water');
  material.name = 'courtyard-water-refined-surface';material.userData.waterKind = 'refined-surface';
  material.customProgramCacheKey = () => 'courtyard-water-refined-surface-v3';
  const baseCompile = material.onBeforeCompile.bind(material);
  material.onBeforeCompile = (shader, renderer) => {
    baseCompile(shader, renderer);
    const f = layoutConfig.fountain;
    const impact = config.impact;
    Object.assign(shader.uniforms, {
      uPoolTime: state.time, uPoolImpacts: state.impacts,
      uPoolOrigin: { value: new Vector4(f.position[0], f.position[2], Math.cos(f.rotationY), Math.sin(f.rotationY)) },
      uPoolMotion: { value: new Vector3(config.flowSpeed, config.waveSpeed, config.waveStrength) },
      uPoolBoundary: { value: new Vector4(f.innerRadius * Math.cos(Math.PI / 8), ...config.edgeGlintWidth, waterConfig.ripples.lifetime) },
      uPoolClearRadius: { value: new Vector2(...config.clearWaterRadius) },
      uPoolDropFocus: { value: new Vector2(...config.dropFocus) },
      uPoolRippleTiming: { value: new Vector2(impact.contactDuration, impact.secondaryDelay) },
      uPoolRippleShape: { value: new Vector4(impact.startRadius, impact.contactRadius, impact.primaryHalfWidth, impact.secondaryHalfWidth) },
      uPoolRippleGain: { value: new Vector3(impact.strength.contact, impact.strength.primary, impact.strength.secondary) },
      uPoolImpactLight: { value: new Color(config.colors.impactLight) },
      uPoolShelfFrame: { value: new Vector4(...fountainShelf.origin, ...fountainShelf.tangent) },
      uPoolShelfPieces: { value: fountainShelf.stones.map(({ span, reach, bankY, lipY }) => new Vector4(
        span[0] * fountainShelf.edgeLength, span[1] * fountainShelf.edgeLength, reach,
        reach * (bankY - f.waterHeight) / (bankY - lipY),
      )) },
      uPoolShelfCuts: { value: fountainShelf.stones.map(({ cut }) => new Vector4(...cut)) },
      uPoolShelfRake: { value: fountainShelf.stones.map(({ span, reach, bankY, lipY, fall }) => (
        reach * fall / ((bankY - lipY) * (span[1] - span[0]) * fountainShelf.edgeLength)
      )) },
      uPoolShelfWater: { value: new Color(config.colors.shelfWater) },
      uPoolShallow: { value: new Color(config.colors.shallow) }, uPoolBase: { value: new Color(config.colors.base) },
      uPoolMiddle: { value: new Color(config.colors.middle) }, uPoolDeep: { value: new Color(config.colors.deep) },
      uPoolShade: { value: new Color(config.colors.shade) }, uPoolWhite: { value: new Color(config.colors.white) },
    });
    const declarations = /* glsl */`
      uniform float uPoolTime;
      uniform vec4 uPoolImpacts[${waterConfig.ripples.capacity}];
      uniform vec4 uPoolOrigin; uniform vec3 uPoolMotion; uniform vec4 uPoolBoundary;
      uniform vec2 uPoolClearRadius;
      uniform vec2 uPoolDropFocus;
      // Contact duration and secondary delay.
      uniform vec2 uPoolRippleTiming;
      // Start radius, contact radius, and the two ring half-widths.
      uniform vec4 uPoolRippleShape;
      uniform vec3 uPoolRippleGain;
      uniform vec3 uPoolImpactLight;
      uniform vec4 uPoolShelfFrame;
      uniform vec4 uPoolShelfPieces[${fountainShelf.stones.length}];
      uniform vec4 uPoolShelfCuts[${fountainShelf.stones.length}];
      uniform float uPoolShelfRake[${fountainShelf.stones.length}];
      uniform vec3 uPoolShelfWater;
      uniform vec3 uPoolShallow; uniform vec3 uPoolBase; uniform vec3 uPoolMiddle;
      uniform vec3 uPoolDeep; uniform vec3 uPoolShade; uniform vec3 uPoolWhite;

      vec3 shelfWaterBands(vec2 bank, vec4 piece, vec4 cut, float rake, float aa) {
        float spanFade = smoothstep(piece.x - .13, piece.x + .047, bank.x)
          * (1.0 - smoothstep(piece.y - .047, piece.y + .13, bank.x));
        float startCut = cut.y * (1.0 - clamp((bank.x - piece.x) / cut.x, 0.0, 1.0));
        float endCut = cut.w * (1.0 - clamp((piece.y - bank.x) / cut.z, 0.0, 1.0));
        float lip = piece.z - startCut - endCut;
        float stoneSpan = smoothstep(piece.x - aa * .3, piece.x + aa * .3, bank.x)
          * (1.0 - smoothstep(piece.y - aa * .3, piece.y + aa * .3, bank.x));
        float shallows = (1.0 - smoothstep(lip + .014, lip + .29, bank.y)) * spanFade;
        float entry = piece.w + rake * (bank.x - (piece.x + piece.y) * .5);
        float submergedStone = smoothstep(entry - aa * .25, entry + .026, bank.y)
          * (1.0 - smoothstep(lip - .012, lip + .041, bank.y)) * stoneSpan;
        float fromEntry = bank.y - entry;
        float entrySpan = smoothstep(piece.x, piece.x + cut.x * .67, bank.x)
          * (1.0 - smoothstep(piece.y - cut.z * .67, piece.y, bank.x));
        float contact = smoothstep(-aa * .24, .007, fromEntry)
          * (1.0 - smoothstep(.009, .029 + aa * .28, fromEntry))
          * smoothstep(-aa * .25, .013, lip - entry) * entrySpan;
        return vec3(shallows, submergedStone, contact);
      }

      float reflectedBank(vec2 p, vec2 normal, vec4 profile, float lean, float aa) {
        float along = dot(p, vec2(normal.y, -normal.x));
        float across = uPoolBoundary.x - dot(p, normal);
        float branches = artNoise(vec2(along * 5.1, across * 4.2) + vec2(profile.w, 7.4));
        float endShape = along - across * lean + (branches - .5) * .14;
        float taper = smoothstep(profile.x - .05, profile.x + .29, endShape)
          * (1.0 - smoothstep(profile.y - .35, profile.y + .078, endShape));
        float disturbance = sin(along * 8.7 + uPoolTime * .52 + profile.w) * .029;
        float reach = (profile.z * pow(taper, .64) + (branches - .5) * .29 + disturbance) * smoothstep(.03, .36, taper);
        float edge = 1.0 - smoothstep(reach - .026 - aa * .4, reach + .058 + aa * .45, across);
        float sky = artNoise(vec2(along * 6.7 + profile.w, across * 17.0 - disturbance * 2.0));
        float gaps = smoothstep(.69, .89, sky) * .38;
        return edge * taper * smoothstep(.036, .15, across) * (1.0 - gaps);
      }

      float bankGlint(vec2 p, vec2 normal, vec2 segment, float offset, float phase, float aa) {
        float along = dot(p, vec2(normal.y, -normal.x));
        float across = uPoolBoundary.x - dot(p, normal);
        float lengthMask = smoothstep(segment.x - .036, segment.x + .06, along)
          * (1.0 - smoothstep(segment.y - .05, segment.y + .037, along));
        float widthMask = smoothstep(offset, offset + .013, across)
          * (1.0 - smoothstep(offset + uPoolBoundary.y, offset + uPoolBoundary.z + aa * .21, across));
        float brokenEdge = smoothstep(.29, .71, artNoise(vec2(along * 14.6, across * 3.7 + 4.1)));
        float shimmer = .78 + .22 * sin(uPoolTime * .87 + along * 14.5 + phase);
        return lengthMask * widthMask * brokenEdge * shimmer;
      }

      float rippleBand(float distanceToCenter, float radius, float halfWidth, float aa) {
        float distanceToRing = abs(distanceToCenter - radius);
        return 1.0 - smoothstep(max(halfWidth - aa * .22, halfWidth * .5), halfWidth + aa * .55, distanceToRing);
      }

      float impactLightAt(vec2 p, vec4 event, float aa) {
        float age = event.z;
        float lifetime = uPoolBoundary.w;
        if (event.w <= 0.0 || age < 0.0 || age >= lifetime) return 0.0;

        vec2 offset = p - event.xy;
        float distanceToCenter = length(offset);
        float speed = ${waterConfig.ripples.speed.toFixed(2)};
        float radius = uPoolRippleShape.x + age * speed;
        float contactReach = uPoolRippleShape.y + aa * .35;
        float ringReach = radius + .004 + max(uPoolRippleShape.z, uPoolRippleShape.w) + aa * .55;
        if (distanceToCenter > max(contactReach, ringReach)) return 0.0;

        float contact = 1.0 - smoothstep(uPoolRippleShape.y * .27, contactReach, distanceToCenter);
        contact *= mix(.45, 1.0, smoothstep(0.0, .016, age))
          * (1.0 - smoothstep(.027, uPoolRippleTiming.x, age)) * uPoolRippleGain.x;

        // Anchor the broken arcs to the landing point, even when the event changes slots.
        vec2 heading = offset / max(distanceToCenter, .002);
        vec2 seed = event.xy * 18.0 + vec2(7.1, 3.3);
        float arcShape = artNoise(heading * vec2(3.1, 4.5) + seed);
        float arcs = mix(.23, 1.0, smoothstep(.31, .63, arcShape));
        float primaryRadius = radius + (arcShape - .5) * .008;
        float primary = rippleBand(distanceToCenter, primaryRadius, uPoolRippleShape.z, aa);
        primary *= smoothstep(.006, .042, age) * (1.0 - smoothstep(.132, lifetime, age))
          * (1.0 - age * .58) * arcs * uPoolRippleGain.y;

        float ageAfterDelay = max(age - uPoolRippleTiming.y, 0.0);
        float trailingRadius = uPoolRippleShape.x + ageAfterDelay * speed * .94;
        float trailingArcs = smoothstep(.28, .65, artNoise(heading * vec2(3.8, 3.0) + seed + vec2(8.3, 2.2)));
        float trailing = rippleBand(distanceToCenter, trailingRadius, uPoolRippleShape.w, aa);
        trailing *= smoothstep(0.0, .041, ageAfterDelay) * (1.0 - smoothstep(.257, .575, age))
          * trailingArcs * uPoolRippleGain.z;
        return min(.92, max(contact, max(primary, trailing)) * event.w);
      }
    `;
    const response = /* glsl */`
      vec2 delta = vArtWorldPosition.xz - uPoolOrigin.xy;
      vec2 p = vec2(uPoolOrigin.z * delta.x - uPoolOrigin.w * delta.y,
                    uPoolOrigin.w * delta.x + uPoolOrigin.z * delta.y);
      float t = uPoolTime;
      vec2 drift = vec2(t, -t * .25) * uPoolMotion.x;
      float broad = artNoise(p * vec2(2.2, 1.6) + drift * .5 + vec2(3.7, 6.1));
      float aa = clamp(max(fwidth(p.x), fwidth(p.y)), .003, .12);
      float detail = 1.0 - smoothstep(.035, .095, aa);
      float centerDistance = length(p);
      float leftReflection = reflectedBank(p, vec2(-.923880, -.382683), vec4(-.93, 1.01, .58, 4.6), -.27, aa);
      float backReflection = reflectedBank(p, vec2(-.382683, -.923880), vec4(-1.03, .99, .75, 12.3), .51, aa);
      float reflection = max(leftReflection, backReflection)
        * smoothstep(uPoolClearRadius.x, uPoolClearRadius.y, centerDistance);

      float shoreDistance = 10.0;
      for (int i = 0; i < 8; i++) {
        float angle = (float(i) + .5) * PI / 4.0;
        shoreDistance = min(shoreDistance, uPoolBoundary.x - dot(p, vec2(cos(angle), -sin(angle))));
      }
      vec2 shelfDelta = p - uPoolShelfFrame.xy;
      vec2 shelfTangent = uPoolShelfFrame.zw;
      vec2 bank = vec2(dot(shelfDelta, shelfTangent), dot(shelfDelta, vec2(shelfTangent.y, -shelfTangent.x)));
      vec3 shelf = vec3(0.0);
      for (int i = 0; i < ${fountainShelf.stones.length}; i++) {
        shelf = max(shelf, shelfWaterBands(bank, uPoolShelfPieces[i], uPoolShelfCuts[i], uPoolShelfRake[i], aa));
      }
      float nearBank = 1.0 - smoothstep(.025, .27, shoreDistance + (broad - .5) * .047);
      float depth = smoothstep(.24, 1.43, shoreDistance) * .32;
      vec3 clearWater = mix(uPoolBase, uPoolMiddle, depth);
      clearWater = mix(clearWater, uPoolShallow, nearBank * .67);
      vec3 shelfTone = mix(uPoolShallow, uPoolShelfWater, shelf.y * .38);
      clearWater = mix(clearWater, shelfTone, shelf.x * .87);
      vec3 litWater = mix(clearWater, uPoolDeep, reflection * .93);

      float wave = smoothstep(.955, .995, sin(centerDistance * 12.0 - t * uPoolMotion.y * 12.0 + broad));
      wave *= smoothstep(.65, .9, centerDistance) * (1.0 - smoothstep(1.5, 1.95, centerDistance));
      wave *= smoothstep(.52, .76, artNoise(p * 7.5 + drift)) * uPoolMotion.z;
      float glint = smoothstep(.78, .94, artNoise(p * 7.0 - drift))
        * smoothstep(.90, .99, sin(p.x * 11.0 + p.y * 6.0 - t * .72 + broad * 3.0)) * .64;
      float dropZone = 1.0 - smoothstep(.19, .45, length(p - uPoolDropFocus));
      float ambientLight = max(wave * mix(1.0, .26, dropZone), glint * mix(1.0, .32, dropZone));
      ambientLight *= mix(.25, 1.0, detail) * mix(1.0, .67, reflection);

      float litBack = bankGlint(p, vec2(.382683, -.923880), vec2(-.19, .41), .075, .48, aa);
      float litCorner = bankGlint(p, vec2(.923880, .382683), vec2(-.39, .06), .174, 2.94, aa);
      float shelfArc = smoothstep(.29, .54, artNoise(vec2(bank.x * 14.5, 3.7)));
      float shelfPulse = .74 + .26 * sin(t * .79 - bank.x * 7.1);
      float shelfLight = shelf.z * shelfArc * shelfPulse;
      float shoreLight = max(max(litBack, litCorner) * .60, shelfLight * .34);

      float impacts = 0.0;
      for (int i = 0; i < ${waterConfig.ripples.capacity}; i++) {
        impacts = max(impacts, impactLightAt(p, uPoolImpacts[i], aa));
      }
      impacts *= smoothstep(.012, .095, shoreDistance) * mix(1.0, .48, reflection);
      float white = max(ambientLight, shoreLight);
      litWater = mix(litWater, uPoolWhite, white);
      litWater = mix(litWater, uPoolImpactLight, impacts);
      vec3 shadedBank = mix(uPoolShade, uPoolShallow * .64, shelf.x * .44);
      vec3 shadedWater = mix(shadedBank, clearWater, .12 + shelf.x * .37 + nearBank * .10);
      shadedWater = mix(shadedWater, uPoolDeep * .84, reflection * .79);
      shadedWater = mix(shadedWater, uPoolWhite, white * .13 + shelfLight * .08);
      shadedWater = mix(shadedWater, uPoolImpactLight, impacts * .45);
      outgoingLight = mix(shadedWater, litWater, getShadowMask());
    `;
    const anchor = 'outgoingLight = mix(uArtWaterShade, uArtWater, getShadowMask());';
    if (!shader.fragmentShader.includes(anchor)) throw new Error('Pool surface extension anchor changed.');
    shader.fragmentShader = shader.fragmentShader.replace('void main() {', `${declarations}\nvoid main() {`).replace(anchor, response);
  };
  return material;
}
