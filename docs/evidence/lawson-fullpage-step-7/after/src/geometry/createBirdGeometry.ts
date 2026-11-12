import { BufferGeometry, Color, Float32BufferAttribute, Vector3 } from 'three';
import { birdConfig } from '../config/birds';

type Point = readonly [number, number, number];
/** Solid, positively oriented low-poly pieces, including the undersides. */
export function createBirdGeometry(part: 'body' | 'left' | 'right' | 'all') {
  const positions: number[] = [], colors: number[] = [], parts: number[] = [];
  let activePart = 0;
  const palette = Object.fromEntries(Object.entries(birdConfig.colors).map(([k, v]) => [k, new Color(v)]));
  const a = new Vector3(), b = new Vector3(), normal = new Vector3();
  function triangle(p: Point, q: Point, r: Point, accent?: string) {
    a.set(q[0] - p[0], q[1] - p[1], q[2] - p[2]);b.set(r[0] - p[0], r[1] - p[1], r[2] - p[2]);normal.crossVectors(a, b).normalize();
    const color = palette[accent ?? (normal.y > .3 ? 'light' : normal.y < -.3 ? 'cool' : 'warm')]!;
    for (const v of [p, q, r]) { positions.push(...v);colors.push(color.r, color.g, color.b);parts.push(activePart); }
  }
  function convex(vertices: Point[], faces: number[][], accent?: string) {
    const center = vertices.reduce((o, v) => o.add(new Vector3(...v)), new Vector3()).divideScalar(vertices.length);
    for (const [i, j, k] of faces) {
      const p = vertices[i!]!, q = vertices[j!]!, r = vertices[k!]!;
      a.set(q[0] - p[0], q[1] - p[1], q[2] - p[2]);b.set(r[0] - p[0], r[1] - p[1], r[2] - p[2]);normal.crossVectors(a, b);
      if (normal.dot(new Vector3(...p).sub(center)) < 0) triangle(p, r, q, accent);else triangle(p, q, r, accent);
    }
  }
  function prism(points: Array<readonly [number, number]>, y: number, thickness: number, tip = false) {
    let area = 0;for (let i = 0; i < points.length; i++) { const p = points[i]!, q = points[(i + 1) % points.length]!;area += p[0] * q[1] - q[0] * p[1]; }
    if (area > 0) points.reverse();
    const top = points.map(([x, z]) => [x, y + thickness / 2, z] as Point), bottom = points.map(([x, z]) => [x, y - thickness / 2, z] as Point);
    for (let i = 1; i < points.length - 1; i++) { triangle(top[0]!, top[i]!, top[i + 1]!, tip && i === 2 ? 'tip' : 'warm');triangle(bottom[0]!, bottom[i + 1]!, bottom[i]!, 'cool'); }
    for (let i = 0; i < points.length; i++) { const j = (i + 1) % points.length;triangle(top[i]!, bottom[i]!, bottom[j]!, 'cool');triangle(top[i]!, bottom[j]!, top[j]!, 'cool'); }
  }
  if (part === 'body' || part === 'all') {
    convex([[0, .02, .245], [0, .02, -.225], [.085, .02, 0], [-.085, .02, 0], [0, .105, .005], [0, -.065, -.005]],
      [[4, 0, 2], [4, 2, 1], [4, 1, 3], [4, 3, 0], [5, 2, 0], [5, 1, 2], [5, 3, 1], [5, 0, 3]]);
    convex([[0, .115, .28], [-.055, .025, .20], [.055, .025, .20], [0, .035, .37]], [[0, 1, 2], [0, 3, 1], [0, 2, 3], [1, 3, 2]], 'warm');
    convex([[0, .04, .345], [-.025, .025, .32], [.025, .025, .32], [0, .025, .415]], [[0, 1, 2], [0, 3, 1], [0, 2, 3], [1, 3, 2]], 'beak');
    prism([[0, -.17], [.075, -.34], [0, -.305], [-.075, -.34]], .015, .014);
  }
  if (part !== 'body') for (const side of part === 'all' ? [-1, 1] : [part === 'left' ? -1 : 1]) {
    activePart = side;
    prism([[0, .10], [side * .22, .035], [side * .425, -.095], [side * .30, -.19], [side * .05, -.08]], .025, .018, true);
  }
  const geometry = new BufferGeometry();geometry.name = `courtyard-bird-${part}`;
  geometry.setAttribute('position', new Float32BufferAttribute(positions, 3));geometry.setAttribute('color', new Float32BufferAttribute(colors, 3));
  if (part === 'all') geometry.setAttribute('birdPart', new Float32BufferAttribute(parts, 1));
  geometry.computeVertexNormals();geometry.computeBoundingBox();geometry.computeBoundingSphere();
  return geometry;
}
