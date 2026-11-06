# GitHub保存说明

根据用户“现在你把东西，放到github”的明确指示，把本工作区成果保存到指定仓库：

- 仓库：[Banagher-001/Stylized-Dreamy-Flower-Bed-Sky-Island](https://github.com/Banagher-001/Stylized-Dreamy-Flower-Bed-Sky-Island)
- 分支：`main`；准确提交身份以[该分支的提交记录](https://github.com/Banagher-001/Stylized-Dreamy-Flower-Bed-Sky-Island/commits/main/)为准。
- 上传前远端为空，因此本次为初始提交，没有覆盖已有远端历史。

## 保存范围

`src/`、`public/`、HTML/Vite/TypeScript配置、锁文件、脚本与测试、全部阶段说明及验收证据，以及`release/`内新旧交付包一起保存。`node_modules/`、临时`dist/`、Python缓存和本机配置不提交；成品已包含在静态站ZIP，源码可锁定重建。

第十二步候选为 **step12-95740fb789b56da7**。本次没有修改已验收的应用、素材或锁定依赖，也没有重新封包。最新三份ZIP及其清单仍与第十二步解压复验时逐字节相同：

- [源码包](../release/scroll-garden-step12-source.zip)
- [静态网页成品包](../release/scroll-garden-step12-site.zip)
- [验收证据包](../release/scroll-garden-step12-evidence.zip)
- [SHA-256与解压复验清单](../release/scroll-garden-step12-manifest.json)

为此次仓库保存增加了缓存忽略规则和本说明，并更新根README的存储描述。这些仓库交接信息属于封包后的后续记录；ZIP内README、历史报告及manifest中的“未Git提交/推送”是当时真实状态，不回改历史证明。

## 使用

安装Node24.22.1 / npm11.9.0，在仓库根目录执行：

```bash
npm ci
npm run dev
```

生产构建使用`npm run build`，静态托管上传`dist/`内容。也可解压静态成品包直接通过HTTP托管。默认首页是滚动庭院，`?tour=prototype`兼容旧链接，`?tour=reference`进入旧参考作品集。

操作、媒体替换、静态目录和复验方法见[交付说明](scroll-garden/delivery.md)及[维护说明](scroll-garden/maintenance.md)。真实个人AI影片、职责/分镜和联系方式仍待提供；真机及实际读屏等边界继续按验收记录保留。

此次操作只保存代码与文件到GitHub，没有部署网站、启用GitHub Pages或创建线上发布。
