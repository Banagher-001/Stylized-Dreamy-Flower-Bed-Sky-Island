# 当前三作品版本运行指南

日期：2026-11-14（Asia/Shanghai）。当前 Coding 顺序为 LAWSON → BOTTLE OCEAN → COURTYARD，默认罗森。本文说明当前源码及本轮交付包；完整验收结果与限制由同候选的 step-7-verification.md、step-7-handoff.md 和交付清单记录。

## 成品包：只预览网站

完整解压文件名包含本轮候选身份的 `-site.zip`，保留 index.html、assets、experiments、scripts 等目录，不只取出一个 HTML。

安装符合要求的 Node.js 后，Windows 可双击包内 START-PREVIEW.cmd。macOS/Linux 或手动启动：

```bash
node scripts/preview-site.mjs --open
```

该预览使用 Node 内置模块，不需要 npm ci。终端会打印实际本机地址，默认尝试 4173，端口占用时说明后尝试其他端口；保持窗口运行，Ctrl+C 停止。自动打开浏览器失败时可手动复制地址。

指定端口、目录和项目子路径时可使用：

```bash
node scripts/preview-site.mjs --dir . --port 4175 --base /portfolio-check/ --strict-port
```

这是 HTTP 预览，双击 index.html 不作为完整运行方式。本机 localhost 地址只供同一台电脑访问；公开访问需另行静态部署，本轮交付不自动上线。

## 源码包或当前仓库：安装、修改和构建

要求 Node.js >=22.12.0、npm >=10，推荐与 .nvmrc 对应的 Node.js LTS 24。本轮实际工具版本记在最终验收中。源码包可直接使用，无需旧 dist、其他压缩包或原 Git 历史。

macOS/Linux 在源码根目录执行：

```bash
npm ci
npm run dev
```

Windows PowerShell 使用：

```powershell
npm.cmd ci
npm.cmd run dev
```

Windows 也可双击源码目录的 START-DEV.cmd。开发服务打印实际地址，默认端口为 5173；首次安装依赖可能需要网络。运行网站本身不要求 API 密钥、数据库、GitHub 在线资源或外部 CDN。

类型检查与构建：

```bash
npm run typecheck
npm run build
npm run preview
```

build 已包含类型检查，默认生成当前目录 dist。preview 需要先构建；也可以用 `node scripts/preview-site.mjs --dir dist` 通过无依赖静态服务预览产物。PowerShell 对应使用 npm.cmd。验收时构建到专用目录以保留旧归档，用户自行构建时使用上述正常命令即可。

## 如何进入作品

打开个人网站后，沿章节阅读或使用稳定阅读，到 Coding/交互实验区选择“瓶中海洋”，点击“进入完整网页”。原页面填满宿主工具栏以外的区域，原控制台可滚动，支持画质、镜头、沙盒、暂停、截图和 H/Space/Escape 等原操作。

顶部可去档案、独立打开或返回阅读。子页 Escape 用于原编辑退出；宿主工具栏获得原生焦点后 Escape 按宿主规则返回。关闭或去档案会卸载当前原页，重新进入从原默认状态启动。

水潭入口仍打开 courtyard。进入独立作品会停止主站导览并暂停被覆盖庭院的持续绘制，返回保留用户原播放选择，导览不自动续播。

## 原文件、像素与 PNG

原瓶中海洋成品位置为 public/experiments/bottle-ocean/index.html；构建内为 experiments/bottle-ocean/index.html。固定原提交 d94c1f911a39143fd8f5efe152b99a87fdc53184，成品 SHA256 为 941feb2ea6ddd3cc93aad5b0b92dbca52ee66a3e1098fee0dbf16f01ca63d1ef。

原像素档位决定内部低分辨率渲染，截图则按画布 CSS 尺寸 × min(DPR,2)导出 PNG，二者不能混用。PNG 仅含原 WebGL 场景，不含原控制台或宿主工具栏，不固定为 1920×1080。

原亮度默认步进、standard 读数精度、镜头惯性、原暂停仍绘制及竖屏可能裁去部分瓶身的行为保留。真实 hidden、真机/系统缩放、Safari/Windows 与硬件性能范围以本轮实际报告为准，手机模拟和 Linux WebKit 不代替真机结论。

## 包身份与历史

源码与成品包使用同一候选身份，交付时附包大小、SHA256 和逐文件清单。下载后以同目录 manifest.json/SHA256SUMS 与聊天中的交付链接核对。摘要不写回其自身压缩包，避免循环生成。

源码包保留应用、构建、启动和必要运行说明；README 中引用的完整历史原始证据及旧大型归档不随源码包复制。本轮验证记录保留在工作区/后续仓库保存中，不能把旧归档当成当前三作品成品。

本轮工作区交付与 GitHub 提交、部署分别记录。Windows 启动脚本的静态检查不等于已经做过 Windows 真机测试。
