# 第七步：完整原功能配对表

第七步已完成。候选 `bottle-ocean-step7-3b31ab385ebfc4cb`；日期 2026-11-14（Asia/Shanghai）。在已验证范围内，瓶中海洋的原功能在 Coding 大尺寸现场保留。34 个原 DOM 控件为 12 滑杆和 22 按钮；下表恰好 34 行。68 项配对检查是功能组计数，不冒充 68 个原控件。

## 配对条件和方法

固定原提交 `d94c1f911a39143fd8f5efe152b99a87fdc53184`，原/内嵌 HTML SHA256 均为 `941feb2ea6ddd3cc93aad5b0b92dbca52ee66a3e1098fee0dbf16f01ca63d1ef`。独立原页由原仓库 HTTP 提供；内嵌为最终生产构建。逐组先后运行，两端使用同引擎版本、实际子视口、DPR、触摸与原前置状态，通过真实鼠标、键盘、触摸和原按钮操作。

| 条件 | 宿主外层 | 两端实际原画布/子视口 | DPR |
|---|---|---|---|
| 桌面 | 1440×900 | 1440×844 | 1 |
| 手机竖屏模拟 | 390×844 | 390×796 | 3 |
| 手机横屏模拟 | 844×390 | 844×342 | 3 |
| 窄屏模拟 | 320×740 | 320×692 | 2 |

实际尺寸来自先测量再配对，见 [pair-conditions.json](../evidence/beach-bottle-boat-step-7/pair-conditions.json)。观察器只读取诊断，并在调用原 GL 绘制函数时原参委托一次以计数，不改原时钟、RAF、dt、随机数、物理、相机或设置 API。额外的观察 RAF 只采样；数值确定量比较容差 1e-6，不要求自然动画同相位。就绪同时核对当前 API/canvas、真实绘制、loader 和错误。

## 34 控件逐行结果

每行链接分别包含原生输入、前置和实际对象/相机/文件结果，行内效果必须与该控件对应；共享组文件仍按控件分别列行。低中高与一次方向键步进的原始值均保存在滑杆 samples/nativeStep 中。

