# 个人作品集扩展：验证记录

当前页面已从独立庭院作品扩展为 sakan / 张辰翰的个人作品集，保留动态封面，增加真实个人介绍、作品策展展示、筛选、档案、视频与画面切片。设计与内容来源见 [设计说明](portfolio-design.md)。

## 本轮实际检查

| 检查 | 结果 |
| --- | --- |
| 严格 TypeScript 与 Vite 生产构建 | 通过，未变更依赖和锁文件 |
| Chromium 155.0.8059.79 | 9 组通过，无警告、异常或 HTTP 失败 |
| Firefox 153.0 | 9 组通过，保留 5 条已知 PCF/故障注入日志，未识别问题 0；不声称零警告 |
| Linux GTK WebKit 26.5 | 9 组通过，无警告、异常或 HTTP 失败；不是 Safari 实机 |
| 真实滚动离开封面 | 三引擎 GPU 绘制计数与场景时间停止增长，返回无时间快进，手动暂停状态保留 |
| 模式切换与暂停恢复 | 检查实际呈现画面发生模式变化，切回像素后画面完全一致；强制丢失/恢复后仍一致 |
| 分类与项目档案 | 全部/视觉/交互显示 3/2/1 项；三件项目均可键盘打开、焦点留在弹窗内、Escape 关闭并返回入口 |
| 视频与分镜 | 原生播放器与画面切片存在；视频首屏不请求，Chromium 中实际解码播放为 12 秒、关闭后暂停 |
| 响应式 | Chromium 8 组视口/DPR，Firefox/WebKit 各 2 组；无水平溢出，主要导航、模式、暂停和分类目标 ≥44×44 CSS 像素 |
| 无 WebGL | 封面显示可读错误，3 个场景按钮禁用；介绍、导航、分类和作品详情继续可用，无未处理异常 |
| 隔离安装构建 | 新目录不复用原 node_modules，重新 npm ci 与构建，12 个静态文件 SHA-256 相同 |
| 场景源文件保护 | 26 个已有场景/配置/动画/材质文件逐字节保持；renderer 仅调整暂停呈现预算，未修改场景或取样算法 |

视频播放仅在 Chromium 实测；Firefox/WebKit 本轮记录 `canPlayType` 与媒体结构，未把未执行的解码/停播计入通过。手机尺寸为浏览器模拟，没有实体手机或物理 GPU 帧率验收。既有第九步的硬件/原生 OS 缺口继续保留，没有因为扩展作品集而转为已通过。

## 视口与修复证据

Chromium 代表性组合：280×600 DPR1、320×568 DPR1、390×844 DPR2、760×1000 DPR1.25、768×1024 DPR1.5、1024×768 DPR1、1920×1080 DPR2、844×390 DPR3。另两引擎为 390×844 DPR2 与 1440×1000 DPR1。并非所有排列的遍历，也不是实体触屏测试。

WebKit 暂停模式回切曾出现「模式标签已经改变，但合成器仍呈现上一模式」的情况，单纯等待不会修复。实际记录显示场景时间仍为 2 秒、输出仍为 680×680；补一次绘制后画面恢复一致。现通过有限的两帧提交预算解决，随后不持续绘制。新检查同时要求正常/像素画面确实不同、回切后像素画面相同，避免仅检查标签而漏过呈现问题。

所有测试使用 Linux 云机器的软件图形环境，软件诊断不能说明 Apple GPU 或真实 Safari 行为。Firefox 深度比较提示继续原样保存。应用没有测试探针全局变量；计数探针仅由 Playwright 在测试上下文注入。

## 本地证据

- [Chromium 结果](evidence/portfolio/verification-chromium.json)
- [Firefox 结果](evidence/portfolio/verification-firefox.json)
- [GTK WebKit 结果](evidence/portfolio/verification-webkit.json)
- [无 WebGL 结果](evidence/portfolio/fallback.json)
- [隔离构建](evidence/portfolio/clean-build.json)
- [场景保护摘要](evidence/portfolio/source-preservation.json)
- [媒体来源与样片状态](evidence/portfolio/media-provenance.json)
- [封面截图](evidence/portfolio/chromium-cover.png)
- [个人介绍截图](evidence/portfolio/chromium-about.png)
- [作品编排截图](evidence/portfolio/chromium-works.png)
- [手机尺寸截图](evidence/portfolio/chromium-mobile.png)
- [项目档案截图](evidence/portfolio/chromium-project.png)

本轮原始检查工具见 [tests/portfolio](../tests/portfolio/README.md)。本轮未将历史第九步报告覆盖为当前结果，也未重复耗时的旧十分钟测试来替代页面检查。

## 交付状态

当前个人作品集在 `release/portfolio-source.zip`、`release/portfolio-site.zip` 和 `release/portfolio-manifest.json` 中交付；旧 `courtyard-*` 保留为历史快照。启动说明同步至当前云环境草稿。未发布、部署、创建 Git 提交或推送到 GitHub。
