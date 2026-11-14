"""Write final user-facing records from adopted evidence and fixed archive metadata."""
from common import *
f=read(OUT/'functional-summary.json');d=read(OUT/'delivery-manifest.json');v=read(OUT/'package-validation.json');j=read(OUT/'package-journey/browser.json');dynamic=read(OUT/'dynamic-analysis.json');cleanup=read(OUT/'services-cleanup.json');assert f['complete']and v['complete']and j['complete']and cleanup['scratchRemoved']
candidate=d['candidateId'];prefix='../evidence/beach-bottle-boat-step-7/'
names=['收起/展开面板','隐藏界面','波高','波速','波浪密度','波向','水位','船体响应','船体阻尼','风力','精致画质','标准画质','复古画质','像素强度','夕阳时间','亮度','瓶身透明度','灯塔灯光','浪花效果','沙尘粒子','电影主视角','瓶身侧视角','俯视沙盘','帆船特写','环境全景','放置石头','放置贝壳','撤销放置','恢复装饰','暂停/继续','重置所有参数','恢复默认镜头','保存 PNG','恢复界面']
effects=['真实折叠→展开，面板尺寸及可操作状态记录','真实隐藏 UI，画布继续绘制','0/50/100 与步进；实际波场振幅及连续浮沉','0.2/1.6/3 与步进；实际波场 omega','0.5/1.75/3 与步进；实际波数 k','0/180/360 与步进；方向向量，另补四方向连续样本','0/50/100 与步进；水面 baseLevel 和船体连续跟随','0/50/100 与步进；0/100 连续姿态差异、原响应公式','0/50/100 与步进；0/100 连续轨迹、原阻尼公式','0/50/100 与步进；真实 wind、漂移及自然衰减','实际 scale=2、levels=48 与内部尺寸','实际 scale=2.85、levels=26；原 range=2.9 保留','实际 scale=3.8、levels=12 与内部尺寸','1/3/5 与步进；post.scale 与实际内部像素尺寸','0/50/100 与步进；实际灯色/强度','0.6/1.1/1.6 与步进；实际曝光；默认 0.82/0.8 差异保留','0.04/0.22/0.4 与步进；实际玻璃材质 uniform','实际灯光关闭并恢复','实际浪花对象关闭并恢复','实际沙尘对象关闭并恢复','实际相机位置、目标和 FOV→42；相位不强求相同','实际相机位置、目标和 FOV→39','实际相机位置、目标和 FOV→44','实际相机位置、目标和 FOV→36','实际相机位置、目标和 FOV→47','真实沙地点击形成 rock 对象','真实沙地点击形成 shell 对象','撤销最后的 shell，rock 保留','用户物件清零，原场景保留','simTime/水面/船体冻结；绘制/相机继续；恢复推进','多项改变后恢复原默认参数、画质、机位、编辑、装饰及播放','旋转/平移/缩放后原按钮恢复；保存 80 后续帧实际机位，原惯性保留','桌面及 DPR3 手机实际原按钮 PNG，另有隐藏 UI Enter 导出','真实原恢复按钮显示 UI，继续操作']
parity=f'''# 第七步：完整原功能配对表

第七步已完成。候选 `{candidate}`；日期 2026-11-14（Asia/Shanghai）。在已验证范围内，瓶中海洋的原功能在 Coding 大尺寸现场保留。34 个原 DOM 控件为 12 滑杆和 22 按钮；下表恰好 34 行。68 项配对检查是功能组计数，不冒充 68 个原控件。

## 配对条件和方法

固定原提交 `d94c1f911a39143fd8f5efe152b99a87fdc53184`，原/内嵌 HTML SHA256 均为 `{ENTRY_SHA}`。独立原页由原仓库 HTTP 提供；内嵌为最终生产构建。逐组先后运行，两端使用同引擎版本、实际子视口、DPR、触摸与原前置状态，通过真实鼠标、键盘、触摸和原按钮操作。

| 条件 | 宿主外层 | 两端实际原画布/子视口 | DPR |
|---|---|---|---|
| 桌面 | 1440×900 | 1440×844 | 1 |
| 手机竖屏模拟 | 390×844 | 390×796 | 3 |
| 手机横屏模拟 | 844×390 | 844×342 | 3 |
| 窄屏模拟 | 320×740 | 320×692 | 2 |

实际尺寸来自先测量再配对，见 [pair-conditions.json]({prefix}pair-conditions.json)。观察器只读取诊断，并在调用原 GL 绘制函数时原参委托一次以计数，不改原时钟、RAF、dt、随机数、物理、相机或设置 API。额外的观察 RAF 只采样；数值确定量比较容差 1e-6，不要求自然动画同相位。就绪同时核对当前 API/canvas、真实绘制、loader 和错误。

## 34 控件逐行结果

每行链接分别包含原生输入、前置和实际对象/相机/文件结果，行内效果必须与该控件对应；共享组文件仍按控件分别列行。低中高与一次方向键步进的原始值均保存在滑杆 samples/nativeStep 中。

| 控件 | 功能 | 实际效果与保留差异 | 两端原始记录 | 结论 |
|---|---|---|---|---|
'''
for i,(name,effect)in enumerate(zip(names,effects),1):
 entry=f['controlLedger'][str(i)][0];links=' / '.join('['+label+']('+str(Path('../..')/entry['sides'][side])+')'for side,label in[('reference','原页'),('embedded','内嵌')]);parity+=f'| CTL-{i:02} | {name} | {effect} | {links} | 配对通过'+('；原有差异保留'if i in[12,16,32]else'')+' |\n'
