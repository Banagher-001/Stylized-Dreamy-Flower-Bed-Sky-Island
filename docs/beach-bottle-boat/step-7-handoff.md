# 第七步交付：瓶中海洋完整接入

本轮七步接入在已验证范围内完成。候选 **bottle-ocean-step7-3b31ab385ebfc4cb**，日期 2026-11-14（Asia/Shanghai）。当前 Coding 为 LAWSON → BOTTLE OCEAN → COURTYARD，默认罗森；瓶中海洋现场运行完整原网页，档案/独立打开/返回阅读保留，水潭入口仍是庭院。

本轮未提交、推送、部署或发布；工作区包含此前未提交成果，基提交 `eae15c040aa1527833d844d1bbf81eb551843386` 不能单独代表本次成品。产品以本步 candidate-manifest 的 97 输入和 69 产出为准。本步无新增产品修改，README/资料与交付文件已整理。

## 当前可下载文件

两个 ZIP 均在仓库外保留，没有塞入 Git 或冒充已上传。完整解压后使用 HTTP，不能仅双击 index.html。

| 包 | 大小 | 实际验证 |
|---|---:|---|
| [成品 ZIP](/workspace/deliverables/beach-bottle-boat-step-7/bottle-ocean-step7-3b31ab385ebfc4cb/bottle-ocean-step7-3b31ab385ebfc4cb-site.zip) | 6,950,380 字节（约 6.63 MiB） | 自带无 npm 依赖 Node HTTP 预览；根/子路径实际运行 |
| [源码 ZIP](/workspace/deliverables/beach-bottle-boat-step-7/bottle-ocean-step7-3b31ab385ebfc4cb/bottle-ocean-step7-3b31ab385ebfc4cb-source.zip) | 7,025,391 字节（约 6.70 MiB） | 独立 npm ci/类型/构建，69 产出逐字节一致 |

- `bottle-ocean-step7-3b31ab385ebfc4cb-site.zip`
  SHA256：`deab7323b2572b244558a7fa49d6ba978b56e4cf7feb822ea2e742954a09b522`
- `bottle-ocean-step7-3b31ab385ebfc4cb-source.zip`
  SHA256：`3431d977b59fc56eb13ed98116ec76b551e87a4daa92fd3f02c967060febd438`

[逐文件清单](/workspace/deliverables/beach-bottle-boat-step-7/bottle-ocean-step7-3b31ab385ebfc4cb/manifest.json) · [SHA256SUMS](/workspace/deliverables/beach-bottle-boat-step-7/bottle-ocean-step7-3b31ab385ebfc4cb/SHA256SUMS) · [运行指南](step-7-run-guide.md) · [完整配对表](step-7-parity.md) · [最终验收](step-7-verification.md)。

成品完整解压后，安装 Node.js LTS 24，Windows 可双击 START-PREVIEW.cmd；其他平台运行 `node scripts/preview-site.mjs --open`，无需 npm ci。源码使用 `npm ci`、`npm run dev`；PowerShell 对应 `npm.cmd ci`、`npm.cmd run dev`。源码包保留重建必要文件和指南，不包含完整 Git 历史、所有测试证据或旧大型归档。localhost 仅在自己电脑有效，公开访问仍需后续静态部署。

## 来源与保持

