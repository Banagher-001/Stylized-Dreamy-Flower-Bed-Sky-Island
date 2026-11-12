# 第六步验收：设备、异常、输入与恢复

本步宿主核心加固已完成。最终构建及49组核心验收通过，范围覆盖真实 Chromium、Firefox、WebKit，引入的修复集中在错误文档识别、图形上下文丢失与恢复提示、全屏受限提示，以及当前文档重新观察。原网页及其46个运行文件未改。

本次没有连接 iOS/Android 真机，没有触发实际 BFCache 缓存恢复；这些边界与屏幕阅读器、硬件性能等单列未验证，不宣称全设备兼容或完整原功能逐项回归。没有提交、推送或发布。

## 1. 复现和实际修改

| 项目 | 复现依据 | 最终行为 |
|---|---|---|
| 完整加载的错误HTML仍停在loading | `before-fix/browser.json` → document wrong HTML，实际HTTP404，完整错误文档无原#app/viewport | 导航完成后明确缺失原页结构则error，提供重试；不猜测页面脚本无法读取的HTTP状态 |
| 原图形上下文丢失但宿主仍ready | 同记录 → graphics child context loss，真实WEBGL_lose_context，原API ready仍true | 监听当前子文档canvas真实lost/restored，旧ready不掩盖丢失；恢复事件后保留需要重新载入的提示 |
| 全屏被实际策略禁止但缺少能力提示 | `permission-before/browser.json`，子文档fullscreenEnabled=false | 场景保持ready，显示全屏受限说明，不把它当场景加载错误，也不展示无意义的重试按钮 |
| 前台返回与页面恢复 | 新管理器生命周期检查 | visibility返回和pageshow立即重读当前文档；不重新创建实例或自动继续导览 |

修改范围只有3个既有生产输入：

- `createLawsonExperience.ts`：完整文档结构判断；按文档拥有的canvas事件监听及清理；图形恢复保守处理；真实fullscreenEnabled限制；前台/页面恢复观察。
- `createProjectViewer.ts`：显示具体宿主原因和能力说明，保留原页面与操作；能力说明不显示重试；移除错误文档也有“原页重试”的不准确通用文案。
- `startTourPrototype.ts`：把管理器的可选说明传给查看层。

没有修改主场景、原UI、模型、动画时钟、默认画质、原业务API或原46文件，没有新生产文件、iframe样式注入或生产桥接脚本。其他92个主站生产输入保持原样。

图形恢复采用明确边界：原API的ready早于新的GPU代次，原页没有提供新的恢复就绪信号。本步不凭该旧标记自动宣称恢复完成；真实restored后显示“图形连接已恢复，请重新载入场景”，访客显式重试建立新文档后才重新ready。反馈不遮挡原页面。

## 2. 核查环境与版本

| 环境 | 实际结果和边界 |
|---|---|
| Chromium 155.0.8059.79 | 有界面模式，Mesa软件WebGL；主要交互、异常和原生权限验证 |
| Firefox 153.0 | 实际引擎/原页运行，桌面、手机视口、连续尺寸变化和原灯光控件通过 |
| WebKit 26.5 | 实际Linux WebKit包运行，同类布局/控件通过；不等于macOS或iOS Safari真机 |
| 手机触摸 | 浏览器原生输入模拟，touch事件isTrusted=true，非物理手指设备 |
| 原生Chrome | 独立临时profile，CDP连接使用no_defaults=True，真实标签隐藏/返回；未改document.hidden或手工派发事件 |

WebKit首次依赖探针没有识别缓存库，原包启动脚本还会覆盖LD_LIBRARY_PATH。保留失败记录后，用独立测试启动脚本把已有缓存库加入运行路径，实际启动并取得WebGL2及应用就绪，未修改浏览器原包或安装生产依赖。见 [browser-capabilities.json](../evidence/lawson-fullpage-step-6/browser-capabilities.json) 和测试启动脚本。

