import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { MODELS } from '../config/assetManifest.js';
import { CEILING_NAME_PATTERNS } from '../config/sceneConfig.js';

const inZone = (c, x, y, z) => (c.x >= x[0] && c.x <= x[1] && c.y >= y[0] && c.y <= y[1] && c.z >= z[0] && c.z <= z[1]);

/**
 * Interactive proxy rules. Each rule uses the real object name *and* its world position, so
 * e.g. the coffee sign inside the shop is not confused with the LAWSON shop-front sign band.
 */
const INTERACTIVE_RULES = [
  {
    id: 'sign', label: 'LAWSON 招牌 / 灯箱', action: 'light:LawsonSign',
    test: (n, c) => /sign|lawson|logo|shield|band|stripe|lightbox|pylon|text/i.test(n)
      && c.z > 6.4 && c.y > 2.6,
  },
  {
    id: 'facade', label: '外墙灯带', action: 'light:FacadeStrip',
    test: (n, c) => /facade|stripe|canopy|eave|band/i.test(n) && c.z > 6.6 && c.y > 2.2 && c.y < 5.2,
  },
  {
    id: 'door', label: '自动门', action: 'door',
    test: (n, c) => /door|glass|handle/i.test(n) && Math.abs(c.x) < 1.9 && c.z > 6.8 && c.z < 8.2 && c.y < 3.0,
  },
  {
    id: 'vending', label: '自动售货机', action: 'light:VendingLighting',
    test: (n, c) => /vend/i.test(n),
  },
  {
    id: 'atm', label: 'ATM', action: 'toggle:atm',
    test: (n, c) => /^atm|atm[A-Z_a-z]/i.test(n) && c.x > 10.5,
  },
  {
    id: 'coffee', label: '咖啡机', action: 'toggle:coffee',
    test: (n, c) => /coffee/i.test(n) && c.x < -8 && c.z < 6,
  },
  {
    id: 'oden', label: '关东煮 / 热食蒸汽', action: 'toggle:steam',
    test: (n, c) => /oden|steam|fried|hotfood/i.test(n) && c.z < 6.5,
  },
  {
    id: 'cooler', label: '饮料冷藏柜', action: 'light:CoolerLighting',
    test: (n, c) => /cooler|fridge/i.test(n),
  },
  {
    id: 'freezer', label: '卧式冰柜', action: 'light:CoolerLighting',
    test: (n, c) => /freezer|snowflake|icecream|lid/i.test(n) && c.x > 6,
  },
  {
    id: 'microwave', label: '微波炉', action: 'focus:microwave',
    test: (n, c) => /microwave/i.test(n),
  },
  {
    id: 'basket', label: '购物篮', action: 'light:CoolerLighting',
    test: (n, c) => /basket|crate/i.test(n),
  },
  {
    id: 'checkout', label: '收银台', action: 'focus:checkout',
    test: (n, c) => /checkout|counter|register|pos[A-Z_]|receipt|scanner/i.test(n) && c.x < -4 && c.z > 4,
  },
  {
    id: 'clerkA', label: '店员 A（收银）', action: 'focus:clerkA',
    test: (n) => /^clerkA_/i.test(n),
  },
  {
    id: 'clerkB', label: '店员 B（理货）', action: 'focus:clerkB',
    test: (n) => /^clerkB_/i.test(n),
  },
  {
    id: 'dining', label: '店内用餐区', action: 'focus:dining',
    test: (n, c) => /diningFurniture|diningStool|diningRecycle/i.test(n) && c.z < -4.6,
  },
  {
    id: 'alcohol', label: '酒品专区', action: 'focus:alcohol',
    test: (n, c) => /alcoholWallUnit|alcoholEndCap/i.test(n) && c.z < -5.4,
  },
  {
    id: 'shelf', label: '货架通道', action: 'focus:aisle',
    test: (n, c) => /aisle[a-e]_/i.test(n),
  },
];

