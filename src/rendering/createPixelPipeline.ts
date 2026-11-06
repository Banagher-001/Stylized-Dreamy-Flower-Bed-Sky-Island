import {
  BufferGeometry, Float32BufferAttribute, HalfFloatType, LinearSRGBColorSpace,
  Mesh, NearestFilter, OrthographicCamera, Scene, ShaderMaterial,
  SRGBColorSpace, UnsignedByteType, Vector2, WebGLRenderTarget,
} from 'three';
import type { Camera, WebGLRenderer } from 'three';
import { visualConfig } from '../config/visual';
import type { PixelOptions } from '../config/visual';

/** Linear scene target -> texel-center lookup -> one final sRGB output. */
export function createPixelPipeline(renderer: WebGLRenderer, options: PixelOptions) {
  const halfFloat = options.storage !== 'byte' && renderer.extensions.has('EXT_color_buffer_float');
  const target = new WebGLRenderTarget(1, 1, {
    type: halfFloat ? HalfFloatType : UnsignedByteType,
    minFilter: NearestFilter,
    magFilter: NearestFilter,
    generateMipmaps: false,
    depthBuffer: true,
    stencilBuffer: false,
  });
  // SRGB8 attachments perform storage encoding / sample decoding in hardware.
  // This avoids dark-color loss on devices without renderable half-float targets.
  target.texture.colorSpace = halfFloat ? LinearSRGBColorSpace : SRGBColorSpace;
  target.texture.name = 'courtyard-pixel-scene';
  const geometry = new BufferGeometry();
  geometry.setAttribute('position', new Float32BufferAttribute([-1, -1, 0, 3, -1, 0, -1, 3, 0], 3));
  geometry.setAttribute('uv', new Float32BufferAttribute([0, 0, 2, 0, 0, 2], 2));
  const finish = visualConfig.finishes[options.finish];
  const material = new ShaderMaterial({
    name: 'courtyard-pixel-output',
    depthTest: false,
    depthWrite: false,
    toneMapped: false,
    uniforms: {
      uScene: { value: target.texture },
      uSampleSize: { value: new Vector2(1, 1) },
      uLevels: { value: finish.levels },
      uDither: { value: finish.dither },
    },
    vertexShader: /* glsl */`
      varying vec2 vPixelUv;
      void main() {
        vPixelUv = uv;
        gl_Position = vec4(position.xy, 0.0, 1.0);
      }
    `,
    fragmentShader: /* glsl */`
      uniform sampler2D uScene;
      uniform vec2 uSampleSize;
      uniform float uLevels;
      uniform float uDither;
      varying vec2 vPixelUv;
      float bayer2(vec2 p) {
        vec2 b = mod(p, 2.0);
        return mod(2.0 * b.x + 3.0 * b.y, 4.0);
      }
      void main() {
        vec2 cell = clamp(floor(vPixelUv * uSampleSize), vec2(0.0), uSampleSize - 1.0);
        vec2 centerUv = (cell + 0.5) / uSampleSize;
        vec3 linearColor = texture2D(uScene, centerUv).rgb;
        vec3 displayColor = linearToOutputTexel(vec4(linearColor, 1.0)).rgb;
        if (uLevels > 1.0) {
          float threshold = (4.0 * bayer2(cell) + bayer2(floor(cell / 2.0)) + 0.5) / 16.0 - 0.5;
          float steps = uLevels - 1.0;
          displayColor = floor(clamp(displayColor + threshold * uDither / steps, 0.0, 1.0) * steps + 0.5) / steps;
        }
        gl_FragColor = vec4(displayColor, 1.0);
      }
    `,
  });
  const outputScene = new Scene();
  const camera = new OrthographicCamera(-1, 1, 1, -1, 0, 1);
  const mesh = new Mesh(geometry, material);
  mesh.frustumCulled = false;
  outputScene.add(mesh);
  let disposed = false;
  let allocations = 0;

  function releaseGpuResources() {
    target.dispose();
    geometry.dispose();
    material.dispose();
  }

  return {
    releaseGpuResources,
    resize(outputWidth: number, outputHeight: number) {
      const scale = Math.min(1, options.resolution / Math.max(outputWidth, outputHeight));
      const width = Math.max(1, Math.round(outputWidth * scale));
      const height = Math.max(1, Math.round(outputHeight * scale));
      if (width !== target.width || height !== target.height) {
        target.setSize(width, height);
        material.uniforms.uSampleSize!.value.set(width, height);
        allocations++;
      }
    },
    render(scene: Scene, sceneCamera: Camera) {
      renderer.setRenderTarget(target);
      renderer.render(scene, sceneCamera);
      renderer.setRenderTarget(null);
      renderer.render(outputScene, camera);
    },
    getInfo() {
      return {
        sampleWidth: target.width, sampleHeight: target.height,
        designResolution: options.resolution, finish: options.finish,
        storage: halfFloat ? 'linear-half-float' : 'srgb8',
        minFilter: 'nearest', magFilter: 'nearest', mipmaps: false,
        levels: finish.levels, dither: finish.dither, allocations,
      };
    },
    dispose() {
      if (disposed) return;
      disposed = true;
      releaseGpuResources();
      outputScene.clear();
    },
  };
}
