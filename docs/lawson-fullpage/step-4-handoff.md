# 第四步交接：第五步原网页实例接入

第四步完成的是正式主站宿主，实际验收见 [第四步验收](step-4-verification.md)。当前原页可独立打开，作品层仍显示准备态；第五步尚未开始。

## 1. 已实现模块与唯一状态

`src/tour/projectContent.ts` 导出：

```ts
type ProjectId = 'lawson' | 'courtyard';
type ProjectTab = 'live' | 'archive';
interface ActiveProject { readonly id: ProjectId; readonly tab: ProjectTab }
type EmbeddedProjectState = 'prepared' | 'loading' | 'slow' | 'error' | 'ready';
projects;
resolveProjectEntry(id: ProjectId): string | undefined;
```

真实相对入口为 `experiments/lawson/index.html`，按 Vite `BASE_URL` 和 `document.baseURI` 解析。根目录与仓库同名子路径已验证；返回庭院时 URL 为 undefined。iframe 必须复用这个解析函数，不另写固定根路径或私有 GitHub 地址。

`src/tour/createProjectViewer.ts` 的实际公开对象：

| 接口 | 当前行为及第五步用途 |
|---|---|
| `open(id, tab, source?)` | 配置身份、停止/保存阅读所需生命周期、打开唯一 dialog；跨项目先关闭再配置 |
| `close()` | 关闭并同步完成宿主退出，原排队 close 事件不会重复恢复 |
| `active`，只读 getter | 打开期间返回新的 `{id, tab}` 快照；关闭/销毁后 undefined。第五步以此判断是否应挂载 |
| `embeddedMount`，只读 getter | `.tour-project-embed-mount`，始终为同一个 HTMLElement；准备态是相邻节点，容器当前为空 |
| `liveBounds`，只读 getter | 原 `.tour-project-live-space` 的 bounds，仅供庭院构图；不是罗森挂载区尺寸 |
| `element`，只读 getter | 唯一 `.tour-project-dialog` |
| `setEmbeddedStatus(state, message?)` | 更新宿主 `data-embedded-state`、工具栏状态；只有 prepared 显示准备卡片。关闭或非罗森时忽略 |
| `sync(mode, playing, unavailable?)` | 继续只同步主庭院的模式/动效和可用性，不用它表示原页状态 |
| `dispose()` | 取消监听、焦点回调、档案媒体及宿主 DOM；第五步需要先释放原页实例 |

`setEmbeddedStatus` 不负责创建 iframe、加载观察、错误遮罩或重试控件，也不替管理器判断是否仍在 live。第五步必须自己检查 active、实例代次及当前文档；不能直接让旧 ready/error 回调更新它。

## 2. 生命周期实际时序

创建查看层时传入的回调为 `open(project)`、`change(project)`、`close()`、`mode(mode)`、`motion()`。主站当前在 open/change 调用 `syncProject()`，close 调用 `closeOverlay('project')`。

首次打开顺序：身份和 engaged → configure → select(tab, false) → `lifecycle.open(active())` → `dialog.showModal()` → 聚焦返回。open 回调时挂载节点已存在于 DOM，但 dialog 尚未 showModal；依赖可见尺寸的工作应等布局完成，并再次校验活动身份/代次。

切页签：保存/清理档案媒体 → 设置当前 tab 与 hidden → 初始化当前项目档案或恢复滚动 → `lifecycle.change(active())`。关闭：关闭 dialog → 视频释放 → engaged=false → `lifecycle.close()` → 阅读恢复 → 下一帧安全恢复焦点。读取 active 必须以当前 getter 为准。

第五步可在这三个入口追加一个原页实例协调函数：

```text
active?.id === 'lawson' && active.tab === 'live'  → 按需 mount
其他项目 / archive / closed / dispose           → 失效旧回调并 unmount
```

一个 manager 持有实例、代次、计时器/观察；不要在主站复制一套会漂移的 activeProject 状态。主站现有覆盖门控已让罗森 live、任一 archive 实际停绘，独立打开不会恢复主庭院绘制。

## 3. 已保留的原网页及约束

原运行文件在 `public/experiments/lawson/`，构建副本在 `dist/experiments/lawson/`：46 文件、20,332,784 字节，全部与源版本逐字节一致。源使用自己的本地 Three.js r160；主站 0.187.0 继续隔离。

第五步使用描述性 iframe title、100% 内容区域和原生全屏允许，保留原网页 CSS、JS、控制台和全部资源。不添加会限制原功能的 sandbox，不注入桥接脚本，不改变原画质/时间/任务，也不把截图当作内嵌运行。当前 CSS 已给 `.tour-project-embed-mount > iframe` 全宽全高，无固定比例或缩放。

实例管理器需实现幂等 mount/retry/unmount/dispose。只在罗森 live 创建一次；离开 live 清理，不能把原 `pauseAll` 当作原页停绘。原页重试刷新当前 iframe 文档，观察须重新取得 document/API，并使旧文档信号失效。

## 4. 第五步实际待验证项

沿用第二步 [接口契约](step-2-interface.md)：错误优先读取原 fatal、`__LAWSON__.error` 和 body 标记；只有当前原 `__LAWSON__.ready === true` 且无错误才算 ready，HTML load 不等于就绪；约 12 秒为 slow，等待不能伪造成确定失败。loading/slow/error 时保留返回与独立打开。

宿主已在 cancel 分支保留“焦点位于 embeddedMount 内时不关闭整个作品”。本步没有真实 iframe，该分支尚未验明原锁定/全屏/Esc。第五步应验证真实用户手势、滚轮/键盘隔离、原 retry 文档替换、关闭/快速开关后的过期回调、锁定/全屏清理，以及 iframe 到档案的资源释放。

完成接入后再验证两套 WebGL 不并行持续绘制、原页完整功能、真实错误/慢载入、各尺寸阅读恢复；第六/第七步继续设备及原功能对照回归，不把独立打开已成功等同内嵌已完成。

## 5. 保护范围和可复查资料

第四步 6 个既有主站输入修改、3 个新增产品文件详见 [integrity.json](../evidence/lawson-fullpage-step-4/integrity.json)，其余 85 个输入保留。前四组封存 77/109/115/95 文件与原 46 运行文件保持原样。不要重新执行旧 finalizer，也不要回写旧报告以匹配新代码。

本步把验收时的源码副本封存在证据目录的 `after/`，不依赖未来会继续修改的工作源码路径。后续新增下一步基线，区分当前代码与本步副本，不回写本步副本，也不把正常后续变化误报成原页损坏。

机器交接见 [step-5-handoff.json](../evidence/lawson-fullpage-step-4/step-5-handoff.json)，本步检查脚本在 `tests/lawson-fullpage-step-4/`。当前未提交、推送或发布。
