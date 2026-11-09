# 第四步验收：自动导览与手动接管

状态：**第四步已执行完成，H01～H16当前环境验收通过；实体设备项目独立待验证。** 候选`garden-enhancement-step4-2b6d5479a1939f3e`，基线为第三步`garden-enhancement-step3-79dad8c41ee79a61`，不是GitHub上的旧提交。[最终签收](../evidence/garden-enhancement-step-4/summary.json)及[本步封印](../evidence/garden-enhancement-step-4/evidence-manifest.json)绑定当前版本。

## 已核对的行为

顶部单一按钮从当前位置开始，运行中可停止，接管后明确继续，结尾只提供明确重新导览。底部“播放环境/暂停环境”保持独立。当前段落完整显示、成功图片解码且相机稳定后，经过两个实际完整帧才开始完整阅读时间。默认不开启，不自动打开作品或视频，不跨刷新追赶。

三引擎主回归各29组，共87组；故障/容量为Chromium6组、Firefox5组、WebKit5组，共16组。实际节点检查覆盖十站×三主画幅×三引擎，共90次完整阅读站开启；各引擎至少20轮真实开始/停止。所有数字只计本步新跑，不把第一/二/三步历史结果冒充重测。

| 编号 | 当前结论 | 依据 |
| --- | --- | --- |
| H01 正确基线 | 通过 | 第三步独立102文件快照核对，当前候选另有104文件快照；79/355/226份旧封印校验；[基线](../evidence/garden-enhancement-step-4/baseline-version.json)、[范围保护](../evidence/garden-enhancement-step-4/scope-guard.json) |
| H02 状态与续接 | 通过 | 默认manual，未开始过时作品关闭仍manual；从实际当前位置续接，不向旧站回弹；[控制器确定性检查](../evidence/garden-enhancement-step-4/controller-deterministic.json)及三引擎真实操作 |
| H03 阅读与准备 | 通过 | 90次实际站点标题/正文完全显现后计时；每引擎一次真实A1最低截止唤醒到A2；延迟图片成功、8秒超时、迟到图片不复活、错误占位及解码拒绝不自旋均通过 |
| H04 完整路线与收尾 | 通过 | [211.68秒原速完整片](../evidence/garden-enhancement-step-4/auto-guide-full.mp4)自然经过13节点并在终章停止；每个实际离站均不早于完整截止；另验真实六秒终章及[可打断重播](../evidence/garden-enhancement-step-4/replay-native-takeover.json) |
| H05 输入接管 | 通过 | 实际wheel反向、原生键盘、鼠标选字/可信copy、Chromium原生触摸滚动、FF/WK真实touch tap；另有真正的原生滚动条拖动，非DOM scroll替代 |
| H06 所有权与取消 | 通过 | 首次从静止阅读站开启也识别外部位置改变；原生输入不被preventDefault，代次+句柄拒绝旧回调；二十轮取消及过期回调专项通过 |
| H07 两种播放独立 | 通过 | 九组主要画幅分别验证四组合；环境暂停时导览阅读连续450ms零GL，截止唤醒原循环；停止导览后水体维持原选择 |
| H08 画面切换 | 通过 | 正常/像素往返保持导览deadline及环境时间，暂停GPU画面逐像素恢复 |
| H09 查看器返回 | 通过 | 原生位置误差≤1CSS px，图片/项目返回原有效焦点，现场体验唯一原画布，视频关闭释放，导览不自动续播 |
| H10 隐藏/布局/RM | 通过 | 真CDP标签页切换、方向尺寸/实际scale变化、真实减少动态偏好和离屏停绘；旧截止过后仍停在原位置；[原生恢复](../evidence/garden-enhancement-step-4/native-guide-recovery.json) |
| H11 图形与失败 | 通过 | 真实上下文丢失、查看器中丢失并关闭、恢复不重启；无WebGL实际失败保留十段阅读及参考入口 |
| H12 画幅与可读性 | 通过 | 三主画幅、320×568/844×390及DPR1/2/3；CSS根字体200%压力下十节点无溢出；真实手机/系统缩放另列，未混淆 |
| H13 资源 | 通过 | 三引擎桌面各20轮，另两画幅各4轮开始/停止，几何/纹理/程序保持；不增加GPU资源、无限RAF或interval |
| H14 视觉与内容 | 通过 | [18组完整GPU画布、4组介绍实际RGBA及2份整页参考](../evidence/garden-enhancement-step-4/scene-and-background-protection.json)逐像素一致；背景CSS、水球、路线、素材和正文的原输入字节保持 |
| H15 构建与性能 | 通过 | 严格构建；原30次wheel p95下降2.11%；像素匹配回放通过，正常画面超阈值首轮保留并完成ABBA同路径复测，最大最终p95增幅9.96%＜10%；[最终比较](../evidence/garden-enhancement-step-4/performance-comparison.json) |
| H16 版本与交付 | 通过 | 最终严格重构建83输入/18成品字节一致，独立104文件快照、两段原速录像与[结果绑定](../evidence/garden-enhancement-step-4/result-binding.json)齐全；不开始第五步 |

三引擎原始报告：[Chromium](../evidence/garden-enhancement-step-4/browser-chromium.json)、[Firefox](../evidence/garden-enhancement-step-4/browser-firefox.json)、[GTK WebKit](../evidence/garden-enhancement-step-4/browser-webkit.json)。故障注入分别见[Chromium](../evidence/garden-enhancement-step-4/faults-chromium.json)、[Firefox](../evidence/garden-enhancement-step-4/faults-firefox.json)、[WebKit](../evidence/garden-enhancement-step-4/faults-webkit.json)。

