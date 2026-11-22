import { ExtrudeGeometry, Group, Matrix4, Mesh, Path, Shape } from 'three';
import type { BufferGeometry, Material } from 'three';
import { fountainShelf } from '../config/fountain';
import { layoutConfig } from '../config/layout';
import { poolEdges } from '../config/poolMasonry';
import type { PoolEdge } from '../config/poolMasonry';
import { applyStoneTint, createStonePrismGeometry } from '../geometry/createStoneBlockGeometry';

type Point = readonly [number, number];
type Span = readonly [start: number, end: number];
type Band = 'foot' | 'lower' | 'upper' | 'lining' | 'crown' | 'shelf';
const angle = Math.PI / 4;
const f = layoutConfig.fountain;

function corner(radius: number, side: number): Point {
  return [radius * Math.cos(side * angle), -radius * Math.sin(side * angle)];
}

function alongEdge(radius: number, side: number, fraction: number): Point {
  const a = corner(radius, side), b = corner(radius, side + 1);
  return [a[0] + (b[0] - a[0]) * fraction, a[1] + (b[1] - a[1]) * fraction];
}

function spans(joint?: number): Span[] {
  return joint === undefined ? [[0, 1]] : [[0, joint], [joint, 1]];
}

/** Each edge ends at its original miter. Only the joint inside an edge can lean. */
function footprint(side: number, outer: number, inner: number, [start, end]: Span, gap: number, skew = 0): Point[] {
  const inset = (radius: number) => gap / (4 * radius * Math.sin(angle / 2));
  const outerInset = inset(outer), innerInset = inset(inner);
  return [
    alongEdge(outer, side, start + outerInset),
    alongEdge(outer, side, end - outerInset),
    alongEdge(inner, side, end - innerInset + (end < 1 ? skew : 0)),
    alongEdge(inner, side, start + innerInset + (start > 0 ? skew : 0)),
  ];
}

function cutCorner(points: Point[], cut: NonNullable<PoolEdge['crown']['cut']>): Point[] {
  const { corner: index, inward, along } = cut;
  const a = points[index]!;
  const previous = points[(index + points.length - 1) % points.length]!;
  const next = points[(index + 1) % points.length]!;
  function inset(b: Point, length: number): Point {
    const dx = b[0] - a[0], dz = b[1] - a[1];
    const t = length / Math.hypot(dx, dz);
    return [a[0] + dx * t, a[1] + dz * t];
  }
  return [
    ...points.slice(0, index), inset(previous, index === 0 ? inward : along),
    inset(next, index === 0 ? along : inward), ...points.slice(index + 1),
  ];
}

function ringPath(path: Path, radius: number, direction: number) {
  path.moveTo(radius, 0);
  for (let i = 1; i < 8; i++) {
    const [x, z] = corner(radius, i * direction);
    path.lineTo(x, -z);
  }
  path.closePath();
}

