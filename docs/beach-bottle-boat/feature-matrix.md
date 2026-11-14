# 第一步：34 个原控件与操作基线

原生输入后核对原状态、场景对象、相机、连续模拟或实际下载。主功能在 Chromium 独立 HTTP 页面验证；完整逐项记录见 [验收报告](step-1-verification.md) 和 [机器汇总](../evidence/beach-bottle-boat-step-1/final-summary.json)。

12 个滑杆与 22 个按钮共 34 个 DOM 控件。下表每行对应一个控件；分组测试 ID 可覆盖多个同类按钮，不重复计算为新控件。

| 控件 ID | DOM / 原功能 | 实际对应记录 | 判定 |
|---|---|---|---|
| CTL-01 | #panel-toggle · 收起 / 展开控制面板 | BUTTON.panel | 通过 |
| CTL-02 | action=toggleUI · 隐藏界面 / H | BUTTON.ui-hide-restore | 通过 |
| CTL-03 | #waveHeight · waveHeight | SLIDER.waveHeight | 通过 |
| CTL-04 | #waveSpeed · waveSpeed | SLIDER.waveSpeed | 通过 |
| CTL-05 | #waveDensity · waveDensity | SLIDER.waveDensity | 通过 |
| CTL-06 | #waveDirection · waveDirection | SLIDER.waveDirection | 通过 |
| CTL-07 | #waterLevel · waterLevel | SLIDER.waterLevel | 通过 |
| CTL-08 | #boatResponse · boatResponse | SLIDER.boatResponse | 通过 |
| CTL-09 | #boatDamping · boatDamping | SLIDER.boatDamping | 通过 |
| CTL-10 | #wind · wind | SLIDER.wind | 通过 |
| CTL-11 | quality=fine · 精致 | BUTTON.quality | 通过 |
| CTL-12 | quality=standard · 标准 | BUTTON.quality | 通过 |
| CTL-13 | quality=retro · 复古 | BUTTON.quality | 通过 |
| CTL-14 | #pixelScale · pixelScale | SLIDER.pixelScale | 通过 |
| CTL-15 | #sunset · sunset | SLIDER.sunset | 通过 |
| CTL-16 | #brightness · brightness | SLIDER.brightness | 原页已有问题（默认读数）；输入通过 |
| CTL-17 | #glassOpacity · glassOpacity | SLIDER.glassOpacity | 通过 |
| CTL-18 | toggle=lighthouse · 灯塔灯光 | BUTTON.toggle-lighthouse | 通过 |
| CTL-19 | toggle=spray · 浪花效果 | BUTTON.toggle-spray | 通过 |
| CTL-20 | toggle=dust · 沙尘粒子 | BUTTON.toggle-dust | 通过 |
| CTL-21 | preset=cinema · 01 / CINEMA电影主视角 | CAMERA.five-presets | 通过 |
| CTL-22 | preset=side · 02 / BOTTLE瓶身侧视角 | CAMERA.five-presets | 通过 |
| CTL-23 | preset=top · 03 / OVERHEAD俯视沙盘 | CAMERA.five-presets | 通过 |
| CTL-24 | preset=closeup · 04 / SHIP帆船特写 | CAMERA.five-presets | 通过 |
| CTL-25 | preset=panorama · 05 / PANORAMA环境全景 | CAMERA.five-presets | 通过 |
| CTL-26 | edit=rock · 放置石头 | SANDBOX.real-props | 通过 |
| CTL-27 | edit=shell · 放置贝壳 | SANDBOX.real-props | 通过 |
| CTL-28 | action=undoProp · 撤销放置 | SANDBOX.real-props | 通过 |
| CTL-29 | action=resetProps · 恢复装饰 | SANDBOX.real-props | 通过 |
| CTL-30 | #pause-button · 暂停模拟 | PLAYBACK.freeze-resume | 通过 |
| CTL-31 | action=reset · 重置所有参数 | PLAYBACK.full-reset | 通过 |
| CTL-32 | action=resetCamera · 恢复默认镜头 | CAMERA.pointer-reset / CAMERA.reset-inertia | 原页已有问题（残余惯性）；操作通过 |
| CTL-33 | action=screenshot · 保存当前截图 | EXPORT.native-download | 通过 |
| CTL-34 | #restore-ui · 显示界面 (H) | BUTTON.ui-hide-restore | 通过 |

按钮与滑杆的更多实际效果：

| 组 | 原操作与实际证据 |
|---|---|
| 12 滑杆 | 各低/中/高、原生方向键步进、原按钮恢复；波场振幅/频率/方向/水位、后处理尺寸/曝光、灯色、玻璃透明度与风均读取实际对象。船体响应/阻尼另有连续轨迹 |
| 画质 | fine / standard / retro 实际 scale=2 / 2.85 / 3.8，levels=48 / 26 / 12；standard 滑杆取整区别单列 |
| 环境开关 | 灯塔、浪花、沙尘实际对象关闭并恢复；画面灯塔拾取也实测 |
| 镜头 | 五原预设、左旋右移滚轮、瓶/地形双击、灯塔单/双击；镜头恢复后的原惯性单列 |
| 沙盒 | 石头/贝壳由原画布点击新增真实对象；撤销末次、再放置、恢复；拖动和非编辑点击没有新增；Escape 退出 |
| 播放/重置 | 暂停模拟冻结而绘制继续，相机可操作；继续推进。原总重置恢复 12 参数、画质、机位、编辑、用户装饰与播放状态 |
| 下载 | 原截图按钮实际 PNG 下载；隐藏 UI 后保留焦点的原按钮也可由真实 Enter 激活；尺寸按原规则，场景不含 DOM 面板 |

其他必验操作：

| 记录 ID | 范围与结果 |
|---|---|
| KEYBOARD.original | H/Space/Escape；输入焦点保护、按钮 Space 原生激活均通过 |
| MOTION.height-0/50/100 | 每档 ≥8 实际 simTime 秒、≥40 不同渲染帧；水面和船体连续联动通过 |
| MOTION.directions | 0/90/180/270 原方向向量和连续姿态均已保存 |
| MOTION.boatResponse/boatDamping/wind | 原生 UI 0/100 与真实轨迹；风力零值保留自然衰减，不强制归零 |
| MOTION.strong-water-safety | 强浪、水位 0/100、风力 100 代表组合数值有效，原安全检查为真；非穷举 |
| ENGINE.representative | Chromium、Firefox、Linux WebKit 的加载、滑杆、镜头、界面和 PNG 代表路径通过 |
| VIEW.mobile-touch | 390×844 与 844×390，原生触摸点按、单指旋转、双指缩放，面板可折叠展开与滚动；手机模拟，不是真机 |
| LOAD.file-cold | Firefox 原文件冷启动通过；受管 Chromium 策略阻止，记设备/浏览器限制 |
| FAILURE.webgl-disabled | 真正禁用 WebGL 后 ready=false、原错误界面显示，通过故障基线 |
| FAILURE.context-loss-reload | 真实 contextlost 及刷新恢复已记录；原 ready/错误遮罩缺陷单列 |
| LIFECYCLE.reduced-motion | 实际匹配减少动态偏好，CSS 动画缩短，3D 继续；原语义已记录 |
| LIFECYCLE.native-tab-visibility | 实际标签切换尝试没有观察到 hidden；后台恢复/节流未验证，不计通过 |

原问题、文档差异及未覆盖边界见 [original-issues.md](original-issues.md)。所有记录只针对独立原页；内嵌保留性仍需后续对照。
