# 关于我改版验收记录

本目录直接保留各步索引、构建身份、浏览器结果及第十四步最终采用的完整路线和采样记录。

全部原始截图、录像、脚本、源码副本、中间失败记录与未采用草稿共 8,836 个原文件，保存在 [Git LFS 完整附件](../../../release/about-refresh-step14-6341623c81b6b265-evidence.zip)。[逐文件清单及 SHA256](../../../release/about-refresh-step14-6341623c81b6b265-evidence-manifest.json)核对附件内容。此前步骤报告引用的未直接展示文件，可从该附件恢复原路径。

运行或修改网页只需要源码/成品，不需要完整验收附件。需要恢复全部历史记录时，在仓库根目录执行：

```bash
git lfs pull --include="release/about-refresh-step14-6341623c81b6b265-evidence.zip" --exclude=""
python -m zipfile -e release/about-refresh-step14-6341623c81b6b265-evidence.zip .
```

Git LFS 附件需先取得实际大文件，不能将小型指针文件当作 ZIP 解压。解压会恢复 docs/about-refresh/evidence/ 原路径；另有两份附件自身的清单与说明。原始失败记录、草稿状态和“未上传”描述保留各自生成时事实，当前仓库保存见 [GitHub 交接](../../github-about-refresh-handoff.md)。
