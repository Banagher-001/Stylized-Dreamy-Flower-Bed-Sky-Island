# 七步增强：GitHub保存说明

本次根据用户“保存到github仓库”的明确指示，将已完成的七步增强保存到[原仓库](https://github.com/Banagher-001/Stylized-Dreamy-Flower-Bed-Sky-Island)的`main`。提交前远端为`4d564f3a79e1e4cc84f9d08b043f9ac5b83c69e3`；保留其历史，以正常提交和快进推送保存。准确提交身份见[main提交记录](https://github.com/Banagher-001/Stylized-Dreamy-Flower-Bed-Sky-Island/commits/main/)。

本轮候选为`garden-enhancement-step7-487410d10d8ad600`，内容包括介绍背景羽化、水球曲面流纹、可随时接管的导览、世界云影、三只飞鸟及最终交付。此次GitHub保存不改动已验收应用和素材，也不重新打包已有ZIP。

## 保存范围

源码、素材、锁文件、构建配置、Windows启动入口、预览/打包工具、测试源码、七步设计/实现/验收文件、全部原始报告和封印记录，以及新旧交付归档均保存。node_modules、临时dist、Python缓存和本地浏览器目录不提交。

| 当前文件 | 保存方式 |
| --- | --- |
| [成品包](../release/garden-enhancement-step7-487410d10d8ad600-site.zip)，1,490,000字节 | 普通Git，可直接从仓库下载 |
| [源码包](../release/garden-enhancement-step7-487410d10d8ad600-source.zip)，2,037,086字节 | 普通Git，可直接从仓库下载 |
| [完整验收附件](../release/garden-enhancement-step7-487410d10d8ad600-evidence.zip)，431,569,189字节 | Git LFS，保留原路径及原字节 |
| [交付校验清单](../release/garden-enhancement-step7-487410d10d8ad600-manifest.json) | 原已签收文件保持 |
| [本次存储记录](../release/garden-enhancement-step7-487410d10d8ad600-github-storage.json) | 后续保存记录，与历史验收分开 |

验收ZIP超过普通Git的100MiB单文件限制，采用仓库本地配置的Git LFS；`.gitattributes`只匹配这一份大包。原始证据目录仍保留，所以封包后才生成的独立解压验证、最终封印和服务记录也保存于Git。尝试附件通道时创建的空草稿已清理，不留下未完成的Release。

完整验收ZIP的SHA256：

```text
84ba8484a445fd24ab9aa22e083f2688d495c4893cfca9a37bab9f09efe10788
```

## 怎样下载和运行

仅查看网页：下载上面的成品ZIP，完整解压，已安装Node LTS24后双击其中`START-PREVIEW.cmd`。要继续修改可用源码ZIP；仓库根目录也有`START-DEV.cmd`。详见[快速上手](garden-enhancement/quickstart.md)。这两个小包使用普通Git，不要求安装Git LFS。

需要克隆全部原始记录及大附件时，安装Git LFS后运行：

```bash
git lfs install
git clone https://github.com/Banagher-001/Stylized-Dreamy-Flower-Bed-Sky-Island.git
cd Stylized-Dreamy-Flower-Bed-Sky-Island
git lfs pull
```

已有克隆可以在仓库中执行`git pull --ff-only`后`git lfs pull`。如果大附件只是以`version https://git-lfs.github.com/spec/v1`开头的小文本，那是LFS指针，尚未取得ZIP本体。GitHub的源码快照ZIP对LFS对象的包含取决于仓库设置；查看和修改网页优先用已验证的成品/源码小包。

## 完整性与状态

上传前独立复核第一至七步共1648个封存文件、92个构建输入和18个产物，SHA均与签收结果一致。源码/成品ZIP也与原交付清单一致。提交索引中的大附件采用LFS指针，本地与LFS对象内容仍保持上述431,569,189字节和原SHA256。

新增的根README、LFS跟踪规则和本次交接记录属于封包后的GitHub保存说明。已签收包、manifest、summary和历史报告中的“未提交/推送”保留当时事实，不回写历史证明。以后重新审计应先取得LFS附件；阶段最终器的旧Git HEAD和before-files属于其原执行边界，不能直接当作今天仓库状态重跑。

本次只保存到GitHub，没有启用GitHub Pages、部署网站或创建公开Release。实体Windows、iOS/Android、硬件GPU、系统字体/安全区和实际读屏等边界继续按[最终验收记录](garden-enhancement/step-7-verification.md)保留。
