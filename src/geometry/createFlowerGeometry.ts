import { BufferGeometry, Float32BufferAttribute } from 'three';

function plantGeometry(positions: number[], parts: number[], heights: number[]) {
  const geometry = new BufferGeometry();
  geometry.setAttribute('position', new Float32BufferAttribute(positions, 3));
  geometry.setAttribute('plantPart', new Float32BufferAttribute(parts, 1));
  geometry.setAttribute('plantHeight', new Float32BufferAttribute(heights, 1));
  geometry.computeVertexNormals();
  geometry.computeBoundingBox();
  geometry.computeBoundingSphere();
  return geometry;
}

type Point = readonly [number, number, number];
function builder() {
  const positions: number[] = [], parts: number[] = [], heights: number[] = [];
  function triangle(a: Point, b: Point, c: Point, part = 0) {
    for (const p of [a, b, c]) {
      positions.push(...p);
      parts.push(part);
      heights.push(p[1]);
    }
  }
  return { triangle, finish: () => plantGeometry(positions, parts, heights) };
}

export function createGrassGeometry() {
  const b = builder();
  for (let i = 0; i < 3; i++) {
    const angle = i * Math.PI * 2 / 3;
    const c = Math.cos(angle), s = Math.sin(angle);
    const height = i === 0 ? 1 : 0.72 + i * 0.08;
    const point = (x: number, y: number, z: number): Point => [c * x - s * z, y, s * x + c * z];
    const left = point(-0.12, 0, 0), right = point(0.12, 0, 0);
    const shoulder = point(0.08, height * 0.6, 0.10);
    const tip = point(0.23, height, 0.18);
    b.triangle(left, right, shoulder);
    b.triangle(left, shoulder, tip);
  }
  return b.finish();
}

export function createStemGeometry() {
  const b = builder();
  b.triangle([-0.025, 0, 0], [0.025, 0, 0], [0.025, 1, 0]);
  b.triangle([-0.025, 0, 0], [0.025, 1, 0], [-0.025, 1, 0]);
  b.triangle([0, 0, -0.025], [0, 0, 0.025], [0, 1, 0.025]);
  b.triangle([0, 0, -0.025], [0, 1, 0.025], [0, 1, -0.025]);
  b.triangle([0, 0.4, 0], [0.18, 0.65, 0.04], [0.04, 0.63, -0.04]);
  b.triangle([0, 0.56, 0], [-0.17, 0.77, -0.02], [-0.04, 0.76, 0.05]);
  return b.finish();
}

export function createFlowerGeometry(petals: 4 | 5) {
  const b = builder();
  for (let i = 0; i < petals; i++) {
    const angle = i * Math.PI * 2 / petals;
    const point = (radius: number, offset: number, y: number): Point => [Math.cos(angle + offset) * radius, y, Math.sin(angle + offset) * radius];
    const root = point(0.07, 0, 0), left = point(0.33, -0.48, 0.035);
    const tip = point(0.5, 0, 0.08), right = point(0.33, 0.48, 0.035);
    b.triangle(root, tip, left);
    b.triangle(root, right, tip);
  }
  const a: Point = [-0.085, 0.05, 0], c: Point = [0.085, 0.05, 0];
  b.triangle(a, [0, 0.05, 0.085], c, 1);
  b.triangle(a, c, [0, 0.05, -0.085], 1);
  return b.finish();
}
