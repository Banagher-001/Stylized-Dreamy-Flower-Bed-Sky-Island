import { fountainConfig } from '../config/fountain';

/** Foam coverage on the existing pool surface, in bank coordinates. */
export const poolShoreFoamGLSL = /* glsl */`
  uniform vec2 uPoolFoamNormals[${fountainConfig.shoreFoam.patches.length}];
  uniform vec4 uPoolFoamBands[${fountainConfig.shoreFoam.patches.length}];
  uniform vec3 uPoolFoamPatterns[${fountainConfig.shoreFoam.patches.length}];
  uniform vec3 uPoolFoamWhite;
  uniform vec3 uPoolFoamShade;

  float driftingFoamGrains(vec2 bank, float wave, float seed, float aa) {
    vec2 grid = vec2(bank.x, bank.y - wave * .62) * vec2(13.0, 32.0) + vec2(seed, 2.7);
    vec2 cell = floor(grid);
    float random = artHash(cell + 8.6);
    vec2 center = .25 + .5 * vec2(artHash(cell + 3.3), artHash(cell + 16.9));
    float radius = mix(.105, .21, artHash(cell + 4.8));
    float distanceToCenter = length(fract(grid) - center);
    float edge = radius + clamp(aa * 5.5, .035, .13);
    return smoothstep(.56, .76, random) * (1.0 - smoothstep(radius * .46, edge, distanceToCenter));
  }

  // The core tapers along the wall, with an uneven crest on the water side.
  float foamBand(vec2 bank, vec4 band, vec3 pattern, float aa) {
    float along = bank.x, across = bank.y;
    float seed = pattern.x;
    float taper = smoothstep(band.x - .045, band.x + .135, along)
      * (1.0 - smoothstep(band.y - .125, band.y + .035, along));
    float coarse = artNoise(vec2(along * 12.0 + seed * 3.0, 1.8));
    float grain = artNoise(vec2(along * 17.0 + seed, across * 55.0 + 4.3));
    float wave = .010 * sin(uPoolTime * 1.54 + along * 7.2 + seed)
      + .003 * sin(uPoolTime * 2.09 - along * 8.0 - seed);
    float reach = mix(band.z + .034, band.w, smoothstep(.12, .74, coarse))
      + (grain - .47) * .018 + wave;
    float contact = smoothstep(band.z - .018, band.z + .009, across);
    float crest = 1.0 - smoothstep(reach - .015, reach + .008 + aa * .26, across);
    float holes = smoothstep(.66, .94, grain) * smoothstep(reach - .042, reach + .001, across);
    float foam = contact * crest * (1.0 - holes * .82) * pattern.y;

    if (pattern.z > 0.0 && across > reach - .003 && across < reach + .052) {
      float fringe = smoothstep(reach - .003, reach + .016, across)
        * (1.0 - smoothstep(reach + .036, reach + .052, across));
      float grains = driftingFoamGrains(bank, wave, seed, aa);
      foam = max(foam, grains * fringe * pattern.z);
    }
    return foam * taper;
  }

  float samplePoolShoreFoam(vec2 p, float shoreDistance, float aa) {
    if (shoreDistance > .34) return 0.0;
    float foam = 0.0;
    for (int i = 0; i < ${fountainConfig.shoreFoam.patches.length}; i++) {
      vec2 normal = uPoolFoamNormals[i];
      vec2 bank = vec2(dot(p, vec2(normal.y, -normal.x)), uPoolBoundary.x - dot(p, normal));
      vec4 band = uPoolFoamBands[i];
      if (bank.x < band.x - .045 || bank.x > band.y + .035 || bank.y > band.w + .078) continue;
      foam = max(foam, foamBand(bank, band, uPoolFoamPatterns[i], aa));
    }
    return foam;
  }
`;
