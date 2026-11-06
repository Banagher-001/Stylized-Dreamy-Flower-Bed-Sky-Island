## 第十二步独立交付检查

当前默认首页为庭院；`?tour=reference`为旧参考稿。当前交付检查入口为`step12_release_check.py`（独立HTTP根/子目录、入口及逐资源SHA/MIME）、`step12_regression.py`（复用附带Step11合同，从新默认地址重跑）、`step12_scene.py`（独立Step11基线完整画布对照）。命令、依赖、原生输入工具与历史夹具前提见[交付说明](../../docs/scroll-garden/delivery.md)。新输出必须指定独立目录，旧报告保持。

源码包包含这些检查所需代码；全部历史套件仍供追溯，部分需要完整工作区历史大图及当时的服务布局，不能宣称仅解压当前源码可全量重跑。以下内容为各阶段的历史运行说明。

# 滚动庭院当前复验：第十一步

当前应用依赖保持不变，使用既有Python/Playwright/Pillow/websockets与缓存浏览器。当前开发5173、生产4173；对照为第十步。验收产物独立写入 `docs/evidence/scroll-garden-step-11/`，旧脚本与证据保留。

```bash
export DISPLAY=:100
export LIBGL_ALWAYS_SOFTWARE=1
export LD_LIBRARY_PATH=/workspace/.cache/browser-deps/root/usr/lib/x86_64-linux-gnu
export PLAYWRIGHT_BROWSERS_PATH=/workspace/.cache/ms-playwright
export COURTYARD_WEBKIT_EXECUTABLE=/workspace/.cache/browser-deps/run-webkit.sh
npm run build
python3 tests/scroll-garden/step11_checks.py --group browser
python3 tests/scroll-garden/step11_checks.py --group legacy
python3 tests/scroll-garden/step11_checks.py --group final
python3 tests/scroll-garden/step11_baseline.py --phase before --url http://127.0.0.1:4174 --latency-only
python3 tests/scroll-garden/step11_baseline.py --phase after --url http://127.0.0.1:4173
python3 tests/scroll-garden/step11_record.py
python3 tests/scroll-garden/step11_finalize.py
```

本云环境显示服务使用本步独立的 `:100`，原服务停用后为继续验收恢复了5173/4173。跨引擎依赖仍为 `LD_LIBRARY_PATH=/workspace/.cache/browser-deps/root/usr/lib/x86_64-linux-gnu`、`PLAYWRIGHT_BROWSERS_PATH=/workspace/.cache/ms-playwright`、`COURTYARD_WEBKIT_EXECUTABLE=/workspace/.cache/browser-deps/run-webkit.sh`，配合 `LIBGL_ALWAYS_SOFTWARE=1`。重跑时先准备自己的Xvfb与预览进程，结束后只清理自己启动的测试服务。

恢复对照时，将 `docs/evidence/scroll-garden-step-11/baseline-step10.tar.gz` 解压到 `/tmp/scroll-garden-step-11-before/`，把同目录 `baseline-files.json` 复制为 `/tmp/scroll-garden-step-11-before-manifest.json`。4174直接服务快照的dist目录；不要用当前构建覆盖before。首次重建证据应先运行完整before基线；已有截图时可只重新采集独立性能样本。性能前后各五路线、每路六次原生wheel，总30次；测量时不运行其他浏览器、录屏或截图。

browser包含十次方式往返、十次方向往返、原生输入、十站完整内容、临时长文、200%文字、减少动态、焦点、稳定版回看、查看层返回与十次媒体资源循环。dialogs保留固定手机仿真三种困难布局及无WebGL完整阅读；renderer检查DPR1/2/3、相同尺寸不重复分配、暂停/离屏零绘制。overlay-resize专测查看器打开期间旋转后的原位返回。media-faults通过实际网络中断验证图片、封面、视频失败与重试，不伪造媒体成功事件。

legacy复用原三柱全部关键断言，旧减少动态运镜合同改为普通触摸视口，新的稳定阅读由专项检查。图形恢复后须先确认十站稳定可读，再显式点击沉浸恢复，继续原相机/文字/画面断言。旧文件不改写，结果记入本步regression目录。

