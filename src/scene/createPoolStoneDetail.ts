import { Matrix4, Mesh, Vector3 } from 'three';
import type { BufferGeometry, Group, Material } from 'three';
import { layoutConfig } from '../config/layout';
import type { MossPatch } from '../config/pavingMoss';
import { createPavingMossGeometry } from '../geometry/createPavingMossGeometry';
import { createStonePrismGeometry } from '../geometry/createStoneBlockGeometry';

const pool = layoutConfig.fountain;

const pedestalStones = [
  {
    name: 'fountain-pedestal-foot', size: pool.pedestalFootSize, height: pool.pedestalFootHeight,
    outline: [[-.5, -.406], [-.483, .38], [-.406, .482], [.351, .499], [.494, .381], [.493, -.348], [.406, -.468]],
    options: { bevel: .019, cornerCut: .016, seed: 61, chipSize: .038, chipCorner: 6 },
  },
  {
    name: 'fountain-pedestal', size: pool.pedestalSize, height: pool.pedestalHeight,
    outline: [[-.466, -.43], [-.5, .324], [-.398, .481], [.317, .5], [.498, .341], [.484, -.35], [.38, -.494]],
    options: { bevel: .022, cornerCut: .012, seed: 43, chipSize: .074, chipCorner: 4, tintStrength: 1.35 },
    taper: .09,
  },
  {
    name: 'fountain-pedestal-cap', size: pool.pedestalCapSize, height: pool.pedestalCapHeight,
    outline: [[-.471, -.465], [-.5, .343], [-.433, .477], [.348, .5], [.499, .365], [.483, -.393], [.412, -.484]],
    options: { bevel: .013, cornerCut: .009, seed: 29, chipSize: .064, chipCorner: 4, tintStrength: 1.25 },
  },
] as const;

interface MossSite {
  name: string;
  support: string;
  side: number;
  along: number;
  radius: number;
  elevation: number;
  face: 'inside' | 'outside' | 'top';
  lobes: MossPatch['lobes'];
}

const mossSites: readonly MossSite[] = [
  {
    name: 'fountain-moss-inner-2', support: 'fountain-rim-wall',
    side: 4, along: .87, radius: pool.innerRadius, elevation: .388, face: 'inside',
    lobes: [
      {
        outline: [[-.118, -.008], [-.093, -.029], [-.061, -.027], [-.032, -.04], [.023, -.039], [.062, -.03],
          [.099, -.014], [.088, .006], [.053, .012], [.015, .027], [-.049, .021], [-.083, .025], [-.113, .013]],
        peak: [-.009, -.024], rise: .024, rim: .012,
      },
      {
        outline: [[.06, -.02], [.094, -.039], [.131, -.035], [.15, -.019], [.136, .003], [.102, .008], [.079, -.004]],
        peak: [.108, -.022], rise: .022, rim: .010,
      },
      {
        outline: [[-.129, .016], [-.104, .007], [-.076, .021], [-.076, .032], [-.107, .038], [-.126, .028]],
        peak: [-.106, .022], rise: .013, rim: .006,
      },
    ],
  },
  {
    name: 'fountain-moss-coping-2', support: 'fountain-coping-4-step',
    side: 4, along: .87, radius: pool.innerRadius + .10, elevation: .524, face: 'top',
    lobes: [
      {
        outline: [[-.127, -.023], [-.108, -.052], [-.072, -.061], [-.012, -.051], [.019, -.068], [.065, -.05],
          [.097, -.031], [.113, -.003], [.081, .018], [.055, .041], [.013, .034], [-.035, .05], [-.092, .025]],
        peak: [-.023, -.015], rise: .022, rim: .009,
      },
      {
        outline: [[.071, .029], [.101, .012], [.125, .021], [.131, .037], [.106, .058], [.083, .052]],
        peak: [.1, .036], rise: .013, rim: .006,
      },
    ],
  },
  {
    name: 'fountain-moss-seam-3', support: 'fountain-edge-3-lining-1',
    side: 3, along: .571, radius: pool.innerRadius - .031, elevation: .384, face: 'inside',
    lobes: [
      {
        outline: [[-.071, -.008], [-.057, -.02], [-.036, -.029], [-.016, -.018], [.003, -.012],
          [.011, .002], [-.009, .015], [-.041, .016], [-.063, .008]],
        peak: [-.037, -.01], rise: .019, rim: .008,
      },
      {
        outline: [[.026, .01], [.039, -.004], [.054, -.007], [.069, .006], [.061, .019], [.041, .022]],
        peak: [.047, .008], rise: .012, rim: .005,
      },
    ],
  },
  {
    name: 'fountain-moss-foot', support: 'fountain-edge-1-foot-1',
    side: 5, along: .147, radius: pool.baseRadius - .003, elevation: .066, face: 'outside',
    lobes: [
      {
        outline: [[-.137, -.007], [-.115, -.021], [-.071, -.023], [-.031, -.018], [.012, -.029],
          [.055, -.025], [.084, -.009], [.112, .003], [.088, .018], [.042, .023], [-.001, .018],
          [-.048, .028], [-.091, .018], [-.126, .012]],
        peak: [-.02, -.002], rise: .016, rim: .006,
      },
    ],
  },
];

