# 瓶中海洋完整接入：GitHub 保存说明

根据用户“先把上次更新好的最新版网页更新到我的 GitHub 仓库”的明确指示，将上轮已完成验收的个人网站保存到 [Banagher-001/Stylized-Dreamy-Flower-Bed-Sky-Island](https://github.com/Banagher-001/Stylized-Dreamy-Flower-Bed-Sky-Island) 的 main 分支。本记录准备时间为 2026-11-14T17:42:47.169915+08:00。上传前远端与本地基线均为 `eae15c040aa1527833d844d1bbf81eb551843386`；使用正常提交与快进推送保留历史。本记录首次加入的提交对应本次保存，准确身份见 [main 提交记录](https://github.com/Banagher-001/Stylized-Dreamy-Flower-Bed-Sky-Island/commits/main/)。

## 本次版本和范围

候选 **bottle-ocean-step7-3b31ab385ebfc4cb**，Coding 顺序为 LAWSON → BOTTLE OCEAN → COURTYARD，默认罗森。瓶中海洋以大尺寸完整网页运行，保留原控制台、参数、镜头、沙盒、模拟、原按钮 PNG 下载、档案、独立打开与返回阅读。当前 97 项生产输入与上轮验收候选逐项一致。

保存当前主站源码、两个独立网页的共用容器、瓶中海洋专用观察器、三作品选择器、真实封面，以及 public/experiments/bottle-ocean/ 中原成品、来源和第三方说明。原瓶中海洋提交为 d94c1f911a39143fd8f5efe152b99a87fdc53184，成品 SHA256 为 `941feb2ea6ddd3cc93aad5b0b92dbca52ee66a3e1098fee0dbf16f01ca63d1ef`，原文件没有重构建或改写。

本次也保存瓶中海洋各阶段实际标准、测试、原始记录和独立封存，并将两个原验收 ZIP 原字节复制到 release/。既有罗森、庭院与旧归档保持；14 组独立封存完整。node_modules、临时 dist、缓存和上传到聊天的简历 PDF 不纳入本次保存。

新一轮简历更新及三维工具卡目前仍是设计方案，本次未实施这些改版。

## 当前可下载包

- [成品包，约 6.63 MiB](../release/bottle-ocean-step7-3b31ab385ebfc4cb-site.zip)：完整解压，安装 Node.js 后运行 START-PREVIEW.cmd，或执行 `node scripts/preview-site.mjs --open`；无需安装 npm 开发依赖。
- [源码包，约 6.70 MiB](../release/bottle-ocean-step7-3b31ab385ebfc4cb-source.zip)：最小可重建应用，不包括完整 Git 历史或全部历史证据。
- [包摘要、逐文件清单和验证索引](../release/bottle-ocean-step7-3b31ab385ebfc4cb-manifest.json)。
- [SHA256SUMS](../release/bottle-ocean-step7-3b31ab385ebfc4cb-SHA256SUMS)：在 release 目录中可运行 `sha256sum -c bottle-ocean-step7-3b31ab385ebfc4cb-SHA256SUMS` 核对。

成品 SHA256：`deab7323b2572b244558a7fa49d6ba978b56e4cf7feb822ea2e742954a09b522`。

源码 SHA256：`3431d977b59fc56eb13ed98116ec76b551e87a4daa92fd3f02c967060febd438`。

这两个 ZIP 保持上轮验收字节，未重新封包；独立中文/空格目录解压、全新依赖安装与源码构建已实际通过，69 个重建输出与验收构建逐字节一致。源码和成品中的 README/QUICKSTART 描述其生成时状态；本次仓库保存由本记录与 Git 历史单列，不回改封存文件。原验收报告中的工作区绝对交付路径用于历史追溯，GitHub 下载请使用本页 release 相对链接。

## 仓库源码启动

要求 Node.js >=22.12、npm >=10；验收实际使用 Node.js 24.22.1、npm 11.9.0。完整下载仓库后，Windows PowerShell 在项目根目录执行：

```powershell
npm.cmd ci
npm.cmd run dev
```

macOS/Linux 使用 `npm ci`、`npm run dev`。生产构建和预览为 `npm run build`、`npm run preview`。完整原网页资源已随仓库提供，运行不依赖 GitHub 在线页面或私有仓库，也不使用外部 CDN。

网站通过终端打印的 HTTP 地址访问，不能只双击 HTML。本机 localhost 地址仍然只在同一电脑有效；本次保存仓库未部署公开网站。

## 验证依据与历史

[逐项对照](beach-bottle-boat/step-7-parity.md)、[最终验收](beach-bottle-boat/step-7-verification.md)、[运行指南](beach-bottle-boat/step-7-run-guide.md)、[本次存储清单](bottle-ocean-github-storage.json)。上轮实际采用 68 项原页/内嵌配对检查，Chromium 覆盖全部 34 个原控件和 17 组自然动态条件；Firefox 与 Linux WebKit 为代表范围。成品另完成根/子路径、主站、罗森、庭院、原生下载与阅读返回的验证。

本次上传前复核候选 97 输入、原成品、两包、全部 14 组封存及差异格式；产品未变，沿用上轮实际构建和浏览器证据。原亮度精度、镜头惯性、暂停仍绘制等原语义保持；真机、Windows、Safari、真实后台 hidden 与硬件性能等限制继续按验收报告保留。

封存标准、机器结果、源码副本与包内“未提交/推送/发布”保留当时事实。第二步仅有标准、没有单独执行的历史也不改写。本次只保存 GitHub 仓库，不启用 Pages、不部署、不创建公开 Release。

差异格式核对中，原成品 HTML、历史 diff 上下文和已封存脚本保留了 78 处原始空白记录，逐项归属与摘要见存储清单；其余暂存文件格式检查通过。没有为消除提示改写原文件或封存。