const BLOCKER_RULES = [
  { patterns: [/aisle[a-e]_(frame|boards|products|endcaps)/i], label: 'aisle' },
  { patterns: [/checkoutcounter/i, /countermain/i, /counterreturn/i], label: 'counter' },
  { patterns: [/uprightcoolerbank/i, /coolerframe/i], label: 'cooler' },
  { patterns: [/chestfreezer/i, /freezertopf/i], label: 'freezer' },
  { patterns: [/microwavestation/i, /microwavestand/i, /atmKiosk/i, /atmCabinet/i], label: 'station' },
  { patterns: [/odendisplay/i, /odenpot/i, /odenstation/i, /coffeestation/i], label: 'hotfood' },
  { patterns: [/walldailygoods/i, /wallsnack/i], label: 'wallshelf' },
  // --- interior rework (2026-11-02) new fixtures: keep walk-mode collisions honest ---
  { patterns: [/dressPromoIsland/i, /dressPromoTable/i, /dressEndTower/i, /dressWallShelf/i,
                /dressRestock/i], label: 'display' },
  { patterns: [/backroomStorageRack_15/i, /backroomDrinkCrates/i, /backroomNewCartons/i,
                /backroomHandTruck/i, /backroomCleanCorner/i], label: 'backroom' },
  { patterns: [/basketRack/i, /magazineRack/i, /tobaccoCabinet/i, /impulseRack/i,
                /odenPriceSign/i, /bagStand16/i], label: 'checkout-prop' },
  { patterns: [/miniFreezerShell/i, /recycleBins/i, /packingCounter/i, /packingStation/i,
                /microHotWater/i, /atmStandSign/i, /queuePost|stanchion|beltPost/i], label: 'cold-prop' },
  // --- 2nd interior deepening (2026-11-02): dining / alcohol / corners ---
  { patterns: [/alcoholWallUnit/i, /alcoholEndCap/i, /alcoholSignStand/i], label: 'alcohol' },
  { patterns: [/diningFurniture/i, /diningStool/i, /diningRecycle/i], label: 'dining' },
  { patterns: [/cornerShelves/i, /promoCarts/i, /entranceCart/i], label: 'deepening-prop' },
];

export class AssetManager {
  constructor() {
    this.loader = new GLTFLoader();
    this.sceneRoot = null;
    this.cars = {};
    this.materials = [];
    this.nodes = new Map();
  }

  async loadAll(onProgress) {
    const total = 4;
    let done = 0;
    const report = (label) => {
      done += 1;
      if (onProgress) onProgress(done / total, label);
    };
    const sceneGltf = await this._load(MODELS.scene.url);
    report('便利店场景');
    this.sceneRoot = sceneGltf.scene;
    this.sceneRoot.name = 'LawsonScene';
    this.sceneRoot.updateMatrixWorld(true);

    for (const tag of ['A', 'B', 'C']) {
      const gltf = await this._load(MODELS.cars[tag].url);
      const root = gltf.scene;
      root.name = 'CarRoot_' + tag;
      root.updateMatrixWorld(true);
      this.cars[tag] = root;
      report('汽车 ' + tag);
    }
    return { scene: this.sceneRoot, cars: this.cars };
  }

  _load(url) {
    return new Promise((resolve, reject) => {
      this.loader.load(url, resolve, undefined, (err) => {
        reject(new Error('加载失败: ' + url + ' — ' + (err && err.message ? err.message : err)));
      });
    });
  }

  /** Collect node names into a lookup map (all levels). */
  indexNodes(root) {
    const map = new Map();
    root.traverse((o) => {
      if (o.name) {
        if (!map.has(o.name)) map.set(o.name, []);
        map.get(o.name).push(o);
      }
    });
    return map;
  }

  find(map, name) {
    const arr = map.get(name);
    return arr && arr.length ? arr[0] : null;
  }

