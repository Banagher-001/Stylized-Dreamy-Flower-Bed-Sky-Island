# 备用启动与排障

常规启动是 Windows 的 `START-DEV.cmd`，或在源码目录执行 `npm.cmd ci`、`npm.cmd run dev`。如果失败，按下面与当前情况对应的方案操作。文中的 `npm.cmd` 用于 Windows；macOS / Linux 使用 `npm`，`node` 命令通用。

## 只想先查看网页：使用成品包

1. 下载[当前成品 ZIP](../release/experiment-inline-step7-4901f6d5c2824013-site.zip)。在 GitHub 的文件页面可点击「Download raw／下载原始文件」。
2. 完整解压，进入同时包含 `index.html`、`SITE-PACKAGE.txt`、`assets`、`experiments` 和 `scripts` 的文件夹。不要在 ZIP 压缩包内部运行，也不要只取出 HTML。
3. Windows 在该文件夹空白处右键，选择「在终端中打开」，执行：

```powershell
node scripts/preview-site.mjs --port 0
```

4. 将终端显示的完整地址复制到浏览器。端口由系统自动选择，每次可能不同；不要固定打开旧的 `5173` 或 `4173`。
5. 保留终端；按 `Ctrl+C` 停止服务。

此方式需要 Node.js 22.12 或更高版本，推荐安装 Node.js 24 LTS。成品已构建好，包含庭院、工具卡和「交互实验」中的罗森便利店与瓶中海洋。

双击 `START-PREVIEW.cmd` 没有反应或浏览器没有自动弹出时，也使用上述手动命令。打开终端运行能保留报错；浏览器未自动打开时，手动复制地址即可。

## 依赖已安装：源码构建后预览

在包含 `package.json`、`package-lock.json` 和 `src` 的源码目录打开终端：

```powershell
npm.cmd run build
node scripts/preview-site.mjs --dir dist --port 0
```

第一条成功后再执行第二条。预览使用 `dist` 中的构建结果；修改源码后，先在旧预览终端按 `Ctrl+C`，重新构建，再启动预览。若 `npm.cmd ci` 尚未成功或构建报错，先用成品包查看网页。

## 依赖已安装：直接启动开发工具

在源码根目录执行：

```powershell
node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5174
```

此方式绕过 `npm.cmd run dev`，支持开发时的自动刷新。若端口被占用，Vite 可能选择下一个端口，始终以终端显示的地址为准。若提示找不到该文件，表示本地依赖没有完整安装，需要重试 `npm.cmd ci`；单纯换启动命令不能补齐缺失的依赖。

## 按报错处理

| 看到的情况 | 处理方法 |
| --- | --- |
| 找不到 `node`，或提示不是内部命令 | 安装 [Node.js 24 LTS](https://nodejs.org/)，关闭旧终端并重新打开，执行 `node --version` 确认。Windows 使用官网 `.msi` 安装器。 |
| PowerShell 提示禁止运行 `npm.ps1` | 使用 `npm.cmd ci` / `npm.cmd run dev`；也可以先输入 `cmd` 进入命令提示符，再运行 `npm ci` / `npm run dev`。无需更改 PowerShell 执行策略。 |
| 找不到 `package.json`，或 `ENOENT` | 当前目录不对，或源码没有完整解压。在含 `package.json` 的目录打开终端。成品包没有该文件，应使用成品预览命令。 |
| `npm ci` 提示缺少锁文件或锁文件不匹配 | 重新下载并完整解压同一版本的源码，保留配套的 `package.json` 与 `package-lock.json`，再安装；不要混用不同版本的文件。 |
| 依赖下载超时，出现 `ETIMEDOUT` / `ECONNRESET` | 先检查网络并重试；也可按下方命令仅为本次安装指定镜像。急需查看时，改用成品包。 |
| 安装时报 `EBUSY` / `EPERM`，提示文件被占用 | 关闭自己为本项目打开的旧开发／预览终端后再重试，必要时退出正在占用项目文件的程序。 |
| 端口被占用 | 成品预览加 `--port 0` 自动选择空闲端口；开发可使用上述 `--port 5174`，按终端实际地址访问。 |
| 提示缺少 `dist/index.html` | 源码尚未构建，先成功执行 `npm.cmd run build`；或者下载成品包。仓库／源码包的 `START-PREVIEW.cmd` 不能替代构建。 |
| 浏览器打不开、一直加载，或地址以 `file://` 开头 | 用预览命令启动 HTTP 服务；确认终端仍在运行、地址与端口一致，且 `assets`、`experiments` 没有遗漏。浏览器需支持 WebGL 2。 |

仅在依赖下载遇到网络问题时，可尝试：

```powershell
npm.cmd ci --registry=https://registry.npmmirror.com
npm.cmd run dev
```

第一条只为本次安装指定镜像，不修改全局 npm 配置。安装成功后再执行第二条；如果仍失败，保留完整报错，使用成品预览方案。

本地 `localhost` / `127.0.0.1` 地址只供当前电脑访问。以上备用方式不等于公开部署；GitHub 中保存的成品包与源码包继续保持原验收字节。
