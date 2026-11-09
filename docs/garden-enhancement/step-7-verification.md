# 第七步验收：七步增强的最终候选

候选`garden-enhancement-step7-487410d10d8ad600`，基线`garden-enhancement-step6-487410d10d8ad600`。本文说明当次证据与口径；K01～K18最终签收状态见包外签收摘要与同名前缀的release版本总清单。实体设备与Windows实际操作独立列出，不作为桌面模拟已测。

## K01～K18与当次证据

| 项目 | 实际依据 |
| --- | --- |
| K01 基线 | [基线版本](../evidence/garden-enhancement-step-7/baseline-version.json)：独立113文件；前六步1428份封印及10个旧release原样保护 |
| K02～K05 画面与效果 | 三引擎全路线/实际216组整鸟安全区；[完整场景对照](../evidence/garden-enhancement-step-7/complete-scene-protection.json)18组完整GPU、4组介绍实际RGBA、2组旧参考全页逐像素一致；模型逐顶点、完整原速全景/水潭/三柱 |
| K06～K08 播放与导览 | 三引擎四组合/真实输入接管，真实终章与可打断重播；当次完整片13节点原生到位/截止/离站记录 |
| K09 作品 | 图片/档案/视频/现场体验，原位置与有效焦点返回、唯一画布；[实际视频失败重试](../evidence/garden-enhancement-step-7/video-failure-recovery.json)包含真实MP4错误与恢复解码 |
| K10～K11 生命周期 | [原生检查](../evidence/garden-enhancement-step-7/native-guide-recovery.json)10组，真实隐藏、有效缩放、图形丢失/恢复的完整鸟群画面；三引擎图片故障与实际无WebGL十段阅读 |
| K12 尺寸/浏览器 | Chromium/Firefox/GTK WebKit各29组，1440×900/1366×768/390×844；320窄屏/844横屏/DPR3/CSS根字体200%/减少动态代表组合，各报告列实际覆盖 |
| K13 性能/持续 | [最终匹配性能](../evidence/garden-enhancement-step-7/performance-comparison.json)、[总体资源成本](../evidence/garden-enhancement-step-7/overall-resource-cost.json)、[600秒持续运行](../evidence/garden-enhancement-step-7/endurance.json) |
| K14 构建/HTTP | [严格构建](../evidence/garden-enhancement-step-7/build-verification.json)、[实际预览](../evidence/garden-enhancement-step-7/production-preview-verification.json)和独立根/子路径检查 |
| K15 演示 | [完整导览](../evidence/garden-enhancement-step-7/final-guide.mp4)、[控制与持续运行](../evidence/garden-enhancement-step-7/final-controls.mp4)、[时长](../evidence/garden-enhancement-step-7/video-timing-verification.json)、[完整帧来源](../evidence/garden-enhancement-step-7/video-frame-origins.json)、[直接复核](../evidence/garden-enhancement-step-7/video-frame-review.json) |
| K16～K17 包与启动 | [启动/HTTP实跑](../evidence/garden-enhancement-step-7/launcher-and-http.json)、包外`package-verification.json`及三个`unpacked-*-integrity.json`，源码独立安装重建与成品实际浏览器核验 |
| K18 收尾 | 包外`scope-guard.json`、`service-lifecycle.json`、`result-binding.json`、`summary.json`及最终封印；真实服务、文档与保存状态核对 |

[当次回归索引](../evidence/garden-enhancement-step-7/fresh-regressions.json)包含11份新报告，另有本轮视频错误恢复、模型、资源、持续运行、独立启动/解压检查。历史报告只作为出处引用，不计作新跑次数。

## 原速与持续运行

完整导览213.48秒；控制/持续片687.92秒。两段原始记录与输出时长完全相同，只有H264编码转换，没有改时钟、强制姿态、加速或插帧。完整片有全景、十段正文、水潭和结尾13个完整到位节点，每个实际离站不早于原截止；实际总长不以早期2～3分钟草案代替已校准的阅读规则。

