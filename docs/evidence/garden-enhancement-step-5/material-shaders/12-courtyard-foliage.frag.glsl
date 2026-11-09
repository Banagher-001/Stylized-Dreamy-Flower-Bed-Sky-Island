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
    // Evaluate derivatives before the coherent empty-space branch. The cloud
    // is already fully clear outside these bounds, including the wrap seam.
    float aa = min(max(fwidth(q.x), fwidth(q.y)) * .75, .10);
    if (abs(q.x) > 1.8 || abs(q.y) > 1.6) return 0.0;
    vec2 b = (q - vec2(.48, -.16)) * vec2(1.3, 1.18);
    vec2 c = (q + vec2(.44, -.22)) * vec2(1.15, 1.38);
    float d = cloudSoftMin(cloudSoftMin(dot(q, q), dot(b, b)), dot(c, c));
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


  uniform float uEnvironmentTime;
  uniform float uEnvironmentCanopy;
  float environmentCanopyWave(vec2 p) {
    float gust = 0.68 + 0.32 * sin(6.28318530718 * uEnvironmentTime / 16.0000000000 + dot(p, vec2(0.06, 0.04)));
    return uEnvironmentCanopy * gust * (
      0.76 * sin(6.28318530718 * uEnvironmentTime / 10.5000000000 + dot(p, vec2(0.35, 0.11)))
      + 0.24 * sin(6.28318530718 * uEnvironmentTime / 12.0000000000 + dot(p, vec2(-0.12, 0.42))));
  }


      varying vec3 vArtWorldPosition;
      
      varying float vArtPlantPart; varying float vArtPlantHeight;
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
      float environmentWave = environmentCanopyWave(position);
        float distanceToCanopy = 10.0;
        for (int i = 0; i < 3; i++) {
          vec4 canopyBounds = uArtTreePatches[i];
          float c = cos(uArtTreeRotations[i]);
          float s = sin(uArtTreeRotations[i]);
          vec2 local = mat2(c, -s, s, c) * (position - canopyBounds.xy);
          float d = length(local / canopyBounds.zw);
          d += (artNoise(position * uArtTreeNoiseScale) - 0.5) * uArtTreeNoiseAmount;
          
      float edgeBand = smoothstep(0.84, 0.94, d) * (1.0 - smoothstep(1.14, 1.24, d));
      float distanceGradient = length(local / (canopyBounds.zw * canopyBounds.zw)) / max(length(local / canopyBounds.zw), 0.001);
      d += environmentWave * 0.0450000000 * distanceGradient * edgeBand;
      distanceToCanopy = min(distanceToCanopy, d);
        }
        float silhouette = 1.0 - smoothstep(1.0 - uArtTreeSoftness, 1.0 + uArtTreeSoftness, distanceToCanopy);
        if (uArtTreeDetailEnabled < 0.5) return silhouette * uArtTreesEnabled;
        float branches = artNoise(position * uArtTreeDetail.x + vec2(8.3, 3.7));
        float leaves = artHash(floor(position * uArtTreeDetail.y));
        float brokenDistance = distanceToCanopy + (branches - 0.5) * uArtTreeDetail.z + (leaves - 0.5) * 0.06;
        float body = 1.0 - smoothstep(1.0 - uArtTreeSoftness, 1.0 + uArtTreeSoftness, brokenDistance);
        float holes = step(0.74, branches) * step(0.68, artNoise(position * 8.5));
       holes *= 1.0 - uEnvironmentCanopy * 0.0250000000 * (0.5 + 0.5 * environmentWave);
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
void main() {
float cloudSceneShadow = getShadowMask();
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
	
        float plantOcclusion = max(1.0 - cloudSceneShadow, artCanopy(vArtWorldPosition.xz));
        vec3 litPlant = diffuseColor.rgb * mix(0.93, 1.0, clamp(vArtPlantHeight, 0.0, 1.0));
        outgoingLight = mix(litPlant, uArtPlantShade, plantOcclusion);
      

    // CLOUD_SHADOW_FINISH: shared world field after the original material finish.
    float cloudLuminance = dot(outgoingLight, vec3(.2126, .7152, .0722));
    float cloudMask = cloudCoverage(vArtWorldPosition);
    float cloudAmount = cloudMask * 0.1300000000 * (mix(.10, 1.0, 1.0 - plantOcclusion)) * uCloudActive;
    outgoingLight *= vec3(1.0) - cloudAmount * vec3(1.0, .96, .85);
    #include <opaque_fragment>
  
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}