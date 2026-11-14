# 第一步：原版文件与版本清单

日期：2026-11-13（Asia/Shanghai）。来源为用户提供的 [Beach-Bottle-Boat 仓库](https://github.com/Banagher-001/Beach-Bottle-Boat)，本步独立运行已有成品，没有重构建。

| 项目 | 固定值 |
|---|---|
| 原仓库位置 | /workspace/Beach-Bottle-Boat |
| 原提交 | d94c1f911a39143fd8f5efe152b99a87fdc53184 |
| 主站位置 | /workspace/Stylized-Dreamy-Flower-Bed-Sky-Island |
| 主站提交 | eae15c040aa1527833d844d1bbf81eb551843386 |
| 原运行入口 | index.html；bottle_ocean_sandbox.html 为字节相同的别名 |
| 单份成品大小 | 1,979,264 字节 |
| 成品 SHA256 | 941feb2ea6ddd3cc93aad5b0b92dbca52ee66a3e1098fee0dbf16f01ca63d1ef |
| 原源文件总数 | 44，不含 .git |

完整逐文件路径、字节数和 SHA256 见 [baseline.json](../evidence/beach-bottle-boat-step-1/baseline.json) 的 originalFiles；两个成品一致，不必为了运行同时复制两份。

| 分类 | 文件 | 用途与本步处理 |
|---|---|---|
| 运行成品 | index.html、bottle_ocean_sandbox.html | 自包含 HTML；内联 Three.js、界面、场景、着色器及生成资源。通过原字节运行 |
| 第三方说明 | THIRD_PARTY_NOTICES.md | 列出 Three.js MIT 声明、esbuild MIT、Playwright Apache-2.0；后续保存独立作品时随来源说明保留 |
| 构建输入 | src/index.template.html、src/main.js | 原页面模板和启动/状态/交互主逻辑；只读 |
| 原世界 | src/world.js | 完整沙地、外海、天空、灯塔、装饰、粒子及环境交互；本轮运行的是完整世界 |
| 原开发替代 | src/world-stub.js | 开发用替代世界；未使用、未重构建 |
| 场景与模拟 | src/bottle.js、boat.js、water.js、waves.js | 玻璃瓶、三桅船、瓶内水面、CPU/GPU 共用解析波场；只读 |
| 渲染与输入 | src/post.js、camera.js、ui.js | 像素后处理、OrbitControls、界面与快捷键；只读 |
| 工程配置 | package.json、pnpm-lock.yaml、build.mjs | three 0.180.0；开发依赖 esbuild 0.25.11、playwright-core 1.56.1；本步不安装或升级 |
| 原工具 | tools/serve.mjs、tools/qa.mjs | 使用原 serve 工具提供本机 HTTP；原 QA 脚本未作为本轮验收执行 |
| 原说明/QA | README.md、QA_REPORT.md | 参考资料；旧 Windows/RTX 3060、83 项及 60 FPS 结论没有计入本轮通过项 |
| 原宣传图 | screenshots/ 下 6 张 PNG | 只作来源参考；本轮另存真实运行截图 |
| 原 QA 证据 | qa-shots/ 下 14 个文件 | 历史图片、日志及结果；不覆盖、不当作本轮证据 |
| 仓库辅助 | .gitattributes、.gitignore、.nojekyll | 仓库/静态发布辅助；本步不修改、不部署 |

HTTP 实际请求均为本机成品文档，没有外部请求尝试；外部 HTTP 请求拦截开启时，原页仍完整运行。Firefox 的新上下文 file:// 加载也取得实际场景。受管 Chromium 的 file:// 被浏览器策略阻止，见 [原有问题与边界](original-issues.md)。

本步只在主站的 docs/beach-bottle-boat、docs/evidence/beach-bottle-boat-step-1、tests/beach-bottle-boat-step-1 新增资料。主站 95 项生产输入、罗森 46 个运行文件、原仓库 44 个文件和八组既有证据封存均纳入执行前后复核，结果见 [验收报告](step-1-verification.md)。