native-zoom使用Linux实际浏览器窗口及X11快捷键：Chromium页面200%，Firefox持久原生窗口仅文字200%。native-recovery使用真实Target激活/隐藏及WebGL丢失扩展，不修改document.hidden或派发假的visibility事件。scope对完整画布零容差比较108组，不使用遮罩；geometry使用精确画布宽高与真实基线。

GTK WebKit固定手机仿真的动态旋转会出现屏幕覆盖与CSS视口更新不同步；旋转回归采用支持触摸的实际CSS布局视口并断言100vw与innerWidth一致，另用is_mobile固定尺寸测试手机查看器。其手机模式明确不支持wheel接口，专项使用原生PageDown核对背景锁，普通布局的wheel由三柱回归保留。Chromium另有真实双触点分离手势；synthesizePinchGesture在本环境无缩放效果，未将它冒充通过。

CSS rem放大、原生页面缩放、Firefox原生仅文字缩放分别记录。模拟触摸、Linux原生浏览器、GTK WebKit均不等于真实iOS/Android；实际系统大字、浏览器栏/刘海、读屏、物理触控板/APZ和硬件FPS继续单列待核。

---

# 第十步历史复验

当前采用原有Python/Playwright/Pillow/websockets与缓存浏览器，应用依赖不变。开发5173、生产预览4173；隔离第九步源码/构建位于 `/tmp/scroll-garden-step-10-before`，在该目录启动4174作对照。可用 `docs/evidence/scroll-garden-step-10/baseline-step9-source.tar.gz` 重建基线，不能用当前源码覆盖before。

```bash
npm run build
python3 tests/scroll-garden/step10_geometry.py
python3 tests/scroll-garden/step10_browser.py --engine chromium
python3 tests/scroll-garden/step10_regression.py --suite chapter --engine chromium
python3 tests/scroll-garden/step10_regression.py --suite about --engine chromium
python3 tests/scroll-garden/step10_regression.py --suite films --engine chromium
python3 tests/scroll-garden/step10_recovery.py
python3 tests/scroll-garden/step10_fallback.py
python3 tests/scroll-garden/step10_scope.py
```

browser和三个regression分别运行firefox/webkit，普通访客界面完整检查，debug=1另在新流程专项检查。沿用DISPLAY=:99、LD_LIBRARY_PATH=/workspace/.cache/browser-deps/root/usr/lib/x86_64-linux-gnu、PLAYWRIGHT_BROWSERS_PATH=/workspace/.cache/ms-playwright、COURTYARD_WEBKIT_EXECUTABLE=/workspace/.cache/browser-deps/run-webkit.sh。Chromium使用ANGLE/SwiftShader，GTK WebKit与模拟手机不作为Apple Safari或真机证明。

geometry检查五条移动曲线每尺寸5005样本、全部段/下降/水潭连接的一阶连续性、保守实体安全余量、30个阅读视线、101个W稳定样本和78组真实基线固定姿态。重建相机使用精确画布宽高，不用舍入诊断aspect。

browser验证真实按钮点击后只等待到站，不用辅助scrollTo掩盖导航失效；包含可逆开/结幕、同一阅读区的实际文字节点与用户选择保留、五入口/连点/键盘/触摸、W原生滚轮稳定、结尾回看、10轮DOM/GPU、模式/时间继承、真实背景对比度及正常/调试界面。反向复现保存实际scrollY，七位小数H仅作诊断；独立的step10_scroll_precision.py保留WebKit一像素重建差异。

regression复用旧三柱完整断言，适配标题/模式标签、当前资源预算和独立证据目录；隐藏调试站点在正常浏览中改为原生定位，真实debug按钮由专项测试。键盘焦点单独断言后，模式比较先用一次中性场景点击统一输入焦点，保留可见焦点样式与零像素容差。C暂停观察沿用有界布局稳定再检查零新增绘制，初版诊断和旧证据均保留。

scope保护3118份原文件，只允许三份原型源文件与新增presentation.ts及当前文档。96组完整纯canvas对照覆盖13固定姿态与3未改时序转场，保留3D符印，无蒙版、零容差。只有W的同相机隔离样本临时把测试scrollRange对齐123CSSpx整数倍以精确表示11.5H，拍后立即还原；其他样本和所有正常输入/性能测试使用原始范围。真实W落点因新增hold产生的微量差异另存diagnostics，不混作材质变化。`--scope-only`只检查文件。