## 原速演示与交付核对

[完整导览211.68秒](../evidence/garden-enhancement-step-4/auto-guide-full.mp4)从明确开始到终章自然结束，环境保持正常播放。实际Mutation记录的13段停留分别不短于4、10、14、14、12、10、10、8、10、12、12、8、6秒；[实际时间核对](../evidence/garden-enhancement-step-4/video-timing-verification.json)逐站保存到位、截止与离站时刻，没有通过改变时钟缩短阅读。

[接管/续播13.8秒](../evidence/garden-enhancement-step-4/auto-guide-takeover.mp4)展示A2真实反向wheel接管、人工到A3、从A3继续、画面与环境设置保持停留、停止导览后环境继续，以及最后静止零绘制。两段MP4与各自原始记录时长完全相同；仅H264编码转换，不变速、不补画面。另有[真实终章/重播接管](../evidence/garden-enhancement-step-4/replay-native-takeover.json)，不是只检查按钮文字。

五张完整录像帧的[来源](../evidence/garden-enhancement-step-4/video-frame-origins.json)和[直接视觉审阅](../evidence/garden-enhancement-step-4/video-frame-review.json)保留，分别覆盖A2、B2、水潭、终章和正常画面续播；没有裁切、掩码、缩放、覆盖或修图。抽帧审阅与逐站实际状态记录合用，不冒充全片逐帧审查或实体帧率。

最终严格构建字节与全部最终浏览器测试一致；[HTTP核对](../evidence/garden-enhancement-step-4/production-preview-verification.json)对独立成品4177和用户预览4173逐一请求18文件，共36次状态、MIME、SHA校验。测试结束仅停止本步4176/4177和自建X102，保留5173开发服务及4173预览，[服务记录](../evidence/garden-enhancement-step-4/service-lifecycle.json)单列。旧三步封印及10份旧release文件保持。

## 性能口径与完整保留的数据

单浏览器，任何时刻只有一个页面实际渲染/采样，两页均从原pixel/native/pixel完整路线预热；没有其他浏览器、截图或录像并行。导览关闭时真实30次wheel p95为189.7→185.7ms。导览开启时实际记录A3→B1的原7秒移动，再在第三步成品中回放同一原生位置与动画采样时间，锁定相机/环境/模式；环境固定2秒。首轮113个像素样本、89个正常样本的相机坐标误差为0。

回放注入scroll通知属于测试工具，不冒充真实用户输入。帧工作量计时包含导览控制器+渲染，基线包含等价原生位置写入+通知+原渲染；纯回调数据也保留。实际帧间隔来自原生RAF时间戳，CPU耗时来自真实performance.now。没有拿静态零绘制与导览运行直接比较。

像素首轮脚本工作p95约−18.18%，绘制间隔约−19.93%。正常首轮脚本工作p95约+31.25%，绘制间隔不变，**该异常没有删掉或直接签收**。[首轮全部样本](../evidence/garden-enhancement-step-4/performance-matched.json)保留。

针对正常画面使用前/后/后/前顺序复测：仅测试包装器给导览传入原采集运动时间戳以锁定完全相同轨迹；真实performance.now及原生RAF实际时刻不改写，既不作为用户实时操作证明，也不作为原速录像。每轮保留89个脚本样本、88个帧间隔，各版两轮全部合并178/176个样本，**不选择最好一轮**。相机H误差为0，脚本p95约−22.67%，绘制间隔166.7→183.3ms（约+9.958%），符合预设10%界限。[全部ABBA数据](../evidence/garden-enhancement-step-4/performance-native-recheck.json)及[最终判断](../evidence/garden-enhancement-step-4/performance-comparison.json)保留，期间没有修改产品代码。

这些是Linux SwiftShader比较，不是实体GPU完成耗时或真机FPS保证。

## 故障、工具边界与保护说明

已修正旧截止回调覆盖新句柄、首次静止站缺少滚动锚点、暂停环境后图片完成缺少唤醒三处问题。原始诊断与两个中间候选源码/成品、旧回归记录保留在本步证据目录；最终报告均指向上述最终候选。

故障测试只挂起真实图片请求，放行开发模块，等待DOM和布局就绪而非故意无法满足的网络空闲；404及decode拒绝注入明确标记。原生键盘滚动与触摸惯性允许自然结束，再检查无自动推进。原生滚动条采用真实窗口内1366×768视口避免窗口边缘裁切；1440×900已在三引擎主回归覆盖。没有伪造document.hidden或用合成visibility事件当实际后台检查。

纯GPU对照仅等量隐藏DOM文字/控件以隔离整个原始GPU画布，保留所有三维与GPU文字，**没有裁掉水潭、加掩码或使用容差**；未改画面的完整页面另外保存。介绍背景用真实RGBA像素比较。无WebGL采用真正禁用图形初始化，完整原文仍可阅读。

## 尚需实体设备的项目

Chromium155、Firefox153及GTK WebKit26.5是本步实际引擎；GTK WebKit不等于实体iPhone Safari。真实iOS/Android、设备GPU帧率、浏览器地址栏升降、系统字体缩放、缺口安全区、VoiceOver/TalkBack及实体触控板/APZ需要相应设备，本轮未提供，独立待验证。CSS字体压力、桌面触摸能力与浏览器viewport不能冒充这些实体项目。

本步保存在工作区，不Git提交、推送、部署或发布，旧release ZIP不重封。云影、飞鸟与第五步均未开始。
