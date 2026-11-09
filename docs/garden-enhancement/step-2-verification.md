# 第二步验收：关于我背景羽化

候选 **garden-enhancement-step2-3a477d247f5475fe**。本步完成状态以[summary.json](../evidence/garden-enhancement-step-2/summary.json)为准；以下分别列出本次实测、代码保护与未具备的设备条件。新导览、水球流纹、云影和飞鸟不在本步验收范围。

## 背景、正文与输入实测

| 引擎 | 站点/阶段/方向条件 | 前后实际尺寸背景对 | 保守最低正文对比度 | 新外缘最大alpha |
| --- | --- | --- | --- | --- |
| Chromium155 | 108 | 18 | 5.5553:1 | 0 |
| Firefox153 | 108 | 18 | 5.5850:1 | 0 |
| GTK WebKit26.5 | 108 | 18 | 5.5674:1 | 0 |

三引擎共324个显现/阅读/离开与正反向条件，54组实际背景前后测量；另有4个实际可沉浸边界/DPR3样本。每次同步比较原文字、字框/面板几何、aria/inert、相机、阅读阶段与环境时间，均保持。它们不是旧215组功能检查或第一步51图的重新命名。

主矩阵为1440×900/DPR1、1366×768/DPR1和390×844/DPR2，各自像素/正常两种画面、A1/A2/A3。窄屏/短横屏/DPR3及200%rem使用标准规定的代表子集；不宣称所有条件的全组合或真实手机通过。

来源：[Chromium](../evidence/garden-enhancement-step-2/background-chromium.json)、[Firefox](../evidence/garden-enhancement-step-2/background-firefox.json)、[WebKit](../evidence/garden-enhancement-step-2/background-webkit.json)。

正式页面完整前后截图和背景测量分别保存。背景测量只隔离下方场景与正文，保留真实背景的遮罩、颜色、尺寸和透明度，采样后恢复并核对属性相同。Chromium/WebKit得到实际透明PNG；Firefox截图后端不支持透明截屏，以同一背景在黑/白底上的两份实际截图差分解算alpha，原截图保留，没有二次羽化或修改目标遮罩。外缘透明与整条边缘到中心单调过渡同时检查，不以单根透明线判定完成。

正文对比度使用每个可见字符范围的实际背景RGBA，在最不利白底上合成后计算；Firefox直接用实际白底渲染。该下界保守覆盖实际庭院底色，忽略文字发光的额外帮助；最低5.5553:1超过4.5:1要求。第一步旧遮罩固有尺寸43/255读数仍保留，本文数据是本步实际尺寸测量。

本次额外输入/阅读条件为Chromium9组、Firefox7组、WebKit7组：实际选择与可信copy事件、原生小幅wheel、三次稳定/沉浸阅读往返、原正文节点保持、键盘Enter与焦点、手机tap、Chromium实际触摸拖动、容量边界、200%rem、减少动态和实际WebGL创建失败。WebKit固定mobile的wheel接口不可用，相关步骤如实跳过该接口，普通布局wheel、tap和其他引擎原生触摸另测；没有产品UA特例。

320px/200%文字的原有8px开场溢出得到修复，字体、正文和按钮不缩小、不裁切；[诊断](../evidence/garden-enhancement-step-2/preexisting-overflow-diagnostic.json)证明基线也有同样现象。本步允许范围内仅增加两条稳定阅读收缩/换行规则，修复后的三引擎代表条件无横向溢出，第一柱背景在稳定阅读为display:none。

## 保护项、资源和作品返回

[scene-resource-viewer-scope.json](../evidence/garden-enhancement-step-2/scene-resource-viewer-scope.json)记录：

- 12组完整GPU画布对照逐像素一致：三画幅、两模式、A2及水潭。只有为GPU隔离等量隐藏DOM界面，全部场景与GPU文字保留，无图像掩码、裁掉场景或通道容差；正式背景效果另用完整未处理页面验收。
- 第二/三柱8组完整页面和旧参考稿2组完整页面逐像素一致。图像按实际decode完成后采样，不用尚未完成绘制的媒体状态比较。
- 三画幅各10次预热画面模式循环，几何58、纹理6、双模式程序22保持，与独立基线同条件统计一致；本步新增WebGL资源为0。CSS合成成本与Three资源计数分别看待。
- 桌面/手机2组完整图片、现场体验/档案及早期视频返回保持在1CSS px内，场景始终一个画布，关闭后视频释放；作品层中介绍背景不可见。

