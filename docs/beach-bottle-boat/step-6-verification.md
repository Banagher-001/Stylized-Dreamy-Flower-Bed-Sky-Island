# 第六步验收：主站隔离、异常与兼容

第六步已执行完成。修复了一个宿主边界问题：子网页自己导航到可访问的 about:blank 后，查看器会继续显示正在载入。现在区分初始化暂时空白与运行后的文档替换，异常导航转为可恢复错误，并及时解除旧文档/画布监听与引用。原场景 HTML、控制台、模拟、默认参数和画面均未改动。日期：2026-11-14（Asia/Shanghai）。

本轮仅完成第六步，未提交 GitHub、上传、部署或发布；第二步仍仅有标准，第七步完整原页/内嵌对照尚未执行。

## 实际修改及因果验证

相对第五步实际候选，仅修改 src/tour/createEmbeddedPageExperience.ts，其余 96 项既有生产输入不变。未新增产品依赖、业务 UI 或原场景代码。文件、入口、封面和三作品设计保留。

- 首次实际复现与截图保存在 child-navigation-before；观察脚本的日志问题另列，未混为产品问题。
- 使用修正后的观察器再次运行保留的初始构建：child-navigation-clean-before。原文档实际变为空白，父页可以访问新文档，但仍显示 loading；该次没有观察器或页面脚本错误，复现记录保留为未通过。
- 在修复后构建 chromium-core-clean 中，同一操作转为 error，原按钮重试恢复真实原页并可操作。两个构建独立保存并记录切换，不回滚当前产品源码来凑对照。
- 文档身份判定移动到来源验证之前；实际文档替换先清理旧监听。不可访问的新文档也释放旧文档引用。首次真实响应仍计入原 12 秒门槛，不因第一份有效 Document 到达重新计时。

准确差异：[step-6.diff](../evidence/beach-bottle-boat-step-6/step-6.diff)。当前 97 项输入、独立 after 副本及最终构建：[candidate-manifest.json](../evidence/beach-bottle-boat-step-6/candidate-manifest.json)。固定的原 HTML SHA256 为 941feb2ea6ddd3cc93aad5b0b92dbca52ee66a3e1098fee0dbf16f01ca63d1ef。

## 执行范围与结果

最终采用 34 项浏览器通过记录、1 项环境限制，按单项索引采用，不把含首次失败的整份报告说成全通过。

| 引擎 | 采用的通过记录 | 环境限制 | 实际往返轮数 |
|---|---:|---:|---:|
| chromium 155.0.8059.79 | 22 | 1 | 10 |
| firefox 153.0 | 6 | 0 | 3 |
| webkit 26.5 | 6 | 0 | 3 |

Chromium 覆盖主矩阵、网络/导航/图形故障、三作品切换、触摸、尺寸与主站回归；Firefox/Linux WebKit 覆盖正常操作/下载/返回、三轮往返、空白及错误导航、错误重试、小屏代表流程。不是所有引擎全部 34 控件的最终对照。

| 执行标准 | 结果 | 实际记录 |
|---|---|---|
| S6-01 | 通过 | baseline.json, candidate-manifest.json |
| S6-02 | 通过 | ISOLATION.documents, INPUT.native |
| S6-03 | 通过 | INPUT.native |
| S6-04 | 通过 | INPUT.native, LAYOUT.sizes, PREF.reduced |
| S6-05 | 通过 | LIFE.cycles |
| S6-06 | 通过 | LIFE.pending, LIFE.cycles；待创建 RAF 的退出时序未观测；取消路径已审查，真实待响应/迟到回调已测 |
| S6-07 | 通过 | FAULT.slow |
| S6-08 | 通过 | FAULT.responses |
| S6-09 | 通过 | NAV.blank, NAV.child-blank, NAV.paths |
| S6-10 | 通过 | FAULT.child-init, FAULT.child-graphics |
| S6-11 | 通过 | FAULT.host-init, FAULT.parent-graphics |
| S6-12 | 通过 | CAP.native, CAP.denied, INPUT.native, LAYOUT.sizes, visual-review.json |
| S6-13 | 通过 | LAYOUT.sizes, FAULT.slow |
| S6-14 | 通过 | LAYOUT.resize |
| S6-15 | 通过 | RESOURCE.return |
| S6-16 | 通过（条件范围见记录） | VISIBILITY.return；普通标签往返与实例保持通过；真实 hidden 未观测 |
| S6-17 | 通过 | REGRESS.courtyard, REGRESS.reading, LIFE.cycles, CAP.native |
| S6-18 | 通过 | RESOURCE.return |
| S6-19 | 通过 | adoption-plan.json |
| S6-20 | 通过 | build-candidate.json, PATH.prefix, services-cleanup.json, step-6.diff |

机器结果和每项原始记录位置：[final-summary.json](../evidence/beach-bottle-boat-step-6/final-summary.json)。首次失败、采用的复测、观察脚本问题和故障日志均另列。

## 已取得的实际证据

独立文档、Window 和原 canvas 对应正确，原页 Three.js 修订为 180，主站安装版本为 0.187.0；主站没有瓶中海洋全局 API。浏览封面/档案时没有运行 HTML 请求或隐藏 iframe，主站关键字体/颜色/布局在原页操作前后保持一致。

Chromium 完成 10 轮，Firefox/WebKit 各 3 轮；各监测峰值不超过一个独立 iframe，退出为零。档案往返默认波高 35、旧 Frame detached，重复当前现场不新增实例。载入中返回/档案、slow 重试再档案、error 重试后返回、旧响应到达时已经打开罗森或庭院等六种序列均实际检查，并再次进入原页操作。

