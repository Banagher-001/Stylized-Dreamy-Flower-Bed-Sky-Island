# 第三步阅读原型证据

结论与覆盖限制见 [第三步验收记录](../../scroll-garden/step-3-verification.md)，进入方式见 [使用说明](../../scroll-garden/step-3-implementation.md)。

- `baseline.json`、`before-*.png`、`route-before.json`：修改前第二步的镜头、画面和实例数据基线，未覆盖旧第二步证据。
- `route-geometry.json`：3003 个路径样本、9 条三站柱面射线、45 个阅读停留样本、1001 个单调下降样本及各交界核对。
- `verification-{chromium,firefox,webkit}.json`：三引擎共 47 组集成检查；Firefox 的 4 条已知诊断保留。
- `*-A1.png`、`*-A2.png`、`*-A3.png`：三站阅读画面；`*-travel-*.png` 为显隐、下降和出柱中间态。
- `*-mobile-A*.png`、`*-1366-A2.png`：模拟手机三站与中等桌面画幅；`layout-1366-A*.png` 补齐 Chromium 中等画幅的三站。
- `layout-orientation.json`、`rotation-landscape-*.png`：模拟横竖切换的进度保留。狭矮横屏的完整阅读构图仍待第 11 步，未标成已通过。
- `capacity-1440.png`、`capacity-390.png`：明确标注的 200 字压力样本，只由测试临时注入。1440×900 可容纳；390×844 侵占柱面焦点，不符合本步构图要求。正式应用仍只有三段真实短文。
- `recovery-contrast.json`、`native-before/after-*.png`：通过直接 CDP 控制原生 Chromium 的实际标签切换、下降中途恢复和完整阅读态对比度。未改写页面可见性属性。
- `after-reference-*.png`：默认参考稿与修改前两模式逐像素对照。
- `pillar-reading-demo.mp4`、对应 WebM、`raw-recording/`、`demo-recording.json`：实际滚轮双向操作实录与原始记录，不作为硬件 FPS 证据。
- `fallback.json`、`no-webgl.png`：无 WebGL 提示、图形控制禁用及返回参考稿。
- `summary.json`：源码保护、构建产物摘要、检查结果和交付边界。

`calibration-1440-*` 是初次桌面构图检查，正式最终画面使用引擎名前缀。没有以几何采样替代所有像素与视线检查，也没有将 Linux WebKit 或手机模拟当作真实 Safari、手机硬件验证。