| 控件 | 功能 | 实际效果与保留差异 | 两端原始记录 | 结论 |
|---|---|---|---|---|
| CTL-01 | 收起/展开面板 | 真实折叠→展开，面板尺寸及可操作状态记录 | [原页](../../docs/evidence/beach-bottle-boat-step-7/chromium-controls/BUTTON-interface-reference.json) / [内嵌](../../docs/evidence/beach-bottle-boat-step-7/chromium-controls/BUTTON-interface-embedded.json) | 配对通过 |
| CTL-02 | 隐藏界面 | 真实隐藏 UI，画布继续绘制 | [原页](../../docs/evidence/beach-bottle-boat-step-7/chromium-controls/BUTTON-interface-reference.json) / [内嵌](../../docs/evidence/beach-bottle-boat-step-7/chromium-controls/BUTTON-interface-embedded.json) | 配对通过 |
| CTL-03 | 波高 | 0/50/100 与步进；实际波场振幅及连续浮沉 | [原页](../../docs/evidence/beach-bottle-boat-step-7/chromium-controls/SLIDER-waveHeight-reference.json) / [内嵌](../../docs/evidence/beach-bottle-boat-step-7/chromium-controls/SLIDER-waveHeight-embedded.json) | 配对通过 |
| CTL-04 | 波速 | 0.2/1.6/3 与步进；实际波场 omega | [原页](../../docs/evidence/beach-bottle-boat-step-7/chromium-controls/SLIDER-waveSpeed-reference.json) / [内嵌](../../docs/evidence/beach-bottle-boat-step-7/chromium-controls/SLIDER-waveSpeed-embedded.json) | 配对通过 |
| CTL-05 | 波浪密度 | 0.5/1.75/3 与步进；实际波数 k | [原页](../../docs/evidence/beach-bottle-boat-step-7/chromium-controls/SLIDER-waveDensity-reference.json) / [内嵌](../../docs/evidence/beach-bottle-boat-step-7/chromium-controls/SLIDER-waveDensity-embedded.json) | 配对通过 |
| CTL-06 | 波向 | 0/180/360 与步进；方向向量，另补四方向连续样本 | [原页](../../docs/evidence/beach-bottle-boat-step-7/chromium-controls/SLIDER-waveDirection-reference.json) / [内嵌](../../docs/evidence/beach-bottle-boat-step-7/chromium-controls/SLIDER-waveDirection-embedded.json) | 配对通过 |
| CTL-07 | 水位 | 0/50/100 与步进；水面 baseLevel 和船体连续跟随 | [原页](../../docs/evidence/beach-bottle-boat-step-7/chromium-controls/SLIDER-waterLevel-reference.json) / [内嵌](../../docs/evidence/beach-bottle-boat-step-7/chromium-controls/SLIDER-waterLevel-embedded.json) | 配对通过 |
| CTL-08 | 船体响应 | 0/50/100 与步进；0/100 连续姿态差异、原响应公式 | [原页](../../docs/evidence/beach-bottle-boat-step-7/chromium-controls/SLIDER-boatResponse-reference.json) / [内嵌](../../docs/evidence/beach-bottle-boat-step-7/chromium-controls/SLIDER-boatResponse-embedded.json) | 配对通过 |
| CTL-09 | 船体阻尼 | 0/50/100 与步进；0/100 连续轨迹、原阻尼公式 | [原页](../../docs/evidence/beach-bottle-boat-step-7/chromium-controls/SLIDER-boatDamping-reference.json) / [内嵌](../../docs/evidence/beach-bottle-boat-step-7/chromium-controls/SLIDER-boatDamping-embedded.json) | 配对通过 |
| CTL-10 | 风力 | 0/50/100 与步进；真实 wind、漂移及自然衰减 | [原页](../../docs/evidence/beach-bottle-boat-step-7/chromium-controls/SLIDER-wind-reference.json) / [内嵌](../../docs/evidence/beach-bottle-boat-step-7/chromium-controls/SLIDER-wind-embedded.json) | 配对通过 |
| CTL-11 | 精致画质 | 实际 scale=2、levels=48 与内部尺寸 | [原页](../../docs/evidence/beach-bottle-boat-step-7/chromium-controls/BUTTON-qualities-reference.json) / [内嵌](../../docs/evidence/beach-bottle-boat-step-7/chromium-controls/BUTTON-qualities-embedded.json) | 配对通过 |
| CTL-12 | 标准画质 | 实际 scale=2.85、levels=26；原 range=2.9 保留 | [原页](../../docs/evidence/beach-bottle-boat-step-7/chromium-controls/BUTTON-qualities-reference.json) / [内嵌](../../docs/evidence/beach-bottle-boat-step-7/chromium-controls/BUTTON-qualities-embedded.json) | 配对通过；原有差异保留 |
| CTL-13 | 复古画质 | 实际 scale=3.8、levels=12 与内部尺寸 | [原页](../../docs/evidence/beach-bottle-boat-step-7/chromium-controls/BUTTON-qualities-reference.json) / [内嵌](../../docs/evidence/beach-bottle-boat-step-7/chromium-controls/BUTTON-qualities-embedded.json) | 配对通过 |
| CTL-14 | 像素强度 | 1/3/5 与步进；post.scale 与实际内部像素尺寸 | [原页](../../docs/evidence/beach-bottle-boat-step-7/chromium-controls/SLIDER-pixelScale-reference.json) / [内嵌](../../docs/evidence/beach-bottle-boat-step-7/chromium-controls/SLIDER-pixelScale-embedded.json) | 配对通过 |
| CTL-15 | 夕阳时间 | 0/50/100 与步进；实际灯色/强度 | [原页](../../docs/evidence/beach-bottle-boat-step-7/chromium-controls/SLIDER-sunset-reference.json) / [内嵌](../../docs/evidence/beach-bottle-boat-step-7/chromium-controls/SLIDER-sunset-embedded.json) | 配对通过 |
| CTL-16 | 亮度 | 0.6/1.1/1.6 与步进；实际曝光；默认 0.82/0.8 差异保留 | [原页](../../docs/evidence/beach-bottle-boat-step-7/chromium-controls/SLIDER-brightness-reference.json) / [内嵌](../../docs/evidence/beach-bottle-boat-step-7/chromium-controls/SLIDER-brightness-embedded.json) | 配对通过；原有差异保留 |
| CTL-17 | 瓶身透明度 | 0.04/0.22/0.4 与步进；实际玻璃材质 uniform | [原页](../../docs/evidence/beach-bottle-boat-step-7/chromium-controls/SLIDER-glassOpacity-reference.json) / [内嵌](../../docs/evidence/beach-bottle-boat-step-7/chromium-controls/SLIDER-glassOpacity-embedded.json) | 配对通过 |
| CTL-18 | 灯塔灯光 | 实际灯光关闭并恢复 | [原页](../../docs/evidence/beach-bottle-boat-step-7/chromium-controls/BUTTON-toggle-lighthouse-reference.json) / [内嵌](../../docs/evidence/beach-bottle-boat-step-7/chromium-controls/BUTTON-toggle-lighthouse-embedded.json) | 配对通过 |
| CTL-19 | 浪花效果 | 实际浪花对象关闭并恢复 | [原页](../../docs/evidence/beach-bottle-boat-step-7/chromium-controls/BUTTON-toggle-spray-reference.json) / [内嵌](../../docs/evidence/beach-bottle-boat-step-7/chromium-controls/BUTTON-toggle-spray-embedded.json) | 配对通过 |
| CTL-20 | 沙尘粒子 | 实际沙尘对象关闭并恢复 | [原页](../../docs/evidence/beach-bottle-boat-step-7/chromium-controls/BUTTON-toggle-dust-reference.json) / [内嵌](../../docs/evidence/beach-bottle-boat-step-7/chromium-controls/BUTTON-toggle-dust-embedded.json) | 配对通过 |
| CTL-21 | 电影主视角 | 实际相机位置、目标和 FOV→42；相位不强求相同 | [原页](../../docs/evidence/beach-bottle-boat-step-7/chromium-camera-retest/CAMERA-presets-reference.json) / [内嵌](../../docs/evidence/beach-bottle-boat-step-7/chromium-camera-retest/CAMERA-presets-embedded.json) | 配对通过 |
| CTL-22 | 瓶身侧视角 | 实际相机位置、目标和 FOV→39 | [原页](../../docs/evidence/beach-bottle-boat-step-7/chromium-camera-retest/CAMERA-presets-reference.json) / [内嵌](../../docs/evidence/beach-bottle-boat-step-7/chromium-camera-retest/CAMERA-presets-embedded.json) | 配对通过 |
| CTL-23 | 俯视沙盘 | 实际相机位置、目标和 FOV→44 | [原页](../../docs/evidence/beach-bottle-boat-step-7/chromium-camera-retest/CAMERA-presets-reference.json) / [内嵌](../../docs/evidence/beach-bottle-boat-step-7/chromium-camera-retest/CAMERA-presets-embedded.json) | 配对通过 |
| CTL-24 | 帆船特写 | 实际相机位置、目标和 FOV→36 | [原页](../../docs/evidence/beach-bottle-boat-step-7/chromium-camera-retest/CAMERA-presets-reference.json) / [内嵌](../../docs/evidence/beach-bottle-boat-step-7/chromium-camera-retest/CAMERA-presets-embedded.json) | 配对通过 |
| CTL-25 | 环境全景 | 实际相机位置、目标和 FOV→47 | [原页](../../docs/evidence/beach-bottle-boat-step-7/chromium-camera-retest/CAMERA-presets-reference.json) / [内嵌](../../docs/evidence/beach-bottle-boat-step-7/chromium-camera-retest/CAMERA-presets-embedded.json) | 配对通过 |
| CTL-26 | 放置石头 | 真实沙地点击形成 rock 对象 | [原页](../../docs/evidence/beach-bottle-boat-step-7/chromium-actions/SANDBOX-props-reference.json) / [内嵌](../../docs/evidence/beach-bottle-boat-step-7/chromium-actions/SANDBOX-props-embedded.json) | 配对通过 |
| CTL-27 | 放置贝壳 | 真实沙地点击形成 shell 对象 | [原页](../../docs/evidence/beach-bottle-boat-step-7/chromium-actions/SANDBOX-props-reference.json) / [内嵌](../../docs/evidence/beach-bottle-boat-step-7/chromium-actions/SANDBOX-props-embedded.json) | 配对通过 |
| CTL-28 | 撤销放置 | 撤销最后的 shell，rock 保留 | [原页](../../docs/evidence/beach-bottle-boat-step-7/chromium-actions/SANDBOX-props-reference.json) / [内嵌](../../docs/evidence/beach-bottle-boat-step-7/chromium-actions/SANDBOX-props-embedded.json) | 配对通过 |
| CTL-29 | 恢复装饰 | 用户物件清零，原场景保留 | [原页](../../docs/evidence/beach-bottle-boat-step-7/chromium-actions/SANDBOX-props-reference.json) / [内嵌](../../docs/evidence/beach-bottle-boat-step-7/chromium-actions/SANDBOX-props-embedded.json) | 配对通过 |
| CTL-30 | 暂停/继续 | simTime/水面/船体冻结；绘制/相机继续；恢复推进 | [原页](../../docs/evidence/beach-bottle-boat-step-7/chromium-actions/PLAYBACK-pause-reference.json) / [内嵌](../../docs/evidence/beach-bottle-boat-step-7/chromium-actions/PLAYBACK-pause-embedded.json) | 配对通过 |
| CTL-31 | 重置所有参数 | 多项改变后恢复原默认参数、画质、机位、编辑、装饰及播放 | [原页](../../docs/evidence/beach-bottle-boat-step-7/chromium-actions/PLAYBACK-reset-all-reference.json) / [内嵌](../../docs/evidence/beach-bottle-boat-step-7/chromium-actions/PLAYBACK-reset-all-embedded.json) | 配对通过 |
| CTL-32 | 恢复默认镜头 | 旋转/平移/缩放后原按钮恢复；保存 80 后续帧实际机位，原惯性保留 | [原页](../../docs/evidence/beach-bottle-boat-step-7/chromium-actions/CAMERA-pointer-reset-reference.json) / [内嵌](../../docs/evidence/beach-bottle-boat-step-7/chromium-actions/CAMERA-pointer-reset-embedded.json) | 配对通过；原有差异保留 |
| CTL-33 | 保存 PNG | 桌面及 DPR3 手机实际原按钮 PNG，另有隐藏 UI Enter 导出 | [原页](../../docs/evidence/beach-bottle-boat-step-7/chromium-export-retest/EXPORT-desktop-reference.json) / [内嵌](../../docs/evidence/beach-bottle-boat-step-7/chromium-export-retest/EXPORT-desktop-embedded.json) | 配对通过 |
| CTL-34 | 恢复界面 | 真实原恢复按钮显示 UI，继续操作 | [原页](../../docs/evidence/beach-bottle-boat-step-7/chromium-controls/BUTTON-interface-reference.json) / [内嵌](../../docs/evidence/beach-bottle-boat-step-7/chromium-controls/BUTTON-interface-embedded.json) | 配对通过 |

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
| DYN.waveHeight-0 | 8.015 / 162 | 8.032 / 162 | 配对通过 |
| DYN.waveHeight-50 | 8.032 / 162 | 8.015 / 162 | 配对通过 |
| DYN.waveHeight-100 | 8.015 / 162 | 8.048 / 162 | 配对通过 |
| DYN.direction-0 | 8.049 / 163 | 8.032 / 163 | 配对通过 |
| DYN.direction-90 | 8.016 / 162 | 8.032 / 163 | 配对通过 |
| DYN.direction-180 | 8.049 / 163 | 8.015 / 163 | 配对通过 |
| DYN.direction-270 | 8.032 / 162 | 8.015 / 162 | 配对通过 |
| DYN.boatResponse-0 | 8.032 / 162 | 8.049 / 162 | 配对通过 |
| DYN.boatResponse-100 | 8.015 / 162 | 8.048 / 163 | 配对通过 |
| DYN.boatDamping-0 | 8.048 / 163 | 8.031 / 162 | 配对通过 |
| DYN.boatDamping-100 | 8.014 / 162 | 8.032 / 162 | 配对通过 |
| DYN.wind-0 | 8.032 / 162 | 8.048 / 162 | 配对通过 |
| DYN.wind-100 | 8.015 / 162 | 8.015 / 162 | 配对通过 |
| DYN.waterLevel-0 | 8.015 / 162 | 8.015 / 162 | 配对通过 |
| DYN.waterLevel-100 | 8.032 / 163 | 8.032 / 163 | 配对通过 |
| DYN.strong-water-0 | 8.031 / 162 | 8.015 / 163 | 配对通过 |
| DYN.strong-water-100 | 8.016 / 162 | 8.031 / 162 | 配对通过 |