## 3. 49组核心通过结果

逐组记录和精确构建来源见 [accepted-browser-results.json](../evidence/lawson-fullpage-step-6/accepted-browser-results.json)。

| 类别 | 组数 | 实际覆盖 |
|---|---:|---|
| 文档/图形/小屏反馈 | 3 | 错误HTML；真实子canvas丢失及恢复、旧ready保持无效并经宿主重试恢复；320×568错误状态＋200%宿主字号 |
| 视口与连续尺寸变化 | 15 | Chromium八种视口和连续旋转；Firefox、WebKit各桌面/手机及连续尺寸变化 |
| 网络异常 | 7 | HTML404/500、vendor模块失败、车辆模型失败、冷/热缓存离线与恢复、实际frame-ancestors限制及独立打开 |
| 触摸/键盘/压力/接管/缩放/安全区 | 6 | 单指旋转、双指缩放、控制台触摸滚动、点按；53次原生Tab遍历；10次完整及20次快速取消；媒体接管；真实浏览器200%缩放；实际CSS env安全区模拟 |
| 减少动态、主图形恢复和历史返回 | 3 | 减少动态保留原JS行为；主庭院lost/restored不唤醒覆盖绘制；实际历史返回后重新加载可操作 |
| 隐藏/返回 | 3 | loading、ready、error均观察父/子文档真实hidden及visible，保持实例；加载阶段后台等待13秒到slow后仍可恢复 |
| 原生权限 | 3 | 实际策略拒绝全屏、无用户激活的原指针锁定请求拒绝、原按钮全屏/锁定及X11 Esc成功路径 |
| Vite HMR | 4 | 隔离副本loading/ready/error真实模块更新清理旧实例，新体验可用；CSS更新保留当前iframe |
| 最终构建三引擎及独立原页对照 | 4 | 三引擎实际能力与原灯光控制；同视口独立原页/内嵌手机版结构、默认值和布局对照 |
| 浏览器禁用WebGL | 1 | 真正以--disable-webgl启动，原渲染器失败后主站阅读、档案、返回仍可用 |
| 合计 | 49 | 不含失败探针、较弱的模拟结果和未验证设备 |

布局视口为1920×1080、1440×900、1366×768、768×1024、390×844、375×812、320×568、844×390。原页填满工具栏剩余区域；宿主按钮至少44×44；小屏反馈/档案和关闭可达，原页控件维持原尺寸。

实际浏览器200%缩放使用原生X11按键：CSS视口从1440×913变为720×456，DPR从1变2，根字号仍16px；与把宿主根字号改为32px分开记录。见interactions中的zoom组。

安全区使用协议实际存在的 `Emulation.setSafeAreaInsetsOverride`，将CSS env置为上24、左右20、下34。在390×844中，工具栏70高，iframe为x20/y70/350×740，底部到810，保留34下安全区。此为真实浏览器env模拟，不是物理刘海或地址栏验证。

## 4. 后台与资源恢复的实证

自动化框架默认强制focus/visibility，最初切标签没有出现真实hidden，相关探针保留且未作为后台通过依据。随后启动独立Chrome，使用默认上下文及no_defaults CDP连接，父页和原iframe都实际变为hidden，再返回visible。没有覆写属性、手工事件或修改应用时钟。

加载阶段在后台等待13秒，实际状态为slow，返回释放真实模型请求后ready；运行及错误阶段亦保留当前iframe，错误通过显式重试恢复，导览不自启。三组均证明返回后覆盖状态主庭院连续1秒draw=0。

主庭院在覆盖期间丢失/恢复context，罗森保持独立可用、主庭院不持续绘制。丢失会按已有规则转入稳定阅读；关闭后封面仍离屏时继续停绘，滚回可见封面后再完成ready。检查脚本没有为了得到ready而强迫离屏绘制。

