import * as THREE from 'three';
import { DAY_NIGHT_KEYS, PRESETS } from '../config/lightConfig.js';
import { CAMERA_PRESETS } from '../config/sceneConfig.js';

const _c1 = new THREE.Color();
const _c2 = new THREE.Color();

function smoothstep(t) { return t * t * (3 - 2 * t); }

/** Interpolates sky / sun / fog / exposure / lamp state from a 0-24h clock. */
export class DayNightSystem {
  constructor(sceneManager, renderer, lighting) {
    this.sceneManager = sceneManager;
    this.renderer = renderer;
    this.lighting = lighting;
    this.time = 18.5;
    this.keys = DAY_NIGHT_KEYS;
    this.onChange = null;
    this.apply(this.time);
  }

  setTime(hours, silent) {
    this.time = Math.max(0, Math.min(24, hours));
    this.apply(this.time);
    if (!silent && this.onChange) this.onChange(this.time);
    return this.time;
  }

  setPreset(name) {
    const t = PRESETS[name];
    if (t === undefined) return this.time;
    // keep the slider/UI in sync without an extra callback loop
    return this.setTime(t);
  }

  sample(t) {
    const keys = this.keys;
    let a = keys[0];
    let b = keys[keys.length - 1];
    for (let i = 0; i < keys.length - 1; i += 1) {
      if (t >= keys[i].t && t <= keys[i + 1].t) { a = keys[i]; b = keys[i + 1]; break; }
    }
    const span = Math.max(1e-4, b.t - a.t);
    const f = smoothstep(Math.max(0, Math.min(1, (t - a.t) / span)));
    const lerpNum = (x, y) => x + (y - x) * f;
    const lerpCol = (x, y, out) => out.set(x).lerp(_c2.set(y), f).clone();
    return {
      skyTop: lerpCol(a.skyTop, b.skyTop, _c1),
      skyBottom: lerpCol(a.skyBottom, b.skyBottom, _c1),
      fog: lerpCol(a.fog, b.fog, _c1),
      sun: lerpNum(a.sun, b.sun),
      sunColor: lerpCol(a.sunColor, b.sunColor, _c1),
      hemi: lerpNum(a.hemi, b.hemi),
      ambient: lerpNum(a.ambient, b.ambient),
      exposure: lerpNum(a.exposure, b.exposure),
      lamps: lerpNum(a.lamps, b.lamps),
      emissive: lerpNum(a.emissive, b.emissive),
    };
  }

  apply(t) {
    const s = this.sample(t);
    this.sceneManager.setSky('#' + s.skyTop.getHexString(), '#' + s.skyBottom.getHexString());
    this.sceneManager.setFog('#' + s.fog.getHexString(), 70, 235);
    this.sceneManager.sun.intensity = s.sun;
    this.sceneManager.sun.color.copy(s.sunColor);
    this.sceneManager.hemi.intensity = s.hemi;
    this.sceneManager.ambient.intensity = s.ambient;
    this.renderer.setExposure(s.exposure);

    // sun / moon orbit: highest at noon, below horizon at night
    const ang = ((t - 6) / 12) * Math.PI;
    const el = Math.sin(ang);
    const az = Math.cos(ang);
    const height = 12 + 54 * Math.max(-0.25, el);
    this.sceneManager.sun.position.set(-40 * az, height, 32 + 10 * az);
    this.sceneManager.sun.visible = el > -0.18;

    this.lighting.setOutdoorFactor(s.lamps);
    this.lighting.setEmissiveGlobal(s.emissive);
  }
}
