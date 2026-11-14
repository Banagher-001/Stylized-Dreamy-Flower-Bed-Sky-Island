# 第三步验收：完整资源保存与独立访问

第三步完成。新增完整原网页、第三方声明、来源说明和真实封面；主站构建及 17 项 HTTP/浏览器检查通过，12 项执行标准均有结果。未添加 Coding 入口或 iframe，未提交、上传或部署。第二步目前仍仅有已细化标准。日期：2026-11-13（Asia/Shanghai）。

| 交付 | 位置 / 结果 |
|---|---|
| 完整网页 | public/experiments/bottle-ocean/index.html，1,979,264 字节，与固定原版一致 |
| 第三方说明 | public/experiments/bottle-ocean/THIRD_PARTY_NOTICES.md，按原字节保存 |
| 来源和运行说明 | public/experiments/bottle-ocean/SOURCE.md |
| 真实封面候选 | src/assets/bottle-ocean-cover.png，1920×1080，复制原截图，无编辑；第四步再引用 |
| 运行入口 | experiments/bottle-ocean/index.html |

原提交 d94c1f911a39143fd8f5efe152b99a87fdc53184；HTML SHA256 为 941feb2ea6ddd3cc93aad5b0b92dbca52ee66a3e1098fee0dbf16f01ca63d1ef。原 HTML 没有重新构建、压缩、替换引擎或注入主站业务。逐文件来源与摘要见 [runtime-manifest.json](../evidence/beach-bottle-boat-step-3/runtime-manifest.json)。

构建与路径：

- 使用现有 npm run build，包含 tsc --noEmit 和 Vite 8.3.5，退出码 0。输出至本步专用临时目录，原 dist 未覆盖。Vite 关于 outDir 位于根目录外且不会清空的提示符合预期；目录由本步独占创建。
- 原仓库、公有目录、生产产物和开发/生产 HTTP 正文的 HTML SHA256 均一致。第三方说明原样保留，SOURCE.md 同样复制到产物。
- 新生产产物共 68 个文件，其中原有 65 个生产文件与现有 dist 对应文件全部字节一致，仅新增 3 个独立资源文件。未引用的封面没有进入主站 bundle。
- 下表为本机验收地址，测试服务已停止，不是当前公网地址：

| 条件 | 当时入口 | 结果 |
|---|---|---|
| 开发 | http://127.0.0.1:45373/experiments/bottle-ocean/index.html | 正确正文、完整默认场景 |
| 生产根路径 | http://127.0.0.1:44855/experiments/bottle-ocean/index.html | 正确正文、完整默认场景及代表操作 |
| 生产子路径 | http://127.0.0.1:44855/portfolio-check/experiments/bottle-ocean/index.html | 实际前缀挂载，正文、刷新、代表操作均通过 |

生产前缀由严格静态服务器实际映射同一份相对 base 构建产物；没有用主页 200 回退代替正确原页。9 个静态文件响应逐份比较正文摘要。测试浏览器使用新上下文、路由禁用缓存及阻断外部 HTTP；外部请求尝试为 0。

实际运行与下载：

- Linux Chromium 155.0.8059.79，WebGL2 使用 ANGLE/Mesa llvmpipe；软件渲染不代表真机或硬件性能。开发/生产根路径为 1280×720、DPR1；前缀原页为 960×600、DPR2。先记录原 fine 默认画面，再通过原画质按钮使用 retro 做代表操作。
- 原场景实际绘制，3 根桅杆、完整地形、海岸、外海、玻璃、天空与灯塔均有对象和画面证据；12 滑杆、22 按钮与第一步一致。
- 原生键盘将波高从 0 改至 100，连续观察自然模拟与水面/船体，未写时钟、dt 或姿态：

| 条件 | 实际模拟秒 | 连续不同模拟帧 | 水面高度峰谷差 | 船体高度峰谷差 |
|---|---:|---:|---:|---:|
| 根路径 | 2.5328 | 52 | 0.201166 | 0.239814 |
| 前缀路径 | 2.5331 | 55 | 0.201085 | 0.239457 |

- 原镜头按钮改变实际相机；原 UI 隐藏后可恢复。根路径通过原点击放置石头和贝壳，并核对真实新增对象、撤销和恢复后的集合。
- 两个入口均通过原截图按钮实际下载 PNG，已查看图像，能辨认瓶、船、水与地形，不是空白或错误帧：

| 条件 | 实际 PNG 尺寸 | 字节数 |
|---|---|---:|
| 根路径 | 1280×720 | 267294 |
| 前缀路径 | 1920×1200 | 221631 |

尺寸符合画布 CSS×min(DPR,2)，导出不含 DOM 面板。证据：[根路径下载](../evidence/beach-bottle-boat-step-3/browser/production-download.png)、[前缀路径下载](../evidence/beach-bottle-boat-step-3/browser/prefix-download.png)。

主站边界与完整性：

- 开发、生产根路径和生产前缀的个人网站均实际浏览到 Coding 区，当前罗森/庭院按钮可用；该阶段没有瓶中海洋网页或封面请求，没有 iframe，也没有主站全局瓶中海洋 API。
- 正常测试无 pageerror、console.error、失败请求或 HTTP 错误。这里只证明静态新增资源没有提前运行，完整主站/罗森内嵌回归仍由后续步骤承担。
- 原仓库 44 文件保持干净，主站 95 项既有生产输入、罗森 46 运行文件、八组旧封存及第一步 253 个封存文件复核通过；第二步标准等既有文档保持原样。
- 本步浏览器关闭，3 个自有服务按 PID/启动时标核对后停止；临时生产文件摘要保存并核对后，删除本步专用临时目录。既有 dist 的 65 个文件全部保持原样。

判定与范围：

[final-summary.json](../evidence/beach-bottle-boat-step-3/final-summary.json) 对照 S3-01 至 S3-12，引用 17 项实际记录。首次运行全部通过，没有删除失败或用旧截图充当本轮证据。原始报告保留；其中 HOST.* 的旧诊断字段 nativeModeToggleUsed 为无条件值，不作为实际点击证明，接受依据是稳定阅读模式、可见可用的 Coding 控件、网络和实例断言；脚本已修正该字段，详见 report-notes.json。

原亮度读数、镜头惯性及图形丢失语义未修改；后台实际 hidden 恢复、真机和硬件性能仍未验证。当前只做 Linux Chromium 代表复核，不扩写为所有浏览器 34 控件或完整 iframe 接入通过。

[构建日志](../evidence/beach-bottle-boat-step-3/build.log) · [HTTP/浏览器报告](../evidence/beach-bottle-boat-step-3/browser/browser.json) · [资源清理](../evidence/beach-bottle-boat-step-3/services-cleanup.json) · [交接说明](step-3-handoff.md)。

本步封存复核：python tests/beach-bottle-boat-step-3/finalize.py --verify-only。此命令只核对本步保存的资料与资源；执行时对现有产品和历史的完整性结论保存在 final-summary.json。
