# 第五步交接：设备、异常与最终原版回归

第五步已把完整原页面按需接入，验收见 [第五步验收](step-5-verification.md)。第六步从现有实现做设备和异常加固，无需重新搭建 C2、查看层或重写原网页。

## 1. 当前入口和所有者

`projectContent.ts` 的 resolveProjectEntry 继续提供同源真实入口。C2、独立打开和 iframe 采用同一地址规则。

`startTourPrototype.ts` 创建一个 `createLawsonExperience` 管理器，传入 container、entry、wanted 和 status。wanted 从查看层 active 派生；没有第二套活动项目状态。open 先 beginOverlay/syncProject，再 mount；change 先按身份 mount/unmount 再同步；close 先 unmount，再 closeOverlay；主站 dispose 先释放原页。

## 2. 管理器实际接口

| 方法/输入 | 实际行为 |
|---|---|
| mount() | 仅 wanted 时工作；有实例或挂载帧则不重复；先 loading，下一帧在有效可见挂载节点创建原 iframe |
| retry() | wanted 且未 disposed 时，先 unmount 再 mount，替换实例 |
| unmount() | 实例代次失效、取消挂载帧/定时器/监听、退出所属锁定或全屏、移除 iframe |
| dispose() | 最终标记后 unmount；后续 mount/retry 无效 |
| container | 第四步稳定的 embeddedMount |
| entry | 原 resolveProjectEntry('lawson') 的结果 |
| wanted() | 当前确实是 lawson/live 且主站未销毁 |
| status(state) | 转交查看层 setEmbeddedStatus；不写原页面状态 |

iframe 有描述性 title、`allow="fullscreen"` 和 allowFullscreen，无 sandbox；原页加载、控制台、默认时间/画质、模型与本地 Three 保留。生产管理器只读取原状态，不调用原业务 API，不插入桥接脚本。

## 3. 状态观察与文档更新

实例代次属于管理器，每个实例还有 documentGeneration。每次 observe 重新取 contentDocument/contentWindow/API，遇到新文档重置等待起点。轮询在等待阶段约 200ms、ready 后约 500ms；load 会立即再观察。单一当前计时器受实例、文档代次及 timer 身份保护。

原 fatal 实际显示、API error 或 body error 优先，当前 API ready 才成功。约 12 秒仍无确定结果为 slow。原重试刷新 iframe 文档，宿主重试替换 iframe。原 30 秒 guard 的 fatal 没有 API error 时也能被识别；fatal 仍显示时，后来的 ready 不会掩盖错误。

目前没有可靠原信号的 HTML/模块等待按 loading/slow 处理，不凭 iframe load 或单个 onerror 猜测 HTTP 成功/失败。第六步继续细查文档失败、网络限制等边界，不能用额外状态模拟替代实际故障。

## 4. 宿主反馈、输入与退出

查看层新增 lifecycle.retry 回调、重试按钮和工具栏反馈行。slow/error 显示，档案/其他作品/ready 隐藏。反馈自然增加工具栏高度，原页占剩余区域；没有覆盖原控制台或原重试。正常桌面/手机仍为 56/48px 工具栏。

原页滚轮、拖动和键盘已经核查；原全屏、漫游锁定及真实 X11 Esc 已验证。所属子文档才是 pointerLockElement 的可靠读取位置，本次浏览器的父文档 getter 为 null，不能据此误报锁定失败。宿主 cancel 在焦点位于 iframe 挂载区域时保留原浏览器行为。

离开 live 会销毁原实例，再进按原默认状态运行；当前不保存退出前的镜头、时间、屋顶或车辆设置。卸载先于庭院恢复，保留原暂停/播放、阅读锚点和焦点，导览由访客手动继续。HMR dispose 已接入管理器；本步未将实际开发热更新流程列为已完成浏览器用例。

## 5. 第六/第七步承接项

第六步优先核对实际设备/浏览器、触摸与安全区、原移动界面既有布局、网络失败/慢载入、连续所有者切换、后台与可见性、恢复后焦点和原生权限差异。原页面的移动端局限和已知问题保持明确，不能以宿主已可用宣称原页移动能力全部补齐。

目前已验证关闭/档案卸载，没有把原 pauseAll 当作停绘接口；原实例保持打开但整个浏览器标签隐藏时，仍保留原页自己的行为，原 JS 的后台停绘不在本步做改写。第六步对实际结果继续记录。

第七步按照 feature-matrix 的原 41 控件与 17 类点击逐项对照，包含原已知问题。不得把基本控制台核查和源码字节一致直接替代完整交互回归。原文件仍为 46 个固定运行文件，新增控制功能或修复原页问题需有明确范围。

## 6. 证据与保护

源码前后副本、实际 diff、构建输入/输出哈希、网络/绘制计数、失败尝试与 15 组通过索引在本步证据目录；机器交接为 `docs/evidence/lawson-fullpage-step-5/step-6-handoff.json`。

本步封存 after/ 中的源码副本，后续可按下一步授权修改工作源码，不能回写副本或重跑旧 finalizer 覆盖结果。旧五组封存及源/public 原 46 文件保持原样。未提交、推送或发布。
