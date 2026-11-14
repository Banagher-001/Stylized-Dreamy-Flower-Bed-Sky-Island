"""Write reviewed human reports from the adopted, actually executed records."""
from common import *
s=read(OUT/'final-summary.json');adopted=s['adoptedChecks'];passed=sum(a['status']=='通过'for a in adopted);limits=sum(a['status']=='环境限制'for a in adopted)
def evidence(engine,id):
 a=next(a for a in adopted if a['engine']==engine and a['id']==id)
 return next(c['evidence']for c in read(OUT/a['run']/'browser.json')['checks']if c['id']==id)
resource=evidence('chromium','RESOURCE.return');cap=evidence('chromium','CAP.native');sizes=evidence('chromium','LAYOUT.sizes');resize=evidence('chromium','LAYOUT.resize');namespace=evidence('chromium','ISOLATION.documents');desktop=evidence('chromium','INPUT.native')['download'];phone=next(r['download']for r in sizes['sizes']if r.get('download'));rounds={e:len(evidence(e,'LIFE.cycles')['rounds'])for e in['chromium','firefox','webkit']}
rows=[]
for engine in['chromium','firefox','webkit']:
 a=[a for a in adopted if a['engine']==engine];rows.append(f'| {engine} {a[0]["version"]} | {sum(x["status"]=="通过"for x in a)} | {sum(x["status"]=="环境限制"for x in a)} | {rounds[engine]} |')
checks=[]
for c in s['standardChecks']:
 detail='普通标签往返与实例保持通过；真实 hidden 未观测'if c['id']=='S6-16'else'待创建 RAF 的退出时序未观测；取消路径已审查，真实待响应/迟到回调已测'if c['id']=='S6-06'else''
 checks.append(f'| {c["id"]} | {c["status"]} | '+', '.join(c['records'])+('；'+detail if detail else'')+' |')