```bash
python3 tests/scroll-garden/step10_record.py
python3 tests/scroll-garden/step10_baseline.py --phase after --url http://127.0.0.1:4173
python3 tests/scroll-garden/step10_finalize.py
```

录制和性能各自独立运行，不并行其他浏览器。录像通过实际有界wheel遍历完整正向像素/反向正常路线、播放暂停、结尾回看、现场体验及明确标版本的早期视频档案，保留原墙钟时间。帧间隔探针只包装已有RAF，无额外循环，不作硬件FPS证明。

性能新测第九步与最终第十步：同样完整预热，T01/T12/T23/T3W/WIDE各6次真实wheel，共前后各30；采样不截图，随后三尺寸双模式各18姿态共108图及参考稿。所有原始值与失败诊断保留。finalize核对实际通过计数、完整录像、当前TS/CSS摘要、原文件/画布保护和前后资源/性能；不能在缺证据时填通过。

以下保留第九步及更早历史复验说明，仅用于匹配版本。

---

# 滚动庭院历史复验：第九步

使用原有Python/Playwright/Pillow/websockets、浏览器及缓存依赖，应用依赖不变。开发5173、生产预览4173；第八步源码/构建基线位于 `/tmp/scroll-garden-step-9-before`，其独立dist预览4174用于配对。可从 `docs/evidence/scroll-garden-step-9/baseline-step8-source.tar.gz` 重建基线；不能用当前源码覆盖before证据。

```bash
npm run build
python3 tests/scroll-garden/step9_geometry.py
python3 tests/scroll-garden/step9_highlights.py
python3 tests/scroll-garden/step9_browser.py --engine chromium
python3 tests/scroll-garden/step9_regression.py --suite chapter --engine chromium
python3 tests/scroll-garden/step9_regression.py --suite about --engine chromium
python3 tests/scroll-garden/step9_regression.py --suite films --engine chromium
python3 tests/scroll-garden/step9_fallback.py
python3 tests/scroll-garden/step9_recovery.py
python3 tests/scroll-garden/step9_scope.py
```

水球专项和chapter分别运行firefox/webkit。Linux环境沿用DISPLAY=:99、LD_LIBRARY_PATH=/workspace/.cache/browser-deps/root/usr/lib/x86_64-linux-gnu、PLAYWRIGHT_BROWSERS_PATH=/workspace/.cache/ms-playwright、COURTYARD_WEBKIT_EXECUTABLE=/workspace/.cache/browser-deps/run-webkit.sh。Chromium使用ANGLE/SwiftShader；GTK WebKit不等于Apple Safari，模拟手机不等于真机。

geometry检查完整600秒组合周期30001个实际形体/水束/事件样本、384次出生与8064轨迹点、实际变形三角形碰撞、迟时间与反向跳时的确定性、三尺寸采样像素直径和真实dispose事件。highlights用原材质实际白色混合量及深度遮挡测高光面积；诊断renderer/target仅存在于测试，产品无新增pass。

browser检查2/4/6/8秒双模式O/W、真实共享时间推进与暂停后RGB/绘制稳定、全路线缓存和orb=legacy独立退回第八步。regression复用原断言，适配当前标题/封面文件名、输出目录和允许的资源预算；现场体验先在两秒内确认布局/相机/绘制连续三帧稳定且至少观察120ms，再执行原250ms零新增绘制断言。逐帧记录保留，未把必要ResizeObserver布局末帧当作持续绘制。原脚本及旧证据不改。fallback/recovery复验原生媒体失败、实际后台隐藏及上下文恢复。

scope先保护2243份原文件，再比较三尺寸×两模式×五姿态30组纯场景；临时隐藏DOM，保留3D符印。只遮罩新旧球体、水束、实际可见飞滴和真实落点波纹的投影范围及12CSSpx像素边缘，外部要求零差异；不使用整池蒙版。orb=legacy的30组及默认参考稿双模式要求全图一致。`--scope-only`只核对文件，不启动浏览器。

```bash
python3 tests/scroll-garden/step9_layout.py --capture-cover
python3 tests/scroll-garden/step9_record.py
python3 tests/scroll-garden/step9_baseline.py --phase after --url http://127.0.0.1:4173
```