parity+='''
船体响应/阻尼的闭包局部系数不是公开诊断字段：没有伪造 API 读取。固定原源码中的 response、spring、dampingRatio 公式结合真实输入后的连续姿态完成核对。原阻尼滑杆越大，垂直比 0.82→0.26、角比 0.9→0.32，代表样本运动幅度更大；未倒置原滑杆。

## 附加操作

| 记录 | 实际配对结果 |
|---|---|
| CAMERA.pointer-reset | 左旋、右移、滚轮改变原相机/目标/距离；原镜头恢复后的残余惯性单列 |
| POINTER.picking | 真实射线辅助定位后原生双击瓶体/地形聚焦；灯塔单击切灯、双击原事件序列有记录 |
| SANDBOX.props | 石头/贝壳实际放置、撤销、再次放置、恢复；拖动与非编辑点击不新增，Escape 退出 |
| SANDBOX.boundaries | 实际瓶体投影命中瓶后方沙地，外海/天空代表点没有新增；瓶腔拒绝分支未真正命中，不计覆盖 |
| INPUT.keyboard | H、Space、Escape 及输入/按钮焦点原规则；原生 Tab/Shift+Tab 往返；宿主原生 Escape 返回 |
| VIEW.phone/landscape/narrow | 原面板展开/折叠/滚动和透明度输入可用；390 竖屏两端原生模拟单指旋转、双指缩放改变实际相机 |
| VIEW.resize | 同一原 Document、timeOrigin 与用户波高保留，真实横屏→竖屏→桌面变化后两端子视口匹配 |
| PACKAGE.core-flow | 在实际解压成品中启动导览，进入原页停止导览；真实子页滚轮改变原相机，父 displayH/targetH/相机/scrollY 保持，返回阅读不自行续播导览 |

控制与附加操作采用索引见 [functional-summary.json](../evidence/beach-bottle-boat-step-7/functional-summary.json)。原台式快捷键和触摸不跨文档转发；原焦点保护保持。

## 17 个连续动态配对条件

每端都自然运行至少 8 个实际 simTime 秒，同时取得至少 40 个不同 GL 绘制帧。逐帧保存原水面采样、船体位置/rootY/pitch/roll、实际 GPU 波场时间及原安全遥测，不直接写物理状态。

| 条件 | 原页 sim秒/帧 | 内嵌 sim秒/帧 | 结果 |
|---|---|---|---|
'''
for c in dynamic['conditions']:
 a=c['sides']['reference'];b=c['sides']['embedded'];parity+=f"| {c['id']} | {a['simSeconds']:.3f} / {a['distinctRenderedFrames']} | {b['simSeconds']:.3f} / {b['distinctRenderedFrames']} | 配对通过 |\n"
