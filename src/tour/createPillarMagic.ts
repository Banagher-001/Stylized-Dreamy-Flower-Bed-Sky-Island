import { Box3, BufferAttribute, BufferGeometry, CanvasTexture, Color, LinearFilter, Mesh, PlaneGeometry, Points, Raycaster, ShaderMaterial, Triangle, Vector3 } from 'three';
import type { OrthographicCamera, Scene } from 'three';
import type { RenderMode } from '../config/scene';
import { readingStations } from './reading';
import type { MagicReadingFrame } from './magicStyle';
import { tourPoses } from './route';
import type { TourPose } from './route';
import { magicStyle, sampleMagic } from './magicStyle';

const vertex = `
  attribute float aRank; attribute float aSeed;
  uniform float uDust; uniform float uTime; uniform float uCount; uniform float uOpacity; uniform float uDisperse; uniform float uPointSize;
  varying vec2 vUv; varying float vAlpha; varying float vHue;
  void main(){
    vec3 p=position;vUv=uv;vAlpha=1.0;vHue=aSeed;
    if(uDust>.5){
      p.x+=.012*sin(uTime*.65+aSeed*9.0)+sign(p.x)*.05*uDisperse;
      p.y+=.012*cos(uTime*.55+aSeed*7.0)-.18*uDisperse;
      vAlpha=clamp(uCount-aRank,0.0,1.0)*uOpacity;
    }
    gl_Position=projectionMatrix*modelViewMatrix*vec4(p,1.0);gl_PointSize=uPointSize;
  }`;
const fragment = `
  uniform sampler2D uAtlas; uniform float uDust; uniform float uIndex; uniform float uTrace; uniform float uWake; uniform float uLod;
  uniform vec3 uCool; uniform vec3 uGold; uniform vec3 uEtch; uniform vec3 uLilac;
  varying vec2 vUv; varying float vAlpha; varying float vHue;
  void main(){
    if(uDust>.5){
      float edge=max(abs(gl_PointCoord.x-.5),abs(gl_PointCoord.y-.5));
      float alpha=vAlpha*(1.0-smoothstep(.25,.5,edge));if(alpha<.01)discard;
      vec3 color=mix(uCool,uGold,step(.76,vHue));color=mix(color,uLilac,step(.94,vHue));gl_FragColor=vec4(color,alpha);
    }else{
      float ink=texture2D(uAtlas,vec2((vUv.x+uIndex)/3.0,vUv.y)).a;
      float angle=fract(atan(vUv.y-.59,vUv.x-.5)/6.2831853+.25);
      float traced=smoothstep(angle-.025,angle+.025,uTrace);float awake=uWake*traced;
      float alpha=ink*(.24+.76*awake)*uLod;if(alpha<.008)discard;
      vec3 color=mix(uEtch,mix(uGold,uCool,smoothstep(.22,.38,vUv.y)),awake);gl_FragColor=vec4(color,alpha);
    }
    #include <colorspace_fragment>
  }`;
const clamp = (x: number, a: number, b: number) => Math.max(a, Math.min(b, x));

/** Fit the complete inscription to the stone's real, camera-facing plane. */
function fitInscription(stone: Mesh, hit: Vector3) {
  const positions = stone.geometry.getAttribute('position');
  const normals = stone.geometry.getAttribute('normal');
  const face = new Box3();
  const triangles: Triangle[] = [];
  for (let i = 0; i < positions.count; i += 3) {
    if (normals.getZ(i) < .999) continue;
    const a = new Vector3().fromBufferAttribute(positions, i);
    const b = new Vector3().fromBufferAttribute(positions, i + 1);
    const c = new Vector3().fromBufferAttribute(positions, i + 2);
    triangles.push(new Triangle(a, b, c));
    face.expandByPoint(a).expandByPoint(b).expandByPoint(c);
  }
  if (face.isEmpty()) return undefined;
  const preferred = stone.worldToLocal(hit.clone());
  const center = face.getCenter(new Vector3());
  const point = new Vector3();
  const weights = new Vector3();
  function onFace(x: number, y: number) {
    point.set(x, y, face.max.z);
    return triangles.some(triangle => triangle.getBarycoord(point, weights) !== null
      && Math.min(weights.x, weights.y, weights.z) >= -1e-7);
  }

  const { faceMargin: margin, sigilSize, surfaceOffset } = magicStyle;
  const fullSize = Math.min(sigilSize, face.max.x - face.min.x - 2 * margin, face.max.y - face.min.y - 2 * margin);
  for (let size = fullSize; size > 0; size -= .025) {
    const radius = size / 2 + margin;
    const x = clamp(preferred.x, face.min.x + radius, face.max.x - radius);
    const y = clamp(preferred.y, face.min.y + radius, face.max.y - radius);
    for (const [cx, cy] of [[x, y], [center.x, y], [x, center.y], [center.x, center.y]] as const) {
      if (onFace(cx - radius, cy - radius) && onFace(cx + radius, cy - radius) &&
          onFace(cx - radius, cy + radius) && onFace(cx + radius, cy + radius)) {
        return { local: new Vector3(cx, cy, face.max.z + surfaceOffset), face, size };
      }
    }
  }
}

