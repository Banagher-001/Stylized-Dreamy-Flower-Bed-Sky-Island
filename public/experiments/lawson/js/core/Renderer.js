import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { QUALITY_PRESETS } from '../config/sceneConfig.js';

/** WebGL renderer + optional bloom composer, resolution and quality management. */
export class Renderer {
  constructor(canvas, scene, camera) {
    this.canvas = canvas;
    this.scene = scene;
    this.camera = camera;
    this.quality = 'high';

    this.renderer = new THREE.WebGLRenderer({
      canvas: canvas,
      antialias: true,
      powerPreference: 'high-performance',
      alpha: false,
      stencil: false,
    });
    this.renderer.setSize(window.innerWidth, window.innerHeight, false);
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.0;
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    // 阴影贴图每 2 帧更新一次：店内场景 98% 物体是静态的，
    // 只有店员/车辆/门在动，半速阴影肉眼看不出差别，但省掉一半 shadow pass。
    this.renderer.shadowMap.autoUpdate = false;
    this.renderer.shadowMap.needsUpdate = true;
    this._frameNo = 0;
    this.shadowInterval = 2;
    this.renderer.info.autoReset = false;
    this.resScale = 1.0;
    this._lowFps = 0;
    this._highFps = 0;
    this._resizePending = false;

    this.composer = new EffectComposer(this.renderer);
    this.renderPass = new RenderPass(scene, camera);
    this.bloomPass = new UnrealBloomPass(
      new THREE.Vector2(window.innerWidth, window.innerHeight), 0.12, 0.35, 1.15);
    this.outputPass = new OutputPass();
    this.composer.addPass(this.renderPass);
    this.composer.addPass(this.bloomPass);
    this.composer.addPass(this.outputPass);

    this.setQuality('high');
    this._onResize = () => this._scheduleResize();
    window.addEventListener('resize', this._onResize, { passive: true });
    window.addEventListener('orientationchange', this._onResize, { passive: true });
    document.addEventListener('fullscreenchange', this._onResize);
    if (window.visualViewport) window.visualViewport.addEventListener('resize', this._onResize, { passive: true });
    const watchDpr = () => {
      if (this._dprMedia) this._dprMedia.removeEventListener('change', watchDpr);
      this._dprMedia = window.matchMedia('(resolution: ' + (window.devicePixelRatio || 1) + 'dppx)');
      this._dprMedia.addEventListener('change', watchDpr);
      this._scheduleResize();
    };
    watchDpr();
    if (window.ResizeObserver) {
      this._ro = new ResizeObserver(() => this._scheduleResize());
      this._ro.observe(this.canvas);
    }
  }

  setQuality(level) {
    const p = QUALITY_PRESETS[level] || QUALITY_PRESETS.high;
    this.quality = level;
    this.preset = p;
    const dpr = Math.min(window.devicePixelRatio || 1, p.pixelRatio);
    this.renderer.setPixelRatio(dpr);
    this.composer.setPixelRatio(dpr);
    this.bloomPass.enabled = !!p.bloom;
    this.bloomPass.strength = p.bloomStrength;
    this.renderer.shadowMap.enabled = !!p.shadows;
    this.shadowInterval = this.quality === 'low' ? 3 : (this.quality === 'medium' ? 2 : 2);
    this.renderer.shadowMap.needsUpdate = true;
    this.resize();
  }

  _scheduleResize() {
    if (this._resizePending) return;
    this._resizePending = true;
    requestAnimationFrame(() => {
      this._resizePending = false;
      this.resize();
      setTimeout(() => this.resize(), 120);
    });
  }

  /** effective pixel ratio: preset cap + total pixel budget + adaptive scale */
  _effectiveDpr(w, h) {
    const p = this.preset || QUALITY_PRESETS.high;
    const base = Math.min(window.devicePixelRatio || 1, p.pixelRatio || 1);
    const budget = p.maxPixels ? Math.sqrt(p.maxPixels / Math.max(1, w * h)) : base;
    const dpr = Math.min(base, budget) * this.resScale;
    return Math.max(0.6, Math.min(2, dpr));
  }

  _applyPixelRatio(w, h) {
    const dpr = this._effectiveDpr(w, h);
    this.renderer.setPixelRatio(dpr);
    this.composer.setPixelRatio(dpr);
    this._lastDpr = dpr;
  }

  resize() {
    const canvas = this.canvas;
    let w = canvas.clientWidth || window.innerWidth;
    let h = canvas.clientHeight || window.innerHeight;
    w = Math.max(1, Math.round(w));
    h = Math.max(1, Math.round(h));
    this._width = w;
    this._height = h;
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    // updateStyle=false: CSS keeps canvas at 100% and the drawing buffer follows the real window
    this.renderer.setSize(w, h, false);
    this._applyPixelRatio(w, h);
    this.composer.setSize(w, h);
    this.bloomPass.resolution.set(Math.floor(w / 2), Math.floor(h / 2));
    this.renderer.info.reset();
  }

  /** called roughly once per second from the main loop */
  tickPerformance(fps) {
    if (!this.preset) return;
    if (fps > 0 && fps < 54) {
      this._lowFps += 1;
      this._highFps = 0;
      if (this._lowFps >= 2 && this.resScale > 0.71) {
        this.resScale = Math.max(0.70, this.resScale - 0.08);
        this._lowFps = 0;
        this.resize();
      }
    } else if (fps > 59) {
      this._highFps += 1;
      this._lowFps = 0;
      if (this._highFps >= 6 && this.resScale < 1.0) {
        this.resScale = Math.min(1.0, this.resScale + 0.04);
        this._highFps = 0;
        this.resize();
      }
    } else {
      this._lowFps = 0;
      this._highFps = 0;
    }
  }

  setExposure(v) {
    this.renderer.toneMappingExposure = v;
  }

  render(dt) {
    this._frameNo += 1;
    if (this.preset && this.preset.shadows) {
      const interval = this.shadowInterval || 2;
      if (this._frameNo % interval === 0) this.renderer.shadowMap.needsUpdate = true;
    }
    this.renderer.info.reset();
    if (this.bloomPass.enabled) {
      this.composer.render(dt);
    } else {
      this.renderer.render(this.scene, this.camera);
    }
  }

  get stats() {
    const info = this.renderer.info;
    return {
      drawCalls: info.render.calls,
      triangles: info.render.triangles,
      programs: info.programs ? info.programs.length : 0,
      geometries: info.memory.geometries,
      textures: info.memory.textures,
      pixelRatio: Number((this._lastDpr || 1).toFixed(2)),
      resScale: Number(this.resScale.toFixed(2)),
      width: this._width || 0,
      height: this._height || 0,
    };
  }
}