  /** Prepare materials, shadows and discovery metadata for the static scene. */
  prepareStatic(root, sceneManager) {
    const nodeMap = this.indexNodes(root);
    const materialGroups = new Map();   // material -> Set(groupId)
    const emissive = [];
    const matSeen = new Set();
    const shadows = { cast: 0, receive: 0 };

    root.traverse((obj) => {
      if (!obj.isMesh) return;
      obj.castShadow = false;
      obj.receiveShadow = false;
      const geom = obj.geometry;
      if (geom && !geom.boundingSphere) geom.computeBoundingSphere();
      const radius = geom && geom.boundingSphere ? geom.boundingSphere.radius : 0.5;
      const mats = Array.isArray(obj.material) ? obj.material : [obj.material];
      let transparent = false;
      mats.forEach((m) => { if (m && (m.transparent || (m.opacity !== undefined && m.opacity < 1))) transparent = true; });
      if (radius > 1.7 && !transparent) { obj.castShadow = true; shadows.cast += 1; }
      if (!transparent && radius > 0.9) { obj.receiveShadow = true; shadows.receive += 1; }

      mats.forEach((mat) => {
        if (!mat || matSeen.has(mat)) return;
        matSeen.add(mat);
        // convert transmission (screen space refraction) to cheap transparency for realtime
        if (mat.transmission !== undefined && mat.transmission > 0) {
          mat.transmission = 0;
          mat.transparent = true;
          mat.opacity = Math.min(mat.opacity !== undefined ? mat.opacity : 1, 0.32);
          mat.depthWrite = false;
          mat.metalness = 0;
        }
        if (mat.transparent || (mat.opacity !== undefined && mat.opacity < 1)) mat.depthWrite = false;
        if (mat.envMapIntensity !== undefined) mat.envMapIntensity = sceneManager.envIntensity;
        mat.side = mat.side !== undefined ? mat.side : THREE.FrontSide;
        if (mat.emissive && mat.emissiveIntensity !== undefined && mat.emissiveIntensity > 0.01) {
          // Blender exported HDR emissive strengths (up to ~9). Realtime + bloom needs a
          // much lower ceiling per material family, otherwise every lightbox turns into a
          // white blob and the brand blue is lost.
          const nm = mat.name || '';
          const authored = mat.emissiveIntensity;
          let cap = 0.90;
          if (/glow|stripe|white/i.test(nm)) cap = 0.16;
          else if (/sign|lawson|logo|shield|lightbox/i.test(nm)) cap = 0.34;
          else if (/head|tail|brake|turn|reverse|plate/i.test(nm)) cap = 1.6;
          else if (/warm|interior|ceil|panel|emitwarm/i.test(nm)) cap = 0.58;
          else if (/cooler|freez|led|cool/i.test(nm)) cap = 0.78;
          mat.emissiveIntensity = Math.min(authored * 0.5, cap);
          emissive.push({ material: mat, base: mat.emissiveIntensity, groups: [] });
        }
        this.materials.push(mat);
      });
    });

    const roofNodes = [];
    const roof = this.find(nodeMap, 'roofRoot');
    if (roof) roofNodes.push(roof);
    const ceilingNodes = [];
    root.traverse((o) => {
      if (!o.isMesh) return;
      if (CEILING_NAME_PATTERNS.some((re) => re.test(o.name))) ceilingNodes.push(o);
      if (/^roof/i.test(o.name) && !roofNodes.includes(o)) roofNodes.push(o);
    });

    return {
      nodeMap: nodeMap,
      roofNodes: roofNodes,
      ceilingNodes: ceilingNodes,
      emissive: emissive,
      shadows: shadows,
    };
  }