原左旋、右移、滚轮、面板内部滚动、H/Space/Escape、输入框焦点保护、Tab/Shift+Tab 及原截图实际有效。父页阅读位置与样式未被子页输入推进，原暂停仍绘制的语义保留。宿主 Escape 使用真实工具栏输入交接，关闭后主站原生滚动可继续。

主庭院先证明实际在绘制，作品覆盖期间 GL 调用为 3491 → 3491，子页为 1487 → 2312。关闭后旧 Frame 移除、绘制按用户选择恢复，scrollY 为 10854 → 10854。活动导览由原按钮启动后打开作品即停止，返回不自行续播；原来暂停与播放的选择分别复核。

404、HTTP200 错误内容和实际请求中断均不误就绪；真实请求延迟到 slow 门槛后仍可等待/重试/返回，释放原字节后恢复。错误路径、实际跨源文档、空白与正常同 iframe 新文档均重新判定，旧 ready 不复活。根路径和实际 /portfolio-check/ 内嵌/独立链接可用，缺失静态资源实际 404，不由 SPA HTML 冒充。

父、子 WebGL 创建失败分别控制真实 getContext；真实 WEBGL_lose_context 在原 canvas 上取得 trusted 丢失/恢复事件。子页恢复事件不解除旧故障，原 ready=true 时仍要求新文档重试；恢复后切罗森/庭院正常。主站实际丢失时子页仍能操作，恢复后庭院重新绘制。未派发假事件或改原错误字段。

罗森原全屏实际绘制计数 [13525, 15715]，原行走模式取得并释放指针锁，真实 X11 Escape 后查看器保持可用。真实 Permissions-Policy fullscreen=() 拒绝时，能力提示准确、原场景仍就绪，可返回并运行瓶中海洋。该原按钮拒绝产生的原脚本日志按故障场景保留。

关于我、AI影像原图媒体、Coding 选择/键盘/档案、庭院正常/像素/动效/视频和水潭入口均回归。真实减少动态偏好下主站保持暂停，原页按其原语义继续；用户手动选择播放后返回也保留选择。

## 尺寸、像素与真实 PNG

覆盖 1440×900、1280×720、390×844、844×390、320×740，以及 800×600/根字号 200%。原面板展开、滚动与玻璃滑杆可用，320 错误状态和真实 slow 状态的工具栏均可达。390 手机模拟实际单指旋转、双指缩放改变原相机，主站无误滚动。

同一已运行文档连续改变尺寸，保留 iframe、Document 和用户波高，返回按原语义锚点和有效焦点恢复。原页按像素档位降低内部渲染分辨率；retro 的 scale=3.8，内部尺寸取 max(240, round(cssWidth/scale)) × max(135, round(cssHeight/scale))。本次 390×796 的原 canvas 内部分辨率为 240×209，属于原设计，不能按导出 PNG 的 DPR 规则判错或改原 renderer。

原截图另按 canvas CSS 尺寸 × min(DPR,2)复制场景。实际原按钮下载：桌面 1440×844，手机 780×1592，均保存并人工查看，场景内容与当前取景一致，不含 DOM 控制台。Firefox、WebKit 另各取得原按钮 PNG。

[桌面原按钮 PNG](../evidence/beach-bottle-boat-step-6/chromium-core-clean/native-input-download.png) · [手机原按钮 PNG](../evidence/beach-bottle-boat-step-6/chromium-layout/phone-native-download.png) · [320 窄屏错误反馈](../evidence/beach-bottle-boat-step-6/chromium-layout/layout-320-error.png)。手机截图是原竖屏/用户操作后的取景，保留原来部分瓶身可能出画的行为。

## 首次失败、测试修正与边界

所有首次失败均保留，分别采用复测，没有清空日志或改写旧报告。除上述一个宿主问题外，测试修正包含：重复现场选择器需限定 button；两段观察 IIFE 拼接需分号；原内部像素分辨率与导出 PNG 规则必须分开；Firefox 子框架重载应从稳定父页确认当前 Document/API，不能一直等旧子执行环境；Firefox 会恢复原控件焦点，Tab 需按实际序列检查，宿主 Escape 用原生工具栏交接。未因此修改原 HTML 或增加产品键盘转发。

正常采用路径没有未解释的 pageerror/console.error 或外部 HTTP 请求尝试。受控 404、WebGL 故障及原全屏权限拒绝日志单列；主动关闭/切换造成的请求取消与软件 WebGL 警告保留并区分。具体清单见机器汇总与原始 browser.json。

普通真实标签往返保持同一实例、timeOrigin 和已改参数；Xvfb 未观测到真实 hidden，隐藏恢复与后台节流不算通过。极快退出发生在创建 RAF 之前的时序没有实际观测，取消路径已审查；网络待响应退出已实测，二者不混同。未验证真手机、iOS/macOS Safari、Windows 或硬件 GPU 性能，不声称 GPU 内存同步归零。

原仓库 44 文件、罗森 46 运行文件、成品/声明/来源、真实封面和此前 12 组封存完整。原 dist 的 65 文件未覆盖。初始与修复后各一次生产构建均包含类型检查，两个独立 69 文件构建清单保存并在清理前核对；4 个本步自有服务与浏览器按身份退出，专用临时目录清理，没有停止其他服务。

[兼容性范围](step-6-compatibility.md) · [第七步交接](step-6-handoff.md)。封存独立核对：python tests/beach-bottle-boat-step-6/finalize.py --verify-only。封存对象为证据、文档、脚本和独立 before/after，当前产品源码只作为候选记录，后续授权修改无需改写本步历史。
