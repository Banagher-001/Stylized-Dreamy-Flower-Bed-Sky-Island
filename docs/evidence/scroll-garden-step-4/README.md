# 第四步样板证据

结论见 [第四步验收](../../scroll-garden/step-4-verification.md)，进入方式见 [使用说明](../../scroll-garden/step-4-implementation.md)。

- `baseline-before.json`、`before-*.png`、`route-before.json`：第三步修改前基线。此前步骤的原始证据未覆盖。
- `geometry-isolation.json`：3003 个路线样本、原实例摘要、7 个独立材质绑定、原缓冲/变换保护、三处正面边界及正反面射线。
- `verification-{chromium,firefox,webkit}.json`：最终版共 50 组集成检查。Firefox 的 PCF、故意丢失上下文、滚动关联定位提示保留。
- `chromium-A1.png` / `A2` / `A3` 与 Firefox、WebKit 对应文件、`*-1366-A*.png`、`*-mobile-A*.png`：三站最终画面。`after-native-A*.png` 为正常模式对照。
- `*-contrast-background-A*.png`：测量对比度时暂时隐藏字面、保留雾影和场景的背景采集，测量后恢复文字；不是正常页面截图。
- `*-travel-*.png`：显隐、下降和柱底转场中间态。`*-context-check.json` 与对应前后图：完整操作序列中的图形恢复比较。
- `native-recovery.json` 与 `native-before/after-*.png`：原生 Chromium 的真实标签切换和下降中途恢复，未伪造可见性事件。
- `latency-before.json`、`latency-after.json`：同脚本、1440×900、固定环境时间、各 30 次实际滚轮停止。主要测量期间不截图、不并行运行其他浏览器检查。
- `before-cost-reduction-latency-after.json`：成本调整前 p95 242ms 的超预算数据；`cost-reduced-latency-after.json` 保留首次成本调整后的数据。原始峰值均保留，不用后续结果覆盖。
- `magic-reading-demo.mp4` 及 WebM、`demo-recording.json`：最终版固定环境、实际双向滚轮实录。
- `magic-ambient-demo.mp4` 及 WebM、`ambient-recording.json`：固定 A2 镜头、实际环境播放，正文稳定与符印附近画面变化单独检查。
- `decoration-fallback.json`、`decoration-font-fallback.png`：测试浏览器中禁用 Canvas2D 后仍可阅读、字体回退、返回入口及缓存程序预算对照。
- `fallback.json`、`no-webgl.png`：无 WebGL 的可读提示和参考稿入口。
- `after-reference-*.png`：默认参考稿与修改前的两模式逐像素对照。
- `summary.json`：最终源码保护、构建摘要、结果与交付边界。

`initial-*` 为首轮符印初始化降级时的诊断/测量；`calibration-*`、`context-debug*`、`context-fixed-*`、`shader-diagnostics.json` 和 `native-timeout-diagnostics.json` 为中间定位记录。它们保留用于溯源，不代表最终通过结果。`raw-recording/` 保留录制原件，视频不作为物理 GPU FPS 证据。

手机 200 字压力样本与狭矮横屏限制未被改写为通过。Linux WebKit、手机模拟与云软件图形环境均不等同于 Apple Safari、真实手机或硬件帧率验收。
