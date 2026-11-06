import {
  Color,
  DirectionalLight,
  HemisphereLight,
  Mesh,
  OrthographicCamera,
  PlaneGeometry,
  Scene,
} from 'three';
import { palette } from '../config/palette';
import { sceneConfig } from '../config/scene';
import { lightingConfig } from '../config/lighting';
import { createGroundMaterial } from '../materials/createGroundMaterial';
import { createBlockout } from './createBlockout';
import { createVegetation } from './createVegetation';
import { createWaterState } from '../materials/createWaterMaterial';
import { createFountainEffects } from './createFountainEffects';
import { createEnvironmentState } from '../animation/environmentMotion';
import type { EnvironmentOptions } from '../config/environment';
import { createFloatingPetals } from './createFloatingPetals';
import { createFountainAppearance } from './createFountainAppearance';
import type { FountainStyle } from '../config/fountain';
import type { OrbStyle } from '../config/orb';

export function createScene(options: Partial<EnvironmentOptions> = {}, fountainStyle: FountainStyle = 'legacy', orbStyle: OrbStyle = 'legacy') {
  const environmentState = createEnvironmentState(options);
  const scene = new Scene();
  scene.background = new Color(palette.grassBase);

  const camera = new OrthographicCamera();
  camera.position.set(...sceneConfig.camera.position);
  camera.lookAt(...sceneConfig.camera.target);
  camera.near = sceneConfig.camera.near;
  camera.far = sceneConfig.camera.far;

  const groundGeometry = new PlaneGeometry(sceneConfig.ground.size, sceneConfig.ground.size);
  const groundMaterial = createGroundMaterial(environmentState);
  const ground = new Mesh(groundGeometry, groundMaterial);
  ground.name = 'courtyard-ground';
  ground.rotation.x = -Math.PI / 2;
  ground.receiveShadow = true;
  scene.add(ground);

  const waterState = createWaterState();
  const blockout = createBlockout(waterState);
  scene.add(blockout.root);
  let fountainAppearance: ReturnType<typeof createFountainAppearance> | undefined;
  if (fountainStyle === 'refined') {
    try { fountainAppearance = createFountainAppearance(scene, waterState); }
    catch (error) { console.warn('Pool finish unavailable; original fountain retained.', error); }
  }
  const fountainEffects = createFountainEffects(waterState, orbStyle);
  scene.add(fountainEffects.root);

  const hemisphere = new HemisphereLight(
    palette.highlight,
    palette.stoneShade,
    lightingConfig.fill.intensity,
  );
  hemisphere.name = 'courtyard-fill';
  const sun = new DirectionalLight(palette.highlight, lightingConfig.sun.intensity);
  sun.name = 'courtyard-sun';
  sun.position.set(...lightingConfig.sun.position);
  sun.castShadow = lightingConfig.shadows.enabled;
  const shadows = lightingConfig.shadows;
  sun.shadow.mapSize.setScalar(shadows.mapSize);
  sun.shadow.camera.left = -shadows.extent;
  sun.shadow.camera.right = shadows.extent;
  sun.shadow.camera.top = shadows.extent;
  sun.shadow.camera.bottom = -shadows.extent;
  sun.shadow.camera.near = shadows.near;
  sun.shadow.camera.far = shadows.far;
  sun.shadow.bias = shadows.bias;
  sun.shadow.normalBias = shadows.normalBias;
  sun.shadow.radius = shadows.radius;
  scene.add(hemisphere, sun, sun.target);

  let currentViewHeight: number = sceneConfig.camera.viewHeight;
  let currentAspect = 1;
  function setAspect(aspect: number) {
    currentAspect = aspect;
    const halfHeight = currentViewHeight / 2;
    camera.left = -halfHeight * aspect;
    camera.right = halfHeight * aspect;
    camera.top = halfHeight;
    camera.bottom = -halfHeight;
    camera.updateProjectionMatrix();
  }

  setAspect(1);
  camera.updateMatrixWorld(true);
  const vegetation = createVegetation(camera, environmentState);
  scene.add(vegetation.root);
  const petals = environmentState.options.enabled && environmentState.options.petals ? createFloatingPetals() : undefined;
  if (petals) { petals.update(environmentState.time.value);scene.add(petals.mesh); }
  let disposed = false;

  return {
    scene,
    camera,
    setAspect,
    setViewHeight(height: number) {
      if (!Number.isFinite(height) || height <= 0) throw new RangeError('Camera view height must be positive.');
      if (height === currentViewHeight) return;
      currentViewHeight = height;
      setAspect(currentAspect);
    },
    update(time: number) {
      fountainEffects.update(time);
      environmentState.time.value = time;
      petals?.update(time);
    },
    waterState,
    fountainStyle: fountainAppearance ? 'refined' : fountainStyle === 'refined' ? 'fallback' : 'legacy',
    fountainMetadata: fountainAppearance?.metadata,
    orbStyle: fountainEffects.root.userData.orbStyle ?? (orbStyle === 'lively' ? 'fallback' : 'legacy'),
    orbMetadata: fountainEffects.root.userData.orbMetadata,
    environmentState,
    dispose() {
      if (disposed) return;
      disposed = true;
      groundGeometry.dispose();
      groundMaterial.dispose();
      fountainAppearance?.dispose();
      blockout.dispose();
      vegetation.dispose();
      fountainEffects.dispose();
      petals?.dispose();
      sun.shadow.dispose();
      scene.clear();
    },
  };
}