  /**
   * Static batching: merge opaque, non-interactive leaf meshes by material into a few
   * big meshes. This is the single biggest draw-call saver for the 2,400-mesh shop.
   * Anything animated / clickable / cut-away stays untouched:
   *   - clerk A/B rig and their ancestors,
   *   - the two sliding-door pivots,
   *   - roof / ceiling cut-away nodes,
   *   - steam puffs (visibility toggled),
   *   - every mesh used by the interaction raycast.
   */
  mergeStatic(root, opts = {}) {
    root.updateMatrixWorld(true);
    const protectedSet = new Set();
    const protect = (obj) => { if (obj) obj.traverse((o) => protectedSet.add(o)); };
    const protectAncestors = (obj) => { let p = obj; while (p) { protectedSet.add(p); p = p.parent; } };
    (opts.interactives || []).forEach((entry) => {
      (entry.meshes || []).forEach((mesh) => { protectAncestors(mesh); });
    });
    (opts.roofNodes || []).forEach((n) => { protect(n); protectAncestors(n); });
    (opts.ceilingNodes || []).forEach((n) => { protect(n); protectAncestors(n); });
    const dynamicRoots = [];
    root.traverse((o) => {
      const n = o.name || '';
      if (/^(clerkA_root|clerkB_root|slideDoorLeft_pivot|slideDoorRight_pivot)$/.test(n)) dynamicRoots.push(o);
      if (/clerk[AB]_/i.test(n)) dynamicRoots.push(o);
      if (/steam/i.test(n)) dynamicRoots.push(o);
    });
    dynamicRoots.forEach((n) => { protect(n); protectAncestors(n); });

    const rootInv = new THREE.Matrix4().copy(root.matrixWorld).invert();
    const groups = new Map();
    root.traverse((obj) => {
      if (!obj.isMesh) return;
      if (obj.isSkinnedMesh || obj.isInstancedMesh) return;
      // hidden-in-GLB props must stay hidden; merging would make them visible
      let vis = true;
      for (let q = obj; q; q = q.parent) { if (q.visible === false) { vis = false; break; } }
      if (!vis) return;
      if (protectedSet.has(obj)) return;
      if (obj.children && obj.children.length) return;
      if (Array.isArray(obj.material)) return;
      const mat = obj.material;
      if (!mat) return;
      const transparent = mat.transparent || (mat.opacity !== undefined && mat.opacity < 1) || mat.alphaTest > 0;
      if (transparent) return;
      const geom = obj.geometry;
      if (!geom || !geom.attributes || !geom.attributes.position) return;
      if (geom.morphAttributes && Object.keys(geom.morphAttributes).length) return;
      if (geom.drawGroups && geom.drawGroups.length > 1) return;
      const sig = Object.keys(geom.attributes).sort().join(',') + '|' + (geom.index ? 'i' : 'n') + '|' + (obj.castShadow ? 'c' : '-') + '|' + (obj.receiveShadow ? 'r' : '-');
      const key = mat.uuid + '|' + sig;
      let group = groups.get(key);
      if (!group) { group = { material: mat, geoms: [], objs: [], castShadow: false, receiveShadow: false }; groups.set(key, group); }
      const g = geom.clone();
      const m = new THREE.Matrix4().multiplyMatrices(rootInv, obj.matrixWorld);
      g.applyMatrix4(m);
      group.geoms.push(g);
      group.objs.push(obj);
      group.castShadow = group.castShadow || !!obj.castShadow;
      group.receiveShadow = group.receiveShadow || !!obj.receiveShadow;
    });

    let merged = 0;
    let batchIndex = 0;
    const removeList = [];
    groups.forEach((group) => {
      if (group.geoms.length === 0) return;
      let geometry = null;
      try {
        geometry = group.geoms.length === 1 ? group.geoms[0] : mergeGeometries(group.geoms, false);
      } catch (err) {
        console.warn('[AssetManager] merge failed for', group.material && group.material.name, err);
        geometry = null;
      }
      if (!geometry) {
        // keep originals when a merge group could not be merged
        group.geoms.forEach((g) => { if (g !== geometry) g.dispose(); });
        return;
      }
      if (group.geoms.length > 1) group.geoms.forEach((g) => g.dispose());
      const mesh = new THREE.Mesh(geometry, group.material);
      mesh.name = 'staticBatch_' + (batchIndex++);
      mesh.castShadow = group.castShadow;
      mesh.receiveShadow = group.receiveShadow;
      mesh.matrixAutoUpdate = false;
      mesh.updateMatrix();
      root.add(mesh);
      merged += 1;
      group.objs.forEach((obj) => removeList.push(obj));
    });
    removeList.forEach((obj) => { if (obj.parent) obj.parent.remove(obj); });
    this.batchReport = { removedMeshes: removeList.length, batches: merged, groups: groups.size };
    console.info('[AssetManager] static batch ' + JSON.stringify(this.batchReport));
    return this.batchReport;
  }

  /** Build the interactive proxy table from the static scene (name + world position). */
  buildInteractives(root) {
    const list = [];
    const box = new THREE.Box3();
    const centre = new THREE.Vector3();
    root.updateMatrixWorld(true);
    root.traverse((obj) => {
      if (!obj.isMesh) return;
      const name = obj.name || '';
      box.setFromObject(obj);
      if (box.isEmpty()) return;
      box.getCenter(centre);
      for (const rule of INTERACTIVE_RULES) {
        if (!rule.test(name, centre)) continue;
        let entry = list.find((e) => e.id === rule.id);
        if (!entry) {
          entry = { id: rule.id, label: rule.label, action: rule.action, meshes: [], box: new THREE.Box3() };
          entry.box.makeEmpty();
          list.push(entry);
        }
        entry.meshes.push(obj);
        entry.box.union(box);
        break;
      }
    });
    return list.filter((e) => e.meshes.length > 0);
  }

  /** Simple AABB blockers used by the interior walk mode. */
  buildBlockers(root) {
    const groups = new Map();
    root.traverse((obj) => {
      if (!obj.isMesh) return;
      const name = obj.name || '';
      for (const rule of BLOCKER_RULES) {
        if (rule.patterns.some((re) => re.test(name))) {
          let box = groups.get(rule.label);
          if (!box) { box = new THREE.Box3(); box.makeEmpty(); groups.set(rule.label, box); }
          box.union(new THREE.Box3().setFromObject(obj));
          break;
        }
      }
    });
    return Array.from(groups.values()).filter((b) => !b.isEmpty());
  }

