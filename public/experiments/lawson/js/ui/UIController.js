import { LIGHT_GROUPS } from '../config/lightConfig.js';

/** Binds the HTML control panel to the app through an actions object. */
export class UIController {
  constructor(opts) {
    this.uiState = opts.uiState;
    this.actions = opts.actions || {};
    this.$ = (sel) => document.querySelector(sel);
    this.lightToggles = {};
    this._buildLightToggles();
    this._bind();
    this._renderMode = null;
  }

  _buildLightToggles() {
    const host = this.$('#light-toggles');
    if (!host) return;
    host.innerHTML = '';
    LIGHT_GROUPS.forEach((g) => {
      const el = document.createElement('div');
      el.className = 'toggle on';
      el.dataset.group = g.id;
      el.innerHTML = '<span class="lbl"><i class="dotc"></i>' + g.label + '</span><span class="sw"></span>';
      el.addEventListener('click', () => {
        const on = !el.classList.contains('on');
        el.classList.toggle('on', on);
        if (this.actions.toggleLight) this.actions.toggleLight(g.id, on);
      });
      host.appendChild(el);
      this.lightToggles[g.id] = el;
    });
  }

  _bind() {
    document.querySelectorAll('[data-preset]').forEach((btn) => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('[data-preset]').forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');
        if (this.actions.setPreset) this.actions.setPreset(btn.dataset.preset);
      });
    });
    const slider = this.$('#time-slider');
    if (slider) {
      slider.addEventListener('input', () => {
        const v = parseFloat(slider.value);
        this._setTimeLabel(v);
        if (this.actions.setTime) this.actions.setTime(v);
      });
    }
    const allOn = this.$('#lights-all-on');
    const allOff = this.$('#lights-all-off');
    if (allOn) allOn.addEventListener('click', () => {
      this._setAllLightToggles(true);
      if (this.actions.setAllLights) this.actions.setAllLights(true);
    });
    if (allOff) allOff.addEventListener('click', () => {
      this._setAllLightToggles(false);
      if (this.actions.setAllLights) this.actions.setAllLights(false);
    });
    const tToggle = this.$('#traffic-toggle');
    if (tToggle) tToggle.addEventListener('click', () => {
      const running = !tToggle.classList.contains('running');
      tToggle.classList.toggle('running', running);
      tToggle.classList.toggle('active', running);
      tToggle.textContent = running ? '暂停车辆' : '开始车辆';
      if (this.actions.trafficToggle) this.actions.trafficToggle(running);
    });
    const tReset = this.$('#traffic-reset');
    if (tReset) tReset.addEventListener('click', () => {
      if (this.actions.trafficReset) this.actions.trafficReset();
    });
    document.querySelectorAll('#traffic-speed button').forEach((btn) => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('#traffic-speed button').forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');
        if (this.actions.trafficSpeed) this.actions.trafficSpeed(parseFloat(btn.dataset.speed));
      });
    });
    document.querySelectorAll('#car-demo button').forEach((btn) => {
      btn.addEventListener('click', () => {
        if (this.actions.demoCar) this.actions.demoCar(btn.dataset.car);
      });
    });
    document.querySelectorAll('#clerk-buttons button').forEach((btn) => {
      btn.addEventListener('click', () => {
        if (this.actions.focusClerk) this.actions.focusClerk(btn.dataset.clerk);
      });
    });
    document.querySelectorAll('#camera-buttons button').forEach((btn) => {
      btn.addEventListener('click', () => {
        this.setCameraActive(btn.dataset.cam);
        if (this.actions.setCamera) this.actions.setCamera(btn.dataset.cam);
      });
    });
    const roof = this.$('#btn-roof');
    if (roof) roof.addEventListener('click', () => {
      if (this.actions.toggleRoof) this.actions.toggleRoof();
    });
    const walk = this.$('#btn-walk');
    if (walk) walk.addEventListener('click', () => {
      if (this.actions.toggleWalk) this.actions.toggleWalk();
    });
    const reset = this.$('#btn-reset-cam');
    if (reset) reset.addEventListener('click', () => {
      this.setCameraActive('hero');
      if (this.actions.resetCamera) this.actions.resetCamera();
    });
    const collapse = this.$('#panel-collapse');
    if (collapse) collapse.addEventListener('click', () => {
      const panel = this.$('#panel');
      panel.classList.toggle('collapsed');
      collapse.textContent = panel.classList.contains('collapsed') ? '+' : '–';
    });
    const fs = this.$('#btn-fullscreen');
    if (fs) fs.addEventListener('click', () => {
      if (!document.fullscreenElement) document.documentElement.requestFullscreen();
      else document.exitFullscreen();
    });
    const help = this.$('#btn-help');
    const helpOverlay = this.$('#help');
    if (help && helpOverlay) {
      help.addEventListener('click', () => helpOverlay.classList.remove('hidden'));
      const close = this.$('#help-close');
      if (close) close.addEventListener('click', () => helpOverlay.classList.add('hidden'));
      helpOverlay.addEventListener('click', (e) => {
        if (e.target === helpOverlay) helpOverlay.classList.add('hidden');
      });
    }
    const settings = this.$('#btn-settings');
    if (settings) settings.addEventListener('click', () => {
      const order = ['high', 'medium', 'low'];
      const cur = this.uiState.state.quality;
      const next = order[(order.indexOf(cur) + 1) % order.length];
      if (this.actions.setQuality) this.actions.setQuality(next);
    });
  }

  _setAllLightToggles(on) {
    Object.values(this.lightToggles).forEach((el) => el.classList.toggle('on', on));
  }

  _setTimeLabel(v) {
    const h = Math.floor(v);
    const m = Math.round((v - h) * 60);
    const label = this.$('#time-label');
    if (label) label.textContent = String(h).padStart(2, '0') + ':' + String(m).padStart(2, '0');
  }

  setLoading(ratio, text) {
    const bar = this.$('#loader-bar');
    const pct = this.$('#loader-pct');
    const txt = this.$('#loader-text');
    if (bar) bar.style.width = Math.round(ratio * 100) + '%';
    if (pct) pct.textContent = Math.round(ratio * 100) + '%';
    if (txt && text) txt.textContent = text;
  }

  hideLoader() {
    const loader = this.$('#loader');
    if (loader) {
      loader.classList.add('hide');
      setTimeout(() => { if (loader.parentNode) loader.parentNode.removeChild(loader); }, 700);
    }
  }

  showError(message) {
    const fatal = this.$('#fatal');
    const msg = this.$('#fatal-msg');
    if (msg) msg.textContent = message;
    if (fatal) fatal.classList.remove('hidden');
    const retry = this.$('#fatal-retry');
    if (retry) retry.addEventListener('click', () => window.location.reload());
  }

  syncState(state) {
    this._setTimeLabel(state.timeOfDay);
    const slider = this.$('#time-slider');
    if (slider && Math.abs(parseFloat(slider.value) - state.timeOfDay) > 0.05) slider.value = String(state.timeOfDay);
    Object.entries(this.lightToggles).forEach(([id, el]) => {
      const on = state.lights[id] !== false;
      el.classList.toggle('on', on);
    });
    const roof = this.$('#btn-roof');
    if (roof) roof.textContent = state.roofVisible ? '隐藏屋顶' : '显示屋顶';
    const walk = this.$('#btn-walk');
    if (walk) walk.classList.toggle('active', !!state.walk);
    const walkBar = this.$('#walk-bar');
    if (walkBar) walkBar.classList.toggle('hidden', !state.walk);
    const tToggle = this.$('#traffic-toggle');
    if (tToggle) {
      const running = !!(state.traffic && state.traffic.running);
      tToggle.classList.toggle('running', running);
      tToggle.classList.toggle('active', running);
      tToggle.textContent = running ? '暂停车辆' : '开始车辆';
    }
    document.querySelectorAll('[data-preset]').forEach((b) => {
      const map = { day: 9, dusk: 18.5, night: 22 };
      const target = map[b.dataset.preset];
      b.classList.toggle('active', Math.abs(state.timeOfDay - target) < 0.6);
    });
    if (state.cameraMode) {
      const mode = state.cameraMode;
      document.querySelectorAll('#camera-buttons button').forEach((b) => {
        b.classList.toggle('active', b.dataset.cam === mode);
      });
    }
    const perf = this.$('#perf');
    if (perf) {
      const fpsEl = this.$('#fps');
      const trisEl = this.$('#tris');
      if (fpsEl && state.fps > 0) fpsEl.textContent = String(state.fps);
      if (trisEl && state.stats && state.stats.triangles) trisEl.textContent = String(Math.round(state.stats.triangles / 1000));
    }
  }

  setCameraActive(name) {
    document.querySelectorAll('#camera-buttons button').forEach((b) => {
      b.classList.toggle('active', b.dataset.cam === name);
    });
  }

  setWalk(on) {
    const bar = this.$('#walk-bar');
    if (bar) bar.classList.toggle('hidden', !on);
    const btn = this.$('#btn-walk');
    if (btn) btn.classList.toggle('active', !!on);
  }

  setPerf(fps, stats) {
    const fpsEl = this.$('#fps');
    const trisEl = this.$('#tris');
    if (fpsEl) fpsEl.textContent = String(fps);
    if (trisEl && stats) trisEl.textContent = String(Math.round((stats.triangles || 0) / 1000));
  }

  setQuality(level) {
    console.log('[UI] quality ->', level);
  }

  hideUI(hide) {
    ['#panel', '.brand', '.topbar', '.hints', '.perf'].forEach((sel) => {
      document.querySelectorAll(sel).forEach((el) => {
        el.style.visibility = hide ? 'hidden' : '';
      });
    });
  }
}