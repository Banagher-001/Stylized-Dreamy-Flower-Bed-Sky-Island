# 关于我十四步改版：GitHub 保存说明

按用户“上传到 GitHub 仓库”的明确指示，将已完成的改版保存到 [Banagher-001/Stylized-Dreamy-Flower-Bed-Sky-Island](https://github.com/Banagher-001/Stylized-Dreamy-Flower-Bed-Sky-Island) 的 main 分支。准备时间 2026-11-17T23:16:00.101756+08:00。本记录首次加入的提交对应本次保存，准确提交见 [main 历史](https://github.com/Banagher-001/Stylized-Dreamy-Flower-Bed-Sky-Island/commits/main/)。上传前本地与远端基线均为 823da097c4a945f406ef266362822c2626e9251f；采用正常提交与快进推送，保留既有历史。

## 当前内容与验证

站点候选 **about-refresh-step14-6341623c81b6b265**，最新交付 **about-refresh-step14-6341623c81b6b265-r3**。保存身份、经历、制作流程与 22 张三维工具卡；四卡入场、自动横排、轮速与缓冲、倾斜预览、固定阅读、分类、全部工具、输入说明和飞离/返回均已接入。个人介绍不展示项目/奖项；AI 影像保留网页设计样片标记，真实作品后续提供后替换。三项 Coding 的完整网页和返回流程保持。

[第十四步验收](about-refresh/step-14-verification.md) · [最终采用记录](about-refresh/evidence/step-14/adoption.json) · [使用说明](about-refresh/run-guide.md) · [维护](about-refresh/maintenance.md)。

保存前严格构建再次通过，197 个运行输入与最终候选一致，69 个站点输出与冻结构建逐字节相同。沿用本轮实际采用的 14 项路线/交付/持续运行检查和第十三步 161 项既有适配依据，不将上传操作写成重新运行全部浏览器测试。

十分钟原始运行已完成 600.398 秒、21 次采样。末尾误用原生 scrollLeft 的断言原样保留；最终采用已记录的程序轨道位移复核，并补查真实卡片位置变化，不把原始 runner 的误判记录改成通过。完整细节见验收报告。

## 可下载的网页

- [成品包，约 6.68 MiB](../release/about-refresh-step14-6341623c81b6b265-r3-site.zip)：完整解压、安装 Node.js 后，Windows 双击 START-PREVIEW.cmd，无需 npm 安装。
- [源码包，约 6.82 MiB](../release/about-refresh-step14-6341623c81b6b265-r3-source.zip)：源码、锁文件、启动器、轻量说明与本轮脚本。首次使用 npm.cmd ci / npm.cmd run dev（Windows PowerShell），或 npm ci / npm run dev。
- [包清单](../release/about-refresh-step14-6341623c81b6b265-r3-manifest.json) · [SHA256SUMS](../release/about-refresh-step14-6341623c81b6b265-r3-SHA256SUMS)。

成品 SHA256：54c90206c8148268f17ff2c78e36d3db81d2376d970137b695aff9ff29f6a358。源码 SHA256：6fd62b13fb21caa8dbc83495559fb5b8971b47b987105cd6a926c792c6f11d48。两个包保持最终验收时原字节；包内“未上传”和此前报告描述生成时状态，本次保存由本页与 Git 提交单列记录。

## 原始记录保存方式

完整原始证据约 2.3 GB，已逐文件原样封存为 [可选 Git LFS 附件](../release/about-refresh-step14-6341623c81b6b265-evidence.zip)，1,882,630,642 字节（1795.42 MiB），SHA256：d4b9d85b885190e3cd8ec3a47b90490c64d9819ba861e2676acac776c9a46248。附件包含全部 8,836 个原文件，逐项核验大小、SHA256 和 ZIP CRC。旧失败记录、未采用草稿、各步源码快照与录像均保留身份。

[附件清单](../release/about-refresh-step14-6341623c81b6b265-evidence-manifest.json) · [附件 SHA256SUMS](../release/about-refresh-step14-6341623c81b6b265-evidence-SHA256SUMS) · [恢复方法](about-refresh/evidence/README.md) · [仓库保存范围](about-refresh-github-storage.json)。

仓库直接保存各步索引、浏览器结果、最终路线、下载与采样记录，便于查看；其余原始文件从附件恢复原路径。运行网站无需下载大附件。node_modules、临时 dist、缓存及聊天上传的简历 PDF 不作为运行源码保存。此前作品、公共原网页资源、既有验收封存和历史发布包保持。

本次只保存仓库，不启用 Pages、不部署网站或创建公开 Release。测试环境与实机范围继续以验收报告为准。

暂存格式检查中，52 处原始转换日志/封存快照空白提示按原字节保留，逐项位置见保存范围清单；当前应用、预览、测试和交付脚本的格式检查通过。没有为消除提示改写已验收证据。
