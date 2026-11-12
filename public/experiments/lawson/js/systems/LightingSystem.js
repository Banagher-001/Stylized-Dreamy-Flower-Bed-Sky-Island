import * as THREE from 'three';
import { LIGHTS, LIGHT_GROUPS } from '../config/lightConfig.js';

/**
 * Builds the realtime light rig (point/spot lights in place of the 209 Blender lights) and
 * keeps a registry that maps light groups -> real lights + emissive materials, so every UI
 * switch changes both the light output and the glowing materials.
 */
export class LightingSystem {
  constructor(scene) {
    this.scene = scene;
    this.groups = new Map();
    this.lights = [];
    this.emissives = [];
    this.groupEnabled = {};
    this.outdoorFactor = 1;
    this.emissiveGlobal = 1;
    this._build();
  }

  _build() {
    LIGHT_GROUPS.forEach((g) => {
      this.groups.set(g.id, { id: g.id, label: g.label, emissive: g.emissive, lights: [], enabled: true });
      this.groupEnabled[g.id] = true;
    });
    LIGHTS.forEach((def, idx) => {
      let light;
      if (def.type === 'spot') {
        light = new THREE.SpotLight(new THREE.Color(def.color), def.intensity, def.distance || 25,
          def.angle || 0.7, def.penumbra || 0.6, def.decay === undefined ? 1.6 : def.decay);
        light.position.fromArray(def.pos);
        if (def.target) {
          light.target.position.fromArray(def.target);
          this.scene.add(light.target);
        }
        if (def.shadow) {
          light.castShadow = true;
          light.shadow.mapSize.set(1024, 1024);
          light.shadow.bias = -0.0009;
          light.shadow.camera.near = 1;
          light.shadow.camera.far = 40;
        }
      } else {
        light = new THREE.PointLight(new THREE.Color(def.color), def.intensity,
          def.distance || 12, def.decay === undefined ? 1.7 : def.decay);
        light.position.fromArray(def.pos);
        if (def.shadow) {
          light.castShadow = true;
          light.shadow.mapSize.set(512, 512);
        }
      }
      light.name = 'group_' + def.group + '_' + idx;
      light.userData.group = def.group;
      light.userData.base = def.intensity;
      light.userData.auto = def.auto || false;
      this.scene.add(light);
      this.lights.push(light);
      const grp = this.groups.get(def.group);
      if (grp) grp.lights.push(light);
    });
  }

  /** Register emissive materials discovered in the loaded model. */
  registerEmissives(list) {
    this.emissives = [];
    list.forEach((entry) => {
      const name = (entry.material && entry.material.name) || '';
      let groupId = null;
      for (const g of LIGHT_GROUPS) {
        if (g.emissive.some((re) => re.test(name))) { groupId = g.id; break; }
      }
      if (!groupId) {
        // heuristic fallbacks by name fragments
        if (/cooler|freez|led/i.test(name)) groupId = 'CoolerLighting';
        else if (/sign|lawson|logo|shield/i.test(name)) groupId = 'LawsonSign';
        else if (/head|tail|brake|turn|reverse/i.test(name)) groupId = 'VehicleLights';
        else groupId = 'StoreInterior';
      }
      entry.group = groupId;
      this.emissives.push(entry);
      const grp = this.groups.get(groupId);
      if (grp) {
        grp.emissiveCount = (grp.emissiveCount || 0) + 1;
        if (name) (grp.materials = grp.materials || []).push(entry.material);
      }
    });
  }

  /** Lights that belong to a moving object (cars) can be attached here so groups still work. */
  attachDynamicLight(light, groupId, baseIntensity) {
    light.userData.group = groupId;
    light.userData.base = baseIntensity !== undefined ? baseIntensity : light.intensity;
    light.userData.dynamic = true;
    this.lights.push(light);
    const grp = this.groups.get(groupId);
    if (grp) grp.lights.push(light);
    return light;
  }

  setGroupEnabled(groupId, on) {
    this.groupEnabled[groupId] = !!on;
    this.refresh();
  }

  toggleGroup(groupId) {
    this.setGroupEnabled(groupId, !this.groupEnabled[groupId]);
    return this.groupEnabled[groupId];
  }

  setAll(on) {
    Object.keys(this.groupEnabled).forEach((k) => { this.groupEnabled[k] = !!on; });
    this.refresh();
  }

  setOutdoorFactor(f) {
    this.outdoorFactor = Math.max(0, Math.min(1.2, f));
    this.refresh();
  }

  setEmissiveGlobal(f) {
    this.emissiveGlobal = f;
    this.refreshEmissive();
  }

  refresh() {
    this.lights.forEach((light) => {
      const groupId = light.userData.group;
      const on = this.groupEnabled[groupId] !== false;
      const base = light.userData.base || 0;
      let factor = on ? 1 : 0;
      if (light.userData.auto) factor *= this.outdoorFactor;
      light.intensity = base * factor;
      if (!light.userData.dynamic) light.visible = factor > 0.001;
      else light.visible = factor > 0.001 && light.userData.active !== false;
    });
    this.refreshEmissive();
  }

  refreshEmissive() {
    this.emissives.forEach((entry) => {
      const on = this.groupEnabled[entry.group] !== false;
      const fac = on ? this.emissiveGlobal : 0.0;
      const m = entry.material;
      if (!m) return;
      if (m.emissiveIntensity !== undefined) m.emissiveIntensity = entry.base * fac;
      if (m.emissive) {
        // keep the authored colour, only scale intensity
        if (!entry._emissiveColor) entry._emissiveColor = m.emissive.clone();
      }
    });
  }

  getState() {
    const out = {};
    Object.keys(this.groupEnabled).forEach((k) => { out[k] = this.groupEnabled[k]; });
    return out;
  }
}