verification=f'''# 第六步验收：主站隔离、异常与兼容

第六步已执行完成。修复了一个宿主边界问题：子网页自己导航到可访问的 about:blank 后，查看器会继续显示正在载入。现在区分初始化暂时空白与运行后的文档替换，异常导航转为可恢复错误，并及时解除旧文档/画布监听与引用。原场景 HTML、控制台、模拟、默认参数和画面均未改动。日期：2026-11-14（Asia/Shanghai）。

本轮仅完成第六步，未提交 GitHub、上传、部署或发布；第二步仍仅有标准，第七步完整原页/内嵌对照尚未执行。

## 实际修改及因果验证

相对第五步实际候选，仅修改 src/tour/createEmbeddedPageExperience.ts，其余 96 项既有生产输入不变。未新增产品依赖、业务 UI 或原场景代码。文件、入口、封面和三作品设计保留。

- 首次实际复现与截图保存在 child-navigation-before；观察脚本的日志问题另列，未混为产品问题。
- 使用修正后的观察器再次运行保留的初始构建：child-navigation-clean-before。原文档实际变为空白，父页可以访问新文档，但仍显示 loading；该次没有观察器或页面脚本错误，复现记录保留为未通过。
- 在修复后构建 chromium-core-clean 中，同一操作转为 error，原按钮重试恢复真实原页并可操作。两个构建独立保存并记录切换，不回滚当前产品源码来凑对照。
- 文档身份判定移动到来源验证之前；实际文档替换先清理旧监听。不可访问的新文档也释放旧文档引用。首次真实响应仍计入原 12 秒门槛，不因第一份有效 Document 到达重新计时。

准确差异：[step-6.diff](../evidence/beach-bottle-boat-step-6/step-6.diff)。当前 97 项输入、独立 after 副本及最终构建：[candidate-manifest.json](../evidence/beach-bottle-boat-step-6/candidate-manifest.json)。固定的原 HTML SHA256 为 {ENTRY_SHA}。

## 执行范围与结果

最终采用 {passed} 项浏览器通过记录、{limits} 项环境限制，按单项索引采用，不把含首次失败的整份报告说成全通过。

| 引擎 | 采用的通过记录 | 环境限制 | 实际往返轮数 |
|---|---:|---:|---:|
{chr(10).join(rows)}

Chromium 覆盖主矩阵、网络/导航/图形故障、三作品切换、触摸、尺寸与主站回归；Firefox/Linux WebKit 覆盖正常操作/下载/返回、三轮往返、空白及错误导航、错误重试、小屏代表流程。不是所有引擎全部 34 控件的最终对照。

| 执行标准 | 结果 | 实际记录 |
|---|---|---|
{chr(10).join(checks)}

机器结果和每项原始记录位置：[final-summary.json](../evidence/beach-bottle-boat-step-6/final-summary.json)。首次失败、采用的复测、观察脚本问题和故障日志均另列。

## 已取得的实际证据

独立文档、Window 和原 canvas 对应正确，原页 Three.js 修订为 {namespace['documentBoundaries']['childRevision']}，主站安装版本为 {namespace['installedHostThreeVersion']}；主站没有瓶中海洋全局 API。浏览封面/档案时没有运行 HTML 请求或隐藏 iframe，主站关键字体/颜色/布局在原页操作前后保持一致。

Chromium 完成 {rounds['chromium']} 轮，Firefox/WebKit 各 {rounds['firefox']} 轮；各监测峰值不超过一个独立 iframe，退出为零。档案往返默认波高 35、旧 Frame detached，重复当前现场不新增实例。载入中返回/档案、slow 重试再档案、error 重试后返回、旧响应到达时已经打开罗森或庭院等六种序列均实际检查，并再次进入原页操作。

原左旋、右移、滚轮、面板内部滚动、H/Space/Escape、输入框焦点保护、Tab/Shift+Tab 及原截图实际有效。父页阅读位置与样式未被子页输入推进，原暂停仍绘制的语义保留。宿主 Escape 使用真实工具栏输入交接，关闭后主站原生滚动可继续。

主庭院先证明实际在绘制，作品覆盖期间 GL 调用为 {resource['coveredDraws']['parent'][0]} → {resource['coveredDraws']['parent'][1]}，子页为 {resource['coveredDraws']['child'][0]} → {resource['coveredDraws']['child'][1]}。关闭后旧 Frame 移除、绘制按用户选择恢复，scrollY 为 {resource['anchor']['scrollY']} → {resource['playingAfterReturn']['scrollY']}。活动导览由原按钮启动后打开作品即停止，返回不自行续播；原来暂停与播放的选择分别复核。

404、HTTP200 错误内容和实际请求中断均不误就绪；真实请求延迟到 slow 门槛后仍可等待/重试/返回，释放原字节后恢复。错误路径、实际跨源文档、空白与正常同 iframe 新文档均重新判定，旧 ready 不复活。根路径和实际 /portfolio-check/ 内嵌/独立链接可用，缺失静态资源实际 404，不由 SPA HTML 冒充。

父、子 WebGL 创建失败分别控制真实 getContext；真实 WEBGL_lose_context 在原 canvas 上取得 trusted 丢失/恢复事件。子页恢复事件不解除旧故障，原 ready=true 时仍要求新文档重试；恢复后切罗森/庭院正常。主站实际丢失时子页仍能操作，恢复后庭院重新绘制。未派发假事件或改原错误字段。

罗森原全屏实际绘制计数 {cap.get('fullscreenDraws')}，原行走模式取得并释放指针锁，真实 X11 Escape 后查看器保持可用。真实 Permissions-Policy fullscreen=() 拒绝时，能力提示准确、原场景仍就绪，可返回并运行瓶中海洋。该原按钮拒绝产生的原脚本日志按故障场景保留。

关于我、AI影像原图媒体、Coding 选择/键盘/档案、庭院正常/像素/动效/视频和水潭入口均回归。真实减少动态偏好下主站保持暂停，原页按其原语义继续；用户手动选择播放后返回也保留选择。

## 尺寸、像素与真实 PNG

覆盖 1440×900、1280×720、390×844、844×390、320×740，以及 800×600/根字号 200%。原面板展开、滚动与玻璃滑杆可用，320 错误状态和真实 slow 状态的工具栏均可达。390 手机模拟实际单指旋转、双指缩放改变原相机，主站无误滚动。

同一已运行文档连续改变尺寸，保留 iframe、Document 和用户波高，返回按原语义锚点和有效焦点恢复。原页按像素档位降低内部渲染分辨率；retro 的 scale=3.8，内部尺寸取 max(240, round(cssWidth/scale)) × max(135, round(cssHeight/scale))。本次 390×796 的原 canvas 内部分辨率为 240×209，属于原设计，不能按导出 PNG 的 DPR 规则判错或改原 renderer。

原截图另按 canvas CSS 尺寸 × min(DPR,2)复制场景。实际原按钮下载：桌面 {desktop['PNG'][0]}×{desktop['PNG'][1]}，手机 {phone['PNG'][0]}×{phone['PNG'][1]}，均保存并人工查看，场景内容与当前取景一致，不含 DOM 控制台。Firefox、WebKit 另各取得原按钮 PNG。

[桌面原按钮 PNG](../evidence/beach-bottle-boat-step-6/chromium-core-clean/native-input-download.png) · [手机原按钮 PNG](../evidence/beach-bottle-boat-step-6/chromium-layout/phone-native-download.png) · [320 窄屏错误反馈](../evidence/beach-bottle-boat-step-6/chromium-layout/layout-320-error.png)。手机截图是原竖屏/用户操作后的取景，保留原来部分瓶身可能出画的行为。

## 首次失败、测试修正与边界

所有首次失败均保留，分别采用复测，没有清空日志或改写旧报告。除上述一个宿主问题外，测试修正包含：重复现场选择器需限定 button；两段观察 IIFE 拼接需分号；原内部像素分辨率与导出 PNG 规则必须分开；Firefox 子框架重载应从稳定父页确认当前 Document/API，不能一直等旧子执行环境；Firefox 会恢复原控件焦点，Tab 需按实际序列检查，宿主 Escape 用原生工具栏交接。未因此修改原 HTML 或增加产品键盘转发。

正常采用路径没有未解释的 pageerror/console.error 或外部 HTTP 请求尝试。受控 404、WebGL 故障及原全屏权限拒绝日志单列；主动关闭/切换造成的请求取消与软件 WebGL 警告保留并区分。具体清单见机器汇总与原始 browser.json。

普通真实标签往返保持同一实例、timeOrigin 和已改参数；Xvfb 未观测到真实 hidden，隐藏恢复与后台节流不算通过。极快退出发生在创建 RAF 之前的时序没有实际观测，取消路径已审查；网络待响应退出已实测，二者不混同。未验证真手机、iOS/macOS Safari、Windows 或硬件 GPU 性能，不声称 GPU 内存同步归零。

原仓库 44 文件、罗森 46 运行文件、成品/声明/来源、真实封面和此前 12 组封存完整。原 dist 的 65 文件未覆盖。初始与修复后各一次生产构建均包含类型检查，两个独立 69 文件构建清单保存并在清理前核对；4 个本步自有服务与浏览器按身份退出，专用临时目录清理，没有停止其他服务。

[兼容性范围](step-6-compatibility.md) · [第七步交接](step-6-handoff.md)。封存独立核对：python tests/beach-bottle-boat-step-6/finalize.py --verify-only。封存对象为证据、文档、脚本和独立 before/after，当前产品源码只作为候选记录，后续授权修改无需改写本步历史。
'''
(DOC/'step-6-verification.md').write_text(verification)
compat='''# 第六步兼容性与条件边界

日期：2026-11-14（Asia/Shanghai）。结论只覆盖本轮实际环境和最终采用的记录，详见 step-6-verification.md 与 final-summary.json。

| 环境/能力 | 本轮实际结论 |
|---|---|
| Linux Chromium 155 | 主矩阵通过：输入/焦点/下载、10 轮往返、网络/文档/图形故障、布局/触摸、主站与作品回归 |
| Firefox 153 | 6 项代表记录通过：同源空白及错误/跨源导航、新文档、3 轮、原操作与 PNG、错误重试、390 窄屏 |
| Linux WebKit 26.5 | 同 Firefox 的 6 项代表范围；不是 Safari 真机验证 |
| 桌面尺寸 | 1440×900、1280×720；同一原文档实际变化，参数保持 |
| 手机模拟 | 390×844、844×390、320×740；Chromium DPR2、真实触摸点按/单指/双指输入，非物理设备 |
| 文字放大 | html 根字号 200%，800×600；非 OS/浏览器缩放测试 |
| 原 PNG 下载 | 三引擎均真实原按钮下载；Chromium 两组不同尺寸/DPR，查看了实际 PNG |
| 罗森全屏/指针锁 | Chromium 原生用户操作取得、真实 X11 Escape 退出，返回无遗留；权限策略拒绝时准确降级 |
| 普通标签往返 | 同一 iframe、timeOrigin、已改参数保持，返回不重建或强制播放 |
| 真实 hidden | Xvfb 未观测；真实后台恢复/节流未验证，没有伪造 visibilitychange |
| 创建 RAF 前极快退出 | 实际时序未观测，取消路径有源码审查；待网络响应时退出已有运行证据 |
| 软件图形环境 | 本轮 LIBGL_ALWAYS_SOFTWARE，记录实际效果与资源归属；不作硬件 FPS 或显存归零承诺 |
| Windows、真手机、Safari、硬件 GPU | 无对应实测环境，保留未验证条件 |
| 全部 34 控件逐项原页/内嵌对照 | 属第七步；本轮代表操作不替代该最终对照 |

Firefox 重载的当前 Document 身份与新 API 从稳定的父文档读取，再以真实坐标/键盘操作新原控件，避免等待已经更替的子执行环境。键盘进出采用浏览器实际顺序，允许 BODY 和原控件上次位置，宿主 Escape 使用原生工具栏点击交接。不同浏览器不以相同固定 Tab 次数验收。

原内部像素缓冲按 quality/scale 和最小尺寸更新，PNG 则按 CSS 尺寸×min(DPR,2)导出，二者分别核对。原亮度步进、standard 精度、镜头残余惯性、暂停仍绘制、上下文丢失旧 ready 和手机取景等既有语义不变，参见 original-issues.md。

全屏策略拒绝触发原按钮原脚本错误、故障注入日志、主动卸载请求取消及软件渲染警告均保留，不能把这些描述成正常路径无条件全平台兼容，也不能删掉原始记录来取得全绿。
'''
(DOC/'step-6-compatibility.md').write_text(compat)
handoff='''# 第六步交接：第七步完整原页/内嵌对照

第六步完成隔离、异常、生命周期与兼容代表验收，修复一个共用容器的文档边界问题。未提交 GitHub、上传或发布；第七步尚未执行，第二步仍只有标准。日期：2026-11-14（Asia/Shanghai）。

## 接续起点

当前候选位于 docs/evidence/beach-bottle-boat-step-6/candidate-manifest.json，共 97 项生产输入；唯一相对第五步的产品修改为 src/tour/createEmbeddedPageExperience.ts。创建阶段暂时 about:blank 允许等待；运行后文档变为空白或异常路径时，先清理旧文档监听，再按当前来源/原信号判定；跨源不可访问也释放旧引用。API、状态类型及两个作品工厂调用方式不变。

Coding 顺序与默认仍为 LAWSON → BOTTLE OCEAN → COURTYARD、默认罗森。瓶中海洋由 resolveProjectEntry('bottle-ocean') 解析 experiments/bottle-ocean/index.html；主站 iframe 与独立打开共用入口，根/真实子路径已复核。原 HTML、封面、声明和罗森运行文件均保持原样。

第五步和更早记录封存未修改；本步新增后合计 13 组历史。下一步固定当前工作区为 before，保留现有未提交成果，不能回 git HEAD 重放修改。核对独立封存副本，不把过去对可变产品源码的总冻结断言当成后续修改的阻挡。

## 第七步执行前应细化

1. 以 feature-matrix.md 的 12 滑杆、22 按钮及其他操作逐项建立独立原页/内嵌对照表。为每项定义同引擎、相同子文档尺寸/DPR与原前置状态，实际点击/拖动/键盘后看对象、相机、连续轨迹或导出文件，不能只数控件。
2. 补齐全部参数、全部画质/镜头、完整重置、拾取、沙盒边界等，明确本步已有代表证据与第七步需要的新对照。原时钟、相位、随机性与惯性保留，不直接写内部状态或要求不同运行逐帧坐标相等。
3. PNG 来自原按钮，按实际 CSS 尺寸×min(DPR,2)，不含 DOM 控制台；原内部像素缓冲按 scale/最小尺寸，不能与导出 PNG 规则混用。本步有桌面 1440×844 与手机 780×1592 的真实文件。
4. 承接兼容性限制：真实 hidden、创建 RAF 前极快退出的实际时序、真手机/Safari/Windows/硬件性能未覆盖；可取得真实条件时补，不伪造事件、属性或设备。环境不足时准确列边界。
5. 原问题单继续使用 original-issues.md。未经另行原场景修改，不修亮度步进、镜头惯性、原暂停绘制和竖屏取景来凑一致。原字节如需改变必须形成单独来源与验证，不能归为本次原样接入。
6. 当前工作区做必要最终类型/构建、入口/路径/原资源与主站/罗森/庭院回归，整理运行说明、源码、成品、已知问题和完整验收。第七步完成后才判断整套接入交付，不能把本步代表结果直接改称所有原功能已对照。

## 可靠的验证方法与记录

使用当前实际 Document/canvas 绑定监听和记录 trusted 图形事件；initScript 以 window/top 身份选择父/子，不以初始 blank 路径判断。Firefox 子框架重载时从稳定父文档确认当前 Document/API，原输入使用真实浏览器动作；Tab 按原序列，不能固定一步到某控件或用 DOM focus 假定原生键盘已切换页面。

本步保留全部首次失败及复测，观察器拼接/选择器、像素判据、Firefox 等待与原生焦点方式修正均在新目录完成。最终只按明确单项采用证据，含失败的首次整报告没有改成全通过。

浏览器和 4 个本步自有服务已退出，初始/修复后构建的清单保存并核对后，专用临时目录清理；原 dist 未覆盖。后续需要运行时启动新自有服务，不使用已清理的临时地址作长期预览。

独立封存核对命令：python tests/beach-bottle-boat-step-6/finalize.py --verify-only。当前产品路径记录在候选清单；封存目标是文档、脚本、原始证据及独立 before/after，允许后续授权修改产品源码而不改写第六步历史。
'''
(DOC/'step-6-handoff.md').write_text(handoff)
p=DOC/'step-6-standard.md';text=p.read_text();a=text.index('状态：');z=text.index('\n',a);p.write_text(text[:a]+'状态：第六步已执行完成。隔离、生命周期、异常、原生输入与三引擎代表范围已验收；修复共用容器的空白/异常文档识别与旧监听清理。真实 hidden、真机及未观测的创建前时序保留限制。结果见 step-6-verification.md；执行前标准另存 standard-before.md。日期：2026-11-14（Asia/Shanghai）。未提交、上传或发布，第七步尚未执行。'+text[z:])
print(json.dumps({'reportsWritten':3,'adoptedPassed':passed,'limits':limits,'standardStatusUpdated':True},ensure_ascii=False))