原仓库 [Beach-Bottle-Boat](https://github.com/Banagher-001/Beach-Bottle-Boat)，固定提交 `d94c1f911a39143fd8f5efe152b99a87fdc53184`。原成品 1,979,264 字节，SHA256 `941feb2ea6ddd3cc93aad5b0b92dbca52ee66a3e1098fee0dbf16f01ca63d1ef`。运行副本 `public/experiments/bottle-ocean/index.html` 与原 HTML 字节相同；SOURCE.md、THIRD_PARTY_NOTICES.md 随源/成品保留。运行不请求 GitHub、私有仓库或外部 CDN。

主站 Three.js 0.187.0、瓶中海洋 0.180.0、罗森 r160 各自保持。原仓库 44 文件、罗森 46 运行文件、既有 13 封存和旧 dist 65 文件保留。当前封面、来源和文件摘要见 [候选清单](../evidence/beach-bottle-boat-step-7/candidate-manifest.json)。

## 第二步约定与实际接口映射

第二步当时只细化了标准，没有单独执行或架构验收文件；该事实不改写。下面是最终代码的实际映射，主要落地于第五步，第六步修复运行后异常文档替换。不是第二步的补写历史。

| 约定 | 实际所有者和接口 | 已有/本次证据 |
|---|---|---|
| 作品身份/同源完整入口 | projectContent 的 bottle-ocean、embedded-page、resolveProjectEntry/BASE_URL；独立打开共用入口 | 第四步；本步实际包根/子路径 |
| 通用文档生命周期 | createEmbeddedPageExperience(options,profile)；options=container/entry/wanted/status；返回 mount/retry/unmount/dispose | 第五/六步；本步新配对进出 |
| 作品专用只读识别 | createBottleOceanExperience；profile=title/canvasSelector/readyEvent/inspect；当前 API+canvas+首帧+loader+错误组合 | 第六步 ISOLATION.documents / FAULT.*；本步 BASE.inventory |
| 状态表 | viewer 的 prepared，容器的 loading/12秒 slow/ready/error；状态带实例、当前文档归属 | 第六步 FAULT.slow/FAULT.responses/NAV.* |
| 图形丢失与陈旧 ready | 当前 canvas 真实 lost/restored 锁故障，直到新文档/重试；不信旧 ready | 第六步 FAULT.child-graphics；本步代码未变 |
| 防过期/文档替换 | generation/documentGeneration/owns；替换先释放旧监听，运行后 blank 或异常 URL 为 error | 第六步 NAV.child-blank/NAV.paths / LIFE.pending |
| 卸载/重试/最多一个实例 | 先失效代号、清 RAF/timer/AbortController/文档引用，再移除 iframe；重试建立新文档 | 第六步 LIFE.cycles、LIFE.pending；本步关闭均为零 iframe |
| 原输入/下载 | iframe 原控制台/原处理器；无跨文档键盘转发或原业务注入 | 本步 34 控件、INPUT.keyboard/VIEW.phone/EXPORT.* |
| 大尺寸/原取景 | projectHost.css 按独立网页类型复用，iframe 填满工具栏外区域，不固定 16:9/transform | 本步先测子尺寸再配对；实际 PNG |
| 阅读/焦点/播放/导览 | startTourPrototype 的 beginOverlay/closeOverlay、covered/syncLoop；viewer 关闭恢复有效触发点 | 第六步 RESOURCE.return、LAYOUT.resize；本步 PACKAGE.core-flow |
| 罗森/庭院/媒体 | 原各自 profile 与既有资源所有者，退出旧现场才进入新现场 | 本步成品罗森原镜头、庭院模式/视频、水潭、影像 |
| 普通标签/真实 hidden | 原实例保留和回来复核；实际 hidden 没有观察成功，不冒充后台验收 | 第六步 VISIBILITY.return 环境限制保留 |

对应第二步 S2-01～15：正常识别→BASE.inventory/ISOLATION.documents；慢载入→FAULT.slow；失败/重试→FAULT.responses/FAULT.child-init；丢失/恢复→FAULT.child-graphics；关闭/旧回调→LIFE.pending；重复/重载/切作品→LIFE.cycles/NAV.paths；现场档案→LIFE.cycles；庭院/媒体→PACKAGE.core-flow；原输入→本步 INPUT/EXPORT；阅读/播放→RESOURCE.return；尺寸/字体→LAYOUT.sizes/resize；标签→VISIBILITY.return（真实 hidden 限制）；主站故障不禁用独立作品→FAULT.host-init/FAULT.parent-graphics。故障与压力记录明确来自[第六步](step-6-verification.md)，未重称本步新通过。

## 结果、边界与后续保存

本步 68 配对组（Chromium50/Firefox9/WebKit9）、全部34原控件、17连续动态条件通过；真实成品另有根/子路径2条流程，源码从全新目录安装构建与原69产出一致。两包、记录和启动指南已可取走。首次失败和证据命名问题留档，复测采用方式见对照/验收。

原亮度精度、标准画质读数、镜头惯性、阻尼语义、暂停仍绘制、手机取景和面板入口事件时序保留。真实后台 hidden、真手机/Windows/Safari/硬件性能、创建前极快退出、瓶腔拒绝实际命中与全部穿模/物件上限没有验证承诺。

只停止本步自有服务与浏览器，临时构建和中文解压/依赖验证目录清理；交付目录与历史资料保留。新封存只包含证据与独立快照，不冻结未来可授权修改的产品/README 路径。核对命令：`python tests/beach-bottle-boat-step-7/finalize.py --verify-only`。

之后用户如要求保存 GitHub，再将本轮实际源码/必要文档与证据按仓库规范提交，并单列大文件取舍；当前没有自动执行该动作。后续公开部署是另一个明确操作，不把本机预览地址交给他人当公网网址。
