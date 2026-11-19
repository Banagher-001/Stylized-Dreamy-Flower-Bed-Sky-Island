# 卡牌改进 · 第二步验收

第二步完成，日期为 2026-11-18（上海时间）。最终候选为 `card-refinement-step2-e000401dbd3d7074`，仅交付当前工作区修改，没有提交、推送或发布。

[实现](step-2-entrance.md) · [原速演示](evidence/step-2/step-2-entrance-final.mp4) · [采用记录](evidence/step-2/adoption.json) · [第三步交接](step-2-handoff.md)

## 构建与可见效果

严格类型检查及生产构建通过。最终记录绑定 199 个运行输入和 69 个生产文件的 SHA256，详见 [构建记录](evidence/step-2/build.json) 和 [构建日志](evidence/step-2/build-final.txt)。没有增加 npm 依赖。

1652×949 的普通入口按真实浏览器时间播放，实测入场 2365.8ms，恢复原卡槽前后最大边界差为 0px；全程保留 22 张卡的相同实例身份。四张牌都具有持续可见的飞行行程，其中 ComfyUI 和 Blender 实际显示背面转正。

| 卡片 | 可见横向行程 | 可见采样时间跨度 |
| --- | --- | --- |
| Midjourney | 519.6px | 1928.5ms |
| ComfyUI | 956.4px | 1740.3ms |
| 可灵 | 1031.1px | 1651.2ms |
| Blender | 462.6px | 1425.1ms |

上述跨度来自真实浏览器绘制帧的牌面投影采样，非补帧或动画配置推算。[完整数据](evidence/step-2/final-checks/visible-four-card-entrance-data.json) · [原始帧记录](evidence/step-2/final-checks/complete-frames.json) · [原始录像](evidence/step-2/final-checks/video/page@5e266c7a4bdbb249c7ee9a760ad627ba.webm) · [动作采样图](evidence/step-2/final-entrance-contact-sheet.png)。MP4 仅转码兼容播放，没有加速或减速。

## 最终采用的检查

最终构建的 [浏览器报告](evidence/step-2/final-checks/browser.json) 包含下列 13 项，全部通过，无页面错误、请求失败、HTTP 失败或外部资源尝试。

| 检查 | 验证内容 |
| --- | --- |
| visible-four-card-entrance | 四卡可见行程、转面、总时长、原实例、无跳位、停留后自动交接、返回不重播 |
| unseen-fast-pass-can-retry | 未看见即离开时保留机会，返回可完成首次入场 |
| font-change-cleans-flight | 飞行中 200% CSS 字号变化后清理，无页面横向溢出 |
| font-readiness-fallback | 字体持续未就绪时回退到可读内容 |
| step1-region-does-not-follow-flight | 飞前、飞中、飞后输入区域与逻辑宽度保持一致 |
| all-tools-interrupt-first-click | 第一次点击打开全部工具，并清理入场 |
| category-interrupt-first-click | 第一次切换分类生效，不被旧动画回调还原 |
| pause-interrupt-retains-choice | 主动暂停在打断后持续保留 |
| wheel-only-shortens-entrance | 原生滚轮可打断飞入并清理，不将此项当作横移已完成 |
| resize-cleans-flight | 改为 390×844 后清理，卡片无遗留展开和横向溢出 |
| initial-reduced-motion | 初始减少动态使用静态卡排 |
| reduced-during-flight | 飞行中切换减少动态后清理 |
| continue-interrupt-first-click | 第一次点击继续浏览即可到达下一模块 |

另用同一候选完成 [原生后台标签页检查](evidence/step-2/final-native-background/result.json)：外部启动独立 Chromium，使用 CDP `no_defaults=True` 接入，在同一原生窗口切换标签；实际 `document.visibilityState` 变为 hidden 后清理飞行，返回为 visible，仍有 22 张卡，没有重播、入场帧或定时器残留。没有修改可见性属性、时钟或 RAF。脚本为 tests/card-refinement-step-2/native_background.py。

第一步的三项补充回归也通过：[普通入口、桌面区域归属、移动触摸仿真](evidence/step-2/region-regression/browser.json)。该组在最终诊断进度值修正前运行，单独保留，不冒充最终候选的检查；最终候选另有上述区域不变检查，区域及调试模块的源码摘要也与第一步一致。

测试使用 Chromium 155 和软件图形环境。窗口、减少动态及触摸为浏览器仿真；200% 为 CSS 字号仿真。字体就绪故障通过临时强制 FontFaceSet.status 为 loading 注入，并在 finally 恢复。没有将这些结果写成实体手机或多浏览器实测。

## 范围和完整性

相对本步开始基线，142 个源码仅四个允许文件变化，其余 138 个、51 个 public 文件及四项 r3 历史交付文件保持摘要。第一步 93 项文档与证据中，仅目录 README 更新交付进度，其余 92 项未改动。原 wheel handler 逐字一致。[完整性记录](evidence/step-2/integrity.json)

中间尝试原样保留，不作为本次最终采用结果。早期 Playwright 默认焦点模拟不能产生原生后台状态，相应失败记录没有计入通过；最终改用上述独立原生浏览器验证，没有为测试改动产品可见性逻辑。最终构建前还修正了正常完成时的诊断 progress 值，因此使用 final-checks 和 final-native-background 绑定最终候选。

本步只完成入场强化，未修复暂停或分类后的全区域滚轮横移，也未修改第四至七步的交互协调、交接和提示。主场景、Coding 嵌入网页、工具内容、图标及历史压缩包均保留。

测试专用服务与原生测试浏览器已清理，[服务清理记录](evidence/step-2/services-cleanup.json) 只涉及本步启动的两个进程，没有关闭其他服务。
