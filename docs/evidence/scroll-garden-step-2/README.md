# 第二步运镜证据

结论见 [验收记录](../../scroll-garden/step-2-verification.md)。

- `verification-{chromium,firefox,webkit}.json`：三引擎生产页面集成检查，保留 Firefox 已知诊断。
- `route-geometry.json`：3003 个几何采样、边界连续性、三柱首站射线、全景边界、第一步分段对照和实例数据摘要。
- `chromium-{overview,about,films,experiments,water}.png`：主要构图；另两引擎保存对应画面。
- `*-travel-*.png`：四个转场中间位置；`*-mobile.png` 为手机模拟。
- `reference-before-*` 与 `reference-after-*`：默认参考稿两种模式精确对照。`reference-instances-before.json` 是修改前实例摘要。
- `scroll-camera-demo.mp4`：可播放的实际浏览器滚轮实录；原始 WebM 与录制元数据保留，不是硬件帧率测试。
- `fallback.json`、`no-webgl.png`：禁用 WebGL 的提示与回退。
- `caption-check.json`：最终生产版本同一转场内的提示更新，含正反向共 5 个位置；不并入既有 37 组功能检查计数。
- `summary.json`：最终汇总、源码保护、产物摘要及阶段边界。

`calibration-*` 是早期构图检查，底部控制条尚覆盖部分画面；最终版本为控制条预留舞台空间。`mode-debug-*` 用于区分浮动控制按钮悬浮状态和场景画面，已确认差异仅在按钮区域；正式图像对照使用一致的鼠标位置。

几何边界、浏览器显示和模拟触摸是不同检查；没有将 GTK WebKit、模拟手机或软件渲染当作真实 Safari、手机或物理 GPU 通过。
