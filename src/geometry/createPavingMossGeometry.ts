import { BufferGeometry, Color, Float32BufferAttribute, Ray, Vector3 } from 'three';
import { pavingMossColors } from '../config/pavingMoss';
import type { MossPatch, MossPoint } from '../config/pavingMoss';
import { applyStoneTint } from './createStoneBlockGeometry';

const baseColor = new Color(pavingMossColors.base);
const tipColor = new Color(pavingMossColors.light);
const edgeColor = new Color(pavingMossColors.edge);
const embed = 0.002;

/** Build closed moss lobes from the actual stone surface in its local coordinates. */
export function createPavingMossGeometry(stone: BufferGeometry, patch: MossPatch) {
  const stonePositions = stone.getAttribute('position');
  const stoneNormals = stone.getAttribute('normal');
  const [anchorX, anchorZ] = patch.anchor;
  const ray = new Ray(new Vector3(), new Vector3(0, -1, 0));
  const a = new Vector3(), b = new Vector3(), c = new Vector3(), hit = new Vector3();

  function support([x, z]: MossPoint) {
    ray.origin.set(anchorX + x, (stone.boundingBox?.max.y ?? 0) + 1, anchorZ + z);
    let point: Vector3 | undefined;
    let face = 0;
    for (let i = 0; i < stonePositions.count; i += 3) {
      a.fromBufferAttribute(stonePositions, i);
      b.fromBufferAttribute(stonePositions, i + 1);
      c.fromBufferAttribute(stonePositions, i + 2);
      if (ray.intersectTriangle(a, b, c, true, hit) && (!point || hit.y > point.y)) {
        (point ??= new Vector3()).copy(hit);
        face = i;
      }
    }
    return point ? { point, normal: new Vector3().fromBufferAttribute(stoneNormals, face) } : undefined;
  }

  const positions: number[] = [];
  const colors: number[] = [];
  function triangle(a: Vector3, b: Vector3, c: Vector3, first: Color, second: Color, third: Color) {
    positions.push(a.x, a.y, a.z, b.x, b.y, b.z, c.x, c.y, c.z);
    colors.push(first.r, first.g, first.b, second.r, second.g, second.b, third.r, third.g, third.b);
  }

  for (const lobe of patch.lobes) {
    const center = support(lobe.peak);
    // Authored outlines run counterclockwise in XZ. Reverse them for the +Y face.
    const rim = [...lobe.outline].reverse().map(support);
    if (!center || rim.some(vertex => !vertex)) continue;
    const surface = rim.map(vertex => vertex!.point);
    const { normal } = center;
    // A lobe belongs to one planar face. Adjacent faces use their own lobes.
    const surfacePlane = normal.dot(center.point);
    if (surface.some(point => Math.abs(normal.dot(point) - surfacePlane) > 0.00001)) continue;
    const root = center.point.clone().addScaledVector(normal, -embed);
    const crown = center.point.clone().addScaledVector(normal, lobe.rise);
    const bottom = surface.map(point => point.clone().addScaledVector(normal, -embed));
    const top = surface.map((point, i) => point.clone().addScaledVector(normal, lobe.rim + i % 3 * 0.001));
    const rimColors = surface.map((_, i) => baseColor.clone().lerp(tipColor, (i % 4) * 0.10));
    for (let i = 0; i < surface.length; i++) {
      const j = (i + 1) % surface.length;
      triangle(crown, top[i]!, top[j]!, tipColor, rimColors[i]!, rimColors[j]!);
      triangle(root, bottom[j]!, bottom[i]!, edgeColor, edgeColor, edgeColor);
      triangle(bottom[i]!, bottom[j]!, top[j]!, edgeColor, edgeColor, rimColors[j]!);
      triangle(bottom[i]!, top[j]!, top[i]!, edgeColor, rimColors[j]!, rimColors[i]!);
    }
  }

  if (!positions.length) return undefined;
  const geometry = new BufferGeometry();
  geometry.setAttribute('position', new Float32BufferAttribute(positions, 3));
  geometry.setAttribute('color', new Float32BufferAttribute(colors, 3));
  geometry.computeVertexNormals();
  geometry.computeBoundingSphere();
  return applyStoneTint(geometry, 19);
}
