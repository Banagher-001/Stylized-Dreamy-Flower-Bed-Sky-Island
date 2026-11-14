# 第一步：原有问题、原语义与验证边界

这些观测来自独立原页面，尚未嵌入个人网站。本步没有修复原成品。

| ID | 类型 | 实际观测 | 后续接入含义 |
|---|---|---|---|
| O-01 | 原页已有问题 | 初始 brightness 状态和文字为 0.82，原生 range 值为 0.8；步进为 0.05，声明默认值未对齐。12 个滑杆的低中高和键盘输入均能正常生效 | 保留原版默认；以后对照时分别看 DOM、文字和场景状态，不把原差异误报为 iframe 回归 |
| O-02 | 原页已有问题 | WebGL 上下文真实丢失后，ready 仍为 true，__bottleError 仍为 null；loader-error 有错误文字，但父 loader 的内联 display:none 没有恢复。刷新后恢复正常 | 宿主必须观察当前 canvas 的 contextlost 等实际故障，不能仅依赖 ready 或错误遮罩可见性；重试需创建新文档 |
| O-03 | 原页已有问题 | 原镜头预设/恢复会受到地面约束和 OrbitControls 剩余惯性影响。旋转后立即恢复，80 个后续渲染帧后仍偏离声明的 cinema 坐标，标签依然为 cinema | 对照实际相机、目标与视图；不把标签当作精确到位证明，不用直接写相机或 API 复位掩盖原行为 |
| S-01 | 原读数精度 | standard 画质实际 scale=2.85，range 和单小数读数为 2.9；实际色阶为 26，1024×768 时离屏尺寸 359×269 | 这是原档位/步进与显示精度的区别，不能为追求四者相同改原画质 |
| S-02 | 原播放语义 | 暂停冻结 simTime、水面和船体，但 RAF、相机与绘制继续。减少动态偏好缩短 CSS 动画，3D 模拟仍继续 | 后续关闭现场必须卸载实例，不能仅点暂停后声称释放图形资源 |
| S-03 | 原截图规则 | PNG 只复制 WebGL 场景，不含 DOM 面板。尺寸为画布 CSS 尺寸×min(DPR,2)。已实测 1920×1080/DPR1 和 960×600/DPR3→1920×1200 | README/旧 QA 的 1920×1080 不是固定输出承诺；内嵌对照按子文档画布实际大小计算 |
| S-04 | 原阻尼语义 | boatDamping 增大时，源码的垂直阻尼比由 0.82 降至 0.26，角阻尼比由 0.9 降至 0.32。真实轨迹已记录 | 不根据名称推断“越大越稳”，不擅自反转滑杆 |
| S-05 | 原编辑规则 | 编辑射线排除外海对象，命中的是可放置地形/不透明物。代表瓶中、外海和天空点击未新增物件；瓶中代表点实际命中瓶后方、超出放置范围的地形 | 不把“视觉点在瓶中”当成射线点位于瓶腔。真正瓶腔拒绝分支有源码依据，但本轮没有取得该分支的原生点击命中，不冒充已覆盖所有边界 |
| S-06 | 原手机构图 | 390×844 手机模拟中，面板默认折叠，展开、滚动、横竖屏和触摸可用；默认电影镜头下瓶身部分超出窄画幅 | 保留原相机与可操作镜头；不把原竖屏取景归因于后续大尺寸查看器，也不声称竖屏一屏展示全部景物 |

对应原始证据：

- O-01、S-01：[controls/browser.json](../evidence/beach-bottle-boat-step-1/controls/browser.json)，UI.default-inventory、BUTTON.quality。
- O-02：[failures/browser.json](../evidence/beach-bottle-boat-step-1/failures/browser.json)，FAILURE.context-loss-reload；包含真实且 trusted 的 canvas 事件。
- O-03、S-05：[boundaries/browser.json](../evidence/beach-bottle-boat-step-1/boundaries/browser.json)，CAMERA.reset-inertia、SANDBOX.representative-rules。
- S-02：[interactions/browser.json](../evidence/beach-bottle-boat-step-1/interactions/browser.json) 和 [failures/browser.json](../evidence/beach-bottle-boat-step-1/failures/browser.json)。
- S-03：[真实场景 PNG](../evidence/beach-bottle-boat-step-1/interactions/export-1920x1080-ui-visible.png)、[DPR 上限 PNG](../evidence/beach-bottle-boat-step-1/interactions/export-960x600-dpr3-capped2.png)、[隐藏 UI 后键盘导出](../evidence/beach-bottle-boat-step-1/boundaries/hidden-ui-native-keyboard-export.png)。
- S-04：physics/boatDamping-0.json、boatDamping-100.json 的连续样本；没有作同相位逐点比较或单调性承诺。
- S-06：[手机原页截图](../evidence/beach-bottle-boat-step-1/chromium-mobile-file-retest/phone-default-390x844.png)。

环境限制与尚未验证的范围：

| ID | 条件 | 本轮结论 |
|---|---|---|
| L-01 | 云端受管 Chromium 的 file:// | 导航返回 ERR_BLOCKED_BY_ADMINISTRATOR，未绕过策略。该引擎的文件直开未验证；Firefox 153 的原文件直开通过；HTTP 三引擎代表路径通过 |
| L-02 | 实际后台 hidden 状态 | Playwright 页面切换及独立 X11 浏览器 Ctrl+T/Ctrl+W 尝试均未使被测页报告 hidden，未出现 visibilitychange。因此隐藏后恢复、后台资源节流未验证；没有覆写 document.hidden 或派发假事件 |
| L-03 | 真机与平台 | 本轮为 Linux 桌面浏览器及 Chromium 触摸/手机模拟；未验证真手机、iOS Safari、macOS Safari、Windows 或硬件 GPU 性能 |
| L-04 | 穷举边界 | 不覆盖所有参数组合、全部地形像素、放置上限、所有穿模条件、所有浏览器的全部 34 控件；代表安全遥测不等于绝不穿模证明 |
| L-05 | 个人网站内嵌 | 本步未接入；滚轮隔离、宿主焦点/阅读恢复、资源回收、主站与罗森回归仍属于后续步骤 |

过程中的测试问题与复测均保留：灯塔点选最初受控制面板遮挡，隐藏 UI 后真实点选通过；风力为 0 的测试最初误要求惯性漂移立即精确归零，改为记录自然衰减后复测通过；手机测试最初未先展开折叠面板，修正顺序后通过。首次失败没有删除或改写，也没有修改原产品来通过测试。
