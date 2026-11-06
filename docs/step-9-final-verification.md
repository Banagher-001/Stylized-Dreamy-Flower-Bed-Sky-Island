# 第九步：最终工程验收

第九步为本轮最后的工程收尾阶段，已完成可在当前云环境执行的检查、必要修复和交付打包。当前文件属于未发布草稿。真实设备覆盖尚不完整，因此不能把工程交付完成等同于所有平台、所有性能指标通过。

## 画面冻结与修复范围

保留第八步的固定正交相机、构图、石材、植物分布、色彩、光照、水体、像素管线和环境微动。默认仍为 384 长边采样、最近邻、原色，飘花默认关闭。没有添加新的视觉阶段。

修改了 5 个应用文件：

| 文件 | 最终修改 |
| --- | --- |
| `src/styles.css` | 所有按钮至少 44×44 CSS 像素；添加图形恢复提示样式 |
| `src/config/palette.ts` | 仅页面辅助文字由 `#73806A` 改为 `#58664F`；场景色板不变 |
| `src/main.ts` | 空 `waterTime` 使用默认状态；图形恢复提示、控件禁用/恢复、无 WebGL 错误语义和恢复时间基准 |
| `src/animation/createAnimationController.ts` | 暴露已有时钟的时间基准重置方法；纯时钟算法不变 |
| `src/rendering/createRenderer.ts` | 销毁时归还上下文槽位；恢复通知；合并有限次静止帧重绘，修复 WebKit 首次暂停与恢复后画布空白 |

WebKit 的问题发生在提交画面与浏览器合成的时序上：场景数据与 GPU 颜色正确，但暂停状态下没有持续动画帧，初始画面可能不显示。修复后按需在浏览器帧内绘制，恢复提示消失后再提交一帧；静止后不保持循环。

29 个受保护的源文件/构建配置与本步开始前 SHA-256 一致；另核对场景色板及纯时钟实现保持。完整记录见 [源码保护摘要](evidence/step-9/source-preservation.json)。同一 Chromium/渲染环境中，固定时间 2 秒的正常、像素画面均与第八步基准逐像素相同。页面文字和按钮的变化不计入场景画布比较。

辅助文字在纸色背景上的对比度由约 3.88 提高至 5.69，在按钮浅色悬停背景约为 4.63。此项是颜色计算与控件检查，不代表完成屏幕阅读器或全部 WCAG 认证。

## 最终执行表

| 项目及标准 | 执行结果 | 证据 |
| --- | --- | --- |
| 画面冻结；参数和场景不发生意外变化 | 同环境基准完全一致，保护文件一致 | `source-preservation.json`、`verification-chromium.json` |
| 三种浏览器引擎正常/像素模式、实际可见画面、生产与开发一致 | Chromium、Firefox、GTK WebKit 功能通过 | `verification-{chromium,firefox,webkit}.json` |
| 宽 280～1920、横屏、DPR 1/1.25/1.5/2/3、输出上限 2、触达 ≥44 | 每引擎 7 组组合通过，无横向溢出；手机为模拟 | 三份引擎报告第 6 组 |
| 键盘、焦点、状态、暂停、减少动态 | 三引擎通过；减少动态使用浏览器偏好模拟 | 三份引擎报告第 4、5 组 |
| 原生浏览器缩放；后台、跨屏及系统偏好 | X11 键盘缩放 80%～200% 触发真实 DPR 变化并通过；其他范围见平台表 | `native-x11-events.json` |
| 实际 gzip、1.6Mbps/150ms、冷 HTTP 缓存，可见/可操作 ≤5 秒 | 三次均通过，最慢可见 2.47 秒、首次模式切换 2.92 秒 | `network-and-size.json` |
| 首屏压缩资源目标 ≤200kB | 实测响应体合计 164,553 字节，含重复 favicon；不含 HTTP 头 | `network-and-size.json` |
| 连续墙钟 ≥10 分钟、50 次模式变化、资源稳定 | 604.48 秒通过，20 个采样点，最终 GPU 活跃对象计数一致 | `ten-minute-stability.json` |
| 每引擎 20 次初始化/销毁，主画面继续工作 | 60/60 上下文槽位释放；另外 20 次检查监听器/观察器归零 | 引擎报告、`scheduling-and-cleanup.json` |
| 每引擎 2 次实际上下文丢失/恢复 | 6/6 恢复，固定暂停画面一致、控件可用 | 三份引擎报告第 7 组 |
| 半浮点与 sRGB8 两条采样路径 | 三引擎色板最大通道差 0；同帧 GPU 棋盘错格 0、仅黑白两色 | 三份引擎报告第 8 组 |
| 无 WebGL 时明确提示、无残留画布/可点击失效控件 | 真实禁用 WebGL 后通过；预期故障日志单列 | `no-webgl-fallback.json` |
| 控制台无未识别异常、无 HTTP 失败 | 三引擎均无未识别异常；Firefox 有已知提示，零警告标准未满足 | 三份引擎报告第 10 组 |
| 桌面 ≥55 FPS/p95≤25ms；中档手机 ≥30 FPS/p95≤50ms | **未实测物理硬件，未判定达标** | 平台覆盖表 |
| 隔离目录安装并构建；产物可复现 | 未复用原 `node_modules`；`npm ci`、严格类型检查、构建通过，6 个产物摘要相同 | `clean-build.json` |
| 文档、源文件包、静态网页包与摘要 | 已交付，未执行部署或发布 | `release/manifest.json` |

