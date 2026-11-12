# 第二步接口契约：作品身份、原网页及生命周期

本契约已设计定稿，宿主代码在第四步实现，原页实例在第五步挂接。样稿脚本是独立演示代码，不直接复制为正式主站控制器。

## 1. 作品身份

```ts
type ProjectId = 'lawson' | 'courtyard';
type ProjectTab = 'live' | 'archive';
type ProjectExperience =
  | { kind: 'host-scene' }
  | { kind: 'embedded-page'; entryPath: 'experiments/lawson/index.html' };

interface ActiveProject {
  id: ProjectId;
  tab: ProjectTab;
}
```

作品注册表拟放 `src/tour/projectContent.ts`，提供 id、名称、类型、摘要、封面、档案及 experience。复用当前庭院资料和媒体，不丢弃现有视频/帧图。C1/C3 仍由 `experimentContent.ts` 管理，C2 根据注册表取当前作品。

`selectedProjectId` 属于展位，默认 lawson，关闭后保留。`activeProject` 属于唯一作品层，关闭后为空。以 activeProject 为统一来源派生 tab 和渲染条件，不维护互相冲突的多份作品状态。

公开打开调用定为 `open(projectId, tab, trigger?)`；切页签只改变当前作品的 tab。体验层内部不切项目，换项目先返回 C2。

## 2. 模块责任与接入点

| 模块 | 后续实现责任 |
|---|---|
| `projectContent.ts`（拟新增） | 两个作品的数据和运行类型 |
| `createExperimentReader.ts` | C2 选择、预览、携带身份的打开回调、图像失败占位 |
| `experimentReading.ts` | C2 显示标签改为“交互作品”，保留 ID、区间和 stop |
| `createProjectViewer.ts` | 唯一 dialog，按身份取标题/档案，罗森紧凑布局、焦点和 cancel |
| `createLawsonExperience.ts`（拟新增） | 按需创建、观察、重试、卸载原 iframe；第五步实现 |
| `startTourPrototype.ts` | 停绘、导览、媒体互斥、保存/恢复及 activeProject 协调 |
| `createReadingLayout.ts` / `readerFlow.ts` | 稳定阅读完整入口、按作品判断可用性及容量复测 |
| `experiment.css` 或独立宿主样式 | 选择器限定在 C2/作品层，罗森模式与庭院模式分别处理 |

当前 `createProjectViewer.ts` 固定导入庭院项目，`startTourPrototype.ts` 的 live 代表复用庭院画布。后续必须检查以下全部关系：covered、offscreen、syncLoop、experiencePose、applyCamera、体验区域 resize 和读取面板的隐藏。它们不能只凭 live 判断，须同时检查作品 ID。

## 3. 运行路径与构建

```text
source: /workspace/luosen-asset/lawson-blender/out/web_final/
target: public/experiments/lawson/
build:  dist/experiments/lawson/
entry:  experiments/lawson/index.html
```

入口由一个函数按 Vite 网站 base 解析，iframe 和独立链接共用。当前配置为 `base: './'`；应以 `import.meta.env.BASE_URL` 和当前站点文档位置正确解析，不能固定为 `/experiments/...`。根目录、`/portfolio/` 等子路径需用实际构建输出验证。

项目内容为可信的同源原网页，保留独立文档、原 import map 和本地 Three.js r160。主站 three 0.187.0 不参与原页模块解析。原 CSS、JS 与模型相对路径不改写，不向访客暴露私有仓库 raw 地址。

## 4. 原页实例契约

实例管理器的职责范围为：

```ts
mount(): void;     // 当前 live 需要时创建，重复调用不再增加实例
retry(): void;     // 先失效旧实例，再建立同一入口的新实例
unmount(): void;   // 失效观察、计时器和实例，再移除节点
dispose(): void;   // 最终清理，后续回调不能重建
```

