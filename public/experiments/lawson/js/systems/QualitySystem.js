import { QUALITY_PRESETS } from '../config/sceneConfig.js';

/** Owns the render quality level + adaptive downgrade when the frame rate collapses. */
export class QualitySystem {
  constructor(renderer, sceneManager, onChange) {
    this.renderer = renderer;
    this.sceneManager = sceneManager;
    this.level = 'high';
    this.onChange = onChange || null;
    this._lowFrames = 0;
    this._downgraded = false;
    this.apply('high');
  }

  static detectDefault() {
    const mem = navigator.deviceMemory || 8;
    const cores = navigator.hardwareConcurrency || 8;
    if (mem <= 4 && cores <= 4) return 'low';
    if (mem <= 8 && cores <= 6) return 'medium';
    return 'high';
  }

  apply(level) {
    const preset = QUALITY_PRESETS[level] ? level : 'high';
    this.level = preset;
    this.renderer.setQuality(preset);
    const sun = this.sceneManager.sun;
    const size = QUALITY_PRESETS[preset].shadowMap;
    sun.castShadow = QUALITY_PRESETS[preset].shadows;
    if (sun.shadow && sun.shadow.mapSize.x !== size) {
      sun.shadow.mapSize.set(size, size);
      if (sun.shadow.map) {
        sun.shadow.map.dispose();
        sun.shadow.map = null;
      }
    }
    if (this.onChange) this.onChange(preset);
    return preset;
  }

  set(level) { return this.apply(level); }

  /** Called each second with the measured fps. */
  tick(fps) {
    if (this._downgraded || this.level === 'low') return;
    if (fps > 0 && fps < 26) {
      this._lowFrames += 1;
      if (this._lowFrames >= 3) {
        const next = this.level === 'high' ? 'medium' : 'low';
        this._downgraded = true;
        this.apply(next);
        console.warn('[Quality] low fps (' + fps + '), downgraded to', next);
      }
    } else {
      this._lowFrames = 0;
    }
  }
}
