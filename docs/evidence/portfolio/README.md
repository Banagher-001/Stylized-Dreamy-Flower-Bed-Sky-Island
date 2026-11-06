# 个人作品集证据

本目录记录第九步之后新增的个人作品集页面，结论见 [验证记录](../../portfolio-verification.md)。

- `verification-{chromium,firefox,webkit}.json`：当前页面每引擎 9 组功能检查。Firefox 保留已知诊断；视频实际播放仅在 Chromium 检查。
- `chromium-{cover,about,works,project,desktop,mobile}.png`：最终封面、介绍、作品编排、档案、整页和手机模拟画面。另两引擎保存相同类型截图。
- `fallback.json`：没有 WebGL 时介绍、导航和项目档案继续可用。
- `clean-build.json`：隔离安装和构建，12 个产物摘要一致。
- `source-preservation.json`：26 个已有源文件保持；renderer 的有限静止帧预算单独说明。
- `media-provenance.json`：概念图来源、压缩资源摘要及原有场景演示视频来源。
- `environment-draft-save.json`：启动说明已保存并读回为草稿修订 5，未发布。
- `summary.json`：当前机器可读汇总。

`first-*` 为早期排版检查，当时整页截图没有触发全部懒加载图片，不能当作最终缺图或最终验收依据。`webkit-mode-*` 与 `webkit-mode-debug.json` 是修复前上一模式残留的排查记录，最终回切与恢复以 WebKit 功能报告为准。

浏览器手机尺寸和 Linux GTK WebKit 都不替代实体手机、Safari 或物理 GPU 验证。设计样片不作为个人实际项目署名。
