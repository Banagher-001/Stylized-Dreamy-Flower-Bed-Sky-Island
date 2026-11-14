# 第五步验收：完整瓶中海洋在 Coding 内运行

第五步完成：选择 BOTTLE OCEAN，点击“进入完整网页”，会在大尺寸查看器中运行原网页。原控制台、海浪与船体、镜头、沙盒、快捷键和 PNG 下载继续由原页面执行；支持慢载入、失败反馈、重试、档案往返和返回阅读。本轮未提交 GitHub、上传或发布。日期：2026-11-13（Asia/Shanghai）。

这是第五步的代表功能与接入验收。第六步的系统隔离/异常检查和第七步的全部原功能对照尚未执行；第二步仍只有标准，没有补记成已执行。

## 实际实现与保护

新增 `createEmbeddedPageExperience.ts` 和 `createBottleOceanExperience.ts`。共用容器管理 iframe/文档/画布归属、观察、重试和清理；瓶中海洋适配器只读原就绪、加载、错误及实际图形信号。现有罗森工厂保留原判据并使用共用容器。编排接通当前作品，查看器反馈/重试扩大到当前独立网页，入口文案与真实能力一致。

相对第四步候选，4 个已有生产输入改变，另增 2 个模块；其余 91 个既有输入不变，`projectHost.css` 与 `createExperimentReader.ts` 保持第四步状态。原未提交工作作为 before 保留。准确本步差异见 [step-5.diff](../evidence/beach-bottle-boat-step-5/step-5.diff)，`product.diff` 是从 git HEAD 起的累计差异，不能把其中第四步内容归为本步重新实施。

原仓库提交为 `d94c1f911a39143fd8f5efe152b99a87fdc53184`；完整原 HTML 仍是 1,979,264 字节，SHA256 为 `941feb2ea6ddd3cc93aad5b0b92dbca52ee66a3e1098fee0dbf16f01ca63d1ef`。public 与本次构建内一致，没有重构建、裁剪、注入或改默认参数。原仓库 44 文件、罗森 46 运行文件、真实封面及 11 组既有历史封存校验通过；原 dist 的 65 文件没有覆盖。实际候选 97 项输入见 [candidate-manifest.json](../evidence/beach-bottle-boat-step-5/candidate-manifest.json)。

## 20 项执行标准

| ID | 实际结果 | 主要记录 |
|---|---|---|
| S5-01 | 第四步候选固定为 before，原资源与历史完整 | baseline、candidate、final-summary |
| S5-02 | 浏览卡片/档案不请求运行 HTML、不创建 iframe；仅现场加载正确同源入口，原控制台可用 | LIVE.lazy、LIVE.ready |
| S5-03 | 当前 API、原 renderer/canvas、有效尺寸、绘制、loader 和错误信号组合就绪；错误页、初始化失败与旧 ready 均不能假成功 | LIVE.ready、FAULT.error-retry/initialization/graphics |
| S5-04 | 原生波高 0/100 使真实水面/船体联动；曝光、玻璃、环境开关和俯视镜头有实际对象/画面变化 | CORE.controls |
| S5-05 | 原生点击形成石头与贝壳对象；撤销、恢复装饰、Escape 退出编辑、暂停和继续有效 | CORE.sandbox-pause |
| S5-06 | 左旋、右移、滚轮、H/Space/Escape 保留原归属；输入框焦点保护、Tab/Shift+Tab、宿主 Escape/返回正确 | INPUT.keys-download、INPUT.focus |
| S5-07 | 两种子视口/DPR 下原按钮真实下载 PNG，尺寸与场景内容正确；另有两引擎真实下载 | INPUT.keys-download、PATH.prefix、visual-review |
| S5-08 | 原请求实际等待满 12 秒进入 slow，原字节响应释放后自然 ready，不把首次响应当重新计时 | FAULT.slow |
| S5-09 | HTTP 200 错误文档和真正 WebGL 创建失败均为 error；原重试按钮创建新文档恢复 | FAULT.error-retry、FAULT.initialization |
| S5-10 | 真实扩展 lose/restore、trusted 原 canvas 事件已记录；原 ready 仍真时保持 error，新文档重试恢复 | FAULT.graphics |
| S5-11 | 连续失败重试和待响应时重试始终最多一个 iframe，旧响应不覆盖新状态 | FAULT.error-retry、LIFE.pending-exit |
| S5-12 | 原请求待响应时关闭/去档案移除旧文档；迟到响应不再挂回现场 | LIFE.pending-exit |
| S5-13 | 档案往返恢复原默认波高 35/无用户装饰，新 timeOrigin；同 iframe 重载取得新 Document 并重新就绪 | LIFE.navigation |
| S5-14 | 罗森错误文档→原按钮重试→原 __LAWSON__ 就绪；退出切瓶中海洋无串状态或双实例 | REGRESS.lawson |
| S5-15 | 庭院正常/像素、动效、视频与水潭入口正常；宿主 WebGL 创建失败时子网页仍真实运行 | REGRESS.courtyard、FAULT.host-graphics |
| S5-16 | 覆盖时庭院实际停绘、子页持续绘制，返回恢复阅读/焦点和原播放选择，活动导览停止后不自行继续；跨尺寸返回保留阅读锚点 | RESOURCE.return、LAYOUT.resize；真实 hidden 未观测，见限制 |
| S5-17 | 四种视口、小屏原控制台滚动、真实触摸、根字号 200% 及同一原文档连续变尺寸可用 | LAYOUT.sizes、LAYOUT.resize |
| S5-18 | 包含类型检查的生产构建成功；根路径及实际 /portfolio-check/ 内嵌/独立链接正确，构建原 HTML 摘要不变 | build、PATH.prefix |
| S5-19 | 三引擎均实际加载、参数/镜头、快捷键/焦点、真实 PNG 下载和关闭返回；范围为代表检查 | Chromium、Firefox、Linux WebKit 记录 |
| S5-20 | 差异、独立快照、候选与原资源保护、历史及自有服务/临时目录清理完成，后续项目明确 | final-summary、services-cleanup、handoff |