同一时刻最多一个罗森 iframe。创建发生在进入罗森 live 后，封面浏览、庭院体验及罗森档案都不创建。iframe 具有描述性 title、100% 内容区宽高、原生全屏允许；用户手势按原页逻辑获取鼠标锁定。受控同源原页不附加限制其功能的 sandbox，不写不存在的 `pointer-lock` Permissions Policy 指令。

宿主不调用 hideUI、改变画质/时间、强制店员任务或重排原控制台。`pauseAll` 不是停绘接口，离开现场使用卸载。不能仅凭卸载宣称 GPU 内存立即释放。

## 5. 就绪、错误、重试与过期回调

只读取当前 iframe 当前文档的已有状态，不改原文件，也不加入消息桥：

1. 首先检查实例代次、当前来源窗口及挂载状态，旧结果立即忽略。
2. 每次观察重新取得当前 document 和 `window.__LAWSON__`，不缓存重试前的 API 对象。
3. 原 `#fatal` 实际显示、`__LAWSON__.error` 有值，或 `body.dataset.ready === 'error'`，均判为原页错误。错误优先于曾经的 ready。
4. 当前 `__LAWSON__.ready === true` 且无原 fatal，才判为 ready。
5. iframe load 仅代表文档事件；没有原就绪信号时继续 loading，约 12 秒后 slow。
6. 无法确认的等待不伪造确定失败。出现明确文档失败才进入 error；返回及独立打开持续可用。
7. 原页重试按钮会刷新 iframe 自己的文档。新的 load/document 使旧文档观察失效，重新从 loading 等待，不需要重新注入脚本。
8. 宿主重试则清理旧 iframe，增加实例代次并重新挂载；关闭或切档案时先失效回调再移除。

原页超时守卫可能只显示 fatal，而没有填写与模块错误完全相同的标记，因此必须读原错误界面；不能只检测一个 API 字段。真实慢载入、HTML 失败、模型失败和原重试将在第五/第六步验证，第二步状态菜单只是布局演示。

## 6. 宿主绘制和返回

| 活动内容 | 主庭院绘制 | 罗森实例 |
|---|---|---|
| 普通阅读 | 主站既有条件 | 无 |
| 庭院 live | 现有庭院 live 条件 | 无 |
| 罗森 live（包括加载和错误） | 停止 | 最多一个 |
| 任一作品 archive | 停止 | 无 |
| 关闭作品 | 恢复打开前设置 | 无 |

沿用现有 beginOverlay/closeOverlay、媒体互斥和 readingLayout.capture/restore。打开停止 guide，关闭不自动重新启动。恢复原 animation.playing，不强制播放；重置主站时间戳避免关闭后跳帧。

同一视口下恢复原滚动和锚点；视口、字号、稳定阅读模式变化后按保存锚点与段内比例恢复。按钮仍连接时焦点还原触发项，其他情况回退到所选作品或 C2 标题。

## 7. 输入和可用性

宿主原生 dialog 的 cancel 必须区分焦点：焦点在 iframe 内时不关闭整个作品，原 Esc 继续退出锁定/全屏；焦点在宿主可交互控件时可关闭。不要为了解决此事向子页添加全局键盘拦截。真实浏览器边界由第五/第六步检验。

关闭/路由清理时也要处理仍持有的浏览器锁定/全屏状态；使用原生浏览器退出或移除释放机制，不能替换原场景逻辑。普通打开时先聚焦外层返回，再由访客点击原场景获取输入。

庭院故障只影响庭院 live。罗森入口可尝试独立加载并按其实际结果反馈；不能因为主庭院 failed 就一并 disable 罗森。档案、返回及独立打开保持可用。

## 8. 第四/第五步验收所需真实案例

第二步只锁定这些验证目标，没有提前声称通过：主庭院真实停绘计数、iframe ready/error、原页重试导致文档更新、快速关闭的旧回调、原 41 控件与 17 类点击、真实全屏/锁定/Esc、滚轮隔离、背景可见性、手机实际能力及返回阅读的跨尺寸恢复。
