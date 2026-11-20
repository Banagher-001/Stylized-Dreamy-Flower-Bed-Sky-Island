import { BufferGeometry, Color, Float32BufferAttribute, Matrix3, Points, ShaderMaterial, Vector2, Vector3, Vector4 } from 'three';
import { sampleOrbPose } from '../animation/orbMotion';
import { samplePeriodicPhase } from '../animation/orbSurface';
import { lightingConfig } from '../config/lighting';
import { orbConfig, particleOrbFlow, particleOrbWave, type ParticleOrbStyle } from '../config/orb';

const shellCount = 600;
const interiorCount = Math.round(shellCount * .18);
const referenceTime = 2.6001;
const goldenAngle = Math.PI * (3 - Math.sqrt(5));
// Point sprites extend past their centers, so the shell sits inside the nominal radius.
const shellRadius = orbConfig.radius - .013;
const minimumPointSize = 1.30;
const diameter = [.034, .049] as const;
const colors = { body: '#7DB2CD', shade: '#659CBE', light: '#CEE4EE' } as const;

/** Rest positions stay in local space so the same radial field can be sampled each frame. */
export function createParticleOrb(style: ParticleOrbStyle) {
  const waves = style !== 'particles';
  const flow = style === 'particle-flow' || style === 'particle-drops';
  const count = shellCount + interiorCount;
  const positions = new Float32Array(count * 3);
  const directions = new Float32Array(count * 3);
  const layers = new Float32Array(count);
  const diameters = new Float32Array(count);

  function fillLayer(start: number, size: number, inside: boolean) {
    for (let i = 0; i < size; i++) {
      const id = start + i;
      const index = id * 3;
      const y = 2 * (i + .5) / size - 1;
      const turn = i * goldenAngle + (inside ? .7 : 0);
      const ring = Math.sqrt(1 - y * y);
      const x = ring * Math.cos(turn);
      const z = ring * Math.sin(turn);
      const radius = inside
        ? .202 * Math.cbrt((.27 + i * .754877666) % 1)
        : shellRadius + .0028 * Math.sin(i * 2.17);
      positions[index] = x * radius;
      positions[index + 1] = y * radius * orbConfig.shape.yRatio;
      positions[index + 2] = z * radius;
      directions[index] = x;
      directions[index + 1] = y;
      directions[index + 2] = z;
      layers[id] = Number(inside);
      diameters[id] = (diameter[0] + (diameter[1] - diameter[0]) * ((.31 + i * .618033989) % 1)) * (inside ? .86 : 1);
    }
  }
  fillLayer(0, shellCount, false);
  fillLayer(shellCount, interiorCount, true);

  const geometry = new BufferGeometry();
  geometry.setAttribute('position', new Float32BufferAttribute(positions, 3));
  geometry.setAttribute('orbDirection', new Float32BufferAttribute(directions, 3));
  geometry.setAttribute('orbLayer', new Float32BufferAttribute(layers, 1));
  geometry.setAttribute('orbDiameter', new Float32BufferAttribute(diameters, 1));
  geometry.computeBoundingBox();
  geometry.computeBoundingSphere();
  const { primary, secondary, stemFade, interiorFollow } = particleOrbWave;
  const centerY = sampleOrbPose(referenceTime).y;
  const bottomY = centerY + geometry.boundingBox!.min.y;
  const maximumDisplacement = waves ? primary.amplitude + secondary.amplitude : 0;
  geometry.boundingSphere!.radius += diameter[1] / 2 + maximumDisplacement;
  geometry.boundingBox!.expandByScalar(maximumDisplacement);
  const wavePhase = waves ? new Vector2() : undefined;
  let flowBasis: Matrix3 | undefined;
  if (flow) {
    const axis = new Vector3(...particleOrbFlow.axis).normalize();
    const front = new Vector3(...particleOrbFlow.front).projectOnPlane(axis).normalize();
    const tangent = new Vector3().crossVectors(axis, front);
    flowBasis = new Matrix3().set(front.x, front.y, front.z, tangent.x, tangent.y, tangent.z, axis.x, axis.y, axis.z);
  }

  const material = new ShaderMaterial({
    name: 'courtyard-particle-orb',
    transparent: true,
    depthTest: true,
    depthWrite: false,
    toneMapped: false,
    defines: { ...(waves && { ORB_WAVE: 1 }), ...(flow && { ORB_FLOW: 1 }) },
    uniforms: {
      uSampleHeight: { value: 1 },
      uMinimumPointSize: { value: minimumPointSize },
      uSunDirection: { value: new Vector3(...lightingConfig.sun.position).normalize() },
      uBody: { value: new Color(colors.body) },
      uShade: { value: new Color(colors.shade) },
      uLight: { value: new Color(colors.light) },
      ...(wavePhase && {
        uWavePhase: { value: wavePhase },
        uPrimaryWave: { value: new Vector4(...primary.direction, primary.amplitude) },
        uSecondaryWave: { value: new Vector4(...secondary.direction, secondary.amplitude) },
        uStemFade: { value: new Vector2(...stemFade) },
        uInteriorFollow: { value: interiorFollow },
        uOrbYRatio: { value: orbConfig.shape.yRatio },
      }),
      ...(flowBasis && {
        uFlowBasis: { value: flowBasis },
        uFlowOffset: { value: particleOrbFlow.offset },
        uFlowFrontPhase: { value: samplePeriodicPhase(particleOrbFlow.frontTime, primary.period) },
        uFlowCrestWidth: { value: new Vector2(...particleOrbFlow.crestWidth) },
        uFlowBackWeight: { value: particleOrbFlow.backWeight },
        uFlowLight: { value: new Color(particleOrbFlow.colors.crest) },
        uFlowShade: { value: new Color(particleOrbFlow.colors.shade) },
      }),
    },
    vertexShader: /* glsl */`
      attribute vec3 orbDirection;
      attribute float orbLayer;
      attribute float orbDiameter;
      uniform float uSampleHeight;
      uniform float uMinimumPointSize;
      uniform vec3 uSunDirection;
      uniform vec3 uBody;
      uniform vec3 uShade;
      uniform vec3 uLight;
      varying vec3 vColor;
      varying float vOpacity;

      #ifdef ORB_WAVE
        uniform vec2 uWavePhase;
        uniform vec4 uPrimaryWave;
        uniform vec4 uSecondaryWave;
        uniform vec2 uStemFade;
        uniform float uInteriorFollow;
        uniform float uOrbYRatio;

        vec3 displaceOrbPoint(vec3 rest, vec3 direction, float layer) {
          float primary = uPrimaryWave.w * cos(dot(direction, uPrimaryWave.xyz) + uWavePhase.x);
          float secondary = uSecondaryWave.w * sin(dot(direction, uSecondaryWave.xyz) + uWavePhase.y);
          // Keep the lower cap attached to the pedestal's water column.
          float weight = smoothstep(uStemFade.x, uStemFade.y, direction.y) * mix(1.0, uInteriorFollow, layer);
          vec3 ellipticalDirection = direction * vec3(1.0, uOrbYRatio, 1.0);
          return rest + ellipticalDirection * ((primary + secondary) * weight);
        }
      #endif

      #ifdef ORB_FLOW
        uniform mat3 uFlowBasis;
        uniform float uFlowOffset;
        uniform float uFlowFrontPhase;
        uniform vec2 uFlowCrestWidth;
        uniform float uFlowBackWeight;
        uniform vec3 uFlowLight;
        uniform vec3 uFlowShade;

        vec3 colorOrbFlow(vec3 water, vec3 direction, float facing, float lift, float layer) {
          vec3 orbit = uFlowBasis * direction;
          vec2 around = orbit.xy * inversesqrt(max(dot(orbit.xy, orbit.xy), 0.000001));
          float across = orbit.z - uFlowOffset;
          // The highlight slows through the front arc, then continues around the back.
          float phase = uWavePhase.x - uFlowFrontPhase;
          float travel = phase - .26 * sin(phase) + .24 * (1.0 - cos(phase));
          vec2 heading = vec2(cos(travel - .04), sin(travel - .04));
          float lengthMask = smoothstep(.63, .928, dot(around, heading));
          float taper = mix(.64, 1.0, lengthMask);
          float crest = 1.0 - smoothstep(uFlowCrestWidth.x * taper, uFlowCrestWidth.y * taper, abs(across));
          float trough = 1.0 - smoothstep(.024, .104, abs(across - .172));
          float visibility = mix(uFlowBackWeight, 1.0, smoothstep(-.29, .66, facing));
          float surface = mix(1.0, .14, layer);
          float strength = lengthMask * visibility * surface;
          float liftLight = mix(.58, 1.0, smoothstep(-.028, .030, lift));
          return mix(mix(water, uFlowShade, .36 * strength * trough),
                     uFlowLight, .97 * strength * crest * liftLight);
        }
      #endif

      void main() {
        vec3 direction = normalize(mat3(modelMatrix) * orbDirection);
        vec3 viewDirection = normalize(normalMatrix * orbDirection);
        float facing = viewDirection.z;
        float front = smoothstep(-.52, .76, facing);
        float sun = max(dot(direction, uSunDirection), 0.0);
        float rim = pow(1.0 - abs(facing), 2.0);
        vec3 blue = mix(uShade, uBody, .18 + .64 * front + .16 * sun);
        vec3 viewLight = mat3(viewMatrix) * uSunDirection;
        vec3 halfDirection = normalize(viewLight + vec3(0.0, 0.0, 1.0));
        float directGleam = smoothstep(.86, .992, dot(viewDirection, halfDirection));
        float rimGleam = rim * pow(sun, 3.0);
        float gleam = min(.94 * directGleam + .28 * rimGleam, 1.0);
        #ifdef ORB_FLOW
          gleam *= .62;
        #endif
        vColor = mix(blue, uLight, gleam * mix(1.0, .35, orbLayer));
        vOpacity = (.33 + .49 * front + .09 * rim) * mix(1.0, .42, orbLayer);
        vec3 localPosition = position;
        #ifdef ORB_WAVE
          localPosition = displaceOrbPoint(position, orbDirection, orbLayer);
        #endif
        #ifdef ORB_FLOW
          float lift = dot(localPosition - position, orbDirection);
          vColor = colorOrbFlow(vColor, orbDirection, facing, lift, orbLayer);
        #endif
        gl_Position = projectionMatrix * modelViewMatrix * vec4(localPosition, 1.0);
        gl_PointSize = max(uMinimumPointSize, .5 * abs(projectionMatrix[1][1]) * uSampleHeight * orbDiameter);
      }
    `,
    fragmentShader: /* glsl */`
      varying vec3 vColor;
      varying float vOpacity;
      void main() {
        float distanceToCenter = length(2.0 * gl_PointCoord - 1.0);
        float coverage = 1.0 - smoothstep(.60, 1.0, distanceToCenter);
        if (coverage < .015) discard;
        gl_FragColor = vec4(vColor, vOpacity * coverage);
        #include <colorspace_fragment>
      }
    `,
  });

  const object = new Points(geometry, material);
  object.name = 'fountain-water-crown';
  object.position.y = centerY;
  // Size against the active surface so the orthographic cameras agree in pixel and native modes.
  object.onBeforeRender = (renderer) => {
    material.uniforms.uSampleHeight!.value = renderer.getRenderTarget()?.height ?? renderer.domElement.height;
  };

  return {
    object,
    metadata: {
      radius: orbConfig.radius,
      centerY,
      amplitude: 0,
      period: 0,
      referenceTime,
      shellCount,
      interiorCount,
      vertices: count,
      triangles: 0,
      shellRadius,
      minimumPointSize,
      diameter,
      colors,
      addedTextures: 0,
      addedPasses: 0,
      ...(waves && { wave: particleOrbWave, maximumDisplacement }),
      ...(flow && { surfaceFlow: particleOrbFlow }),
    },
    update(time: number) {
      wavePhase?.set(samplePeriodicPhase(time, primary.period), samplePeriodicPhase(time, secondary.period));
      return bottomY;
    },
    dispose() {
      geometry.dispose();
      material.dispose();
    },
  };
}