机器映射及每项原始记录索引：[final-summary.json](../evidence/beach-bottle-boat-step-5/final-summary.json)。最终采用 27 项通过记录、1 项环境限制，首次未通过与复测分别保存。

## 浏览器、尺寸与真实效果

| 引擎 | 最终采用的实际记录 | 范围 |
|---|---:|---|
| Chromium 155.0.8059.79 | 19 项通过 + 1 项环境限制 | 主流程、沙盒、故障、实例/文档、主站/罗森/庭院、根/子路径、资源、尺寸与触摸 |
| Firefox 153.0 | 4 项通过 | 原页就绪、海浪船体/材质/开关/镜头、原快捷键与下载、右移和 Tab 往返 |
| Linux WebKit 26.5 | 4 项通过 | 同上；不代表真机 Safari |

三个引擎的海浪记录各有 52 个不同渲染帧、约 2.55 个自然 simTime 秒，水面高度、船体 rootY/pitch/roll 有真实变化，GPU 水面时间与原 simTime 一致。没有改 Date、performance、RAF 调度、dt、随机数或原模拟参数接口来制造轨迹。短窗口代表联动不等于同相位轨迹一致性或全部参数组合验证。

原暂停测试中 simTime 与船体保持不变，GL 绘制仍增加，符合原语义。宿主停绘测试中，覆盖期间庭院绘制计数为 **3609 → 3609**，子页为 **1412 → 2087**；关闭后旧 Frame detached，庭院恢复绘制，scrollY 为 **10854 → 10854**，焦点回到现场入口。用户原先暂停时返回仍暂停，原先播放时返回恢复播放，导览保持停止。

| 父视口 | 实际子视口 | DPR |
|---|---|---:|
| 1440×900 | 1440×844 | 1 |
| 1280×720 | 1280×664 | 1 |
| 390×844 | 390×796 | 2 |
| 844×390 | 844×342 | 2 |
| 800×600，主站根字号 200% | 800×465 | 1 |

390 竖屏实际浏览器触摸输入改变原相机，原面板可展开/滚动，末端玻璃滑杆实际生效。连续变尺寸另在同一原文档执行 800×600 → 390×844 → 844×390 → 1280×720，保持同 iframe、timeOrigin 与用户波高，canvas 跟随真实区域变化；关闭后按阅读锚点返回。此处是浏览器视口调整与手机模拟，非物理设备旋转。

