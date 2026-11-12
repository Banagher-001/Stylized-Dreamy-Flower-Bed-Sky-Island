import * as THREE from 'three';

const SKY_VERT = [
  'varying vec3 vWorldPosition;',
  'void main() {',
  '  vec4 worldPosition = modelMatrix * vec4(position, 1.0);',
  '  vWorldPosition = worldPosition.xyz;',
  '  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);',
  '}',
].join('\n');

const SKY_FRAG = [
  'uniform vec3 topColor;',
  'uniform vec3 bottomColor;',
  'uniform float offset;',
  'uniform float exponent;',
  'varying vec3 vWorldPosition;',
  'void main() {',
  '  float h = normalize(vWorldPosition + vec3(0.0, offset, 0.0)).y;',
  '  float t = pow(max(h, 0.0), exponent);',
  '  gl_FragColor = vec4(mix(bottomColor, topColor, t), 1.0);',
  '}',
].join('\n');

/** Owns the THREE.Scene: gradient sky dome, fog, environment map, sun/hemi/ambient lights. */
export class SceneManager {
  constructor() {
    this.scene = new THREE.Scene();
    this.scene.fog = new THREE.Fog(new THREE.Color('#6d5a86'), 85, 240);
    this.scene.background = new THREE.Color('#473c78');

    this.skyUniforms = {
      topColor: { value: new THREE.Color('#473c78') },
      bottomColor: { value: new THREE.Color('#f2a06a') },
      offset: { value: 10 },
      exponent: { value: 0.62 },
    };
    const skyGeo = new THREE.SphereGeometry(460, 32, 18);
    const skyMat = new THREE.ShaderMaterial({
      uniforms: this.skyUniforms,
      vertexShader: SKY_VERT,
      fragmentShader: SKY_FRAG,
      side: THREE.BackSide,
      depthWrite: false,
      fog: false,
      toneMapped: false,
    });
    this.sky = new THREE.Mesh(skyGeo, skyMat);
    this.sky.name = 'SkyDome';
    this.sky.renderOrder = -10;
    this.scene.add(this.sky);

    this.hemi = new THREE.HemisphereLight(0x9db6ff, 0x2a2438, 0.5);
    this.hemi.name = 'HemiLight';
    this.scene.add(this.hemi);

    this.ambient = new THREE.AmbientLight(0xffffff, 0.14);
    this.ambient.name = 'AmbientLight';
    this.scene.add(this.ambient);

    this.sun = new THREE.DirectionalLight(0xffd7a8, 1.4);
    this.sun.name = 'SunLight';
    this.sun.position.set(-30, 46, 34);
    this.sun.castShadow = true;
    this.sun.shadow.mapSize.set(2048, 2048);
    this.sun.shadow.camera.near = 4;
    this.sun.shadow.camera.far = 160;
    this.sun.shadow.camera.left = -46;
    this.sun.shadow.camera.right = 46;
    this.sun.shadow.camera.top = 46;
    this.sun.shadow.camera.bottom = -34;
    this.sun.shadow.bias = -0.0006;
    this.sun.shadow.normalBias = 0.035;
    this.sun.target.position.set(0, 0, 2);
    this.scene.add(this.sun);
    this.scene.add(this.sun.target);

    this.envIntensity = 0.35;
  }

  buildEnvironment(renderer) {
    try {
      const pmrem = new THREE.PMREMGenerator(renderer);
      const envScene = new THREE.Scene();
      const mat = this.sky.material.clone();
      mat.uniforms = THREE.UniformsUtils.clone(this.sky.material.uniforms);
      const dome = new THREE.Mesh(new THREE.SphereGeometry(60, 24, 12), mat);
      envScene.add(dome);
      const rt = pmrem.fromScene(envScene, 0.04, 0.1, 200);
      this.scene.environment = rt.texture;
      dome.geometry.dispose();
      mat.dispose();
      pmrem.dispose();
    } catch (err) {
      console.warn('[SceneManager] PMREM environment failed, continuing without it', err);
    }
  }

  setSky(topColor, bottomColor) {
    this.skyUniforms.topColor.value.set(topColor);
    this.skyUniforms.bottomColor.value.set(bottomColor);
    this.scene.background = new THREE.Color(bottomColor).lerp(new THREE.Color(topColor), 0.5);
  }

  setFog(color, near, far) {
    this.scene.fog.color.set(color);
    this.scene.fog.near = near;
    this.scene.fog.far = far;
  }
}