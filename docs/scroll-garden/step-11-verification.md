# 第11步验收：手机与阅读适配

结论：**本步实现与当前云环境可执行验收完成，停在第11步审阅点。真实设备与实际读屏复核尚未完成；第12步未执行。** 结果见[机器可读摘要](../evidence/scroll-garden-step-11/summary.json)，实现见[说明](step-11-implementation.md)。

## 本次实际结果

三引擎共215组功能检查通过：浏览方式与响应阅读49组、困难查看器12组、DPR/资源9组、原三柱回归145组。另有6组真实隐藏/图形恢复、2种原生浏览器200%缩放、3引擎查看器内旋转，以及3引擎图片/封面/视频失败重试。

108组完整场景逐像素一致：18个代表姿态（开场、十站、水潭、结尾和五段移动区）×三尺寸×两模式。默认参考页双模式也完全一致。没有遮罩、通道容差或测试滚动范围改写。三柱、水潭、水球、灯光、植物、魔法图形及原相机路线保持。

15,015个几何样本通过，仍为16段/12.3H；最小实体余量2.900975，最大边界跳变1.22092e-5，一阶导数差0.000550238，符合既定阈值。固定姿态与W稳定区继续保留。

## K01～K20逐项结果

| 项 | 当前环境结果 | 主要证据 |
| --- | --- | --- |
| K01 | 通过；第十步源码、静态构建与原文件摘要独立保留 | baseline-seal、baseline-files、baseline-step10.tar.gz |
| K02 | 通过；十个原article、唯一画布/场景/环境时钟，无重复核心正文或ID | 三引擎browser与renderer |
| K03 | 通过；按十站实际容量判定，稳定后不自动切回，十次临界/方向往返不闪切 | browser、overlay-resize |
| K04 | 通过；可容纳的竖屏继续运镜，小屏/短横屏完整稳定阅读 | 三引擎十站与尺寸矩阵 |
| K05 | 通过；正文正常至少16px，原三柱实际字符背景对比检查≥4.5:1；DOM字保持清晰 | regression-about/films/chapter |
| K06 | 通过；320宽、两类短横屏、200% rem大字、原生页面/仅文字200%缩放及临时长文可读 | browser、native-zoom、dialogs |
| K07 | 通过；安全区公式、模拟内边距、窗口/方向变化和控件可达；真机栏/刘海另列 | browser；边距校准见下文 |
| K08 | 通过；十次方式往返同布局原scrollY误差≤1px；旋转/大字保留C2等原内容块 | browser、overlay-resize、native-recovery |
| K09 | 通过工具可执行范围；原生wheel、触摸拖动、双触点缩放、文本选择与媒体控制保留 | browser、dialogs；工具限制见下文 |
| K10 | 通过；44×44目标、键盘、跳到内容、标题可访问状态和稳定版回看焦点正确 | browser、dialogs |
| K11 | 通过；真正减少连续运镜，环境播放与沉浸选择分开，取消系统偏好不自动开播 | browser、native-recovery |
| K12 | 通过语义检查；稳定版十站连续可访问、无重复正文，无滚动播报轰炸；真实读屏待核 | browser |
| K13 | 通过；两类查看层在短屏/大字可关闭，保留位置、焦点和最新模式/暂停选择 | dialogs、overlay-resize、原媒体回归 |
| K14 | 通过；无WebGL仍可读完整三章与档案，恢复不强制切模式；失败/重试/释放有效 | dialogs、native-recovery、media-faults |
| K15 | 通过；真实隐藏、封面离屏、档案覆盖与暂停停稳停止实际绘制，返回不补跑 | native-recovery、renderer |
| K16 | 通过；DPR1/2/3按上限2分配，相同尺寸不重复分配，十次循环资源不增长 | renderer、媒体循环与基线缓存 |
| K17 | 通过；同条件p95变化0.83%，在10%线内；不作为手机硬件FPS证明 | latency-before/after |
| K18 | 通过；108组纯场景、默认参考页与全部原三柱回归 | paired-scene-isolation、regression |
| K19 | 当前环境通过；真实手机、读屏、系统栏与物理触控板/APZ明确待复核 | 平台与限制表 |
| K20 | 通过；严格类型检查、生产构建、必要回归和本步交付完成 | build-verification、scope-guard |

## 画幅与浏览器

| 覆盖 | 实际范围 |
| --- | --- |
| 三引擎 | Chromium 155.0.8059.79、Firefox 153.0、GTK WebKit 26.5 |
| 桌面 | 1440×900、1366×768；正常/像素、十站、导航、回看与查看器 |
| 手机/小屏 | 390×844主流程三引擎；320×568、375×667、430×932由Chromium覆盖，另外两引擎补320困难组合 |
| 短横屏/平板 | 667×375、844×390、768×1024；三引擎补844×390和查看器困难布局 |
| 大字 | 三引擎200% rem模拟；Chromium原生页面200%、Firefox原生仅文字200%，分别记录 |
| 图形/媒体 | 三引擎真实图形创建失败、图片/封面/视频网络失败与重试；Chromium上下文扩展真实丢失/恢复 |
| 输入 | 原生wheel、Home/End/Enter/Tab、原生tap；Chromium CDP触摸拖动与双触点分离缩放 |

