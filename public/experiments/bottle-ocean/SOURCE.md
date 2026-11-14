# 瓶中海洋 · 原成品来源与运行说明

本目录保存 Beach-Bottle-Boat 的完整单文件成品，原 HTML 和第三方声明按原字节复制。场景、Three.js、着色器、程序化资源、模拟与原界面均包含在 index.html 中。

| 项目 | 固定来源 |
|---|---|
| 来源仓库 | https://github.com/Banagher-001/Beach-Bottle-Boat |
| 原提交 | d94c1f911a39143fd8f5efe152b99a87fdc53184 |
| 原入口 | 仓库根目录 index.html |
| 原别名 | bottle_ocean_sandbox.html，与原 index.html 字节相同；本站使用 index.html 作为唯一入口 |
| HTML 大小 | 1,979,264 字节 |
| HTML SHA256 | 941feb2ea6ddd3cc93aad5b0b92dbca52ee66a3e1098fee0dbf16f01ca63d1ef |
| 原 Three.js | 0.180.0，已经内联，不依赖主站 Three.js |
| 保存日期 | 2026-11-13（Asia/Shanghai） |
| 第三方说明 | [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)，原字节保留 |
| 声明 SHA256 | 0242e66ea25c3e7d1ba883d5e237065e5daa24fa88d83fba74f6859e3edf7861 |

从个人网站项目目录使用已有开发服务 `npm run dev` 后，独立入口为服务地址下的 `experiments/bottle-ocean/index.html`。生产构建后，使用 HTTP 静态服务提供整个构建目录；网站部署在子路径时，在该子路径下使用同一相对入口。此说明不表示网站已部署，也不表示主站根 index.html 支持文件直开。

原成品没有重新构建、压缩或注入主站脚本，没有使用 WORLD_STUB。主站构建仅复制 public 中的静态成品；无需将原工程依赖加入主站。原源码的维护来源为上述固定提交。

原截图按钮导出的是 WebGL 场景 PNG，不含 DOM 控制面板。宽高分别为画布 CSS 尺寸×min(DPR,2)，取整且至少为 1；1920×1080 是一种视口条件，并非所有情况下固定输出。

原版默认亮度读数、镜头恢复惯性、图形丢失后的原状态/提示等问题已有记录。仓库内资料见 [原有问题与验证边界](../../../docs/beach-bottle-boat/original-issues.md) 和 [第一步验收](../../../docs/beach-bottle-boat/step-1-verification.md)；这些文档链接按源代码仓库目录组织，并非生产站点运行依赖。

作品封面候选另存于主站 src/assets/bottle-ocean-cover.png，来自第一步原截图按钮的真实下载，1920×1080、DPR1、原 fine 画质，不含 DOM 面板。来源证据为 docs/evidence/beach-bottle-boat-step-1/interactions/export-1920x1080-ui-visible.png，SHA256 为 7fc210e644776fda61efbe4d05a15e75392d5f563a024474dfcd0bfcf23da4fa。封面与运行入口独立，本目录运行不依赖封面。
