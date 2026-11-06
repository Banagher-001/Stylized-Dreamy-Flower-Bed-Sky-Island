# 第九步：交付与重现

本轮交付为未发布的固定视角风格化庭院网页。第九步工程检查完成；真实手机、物理 GPU、Safari 实机和原生后台覆盖仍有缺口，详见 [验收报告](step-9-final-verification.md) 与 [平台表](step-9-platform-matrix.md)。

## 交付文件

在仓库 `release/` 目录：

| 文件 | 内容 |
| --- | --- |
| `courtyard-source.zip` | 应用源码、锁文件、构建配置、说明、可选验证脚本及第 1～9 步证据；不含依赖缓存、Git 元数据或产物包本身 |
| `courtyard-site.zip` | `dist/` 中的 6 个静态文件，解压即为网站根目录 |
| `manifest.json` | 两个包的 SHA-256、体积/文件数量、构建产物摘要、工具版本及未完成覆盖说明 |

源码包不嵌入 `release/`，避免递归归档；验收材料中的包名指独立交付文件。源码包包含全部必要构建输入，运行应用无需 Python 或云环境的临时浏览器依赖。当前仓库为未产生首次提交的分支，因此清单不伪造 Git 提交号，使用文件与归档摘要标识交付。

## 从源码启动

使用 Node.js 24.22.1 / npm 11.9.0 可重现本次结果；版本记录在 `.nvmrc`。在解压后的项目根目录执行：

```bash
npm ci
npm run build
npm run preview
```

`build` 包含严格 TypeScript 检查。要修改源码使用 `npm run dev`。依赖已锁定，不需图片服务、CDN、后端、数据库或密钥。

隔离临时目录已重新 `npm ci` 并构建，6 个静态产物 SHA-256 与当前 `dist/` 一致，记录见 [隔离构建结果](evidence/step-9/clean-build.json)。这证明当前源文件和工具链下的构建一致性，不代表已经验证未来新云任务的恢复或公网部署。

## 静态网站使用

`courtyard-site.zip` 的根部是 `index.html`、`favicon.svg` 与 `assets/`，可由静态站点服务托管。资源路径按网站根目录构建；如果要放在 `/some/subpath/`，先按目标路径配置 Vite `base` 并重新构建、复验，不能直接假设原包支持任意子路径。

建议托管配置：HTML 与 favicon 重新验证；`assets/` 中带哈希的文件使用 `public, max-age=31536000, immutable`；JS/CSS/SVG 提供正确 MIME 与 gzip/Brotli；压缩响应带 `Vary: Accept-Encoding`。HTTPS 与域名由实际托管环境提供。

本地检查真实 gzip 可执行 `node scripts/serve-dist.mjs dist 4174`。该工具只绑定回环地址、启动时缓存产物，重建后须重启。它不是公网部署动作。当前没有部署或发布任何内容。

## 保留的使用行为

- 默认像素预览：长边采样 384、最近邻、原色；正常画面按钮可直接切换。
- 播放/暂停控制喷泉、草花与树影，默认关闭飘花。尊重减少动态偏好。
- `?waterTime=2` 固定整场景时间；`render=native`、`pixelSize=320|384|448`、`finish=soft`、`env=off` 等沿用已记录的复验参数。
- 上下文中断有恢复提示；无 WebGL 2 时提供可读错误提示。
- 相机与构图固定，没有鼠标拖拽或视角缩放。

后续调色、构图与动效参数位置见 [项目说明](../README.md)。验证工具和运行条件见 [复验说明](../tests/final/README.md)。

## 交付状态

第九步完成后停止新增工作。源码与静态包均保留在当前草稿；未发布环境、未部署站点、未创建提交、未推送仓库。后续修改按用户新指示执行。