type OwnGeometry = (geometry: BufferGeometry) => BufferGeometry;

function addPedestal(fountain: Group, material: Material, own: OwnGeometry) {
  let bottom = pool.baseHeight;
  for (const spec of pedestalStones) {
    const outline = spec.outline.map(([x, z]): [number, number] => [x * spec.size, z * spec.size]);
    const geometry = createStonePrismGeometry(outline, spec.height, spec.options);
    if ('taper' in spec) {
      const positions = geometry.getAttribute('position');
      for (let i = 0; i < positions.count; i++) {
        const scale = 1 - spec.taper * (positions.getY(i) / spec.height + .5);
        positions.setX(i, positions.getX(i) * scale);
        positions.setZ(i, positions.getZ(i) * scale);
      }
      geometry.computeVertexNormals();
      geometry.computeBoundingBox();
      geometry.computeBoundingSphere();
    }
    const mesh = new Mesh(own(geometry), material);
    mesh.name = spec.name;
    mesh.position.y = bottom + spec.height / 2;
    mesh.castShadow = mesh.receiveShadow = true;
    fountain.add(mesh);
    bottom += spec.height;
  }
}

function addMoss(fountain: Group, material: Material, own: OwnGeometry) {
  fountain.updateWorldMatrix(true, true);
  const step = Math.PI / 4;
  for (const site of mossSites) {
    const stone = fountain.getObjectByName(site.support);
    if (!(stone instanceof Mesh)) continue;
    const a = site.side * step, b = a + step;
    const anchor = new Vector3(site.radius * Math.cos(a), site.elevation, -site.radius * Math.sin(a))
      .lerp(new Vector3(site.radius * Math.cos(b), site.elevation, -site.radius * Math.sin(b)), site.along);
    const faceAngle = a + step / 2;
    const worldToStone = stone.matrixWorld.clone().invert();
    const fromPool = worldToStone.multiply(fountain.matrixWorld);
    const outward = new Vector3(Math.cos(faceAngle), 0, -Math.sin(faceAngle));
    if (site.face === 'inside') outward.negate();
    const up = new Vector3(0, 1, 0);
    const tangent = up.clone().cross(outward).transformDirection(fromPool);
    const normal = (site.face === 'top' ? up : outward).transformDirection(fromPool);
    const across = tangent.clone().cross(normal);
    const placement = new Matrix4().makeBasis(tangent, normal, across).setPosition(anchor.applyMatrix4(fromPool));
    const surface = stone.geometry.clone().applyMatrix4(placement.clone().invert());
    // Start just in front of this face so a ray cannot hit the opposite pool wall.
    const relief = createPavingMossGeometry(surface, { anchor: [0, 0], lobes: site.lobes }, 'top', .06);
    surface.dispose();
    if (!relief) continue;
    const moss = new Mesh(own(relief.applyMatrix4(placement)), material);
    moss.name = site.name;
    moss.castShadow = moss.receiveShadow = true;
    stone.add(moss);
  }
}

export function createPoolStoneDetail(fountain: Group, stone: Material, moss: Material, own: OwnGeometry) {
  addPedestal(fountain, stone, own);
  addMoss(fountain, moss, own);
}