/** The outer courses have real joints backed by one continuous inner wall. */
export function createPoolMasonry(fountain: Group, material: Material, own: (geometry: BufferGeometry) => BufferGeometry) {
  const rim = new Group();
  rim.name = 'fountain-rim';
  fountain.add(rim);

  function place(parent: Group, name: string, geometry: BufferGeometry, y: number) {
    const stone = new Mesh(own(geometry), material);
    stone.name = name;
    stone.position.y = y;
    stone.castShadow = stone.receiveShadow = true;
    parent.add(stone);
    return stone;
  }

  const base = Array.from({ length: 8 }, (_, side) => corner(f.baseRadius - .083, side));
  place(fountain, 'fountain-base', createStonePrismGeometry(base, f.baseHeight, {
    bevel: .015, cornerCut: .022, seed: 11,
  }), f.baseHeight / 2);

  const copingTop = f.baseHeight + f.rimHeight;
  const copingBed = copingTop - .148;
  const liningBottom = f.baseHeight - .006;
  const lining = new Shape();
  const opening = new Path();
  ringPath(lining, f.outerRadius - .131, 1);
  ringPath(opening, f.innerRadius, -1);
  lining.holes.push(opening);
  const liningDepth = copingBed + .010 - liningBottom;
  const core = place(rim, 'fountain-rim-wall', applyStoneTint(new ExtrudeGeometry(lining, {
    depth: liningDepth, bevelEnabled: false, steps: 1, curveSegments: 1,
  }), 17), liningBottom);
  core.rotation.x = -Math.PI / 2;

  poolEdges.forEach((edge, index) => {
    const group = new Group();
    group.name = `fountain-edge-${index + 1}`;
    rim.add(group);

    function placeEdgeStone(name: string, band: Band, geometry: BufferGeometry, y: number) {
      const stone = place(group, name, geometry, y);
      stone.userData.poolEdge = index + 1;
      stone.userData.poolBand = band;
    }

    const bands = [
      // Seat the flared soles below the lawn so their bevels reach the grass.
      { kind: 'foot', profile: edge.foot, outer: f.baseRadius, inner: f.innerRadius + .26,
        bottom: -.016, top: f.baseHeight + edge.foot.rise, gap: .025, bevel: .015 },
      { kind: 'lower', profile: edge.lower, outer: f.outerRadius, inner: f.innerRadius + .13,
        bottom: f.baseHeight - .005, top: edge.bed, gap: .028, bevel: .017 },
      { kind: 'upper', profile: edge.upper, outer: f.outerRadius, inner: f.innerRadius + .13,
        bottom: edge.bed + .011, top: copingBed + .005, gap: .030, bevel: .022 },
    ] as const;
    for (const band of bands) {
      const { profile, kind, bottom, top } = band;
      spans(profile.joint).forEach((span, part) => {
        const points = footprint(edge.side, band.outer + profile.spread, band.inner, span, band.gap, profile.skew);
        const geometry = createStonePrismGeometry(points, top - bottom, {
          bevel: band.bevel, cornerCut: .013,
          chipSize: part === 0 ? profile.wear : undefined, chipCorner: 1,
          seed: 37 + index * 19 + part * 13 + (kind === 'foot' ? 1 : Math.round(bottom * 100)),
          tintStrength: kind === 'foot' ? 1.5 : 2.65,
        });
        placeEdgeStone(`${group.name}-${kind}-${part + 1}`, kind, geometry, (bottom + top) / 2);
      });
    }

    if (edge.innerJoint) {
      const [start, joint, end] = edge.innerJoint;
      const wallSpans = [[start, joint], [joint, end]] as const;
      const bottom = f.waterHeight + .003, top = copingBed + .004;
      wallSpans.forEach((span, part) => {
        const points = footprint(edge.side, f.innerRadius + .025, f.innerRadius - .031, span, .030);
        const geometry = createStonePrismGeometry(points, top - bottom, {
          bevel: .007, cornerCut: .005, seed: 79 + part * 13, tintStrength: 1.4,
        });
        placeEdgeStone(`${group.name}-lining-${part + 1}`, 'lining', geometry, (bottom + top) / 2);
      });
    }

    if (edge.side === fountainShelf.side) {
      const { origin, tangent, edgeLength, bedInset, thickness } = fountainShelf;
      const inward: Point = [tangent[1], -tangent[0]];
      fountainShelf.stones.forEach(({ span, reach, bankY, lipY, fall, cut }, piece) => {
        const start = span[0] * edgeLength, end = span[1] * edgeLength;
        const [firstRun, firstDepth, lastRun, lastDepth] = cut;
        const profile: Point[] = [
          [start, -bedInset], [end, -bedInset], [end, reach - lastDepth],
          [end - lastRun, reach], [start + firstRun, reach], [start, reach - firstDepth],
        ];
        const outline = profile.map(([along, depth]): Point => [
          origin[0] + tangent[0] * along + inward[0] * depth,
          origin[1] + tangent[1] * along + inward[1] * depth,
        ]);
        const slope = (lipY - bankY) / reach;
        const twist = fall / (end - start);
        const gradeX = slope * inward[0] + twist * tangent[0];
        const gradeZ = slope * inward[1] + twist * tangent[1];
        const grade = new Matrix4().set(
          1, 0, 0, 0,
          gradeX, 1, gradeZ, -gradeX * origin[0] - gradeZ * origin[1] - twist * (start + end) / 2,
          0, 0, 1, 0,
          0, 0, 0, 1,
        );
        const geometry = createStonePrismGeometry(outline, thickness, {
          bevel: .009, cornerCut: .004, seed: 331 + piece * 47, tintStrength: 1.4,
        }).applyMatrix4(grade);
        placeEdgeStone(`${group.name}-shelf-${piece + 1}`, 'shelf', geometry, bankY - thickness / 2);
      });
    }

    const crown = edge.crown;
    spans(crown.joint).forEach((span, part) => {
      const small = crown.smallStone;
      const secondary = small && part === (small.end === 'start' ? 0 : 1) ? small : undefined;
      const top = copingTop + crown.rise + (secondary?.rise ?? 0);
      const height = top - copingBed;
      const points = footprint(edge.side, f.outerRadius + crown.spread, f.innerRadius, span, .029, crown.skew);
      const name = `fountain-coping-${edge.side}${secondary ? `-${secondary.name}` : ''}`;
      const geometry = createStonePrismGeometry(crown.cut ? cutCorner(points, crown.cut) : points, height, {
        bevel: crown.bevel, cornerCut: .017, chipSize: crown.chip, chipCorner: crown.cut ? 1 : 2,
        seed: 23 + index * 29 + part * 17, tintStrength: 1.65,
      });
      placeEdgeStone(name, 'crown', geometry, copingBed + height / 2);
    });
  });
}
