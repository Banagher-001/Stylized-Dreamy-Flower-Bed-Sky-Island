import * as THREE from 'three';

/** Raycast picking for the real scene objects, with hover outline + tooltip + actions. */
export class InteractionSystem {
  constructor(opts) {
    this.camera = opts.camera;
    this.dom = opts.dom;
    this.interactives = opts.interactives || [];
    this.handlers = opts.handlers || {};
    this.enabled = true;
    this.raycaster = new THREE.Raycaster();
    this.pointer = new THREE.Vector2();
    this.hovered = null;
    this._hoverCheckAt = 0;
    this._downPos = null;
    this._downTime = 0;

    this.meshEntries = [];
    this.meshes = [];
    this.interactives.forEach((entry) => {
      entry.meshes.forEach((mesh) => {
        if (!mesh) return;
        mesh.userData.interaction = entry;
        this.meshes.push(mesh);
        this.meshEntries.push(entry);
      });
    });

    this.tooltip = document.getElementById('tooltip');
    this.outline = new THREE.Box3Helper(new THREE.Box3(), new THREE.Color('#5aa8ff'));
    this.outline.material.depthTest = false;
    this.outline.material.transparent = true;
    this.outline.material.opacity = 0.9;
    this.outline.visible = false;
    this.outline.renderOrder = 999;
    if (opts.scene) opts.scene.add(this.outline);

    this._onMove = this._onPointerMove.bind(this);
    this._onDown = this._onPointerDown.bind(this);
    this._onUp = this._onPointerUp.bind(this);
    this.dom.addEventListener('pointermove', this._onMove);
    this.dom.addEventListener('pointerdown', this._onDown);
    this.dom.addEventListener('pointerup', this._onUp);
    this.dom.addEventListener('pointerleave', () => this._clearHover());
  }

  setEnabled(v) {
    this.enabled = !!v;
    if (!v) this._clearHover();
  }

  _updatePointer(event) {
    const rect = this.dom.getBoundingClientRect();
    this.pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    this.pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  }

  _pick() {
    this.raycaster.setFromCamera(this.pointer, this.camera);
    const hits = this.raycaster.intersectObjects(this.meshes, false);
    for (const hit of hits) {
      if (hit.object && hit.object.visible) return hit;
    }
    return null;
  }

  _onPointerMove(event) {
    if (!this.enabled) return;
    const now = performance.now();
    if (now - this._hoverCheckAt < 55) return;
    this._hoverCheckAt = now;
    this._updatePointer(event);
    const hit = this._pick();
    if (!hit) {
      this._clearHover();
      return;
    }
    const entry = hit.object.userData.interaction;
    if (!entry) {
      this._clearHover();
      return;
    }
    if (this.hovered !== entry) {
      this.hovered = entry;
      this.dom.style.cursor = 'pointer';
      this.outline.box.copy(entry.box);
      this.outline.visible = true;
      if (this.tooltip) {
        this.tooltip.innerHTML = '<b>' + entry.label + '</b> · 点击交互';
        this.tooltip.classList.remove('hidden');
      }
    }
    if (this.tooltip) {
      this.tooltip.style.left = event.clientX + 'px';
      this.tooltip.style.top = event.clientY + 'px';
    }
  }

  _onPointerDown(event) {
    this._downPos = { x: event.clientX, y: event.clientY };
    this._downTime = performance.now();
  }

  _onPointerUp(event) {
    if (!this.enabled || !this._downPos) return;
    const dx = event.clientX - this._downPos.x;
    const dy = event.clientY - this._downPos.y;
    const moved = Math.sqrt(dx * dx + dy * dy);
    const elapsed = performance.now() - this._downTime;
    this._downPos = null;
    if (moved > 7 || elapsed > 900) return;   // dragged => orbit, ignore click
    this._updatePointer(event);
    const hit = this._pick();
    if (!hit) return;
    const entry = hit.object.userData.interaction;
    if (entry) this.activate(entry.action, entry);
  }

  activate(action) {
    if (!action) return;
    const parts = action.split(':');
    const kind = parts[0];
    const arg = parts[1];
    const fn = this.handlers[kind];
    if (typeof fn === 'function') {
      fn(arg);
    } else {
      console.warn('[Interaction] no handler for action', action);
    }
  }

  _clearHover() {
    if (this.hovered) {
      this.hovered = null;
      this.dom.style.cursor = '';
      this.outline.visible = false;
      if (this.tooltip) this.tooltip.classList.add('hidden');
    }
  }
}
