import type { MeshLambertMaterial } from 'three';
import { environmentConfig as config } from '../config/environment';
import { windDirection } from '../animation/environmentMotion';
import type { EnvironmentState } from '../animation/environmentMotion';

type ArtShader = Parameters<MeshLambertMaterial['onBeforeCompile']>[0];
const gl = (value: number) => value.toFixed(10);

const windDeclarations = /* glsl */`
  uniform float uEnvironmentTime;
  uniform float uEnvironmentWind;
  attribute vec3 windRoot;
  attribute vec4 windShape; // height, maximum angle, position phase, rigid head
  const vec2 windDirection = vec2(${windDirection.map(gl).join(',')});
  float plantWindAngle(vec4 shape) {
    float gust = 0.68 + 0.32 * sin(6.28318530718 * uEnvironmentTime / ${gl(config.wind.gustPeriod)} + shape.z * 0.23);
    return shape.y * gust * (0.78 * sin(6.28318530718 * uEnvironmentTime / ${gl(config.wind.periods[0])} + shape.z)
      + 0.22 * sin(6.28318530718 * uEnvironmentTime / ${gl(config.wind.periods[1])} + shape.z * 1.3));
  }
  vec3 rotatePlantWind(vec3 v, float angle) {
    float along = dot(v.xz, windDirection);
    float a2 = angle * angle;
    float c = 1.0 - a2 * (0.5 - a2 / 24.0 + a2 * a2 / 720.0);
    float s = angle * (1.0 - a2 / 6.0 + a2 * a2 / 120.0);
    vec2 horizontal = v.xz + windDirection * (along * (c - 1.0) + v.y * s);
    return vec3(horizontal.x, v.y * c - along * s, horizontal.y);
  }
  vec3 bendPlantWind(vec3 rest, vec3 root, vec4 shape) {
    float height = shape.x;
    float y = shape.w > 0.5 ? height : clamp(rest.y - root.y, 0.0, height);
    float turn = plantWindAngle(shape) * y / height;
    float t2 = turn * turn;
    // Angles are bounded to 8 degrees. These forms remain precise near still poses.
    float sinc = 1.0 - t2 / 6.0 + t2 * t2 / 120.0;
    float cosc = turn * (0.5 - t2 / 24.0 + t2 * t2 / 720.0);
    vec3 center = root + vec3(windDirection.x * y * cosc, y * sinc, windDirection.y * y * cosc);
    return center + rotatePlantWind(rest - root - vec3(0.0, y, 0.0), turn);
  }
  vec3 bendPlantWindNormal(vec3 rest, vec3 root, vec4 shape, vec3 normal) {
    float angle = plantWindAngle(shape);
    float y = shape.w > 0.5 ? shape.x : clamp(rest.y - root.y, 0.0, shape.x);
    // Inverse-transpose of the arc deformation, then rotate into its tangent.
    if (shape.w < 0.5) normal.y /= 1.0 - angle / shape.x * dot((rest - root).xz, windDirection);
    return rotatePlantWind(normal, angle * y / shape.x);
  }
`;

const canopyDeclarations = /* glsl */`
  uniform float uEnvironmentTime;
  uniform float uEnvironmentCanopy;
  float environmentCanopyWave(vec2 p) {
    float gust = 0.68 + 0.32 * sin(6.28318530718 * uEnvironmentTime / ${gl(config.wind.gustPeriod)} + dot(p, vec2(0.06, 0.04)));
    return uEnvironmentCanopy * gust * (
      0.76 * sin(6.28318530718 * uEnvironmentTime / ${gl(config.canopy.period)} + dot(p, vec2(0.35, 0.11)))
      + 0.24 * sin(6.28318530718 * uEnvironmentTime / ${gl(config.canopy.secondaryPeriod)} + dot(p, vec2(-0.12, 0.42))));
  }
`;

/** Extend the art response without replacing real shadow reception or instance colors. */
export function applyEnvironmentMotion(shader: ArtShader, plant: boolean, state: EnvironmentState) {
  shader.uniforms.uEnvironmentTime = state.time;
  shader.uniforms.uEnvironmentWind = state.wind;
  shader.uniforms.uEnvironmentCanopy = state.canopy;
  if (plant) {
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', `#include <common>\n${windDeclarations}`)
      .replace('#include <beginnormal_vertex>', `#include <beginnormal_vertex>
        #ifdef USE_INSTANCING
          if (uEnvironmentWind > 0.5) {
            mat3 windMatrix = mat3(instanceMatrix);
            vec3 windNormal = windMatrix * (objectNormal / vec3(dot(windMatrix[0], windMatrix[0]), dot(windMatrix[1], windMatrix[1]), dot(windMatrix[2], windMatrix[2])));
            windNormal = bendPlantWindNormal((instanceMatrix * vec4(position, 1.0)).xyz, windRoot, windShape, windNormal);
            objectNormal = vec3(dot(windMatrix[0], windNormal), dot(windMatrix[1], windNormal), dot(windMatrix[2], windNormal));
          }
        #endif
      `)
      .replace('#include <begin_vertex>', `#include <begin_vertex>
        #ifdef USE_INSTANCING
          if (uEnvironmentWind > 0.5) {
            mat3 windMatrix = mat3(instanceMatrix);
            vec3 windRest = (instanceMatrix * vec4(transformed, 1.0)).xyz;
            vec3 windDelta = bendPlantWind(windRest, windRoot, windShape) - windRest;
            transformed += vec3(dot(windMatrix[0], windDelta) / dot(windMatrix[0], windMatrix[0]),
              dot(windMatrix[1], windDelta) / dot(windMatrix[1], windMatrix[1]),
              dot(windMatrix[2], windDelta) / dot(windMatrix[2], windMatrix[2]));
          }
        #endif
      `);
  }
  shader.fragmentShader = shader.fragmentShader
    .replace('#include <common>', `#include <common>\n${canopyDeclarations}`)
    .replace('float artCanopy(vec2 position) {', `float artCanopy(vec2 position) {
      float environmentWave = environmentCanopyWave(position);`)
    .replace('distanceToCanopy = min(distanceToCanopy, d);', `
      float edgeBand = smoothstep(0.84, 0.94, d) * (1.0 - smoothstep(1.14, 1.24, d));
      float distanceGradient = length(local / (canopyBounds.zw * canopyBounds.zw)) / max(length(local / canopyBounds.zw), 0.001);
      d += environmentWave * ${gl(config.canopy.displacement)} * distanceGradient * edgeBand;
      distanceToCanopy = min(distanceToCanopy, d);`)
    .replace('float holes = step(0.74, branches) * step(0.68, artNoise(position * 8.5));',
      `float holes = step(0.74, branches) * step(0.68, artNoise(position * 8.5));
       holes *= 1.0 - uEnvironmentCanopy * ${gl(config.canopy.holeShade)} * (0.5 + 0.5 * environmentWave);`);
}