parity+=f'''
最短窗口 {dynamic['minimumSimSeconds']:.3f} sim秒，最少 {dynamic['minimumDistinctRenderedFrames']} 不同绘制帧。零波高振幅/水面高度变化为零；正波高水面及船体自然联动，响应零值的姿态运动显著小于满值。全部样本 GPU 波场时间与原 simTime 一致，有限值检查通过；代表强浪/大风/低高水位中原 containment 标志为真。这只说明采样窗口，不是所有组合不穿模的保证。

[连续原始记录]({prefix}chromium-dynamics/browser.json) · [统计与响应对比]({prefix}dynamic-analysis.json) · [固定源码公式及响应式时序]({prefix}original-physics-responsive-source.json)。

## PNG、画质与浏览器

桌面原按钮在两端实际导出 1440×844 PNG；390×796/DPR3 原画布在两端实际导出 780×1592 PNG，确认 min(DPR,2) 上限。另有隐藏 UI 后保留原截图按钮焦点，用真实 Enter 导出。实际 PNG 均查看，内容为原 WebGL 场景，不含 DOM 控制台和宿主栏。采用 [单独下载复测]({prefix}chromium-export-retest/browser.json)，[人工查看记录]({prefix}visual-review.json)。

内部低分辨率另按 max(240,round(CSS宽/scale)) × max(135,round(CSS高/scale))，renderer DPR 为 1。内部尺寸与 PNG 导出规则分别核对，没有修改原 renderer。

| 引擎/版本 | 本步采用配对组 | 范围 |
|---|---:|---|
| Chromium 155.0.8059.79 | 50 | 全 34 控件、附加操作、17 动态条件、匹配手机/窄屏与导出 |
| Firefox 153.0 | 9 | 新配对启动、波高、三画质、界面、五镜头、沙盒、暂停、键盘、桌面 PNG 及退出 |
| Linux WebKit 26.5 | 9 | 与 Firefox 同一新配对代表范围 |

Firefox/WebKit 不宣称复验全部 34 控件。手机为 Chromium 浏览器模拟；Linux WebKit 不等于 Safari 真机。

## 首次记录、复测和边界

1. 首次 CAMERA.presets 两端都失败：测试在原 reset tween 尚在运行时拖动，首个 cinema 没有可观测位移。复测先原生进入 top，等待实际 FOV，再逐项切换五机位、等待实际相机收敛；未放宽阈值或修改产品。
2. 首次 VIEW.narrow 两端面板初始折叠不同。原 applyResponsive 加 collapsed 后 setUIHidden(false) 又展开，后续真实 resize 会折叠，事件顺序导致入口差异。复测两端原生 321→320 缩放，记录同一 Document，再比对面板和输入；没有派发假 resize 或改样式。原文件保持，冷启动初始折叠不作跨文档固定承诺。
3. 首次桌面/手机 PNG 均实际下载，但测试输出复用了文件名，手机替换了桌面文件。旧记录保留，两项采用独立复测目录中的不同文件名及真实新下载，摘要逐文件核对。

以上首次报告未改成全通过。仍保留原亮度精度、画质取整、镜头惯性、暂停仍绘制和手机取景语义。真实 hidden/后台节流、真机/Windows/Safari/硬件 GPU、创建 RAF 前极快退出、所有放置上限/瓶腔拒绝/所有穿模组合没有新增验证承诺。第六步故障及生命周期证据明确引用为既有结果，不冒充本步新配对。
'''
(DOC/'step-7-parity.md').write_text(parity)
criteria=[('S7-01','97 项 before、固定原版和 13 组封存保护','baseline / candidate-manifest / protection-final'),('S7-02','同引擎/子视口/DPR、原输入与真实就绪','pair-conditions / 每项 conditions'),('S7-03','34 控件逐行配对齐全','parity 34 行 / functional-summary.controlLedger'),('S7-04','12 滑杆低中高、步进与实际效果','chromium-controls / dynamic-analysis / 原公式'),('S7-05','界面三按钮及原 H/Space/Escape','BUTTON.interface / INPUT.keyboard'),('S7-06','三画质及内部像素规则','BUTTON.qualities / SLIDER.pixelScale'),('S7-07','三环境开关实际关闭/恢复','BUTTON.toggle-*'),('S7-08','五机位、恢复、鼠标、拾取','camera-retest / CAMERA.pointer-reset / POINTER.picking'),('S7-09','沙盒实体、撤销/恢复/退出与边界','SANDBOX.props / SANDBOX.boundaries'),('S7-10','暂停/继续与多状态全部重置','PLAYBACK.pause / PLAYBACK.reset-all'),('S7-11','17 条件各端 ≥8 sim秒且 ≥40 绘制帧','chromium-dynamics / dynamic-analysis'),('S7-12','水面/GPU/船体有效联动及代表强组合','dynamic-analysis / visual-review；非穷举'),('S7-13','原输入不误控主站，焦点可交接','INPUT.keyboard / PACKAGE.core-flow'),('S7-14','手机横竖/320 窄屏/真实模拟手势','chromium-views 三项 + narrow-retest'),('S7-15','两匹配尺寸 PNG、DPR>2 与人工查看','chromium-export-retest / EXPORT.hidden / visual-review'),('S7-16','Firefox/WebKit 新配对代表范围','两引擎 controls/actions，共 18 配对组'),('S7-17','主站、罗森、庭院、媒体、水潭与导览','package-journey.core-flow；第六步既有回归'),('S7-18','类型/构建、根/子路径、资源/原 SHA','build-final / package-journey.prefix / 重建'),('S7-19','当前两包、中文空格解压、源码重建与成品运行','delivery-manifest / package-validation / package-journey'),('S7-20','说明、实际映射、历史、封存和自有资源清理','README / run-guide / handoff / cleanup / evidence-manifest')]
verification=f'''# 第七步最终验收

第七步已执行完成。候选 `{candidate}`，日期 2026-11-14（Asia/Shanghai）。已验证范围内完整原功能在个人网站 Coding 区保留，源码与成品两包独立解压、源码重新安装构建及成品运行通过。未提交、推送、部署或发布。

## 实际改动和来源

本步相对第六步 **97 项生产输入全部未变**，无需新增产品修复；更新 README、当前运行指南、对照/交付资料，增加独立验收脚本、证据和仓库外两包。不是回退到 Git HEAD 后重做，也没有重写原 HTML、默认参数、物理或 UI。

主站基提交 `{d['baseCommit']}`；原仓库提交 `d94c1f911a39143fd8f5efe152b99a87fdc53184`，44 文件保持干净；原成品 1,979,264 字节，SHA256 `{ENTRY_SHA}`。原、公有运行副本、生产构建、两包和重建产物摘要一致。Three.js 保持主站 0.187.0 / 瓶中海洋 0.180.0 / 罗森 r160，各自文档运行。

## 执行标准逐项结果

以下“通过”指标准中已定义范围；原问题及未覆盖边界仍保留。

| ID | 结果 | 证据索引 |
|---|---|---|
'''
for id,label,evidence in criteria:verification+=f'| {id} · {label} | 通过 | {evidence} |\n'
verification+=f'''
## 实际测试对象与采用方式

采用 **68 项配对组**：Chromium 50、Firefox 9、Linux WebKit 9；每项均有独立原页和嵌入页结果。Chromium 覆盖全部 34 原控件；17 动态条件共 34 自然运行窗口，最短 {dynamic['minimumSimSeconds']:.3f} sim秒、最少 {dynamic['minimumDistinctRenderedFrames']} 不同绘制帧。测量四组仅用于条件，不充当原功能配对通过数。

首次镜头前置时序、窄屏原响应式时序和 PNG 文件命名问题全部保留，按单项采用复测，不把含失败报告写成整份全通过。实际说明见 [完整配对表](step-7-parity.md)；采用索引与 34 行两端证据见 [functional-summary.json]({prefix}functional-summary.json)。未因此修改原网页或产品代码。

采用配对路径没有 pageerror/console.error、无外部 HTTP 请求尝试。Chromium 保留 allow/allowfullscreen 优先级提示，Firefox 保留软件图形深度纹理过滤与初始布局警告；它们不作为功能失败或零警告承诺。实际请求和事件留在各 browser.json。包内故意请求缺失静态文件返回 404；罗森主动退出时模型请求取消与失败日志按实际记录区分。

## 最终构建和可交付性

实际工具 **Node {v['nodeVersion']}、npm {v['npmVersion']}**；项目要求 Node >=22.12、npm >=10。`npm run build -- --outDir <本步独占目录>` 已包含严格类型检查并成功，生产输出 69 文件。旧 dist 65 文件没有覆盖。97 输入与实际测试构建一一对应。

源码/成品 ZIP 放在独立 `/workspace/deliverables/beach-bottle-boat-step-7/{candidate}/`。两包均实际解压到全新中文/空格目录，并逐文件核对摘要；源码起初无 node_modules/dist，实际 npm ci、类型/生产构建成功，重建的 69 文件与最终候选逐字节相同。没有使用原依赖目录冒充自包含；允许复用 npm 下载缓存。

实际解压成品通过其自带 Node 预览脚本运行，根路径完整经过：关于我/影像、Coding、原控件与 PNG、罗森原镜头、庭院模式/动效/视频、瓶中海洋档案/独立打开、水潭入口、真正运行的导览中断、子页输入隔离及返回阅读。真实 `/portfolio-check/` 子路径另完成原页、输入、PNG、资源摘要/内容类型、MP4 Range 与严格 404；GLB 由现有预览工具以 application/octet-stream 提供并正常载入。

[生产构建]({prefix}build-final.json) · [两包清单]({prefix}delivery-manifest.json) · [独立安装/重建]({prefix}package-validation.json) · [实际成品根/子路径]({prefix}package-journey/browser.json) · [人工图像核对]({prefix}visual-review.json)。Windows 脚本已提供并静态检查，未作 Windows 真机执行声明。

## 历史、清理与限制

13 组既有独立封存逐项核对，原仓库 44 文件、罗森 46 运行文件、封面/声明/来源、旧 dist 和旧归档保留。本步 4 个原服务及 2 个解压包预览服务按 PID/启动时刻/命令身份停止，浏览器已关闭，临时构建/解压/新依赖验证目录清理；两个最终包保留在独立交付目录，没有停止其他服务。

第二步历史仍是“只写标准，未单独执行”，实际约定与第五/六步已实现接口在 [交接映射](step-7-handoff.md) 中说明；没有补造第二步验收。

原亮度/标准画质读数、镜头惯性、暂停仍绘制、阻尼名称语义、窄屏取景与响应式初始事件时序均保留。真实 hidden/后台节流、真手机/Windows/Safari/硬件 GPU、创建 RAF 前极快退出、瓶腔拒绝实际命中、物件上限及所有穿模组合未宣称通过。第六步错误、慢加载、真实图形丢失、反复进入与原播放选择等未变代码证据仍明确引用为历史，不充作本步新配对。

独立核对：`python tests/beach-bottle-boat-step-7/finalize.py --verify-only`。核对范围为封存证据/独立副本及交付文件摘要，后续授权修改产品源码不重写本次历史。
'''
(DOC/'step-7-verification.md').write_text(verification)
handoff=f'''# 第七步交付：瓶中海洋完整接入

本轮七步接入在已验证范围内完成。候选 **{candidate}**，日期 2026-11-14（Asia/Shanghai）。当前 Coding 为 LAWSON → BOTTLE OCEAN → COURTYARD，默认罗森；瓶中海洋现场运行完整原网页，档案/独立打开/返回阅读保留，水潭入口仍是庭院。

本轮未提交、推送、部署或发布；工作区包含此前未提交成果，基提交 `{d['baseCommit']}` 不能单独代表本次成品。产品以本步 candidate-manifest 的 97 输入和 69 产出为准。本步无新增产品修改，README/资料与交付文件已整理。

## 当前可下载文件

两个 ZIP 均在仓库外保留，没有塞入 Git 或冒充已上传。完整解压后使用 HTTP，不能仅双击 index.html。

| 包 | 大小 | 实际验证 |
|---|---:|---|
'''
for kind,label in[('site','成品'),('source','源码')]:
 a=d['artifacts'][kind];handoff+=f"| [{label} ZIP]({a['absolutePath']}) | {a['bytes']:,} 字节（约 {a['bytes']/1048576:.2f} MiB） | "+('自带无 npm 依赖 Node HTTP 预览；根/子路径实际运行'if kind=='site'else'独立 npm ci/类型/构建，69 产出逐字节一致')+' |\n'
