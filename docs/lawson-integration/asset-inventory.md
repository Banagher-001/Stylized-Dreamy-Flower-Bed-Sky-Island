# 罗森运行资源清单

本轮以源仓库 `95dad9881a7b9d31c0ac635f1f335055d8cb3cc4` 的 `lawson-blender/out/web_final/` 为准。清单由入口、import map、ES Module、CSS 和 GLB JSON 引用递归得到，并在本地临时目录制作了根目录与子目录两份逐字节一致的运行副本。

## 体积与依赖

- 必需运行文件：46 个，20,332,784 字节（20.33 MB，未压缩）。
- 四个模型：18,648,040 字节（18.65 MB）。
- 罗森使用 Three.js r160；个人网站使用 three 0.187.0。正式接入采用独立文档隔离模块和样式。
- 静态检查没有遗漏文件、未解析模块或外部网络依赖；四个 GLB 没有外链 buffer/图像 URI。
- 运行目录下 js/css/vendor/assets 与 index.html 共 46 个文件全部被依赖图覆盖。

## 模型

| 文件 | 字节 | 节点 | 网格 | 材质 | 内置动画 |
|---|---:|---:|---:|---:|---:|
| `assets/models/car_A.glb` | 396,308 | 94 | 53 | 19 | 0 |
| `assets/models/car_B.glb` | 489,936 | 103 | 57 | 20 | 0 |
| `assets/models/car_C.glb` | 445,748 | 101 | 61 | 18 | 0 |
| `assets/models/lawson_scene.glb` | 17,316,048 | 2359 | 1278 | 320 | 0 |

场景动作来自网页程序驱动，GLB 的内置动画数量不能直接代表车辆、店员或自动门的运行能力。

## 必需文件

| 路径 | 字节 |
|---|---:|
| `assets/models/car_A.glb` | 396,308 |
| `assets/models/car_B.glb` | 489,936 |
| `assets/models/car_C.glb` | 445,748 |
| `assets/models/lawson_scene.glb` | 17,316,048 |
| `css/controls.css` | 1,316 |
| `css/main.css` | 9,446 |
| `css/responsive.css` | 1,310 |
| `index.html` | 8,821 |
| `js/config/assetManifest.js` | 832 |
| `js/config/lightConfig.js` | 7,082 |
| `js/config/sceneConfig.js` | 3,051 |
| `js/config/vehiclePaths.js` | 3,857 |
| `js/core/AnimationController.js` | 919 |
| `js/core/AssetManager.js` | 20,310 |
| `js/core/Renderer.js` | 6,653 |
| `js/core/SceneManager.js` | 3,627 |
| `js/core/UpdateLoop.js` | 1,359 |
| `js/main.js` | 21,797 |
| `js/systems/CameraSystem.js` | 7,819 |
| `js/systems/ClerkSystem.js` | 32,677 |
| `js/systems/DayNightSystem.js` | 2,870 |
| `js/systems/DoorSystem.js` | 3,462 |
| `js/systems/InteractionSystem.js` | 4,315 |
| `js/systems/LightingSystem.js` | 5,332 |
| `js/systems/QualitySystem.js` | 1,768 |
| `js/systems/TrafficSystem.js` | 25,616 |
| `js/systems/clerk/AnimLibrary.js` | 7,981 |
| `js/systems/clerk/NavGrid.js` | 5,835 |
| `js/systems/clerk/TaskManager.js` | 4,542 |
| `js/systems/clerk/clerkConfig.js` | 8,395 |
| `js/ui/UIController.js` | 9,561 |
| `js/ui/UIState.js` | 884 |
| `vendor/three/jsm/controls/OrbitControls.js` | 29,868 |
| `vendor/three/jsm/loaders/GLTFLoader.js` | 108,522 |
| `vendor/three/jsm/postprocessing/EffectComposer.js` | 4,651 |
| `vendor/three/jsm/postprocessing/MaskPass.js` | 2,231 |
| `vendor/three/jsm/postprocessing/OutputPass.js` | 2,398 |
| `vendor/three/jsm/postprocessing/Pass.js` | 1,706 |
| `vendor/three/jsm/postprocessing/RenderPass.js` | 1,915 |
| `vendor/three/jsm/postprocessing/ShaderPass.js` | 1,576 |
| `vendor/three/jsm/postprocessing/UnrealBloomPass.js` | 12,406 |
| `vendor/three/jsm/shaders/CopyShader.js` | 571 |
| `vendor/three/jsm/shaders/LuminosityHighPassShader.js` | 1,192 |
| `vendor/three/jsm/shaders/OutputShader.js` | 1,393 |
| `vendor/three/jsm/utils/BufferGeometryUtils.js` | 31,906 |
| `vendor/three/three.module.js` | 1,272,972 |

## 展示素材候选

现有归档画面可用于第二步挑选封面与项目档案；它们是旧交付画面，不作为本次运行通过的证据：

- `screenshots_clerk/cherry_final_hero.png`
- `screenshots/03_hero_night.png`
- `screenshots/08_interior.png`
- `screenshots/09_checkout.png`

本次实际运行截图保存在本步证据的各 run 目录中。第二步会确定面向访客的封面取景与文案。

## 留在源工程中的资料

`.blend`、建模脚本、旧网页备份、node_modules、启动器、日志、历史验收报告和长录像属于制作或核查资料。正式网站运行目录按上面的依赖清单制作，源工程仍保留在私有仓库。

逐文件 SHA256、GLB 元信息、导入映射和依赖边，见 [asset-manifest.json](../evidence/lawson-integration-step-1/asset-manifest.json)。
