# 第七步最终验收

第七步已执行完成。候选 `bottle-ocean-step7-3b31ab385ebfc4cb`，日期 2026-11-14（Asia/Shanghai）。已验证范围内完整原功能在个人网站 Coding 区保留，源码与成品两包独立解压、源码重新安装构建及成品运行通过。未提交、推送、部署或发布。

## 实际改动和来源

本步相对第六步 **97 项生产输入全部未变**，无需新增产品修复；更新 README、当前运行指南、对照/交付资料，增加独立验收脚本、证据和仓库外两包。不是回退到 Git HEAD 后重做，也没有重写原 HTML、默认参数、物理或 UI。

主站基提交 `eae15c040aa1527833d844d1bbf81eb551843386`；原仓库提交 `d94c1f911a39143fd8f5efe152b99a87fdc53184`，44 文件保持干净；原成品 1,979,264 字节，SHA256 `941feb2ea6ddd3cc93aad5b0b92dbca52ee66a3e1098fee0dbf16f01ca63d1ef`。原、公有运行副本、生产构建、两包和重建产物摘要一致。Three.js 保持主站 0.187.0 / 瓶中海洋 0.180.0 / 罗森 r160，各自文档运行。

## 执行标准逐项结果

以下“通过”指标准中已定义范围；原问题及未覆盖边界仍保留。

| ID | 结果 | 证据索引 |
|---|---|---|
| S7-01 · 97 项 before、固定原版和 13 组封存保护 | 通过 | baseline / candidate-manifest / protection-final |
| S7-02 · 同引擎/子视口/DPR、原输入与真实就绪 | 通过 | pair-conditions / 每项 conditions |
| S7-03 · 34 控件逐行配对齐全 | 通过 | parity 34 行 / functional-summary.controlLedger |
| S7-04 · 12 滑杆低中高、步进与实际效果 | 通过 | chromium-controls / dynamic-analysis / 原公式 |
| S7-05 · 界面三按钮及原 H/Space/Escape | 通过 | BUTTON.interface / INPUT.keyboard |
| S7-06 · 三画质及内部像素规则 | 通过 | BUTTON.qualities / SLIDER.pixelScale |
| S7-07 · 三环境开关实际关闭/恢复 | 通过 | BUTTON.toggle-* |
| S7-08 · 五机位、恢复、鼠标、拾取 | 通过 | camera-retest / CAMERA.pointer-reset / POINTER.picking |
| S7-09 · 沙盒实体、撤销/恢复/退出与边界 | 通过 | SANDBOX.props / SANDBOX.boundaries |
| S7-10 · 暂停/继续与多状态全部重置 | 通过 | PLAYBACK.pause / PLAYBACK.reset-all |
| S7-11 · 17 条件各端 ≥8 sim秒且 ≥40 绘制帧 | 通过 | chromium-dynamics / dynamic-analysis |
| S7-12 · 水面/GPU/船体有效联动及代表强组合 | 通过 | dynamic-analysis / visual-review；非穷举 |
| S7-13 · 原输入不误控主站，焦点可交接 | 通过 | INPUT.keyboard / PACKAGE.core-flow |
| S7-14 · 手机横竖/320 窄屏/真实模拟手势 | 通过 | chromium-views 三项 + narrow-retest |
| S7-15 · 两匹配尺寸 PNG、DPR>2 与人工查看 | 通过 | chromium-export-retest / EXPORT.hidden / visual-review |
| S7-16 · Firefox/WebKit 新配对代表范围 | 通过 | 两引擎 controls/actions，共 18 配对组 |
| S7-17 · 主站、罗森、庭院、媒体、水潭与导览 | 通过 | package-journey.core-flow；第六步既有回归 |
| S7-18 · 类型/构建、根/子路径、资源/原 SHA | 通过 | build-final / package-journey.prefix / 重建 |
| S7-19 · 当前两包、中文空格解压、源码重建与成品运行 | 通过 | delivery-manifest / package-validation / package-journey |
| S7-20 · 说明、实际映射、历史、封存和自有资源清理 | 通过 | README / run-guide / handoff / cleanup / evidence-manifest |

## 实际测试对象与采用方式

