# sakan · 张辰翰的创作庭院

三柱滚动作品集：从清新的像素庭院出发，用滚轮沿石柱阅读个人介绍、AI 影像和 Coding 作品。水球流纹、移动云影、三只飞鸟与可随时接管的自动导览保留。小屏、短横屏、放大文字或减少动态时，使用同一份正文的稳定阅读。

本轮「关于我」十四步改版候选为 **about-refresh-step14-6341623c81b6b265**。身份、经历和制作流程已接入；第三屏包含 22 张真实工具卡、首批四卡的三维入场、自动横向展示、随滚轮速度加速与缓冲、悬停倾斜、固定阅读、分类、全部工具、操作说明及飞离/返回衔接。本轮改版、下载包和验收记录纳入本次仓库保存，版本与范围见 [GitHub 保存说明](docs/github-about-refresh-handoff.md)。网站尚未部署。

[最新运行指南](docs/about-refresh/run-guide.md) · [维护说明](docs/about-refresh/maintenance.md) · [第十四步验收](docs/about-refresh/step-14-verification.md) · [本轮交接](docs/about-refresh/step-14-handoff.md) · [完整验收附件与恢复方法](docs/about-refresh/evidence/README.md)

姓名张辰翰，化名 sakan（萨坎），现于枫叶互动制作 AI 动画，曾在游族网络。关于我不列场景为正式项目，也不展示奖项。AI 影像区仍明确标记「网页设计样片 / 非个人实际项目」；真实影片、职责与联系方式可在后续提供后替换。

Coding 区按 **LAWSON → BOTTLE OCEAN → COURTYARD** 展示，默认罗森。前两项使用大尺寸独立网页，保留原网页功能，支持档案、独立打开与返回阅读；庭院复用主站场景。原资源位于 `public/experiments/lawson/` 和 `public/experiments/bottle-ocean/`，运行无需访问 GitHub 或私有仓库。

## 使用最新版

- [成品 ZIP](release/about-refresh-step14-6341623c81b6b265-r3-site.zip)：完整解压，安装 Node.js 后，Windows 双击 `START-PREVIEW.cmd`。无需安装 npm 依赖。
- [源码 ZIP](release/about-refresh-step14-6341623c81b6b265-r3-source.zip)：包含当前源码、锁文件、启动工具、维护说明与本轮可复用验收脚本；不含 Git 历史、历史证据及嵌套压缩包。
- [文件及版本清单](release/about-refresh-step14-6341623c81b6b265-r3-manifest.json) · [SHA256SUMS](release/about-refresh-step14-6341623c81b6b265-r3-SHA256SUMS)

网站通过 **HTTP** 运行，不能直接双击 HTML。`127.0.0.1` / `localhost` 只能在启动服务的电脑访问；本地预览不等于公网发布。若要让别人使用网址访问，需要另行部署静态站点。

## 开发环境与启动

已验证 Node.js **24.22.1**、npm **11.9.0**；`.nvmrc` 记录 Node 版本。最低 Node **22.12**、npm **10**。依赖锁定为 Three.js **0.187.0**、Vite **8.3.5**、TypeScript **7.0.2**、`@types/three` **0.187.0**。

Windows 开发可双击 `START-DEV.cmd`。PowerShell 请使用：

```powershell
npm.cmd ci
npm.cmd run dev
```

macOS / Linux：

```bash
npm ci
npm run dev
```

开发默认端口 5173。云环境可用 `npm ci --cache /workspace/.cache/npm`，无需写入受保护的用户目录。重装依赖前关闭自己启动的开发进程，安装后重新启动。

```bash
npm run typecheck
npm run build
node scripts/preview-site.mjs --dir dist --open
```

`build` 先做严格类型检查，再生成 `dist/`。预览脚本只监听本机，显示实际地址；支持 `--port 0` 自动选端口、`--base /portfolio/` 验证子路径、`--strict-port` 禁止占用时换端口。生产部署使用 `dist/` 内容；`npm run preview` 只是本地构建预览。

浏览器需支持 WebGL 2。没有后端、数据库、密钥或 CDN 依赖。应用默认进入当前庭院；`?tour=prototype` 兼容旧链接，`?tour=reference` 进入旧参考稿，`debug=1` 仅用于工程检查。

## 维护与验证

- 关于我与工具卡正文：`src/tour/about-refresh/content.ts`，图标：`src/assets/tool-marks/`。
- 工具卡控制器：`src/tour/about-refresh/`；布局衔接：`src/tour/createReadingLayout.ts`。
- 影像与交互作品资料：`src/tour/filmContent.ts`、`projectContent.ts`、`experimentContent.ts`。
- 本轮完整路线、原网页与持续运行脚本：`tests/about-refresh-final/`。运行参数与证据索引见[验收说明](docs/about-refresh/step-14-verification.md)。

本轮完整路线以真实时钟、实际输入验证。前十三步的细项记录保留于 `docs/about-refresh/`，第十三步的 161 项适配结果作为未变源码的既有依据，不重复计为第十四步新增通过。设备仿真、系统偏好、浏览器引擎和真机实测分别记录；没有宣称实体 iOS / Android、VoiceOver / TalkBack 或硬件 FPS 已通过。

## 历史归档

旧包保留原字节与原版本身份，不代表当前关于我改版。

- **bottle-ocean-step7-3b31ab385ebfc4cb**：此前三作品接入。[运行](docs/beach-bottle-boat/step-7-run-guide.md) · [验收](docs/beach-bottle-boat/step-7-verification.md) · [GitHub 保存说明](docs/github-bottle-ocean-handoff.md)。
- **lawson-fullpage-step7-882322e9045fcdba**：此前双作品接入。[功能对照](docs/lawson-fullpage/step-7-parity.md) · [验收](docs/lawson-fullpage/step-7-verification.md) · [保存说明](docs/github-lawson-handoff.md)。
- **garden-enhancement-step7-487410d10d8ad600**：[快速上手](docs/garden-enhancement/quickstart.md) · [验收](docs/garden-enhancement/step-7-verification.md) · [保存说明](docs/github-enhancement-handoff.md)。约 432 MB 的完整验收 ZIP 使用 Git LFS，获取方式与 SHA256 见该保存说明。

旧 `scroll-garden-step12-*`、`portfolio-*`、`courtyard-*` 及各自报告继续保留。[阶段目录](docs/scroll-garden/README.md)与[初次 GitHub 交接](docs/github-handoff.md)记录当时状态；其中的上传/未上传描述仅适用于各自生成时点。
