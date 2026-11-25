import { Color, Vector2, Vector3, Vector4 } from 'three';
import { createArtMaterial } from './createArtMaterial';
import type { WaterState } from './createWaterMaterial';
import { layoutConfig } from '../config/layout';
import { waterConfig } from '../config/water';
import { fountainConfig as config, fountainShelf } from '../config/fountain';
import { poolEdges } from '../config/poolMasonry';
import { windDirection } from '../animation/environmentMotion';
import { poolCloudReflectionGLSL } from './poolCloudReflection';
import { poolShoreFoamGLSL } from './poolShoreFoam';

/** Opaque, world-attached artwork: one existing surface, original shadow/depth path. */
export function createRefinedWaterMaterial(state: WaterState) {
  const material = createArtMaterial('water');
  material.name = 'courtyard-water-refined-surface';material.userData.waterKind = 'refined-surface';
  material.customProgramCacheKey = () => 'courtyard-water-refined-surface-v8';
  const baseCompile = material.onBeforeCompile.bind(material);
  material.onBeforeCompile = (shader, renderer) => {
    baseCompile(shader, renderer);
    const f = layoutConfig.fountain;
    const impact = config.impact;
    const optics = config.waterOptics;
    const clouds = config.cloudReflection;
    const foam = config.shoreFoam;
    const ripples = config.windRipples;
    const foamNormals = foam.patches.map(({ edge }) => {
      const angle = (poolEdges[edge - 1].side + .5) * Math.PI / 4;
      return new Vector2(Math.cos(angle), -Math.sin(angle));
    });
    const shelves = fountainShelf.stones.map(({ span, reach, bankY, lipY, fall, cut }) => {
      const start = span[0] * fountainShelf.edgeLength;
      const end = span[1] * fountainShelf.edgeLength;
      return {
        bounds: new Vector4(start, end, reach, bankY),
        cut: new Vector4(...cut),
        grade: new Vector2(fall / (end - start), (lipY - bankY) / reach),
      };
    });
    Object.assign(shader.uniforms, {
      uPoolTime: state.time, uPoolImpacts: state.impacts,
      uPoolOrigin: { value: new Vector4(f.position[0], f.position[2], Math.cos(f.rotationY), Math.sin(f.rotationY)) },
      uPoolColorDrift: { value: config.flowSpeed },
      uPoolWind: { value: new Vector2(...windDirection) },
      uPoolWindRippleShape: { value: new Vector4(ripples.wavelength, ripples.speed, ripples.halfWidth, ripples.strength) },
      uPoolWindRippleLight: { value: new Color(ripples.light) },
      uPoolBoundary: { value: new Vector4(f.innerRadius * Math.cos(Math.PI / 8), ...config.edgeGlintWidth, waterConfig.ripples.lifetime) },
      uPoolClearRadius: { value: new Vector2(...config.clearWaterRadius) },
      uPoolDropFocus: { value: new Vector2(...config.dropFocus) },
      uPoolRippleTiming: { value: new Vector2(impact.contactDuration, impact.secondaryDelay) },
      uPoolRippleShape: { value: new Vector4(impact.startRadius, impact.contactRadius, impact.primaryHalfWidth, impact.secondaryHalfWidth) },
      uPoolRippleGain: { value: new Vector3(impact.strength.contact, impact.strength.primary, impact.strength.secondary) },
      uPoolImpactLight: { value: new Color(config.colors.impactLight) },
      uPoolShelfFrame: { value: new Vector4(...fountainShelf.origin, ...fountainShelf.tangent) },
      uPoolShelfPieces: { value: shelves.map(({ bounds }) => bounds) },
      uPoolShelfCuts: { value: shelves.map(({ cut }) => cut) },
      uPoolShelfGrades: { value: shelves.map(({ grade }) => grade) },
      uPoolLevels: { value: new Vector3(f.waterHeight, f.baseHeight, fountainShelf.bedInset) },
      uPoolOptics: { value: new Vector3(1 / optics.refractiveIndex, optics.normalTilt, optics.absorption) },
      uPoolCloudMotion: { value: new Vector4(clouds.heightAboveWater, clouds.driftSpeed, clouds.repeatDistance, clouds.waveInfluence) },
      uPoolRearCloud: { value: new Vector2(...clouds.rearCenter) },
      uPoolNearCloud: { value: new Vector2(...clouds.nearCenter) },
      uPoolCloudBody: { value: new Color(clouds.body) },
      uPoolCloudEdge: { value: new Color(clouds.edge) },
      uPoolFoamNormals: { value: foamNormals },
      uPoolFoamBands: { value: foam.patches.map(({ span, contact, reach }) => new Vector4(...span, contact, reach)) },
      uPoolFoamPatterns: { value: foam.patches.map(({ seed, opacity, fragments }) => new Vector3(seed, opacity, fragments)) },
      uPoolFoamWhite: { value: new Color(foam.white) },
      uPoolFoamShade: { value: new Color(foam.shade) },
      uPoolShelfWater: { value: new Color(config.colors.shelfWater) },
      uPoolSubmergedLip: { value: new Color(config.colors.submergedLip) },
      uPoolShallow: { value: new Color(config.colors.shallow) }, uPoolBase: { value: new Color(config.colors.base) },
      uPoolMiddle: { value: new Color(config.colors.middle) }, uPoolDeep: { value: new Color(config.colors.deep) },
      uPoolShade: { value: new Color(config.colors.shade) }, uPoolWhite: { value: new Color(config.colors.white) },
    });
    const declarations = /* glsl */`
      uniform float uPoolTime;
      uniform vec4 uPoolImpacts[${waterConfig.ripples.capacity}];
      uniform vec4 uPoolOrigin; uniform vec4 uPoolBoundary;
      uniform float uPoolColorDrift;
      uniform vec2 uPoolWind;
      // Wavelength, travel speed, half width, and highlight strength.
      uniform vec4 uPoolWindRippleShape;
      uniform vec3 uPoolWindRippleLight;
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
      uniform vec2 uPoolShelfGrades[${fountainShelf.stones.length}];
      uniform vec3 uPoolLevels;
      uniform vec3 uPoolOptics;
      uniform vec3 uPoolShelfWater;
      uniform vec3 uPoolSubmergedLip;
      uniform vec3 uPoolShallow; uniform vec3 uPoolBase; uniform vec3 uPoolMiddle;
      uniform vec3 uPoolDeep; uniform vec3 uPoolShade; uniform vec3 uPoolWhite;

      vec2 poolLocalXZ(vec2 direction) {
        return vec2(uPoolOrigin.z * direction.x - uPoolOrigin.w * direction.y,
                    uPoolOrigin.w * direction.x + uPoolOrigin.z * direction.y);
      }

      ${poolCloudReflectionGLSL}
      ${poolShoreFoamGLSL}

      float shelfLipAt(float along, vec4 piece, vec4 cut) {
        float startCut = cut.y * (1.0 - clamp((along - piece.x) / cut.x, 0.0, 1.0));
        float endCut = cut.w * (1.0 - clamp((piece.y - along) / cut.z, 0.0, 1.0));
        return piece.z - startCut - endCut;
      }

      float shelfTopAt(vec2 bank, vec4 piece, vec2 grade) {
        return piece.w + dot(grade, vec2(bank.x - (piece.x + piece.y) * .5, bank.y));
      }

      vec3 shelfWaterBands(vec2 bank, vec4 piece, vec4 cut, vec2 grade, float aa) {
        float spanFade = smoothstep(piece.x - .13, piece.x + .047, bank.x)
          * (1.0 - smoothstep(piece.y - .047, piece.y + .13, bank.x));
        float lip = shelfLipAt(bank.x, piece, cut);
        float shallows = (1.0 - smoothstep(lip + .014, lip + .29, bank.y)) * spanFade;
        float slope = max(-grade.y, .001);
        float fromEntry = (uPoolLevels.x - shelfTopAt(bank, piece, grade)) / slope;
        float wetLip = (uPoolLevels.x - shelfTopAt(vec2(bank.x, lip), piece, grade)) / slope;
        float entrySpan = smoothstep(piece.x, piece.x + cut.x * .67, bank.x)
          * (1.0 - smoothstep(piece.y - cut.z * .67, piece.y, bank.x));
        float contact = smoothstep(-aa * .24, .007, fromEntry)
          * (1.0 - smoothstep(.009, .029 + aa * .28, fromEntry))
          * smoothstep(-aa * .25, .013, wetLip) * entrySpan;
        float crest = .035 + .007 * sin(uPoolTime * 1.68 + bank.x * 12.0 + piece.x * 7.5);
        float patches = artNoise(vec2(bank.x * 17.5, 1.37 + piece.x * 4.0));
        float foam = smoothstep(-aa * .2, .006, fromEntry)
          * (1.0 - smoothstep(crest * .45, crest + aa * .24, fromEntry))
          * (1.0 - smoothstep(wetLip - .008, wetLip + .006, fromEntry))
          * smoothstep(.006, .024, wetLip) * entrySpan
          * (.34 + .61 * smoothstep(.24, .72, patches));
        return vec3(shallows, contact, foam);
      }

      // The top plane and cut outline use the same grades and dimensions as the stone meshes.
      vec3 submergedShelf(vec2 bank, vec3 ray, vec4 piece, vec4 cut, vec2 grade, float bedPath, float aa) {
        float descent = dot(grade, ray.xz) - ray.y;
        if (descent <= .001) return vec3(bedPath, 0.0, 0.0);
        float path = (uPoolLevels.x - shelfTopAt(bank, piece, grade)) / descent;
        if (path < 0.0 || path >= bedPath) return vec3(bedPath, 0.0, 0.0);

        vec2 hit = bank + ray.xz * path;
        float lip = shelfLipAt(hit.x, piece, cut);
        float alongEdge = min(hit.x - piece.x, piece.y - hit.x);
        float frontEdge = lip - hit.y;
        float inset = min(min(alongEdge, frontEdge), hit.y + uPoolLevels.z);
        float soften = clamp(aa * .42, .002, .009);
        float face = smoothstep(-soften, soften, inset);
        float front = face * (1.0 - smoothstep(.004, .028 + soften, frontEdge));
        return vec3(path, face, front);
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

      float windRippleLight(vec2 p, vec2 wind, vec3 normal, vec3 incident) {
        vec2 axes = vec2(dot(p, wind), dot(p, vec2(-wind.y, wind.x)));
        float travel = axes.x - uPoolTime * uPoolWindRippleShape.y;
        float curve = .055 * sin(axes.y * 4.25 + axes.x * .76)
          + .027 * sin(axes.y * 2.1 - axes.x * 3.4)
          + (artNoise(axes * vec2(1.6, 3.2) + vec2(8.2, 1.8)) - .5) * .035;
        float wavelength = uPoolWindRippleShape.x;
        float phase = travel + curve;
        float footprint = max(fwidth(phase), .003);
        float halfWidth = uPoolWindRippleShape.z;
        float distanceToCrest = abs(fract(phase / wavelength + .5) - .5) * wavelength;
        float crest = rippleBand(distanceToCrest, 0.0, halfWidth, footprint);
        // Widen the sample band and lower its intensity as it becomes subpixel.
        float coverage = halfWidth / (halfWidth + footprint * .36);
        float resolved = 1.0 - smoothstep(halfWidth * 2.2, halfWidth * 6.1, footprint);

        float breakup = artNoise(vec2(travel * 7.8, axes.y * 7.4) + vec2(3.2, 1.9));
        float groups = artNoise(axes * vec2(2.1, 2.7) + vec2(2.5, 9.0));
        float streaks = smoothstep(.49, .78, breakup) * mix(.25, 1.0, smoothstep(.25, .74, groups));
        vec2 sliding = vec2(travel * 11.4, (axes.y - uPoolTime * .085) * 7.4);
        float glint = smoothstep(.38, .81, artNoise(sliding + vec2(8.3, 3.1)));
        float facing = .72 + .28 * smoothstep(.35, .88, dot(-incident, normal));
        float slope = .74 + .26 * smoothstep(-.016, .014, dot(normal.xz, wind));
        return crest * coverage * mix(.58, 1.0, resolved) * streaks
          * mix(.35, 1.0, glint) * facing * slope * uPoolWindRippleShape.w;
      }

      // Light from the contact and rings, followed by their local influence on the wind ripples.
      vec2 samplePoolImpact(vec2 p, vec4 event, float aa) {
        float age = event.z;
        float lifetime = uPoolBoundary.w;
        if (event.w <= 0.0 || age < 0.0 || age >= lifetime) return vec2(0.0);

        vec2 offset = p - event.xy;
        float distanceToCenter = length(offset);
        float speed = ${waterConfig.ripples.speed.toFixed(2)};
        float radius = uPoolRippleShape.x + age * speed;
        float quietEnd = radius + .19;
        if (distanceToCenter > quietEnd) return vec2(0.0);
        float quiet = (1.0 - smoothstep(radius + .045, quietEnd, distanceToCenter))
          * smoothstep(0.0, .032, age) * (1.0 - smoothstep(.25, lifetime, age)) * event.w;
        float contactReach = uPoolRippleShape.y + aa * .35;
        float ringReach = radius + .004 + max(uPoolRippleShape.z, uPoolRippleShape.w) + aa * .55;
        if (distanceToCenter > max(contactReach, ringReach)) return vec2(0.0, quiet);

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
        return vec2(min(.92, max(contact, max(primary, trailing)) * event.w), quiet);
      }
    `;
    const response = /* glsl */`
      vec2 delta = vArtWorldPosition.xz - uPoolOrigin.xy;
      vec2 p = poolLocalXZ(delta);
      float t = uPoolTime;
      vec2 drift = vec2(t, -t * .25) * uPoolColorDrift;
      float broad = artNoise(p * vec2(2.2, 1.6) + drift * .5 + vec2(3.7, 6.1));
      float aa = clamp(max(fwidth(p.x), fwidth(p.y)), .003, .12);
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
      vec2 shelfInward = vec2(shelfTangent.y, -shelfTangent.x);
      vec2 bank = vec2(dot(shelfDelta, shelfTangent), dot(shelfDelta, shelfInward));
      vec3 incoming = isOrthographic ? transformDirectionByInverseViewMatrix(vec3(0.0, 0.0, -1.0), viewMatrix)
        : normalize(vArtWorldPosition - cameraPosition);
      vec2 incidentXZ = poolLocalXZ(incoming.xz);
      vec3 localIncident = vec3(incidentXZ.x, incoming.y, incidentXZ.y);
      vec2 waterTilt = sin(vec2(dot(p, vec2(4.1, 5.3)), dot(p, vec2(-6.0, 2.5))) + vec2(t * .72, -t * .61))
        * uPoolOptics.y;
      vec3 waterNormal = normalize(vec3(waterTilt.x, 1.0, waterTilt.y));
      vec3 belowWater = refract(localIncident, waterNormal, uPoolOptics.x);
      float bedPath = (uPoolLevels.x - uPoolLevels.y) / max(-belowWater.y, .2);
      vec3 bankRay = vec3(dot(belowWater.xz, shelfTangent), belowWater.y, dot(belowWater.xz, shelfInward));
      vec3 shelf = vec3(0.0);
      vec3 nearestStone = vec3(bedPath, 0.0, 0.0);
      for (int i = 0; i < ${fountainShelf.stones.length}; i++) {
        vec4 piece = uPoolShelfPieces[i];
        vec4 cut = uPoolShelfCuts[i];
        vec2 grade = uPoolShelfGrades[i];
        shelf = max(shelf, shelfWaterBands(bank, piece, cut, grade, aa));
        vec3 hit = submergedShelf(bank, bankRay, piece, cut, grade, bedPath, aa);
        if (hit.y > 0.0 && hit.x < nearestStone.x) nearestStone = hit;
      }
      float nearBank = 1.0 - smoothstep(.025, .27, shoreDistance + (broad - .5) * .047);
      float depth = (1.0 - exp(-bedPath * uPoolOptics.z)) * mix(.07, .46, smoothstep(.24, 1.43, shoreDistance));
      vec3 clearWater = mix(uPoolBase, uPoolMiddle, depth);
      clearWater = mix(clearWater, uPoolShallow, max(nearBank * .24, shelf.x * .82));
      vec3 submergedTone = mix(clearWater, uPoolShelfWater, exp(-nearestStone.x * uPoolOptics.z * 2.4));
      clearWater = mix(clearWater, submergedTone, nearestStone.y * .78);
      clearWater = mix(clearWater, uPoolSubmergedLip, nearestStone.z * .37);
      clearWater *= .985 + (broad - .5) * .054;
      float reflectedShade = reflection * smoothstep(.17, .94, reflection);
      vec3 litWater = mix(clearWater, uPoolDeep, reflectedShade * .86);

      vec2 localWind = poolLocalXZ(uPoolWind);
      float dropZone = 1.0 - smoothstep(.19, .45, length(p - uPoolDropFocus));
      vec4 clouds = samplePoolClouds(p, localIncident, waterTilt, localWind, aa);
      float clearMargin = smoothstep(.16, .31, shoreDistance) * (1.0 - dropZone * .98)
        * (1.0 - max(shelf.x, nearestStone.y) * .92);
      float viewResponse = .91 + .16 * smoothstep(.08, .48, 1.0 + localIncident.y);
      vec2 cloudOpacity = clouds.xy * vec2(.90, .68) * clearMargin * viewResponse
        * (1.0 - reflectedShade * .68);
      float cloudLight = max(cloudOpacity.x, cloudOpacity.y);
      float cloudBody = cloudOpacity.x >= cloudOpacity.y ? clouds.z : clouds.w;
      vec3 reflectedCloud = mix(uPoolCloudEdge, uPoolCloudBody, cloudBody);
      litWater = mix(litWater, reflectedCloud, cloudLight);

      float litBack = bankGlint(p, vec2(.382683, -.923880), vec2(-.19, .41), .075, .48, aa);
      float litCorner = bankGlint(p, vec2(.923880, .382683), vec2(-.39, .06), .174, 2.94, aa);
      float shelfArc = smoothstep(.29, .54, artNoise(vec2(bank.x * 14.5, 3.7)));
      float shelfPulse = .74 + .26 * sin(t * .79 - bank.x * 7.1);
      float shelfLight = shelf.y * shelfArc * shelfPulse;
      float shoreLight = max(max(litBack, litCorner) * .60, shelfLight * .34);
      float foam = max(samplePoolShoreFoam(p, shoreDistance, aa), shelf.z);
      float glintRemaining = 1.0 - smoothstep(.06, .64, foam) * .66;

      vec2 impactSample = vec2(0.0);
      for (int i = 0; i < ${waterConfig.ripples.capacity}; i++) {
        impactSample = max(impactSample, samplePoolImpact(p, uPoolImpacts[i], aa));
      }
      float impacts = impactSample.x * smoothstep(.012, .095, shoreDistance) * mix(1.0, .48, reflection);
      float openWater = smoothstep(.22, .46, shoreDistance) * (1.0 - max(shelf.x, nearestStone.y) * .87);
      float cloudResponse = 1.0 - smoothstep(.045, .40, cloudLight) * .94;
      float windLight = windRippleLight(p, localWind, waterNormal, localIncident) * openWater * cloudResponse
        * (1.0 - .76 * dropZone) * (1.0 - .62 * impactSample.y) * (1.0 - .65 * reflectedShade);
      float shoreWhite = shoreLight * .83 * glintRemaining;
      litWater = mix(litWater, uPoolWhite, shoreWhite);
      litWater = mix(litWater, uPoolWindRippleLight, windLight);
      litWater = mix(litWater, uPoolFoamWhite, foam * (.91 - .30 * reflectedShade));
      litWater = mix(litWater, uPoolImpactLight, impacts);
      vec3 shadedWater = mix(uPoolShade, clearWater, .24 + shelf.x * .43);
      shadedWater = mix(shadedWater, uPoolDeep * .88, reflectedShade * .65);
      shadedWater = mix(shadedWater, mix(uPoolCloudEdge, uPoolShade, .22), cloudLight * .65);
      shadedWater = mix(shadedWater, uPoolWhite, shoreWhite * .13 + shelfLight * .08 * glintRemaining);
      shadedWater = mix(shadedWater, uPoolWindRippleLight, windLight * .30);
      shadedWater = mix(shadedWater, uPoolFoamShade, foam * (.62 - .22 * reflectedShade));
      shadedWater = mix(shadedWater, uPoolImpactLight, impacts * .45);
      outgoingLight = mix(shadedWater, litWater, getShadowMask());
    `;
    const anchor = 'outgoingLight = mix(uArtWaterShade, uArtWater, getShadowMask());';
    if (!shader.fragmentShader.includes(anchor)) throw new Error('Pool surface extension anchor changed.');
    shader.fragmentShader = shader.fragmentShader.replace('void main() {', `${declarations}\nvoid main() {`).replace(anchor, response);
  };
  return material;
}
