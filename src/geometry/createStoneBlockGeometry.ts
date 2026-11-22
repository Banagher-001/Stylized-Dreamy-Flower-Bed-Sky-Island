import { BufferGeometry, Float32BufferAttribute, Vector3 } from 'three';

type Point2 = readonly [number, number];
type Polygon = Vector3[];

export interface StoneGeometryOptions {
  bevel: number;
  cornerCut: number;
  seed: number;
  tintStrength?: number;
  chipSize?: number;
  chipCorner?: number;
}

const EPSILON = 1e-7;

function distinct(points: Polygon): Polygon {
  const unique: Polygon = [];
  for (const p of points) {
    if (!unique.some(q => q.distanceToSquared(p) < EPSILON * EPSILON)) unique.push(p);
  }
  return unique;
}

/** Clip a closed convex solid, adding the new exposed face with outward winding. */
function clip(faces: Polygon[], normal: Vector3, distance: number): Polygon[] {
  const next: Polygon[] = [];
  const intersections: Polygon = [];
  for (const face of faces) {
    const polygon: Polygon = [];
    for (let i = 0; i < face.length; i++) {
      const a = face[i]!;
      const b = face[(i + 1) % face.length]!;
      const da = normal.dot(a) - distance;
      const db = normal.dot(b) - distance;
      if (da <= EPSILON) polygon.push(a);
      if ((da < -EPSILON && db > EPSILON) || (da > EPSILON && db < -EPSILON)) {
        const p = a.clone().lerp(b, da / (da - db));
        polygon.push(p);
        intersections.push(p);
      } else if (Math.abs(da) <= EPSILON) {
        intersections.push(a);
      }
    }
    const clean = distinct(polygon);
    if (clean.length >= 3) next.push(clean);
  }
  const cap = distinct(intersections);
  if (cap.length >= 3) {
    const center = cap.reduce((sum, p) => sum.add(p), new Vector3()).divideScalar(cap.length);
    const helper = Math.abs(normal.y) < 0.9 ? new Vector3(0, 1, 0) : new Vector3(1, 0, 0);
    const u = normal.clone().cross(helper).normalize();
    const v = normal.clone().cross(u).normalize();
    cap.sort((a, b) => {
      const pa = a.clone().sub(center);
      const pb = b.clone().sub(center);
      return Math.atan2(pa.dot(v), pa.dot(u)) - Math.atan2(pb.dot(v), pb.dot(u));
    });
    next.push(cap);
  }
  return next;
}

/** Scalar tint is intentionally subtle; the shared art shader applies its strength. */
export function applyStoneTint(geometry: BufferGeometry, seed: number, strength = 1): BufferGeometry {
  const positions = geometry.getAttribute('position');
  const base = Math.sin(seed * 12.9898 + 0.73) * 0.65;
  const tint = new Float32Array(positions.count);
  for (let i = 0; i < positions.count; i++) {
    tint[i] = (base + Math.sin(positions.getX(i) * 1.6 + positions.getZ(i) * 2.3 + seed) * 0.25) * strength;
  }
  geometry.setAttribute('stoneTint', new Float32BufferAttribute(tint, 1));
  return geometry;
}

/** Convex low-poly prism, clipped into planar bevels and a single optional corner chip. */
export function createStonePrismGeometry(outline: readonly Point2[], height: number, options: StoneGeometryOptions): BufferGeometry {
  if (outline.length < 3 || height <= 0) throw new Error('Stone prism needs a polygon and positive height.');
  let points = outline.map(([x, z]) => [x, z] as Point2);
  const area = points.reduce((sum, p, i) => {
    const q = points[(i + 1) % points.length]!;
    return sum + p[0] * q[1] - q[0] * p[1];
  }, 0);
  if (area > 0) points = points.reverse();
  const half = height / 2;
  const top = points.map(([x, z]) => new Vector3(x, half, z));
  const bottom = points.map(([x, z]) => new Vector3(x, -half, z));
  let faces: Polygon[] = [top, [...bottom].reverse()];
  const sides: { normal: Vector3; distance: number }[] = [];
  for (let i = 0; i < points.length; i++) {
    const j = (i + 1) % points.length;
    const a = bottom[i]!;
    const b = bottom[j]!;
    faces.push([a, b, top[j]!, top[i]!]);
    const normal = b.clone().sub(a).cross(new Vector3(0, 1, 0)).normalize();
    sides.push({ normal, distance: normal.dot(a) });
  }
  const bevel = Math.min(options.bevel, height * 0.2);
  for (let i = 0; i < sides.length; i++) {
    const side = sides[i]!;
    for (const sign of [-1, 1]) {
      const n = side.normal.clone().add(new Vector3(0, sign, 0));
      const d = (side.distance + half - bevel) / n.length();
      faces = clip(faces, n.normalize(), d);
    }
    const previous = sides[(i + sides.length - 1) % sides.length]!;
    const n = previous.normal.clone().add(side.normal);
    const d = (previous.distance + side.distance - options.cornerCut) / n.length();
    faces = clip(faces, n.normalize(), d);
  }
  if (options.chipSize && options.chipSize > 0) {
    const index = (options.chipCorner ?? 0) % sides.length;
    const a = sides[(index + sides.length - 1) % sides.length]!;
    const b = sides[index]!;
    const n = a.normal.clone().add(b.normal).add(new Vector3(0, 1, 0));
    const d = (a.distance + b.distance + half - options.chipSize) / n.length();
    faces = clip(faces, n.normalize(), d);
  }

  const vertices: number[] = [];
  const normals: number[] = [];
  for (const face of faces) {
    const center = face.reduce((sum, p) => sum.add(p), new Vector3()).divideScalar(face.length);
    const faceNormal = new Vector3();
    for (let i = 0; i < face.length; i++) {
      faceNormal.add(face[i]!.clone().sub(center).cross(face[(i + 1) % face.length]!.clone().sub(center)));
    }
    if (faceNormal.lengthSq() < EPSILON * EPSILON) continue;
    faceNormal.normalize();
    // A center fan preserves shared boundary vertices, including collinear ones.
    for (let i = 0; i < face.length; i++) {
      const a = face[i]!;
      const b = face[(i + 1) % face.length]!;
      if (a.clone().sub(center).cross(b.clone().sub(center)).lengthSq() < EPSILON * EPSILON) continue;
      for (const p of [center, a, b]) {
        vertices.push(p.x, p.y, p.z);
        normals.push(faceNormal.x, faceNormal.y, faceNormal.z);
      }
    }
  }
  const geometry = new BufferGeometry();
  geometry.setAttribute('position', new Float32BufferAttribute(vertices, 3));
  geometry.setAttribute('normal', new Float32BufferAttribute(normals, 3));
  applyStoneTint(geometry, options.seed, options.tintStrength);
  geometry.computeBoundingBox();
  geometry.computeBoundingSphere();
  geometry.userData.stoneSolid = true;
  return geometry;
}

export function createStoneBlockGeometry(width: number, height: number, depth: number, options: StoneGeometryOptions): BufferGeometry {
  const x = width / 2;
  const z = depth / 2;
  return createStonePrismGeometry([[-x, -z], [-x, z], [x, z], [x, -z]], height, options);
}