10次完整开关和20次同任务取消，无重复iframe、打开模态框、幽灵绘制或滚动锁；旧计数对象在卸载后保持不变。强制跨媒体接管明确标注为竞态注入，正常入口没有新增隐藏快捷操作。没有承诺GPU内存立即释放。

## 5. 原页功能与现有限制

在390×796原文档视口，对照独立原页与内嵌：均41个原控件，品牌/控制台/顶栏本地bounds相同，默认18.5和屋顶可见一致。两者都存在原品牌与顶栏重叠，未将该原问题冒充宿主修复。见compat-chromium中的独立对照。

权限拒绝路径中，原脚本仍会产生其原有Promise拒绝（全屏策略不允许、缺少指针锁定用户激活）；没有全局吞错或改写原控制器。宿主给出已确认的能力提示，场景仍就绪、返回有效。原减少动态CSS也不代表原JS停止，本步实际观察了其继续绘制，没有调用pauseAll伪装停绘。

仍未验证：iOS/Android真机、物理刘海/动态地址栏/操作系统字号、真实屏幕阅读器、硬件GPU性能。历史返回本次确实是整页重新加载，未触发BFCache恢复；不能据此把缓存恢复分支写为通过。Firefox/WebKit的全套后台和原生权限组合没有穷举。原41控件/17类点击完整对照留到第七步。

## 6. 构建、日志与尝试保留

最终 [build-2.log](../evidence/lawson-fullpage-step-6/build-2.log) 构建成功，包含tsc；git diff --check通过。输入/输出哈希在 [build-result.json](../evidence/lawson-fullpage-step-6/build-result.json)。

build1完成文档、GPU和当前文档观察修复；build2仅补真实fullscreenEnabled限制与宿主能力说明，精确差异在 [build-1-to-2.patch](../evidence/lawson-fullpage-step-6/build-1-to-2.patch)。最终构建重新核查能力拒绝、三种引擎实际控件、相关边界和原生成功路径；未受影响的布局/生命周期及隔离HMR结果保留准确版本来源，未冒充同一次全量构建测试。

测试工具修正也保留：1920视口300ms采样可能没有下一帧，改为等待实际绘制；Tab可进入浏览器自身UI，检查不把它误当背景控件；主庭院稳定阅读离屏恢复不强求绘制；SafeArea接口先用错方法名，查协议后实际env调用通过。旧失败及中间探针均未覆盖。

[event-audit.json](../evidence/lawson-fullpage-step-6/event-audit.json) 对接受用例的日志逐项归因：无未归因新增错误，42条预期故障错误和52条警告保留。源自注入HTTP/资源/权限失败的错误、原自适应画质及引擎警告，与宿主新增异常分开。日志归因不是原脚本所有异常均已修复的声明。

## 7. 完整性和交接

[integrity.json](../evidence/lawson-fullpage-step-6/integrity.json) 核验源/public/dist每份46文件、20,332,784字节均匹配固定SHA-256。源仓库工作区干净、HEAD保持95dad9881a7b9d31c0ac635f1f335055d8cb3cc4；主仓库HEAD保持4a6dd7c5c9c126ab3b9319fab5d8ea16a704dae8。

六组历史封存77/109/115/95/95/51文件及manifest不变。95个主站输入仅3个授权修改，其余92个保留，没有新增生产文件。修改前后源码副本、差异、构建和独立封存属于本步，后续不回写历史。

本次未提交、推送或发布。[第七步交接](step-6-handoff.md) 提供最终逐项原功能回归入口和设备证据边界。

截图：[小屏错误＋200%字号](../evidence/lawson-fullpage-step-6/boundary-final/small-error-200.png)、[真实CSS env安全区模拟](../evidence/lawson-fullpage-step-6/safe-area-final/emulated-safe-area.png)、[原生浏览器200%缩放](../evidence/lawson-fullpage-step-6/interactions/native-browser-200.png)。