最短窗口 8.014 sim秒，最少 162 不同绘制帧。零波高振幅/水面高度变化为零；正波高水面及船体自然联动，响应零值的姿态运动显著小于满值。全部样本 GPU 波场时间与原 simTime 一致，有限值检查通过；代表强浪/大风/低高水位中原 containment 标志为真。这只说明采样窗口，不是所有组合不穿模的保证。

[连续原始记录](../evidence/beach-bottle-boat-step-7/chromium-dynamics/browser.json) · [统计与响应对比](../evidence/beach-bottle-boat-step-7/dynamic-analysis.json) · [固定源码公式及响应式时序](../evidence/beach-bottle-boat-step-7/original-physics-responsive-source.json)。

## PNG、画质与浏览器

桌面原按钮在两端实际导出 1440×844 PNG；390×796/DPR3 原画布在两端实际导出 780×1592 PNG，确认 min(DPR,2) 上限。另有隐藏 UI 后保留原截图按钮焦点，用真实 Enter 导出。实际 PNG 均查看，内容为原 WebGL 场景，不含 DOM 控制台和宿主栏。采用 [单独下载复测](../evidence/beach-bottle-boat-step-7/chromium-export-retest/browser.json)，[人工查看记录](../evidence/beach-bottle-boat-step-7/visual-review.json)。

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