封面从当前真实画布导出；接入素材后再确认来源与最终源码摘要一致。录制与性能均独立运行，不并行其他浏览器检查。录制保留原时间，按实际环境时钟验证播放；性能同路线预热后各30次真实wheel，采样期间不截图，之后保存三尺寸84幅全路线双模式图。保留全部原始值和校准失败记录，不推断硬件FPS。

以下保留第八步及更早的历史复验说明，仅用于匹配版本；当前结果以第九步独立目录和验收说明为准。

---

# 滚动庭院历史复验：第八步

使用已安装的Python/Playwright/Pillow/websockets与本机浏览器，应用依赖未增加。当前开发5173、生产预览4173；第七步源/构建副本位于/tmp/scroll-garden-step-8-before，可用其dist启动4174作隔离对照。

```bash
npm run build
python3 tests/scroll-garden/step8_geometry.py
python3 tests/scroll-garden/step8_browser.py --engine chromium
python3 tests/scroll-garden/step8_regression.py --suite chapter --engine chromium
python3 tests/scroll-garden/step8_regression.py --suite about --engine chromium
python3 tests/scroll-garden/step8_regression.py --suite films --engine chromium
python3 tests/scroll-garden/step8_fallback.py
python3 tests/scroll-garden/step8_recovery.py
python3 tests/scroll-garden/step8_scope.py
```

水潭专项与chapter分别运行firefox/webkit。沿用DISPLAY=:99、LD_LIBRARY_PATH=/workspace/.cache/browser-deps/root/usr/lib/x86_64-linux-gnu、PLAYWRIGHT_BROWSERS_PATH=/workspace/.cache/ms-playwright、COURTYARD_WEBKIT_EXECUTABLE=/workspace/.cache/browser-deps/run-webkit.sh；Chromium使用ANGLE/SwiftShader。GTK WebKit与模拟手机不作Apple Safari或真机证明。

geometry逐个比较旧/新池体buffer/变换、植物实例与七个固定时间的jet/水滴/落点，检查14个独立绑定、真实高度和清理。覆盖率为仅测试的离屏诊断，产品没有额外renderer/target。

browser检查多时间双模式、实际共享时间推进、RGB截图变化、稳定暂停、完整缓存与legacy对照；RGBA截图先转RGB避免透明通道造成虚假相等。regression只改旧断言的标题/素材名、证据目录和已批准程序预算，不修改旧脚本/证据。fallback/recovery复验真实媒体失败及原生CDP隐藏/上下文恢复。

scope暂时隐藏DOM界面比较纯场景：30组对照、legacy30组与默认参考稿2图。新旧相机/文字状态一致，池体实际投影+12CSSpx以外要求零像素差。DOM文字/媒体另有完整交互回归。

```bash
python3 tests/scroll-garden/step8_record.py
python3 tests/scroll-garden/step8_baseline.py --phase after --url http://127.0.0.1:4173
```

录制和性能必须与其他浏览器工作分开。录制保留实际时间，播放验证依据共享时钟而非假定硬件FPS。before仅适用于隔离第七步4174，不得用当前源码覆盖。性能各30次真实wheel，采样期间不截图；先采样后保存84张三尺寸双模式全路径图与参考稿，原始值和峰值保留。

第九步只细化标准，没有第九步水球实现或通过证据。下面保留第七步及更早复验说明供匹配版本使用。

---

# 滚动庭院复验：当前第七步

第七步的检查使用已有Python/Playwright/Pillow/websockets；应用依赖未增加。准备现有开发5173与生产预览4173服务，并先运行 `npm run build`。

```bash
python3 tests/scroll-garden/step7_geometry.py
python3 tests/scroll-garden/step7_browser.py --engine chromium
python3 tests/scroll-garden/step7_regression.py --about --engine chromium
python3 tests/scroll-garden/step7_regression.py --engine chromium
python3 tests/scroll-garden/step7_fallback.py
python3 tests/scroll-garden/step7_resources.py
python3 tests/scroll-garden/step7_recovery.py
python3 tests/scroll-garden/step7_record.py
```