截图由原按钮实际下载，保存为 [1440×844 PNG](../evidence/beach-bottle-boat-step-5/chromium-core/embedded-download.png) 与 [1920×1088 PNG](../evidence/beach-bottle-boat-step-5/chromium-core/prefix-download.png)。后者来自子视口 960×544/DPR2。三个引擎都完成真实按钮下载，尺寸按实际子 canvas × min(DPR,2)核对；人工查看了这两张 PNG，均为原 WebGL 场景且不含 DOM 控制台。

画面：[桌面完整现场](../evidence/beach-bottle-boat-step-5/chromium-core/embedded-default.png) · [手机竖屏](../evidence/beach-bottle-boat-step-5/chromium-regression/embedded-390x844.png) · [手机横屏原控制台](../evidence/beach-bottle-boat-step-5/chromium-regression/embedded-844x390.png)。竖屏默认构图会裁去部分瓶身，这是原页面行为；宿主不擅改原相机或裁剪规则。

## 失败记录与采用的复测

6 项首次/途中未通过记录均保留，没有删除或改写，修正的是测试方式，产品实现未随这些复测改动：

- 两次初始化故障注入根据 initScript 时的 pathname 选择子页，但实际初始路径为 `blank`，原场景因此正常启动；不能算作故障通过。最终按 `window !== top` 限定子文档，记录两次 WebGL 创建实际被阻止，原页产生真实初始化错误，放开新文档后由原按钮重试成功。
- 两次图形故障的初始 Document 事件记录没有覆盖最终 canvas，等待事件超时。第二次保留的快照明确显示上下文由 lost 恢复且绘制继续；最终在当前原 canvas 上直接监听，取得 trusted 的 contextlost/contextrestored，宿主在旧 ready=true 下保持 error，新文档重试成功。没有派发假事件或清除原错误文字。
- 一次宿主失败注入按路径区分，意外同时禁用了子文档 WebGL。最终仅对 `window === top` 禁用创建，原宿主真实失败、原瓶中海洋实际 ready。
- Firefox 第一次 Tab 到达子 Document/BODY，下一次才到原按钮，早期测试误要求一步到按钮。复测真实顺序为 Tab→BODY、Tab→#panel-toggle、Shift+Tab→宿主返回按钮；未增加自制焦点陷阱或修改原 DOM。

对应原始目录：`chromium-faults`、`chromium-fault-retest`、`chromium-regression`、`firefox`；最终采用 `chromium-fault-final`、`chromium-input-host-retest`、`firefox-focus-retest`。同目录中其他已通过记录仍按逐项索引采用，不能把整个含失败的首次报告说成全通过。

## 日志、清理和边界

正常路径无 pageerror、console.error 或外部 HTTP 请求尝试。受控初始化失败与宿主图形创建失败日志在 FAULT 场景中保留；待响应时主动关闭/档案/重试产生的三次 `ERR_ABORTED` 属预期取消。软件 WebGL 警告和既有 fullscreen 配置的 allow/allowfullscreen 提示保留原始记录。

浏览器已关闭；3 个本步自有服务按记录的 PID、argv、startTicks 核对后停止。生产目录保存 69 文件摘要并核对后，专用临时目录清理，未停止其他服务。清理记录见 [services-cleanup.json](../evidence/beach-bottle-boat-step-5/services-cleanup.json)。封存保存的是 before/after 独立副本，未来授权修改产品源码不改写本步历史。

实际标签往返保留同一 iframe 与 timeOrigin，但 Xvfb 中没有观测到 document.hidden=true，因此真实隐藏恢复/后台节流仍是环境限制，不计为通过。没有覆写 hidden、派发 visibilitychange 或修改原网页时钟。另未验证真手机、iOS/macOS Safari、Windows、硬件 GPU 性能、显存同步释放、全部 34 控件在内嵌中的逐项一致性或穷举边界。原亮度默认步进、镜头剩余惯性、暂停持续绘制及竖屏构图等 [原有问题](original-issues.md) 保留。

[实际状态约定](step-5-state-contract.md) · [下一步交接](step-5-handoff.md)。独立封存核对命令：`python tests/beach-bottle-boat-step-5/finalize.py --verify-only`，核对历史副本而不要求以后经授权修改的产品源码保持本步版本。
