# 第九步证据索引

最终结论见 [验收报告](../../step-9-final-verification.md) 和 [平台覆盖表](../../step-9-platform-matrix.md)。当前目录保留原始日志，不把早期诊断截图当作最终通过依据。

## 最终结果

| 文件 | 含义 |
| --- | --- |
| [verification-chromium.json](verification-chromium.json) | Chromium 10 组通过，同环境第八步画布精确回归 |
| [verification-firefox.json](verification-firefox.json) | Firefox 9 组通过、诊断组附注；所有已知提示和故障注入日志保留 |
| [verification-webkit.json](verification-webkit.json) | GTK WebKit 10 组通过，含修复后的可见暂停画面与恢复 |
| [source-preservation.json](source-preservation.json) | 29 个保护文件前后摘要，5 个应用文件变动范围与最终源文件摘要 |
| [source-baseline.json](source-baseline.json) | 本步修改前的源文件/配置内容与摘要，供独立核对变动 |
| [network-and-size.json](network-and-size.json) | 最终产物三次限速、实际 gzip 传输与首屏测量 |
| [ten-minute-stability.json](ten-minute-stability.json) | 最终实现 604.48 秒墙钟播放、50 次模式变化，GPU 对象计数和原始软件帧间隔 |
| [scheduling-and-cleanup.json](scheduling-and-cleanup.json) | 暂停/隐藏事件停止工作、20 次销毁后的监听器和观察器清零 |
| [no-webgl-fallback.json](no-webgl-fallback.json) | 禁用 WebGL 的降级提示，预期故障日志保留 |
| [clean-build.json](clean-build.json) | 隔离安装与构建，6 个文件摘要一致 |
| [native-x11-events.json](native-x11-events.json) | 原生键盘缩放有效，标签页隐藏未能复现，不是物理屏幕/手机 |
| [final-summary.json](final-summary.json) | 最终机器可读汇总及未覆盖项 |
| [environment-draft-save.json](environment-draft-save.json) | 启动说明保存并读回确认；修订 4，未发布 |

每引擎的 `*-composition-{native,pixel}.png`、`*-desktop-{native,pixel}.png` 与 `*-mobile.png` 是对应最终功能检查输出。最终展示：

- [桌面](final-desktop.png)
- [手机尺寸（模拟）](final-mobile.png)
- [场景画布](final-composition.png)
- [无 WebGL 提示](webgl-unavailable.png)

色板截图是辅助材料。GTK 测试夹具的画布呈现可能滞后，因此棋盘验收采用同一绘制帧的 `gl.readPixels`；报告记录真实 GPU 黑白两色、错格 0，而不是依赖临时画布截图。真实场景另外检验了非空画面、实际截图与恢复前后一致。

## 过程记录

`initial-audit.json` 和 `baseline-{native,pixel}.png` 是修改前记录；`fix-verification.json` 是早期修复烟雾检查，不能替代后来的三引擎报告。`browser-discovery.json`、`discovery-*.png`、`webkit-debug-*`、`webkit-present-*`、`webkit-checker-debug.*` 是排查过程；其中存在尚未修复时的空白或旧帧。

`webkit-before-paused-fix.png` 与 `webkit-after-paused-fix.png` 展示暂停首帧问题及修复；`webkit-restore-debug.json` 和 `webkit-restore-*.png` 记录最终恢复后不同等待阶段与基准一致。`native-browser-events.json`、`firefox-native-tab.json` 保留未成功获得原生隐藏事件的尝试，不计验收通过。

所有场景截图采用固定时间 2 秒，除文件中另行说明。第八步视频保留为设计时间动效演示，不能用来证明硬件 FPS。云机器软件渲染与手机模拟都不替代实体设备测试。
