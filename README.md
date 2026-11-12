# sakan · 张辰翰的创作庭院

默认首页为三柱滚动作品集：滚轮/触摸控制运镜，沿柱身阅读个人介绍、AI影像与交互作品。小屏、短横屏、大字或减少动态时使用同一正文的稳定阅读。三柱、魔法文字、水潭和悬浮水球保持现有风格；当前包含介绍背景羽化、球面流纹、可接管自动导览、移动云影和三只飞鸟。

当前工作区已接入罗森便利店完整网页：Coding 区提供 LAWSON / COURTYARD 双作品入口，罗森以大尺寸独立文档运行，保留原页面和控制台，支持档案、独立打开及返回阅读。罗森原资源随项目保存在 `public/experiments/lawson/`，运行时无需访问私有仓库。本次完整嵌入已完成当前环境验收，候选 **lawson-fullpage-step7-882322e9045fcdba**。[逐项功能对照](docs/lawson-fullpage/step-7-parity.md) · [最终验收](docs/lawson-fullpage/step-7-verification.md) · [运行与交付](docs/lawson-fullpage/step-7-handoff.md)。本次仓库保存见 [GitHub 保存说明](docs/github-lawson-handoff.md)；封存报告保留验收当时的状态，网站尚未部署上线。

此前庭院七步增强的验收候选为 **garden-enhancement-step7-487410d10d8ad600**。该阶段三浏览器、十分钟持续运行、20轮反复操作、独立解压与源码重建均通过。[庭院快速上手](docs/garden-enhancement/quickstart.md) · [维护与作品替换](docs/garden-enhancement/maintenance.md) · [该阶段验收](docs/garden-enhancement/step-7-verification.md)。

姓名张辰翰，化名sakan（萨坎），现于枫叶互动制作AI动画，此前在游族网络。真实个人AI影片、分镜/职责及联系方式仍待提供；第二柱明确标记网页设计样片，第三柱展示罗森交互网页、庭院习作与注明版本的早期片段。

通过HTTP预览站点目录即可进入庭院。`?tour=prototype`兼容旧链接，`?tour=reference`进入旧参考作品集。`debug=1`仅供明确工程检查。源码、启动工具、测试、文档、原始验收记录及源码/成品ZIP随仓库保存；约432MB的完整验收ZIP通过Git LFS保存在仓库原路径，获取方式与SHA256见[本轮GitHub保存说明](docs/github-enhancement-handoff.md)。已封存ZIP和报告中的“未提交/推送”保留封包当时的事实，后续仓库保存单列记录。网站尚未部署上线。

## 环境

已验证 Node.js **24.22.1**、npm **11.9.0**。`.nvmrc` 记录实际使用的 Node.js 版本。

依赖版本：Three.js **0.187.0**、Vite **8.3.5**、TypeScript **7.0.2**、`@types/three` **0.187.0**。完整依赖由 `package-lock.json` 锁定。

浏览器需要支持 WebGL 2。没有后端、数据库、外部图片服务或 API 密钥要求。应用运行不请求 CDN。

## 启动

Windows只看成品：完整解压下方成品ZIP，已安装Node后双击其中的`START-PREVIEW.cmd`。修改仓库源码可双击根目录`START-DEV.cmd`；PowerShell手动运行请使用`npm.cmd ci`和`npm.cmd run dev`。

macOS/Linux在仓库根目录执行：

```bash
npm ci
npm run dev
```

开发服务器默认使用 5173 端口。此云任务中的仓库路径为 `/workspace/Stylized-Dreamy-Flower-Bed-Sky-Island`。使用现有隔离任务和 checkout，无需创建 Git worktree。

云环境可使用工作区内缓存，避免写入受保护的用户目录：

```bash
npm ci --cache /workspace/.cache/npm
```

复装依赖前先停止自己启动的开发 / 预览进程，安装完成后重新启动，避免旧进程引用失效的 Vite 依赖预构建缓存。

## 类型检查与生产构建

```bash
npm run typecheck
npm run build
npm run preview
```

`build` 会先运行严格类型检查，再生成 `dist/`。`preview` 默认使用 4173 端口；它用于检查产物，不是面向公网的生产服务器。可用 `-- --port 4173 --strictPort` 固定端口。

Vite 将 Three.js 的核心与 WebGL 渲染模块分包，应用逻辑单独输出；没有提高告警阈值或禁用检查。

需要复验实际 gzip 传输时，在构建后运行：

```bash
node scripts/serve-dist.mjs dist 4174
```

此工具只监听本机，入口使用 `no-cache`，哈希资源使用长期缓存；重新构建后须重启。它用于本地产物验证。网站可直接将 `dist/` 的内容作为静态站点根目录，配置详情见 [交付说明](docs/garden-enhancement/delivery.md)。

## 当前交付文件

下列压缩包是此前庭院增强阶段的归档。当前罗森集成请使用本次提交后的仓库源码重新构建；版本范围与启动方法见[本次运行与交付说明](docs/lawson-fullpage/step-7-handoff.md)，保存记录见 [GitHub 说明](docs/github-lawson-handoff.md)。

- [成品包，约1.5MB](release/garden-enhancement-step7-487410d10d8ad600-site.zip)：完整静态网页与Windows预览入口。
- [源码包，约2MB](release/garden-enhancement-step7-487410d10d8ad600-source.zip)：可独立安装、修改和严格构建。
- [版本及SHA256清单](release/garden-enhancement-step7-487410d10d8ad600-manifest.json)：候选身份与独立解压结果。
- [完整验收附件，约432MB](release/garden-enhancement-step7-487410d10d8ad600-evidence.zip)：通过Git LFS保存，克隆完整记录需要Git LFS；获取方法见[保存说明](docs/github-enhancement-handoff.md)。原始验收记录也保留在`docs/evidence/garden-enhancement-step-*/`。

成品通过HTTP预览，不能直接双击HTML代替。成品本地启动只需要Node，无需安装npm依赖；开发源码首次安装依赖可能需要网络。下载后的文件已在独立中文/空格目录核验。详见[交付说明](docs/garden-enhancement/delivery.md)。

旧`scroll-garden-step12-*`、`portfolio-*`与`courtyard-*`归档及其原始验收说明保持，分别代表此前版本。[初次GitHub交接记录](docs/github-handoff.md)作为历史保留。

## 维护与历史

当前庭院数据：`src/tour/aboutContent.ts`、`filmContent.ts`、`experimentContent.ts`；旧参考稿数据：`src/content/portfolio.ts`。路线与阅读/渲染边界见[维护说明](docs/garden-enhancement/maintenance.md)。

[阶段目录](docs/scroll-garden/README.md)保存逐步标准与实现记录。早期[场景交付](docs/step-9-handoff.md)、[参考作品集设计](docs/portfolio-design.md)及旧courtyard/portfolio归档代表各自版本，不冒充最新滚动庭院。

Linux Chromium/Firefox/GTK WebKit及设备/文字模拟的通过范围见验收。真实iOS/Android、系统浏览器栏/刘海与大字、VoiceOver/TalkBack、物理触控板/APZ及硬件FPS仍待复核；没有把模拟结果写成真机通过。