## 性能、构建与演示

本步将独立基线和候选顺序运行，基线/候选各30次原有转场wheel，加各18次介绍实际显现、背景透明度变化中的wheel，两个样本组单独统计。后者用于覆盖本次CSS背景正在绘制的情况，不以背景隐藏时的转场数据替代。采样不与其他浏览器、截图或录屏并行。

实际数值和同条件差异见[修改前](../evidence/garden-enhancement-step-2/latency-before.json)、[修改后](../evidence/garden-enhancement-step-2/latency-after.json)及[比较](../evidence/garden-enhancement-step-2/performance-comparison.json)。不将第一步190.6ms跨会话当成本次修改前数值。软件SwiftShader数据只用于版本响应比较，不代表硬件或手机FPS。

| 样本组 | 每版样本 | 修改前p95 | 修改后p95 | 变化 |
| --- | --- | --- | --- | --- |
| 原有转场 | 30 | 184.8ms | 187.5ms | +1.46% |
| 介绍背景显现 | 18 | 241.1ms | 199.1ms | −17.42% |

两组均在不恶化超过10%的比较预算内，原始样本全部保留，未挑选最好运行结果。

严格类型检查和生产构建通过，18份产物对应80份实际构建输入；完整摘要及工具链见[构建证明](../evidence/garden-enhancement-step-2/build-verification.json)。没有新增依赖、外部资源或WebGL材质。代码只有`tour.css`及`readingLayout.css`两份变化，TypeScript、素材、相机、水体和环境逻辑均未改。

17.24秒原速[滚动演示](../evidence/garden-enhancement-step-2/about-feather-demo.mp4)使用真实章节/画面按钮及前后原生wheel，展示A1→A2→A3→A2→A1。它是手动浏览，不是尚未实现的自动导览；动作/时间及转码原速核对见[录像记录](../evidence/garden-enhancement-step-2/about-feather-recording.json)。

## F01～F15签收对应

| 条件 | 判定证据 |
| --- | --- |
| F01 | before-files/baseline-version保存5037个原有文件摘要，独立第一步基线解压核验 |
| F02 | 只有两份获准CSS变动，三段正文、原节点与几何/可访问状态实测相同 |
| F03 | 实际尺寸/DPR背景外缘alpha0，透明安全带保留，测量方法与原图可复核 |
| F04 | 四边渐变单调，四角不叠加暗色，完整原页视觉对照保留 |
| F05 | 三引擎最低保守对比度5.5553:1，文字未模糊或重建 |
| F06 | 324个正反向显隐/阅读/离开条件，状态和原几何一致，无新时钟 |
| F07 | 原生选择/copy、键盘焦点、tap和Chromium拖动；装饰pointer-events:none |
| F08 | 主画幅、容量边界、DPR3及200%rem代表样本通过，原320px溢出已修复 |
| F09 | 稳定阅读无悬浮背景，减少动态暂停、原生图形失败仍完整读三章 |
| F10 | 实际背景边界在视口内，未遮挡控件，背景不改变原面板盒/点击范围 |
| F11 | 三引擎本次主检查均通过；Firefox测量后端及WebKit mobile接口限制如实分列 |
| F12 | 12组完整GPU、8组其他章节整页、2组旧稿整页相同；作品返回保持 |
| F13 | 三画幅资源循环新增0；性能以本次独立前后样本及比较报告签收 |
| F14 | 严格类型检查、生产构建通过；产物与最终来源摘要一致 |
| F15 | 本实现/验收、截图、测量、演示和范围保护齐全；未开启第三步 |

最终逐项状态在summary中集中签收，原文件/素材/旧ZIP与第一步证明的保护见[scope-guard.json](../evidence/garden-enhancement-step-2/scope-guard.json)。本步未重封旧包、未Git提交/推送或部署。

真机iOS/Android、OS大字/安全区、触摸选字手柄/系统剪贴板、实际读屏、物理触控板/APZ与硬件FPS仍待实机复核。不能把上述浏览器模拟、可信copy事件或软件截图当作这些设备能力已经验证。