将三个带engine的命令分别运行firefox、webkit。沿用本机缓存的DISPLAY=:99、LD_LIBRARY_PATH=/workspace/.cache/browser-deps/root/usr/lib/x86_64-linux-gnu、PLAYWRIGHT_BROWSERS_PATH=/workspace/.cache/ms-playwright与COURTYARD_WEBKIT_EXECUTABLE=/workspace/.cache/browser-deps/run-webkit.sh。Chromium使用SwiftShader，GTK WebKit不等于Apple Safari，模拟手机不等于真机。

step7_browser检查18个显隐状态、三站完整阅读/反向复现、三个尺寸、真正单画布体验、主动设置保留、档案真实视频解码与释放、重复页签/新打开归顶、10轮资源稳定、触摸/减少动态及未知诊断。对比度从真实字符位置采集背景，DPR截图先归一至CSS坐标。媒体按需载入，不以旧夹具代替当前案例。

跨版本scope配对需要第六步隔离生产预览4174和当前第七步预览4173。第六步源码与构建配置保存在 `docs/evidence/scroll-garden-step-7/baseline-step6-source.tar.gz`，解压到单独目录，复用或安装锁定依赖并构建后启动4174。`step7_scope.py --scope-only`只刷新文件摘要，不启动浏览器。原始截图、柔边遮罩非重复性诊断与新配对截图分别保留。

step7_performance.py是仅采样工具，参数为 `--url`、唯一 `--label` 与 `--source-root`。在没有其他浏览器/录制时交替运行两个版本，每轮同样预热与30次wheel，附逐次CDP指标。原首测越线样本仍保留，复测不能覆盖。

step7_regression复用旧第六步源码中的A/B断言，仅适配STEP07标题、新C调试按钮数、额外项目dialog和已批准资源预算；所有旧脚本/证据保持，读历史路由与本轮新采集参考稿基线，写独立回归子目录。完整通过计数按本轮实际结果统计。

geometry复用历史几何检查，另查C下降1001样本、9次视线、45次稳定姿态、三个安全贴面、7个独立绑定、C3离柱连续，以及体验区主要物体8角均处于控件间可见区域。原buffer/实例与A/B锚点隔离保持。

fallback检查9种装饰/字体回退、无WebGL仍可读C与使用档案、真实封面/视频中断重试；故意失败诊断单列。recovery通过原生CDP真实切换标签，保留实际document.hidden、时钟/媒体暂停及上下文恢复证据。resources在每个模式访问全路径，区分局部缓存与完整缓存。

受控性能与画面对照：

```bash
python3 tests/scroll-garden/step7_baseline.py --phase after
python3 tests/scroll-garden/step7_scope.py
```

before仅适用于修改前第六步，不能用当前源码覆盖旧基线。前后各30次相同C路线实际wheel停止；运行时关闭其他浏览器检查与录制，采样期间不截图，之后才采集画面。保留原始值和峰值，不能推断硬件FPS或物理输入到显示延迟。scope保护全部旧文件，并单列新C石身导致的旧视角背景变化、已知浏览器文字舍入。

layout.py用于首轮诊断，`--capture-cover`从当前真实O画布导出新封面及来源记录；捕获后应核对源摘要和构建素材一致。录制是实际双向wheel与体验/视频/返回，MP4保持原时间，不等于硬件FPS证明。

证据统一保存在docs/evidence/scroll-garden-step-7/。以下为未改的第六步历史复验说明，仅在匹配版本下使用。

---

# 滚动庭院复验：当前第六步

应用依赖未增加。可选检查使用已有Python、Playwright、Pillow及原生恢复所需websockets 16.0，版本见此前测试环境说明。旧步骤脚本与原始证据保留，只在匹配版本复验，不能直接将旧通过计数用于新实现。

先在独立终端准备开发页和生产预览：

```bash
npm run dev -- --port 5173 --strictPort
npm run build
npm run preview -- --port 4173 --strictPort
```

当前检查：

```bash
python tests/scroll-garden/step6_geometry.py
python tests/scroll-garden/step6_browser.py --engine chromium
python tests/scroll-garden/step6_about_regression.py --engine chromium
python tests/scroll-garden/step6_player.py --engine chromium
python tests/scroll-garden/step6_fallback.py
python tests/scroll-garden/step6_resources.py
python tests/scroll-garden/step6_recovery.py
```

