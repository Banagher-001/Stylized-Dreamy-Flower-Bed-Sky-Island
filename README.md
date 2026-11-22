# sakan · 张辰翰的创作庭院

从清新的像素庭院出发，用滚轮沿三根石柱阅读个人介绍、AI 影像和 Coding 作品。中央的 708 粒子水球会起伏，水纹沿球面流动，水珠落入池面时推开涟漪。庭院还有移动云影、三只飞鸟与可随时接管的自动导览。小屏、短横屏、放大文字或减少动态时，使用同一份正文的稳定阅读。

当前成品版本为 **sakan-pool-final-8cbfe430**。三根石柱各有不同的砌石和实体苔体。八边水潭有错缝池壁、贴地基脚和两块半浸浅石，两颗水珠触水后依次泛起亮点、主环和余波。庭院右侧有八块错落的踏石、四处实体青苔和五簇缝间短草。窄屏从「水潭」可以进入庭院现场，`?orb=lively` 可以回看改版前的水球。

[当前成品验收](docs/pool-detail/05-pool-acceptance.md) · [水潭改造前后对照](docs/pool-detail/01-pool-comparison.png) · [原网页功能对照](docs/experiment-inline/step-6-parity.md) · [工具卡改版验收](docs/card-refinement/step-7-acceptance.md) · [备用启动与排障](docs/startup-fallback.md)

姓名张辰翰，化名 sakan（萨坎），现于枫叶互动制作 AI 动画，曾在游族网络。关于我不列场景为正式项目，也不展示奖项。AI 影像区仍明确标记「网页设计样片 / 非个人实际项目」；真实影片、职责与联系方式可在后续提供后替换。

当前源码的「交互实验」窗口展示 **罗森便利店**和**瓶中海洋**。进入作品窗口后自动载入罗森，用上方标签可原位切换，窗下可展开对应档案。水潭章节可进入庭院现场。两个原网页从 `public/experiments/lawson/` 和 `public/experiments/bottle-ocean/` 同源加载，运行无需访问 GitHub 或私有仓库。

## 下载当前成品

完整解压成品包，安装 Node.js 后在 Windows 双击 `START-PREVIEW.cmd`。也可以在解压目录运行 `node scripts/preview-site.mjs --open`。 [当前成品 ZIP](release/sakan-pool-final-8cbfe430.zip) · [SHA-256 校验值](release/sakan-pool-final-8cbfe430-SHA256SUMS)

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

### 启动失败时的备用方案

**备用一：直接预览成品（推荐）。** 如果 `npm.cmd ci` 或开发启动失败，可以完整解压上方的成品包。在能看到 `SITE-PACKAGE.txt` 和 `scripts` 文件夹的目录中，右键选择「在终端中打开」，再运行以下命令。

```powershell
node scripts/preview-site.mjs --port 0
```

此方式只需要 Node.js，无需安装 npm 依赖或重新构建。`--port 0` 自动选择空闲端口；将终端打印的完整 `http://127.0.0.1:实际端口/` 地址复制到浏览器，保留终端窗口。按 `Ctrl+C` 停止。不要直接双击 HTML。

**备用二：源码构建后预览。** 如果依赖已经安装成功，但开发服务器启动失败，可在包含 `package.json` 的源码根目录执行：

```powershell
npm.cmd run build
node scripts/preview-site.mjs --dir dist --port 0
```

先确认构建成功，再打开终端显示的地址。此方式展示构建结果，修改源码后需重新构建；若构建也失败，使用备用一。

**备用三：直接启动开发工具。** 如果依赖已安装、需要继续修改网页，但 `npm.cmd run dev` 无法启动，可绕过 npm 启动命令，换一个端口：

```powershell
node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5174
```

始终打开终端实际打印的地址。提示找不到 `node_modules/vite` 时，需要先成功安装依赖，或使用备用一。macOS / Linux 将以上 `npm.cmd` 换成 `npm`，`node` 命令相同。

双击无反应、Node 未识别、PowerShell 脚本限制、依赖下载失败等情况，见[完整备用启动与排障说明](docs/startup-fallback.md)。

## 维护与验证

- 关于我与工具卡正文：`src/tour/about-refresh/content.ts`，图标：`src/assets/tool-marks/`。
- 工具卡控制器：`src/tour/about-refresh/`；布局衔接：`src/tour/createReadingLayout.ts`。
- 影像与交互作品资料：`src/tour/filmContent.ts`、`projectContent.ts`、`experimentContent.ts`。
- 主站浏览与原网页测试位于 `tests/about-refresh-final/` 和 `tests/experiment-inline-step-7/`。[第七步验收记录](docs/experiment-inline/evidence/step-7/acceptance.json)

水潭改造版验收覆盖原导览路径、滚轮接管、两种画面模式及环境播放。窄屏采用 Chromium 触屏模拟。 [验收记录](docs/pool-detail/05-pool-acceptance.md)

## 历史归档

以下记录对应各阶段的历史构建。

- **sakan-paving-final-bbc12628** 的踏石改造版。 [改造前后对照](docs/paving/evidence/step-6/before-after.png) · [当时的验收](docs/paving/step-6-final-acceptance.md) · [历史成品](release/sakan-paving-final-bbc12628.zip)
- **particle-orb-step7-99634b67a4c3f8f7** 的粒子水球版。 [当时的验收](docs/particle-orb/step-7-final-acceptance.md) · [历史成品](release/particle-orb-step7-99634b67a4c3f8f7-site.zip)
- **experiment-inline-step7-4901f6d5c2824013** 的两作品原位浏览版。[当时的整站验收](docs/experiment-inline/step-7-acceptance.md) · [历史成品](release/experiment-inline-step7-4901f6d5c2824013-site.zip)
- **about-refresh-step14-6341623c81b6b265** 的关于我改版。[运行指南](docs/about-refresh/run-guide.md) · [维护说明](docs/about-refresh/maintenance.md) · [第十四步验收](docs/about-refresh/step-14-verification.md) · [当时的成品](release/about-refresh-step14-6341623c81b6b265-r3-site.zip) · [当时的源码包](release/about-refresh-step14-6341623c81b6b265-r3-source.zip) · [保存说明](docs/github-about-refresh-handoff.md)
- **bottle-ocean-step7-3b31ab385ebfc4cb**：此前三作品接入。[运行](docs/beach-bottle-boat/step-7-run-guide.md) · [验收](docs/beach-bottle-boat/step-7-verification.md) · [GitHub 保存说明](docs/github-bottle-ocean-handoff.md)。
- **lawson-fullpage-step7-882322e9045fcdba**：此前双作品接入。[功能对照](docs/lawson-fullpage/step-7-parity.md) · [验收](docs/lawson-fullpage/step-7-verification.md) · [保存说明](docs/github-lawson-handoff.md)。
- **garden-enhancement-step7-487410d10d8ad600**：[快速上手](docs/garden-enhancement/quickstart.md) · [验收](docs/garden-enhancement/step-7-verification.md) · [保存说明](docs/github-enhancement-handoff.md)。约 432 MB 的完整验收 ZIP 使用 Git LFS，获取方式与 SHA256 见该保存说明。

旧 `scroll-garden-step12-*`、`portfolio-*`、`courtyard-*` 及各自报告继续保留。[阶段目录](docs/scroll-garden/README.md)与[初次 GitHub 交接](docs/github-handoff.md)记录当时状态；其中的上传/未上传描述仅适用于各自生成时点。
