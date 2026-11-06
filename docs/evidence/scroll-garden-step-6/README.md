# 第六步示意版与机制证据

结论见[第六步验收](../../scroll-garden/step-6-verification.md)，入口与素材缺口见[实现说明](../../scroll-garden/step-6-implementation.md)。当前两张概念图不是个人实际项目；隔离庭院视频不是AI动画正片。

- `protected-baseline-sha256.json`：执行前860个既有文件的SHA摘要；最终文件范围核对见`summary.json`。
- `route-before.json`、`baseline-before.json`、`before-*.png`：本次第五步源码的几何、画面和状态基线，旧目录未覆盖。
- `baseline-after.json`、`after-*.png`：本步固定时间三种尺寸与正常模式画面。
- `verification-{chromium,firefox,webkit}.json`：第二柱各17组集成，共51组；包括24状态、反向布局、图片查看、暂停/恢复、手机、对比度、资源和诊断。
- `about-verification-*.json`：本步第一柱回归共52组；`about-*.png`为对应图。
- `player-{chromium,firefox,webkit}.json`：同一媒体组件的隔离播放器各5组，共15组；真实解码、失效重试、10轮清理。`fixture-*.png`始终标测试夹具。
- `chromium-B1.png`～`B4`与其他引擎对应图、`*-1366-B*.png`、`*-mobile-B*.png`：最终四站正常页面截图。
- `*-contrast-background-*.png`：对比度测量临时隐藏字面的背景采集，测后恢复；不是正常页面截图。
- `*-travel-*.png`、`*-context-before/after.png`：下降、离柱与恢复画面。
- `geometry-isolation.json`：3003路径采样、第二柱四站×三比例射线、60个站内样本、14个材质绑定、原缓冲/变换/实例/关键姿态、四个安全锚点和清理。
- `native-recovery.json`：原生实际标签隐藏/返回、6.30H恢复、查看层隐藏返回、隔离视频实际隐藏暂停；对应`native-before/after-*.png`。
- `decoration-fallback.json`与`font-fallback-*.png`：12种装饰/字体回退布局及真实背景对比度。该报告的模式切换在局部B4取样。
- `resource-caches.json`：两模式都访问全程后的完整资源缓存；与局部切换报告分开。
- `fallback.json`、`no-webgl.png`：无WebGL提示、图形控制禁用、两阅读层隐藏、参考入口。
- `image-error.json`与`image-error-*.png`：真实图片中断、短失败提示、查看层重试与返回原位。
- `first-pillar-pixel-protection.json`：桌面/正常模式9图逐像素一致，手机3图最多1/255通道差异；并非全图零差异，前后原图保留。
- `before-reference-*.png`、`after-reference-*.png`：默认参考稿两模式逐像素对照。
- `latency-before.json`、`latency-after.json`：同脚本各30次wheel停止，完整原始样本与源码摘要。集成序列聚合单独保留，584.4ms观测峰值不隐藏。
- `film-reading-demo.mp4`及WebM、`demo-recording.json`、`recording-progress.json`：14个真实wheel位置与原图打开/关闭，固定环境，不是硬件FPS证据。
- `summary.json`：最终源码/构建/保护、素材状态、检查与交付边界。

`layout-initial.json`、`layout-*.png`是首轮接入画面，其源码摘要单独保留。`calibration-image-error*`保留手机切片失败提示截断的初次结果；最终使用短提示。`calibration-native-modal-debug.json`、`native-modal-debug.json`及`calibration-notes.json`解释原生采样校准，初轮组合断言未保存细项，不将其写成已诊断的页面错误。`calibration-integration-latency.json`保存早期完整集成的聚合峰值，未构造不存在的原始样本。

`raw-recording/`保留录制原件，包括首轮进度阈值未达到而中止的片段；最终演示由录制元数据指明。脚本按实时文档范围计算wheel距离，检查实际H，没有将脚本滚动设值包装成手动wheel录制。

手机模拟、Linux软件图形和GTK WebKit不等于真实手机、Apple Safari或物理GPU验收。真实作品、完整手机/横屏适配和实机手感仍待补。
