# 第五步个人介绍证据

当前结论见 [第五步验收记录](../../scroll-garden/step-5-verification.md)，进入方式和内容维护位置见 [实现说明](../../scroll-garden/step-5-implementation.md)。

- `protected-baseline-sha256.json`：第五步执行前的693个既有文件摘要；前后核对见 `summary.json`。
- `baseline-before.json`、`before-*.png`、`route-before.json`：本次实施前第四步源码的画面、状态和路线基线；旧第四步目录保留。
- `baseline-after.json`、`after-*.png`：当前第五步三种目标尺寸、三站与正常模式画面。
- `verification-{chromium,firefox,webkit}.json`：本步52组集成检查、真实选择文本、语义、字框、资源与诊断。
- `chromium-A1.png` / `A2` / `A3` 与其他引擎对应图、`*-1366-A*.png`、`*-mobile-A*.png`：当前三站画面。
- `*-contrast-background-*.png`：对比度测量时暂时隐藏字面的背景采集，测量后恢复；不是正常页面截图。
- `*-travel-*.png`：下降、消隐与跨柱中间状态。`*-context-check.json`及其前后图：集成操作序列后的恢复对照。
- `geometry-isolation.json`：3003个路径采样，旧缓冲/变换、7个材质绑定、实例、关键姿态与3个贴面锚点检查。
- `native-recovery.json`及`native-before/after-*.png`：实际标签切换、观察document.hidden、下降中途恢复，无伪造可见性事件。
- `decoration-fallback.json`：禁用Canvas2D后的正文、九种缺失字体回退布局与字面对比度、参考入口和缓存程序对照；对应`decoration-font-fallback-*.png`。
- `latency-before.json`、`latency-after.json`：本次同环境、同脚本各30个wheel停止样本；前后约202/212ms p95，完整样本和峰值保留。
- `about-reading-demo.mp4`、WebM及`demo-recording.json`：真实双向滚轮实录，固定环境时间，不作为硬件FPS证明。
- `fallback.json`、`no-webgl.png`：无WebGL可读提示、禁用控制和返回参考稿。
- `before-reference-*.png`、`after-reference-*.png`：默认参考稿正常/像素模式的逐像素保护对照。
- `summary.json`：构建与源码摘要、范围保护、浏览器/资源/性能结果、录制信息与交付边界。

`layout-initial.json`和`layout-*.png`是首次接入排版的检查，运行源码随后未再变化。`initial-native-recovery.json`保存首次原生恢复的成功页面断言，`initial-native-cleanup.json`记录当时脚本清理临时目录的竞态；关闭流程修正后的完整通过结果为`native-recovery.json`。`raw-recording/`保留录制原件。

完整集成序列中的Chromium348.1ms诊断峰值保留在报告内，和单独30样本性能对照分开说明。Firefox的5条已知诊断不隐藏。模拟手机和Linux软件图形环境不能证明真实手机、Apple Safari或物理GPU表现；长文、狭矮横屏与完整静态章节仍待后续适配。
