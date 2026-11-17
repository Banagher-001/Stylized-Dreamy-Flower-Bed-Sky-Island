# 关于我改版 · 第十二步验收

完成：2026-11-17T14:25:16.777510+08:00（Asia/Shanghai）。第十二步完成，未提交、推送或发布。

[实现说明](step-12-guidance.md) · [第十三步交接](step-12-handoff.md) · [9.84 秒主站录像](evidence/step-12/step-12-guidance.mp4)

## 最终结果

**189 项最终检查通过**，`npm run build`（包含类型检查）与 `git diff --check` 通过。所有采纳结果匹配最终 build-6 的源码、构建与组件载荷 SHA256，未混用早期版本。

| 范围 | 通过数 | 记录 |
| --- | ---: | --- |
| 说明组件：状态、暂停组合、焦点、首次操作、输入与生命周期 | 24 | accepted-guidance-components |
| 真实主站：上述场景、入场/导览/章节、手机、大字与录像 | 32 | accepted-guidance-main |
| 第十一步飞离、折返、固定与返回操作回归 | 51 | accepted-departure-components / main |
| 第十步全文详情、键盘与恢复回归 | 49 | accepted-detail-components / main |
| 滚轮速度、方向、首事件、按钮和时钟 | 15 | accepted-wheel |
| 22 张及五张分类的双向整圈 | 2 | accepted-cycle-final |
| 阴影牌面内区像素检查 | 1 | accepted-shadow |
| 原有影像、罗森、漂流瓶、环境与章节导览 | 7 | accepted-existing |
| 宽屏、手机、首末详情和大字投影 | 8 | accepted-projection |

[逐项采纳清单](evidence/step-12/adoption.json) · [源码冻结](evidence/step-12/source-freeze.json)

## 布局与操作实测

- 1440×900 主站保持沉浸模式。打开说明前后，工具浏览器高度均为 **494 px**、控制栏高度均为 **62 px**、轨道高度均为 **380 px**；没有挤动卡排。
- 面板宽 **360 px**，内部滚动到 **135 px** 时页面位置保持 **3006 px**，卡排相位也不变。PageDown 只滚动说明，标题和关闭入口保持可见。
- 自动选择在打开、关闭说明前后均保持 true，临时停帧后恢复；原先暂停则保持暂停。临时预览收起后仍由说明持有暂停，关闭只释放自己的持有。
- 首次外部分类、自动按钮、卡片按钮和返回途中说明入口点击有效。固定阅读打开说明后保留全文，第一次 Escape 只关闭说明，第二次可收起固定内容。
- 悬停四角倾斜时，控制文字和说明列表的文本/子节点变更为 **0 次**，节点身份保持。提示与 aria-describedby 指向同一实际可见文案，自动计数不连续播报。
- 390 px 触摸仿真中内联说明宽 **358 px**，正文 **16 px**，关闭按钮高 **44 px**。320 px、200% 大字、稳定宽屏及 1920 宽屏也通过，没有页面横向溢出。
- 触控板横向交接后说明改为原生横向浏览，重新开启程序展示后恢复滚轮说明。模拟混合设备触摸时，浏览条目为“浏览卡片：左右滑动卡片，或使用上一张、下一张浏览。”，返回提示为“正在返回原浏览位置”。

## 视觉留档

[默认桌面](evidence/step-12/final-desktop-default.png) · [桌面说明](evidence/step-12/final-desktop-help.png) · [说明内部滚动](evidence/step-12/final-desktop-help-scrolled.png) · [固定阅读与说明](evidence/step-12/final-desktop-fixed-help.png)

[390 px 触摸](evidence/step-12/accepted-guidance-main/native-390-open.png) · [320 px 触摸](evidence/step-12/accepted-guidance-main/native-320-open.png) · [200% 大字](evidence/step-12/accepted-guidance-main/native-large-open.png)

## 开发诊断与验证边界

初版 48 项说明与 133 项回归均通过。补查发现，混合设备在程序横排已绑定时，最近触摸输入仍可能沿用滚轮、移入或移开文案。修正仅在 toolGuidance 的触摸分支，诊断前后记录与 build-5 原文件均保留；最终 build-6 增加相应检查并重新执行全部 189 项。

循环检查保留了一次旧断言的掉帧误判及定位数据：83 ms 的延迟内卡片实际前进 43.14 px，下一次采样已有 7.05 px 阴影自然进入，正面仍在画面外。最终检查改按实际位移限定入画量，并扩大到十面与三倍模糊半径；运动源码未修改。见 [采样定位](evidence/step-12/cycle-sampling-diagnosis.json)。

浏览器 Chromium 155.0.8059.79。点击、滚轮、键盘与触摸仿真通过浏览器输入执行，页面定位使用真实 scrollTo 路径；组件通过实际宿主接口提供上下文。混合设备指针及后台等生命周期模拟明确标记，未作为实体手机或辅助软件实测。未修改动画时钟，未做其他浏览器验收。

截图追加录制仅用于视觉留档，不重复计入检查数量。录像未经加速，固定世界画面方便观察卡片与说明；旧功能中的世界时间、鸟、水球和作品交互另用既有回归核对。

## 保护与交付

本步修改 5 个相关源文件，新增 toolGuidance.ts、createToolHelp.ts、toolHelp.css。content.ts、22 张图标、其余 **72 个基线源文件**与 **6101 个历史档案**保持，见 [保护核对](evidence/step-12/protection-final.json)。没有重写三维运动、场景、相机或嵌入作品。

测试浏览器、专用静态服务与 Xvfb 已关闭，见 [清理记录](evidence/step-12/services-cleanup.json)。HEAD 和本地 origin/main 仍为 `823da097c4a945f406ef266362822c2626e9251f`，暂存区为空。代码保存在工作区，运行 `npm run dev` 查看。

第十三步系统适配与第十四步整体验收仍待后续指示。
