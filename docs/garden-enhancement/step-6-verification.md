# 第六步验收：三只风格化飞鸟

状态：第六步已完成，J01～J16当前环境验收通过；实体设备项目独立待验。执行范围见[第六步标准](step-6-standard.md)，实现见[记录](step-6-implementation.md)。当前候选`garden-enhancement-step6-487410d10d8ad600`，基线第五步`garden-enhancement-step5-fc6b56eb4157625e`。

## 执行与证据

| 项目 | 依据与实际检查 |
| --- | --- |
| J01 基线 | 第五步独立107文件快照；前五步1205个封存文件、10个旧release文件逐字节保护 |
| J02～J03 鸟形与风格 | 三只暖米白/灰青立体鸟，正常/像素画面全幅截图与原速视频复核 |
| J04～J06 航线与动作 | [模型检查](../evidence/garden-enhancement-step-6/motion-geometry-and-safety.json)：120环境秒密集采样；600秒逐顶点安全检查；静态物最近0.8304、鸟间最近0.4298，均超过0.25单位；CPU双精度参考中，肩部合并姿态与原分部矩阵等价误差约2×10⁻¹⁵单位，实际GPU单精度另验 |
| J07 文字避让 | [实际投影](../evidence/garden-enhancement-step-6/projection-motion-and-depth.json)：1440×900/1366×768/390×844、六个环境时刻与全路线共216组；整鸟轮廓避让实际UI和GPU魔法字样，桌面20px、窄屏14px |
| J08 深度与循环 | 实际GL深度探针、航线/翼角接点密集采样、三航线完整原速周期；探针的刻意着色/深度修改仅用于诊断，与普通视觉证据分开 |
| J09～J11 暂停与生命周期 | 全鸟世界/翼姿及完整GPU像素暂停保持、运镜往返不变；导览/环境四组合、真实隐藏、覆盖、离屏、作品返回及同画布现场体验 |
| J12 尺寸 | 三主尺寸、320窄屏、横屏、DPR2/3、CSS根字体200%及减少动态；不以CSS字体压力冒充OS缩放 |
| J13 兼容与恢复 | Chromium/Firefox/GTK WebKit各29组实际输入检查，真实GL丢失恢复、无WebGL完整十段阅读回退 |
| J14 构建与性能 | 92输入/18成品严格构建，最多新增1几何/1颜色调用/180三角形，0纹理/0全屏pass/0独立RAF；同CPU配置最终匹配性能通过，全部p95增幅符合10%目标 |
| J15 旧画面保护 | [关闭飞鸟对照](../evidence/garden-enhancement-step-6/birds-off-protection.json)：18组完整GPU、4组介绍实际RGBA、2组旧参考全页逐像素一致 |
| J16 同版本交付 | [构建](../evidence/garden-enhancement-step-6/build-verification.json)、[源码成品快照](../evidence/garden-enhancement-step-6/candidate-archive-manifest.json)、最终报告与视频统一指纹，最终逐字节重建、实际HTTP响应核验 |

上述当前环境项目均已通过，[六份最终回归报告索引](../evidence/garden-enhancement-step-6/fresh-regressions.json)绑定同一候选；三引擎各29组、原生生命周期10组、失败/字体2组，均无未处理异常。前五步历史封印与旧release文件保持；本步不进入第七步或进行Git提交、推送、部署、发布。

## 原速演示与性能口径

原速演示使用普通访客界面，`birds=inspect`只提供被动状态，没有调试面板或强制动作；整个场景与导览继续使用原时钟。全景覆盖超过61个实际环境秒，逐只观察48/54/61秒航线的相位接点、拍翼和滑翔；控制演示使用原按钮、真实滚轮、导航和现场体验。只转H264编码，保留原始时长；全幅抽帧不裁切、掩码或修图。

性能按同一1440×900/DPR1、完整预热、30次真实wheel、像素/正常模式分别ABBA、每轮240个匹配运动时刻比较，合并所有336个脚本/334个实际帧间隔样本，不选最好一轮。最终滚轮p95为210.5→218.5ms（+3.80%）；像素脚本4.8→4.6ms（−4.17%）、帧间隔100.0→99.9ms（−0.10%）；正常脚本6.3→5.9ms（−6.35%）、帧间隔283.3→266.7ms（−5.86%）。平均脚本开销分别约+0.104/+0.117ms，未把p95下降解释为整体更快。测试期间cgroup新增节流次数为零。详见[全部原始样本](../evidence/garden-enhancement-step-6/performance-comparison.json)。原生RAF时间和performance.now不改变；只对原渲染回调输入匹配运动时间，以确保相机、环境、云影和水体条件一致。此明确诊断不用于原速视频或硬件帧率证明。

旧候选的布局开销、CPU配额节流及三批绘制的尾部超限均完整保留，定位和修正见[实现记录](step-6-implementation.md)。最终复测的基线和候选使用相同三核亲和性，避免五核亲和性超过云环境四核配额；原场景质量、浏览器和软件图形驱动保持。最终p95增幅目标仍为10%，不会隐去初测或改变标准来签收。

实体iOS/Android、硬件GPU帧率、浏览器地址栏与系统字体/安全区、VoiceOver/TalkBack、实体触控板/APZ仍独立待验；当前桌面模拟和软件GPU结果不替代这些项目。

## 最终交付

[全景飞鸟原速演示](../evidence/garden-enhancement-step-6/birds-overview.mp4)87.12秒，实际环境从2.2666推进至65.0269秒，观察跨度62.7603环境秒/约81.53墙钟秒；三只鸟各跨过一次相位接点，均出现拍翼和滑翔。[暂停、运镜与滚轮接管演示](../evidence/garden-enhancement-step-6/birds-controls.mp4)56.60秒，包含现场体验和水潭。两段原始与输出时长完全一致；[时长与轨迹](../evidence/garden-enhancement-step-6/video-timing-verification.json)、[原图抽帧来源](../evidence/garden-enhancement-step-6/video-frame-origins.json)、[直接视觉复核](../evidence/garden-enhancement-step-6/video-frame-review.json)相互绑定。另保存12张最终正常访客全幅截图，包含两种画面模式、四个全景时刻和关于我/水潭近景。

最终严格重建与已测18个成品文件逐字节一致；候选独立快照113文件。两个本地成品端口的36个实际HTTP文件逐一核对200、MIME与SHA256，用户开发端口也为200，见[实际预览核验](../evidence/garden-enhancement-step-6/production-preview-verification.json)。[服务记录](../evidence/garden-enhancement-step-6/service-lifecycle.json)确认本步4180/4181及X104已关闭，保留用户5173/4173预览；没有发布网站。

[范围保护](../evidence/garden-enhancement-step-6/scope-guard.json)核对原6159文件：仅两处已有场景接入源码与可变进度入口变化，另新增六个飞鸟源码、当前文档/测试/证据。84个其余旧构建输入、前五步1205个封存文件及10个旧release文件未改写；Git HEAD保持`4d564f3a79e1e4cc84f9d08b043f9ac5b83c69e3`。本步不Git提交、推送、部署、发布，第七步未开始。

所有最终报告与历史试作由[结果绑定](../evidence/garden-enhancement-step-6/result-binding.json)、[封印清单](../evidence/garden-enhancement-step-6/evidence-manifest.json)和[签收摘要](../evidence/garden-enhancement-step-6/summary.json)统一登记；可变的progress.md不纳入历史封印。