handoff+='\n'
for kind in['site','source']:
 a=d['artifacts'][kind];handoff+=f"- `{a['fileName']}`\n  SHA256：`{a['sha256']}`\n"
directory=read(OUT/'delivery-config.json')['deliveryDirectory'];handoff+=f'''
[逐文件清单]({directory}/manifest.json) · [SHA256SUMS]({directory}/SHA256SUMS) · [运行指南](step-7-run-guide.md) · [完整配对表](step-7-parity.md) · [最终验收](step-7-verification.md)。

成品完整解压后，安装 Node.js LTS 24，Windows 可双击 START-PREVIEW.cmd；其他平台运行 `node scripts/preview-site.mjs --open`，无需 npm ci。源码使用 `npm ci`、`npm run dev`；PowerShell 对应 `npm.cmd ci`、`npm.cmd run dev`。源码包保留重建必要文件和指南，不包含完整 Git 历史、所有测试证据或旧大型归档。localhost 仅在自己电脑有效，公开访问仍需后续静态部署。

## 来源与保持

原仓库 [Beach-Bottle-Boat](https://github.com/Banagher-001/Beach-Bottle-Boat)，固定提交 `d94c1f911a39143fd8f5efe152b99a87fdc53184`。原成品 1,979,264 字节，SHA256 `{ENTRY_SHA}`。运行副本 `public/experiments/bottle-ocean/index.html` 与原 HTML 字节相同；SOURCE.md、THIRD_PARTY_NOTICES.md 随源/成品保留。运行不请求 GitHub、私有仓库或外部 CDN。

主站 Three.js 0.187.0、瓶中海洋 0.180.0、罗森 r160 各自保持。原仓库 44 文件、罗森 46 运行文件、既有 13 封存和旧 dist 65 文件保留。当前封面、来源和文件摘要见 [候选清单]({prefix}candidate-manifest.json)。

## 第二步约定与实际接口映射

第二步当时只细化了标准，没有单独执行或架构验收文件；该事实不改写。下面是最终代码的实际映射，主要落地于第五步，第六步修复运行后异常文档替换。不是第二步的补写历史。

| 约定 | 实际所有者和接口 | 已有/本次证据 |
|---|---|---|
| 作品身份/同源完整入口 | projectContent 的 bottle-ocean、embedded-page、resolveProjectEntry/BASE_URL；独立打开共用入口 | 第四步；本步实际包根/子路径 |
| 通用文档生命周期 | createEmbeddedPageExperience(options,profile)；options=container/entry/wanted/status；返回 mount/retry/unmount/dispose | 第五/六步；本步新配对进出 |
| 作品专用只读识别 | createBottleOceanExperience；profile=title/canvasSelector/readyEvent/inspect；当前 API+canvas+首帧+loader+错误组合 | 第六步 ISOLATION.documents / FAULT.*；本步 BASE.inventory |
| 状态表 | viewer 的 prepared，容器的 loading/12秒 slow/ready/error；状态带实例、当前文档归属 | 第六步 FAULT.slow/FAULT.responses/NAV.* |
| 图形丢失与陈旧 ready | 当前 canvas 真实 lost/restored 锁故障，直到新文档/重试；不信旧 ready | 第六步 FAULT.child-graphics；本步代码未变 |
| 防过期/文档替换 | generation/documentGeneration/owns；替换先释放旧监听，运行后 blank 或异常 URL 为 error | 第六步 NAV.child-blank/NAV.paths / LIFE.pending |
| 卸载/重试/最多一个实例 | 先失效代号、清 RAF/timer/AbortController/文档引用，再移除 iframe；重试建立新文档 | 第六步 LIFE.cycles、LIFE.pending；本步关闭均为零 iframe |
| 原输入/下载 | iframe 原控制台/原处理器；无跨文档键盘转发或原业务注入 | 本步 34 控件、INPUT.keyboard/VIEW.phone/EXPORT.* |
| 大尺寸/原取景 | projectHost.css 按独立网页类型复用，iframe 填满工具栏外区域，不固定 16:9/transform | 本步先测子尺寸再配对；实际 PNG |
| 阅读/焦点/播放/导览 | startTourPrototype 的 beginOverlay/closeOverlay、covered/syncLoop；viewer 关闭恢复有效触发点 | 第六步 RESOURCE.return、LAYOUT.resize；本步 PACKAGE.core-flow |
| 罗森/庭院/媒体 | 原各自 profile 与既有资源所有者，退出旧现场才进入新现场 | 本步成品罗森原镜头、庭院模式/视频、水潭、影像 |
| 普通标签/真实 hidden | 原实例保留和回来复核；实际 hidden 没有观察成功，不冒充后台验收 | 第六步 VISIBILITY.return 环境限制保留 |

对应第二步 S2-01～15：正常识别→BASE.inventory/ISOLATION.documents；慢载入→FAULT.slow；失败/重试→FAULT.responses/FAULT.child-init；丢失/恢复→FAULT.child-graphics；关闭/旧回调→LIFE.pending；重复/重载/切作品→LIFE.cycles/NAV.paths；现场档案→LIFE.cycles；庭院/媒体→PACKAGE.core-flow；原输入→本步 INPUT/EXPORT；阅读/播放→RESOURCE.return；尺寸/字体→LAYOUT.sizes/resize；标签→VISIBILITY.return（真实 hidden 限制）；主站故障不禁用独立作品→FAULT.host-init/FAULT.parent-graphics。故障与压力记录明确来自[第六步](step-6-verification.md)，未重称本步新通过。

## 结果、边界与后续保存

本步 68 配对组（Chromium50/Firefox9/WebKit9）、全部34原控件、17连续动态条件通过；真实成品另有根/子路径2条流程，源码从全新目录安装构建与原69产出一致。两包、记录和启动指南已可取走。首次失败和证据命名问题留档，复测采用方式见对照/验收。

原亮度精度、标准画质读数、镜头惯性、阻尼语义、暂停仍绘制、手机取景和面板入口事件时序保留。真实后台 hidden、真手机/Windows/Safari/硬件性能、创建前极快退出、瓶腔拒绝实际命中与全部穿模/物件上限没有验证承诺。

只停止本步自有服务与浏览器，临时构建和中文解压/依赖验证目录清理；交付目录与历史资料保留。新封存只包含证据与独立快照，不冻结未来可授权修改的产品/README 路径。核对命令：`python tests/beach-bottle-boat-step-7/finalize.py --verify-only`。

之后用户如要求保存 GitHub，再将本轮实际源码/必要文档与证据按仓库规范提交，并单列大文件取舍；当前没有自动执行该动作。后续公开部署是另一个明确操作，不把本机预览地址交给他人当公网网址。
'''
(DOC/'step-7-handoff.md').write_text(handoff)
print(json.dumps({'documentsWritten':['step-7-parity.md','step-7-verification.md','step-7-handoff.md'],'candidateId':candidate},ensure_ascii=False))
