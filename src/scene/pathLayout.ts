import { layoutConfig } from '../config/layout';

type PointXZ = readonly [x: number, z: number];

const path = layoutConfig.path;
const pathCos = Math.cos(path.rotationY);
const pathSin = Math.sin(path.rotationY);

export function pathPointToWorld(x: number, z: number): PointXZ {
  return [path.position[0] + pathCos * x + pathSin * z, path.position[2] - pathSin * x + pathCos * z];
}

export const pathStones = path.stones.map(stone => {
  const halfWidth = stone.width / 2;
  const halfDepth = stone.depth / 2;
  const [first, second, third, fourth] = stone.cuts;
  const outline: readonly PointXZ[] = [
    [-halfWidth + first, -halfDepth],
    [halfWidth - second, -halfDepth],
    [halfWidth, -halfDepth + second],
    [halfWidth, halfDepth - third],
    [halfWidth - third, halfDepth],
    [-halfWidth + fourth, halfDepth],
    [-halfWidth, halfDepth - fourth],
    [-halfWidth, -halfDepth + first],
  ];
  const rotationY = stone.rotationDegrees * Math.PI / 180;
  const cos = Math.cos(rotationY), sin = Math.sin(rotationY);
  const [centerX, centerZ] = stone.center;
  const worldOutline = outline.map(([x, z]) => pathPointToWorld(centerX + cos * x + sin * z, centerZ - sin * x + cos * z));
  const xs = worldOutline.map(([x]) => x);
  const zs = worldOutline.map(([, z]) => z);
  const bounds = { minX: Math.min(...xs), maxX: Math.max(...xs), minZ: Math.min(...zs), maxZ: Math.max(...zs) };
  return { id: stone.id, center: stone.center, profile: stone.profile, rotationY, outline, worldOutline, bounds };
});

/** Check the circle around a root against the stone outlines at grass level. */
export function isPathPositionClear(x: number, z: number, clearance: number) {
  const clearanceSquared = clearance ** 2;
  for (const { worldOutline, bounds } of pathStones) {
    if (x < bounds.minX - clearance || x > bounds.maxX + clearance
      || z < bounds.minZ - clearance || z > bounds.maxZ + clearance) continue;

    let inside = true;
    for (let i = 0; i < worldOutline.length; i++) {
      const [ax, az] = worldOutline[i]!;
      const [bx, bz] = worldOutline[(i + 1) % worldOutline.length]!;
      const edgeX = bx - ax, edgeZ = bz - az;
      const dx = x - ax, dz = z - az;
      if (edgeX * dz - edgeZ * dx < 0) inside = false;
      const along = (dx * edgeX + dz * edgeZ) / (edgeX * edgeX + edgeZ * edgeZ);
      const closest = Math.max(0, Math.min(1, along));
      if ((dx - edgeX * closest) ** 2 + (dz - edgeZ * closest) ** 2 <= clearanceSquared) return false;
    }
    if (inside) return false;
  }
  return true;
}
