#define LAMBERT
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float opacity;
#include <common>

  uniform float uCloudDrift;
  uniform float uCloudActive;
  float cloudSoftMin(float a, float b) {
    float h = max(0.2400000000 - abs(a - b), 0.0) / 0.2400000000;
    return min(a, b) - h * h * 0.0600000000;
  }
  float cloudPatch(vec2 point, vec2 center, vec2 radius) {
    vec2 q = point - center;
    q.x -= 32.0000000000 * floor(q.x / 32.0000000000 + .5);
    q /= radius;
    vec2 b = (q - vec2(.48, -.16)) * vec2(1.3, 1.18);
    vec2 c = (q + vec2(.44, -.22)) * vec2(1.15, 1.38);
    float d = cloudSoftMin(cloudSoftMin(dot(q, q), dot(b, b)), dot(c, c));
    float aa = min(fwidth(d) * .35, .10);
    return 1.0 - smoothstep(0.4600000000 - aa, 1.3000000000 + aa, d);
  }
  float cloudCoverage(vec3 world) {
    vec2 projected = world.xz - world.y * vec2(0.7727272727,-0.0909090909);
    const vec2 direction = vec2(0.9524241472,0.3047757271);
    vec2 point = vec2(dot(projected, direction) - uCloudDrift,
                      dot(projected, vec2(-direction.y, direction.x)));
    float c0 = cloudPatch(point, vec2(-3.0000000000,-1.4000000000), vec2(4.6000000000,3.3000000000)) * 1.0000000000;
float c1 = cloudPatch(point, vec2(12.0000000000,4.6000000000), vec2(5.6000000000,3.7000000000)) * 0.8800000000;
    return 1.0 - (1.0 - c0) * (1.0 - c1);
  }


      varying vec3 vArtWorldPosition;
      
      
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
      uniform vec4 uArtTreePatches[3];
      uniform float uArtTreeRotations[3];

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
        for (int i = 0; i < 3; i++) {
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
    
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <envmap_physical_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_lambert_pars_fragment>
#include <shadowmap_pars_fragment>
#include <shadowmask_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>

      uniform float uPoolTime;
      uniform vec4 uPoolImpacts[8];
      uniform vec4 uPoolOrigin; uniform vec4 uPoolMotion; uniform vec4 uPoolBoundary;
      uniform vec3 uPoolShallow; uniform vec3 uPoolBase; uniform vec3 uPoolMiddle;
      uniform vec3 uPoolDeep; uniform vec3 uPoolShade; uniform vec3 uPoolWhite;
    
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <specularmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_lambert_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + totalEmissiveRadiance;
	#include <envmap_fragment>
	
        
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
      for (int i = 0; i < 8; i++) {
        vec4 event = uPoolImpacts[i];
        float radius = .025 + event.z * 0.30;
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
    
      

    // CLOUD_SHADOW_FINISH: shared world field after the original material finish.
    float cloudLuminance = dot(outgoingLight, vec3(.2126, .7152, .0722));
    float cloudMask = cloudCoverage(vArtWorldPosition);
    float cloudAmount = cloudMask * 0.0750000000 * (mix(.12, 1.0, getShadowMask()) * mix(.10, 1.0, smoothstep(.015, .32, cloudLuminance))) * mix(1.0, .30, smoothstep(.50, .90, cloudLuminance)) * uCloudActive;
    outgoingLight *= vec3(1.0) - cloudAmount * vec3(1.0, .96, .85);
    #include <opaque_fragment>
  
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}