上表中的证据文件位于 [本步证据目录](evidence/step-9/README.md)。宽度与 DPR 为 7 组代表性组合，没有声称遍历所有排列。

## 浏览器结果的准确含义

每引擎 10 组检查，合计 29 组 `passed`、1 组 `passed_with_notes`。Chromium 155.0.8059.79 和 GTK WebKit 26.5 没有警告或错误。Firefox 153.0 的功能检查通过，诊断组保留说明：29 条同类深度比较采样提示，另有 24 条故意丢失/释放上下文时产生的预期日志，未识别问题为 0。

Firefox 的原始提示包含 `Depth texture comparison requests ... LINEAR ... behavior is implementation-defined`。它来自 Gecko 对深度比较过滤的实现提示，当前使用 Three.js 的 PCF 阴影路径。没有过滤原始输出，也没有更换阴影外观来消除提示。Firefox **零警告目标未满足**；不同硬件上的阴影边缘仍需实机观察。上游提示位置可查 [Gecko WebGLTexture.cpp](https://github.com/mozilla/gecko-dev/blob/master/dom/canvas/WebGLTexture.cpp)。

三个引擎均在 Linux 云机器上运行，采用软件渲染。GTK WebKit 不是 macOS/iOS Safari；其返回的 `Apple GPU` 字符串不能证明存在 Apple 物理 GPU。跨引擎不要求整个画面逐像素相等；测试分别检查可见画面、同引擎开发/生产一致、模式切换和实际 GPU 色板。

## 稳定性与性能边界

10 分钟检查实际等待墙钟时间，没有通过推进设计时间代替。GPU 活跃对象在前后及 20 个采样点保持：181 Buffer、7 Texture、16 Program、145 VertexArray、5 Framebuffer、1 Renderbuffer。计数包含引擎内部资源，与应用层 Three.js 的几何体统计口径不同；这些数值不是显存字节数，也不单独证明任意时长都无泄漏。JS 堆采样保留原始记录，没有把未控制 GC 的波动当作精确泄漏结论。

本次软件环境每分钟平均约 17.4～24.6 FPS，存在长帧，且其他浏览器检查可能竞争云机器资源。这是压力诊断记录，**不用于证明桌面或手机帧率目标达标**。真实硬件测试方法及待测清单见 [平台覆盖与实机补验](step-9-platform-matrix.md)。

暂停后 1 秒的 RAF/绘制计数不再增长，模式变化后也会停止重绘。隐藏事件路径验证了停止绘制和冻结时间，但原生标签页切换在自动化 Xvfb 中未观察到 `document.hidden=true`，不能按原生后台测试通过处理。

弱网数据来自本机实际 gzip 服务加浏览器网络限速：模拟 HTTP 冷缓存，不包含公网 DNS、TLS 建连、CDN 和真实移动网络波动，也没有模拟手机 CPU。正式托管后应在实际域名复核加载指标。

## 最终画面与交付

- [桌面最终截图](evidence/step-9/final-desktop.png)
- [手机尺寸最终截图（模拟）](evidence/step-9/final-mobile.png)
- [场景画布](evidence/step-9/final-composition.png)
- [交付与重现说明](step-9-handoff.md)
- [可选复验工具](../tests/final/README.md)

第八步的 [12 秒动效视频](evidence/step-8/environment-demo.mp4) 继续适用于保留的场景动效；它按设计时间采样，不能充当实机 FPS 证据。

云环境启动说明已更新为第九步状态，并读回确认保存到草稿修订 4；安装脚本、仓库、网络与凭据要求保持。保存不会执行启动脚本或发布，新的云任务恢复没有另行验证。见 [草稿保存记录](evidence/step-9/environment-draft-save.json)。

本轮到此结束。平台缺口明确保留，当前草稿未发布，网站未部署，仓库未提交或推送。
