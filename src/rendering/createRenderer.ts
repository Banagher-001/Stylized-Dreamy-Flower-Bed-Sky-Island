import { NoToneMapping, PCFShadowMap, SRGBColorSpace, Vector2, WebGLRenderer } from 'three';
import type { Camera, Scene } from 'three';
import { renderConfig } from '../config/scene';
import type { RenderMode } from '../config/scene';
import { resolveVisualOptions } from '../config/visual';
import type { PixelOptions } from '../config/visual';
import { createPixelPipeline } from './createPixelPipeline';
import { releaseSceneGpuResources } from './releaseSceneGpuResources';

export type RendererState = 'context-lost' | 'restored' | 'ready';

export function createRenderer(
  host: HTMLElement,
  initialMode: RenderMode,
  onAspectChange: (aspect: number) => void,
  pixelOptions: PixelOptions = resolveVisualOptions(new URLSearchParams()),
  onStateChange?: (state: RendererState) => void,
) {
  const renderer = new WebGLRenderer({ antialias: false, alpha: false });
  renderer.outputColorSpace = SRGBColorSpace;
  renderer.toneMapping = NoToneMapping;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = PCFShadowMap;
  // Only static buildings cast shadows; animated water and vegetation are receivers.
  renderer.shadowMap.autoUpdate = false;
  renderer.shadowMap.needsUpdate = true;
  renderer.info.autoReset = false;
  const pixels = createPixelPipeline(renderer, pixelOptions);
  const outputSize = new Vector2();

  const canvas = renderer.domElement;
  canvas.setAttribute('role', 'img');
  canvas.setAttribute('aria-label', '固定俯视庭院：石柱和粉紫小花围绕八边形喷泉，蓝白水面流动，草花随风轻摆，树影边缘缓慢变化，可暂停整个场景动效。');
  host.append(canvas);

  let mode = initialMode;
  let disposed = false;
  let contextLost = false;
  let recovering = false;
  let suspended = false;
  let animating = true;
  let draw: ((timestamp: number) => void) | undefined;
  let activeScene: Scene | undefined;
  let stillFrame: number | undefined;
  let stillFramesRemaining = 0;
  let previousWidth = 0, previousHeight = 0, previousRatio = 0;

  function cancelStillFrame() {
    if (stillFrame !== undefined) cancelAnimationFrame(stillFrame);
    stillFrame = undefined;
    stillFramesRemaining = 0;
  }

  function queueStillFrame() {
    if (disposed || contextLost || suspended || animating || !draw || stillFrame !== undefined || stillFramesRemaining === 0) return;
    stillFrame = requestAnimationFrame((timestamp) => {
      stillFrame = undefined;
      stillFramesRemaining--;
      if (!disposed && !contextLost && !suspended && !animating) {
        draw?.(timestamp);
        queueStillFrame();
      }
    });
  }

  function requestStillFrame() {
    if (disposed || contextLost || suspended || animating || !draw) return;
    // WebKit can present the previous mode after the first submitted still frame.
    // A finite two-frame budget also covers compositing-layer changes; requests
    // coalesce and a stable paused scene has no running loop.
    stillFramesRemaining = Math.max(stillFramesRemaining, 2);
    queueStillFrame();
  }

  function syncLoop() {
    const available = !disposed && !contextLost && !suspended;
    if (!available || animating) cancelStillFrame();
    renderer.setAnimationLoop(available && animating && draw ? draw : null);
    if (available && !animating) requestStillFrame();
  }

  function resize() {
    const bounds = host.getBoundingClientRect();
    if (bounds.width <= 0 || bounds.height <= 0 || disposed) return;

    const deviceRatio = Math.min(window.devicePixelRatio || 1, renderConfig.maxDevicePixelRatio);

    const width = Math.max(1, Math.floor(bounds.width)), height = Math.max(1, Math.floor(bounds.height));
    if (width !== previousWidth || height !== previousHeight || deviceRatio !== previousRatio) {
      previousWidth = width;previousHeight = height;previousRatio = deviceRatio;
      renderer.setPixelRatio(deviceRatio);
      renderer.setSize(width, height, false);
      renderer.getDrawingBufferSize(outputSize);
      pixels.resize(outputSize.x, outputSize.y);
    }
    canvas.dataset.renderMode = mode;
    const info = pixels.getInfo();
    canvas.dataset.sampleWidth = String(mode === 'pixel' ? info.sampleWidth : outputSize.x);
    canvas.dataset.sampleHeight = String(mode === 'pixel' ? info.sampleHeight : outputSize.y);
    canvas.dataset.pixelProfile = String(info.designResolution);
    canvas.dataset.finish = info.finish;
    onAspectChange(bounds.width / bounds.height);
    requestStillFrame();
  }

  function onContextLost(event: Event) {
    event.preventDefault();
    contextLost = true;
    recovering = true;
    host.dataset.renderState = 'context-lost';
    syncLoop();
    // Three.js rebuilds its caches on restore. Remove callbacks to the old GPU
    // generation now, while deletes are ignored by the lost context.
    pixels.releaseGpuResources();
    if (activeScene) releaseSceneGpuResources(activeScene);
    onStateChange?.('context-lost');
  }

  function onContextRestored() {
    contextLost = false;
    previousWidth = 0;
    renderer.shadowMap.needsUpdate = true;
    onStateChange?.('restored');
    resize();
    syncLoop();
  }

  canvas.addEventListener('webglcontextlost', onContextLost);
  canvas.addEventListener('webglcontextrestored', onContextRestored);
  const observer = new ResizeObserver(resize);
  observer.observe(host);
  window.addEventListener('resize', resize);
  let dprQuery: MediaQueryList;
  function watchDpr() {
    dprQuery?.removeEventListener('change', onDprChange);
    dprQuery = window.matchMedia(`(resolution: ${window.devicePixelRatio}dppx)`);
    dprQuery.addEventListener('change', onDprChange);
  }
  function onDprChange() { watchDpr();resize(); }
  watchDpr();
  resize();

  return {
    canvas,
    setMode(nextMode: RenderMode) {
      mode = nextMode;
      resize();
    },
    setAnimating(value: boolean) { animating = value; syncLoop(); },
    setSuspended(value: boolean) { if (suspended === value) return;suspended = value;syncLoop(); },
    renderOnce() { draw?.(performance.now());requestStillFrame(); },
    getStats() {
      return {
        geometries: renderer.info.memory.geometries,
        textures: renderer.info.memory.textures,
        programs: renderer.info.programs?.length ?? 0,
        calls: renderer.info.render.calls,
        triangles: renderer.info.render.triangles,
        mode,
        outputWidth: renderer.domElement.width,
        outputHeight: renderer.domElement.height,
        pixel: mode === 'pixel' ? pixels.getInfo() : null,
      };
    },
    start(scene: Scene, camera: Camera, update?: (timestamp: number) => void) {
      activeScene = scene;
      draw = (timestamp) => {
        if (disposed || contextLost || suspended) return;
        update?.(timestamp);
        renderer.info.reset();
        if (mode === 'pixel') pixels.render(scene, camera);
        else {
          renderer.setRenderTarget(null);
          renderer.render(scene, camera);
        }
        host.dataset.renderState = 'ready';
        if (recovering) {
          recovering = false;
          onStateChange?.('ready');
          // The recovery notice just revealed the canvas. Submit a finite still
          // frame batch so WebKit can attach its restored compositing layer.
          requestStillFrame();
        }
      };
      syncLoop();
    },
    dispose() {
      if (disposed) return;
      disposed = true;
      cancelStillFrame();
      observer.disconnect();
      window.removeEventListener('resize', resize);
      dprQuery.removeEventListener('change', onDprChange);
      canvas.removeEventListener('webglcontextlost', onContextLost);
      canvas.removeEventListener('webglcontextrestored', onContextRestored);
      renderer.setAnimationLoop(null);
      draw = undefined;
      activeScene = undefined;
      pixels.dispose();
      renderer.dispose();
      // Disposal frees resources; explicitly release the browser's context slot too.
      if (!renderer.getContext().isContextLost() && renderer.extensions.has('WEBGL_lose_context')) {
        renderer.forceContextLoss();
      }
      canvas.remove();
    },
  };
}