GTK WebKit的固定手机仿真在动态旋转时，设备指标、屏幕覆盖与CSS视口更新不同步，已保留诊断。旋转回归采用支持触摸的真实CSS布局视口，并核实100vw与innerWidth一致；独立的is_mobile固定390、844横屏和320大字查看器仍检查。Firefox不支持is_mobile标志，也使用触摸布局视口。这些都不是物理手机方向传感器证据。

手机WebKit明确不支持工具wheel接口，查看器专项使用原生PageDown验证背景不漂移，普通布局wheel由原三柱回归覆盖。Chromium的简化synthesizePinchGesture在本环境没有缩放，未记为通过；改用实际双触点输入，观察到visualViewport.scale增加，再由测试恢复缩放。未由产品代码限制或重置用户缩放。

边距作了保持原UI节奏的校准：沉浸手机顶内边距14px并计入安全区，侧边16px；稳定版顶部取16px与安全区较大者。它与标准初拟的全向16px不同，记录为版式校准，不冒称逐边都按原16px实现。安全区内操作可达、44px目标、正文完整和无非预期横滚的检查通过。

## 性能、资源与暂停

同环境独立重测第十步与第十一步：1440×900，固定时间2，正常/像素/像素回到原模式的全路线预热，五段移动区各+15px三次、−15px三次，每版本30次原生wheel。采样期间无另一浏览器、截图或录屏；采完才保存画面。初次before样本另存为历史，不挑最好的一轮。

| 诊断 | 第十步 | 第十一步 |
| --- | ---: | ---: |
| p95 | 181.3ms | 182.8ms |
| 最大 | 192.8ms | 189.9ms |
| 样本 | 30 | 30 |

p95变化0.83%，接近基线并符合≤10%的标准。以上是Linux软件图形受控诊断，不是手机GPU帧率或物理触控板延迟。

Chromium全路线预热仍为58几何、6纹理、单模式12程序、双模式22缓存，O点像素68/正常67 draw calls。三引擎DPR1/2/3、相同尺寸十次事件与媒体循环无持续增长。暂停停稳后400ms窗口零新增GL绘制；环境播放意图保留但封面离屏时也零绘制，回到可见封面后才继续。

## 演示与证据入口

- [手机操作演示](../evidence/scroll-garden-step-11/mobile-reading-demo.mp4)：17.28秒，390×844，实际tap/wheel、方式切换、样片查看、现场体验/档案/真实旧片段与返回。
- [横屏与大字演示](../evidence/scroll-garden-step-11/landscape-large-text-demo.mp4)：10.80秒，844×390；大字部分是rem模拟，原生缩放另外有独立证明。
- [录像原始动作与编码资料](../evidence/scroll-garden-step-11/demo-recording.json)：原始时间，无加速；源/输出长度与解码释放记录保留。
- [三引擎主流程](../evidence/scroll-garden-step-11/browser-chromium.json)、[Firefox](../evidence/scroll-garden-step-11/browser-firefox.json)、[WebKit](../evidence/scroll-garden-step-11/browser-webkit.json)。
- [原生浏览器缩放](../evidence/scroll-garden-step-11/native-zoom.json)、[真实隐藏与恢复](../evidence/scroll-garden-step-11/native-recovery.json)、[查看层内旋转](../evidence/scroll-garden-step-11/overlay-resize.json)、[媒体失败重试](../evidence/scroll-garden-step-11/media-faults.json)。
- [完整场景对照](../evidence/scroll-garden-step-11/paired-scene-isolation.json)、[几何连续性](../evidence/scroll-garden-step-11/geometry-continuity.json)、[原文件保护](../evidence/scroll-garden-step-11/scope-guard.json)、[构建摘要](../evidence/scroll-garden-step-11/build-verification.json)。
- [独立第十步快照](../evidence/scroll-garden-step-11/baseline-step10.tar.gz)、[快照摘要](../evidence/scroll-garden-step-11/baseline-seal.json)，复验方式见[测试说明](../../tests/scroll-garden/README.md)。

全部结果与最终63份TS/CSS源码摘要对应，构建文件另有摘要；实施前4016份文件的保护检查保留。原三柱回归的旧减少动态合同改为普通触摸阅读，新的稳定阅读另外验证；图形恢复后先确认稳定十站，再显式选择沉浸继续原断言。未削弱相机、内容、媒体释放、实际对比度或暂停零绘制要求。

## 保留的范围

本环境未连接真实iOS/Android设备或实际VoiceOver/TalkBack。真实系统大字、刘海与地址栏伸缩、手机惯性/旋转、物理触控板、Firefox APZ体验和硬件FPS仍待复核，不能从模拟或GTK WebKit推导为通过。

真实个人AI影片与联系方式仍待提供。设计样片和早期12秒庭院片段继续显示来源/版本，不当成个人客户影片或当前全程录像。封面素材、旧视频、历史证据、依赖和release保持。

修改保存工作区，当前构建已更新；没有发布、部署、Git提交或推送。停在第11步，第12步须另行细化与明确开始。
