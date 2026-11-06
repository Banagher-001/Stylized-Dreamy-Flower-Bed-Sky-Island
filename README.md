# sakan · 张辰翰的创作庭院

默认首页为三柱滚动作品集：滚轮/触摸控制运镜，沿柱身阅读个人介绍、AI影像与交互作品。小屏、短横屏、大字或减少动态时使用同一正文的稳定阅读。三柱、魔法文字、水潭和悬浮水球保持现有风格。

第十二步完成技术收尾与候选交付，结果以[逐项验收](docs/scroll-garden/step-12-verification.md)、本步summary及`release/scroll-garden-step12-manifest.json`为准。[打开与保存](docs/scroll-garden/delivery.md) · [修改介绍和作品](docs/scroll-garden/maintenance.md) · [实现说明](docs/scroll-garden/step-12-implementation.md)。

姓名张辰翰，化名sakan（萨坎），现于枫叶互动制作AI动画，此前在游族网络。真实个人AI影片、分镜/职责及联系方式仍待提供；第二柱明确标记网页设计样片，第三柱展示本仓库真实庭院与注明版本的早期片段。

直接打开站点目录即可进入庭院。`?tour=prototype`兼容旧链接，`?tour=reference`进入旧参考作品集。`debug=1`仅供明确工程检查。源码、文档、验收证据和交付归档随本仓库保存；[GitHub保存说明](docs/github-handoff.md)记录本次上传范围。第十二步ZIP和历史报告中“未提交/推送”描述封包当时的状态，已核验归档保持原样。网站尚未部署上线。

## 环境

已验证 Node.js **24.22.1**、npm **11.9.0**。`.nvmrc` 记录实际使用的 Node.js 版本。

依赖版本：Three.js **0.187.0**、Vite **8.3.5**、TypeScript **7.0.2**、`@types/three` **0.187.0**。完整依赖由 `package-lock.json` 锁定。

浏览器需要支持 WebGL 2。没有后端、数据库、外部图片服务或 API 密钥要求。应用运行不请求 CDN。

## 启动

在仓库根目录执行：

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

此工具只监听本机，入口使用 `no-cache`，哈希资源使用长期缓存；重新构建后须重启。它用于本地产物验证。网站可直接将 `dist/` 的内容作为静态站点根目录，配置详情见 [交付说明](docs/scroll-garden/delivery.md)。

## 交付文件

- `release/scroll-garden-step12-source.zip`：源码、锁文件、脚本、测试和说明。
- `release/scroll-garden-step12-site.zip`：可根目录或子目录静态托管的生产文件。
- `release/scroll-garden-step12-evidence.zip`：本步报告、必要基线、代表画面和实际演示。
- `release/scroll-garden-step12-manifest.json`：实际候选指纹、包摘要、解压复验与状态。

请使用HTTP静态托管，不能以file://双击替代；依赖安装是构建条件，成品应用运行无CDN或API密钥需求。源码包不包含node_modules或完整历史大图。当前独立复验命令及历史测试前提见[交付说明](docs/scroll-garden/delivery.md)。把证据包解压到源码目录，可补齐本次证明文件和演示；完整历史资料保留在工作区。

## 维护与历史

当前庭院数据：`src/tour/aboutContent.ts`、`filmContent.ts`、`experimentContent.ts`；旧参考稿数据：`src/content/portfolio.ts`。路线与阅读/渲染边界见[维护说明](docs/scroll-garden/maintenance.md)。

[阶段目录](docs/scroll-garden/README.md)保存逐步标准与实现记录。早期[场景交付](docs/step-9-handoff.md)、[参考作品集设计](docs/portfolio-design.md)及旧courtyard/portfolio归档代表各自版本，不冒充最新滚动庭院。

Linux Chromium/Firefox/GTK WebKit及设备/文字模拟的通过范围见验收。真实iOS/Android、系统浏览器栏/刘海与大字、VoiceOver/TalkBack、物理触控板/APZ及硬件FPS仍待复核；没有把模拟结果写成真机通过。
