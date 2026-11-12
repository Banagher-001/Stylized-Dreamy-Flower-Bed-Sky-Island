import { STORE, OBSTACLES } from './clerkConfig.js';

/**
 * Grid navigation for the shop floor + stock room.
 * A* over a 0.3 m grid with line-of-sight smoothing, never crossing gondolas,
 * the checkout counter, the cooler bank, dining furniture or the stock-room racks.
 */
export class NavGrid {
  constructor() {
    this.cell = 0.30;
    const s = STORE.salesFloor;
    const b = STORE.backroom;
    this.x0 = Math.min(s.x0, b.x0);
    this.x1 = Math.max(s.x1, b.x1);
    this.z0 = Math.min(s.z0, b.z0);
    this.z1 = Math.max(s.z1, b.z1);
    this.nx = Math.ceil((this.x1 - this.x0) / this.cell) + 1;
    this.nz = Math.ceil((this.z1 - this.z0) / this.cell) + 1;
    this.blocked = new Uint8Array(this.nx * this.nz);
    this._build();
  }

  _region(x, z) {
    const s = STORE.salesFloor; const b = STORE.backroom; const d = STORE.doorGap;
    const inSales = x >= s.x0 && x <= s.x1 && z >= s.z0 && z <= s.z1;
    const inBack = x >= b.x0 && x <= b.x1 && z >= b.z0 && z <= b.z1;
    const inDoor = x >= d.x0 && x <= d.x1 && z >= d.z0 && z <= d.z1;
    return inSales || inBack || inDoor;
  }

  _build() {
    const r = 0.20;
    for (let i = 0; i < this.nx; i++) {
      for (let j = 0; j < this.nz; j++) {
        const x = this.x0 + i * this.cell;
        const z = this.z0 + j * this.cell;
        let blocked = !this._region(x, z);
        if (!blocked) {
          for (const ob of OBSTACLES) {
            if (x > ob[0] - r && x < ob[1] + r && z > ob[2] - r && z < ob[3] + r) { blocked = true; break; }
          }
        }
        // partition wall: block it except for the stock-room door gap
        if (!blocked) {
          const d = STORE.doorGap;
          if (z > -4.68 && z < -4.35 && !(x >= d.x0 && x <= d.x1)) blocked = true;
        }
        this.blocked[i * this.nz + j] = blocked ? 1 : 0;
      }
    }
  }

  _cell(x, z) {
    const i = Math.round((x - this.x0) / this.cell);
    const j = Math.round((z - this.z0) / this.cell);
    return [Math.max(0, Math.min(this.nx - 1, i)), Math.max(0, Math.min(this.nz - 1, j))];
  }

  _center(i, j) { return [this.x0 + i * this.cell, this.z0 + j * this.cell]; }

  _free(i, j) { return i >= 0 && j >= 0 && i < this.nx && j < this.nz && !this.blocked[i * this.nz + j]; }

  walkable(x, z) {
    if (!this._region(x, z)) return false;
    if (x < this.x0 || x > this.x1 || z < this.z0 || z > this.z1) return false;
    const [i, j] = this._cell(x, z);
    if (!this._free(i, j)) return false;
    // extra safety: sampled point inside a real obstacle
    for (const ob of OBSTACLES) {
      if (x > ob[0] - 0.16 && x < ob[1] + 0.16 && z > ob[2] - 0.16 && z < ob[3] + 0.16) return false;
    }
    return true;
  }

  nearestWalkable(x, z, maxR = 3.0) {
    if (this.walkable(x, z)) return [x, z];
    for (let r = this.cell; r <= maxR; r += this.cell) {
      for (let a = 0; a < 16; a++) {
        const t = (a / 16) * Math.PI * 2;
        const px = x + Math.cos(t) * r;
        const pz = z + Math.sin(t) * r;
        if (this.walkable(px, pz)) return [px, pz];
      }
    }
    return null;
  }

  findPath(sx, sz, tx, tz) {
    const s = this.nearestWalkable(sx, sz);
    const t = this.nearestWalkable(tx, tz);
    if (!s || !t) return null;
    const [si, sj] = this._cell(s[0], s[1]);
    const [ti, tj] = this._cell(t[0], t[1]);
    if (si === ti && sj === tj) return [{ x: t[0], z: t[1] }];
    const start = si * this.nz + sj;
    const goal = ti * this.nz + tj;
    const open = [start];
    const g = new Float32Array(this.nx * this.nz).fill(Infinity);
    const f = new Float32Array(this.nx * this.nz).fill(Infinity);
    const parent = new Int32Array(this.nx * this.nz).fill(-1);
    const closed = new Uint8Array(this.nx * this.nz);
    g[start] = 0;
    const h = (i, j) => Math.hypot(i - ti, j - tj);
    f[start] = h(si, sj);
    while (open.length) {
      let bi = 0;
      for (let k = 1; k < open.length; k++) if (f[open[k]] < f[open[bi]]) bi = k;
      const cur = open.splice(bi, 1)[0];
      if (cur === goal) break;
      if (closed[cur]) continue;
      closed[cur] = 1;
      const ci = Math.floor(cur / this.nz);
      const cj = cur % this.nz;
      for (let di = -1; di <= 1; di++) {
        for (let dj = -1; dj <= 1; dj++) {
          if (!di && !dj) continue;
          const ni = ci + di; const nj = cj + dj;
          if (!this._free(ni, nj)) continue;
          if (di && dj && (!this._free(ci + di, cj) || !this._free(ci, cj + dj))) continue; // no corner cutting
          const nidx = ni * this.nz + nj;
          const step = (di && dj) ? 1.4142 : 1;
          const ng = g[cur] + step;
          if (ng < g[nidx]) {
            g[nidx] = ng; f[nidx] = ng + h(ni, nj); parent[nidx] = cur;
            open.push(nidx);
          }
        }
      }
    }
    if (parent[goal] === -1 && goal !== start) return null;
    const cells = [];
    let c = goal;
    while (c !== -1) { cells.push(c); if (c === start) break; c = parent[c]; }
    cells.reverse();
    const pts = cells.map((c) => this._center(Math.floor(c / this.nz), c % this.nz));
    pts[pts.length - 1] = [t[0], t[1]];
    return this._smooth(pts);
  }

  _lineOfSight(a, b) {
    const d = Math.hypot(b[0] - a[0], b[1] - a[1]);
    const n = Math.max(2, Math.ceil(d / 0.12));
    for (let i = 0; i <= n; i++) {
      const x = a[0] + (b[0] - a[0]) * (i / n);
      const z = a[1] + (b[1] - a[1]) * (i / n);
      if (!this.walkable(x, z)) return false;
    }
    return true;
  }

  _smooth(pts) {
    if (pts.length <= 2) return pts.map((p) => ({ x: p[0], z: p[1] }));
    const out = [pts[0]];
    let i = 0;
    while (i < pts.length - 1) {
      let j = pts.length - 1;
      for (; j > i + 1; j--) if (this._lineOfSight(pts[i], pts[j])) break;
      out.push(pts[j]);
      i = j;
    }
    return out.slice(1).map((p) => ({ x: p[0], z: p[1] }));
  }
}