将三个带 `--engine` 的脚本分别以firefox、webkit运行，即覆盖第二柱、第一柱回归和隔离播放器。浏览器主检查及第一柱回归支持 `--url`（默认4173）；几何、播放器、原生恢复和降级使用现有本地5173/4173服务。隔离HTML只供测试，未加入生产构建入口或作品内容。

Chromium使用 `/usr/bin/chromium` 与ANGLE/SwiftShader。Linux Firefox/WebKit需要已有浏览器、本机库、显示服务和软件图形环境；本云环境缓存位于 `/workspace/.cache`，可复用 `DISPLAY=:99`、`LD_LIBRARY_PATH=/workspace/.cache/browser-deps/root/usr/lib/x86_64-linux-gnu`、`PLAYWRIGHT_BROWSERS_PATH=/workspace/.cache/ms-playwright` 和 `COURTYARD_WEBKIT_EXECUTABLE=/workspace/.cache/browser-deps/run-webkit.sh`。GTK WebKit不等于Apple Safari实机。

`step6_geometry.py`通过Vite调用 `inspect_film.js`，只读复用此前几何工具，核对3003路径样本、12条第二柱视线、60个满阅读姿态、1001个下降样本、边界连续、14个材质绑定、原几何/实例、原关键姿态与四个实际贴面锚点。采样不替代全部中间画面的视觉评审。

`step6_browser.py`检查四种策展结构、真实来源标识、请求时序、24个显隐状态、同站稳定画面、反向布局、输入、查看层、模式/尺寸/上下文恢复、暂停选择、资源和手机。对比度遍历真实文字节点，暂时隐藏字面采集背景后恢复；手机DPR截图按CSS坐标归一。背景采集图不是正常页面截图。原生scroll会取整，记录请求比例与实际H/U，不把边界微小量化差异写成状态错误。

`step6_about_regression.py`是当前第一柱/默认参考稿回归，原第五步脚本原件未改。测试探针只在浏览器注入，未写进应用。Firefox的PCF、故意上下文丢失和滚动关联定位提示原文保留；其他未解释诊断使正常检查失败。

`step6_player.py`访问 `media-fixture.html`，使用与产品相同的公开媒体组件，检查680×680/12秒庭院夹具的实际解码、帧变化、关闭释放、快速重开、单一video、切换、失败重试及10轮清理。夹具清楚标为非个人AI动画作品。它验证机制，不能作真实个人正片接入验收；故意失效媒体的诊断单独保存。

`step6_recovery.py`以直接CDP控制独立原生Chromium，观察实际document.hidden，不伪造可见性事件。包含B2标签返回、6.30H下降中途恢复、原图查看层隐藏返回、隔离视频隐藏暂停与返回不自播。采样前等待资源事件、实际比例和字体/布局稳定；结束时先关闭自己的浏览器，再清理私有目录并作有界重试。

`step6_fallback.py`检查两柱无Canvas2D、12种字体回退布局/对比度、无WebGL提示及15个图形控制、参考入口，以及真实图片中断、短失败提示、查看重试和进度恢复。`step6_resources.py`在pixel/native/pixel每种模式中访问全程关键姿态，给出完整缓存；它与仅在B4切换时的局部缓存结果分开。

性能对照：

```bash
python tests/scroll-garden/step6_baseline.py --phase after
```

`--phase before`仅适用于执行前第五步源码。此脚本在同一B区域预热路线之后测30次实际wheel停止，测量期间不截图或并行跑其他浏览器检查，之后保存画面与源码摘要。前后原始样本保留，不能用先前步骤的数字替代新基线。完整功能序列仅记录另行标明的聚合诊断，不混入受控样本。

真实操作录制：

```bash
python tests/scroll-garden/step6_record.py
```

需要Playwright已有ffmpeg录制组件，可使用上述浏览器缓存路径。14个位置以真实wheel驱动，按每次实际文档范围计算距离，记录实际H及检查点，最后实际打开/关闭原图。WebM可用本机ffmpeg转MP4；保留原时间，不是物理GPU FPS证明。`step6_layout.py`为首轮布局诊断工具，历史初始图片及其源码摘要不作为最终全部检查的替代。

本步证据位于 `docs/evidence/scroll-garden-step-6/`。当前为设计示意版与机制完成，真实影片/对应资料、完整手机/横屏和实机手感仍待补。测试工具不发布、部署、提交或推送代码，不重打包旧release归档。
