# 罗森完整网页嵌入：运行与交付

状态：第七步当前环境验收已完成，候选 `lawson-fullpage-step7-882322e9045fcdba`。当前工作区未提交、推送或发布。

[逐项功能对照](step-7-parity.md) · [最终验收报告](step-7-verification.md) · [候选清单](../evidence/lawson-fullpage-step-7/candidate-manifest.json)

## 当前实现

个人网站的 Coding/C2 区默认展示罗森便利店，另可选择庭院习作。进入罗森现场后，在工具栏下方的大尺寸区域加载完整原网页；原控制台、模型、灯光、镜头、车辆和店员由原页面处理。档案、独立打开和返回阅读由个人网站提供。

罗森原文件在 `public/experiments/lawson/`，构建后原样进入 `dist/experiments/lawson/`。固定原版本为 `95dad9881a7b9d31c0ac635f1f335055d8cb3cc4`，原运行文件 46 个、20,332,784 字节。网页运行时直接读取这些本地资源，无需登录原私有 GitHub 仓库或提供 API 密钥。两套 Three.js 在独立文档中运行。

关闭现场或切到档案会卸载原文档；再次进入恢复原默认状态。普通切换浏览器标签保留当前实例。个人网站导览在进入作品时停止，返回后由访客自行决定是否开启。

## 下载源码后运行

使用含本次集成代码和完整 public 目录的源码。此前 `garden-enhancement-*` 与更早 ZIP 保留其历史版本内容；本次罗森集成以当前工作区源码及本次验收资料为准。尚未推送的工作区内容不会自动出现在 GitHub 下载包中。

要求 Node.js ≥22.12.0、npm ≥10；当前构建环境 Node.js 24.22.1、npm 11.9.0。首次安装依赖通常需要网络，依赖由现有 package-lock.json 固定。

Windows PowerShell 在项目根目录执行：

```powershell
npm.cmd ci
npm.cmd run dev
```

浏览器打开终端输出的 Local 地址，通常为 `http://localhost:5173/`。使用 npm.cmd 可避免 npm.ps1 的 PowerShell 执行策略拦截，不需要为了本项目修改系统执行策略。

macOS/Linux：

```bash
npm ci
npm run dev
```

开发服务器保持运行时可以访问；停止终端进程后地址不再提供网站。localhost 指当前访问者自己的电脑，发给别人不能让其访问你的本地网页。

## 构建和本地成品预览

Windows PowerShell：

```powershell
npm.cmd run build
npm.cmd run preview
```

macOS/Linux：

```bash
npm run build
npm run preview
```

build 包含严格类型检查，生成 dist。preview 打开终端显示的地址，通常为 `http://localhost:4173/`，用于检查构建结果。

已有完整 dist 时，可以使用根目录现有静态预览工具：

```bash
node scripts/serve-dist.mjs dist 4174
```

用浏览器打开 `http://127.0.0.1:4174/`。这个工具只监听本机，不是公网发布。所有页面需通过 HTTP/HTTPS 服务访问，双击 index.html 的 file:// 方式不属于本项目支持的运行方式。

## 文件保全和静态部署

- 源码运行：保留 src、public、配置文件、package.json 与 package-lock.json。
- 静态交付：发布 dist 内完整内容，保持目录层级；包括 assets 和 experiments/lawson 下的 HTML、CSS、JS、vendor、模型与贴图，不只上传主站 index.html。
- 罗森独立入口为站点基路径下的 `experiments/lawson/index.html`。宿主和原页放在同一站点，原页内部资源继续按原相对路径解析。
- 根路径及项目子路径 `/Stylized-Dreamy-Flower-Bed-Sky-Island/` 均纳入本次 HTTP 校验；其他部署前缀需按实际环境再验证。
- 静态服务器需正确返回 JS 等文件类型；缺失 JS/模型返回真实错误，不能统一改写成主站 HTML。若配置内容安全策略，应允许同源 iframe 与原本地资源；全屏权限以实际服务器、浏览器和用户手势为准。

本步提供本地可运行的代码、构建与说明。托管平台、域名、HTTPS、公网访问和自动部署尚未在本轮实施，不能用本机验收地址充当公网作品链接。

## 原版行为和验证范围

固定原版本已有 R 镜头惯性、漫游中 R 的界面缓存、部分位置 W/S 碰撞、N 说明未绑定、手机品牌/顶栏重叠及较小点击区等问题。详情见[原版问题记录](original-issues.md)，本次[最终对照](step-7-parity.md)已逐项注明。保留原页面不等于这些问题已经修复。

手机没有原生触摸漫游方向键。减少动态设置不会自动停止原 JS 动画；原 pauseAll 也不能代替卸载。图形上下文恢复后，宿主需要显式重新载入原场景，旧 ready 标记不作为新 GPU 状态的就绪证明。

Linux 桌面引擎与触摸模拟分别记录。iOS/Android 真机、物理刘海与动态地址栏、真实屏幕阅读器及硬件 GPU 帧率没有实测时保持未验证。BFCache 与历史返回整页重载分开记录。

## 维护入口

- 作品入口与内容：`src/tour/projectContent.ts`。
- Coding 区作品选择与封面：`src/tour/createExperimentReader.ts`。
- 大尺寸查看器、档案、焦点：`src/tour/createProjectViewer.ts`、`src/tour/projectHost.css`。
- 原 iframe 生命周期与就绪/错误观察：`src/tour/createLawsonExperience.ts`。
- 与庭院、导览、阅读恢复的衔接：`src/tour/startTourPrototype.ts`。

历史证据和 after/ 源码副本保留不改；后续修改当前源码时建立新记录。原文件更新应作为新的原版本重新建立资源清单和对照，不能覆盖旧清单伪装同一版本。