控制片的真实输入部分展示滚轮接管、两种播放独立、暂停翼姿、同画布现场体验和水潭。预热后600.207秒，20轮原按钮操作与明确标为测试设置的原生scroll API路线定位；几何59/纹理6/程序24保持稳定。第一段连续全景观察覆盖189.5916环境秒，超过32/0.22≈145.45秒云影周期及48/54/61秒鸟路，三只均记录拍翼和滑翔。暂停后保留完整鸟姿并进入零闲置绘制窗口。

`birds=inspect`只提供被动状态，不改变普通访客UI。CPU/GL诊断明确另标，不作为原速运动或硬件帧率证据。抽帧保留完整1440×900，不裁切、修图或遮罩。

## 性能与整体成本

第六步与最终应用92输入/18成品逐字节一致，交付启动/打包脚本独立计量。匹配性能保持五项效果开启，同一浏览器/软件渲染、1440×900/DPR1、完整预热、CPU亲和性和环境/相机时刻；真实30次wheel，两模式ABBA保留全部样本。脚本耗时和实际帧间隔分开报告，p95增幅目标10%，超限不直接签收。

三核亲和性用于避免云环境五核亲和性超过四核cgroup配额；原生RAF和performance.now保持，仅在明确的匹配诊断中控制原渲染回调的运动时间戳，不能将该诊断当作原速操作录像。总体成本另从原始独立版本实测资源总量，原版本没有导览，不把不匹配的导览耗时或历史百分比直接相减相加。

## 打包与设备边界

新源码/成品/验收包使用候选独立文件名，旧10个release不覆盖。包内逐文件清单不包含自身，ZIP最后哈希与独立解压结论登记在包外总清单；最终报告因此不会循环包含自己。源码独立目录使用锁定依赖重建，成品用实际包内Node工具与独立检查器验证HTTP、真实子路径、关键交互和失败退路。

共享Node入口已在独立中文/空格目录实跑，含36个生产响应、视频Range、HEAD/404、端口回退/严格冲突、缺构建与错误参数。WindowsCMD做CRLF/路径/npm.cmd/错误分支静态检查。实体Windows双击与自动打开浏览器，实体iOS/Android、硬件GPU FPS、地址栏/系统字体/安全区、VoiceOver/TalkBack及实体触控板/APZ仍待相应实体环境复核；GTK WebKit不等于iOS Safari真机。

源码/成品/验收文件用途见[交付说明](delivery.md)，操作见[快速上手](quickstart.md)，替换真实内容见[维护](maintenance.md)。本步本地交付不代表GitHub已同步或网站已发布。

## 最终性能判断与保留的诊断

最初相同三核配置下，滚轮p95约+10.92%，像素脚本约+37.78%、帧间隔约+19.78%；原始全8轮保存在`versions/garden-enhancement-step7-487410d10d8ad600/initial-performance/`。业务92输入/18成品完全一致、资源配置一致，这些结果没有直接标为达标。

对两项使用交错顺序复测，全部首轮和完整新轮合并：每侧90次wheel的p95为214.2→209.4ms（−2.24%），正常模式沿用已通过的全部336脚本/334间隔样本，p95为7.0→6.5ms（−7.14%）、300.0→266.7ms（−11.10%）。同配置像素合并672脚本/668间隔样本后仍未达到脚本目标，该阶段记录完整保存在`pooled-default-cpu/`，不冒称通过；一次因后处理拼写检查而中断的记录也独立保留，未当完整ABBA比较使用。

最后仅对未解决的像素组，在两侧测试Chrome子进程中安排相同的脚本主线程CPU与图形/worker CPU，并在每轮前执行同样的真实隐藏/显示步骤。此独立CPU配置的全部336脚本/334间隔样本：脚本p95为1.7→1.8ms（+5.88%），间隔116.7→116.7ms（约0%），符合10%目标。线程分配/原始采样见[隔离对照](../evidence/garden-enhancement-step-7/performance-isolation.json)；只调整自有测试子进程，不改变访客网页或全局系统配置。

最终接受滚轮、正常模式与隔离像素各自同条件的前后比较，不混算不同CPU配置，也不把隔离后的绝对数字解释为产品变快。所有初测、阶段复测和最终配置都保留；最终源码与第六步一致，当前结论是交付版本在上述实测条件下没有超出本步性能目标。实体GPU帧率仍待实测。
