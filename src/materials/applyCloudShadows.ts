import { Mesh } from 'three';
import type { Material, MeshLambertMaterial, Scene, WebGLRenderer } from 'three';
import { cloudShadowConfig as config } from '../config/cloudShadows';
import { cloudDirection, cloudProjection } from '../animation/cloudShadows';
import type { CloudShadowState } from '../animation/cloudShadows';

type Shader = Parameters<MeshLambertMaterial['onBeforeCompile']>[0];
const gl = (n: number) => n.toFixed(10);
const pair = (n: readonly number[]) => `vec2(${n.map(gl).join(',')})`;
const field = /* glsl */`
  uniform float uCloudDrift;
  uniform float uCloudActive;
  float cloudSoftMin(float a, float b) {
    float h = max(${gl(config.unionSoftness)} - abs(a - b), 0.0) / ${gl(config.unionSoftness)};
    return min(a, b) - h * h * ${gl(config.unionSoftness * .25)};
  }
  float cloudPatch(vec2 point, vec2 center, vec2 radius) {
    vec2 q = point - center;
    q.x -= ${gl(config.period)} * floor(q.x / ${gl(config.period)} + .5);
    q /= radius;
    // Evaluate derivatives before the coherent empty-space branch. The cloud
    // is already fully clear outside these bounds, including the wrap seam.
    float aa = min(max(fwidth(q.x), fwidth(q.y)) * .75, .10);
    if (abs(q.x) > 1.8 || abs(q.y) > 1.6) return 0.0;
    vec2 b = (q - vec2(.48, -.16)) * vec2(1.3, 1.18);
    vec2 c = (q + vec2(.44, -.22)) * vec2(1.15, 1.38);
    float d = cloudSoftMin(cloudSoftMin(dot(q, q), dot(b, b)), dot(c, c));
    return 1.0 - smoothstep(${gl(config.softness[0])} - aa, ${gl(config.softness[1])} + aa, d);
  }
  float cloudCoverage(vec3 world) {
    vec2 projected = world.xz - world.y * ${pair(cloudProjection)};
    const vec2 direction = ${pair(cloudDirection)};
    vec2 point = vec2(dot(projected, direction) - uCloudDrift,
                      dot(projected, vec2(-direction.y, direction.x)));
    ${config.patches.map((p, i) => `float c${i} = cloudPatch(point, ${pair([p.along, p.across])}, ${pair(p.radius)}) * ${gl(p.density)};`).join('\n')}
    return 1.0 - (1.0 - c0) * (1.0 - c1);
  }
`;

function extend(shader: Shader, surface: string, strength: number, state: CloudShadowState) {
  const anchor = '#include <opaque_fragment>';
  // All derived pool/orb finishes have run before this wrapper. Prepare both
  // strings before assigning, so a missing anchor leaves the original intact.
  if (!shader.fragmentShader.includes(anchor) || !shader.fragmentShader.includes('void main() {') || !shader.vertexShader.includes('vArtWorldPosition')) throw new Error('Cloud receiver shader anchor unavailable');
  const exposure = surface === 'ground' ? 'mix(.08, 1.0, 1.0 - occlusion)'
    : surface === 'foliage' ? 'mix(.10, 1.0, 1.0 - plantOcclusion)'
    : surface === 'flower' ? 'mix(.10, 1.0, 1.0 - flowerOcclusion)'
    : 'mix(.12, 1.0, cloudSceneShadow) * mix(.10, 1.0, smoothstep(.015, .32, cloudLuminance))';
  const water = surface === 'water' ? ' * mix(1.0, .30, smoothstep(.50, .90, cloudLuminance))' : '';
  const finish = /* glsl */`
    // CLOUD_SHADOW_FINISH: shared world field after the original material finish.
    float cloudLuminance = dot(outgoingLight, vec3(.2126, .7152, .0722));
    float cloudMask = cloudCoverage(vArtWorldPosition);
    float cloudAmount = cloudMask * ${gl(strength)} * (${exposure})${water} * uCloudActive;
    outgoingLight *= vec3(1.0) - cloudAmount * vec3(1.0, .96, .85);
    ${anchor}
  `;
  // Water and stone already evaluate the same static architectural shadow.
  // Reuse it in their original response and in the cloud exposure, so shade
  // does not add a second PCF shadow-map lookup for every covered fragment.
  const cached = shader.fragmentShader.replaceAll('getShadowMask()', 'cloudSceneShadow')
    .replace('void main() {', 'void main() {\nfloat cloudSceneShadow = getShadowMask();');
  const fragment = cached.replace('#include <common>', `#include <common>\n${field}`).replace(anchor, finish);
  shader.uniforms.uCloudDrift = state.drift;shader.uniforms.uCloudActive = state.active;
  shader.fragmentShader = fragment;
}

/** Bind existing art materials after their last specialization, preserving
 * geometry, static shadows, original wind and every GPU/DOM magic inscription.
 * Calling bind again discovers replacement pillar materials without rewrapping.
 */
export function createCloudShadowBinding(state: CloudShadowState) {
  const originals = new Map<Material, { compile: Material['onBeforeCompile']; key: Material['customProgramCacheKey']; data: unknown }>();
  let disposed = false;
  return {
    bind(scene: Scene) {
      if (disposed || !state.enabled) return;
      scene.traverse(object => {
        if (!(object instanceof Mesh)) return;
        for (const material of Array.isArray(object.material) ? object.material : [object.material]) {
          const surface = material.userData.artSurface as keyof typeof config.response;
          if (!surface || !(surface in config.response) || originals.has(material)) continue;
          const strength = material.name === 'courtyard-living-orb' ? config.response.orb
            : material.userData.waterKind === 'jet' ? config.response.jet : config.response[surface];
          const compile = material.onBeforeCompile, key = material.customProgramCacheKey;
          originals.set(material, { compile, key, data: material.userData.cloudShadow });
          material.customProgramCacheKey = () => `${key.call(material)}-cloud-shadow-v2-${strength}`;
          material.onBeforeCompile = (shader: Shader, renderer: WebGLRenderer) => {
            compile.call(material, shader, renderer);
            if (!state.active.value) return;
            try { extend(shader, surface, strength, state); }
            catch (error) {
              state.active.value = 0;
              state.failures.push(`${material.name}: ${String(error)}`);
              console.warn('Cloud shade unavailable; original surface lighting retained.', error);
            }
          };
          material.userData.cloudShadow = { surface, strength };
        }
      });
    },
    get metadata() { return { ...state.snapshot(), materials: [...originals.keys()].map(m => ({ name: m.name, ...m.userData.cloudShadow })), newGeometries: 0, newTextures: 0, extraPasses: 0, extraDrawCalls: 0 }; },
    dispose() {
      if (disposed) return;disposed = true;
      for (const [material, original] of originals) {
        material.onBeforeCompile = original.compile;material.customProgramCacheKey = original.key;
        if (original.data === undefined) delete material.userData.cloudShadow;
        else material.userData.cloudShadow = original.data;
      }
      originals.clear();
    },
  };
}