/** World-attached inscriptions and one bounded point pool, owned by the prototype. */
export function createPillarMagic(scene: Scene, chapter?: { column: string; number: string; stations: readonly { id: string }[]; poses: readonly TourPose[] }) {
  scene.updateMatrixWorld(true);
  const canvas = document.createElement('canvas');
  canvas.width = 384;canvas.height = 128;
  const ctx = canvas.getContext('2d');
  if (!ctx) return undefined;
  for (let i = 0; i < 3; i++) {
    ctx.save();ctx.translate(i * 128, 0);ctx.strokeStyle = '#fff';ctx.fillStyle = '#fff';ctx.lineWidth = 6;ctx.lineCap = 'square';
    ctx.shadowColor = 'rgba(255,255,255,.42)';ctx.shadowBlur = 7;
    ctx.beginPath();ctx.arc(64, 52, 40, -.65 * Math.PI, 1.08 * Math.PI);ctx.stroke();
    ctx.beginPath();ctx.moveTo(64, 5);ctx.lineTo(64, 24);ctx.moveTo(64, 77);ctx.lineTo(64, 94);ctx.stroke();
    ctx.lineWidth = 3;
    for (let tick = 0; tick < 3; tick++) { const x = 51 + tick * 13;ctx.globalAlpha = tick <= i ? 1 : .25;ctx.beginPath();ctx.moveTo(x, 42);ctx.lineTo(x, 58);ctx.stroke(); }
    ctx.globalAlpha = 1;ctx.shadowBlur = 2;ctx.font = '18px Georgia, serif';ctx.textAlign = 'center';ctx.fillText(chapter?.number ?? '01', 64, 117);ctx.restore();
  }
  const atlas = new CanvasTexture(canvas);atlas.name = 'pillar-sigil-atlas';atlas.generateMipmaps = false;atlas.minFilter = LinearFilter;atlas.magFilter = LinearFilter;
  const geometry = new PlaneGeometry(magicStyle.sigilSize, magicStyle.sigilSize);
  geometry.setAttribute('aSeed', new BufferAttribute(new Float32Array(4), 1));geometry.setAttribute('aRank', new BufferAttribute(new Float32Array(4), 1));
  const uniforms = (index: number, dust: number) => ({
    uAtlas: { value: atlas }, uIndex: { value: index }, uDust: { value: dust }, uTrace: { value: 0 }, uWake: { value: 0 }, uLod: { value: 0 },
    uTime: { value: 0 }, uCount: { value: 0 }, uOpacity: { value: 0 }, uDisperse: { value: 0 }, uPointSize: { value: 1 },
    uCool: { value: new Color(magicStyle.cool) }, uGold: { value: new Color(magicStyle.gold) }, uEtch: { value: new Color(magicStyle.etch) }, uLilac: { value: new Color(magicStyle.lilac) },
  });
  const sigils: { mesh: Mesh<PlaneGeometry, ShaderMaterial>; anchor: Vector3; metadata: { station: string; stone: string; local: number[]; faceBounds: number[][]; size: number; offset: number } }[] = [];
  const ray = new Raycaster();
  const materials: ShaderMaterial[] = [];
  const column = chapter?.column ?? 'columnUpperLeft';
  const candidates: Mesh[] = [];
  scene.getObjectByName(`${column}-shaft`)?.traverse(object => {
    if (object instanceof Mesh && object.name.startsWith(`${column}-block-`)) candidates.push(object);
  });
  try {
    for (const [i, station] of (chapter?.stations ?? readingStations).entries()) {
      const base = chapter ? chapter.poses[i]! : tourPoses[i === 0 ? 'A' : i === 1 ? 'A2' : 'A3'];
      const eye = new Vector3(...base.position), target = new Vector3(...base.target);
      ray.set(eye, target.clone().sub(eye).normalize());
      const hit = ray.intersectObjects(candidates, false)[0];
      if (!hit || !(hit.object instanceof Mesh)) throw new Error(`Missing inscription surface for ${station.id}.`);
      const stone = hit.object;
      const fit = fitInscription(stone, hit.point);
      if (!fit) throw new Error(`Inscription does not fit ${stone.name}.`);
      const { local, face, size } = fit;
      const material = new ShaderMaterial({ vertexShader: vertex, fragmentShader: fragment, transparent: true, depthTest: true, depthWrite: false, toneMapped: false, uniforms: uniforms(Math.min(i, 2), 0) });
      material.name = 'pillar-sigil-ink';materials.push(material);
      const mesh = new Mesh(geometry, material);mesh.name = `pillar-sigil-${station.id}`;mesh.position.copy(local);mesh.scale.setScalar(size / magicStyle.sigilSize);mesh.castShadow = false;mesh.receiveShadow = false;stone.add(mesh);mesh.updateMatrixWorld(true);
      const anchor = mesh.localToWorld(new Vector3(0, (0.5 - 52 / 128) * magicStyle.sigilSize, 0));
      const metadata = { station: station.id, stone: stone.name, local: local.toArray(), faceBounds: [face.min.toArray(), face.max.toArray()], size, offset: magicStyle.surfaceOffset };
      mesh.userData.inscription = metadata;sigils.push({ mesh, anchor, metadata });
    }
  } catch (error) {
    for (const item of sigils) item.mesh.removeFromParent();
    for (const material of materials) material.dispose();geometry.dispose();atlas.dispose();throw error;
  }
  const capacity = window.innerWidth <= 1000 ? magicStyle.mobilePool : magicStyle.pool;
  const positions = new Float32Array(capacity * 3), seeds = new Float32Array(capacity), ranks = new Float32Array(capacity);
  let seed = 0x51a7;
  const random = () => { seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;return seed / 4294967296; };
  for (let i = 0; i < capacity; i++) { const angle = random() * Math.PI * 2, radius = .27 + .09 * random();positions.set([Math.cos(angle) * radius, Math.sin(angle) * radius * .9, .018 + .025 * random()], i * 3);seeds[i] = random();ranks[i] = i; }
  const normals = new Float32Array(capacity * 3);
  for (let i = 0; i < capacity; i++) normals[i * 3 + 2] = 1;
  const dustGeometry = new BufferGeometry();dustGeometry.setAttribute('position', new BufferAttribute(positions, 3));dustGeometry.setAttribute('normal', new BufferAttribute(normals, 3));dustGeometry.setAttribute('aSeed', new BufferAttribute(seeds, 1));dustGeometry.setAttribute('aRank', new BufferAttribute(ranks, 1));dustGeometry.setAttribute('uv', new BufferAttribute(new Float32Array(capacity * 2), 2));
  const dustMaterial = new ShaderMaterial({ vertexShader: vertex, fragmentShader: fragment, transparent: true, depthTest: true, depthWrite: false, toneMapped: false, uniforms: uniforms(0, 1) });
  dustMaterial.name = 'pillar-light-dust';
  const dust = new Points(dustGeometry, dustMaterial);dust.name = chapter ? `pillar-light-dust-${chapter.number}` : 'pillar-light-dust';dust.frustumCulled = false;dust.visible = false;scene.add(dust);
  let disposed = false;
  const metadata = { anchors: sigils.map((item) => item.metadata), pool: capacity, geometries: 2, textures: 1, programFamilies: 1 };
  return {
    metadata,
    getAnchor(id: string) { return sigils.find((item) => item.metadata.station === id)?.anchor; },
    update(reading: MagicReadingFrame | undefined, camera: OrthographicCamera, time: number, reducedMotion: boolean, mode: RenderMode) {
      if (disposed) return;
      const state = sampleMagic(reading, reducedMotion);
      const active = sigils.find((item) => item.metadata.station === reading?.station.id);
      const size = (active?.metadata.size ?? magicStyle.sigilSize) / (camera.right - camera.left) * window.innerWidth;
      const lod = clamp((size - 16) / 12, 0, 1);
      for (const item of sigils) {
        const active = item.metadata.station === reading?.station.id;
        item.mesh.visible = active && state.glyph > .000001;
        item.mesh.material.uniforms.uWake!.value = active ? state.glyph : 0;
        item.mesh.material.uniforms.uTrace!.value = active ? state.trace : 0;
        item.mesh.material.uniforms.uLod!.value = active ? lod * state.glyph : 0;
      }
      const mobile = window.innerWidth <= 1000;
      const steady = mobile ? magicStyle.mobileReadCount : magicStyle.readCount;
      const pool = Math.min(capacity, mobile ? magicStyle.mobilePool : magicStyle.pool);
      dustGeometry.setDrawRange(0, pool);
      dust.visible = !!active && state.dust > .000001 && !reducedMotion;
      if (active) {
        active.mesh.getWorldPosition(dust.position);active.mesh.getWorldQuaternion(dust.quaternion);
        dust.scale.setScalar(active.metadata.size / magicStyle.sigilSize);
      }
      const uniforms = dustMaterial.uniforms;
      uniforms.uTime!.value = time;uniforms.uCount!.value = steady + (pool - steady) * state.burst;uniforms.uOpacity!.value = state.dust * .72;uniforms.uDisperse!.value = state.disperse;
      uniforms.uPointSize!.value = mode === 'pixel' ? 1.1 : 1.8 * Math.min(devicePixelRatio, 2);
      return { ...state, dustCapacity: pool, dustVisible: dust.visible ? Math.ceil(Number(uniforms.uCount!.value)) : 0, time, lod };
    },
    dispose() {
      if (disposed) return;disposed = true;
      for (const item of sigils) item.mesh.removeFromParent();
      for (const material of materials) material.dispose();
      dust.removeFromParent();dustGeometry.dispose();dustMaterial.dispose();geometry.dispose();atlas.dispose();
    },
  };
}