采用 **68 项配对组**：Chromium 50、Firefox 9、Linux WebKit 9；每项均有独立原页和嵌入页结果。Chromium 覆盖全部 34 原控件；17 动态条件共 34 自然运行窗口，最短 8.014 sim秒、最少 162 不同绘制帧。测量四组仅用于条件，不充当原功能配对通过数。

首次镜头前置时序、窄屏原响应式时序和 PNG 文件命名问题全部保留，按单项采用复测，不把含失败报告写成整份全通过。实际说明见 [完整配对表](step-7-parity.md)；采用索引与 34 行两端证据见 [functional-summary.json](../evidence/beach-bottle-boat-step-7/functional-summary.json)。未因此修改原网页或产品代码。

采用配对路径没有 pageerror/console.error、无外部 HTTP 请求尝试。Chromium 保留 allow/allowfullscreen 优先级提示，Firefox 保留软件图形深度纹理过滤与初始布局警告；它们不作为功能失败或零警告承诺。实际请求和事件留在各 browser.json。包内故意请求缺失静态文件返回 404；罗森主动退出时模型请求取消与失败日志按实际记录区分。

## 最终构建和可交付性

实际工具 **Node v24.22.1、npm 11.9.0**；项目要求 Node >=22.12、npm >=10。`npm run build -- --outDir <本步独占目录>` 已包含严格类型检查并成功，生产输出 69 文件。旧 dist 65 文件没有覆盖。97 输入与实际测试构建一一对应。

源码/成品 ZIP 放在独立 `/workspace/deliverables/beach-bottle-boat-step-7/bottle-ocean-step7-3b31ab385ebfc4cb/`。两包均实际解压到全新中文/空格目录，并逐文件核对摘要；源码起初无 node_modules/dist，实际 npm ci、类型/生产构建成功，重建的 69 文件与最终候选逐字节相同。没有使用原依赖目录冒充自包含；允许复用 npm 下载缓存。

实际解压成品通过其自带 Node 预览脚本运行，根路径完整经过：关于我/影像、Coding、原控件与 PNG、罗森原镜头、庭院模式/动效/视频、瓶中海洋档案/独立打开、水潭入口、真正运行的导览中断、子页输入隔离及返回阅读。真实 `/portfolio-check/` 子路径另完成原页、输入、PNG、资源摘要/内容类型、MP4 Range 与严格 404；GLB 由现有预览工具以 application/octet-stream 提供并正常载入。

[生产构建](../evidence/beach-bottle-boat-step-7/build-final.json) · [两包清单](../evidence/beach-bottle-boat-step-7/delivery-manifest.json) · [独立安装/重建](../evidence/beach-bottle-boat-step-7/package-validation.json) · [实际成品根/子路径](../evidence/beach-bottle-boat-step-7/package-journey/browser.json) · [人工图像核对](../evidence/beach-bottle-boat-step-7/visual-review.json)。Windows 脚本已提供并静态检查，未作 Windows 真机执行声明。

## 历史、清理与限制

13 组既有独立封存逐项核对，原仓库 44 文件、罗森 46 运行文件、封面/声明/来源、旧 dist 和旧归档保留。本步 4 个原服务及 2 个解压包预览服务按 PID/启动时刻/命令身份停止，浏览器已关闭，临时构建/解压/新依赖验证目录清理；两个最终包保留在独立交付目录，没有停止其他服务。

第二步历史仍是“只写标准，未单独执行”，实际约定与第五/六步已实现接口在 [交接映射](step-7-handoff.md) 中说明；没有补造第二步验收。

原亮度/标准画质读数、镜头惯性、暂停仍绘制、阻尼名称语义、窄屏取景与响应式初始事件时序均保留。真实 hidden/后台节流、真手机/Windows/Safari/硬件 GPU、创建 RAF 前极快退出、瓶腔拒绝实际命中、物件上限及所有穿模组合未宣称通过。第六步错误、慢加载、真实图形丢失、反复进入与原播放选择等未变代码证据仍明确引用为历史，不充作本步新配对。

独立核对：`python tests/beach-bottle-boat-step-7/finalize.py --verify-only`。核对范围为封存证据/独立副本及交付文件摘要，后续授权修改产品源码不重写本次历史。