  /**
   * Discover the parts we animate inside each car GLB and derive the rig axes.
   *
   * Audited structure (identical layout in car_A/B/C.glb):
   *   carX_root (identity transform, extras.forward_axis = "-Z")
   *     steerFL / steerFR  (steering pivot at the front axle)
   *       wheelFL / wheelFR (wheel spin node)
   *     wheelRL / wheelRR   (wheel spin node)
   * The wheel spin axis is the node-local axis that maps to the car's +X (right)
   * axis, therefore rolling FORWARD is a NEGATIVE rotation about that axis.
   */
  prepareCar(tag) {
    const root = this.cars[tag];
    root.updateMatrixWorld(true);
    const map = this.indexNodes(root);
    const pick = (patterns) => {
      const found = [];
      map.forEach((items, name) => {
        if (patterns.some((re) => re.test(name))) found.push({ name: name, obj: items[0] });
      });
      return found;
    };
    const THREE_UP = new THREE.Vector3(0, 1, 0);
    const modelQ = new THREE.Quaternion();
    root.getWorldQuaternion(modelQ);
    const forwardAxis = (root.userData && root.userData.forward_axis) || '-Z';
    const fwd = forwardAxis === '-X' ? new THREE.Vector3(-1, 0, 0)
      : forwardAxis === '+X' ? new THREE.Vector3(1, 0, 0)
        : forwardAxis === '+Z' ? new THREE.Vector3(0, 0, 1)
          : new THREE.Vector3(0, 0, -1);
    const rightModel = fwd.clone().cross(THREE_UP).normalize();
    const rightWorld = rightModel.clone().applyQuaternion(modelQ).normalize();
    const upWorld = THREE_UP.clone().applyQuaternion(modelQ).normalize();

    const localAxisFor = (obj, worldAxis) => {
      obj.updateWorldMatrix(true, false);
      const q = new THREE.Quaternion();
      obj.getWorldQuaternion(q);
      return worldAxis.clone().applyQuaternion(q.clone().invert()).normalize();
    };

    const wheelBox = (wheelObj) => {
      const box = new THREE.Box3();
      const tmp = new THREE.Box3();
      wheelObj.updateWorldMatrix(true, true);
      const invWheel = new THREE.Matrix4().copy(wheelObj.matrixWorld).invert();
      wheelObj.traverse((o) => {
        if (!o.isMesh || !o.geometry) return;
        if (!o.geometry.boundingBox) o.geometry.computeBoundingBox();
        const m = new THREE.Matrix4().multiplyMatrices(invWheel, o.matrixWorld);
        tmp.copy(o.geometry.boundingBox).applyMatrix4(m);
        box.union(tmp);
      });
      return box;
    };

    const wheels = pick([/wheel(fl|fr|rl|rr)$/i]).map((item) => {
      const box = wheelBox(item.obj);
      const size = new THREE.Vector3();
      box.getSize(size);
      return {
        name: item.name,
        obj: item.obj,
        radius: Math.max(size.x, size.y, size.z) * 0.5,
        spinAxisLocal: localAxisFor(item.obj, rightWorld),
        baseQuat: item.obj.quaternion.clone(),
      };
    });
    const steers = pick([/steer(fl|fr)$/i]).map((item) => ({
      name: item.name,
      obj: item.obj,
      steerAxisLocal: localAxisFor(item.obj, upWorld),
      baseQuat: item.obj.quaternion.clone(),
    }));
    const head = pick([/headlamp|headlight|headlightl|headlightr/i]);
    const tail = pick([/taillamp|taillight|brelamp|brakelamp/i]);
    const turnL = pick([/turn.*l$|turnfrontl|turnrearl/i]);
    const turnR = pick([/turn.*r$|turnfrontr|turnrearr/i]);
    const reverse = pick([/reverselamp|reverselight/i]);

    root.traverse((obj) => {
      if (!obj.isMesh) return;
      const geom = obj.geometry;
      if (geom && !geom.boundingSphere) geom.computeBoundingSphere();
      const r = geom && geom.boundingSphere ? geom.boundingSphere.radius : 0.5;
      obj.castShadow = r > 0.18;
      obj.receiveShadow = true;
      const mats = Array.isArray(obj.material) ? obj.material : [obj.material];
      mats.forEach((m) => {
        if (!m) return;
        if (m.transmission !== undefined && m.transmission > 0) {
          m.transmission = 0;
          m.transparent = true;
          m.opacity = Math.min(m.opacity !== undefined ? m.opacity : 1, 0.42);
          m.depthWrite = false;
        }
        if (m.envMapIntensity !== undefined) m.envMapIntensity = 0.4;
        if (m.emissive && m.emissiveIntensity !== undefined) m.emissiveIntensity = 0.0;
      });
    });

    return {
      root: root,
      wheels: wheels,
      steers: steers,
      head: head,
      tail: tail,
      turnL: turnL,
      turnR: turnR,
      reverse: reverse,
      forwardAxis: forwardAxis,
      rightModel: rightModel,
    };
  }
}