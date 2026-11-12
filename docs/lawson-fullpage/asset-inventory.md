# 原网页运行文件清单

固定源版本 `95dad9881a7b9d31c0ac635f1f335055d8cb3cc4`，入口 `lawson-blender/out/web_final/index.html`。

共 46 个必要运行文件，20,332,784 字节；4 个 GLB 共 18,648,040 字节。所有模块引用已解析，无运行时外链依赖；模型没有外链 buffer 或图像。

网页启动脚本、README 和建模源文件不属于这 46 个浏览器运行依赖。清单用于固定完整网页的运行闭包，不将开发辅助文件误算成缺失的页面资源。

| 相对原入口的文件 | 字节 | SHA256 前 12 位 |
|---|---:|---|
| `assets/models/car_A.glb` | 396,308 | `7c832daf2463` |
| `assets/models/car_B.glb` | 489,936 | `0fd313905989` |
| `assets/models/car_C.glb` | 445,748 | `a730a81d78bc` |
| `assets/models/lawson_scene.glb` | 17,316,048 | `f953f7413eb4` |
| `css/controls.css` | 1,316 | `5cbe7cdcd986` |
| `css/main.css` | 9,446 | `6609cb077bd9` |
| `css/responsive.css` | 1,310 | `8601fcf67c71` |
| `index.html` | 8,821 | `ef8eb8d65662` |
| `js/config/assetManifest.js` | 832 | `30d61399598f` |
| `js/config/lightConfig.js` | 7,082 | `0a7c83866554` |
| `js/config/sceneConfig.js` | 3,051 | `7a28ae30d4de` |
| `js/config/vehiclePaths.js` | 3,857 | `0a35ecb99839` |
| `js/core/AnimationController.js` | 919 | `7d079522fd06` |
| `js/core/AssetManager.js` | 20,310 | `180ea83606e0` |
| `js/core/Renderer.js` | 6,653 | `123579b8470b` |
| `js/core/SceneManager.js` | 3,627 | `36d2d0ec3eeb` |
| `js/core/UpdateLoop.js` | 1,359 | `fb6f999e91d4` |
| `js/main.js` | 21,797 | `401b1f1331fd` |
| `js/systems/CameraSystem.js` | 7,819 | `319087cdd0aa` |
| `js/systems/ClerkSystem.js` | 32,677 | `b96ba89d76cf` |
| `js/systems/DayNightSystem.js` | 2,870 | `7ea481dbbdb0` |
| `js/systems/DoorSystem.js` | 3,462 | `d51a51d10cb3` |
| `js/systems/InteractionSystem.js` | 4,315 | `6bbd2abba138` |
| `js/systems/LightingSystem.js` | 5,332 | `778f76487ce8` |
| `js/systems/QualitySystem.js` | 1,768 | `a6753418147c` |
| `js/systems/TrafficSystem.js` | 25,616 | `483844a69509` |
| `js/systems/clerk/AnimLibrary.js` | 7,981 | `249d52296e0f` |
| `js/systems/clerk/NavGrid.js` | 5,835 | `e8067b63b1f4` |
| `js/systems/clerk/TaskManager.js` | 4,542 | `c7346b527e25` |
| `js/systems/clerk/clerkConfig.js` | 8,395 | `165946aecca5` |
| `js/ui/UIController.js` | 9,561 | `12bd956cff97` |
| `js/ui/UIState.js` | 884 | `005f671a6894` |
| `vendor/three/jsm/controls/OrbitControls.js` | 29,868 | `5a44a9e86a2a` |
| `vendor/three/jsm/loaders/GLTFLoader.js` | 108,522 | `d073b438e6a0` |
| `vendor/three/jsm/postprocessing/EffectComposer.js` | 4,651 | `d234e578618f` |
| `vendor/three/jsm/postprocessing/MaskPass.js` | 2,231 | `328cf7db0da5` |
| `vendor/three/jsm/postprocessing/OutputPass.js` | 2,398 | `13817fc7a87f` |
| `vendor/three/jsm/postprocessing/Pass.js` | 1,706 | `b3c6128340ea` |
| `vendor/three/jsm/postprocessing/RenderPass.js` | 1,915 | `1c90c0853128` |
| `vendor/three/jsm/postprocessing/ShaderPass.js` | 1,576 | `3b28a1ee27e0` |
| `vendor/three/jsm/postprocessing/UnrealBloomPass.js` | 12,406 | `8f09315c0cec` |
| `vendor/three/jsm/shaders/CopyShader.js` | 571 | `4e3346db194d` |
| `vendor/three/jsm/shaders/LuminosityHighPassShader.js` | 1,192 | `3d841cc594a0` |
| `vendor/three/jsm/shaders/OutputShader.js` | 1,393 | `53a52e430c27` |
| `vendor/three/jsm/utils/BufferGeometryUtils.js` | 31,906 | `9be041e96308` |
| `vendor/three/three.module.js` | 1,272,972 | `76dea8151bc9` |

完整 SHA256、GLB 结构与来源链见 [runtime-manifest.json](../evidence/lawson-fullpage-step-1/runtime-manifest.json)。三个车辆及商店场景均为程序驱动动画；GLB 内没有动画轨道，不应因此误判动画文件缺失。
