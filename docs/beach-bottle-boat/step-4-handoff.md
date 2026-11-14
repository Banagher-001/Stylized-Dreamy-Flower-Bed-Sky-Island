# 第四步交接：第五步完整瓶中海洋现场

第四步完成三作品入口、封面/简介、档案和准确的 prepared/独立打开流程。当前工作区尚未提交 GitHub 或发布；独立网页原字节不变。本步自有测试服务与临时构建产物已清理，已有 dist 未覆盖。第二步仍仅有已细化标准。

| 已落地接口 | 当前行为 |
|---|---|
| projectOrder / ProjectId | lawson → bottle-ocean → courtyard；统一 DOM 与键盘顺序，默认 lawson |
| projects['bottle-ocean'] | 元数据、真实封面、独立网页体验、档案和准备页内容 |
| isPageProject(item) | 明确区分独立网页与主站庭院的数据形状 |
| resolveProjectEntry(id) | 继续 BASE_URL 相对解析，独立打开和未来 iframe 共用入口 |
| setEmbeddedStatus(owner, state, message?) | 仅接受当前同身份独立网页的状态；现有罗森调用已传 'lawson' |
| dialog.dataset.experienceKind | embedded-page 的大尺寸宿主、档案与准备页布局 |
| 正式入口 | experiments/bottle-ocean/index.html |
| 原 HTML SHA256 | 941feb2ea6ddd3cc93aad5b0b92dbca52ee66a3e1098fee0dbf16f01ca63d1ef |

第五步需完成：

1. 新增/配置瓶中海洋专用原页观察规则，使用当前文档的 __bottleOcean、#gl、加载/错误状态与实际 canvas 图形故障。不能把 iframe load、旧 ready 或仅有 canvas 算就绪。
2. 接通当前项目的现场创建/重试/卸载；startTourPrototype.ts 的 syncLawson、retry、dispose 仍只运行罗森。替换/扩展这些路由时保留 wanted、实例/文档归属与过期回调防护。
3. createProjectViewer.ts 的 refreshEmbeddedFeedback 目前仍限定罗森的动态状态；瓶中海洋目前是 prepared。第五步按当前支持的运行器扩展反馈/重试，真实 ready 后隐藏 prepared，不能让错误按钮暂时无处理。
4. 原 H/Space/Escape、滚轮、拖动、沙盒与真实 PNG 下载保留。一个查看器最多一个活动独立网页；原暂停仍绘制，关闭和去档案必须卸载。
5. 复用主站已验证的覆盖暂停、焦点/阅读恢复和导览停止。实际图形丢失后原 ready 可能仍为真，原错误遮罩可能不可见，重试必须使用可信的新文档边界。

第五步无需重做三作品选择、档案或封面；原网页和 PNG 不重构建、不改默认参数。根路径及真实 /portfolio-check/ 前缀独立打开已通过，后续仍要在实际 iframe 中对照原功能和验证输入/生命周期、主站与罗森回归。

本步证据只针对当前入口/档案和独立原页。手机为浏览器触摸模拟，放大条件为根字号测试；实际 hidden、真机及硬件性能未验证。旧封存与本步 after 副本独立保存，允许后续授权修改当前产品源码而不改写这些历史记录。
