# 第一步验收：独立原页基线

第一步基线完成，原有问题与环境限制已单列；这不表示所有路径通过，也不表示已接入 Coding。日期：2026-11-13（Asia/Shanghai）。执行仅新增文档、测试脚本与证据，原成品、个人网站和罗森运行文件保持原样，未提交、上传或部署。

| 结果 | 数量 / 说明 |
|---|---|
| 采用的检查记录 | 51 |
| 通过 | 46 |
| 原页已有问题 | 3 |
| 设备/浏览器限制 | 2 |
| DOM 控件 | 12 滑杆 + 22 按钮，逐项均有操作与确定结果；其中默认亮度和镜头恢复的原问题另外保留 |

版本与环境：

- 原提交 d94c1f911a39143fd8f5efe152b99a87fdc53184，成品 SHA256 941feb2ea6ddd3cc93aad5b0b92dbca52ee66a3e1098fee0dbf16f01ca63d1ef；两 HTML 字节一致，未重构建。
- Linux；Chromium 155.0.8059.79、Firefox 153.0、Linux WebKit 26.5，均实际启动有界面浏览器。
- Chromium WebGL2 为 ANGLE/Mesa llvmpipe；Firefox 报告 llvmpipe；运行环境设置 LIBGL_ALWAYS_SOFTWARE=1。WebKit 的隐私化 renderer 字符串为 Apple GPU，不代表真 Apple 硬件或 Safari 真机。
- 先在 1920×1080、1440×900 / DPR1 记录原 fine 默认画面；主要控件/模拟检查随后通过原按钮选 retro，1024×768。代表兼容为 1280×720，手机模拟 390×844 与 844×390 / DPR3。
- 所有浏览器外部 HTTP 尝试为 0；原服务 no-store、测试路由关闭缓存，再次加载不声称是热缓存验证。未安装/升级原产品依赖，未执行旧 QA 替代本轮验收。

主要结果：

- HTTP 首次/再次加载和 Firefox file:// 冷启动呈现完整世界；实际场景含三桅船、瓶内水、玻璃、天空、沙地、外海和灯塔，并有真实绘制。
- 34 控件、原指针/按键、沙盒对象、播放/全局恢复、镜头和实际 PNG 下载详见 [功能矩阵](feature-matrix.md)。Firefox/WebKit 只覆盖代表操作，没有冒充全量 34 控件复验。
- 原生截图按钮生成了 1920×1080 PNG；960×600 / DPR3 生成 1920×1200，证实 DPR 上限 2。已查看真实下载图像，包含场景且不含 DOM 面板。隐藏 UI 后仍聚焦原按钮的键盘导出也有实测。
- 实际故障注入覆盖 Chromium 禁用 WebGL 与 WEBGL_lose_context；前者有预期初始化错误日志，正常路径没有 pageerror 或 console.error；后者刷新恢复。

连续联动：

| 原波高 | 实际模拟窗口（秒） | 不同渲染帧 | 采样墙钟（秒） | 水面峰谷差 | 船体高度峰谷差 |
|---|---:|---:|---:|---:|---:|
| 0 | 8.0309 | 176 | 8.75 | 0.000000 | 0.000000 |
| 50 | 8.0137 | 174 | 8.80 | 0.132192 | 0.152645 |
| 100 | 8.0303 | 174 | 8.71 | 0.243476 | 0.280599 |

原生 UI 设置、自然过渡后逐真实渲染帧只读取数；simTime 与 GPU 水面时间一致。方向、响应/阻尼/风力、代表强浪/水位组合亦有连续样本和截图。没有改 dt、时钟、RAF 回调参数、物理系数、随机数或船体姿态；部分观测包装以原参数调用原函数一次。脚本数据只能支持已测组合，不能证明所有条件绝不穿模或硬件 60 FPS。

原问题与未验证：

- 原亮度默认值与 range 步进差异；运行中图形丢失后旧 ready、错误标志与遮罩的缺口；镜头恢复的残余惯性，详见 [原问题清单](original-issues.md)。
- 受管 Chromium 禁止 file://；Firefox 文件直开通过。两种真实标签切换方式仍未观测到 hidden，后台恢复/节流未验证。手机为触摸模拟；真机、其他系统、硬件性能与穷举边界未验证。
- 完整 iframe 接入、资源回收和主站隔离属于后续步骤，本步不预先宣布这些通过。

复测和证据：

- 初次灯塔点选遮挡、风力断言过严、手机操作未展开面板等失败原始记录均保留；复测分别采用 interactions-picking-retest、physics-wind-retest、chromium-mobile-file-retest，没有覆盖首次失败。
- [final-summary.json](../evidence/beach-bottle-boat-step-1/final-summary.json) 逐条列出采用记录、浏览器版本、成品摘要和 JSON 位置；rawRuns 保留每轮原始状态。环境限制不计通过。
- [默认 1920 画面](../evidence/beach-bottle-boat-step-1/controls/default-1920x1080.png)、[默认 1440 画面](../evidence/beach-bottle-boat-step-1/controls/default-1440x900.png)、[真实场景下载](../evidence/beach-bottle-boat-step-1/interactions/export-1920x1080-ui-visible.png)、[原始证据目录](../evidence/beach-bottle-boat-step-1)、[本步脚本](../../tests/beach-bottle-boat-step-1)。

完整性和收尾：

- 原仓库 44 个文件摘要和提交不变，git status 干净；主站 95 项生产输入、罗森 46 个运行文件、八组旧封存及各自文件全部复核一致。
- 本步浏览器均关闭，专用 HTTP 服务和 Xvfb 按启动 PID、参数和启动时标核对后停止；未停止其他服务，见 [清理记录](../evidence/beach-bottle-boat-step-1/services-cleanup.json)。
- 本步资料和证据另建 SHA256 清单 [evidence-manifest.json](../evidence/beach-bottle-boat-step-1/evidence-manifest.json)；复核命令：python tests/beach-bottle-boat-step-1/finalize.py --verify-only。

下一步承接见 [step-1-handoff.md](step-1-handoff.md)。第二步仍待用户细化/执行指示。
