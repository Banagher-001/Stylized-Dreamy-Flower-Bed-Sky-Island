# 卡牌改进 · 第四步阅读与续播

预览、固定和键盘阅读都能让卡排停在当前牌面。自动开关保存用户的选择，临时停住由当前交互决定。预览或固定时滚轮可以直接换卡，用户选择了暂停时，手动尾段归零。

[原速演示](evidence/step-4/step-4-reading.mp4) · [构建记录](evidence/step-4/build.json) · [采用记录](evidence/step-4/adoption.json)

## 操作和实现

- `createCardTrack.ts` 将自动选择与临时保持分开。实际运动还取决于卡排可见、阅读条件和入场是否结束。最后一个阅读保持解除后，按需等待 180ms，再从原位置缓起约 300ms。显式暂停立即停位。入场后的正常首次展示和手动滚轮尾段使用各自已有的过渡。
- `createToolBrowser.ts` 汇总卡片阅读、按压、键盘焦点、帮助和卡排切换的保持状态。按钮按下时保留真实目标与牌面，原生 click 决定是否固定。拖出、失焦或按压取消均能释放。固定状态下按上一张或下一张，从固定卡向相邻卡切换，正文保持固定。
- `createCardHover.ts` 从当前宽度、倾斜和正文展开进度接入固定态。换一张预览时，A 收回后才展开 B，卡排在交接期间停住。鼠标滚动时解除阅读保持，同一笔合格输入交给第三步的横移入口。尾段完毕后，按至少 2 CSS px 的真实鼠标移动和 120ms 的停留重新建立预览。
- 暂停按钮保留已固定的正文。继续自动展示先收回阅读，再平缓起步。Tab 聚焦牌面及按钮，Esc 收起后焦点仍可用于操作。帮助和固定同时存在时，关闭帮助即回到固定阅读。
- 分类切换会清理旧阅读和惯性。全部工具返回恢复该分类、位置、固定卡和开关。后台切换清理运行中的帧及候选，恢复后以当前可读性和用户选择决定是否移动。

## 实际验证

1652×949 普通入口的第三步基线中，自动开关在悬停时为开启，鼠标按下后变成关闭。最终构建的真实鼠标 `pointerdown`、`pointerup`、`click` 命中同一按钮。预览尚在展开和靠近起始侧的两次测量，按钮边界最大偏差均为 **0 CSS px**，第一次点击成功。 [修改前](evidence/step-4/before/original-preview-press-disables-automatic-data.json) · [实际点击](evidence/step-4/wheel-response/first-native-click-and-wheel-data.json) · [靠边和取消按压](evidence/step-4/final-checks/edge-click-and-abandoned-press-data.json)

| 验收 | 实测 |
| --- | --- |
| 对预览滚一笔 120px | 120.2ms 内观察到超过 8px 的横向位移，页面和镜头稳定 |
| 对固定卡滚一笔 120px | 118.7ms 内观察到超过 8px 的横向位移，固定释放，自动状态继续按原选择 |
| 停止滚动后保持光标 | 尾段后观察约 870ms，卡面保持摘要，之后主动移动才建立新的预览 |
| 自动开启时移开预览 | 解除保持后从原位置缓起，约 361ms 观察到首个超过 0.5px 的位移 |
| 自动暂停时移开预览 | 停在原位，轨道帧和速度归零 |

[预览接管数据](evidence/step-4/wheel-response/wheel-directly-from-preview-data.json) · [悬停停住与恢复](evidence/step-4/final-checks/hover-hold-and-resume-by-choice-data.json) · [新鼠标移动](evidence/step-4/final-checks/wheel-tail-and-fresh-hover-data.json)

最终构建通过 26 项检查。覆盖相邻预览交接、固定卡切换、键盘顺序、操作说明、全部工具返回和分类切换，并回归前几步的入场、滚轮和阅读布局。原生后台测试使用独立 Chromium 的同一窗口切标签页，实测手动尾段清理、显式自动选择保留、固定卡返回后仍可读。 [第四步场景](evidence/step-4/final-checks/browser.json) · [原生后台](evidence/step-4/native-background/result.json) · [滚轮回归](evidence/step-4/wheel-regression/browser.json) · [入场回归](evidence/step-4/entrance-regression/browser.json)

390px 宽的浏览器触控仿真中，一次 144px 的短拖在松手后回到首张，原用例复跑吸附到下一张。卡距为 312px。另用超过半个卡距的手势记录拖动过程，轨道依次推进到 225px，松手后停在 312px，区域外竖向拖动画面前进 200px。两组通过结果和首次短拖记录一并保留。 [触控位移](evidence/step-4/touch-final/native-mobile-gesture-and-snap-data.json) · [短拖复验](evidence/step-4/short-touch-repeat/browser.json)

生产构建使用 `npm run build`。普通验收使用 `tests/card-refinement-step-4/verify.py`，原生标签页使用 `native_visibility.py`。浏览器报告记录构建身份、接收的输入和实际帧。移动触控和减少动态为浏览器仿真。

第五步可在此基础上使用已有的区域判定、当前卡位和临时保持，衔接首尾反馈与退出时机。卡牌读完、用户明确暂停和离场占用都有独立的触发条件。
