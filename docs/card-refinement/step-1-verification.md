# 卡牌改进 · 第一步验收

第一步完成，2026-11-18T13:28:39.491823+08:00（上海时间）。交付统一区域、只读输入归属、调试边界及下一步合同。本步不改变飞入、实际横移或自动播放；没有提交、推送或发布。

[合同](step-1-contract.md) · [实现交接](step-1-handoff.md) · [采用记录](evidence/step-1/adoption.json)

## 基线与代码

基线提交 13ce33c0bc2e47c91efee9a85deaf34741158296。保存 140 个原源码与 51 个公共文件摘要，仅复制八个相关源码，另保存截图同等尺寸 1652×949 的 G6 暂停状态。新增两个模块，现有文件仅 createToolBrowser.ts 增加 12 行接点。其余 139 个原源码、51 个公共文件和四项 r3 原交付文件保持 SHA256。原 wheel handler 逐字一致。

[基线](evidence/step-1/baseline.json) · [原界面截图](evidence/step-1/baseline-view/before-region-change-postproduction-paused.png) · [完整性核对](evidence/step-1/integrity.json)

严格类型检查与生产构建通过，当前 142 个源码、69 个输出文件身份见 [构建记录](evidence/step-1/build.json) 与 [日志](evidence/step-1/build.txt)。没有增加 npm 依赖。

## 实际采用的浏览器检查

| 场景 | 记录 |
| --- | --- |
| normal-page-unchanged | [通过](evidence/step-1/checks-1/browser.json) |
| stable-resize-and-large-text | [通过](evidence/step-1/checks-1/browser.json) |
| native-mobile-gestures | [通过](evidence/step-1/checks-1/browser.json) |
| desktop-region-and-ownership | [通过](evidence/step-1/checks-4/browser.json) |
| native-selection-and-keyboard | [通过](evidence/step-1/checks-5/browser.json) |

采用五组实际检查：普通 URL 没有诊断层，分类、暂停和鼠标展开仍可用；桌面牌面、间隙、左右留白均归 cards，G6 暂停不影响资格；固定和悬停不改变逻辑宽度；G3 全部放下归 page；浏览器组合手势、分类与导航、帮助和全文弹层、关闭返回、离屏按合同判定。

另覆盖稳定阅读、1100×850 窗口变化、200% CSS 字号仿真，以及 390×844 的原生触摸仿真。横向拖动实际改变卡排 scrollLeft，区域外竖向拖动实际改变页面 scrollY。真实鼠标拖选得到文字，原生 Tab 焦点避开 inert / aria-hidden 的诊断层。

[桌面边界与固定状态](evidence/step-1/checks-4/desktop-pinned-region.png) · [大字稳定阅读](evidence/step-1/checks-1/stable-large-text-region.png) · [手机触控](evidence/step-1/checks-1/native-mobile-gestures.png)

检查使用 Chromium、真实浏览器帧和输入，未替换时钟或 RAF。字号和触摸结果为仿真，不代表实体手机实测。修订后的可复用脚本为 tests/card-refinement-step-1/verify.py，使用 --origin 与新的 --out 目录；云图形环境可另传 --env-file。

## 中间记录与范围

中间尝试原样保留。分类按钮选择器需要限定 button，避免同时匹配根容器的 data-category；弹层关闭与诊断显示异步，应等实际绘制帧更新。一次移动预览后的鼠标激活未建立预期固定状态，最终固定归属场景采用原生 Enter 建立状态，普通入口鼠标展开另验。没有将悬停中的点击时序写成已修复。

本步只核对建议归属，不宣称暂停分类后的滚轮缺口已修复。新的轮控接入在第三步，飞入强化在第二步，交互协调在第四步。没有重跑原十四步或改写其旧证据。

调试入口为 /?debug=1。绿／灰／黄虚线与左下文字明确标注“只读，不接管输入”。普通入口没有新增诊断节点或监听，原卡片样式与布局保持。

本步专用服务结束后，清理结果见 [服务清理](evidence/step-1/services-cleanup.json)。
