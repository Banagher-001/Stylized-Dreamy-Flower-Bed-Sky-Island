# 当前庭院使用说明

版本：about-refresh-step14-6341623c81b6b265。当前关于我改版与 22 张三维工具卡已经接入。工作区交付不代表 GitHub 已保存，也不代表网站已部署。

## 打开成品

1. 安装 Node.js 24 LTS，完整解压成品 ZIP，文件夹可含中文和空格。
2. Windows 双击 `START-PREVIEW.cmd`，保留弹出的终端。macOS / Linux 在解压目录运行 `node scripts/preview-site.mjs --open`。
3. 在浏览器打开终端显示的 HTTP 地址。关闭终端会停止服务；不能通过直接双击 `index.html` 运行。

成品不需要 npm install。不应单独移动 HTML；assets、experiments、scripts 必须随包保留。本地地址仅供当前电脑访问；对外分享需要另行部署静态站点。

## 修改源码

Windows 可双击 `START-DEV.cmd`。若用 PowerShell，执行 `npm.cmd ci`，然后 `npm.cmd run dev`，避免被 npm.ps1 的系统执行策略阻断。macOS / Linux 使用 `npm ci`、`npm run dev`。

运行 `npm run build` 会先检查 TypeScript，再输出 dist。查看生产版：`node scripts/preview-site.mjs --dir dist --open`，也可双击源码包的 `START-PREVIEW.cmd`（须先构建）。Node 最低 22.12，npm 最低 10，本轮使用 Node 24.22.1 / npm 11.9.0。首次安装开发依赖可能需要网络。

## 浏览方式

- 封面滚轮控制运镜；自动导览可开启或停止，手动输入接管。环境播放与导览分别控制。
- 关于我依次展示身份、经历和工具。工具屏先飞入 Midjourney / ComfyUI / 可灵 / Blender 四卡，再横向展示；指针进入卡排时滚轮加速，退出卡排后继续页面运镜。
- 卡片悬停可放大并倾斜，点击固定正文；分类缩小范围，「全部工具」显示完整列表。操作说明随当前输入能力呈现；Esc 先关闭说明或列表，再解除固定。
- 手机使用原生横向滑动，点击卡片展开，不要求鼠标悬停。窄屏、大字、减少动态或空间不足时自动使用稳定阅读，可随时使用完整正文。
- AI 影像标记为网页设计样片。Coding 的「进入完整网页」在大尺寸界面运行原网页；顶部可查看档案、独立打开或返回阅读。
- 三个作品分别为罗森、瓶中海洋和庭院习作。瓶中海洋的截图由其原生按钮下载；回到主站后不会保留隐藏运行的 iframe。

键盘：Tab 前进、Shift+Tab 后退、Enter / Space 激活按钮；作品选择标签使用左右方向键和 Home / End。原网页内部快捷键由原网页处理。第一个「跳到阅读内容」入口可进入稳定阅读。

## 部署目录

静态部署上传 dist 的完整内容；成品包中上传 index.html、assets、experiments 等站点资源，预览脚本和说明文件无需上传。构建使用相对 base，支持站点根目录和仓库子路径。子路径预览示例：

```bash
node scripts/preview-site.mjs --dir dist --base /portfolio/ --port 4176 --strict-port
```

打开终端给出的 `/portfolio/` 地址，不要丢掉路径末尾的 `/`。网站不需要 API 密钥或运行时 GitHub 连接。
