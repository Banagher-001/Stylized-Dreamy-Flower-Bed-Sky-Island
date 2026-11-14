# 第五步实际状态与生命周期约定

日期：2026-11-13（Asia/Shanghai）。本文件描述本步实际代码，验收结果另见 [step-5-verification.md](step-5-verification.md)。

## 入口与职责

正式入口是 `experiments/bottle-ocean/index.html`，由 `resolveProjectEntry('bottle-ocean')` 按主站 BASE_URL 解析；查看器与独立链接共用入口。原 HTML、参数、控制台、模拟、渲染、快捷键和下载全部由原网页运行。宿主不向正式原文档注入业务逻辑，不替换原控制，不运行第二条瓶中海洋渲染循环。

| 实际文件 | 归属 |
|---|---|
| createEmbeddedPageExperience.ts | 单 iframe 的创建、重试、文档识别、图形故障锁定、定时观察及清理 |
| createBottleOceanExperience.ts | 只读原瓶中海洋的 API、加载/错误节点和 renderer 判据 |
| createLawsonExperience.ts | 保留罗森工厂接口，提供原 __LAWSON__、#viewport、#fatal、全屏能力判据 |
| startTourPrototype.ts | 根据当前项目与现场/档案切换控制器，先卸载不再需要的实例，再挂载当前实例；复用原覆盖层与阅读恢复 |
| createProjectViewer.ts | 当前作品专属的状态、原大尺寸容器、反馈、重试、独立打开及返回 |
| projectContent.ts | 瓶中海洋动作文案改为“进入完整网页”，准备说明对应当前能力 |

共用接口是 `mount()`、`retry()`、`unmount()`、`dispose()`。`EmbeddedPageOptions` 提供 container、entry、wanted、status；作品 profile 提供 title、canvasSelector、可选 readyEvent 与只读 inspect。容器负责生命周期，profile 不负责创建或销毁原场景。

## 四层归属

1. **作品/标签**：wanted 必须仍为当前作品的 live，查看器状态写入同时核对 owner 与当前标签。
2. **实例**：每次创建/重试有 generation；关闭或切换先使其失效。待创建 RAF、轮询、监听和回调均核对实例归属。
3. **文档**：预期同源 origin/path，忽略初始 about:blank。每个不同 Document 更新 documentGeneration、清理旧文档及 canvas 监听。轮询同时核对文档代号；同 iframe 重载按新文档检查。
4. **画布/图形**：事件核对当前 Document 与 canvas；isContextLost 与原错误信号补充事件。故障锁定属于该文档，不因旧 ready 或 contextrestored 消失。

未跨轮询长期保存原 API/renderer。观察期间只从当前 contentWindow 临时读取。卸载释放宿主保存的 document/canvas 引用及其闭包，原场景由 iframe 文档生命周期结束。

## 实际状态

| 状态 | 本步条件 |
|---|---|
| prepared | 查看器配置后的准备态；进入现场随即转 loading，档案不运行原页 |
| loading | 创建后等待当前真实文档与原场景完成初始化 |
| slow | 本次载入满 12 秒仍无明确成功/失败；首次响应迟到不重置计时 |
| ready | 当前原文档、原画布、首帧、加载及错误组合通过 |
| error | 错误文档、明确初始化错误、加载后不可访问/无法确认，或本次文档已发生图形故障 |

后续真实文档替换重新计时；slow 可以自然转 ready，不自动循环重试。loading/slow 约 200ms、ready 约 500ms 观察；原 ready 事件、iframe load、主站 pageshow/可见返回只触发复核。

瓶中海洋 ready 要求同时满足：

- `__bottleOcean.ready === true`，无 `__bottleError`，`#loader-error` 无错误文字；即使原错误遮罩不可见也读取文字。
- 当前连接的 `canvas#gl` 与原 renderer.domElement 相同，CSS 和像素尺寸有效。
- 从原 renderer.getContext() 读取的上下文未丢失，原 diagnostics.renderer.calls 和 triangles 均大于零。
- 原 `#loader` 的计算 display 为 none，当前文档无已锁定图形故障。

暂停模拟时仍可 ready，不要求 simTime 一直增加。宿主不为了检测而创建新上下文。单独的 load、ready 标志、存在 canvas 或宿主封面都不足以宣布成功。

## 图形故障与重试

`webglcontextlost` 或原上下文实际丢失锁定 error。真实 `webglcontextrestored` 只更新提示为“图形连接已恢复，请重新载入场景”，不解除锁定。原版没有可靠的新图形代就绪契约，原 ready 及 __bottleError 也可能保留旧值；新文档是可信恢复边界。

原重试按钮执行旧实例 unmount 后 mount，最多一个 iframe。真实文档重载也解除旧文档监听、故障锁定并重新检查。错误/慢载入仍可去档案、返回或独立打开。

## 尺寸、输入和清理

等待 showModal 完成且容器有有效布局后创建 iframe；沿用大尺寸查看器，宽高填满宿主工具栏和安全区以外的区域。没有固定 1920×1080、整页 transform 缩放或宿主控制台覆盖层。原 resize 跟随实际子视口。

原页 H、Space、Escape、鼠标/触摸由原页接收；子页有焦点时 Escape 不关闭宿主。宿主工具栏有焦点时 Escape 走返回。PNG 来自真实原按钮，尺寸为 canvas CSS 尺寸 × min(DPR,2)，内容仅为原 WebGL 场景。

unmount 顺序：使 generation 失效 → 取消待创建 RAF/定时器 → abort 实例、文档、canvas 监听 → 清空宿主持有的文档/canvas 引用 → 释放该实例持有的指针锁/全屏 → 移除 iframe。dispose 幂等。档案往返重新使用原默认值；不以隐藏或原暂停代替卸载，不擅自关闭独立窗口。

作品覆盖复用 beginOverlay/closeOverlay、covered、syncLoop 和既有阅读快照。覆盖时庭院保留原上下文及状态并停止持续绘制；返回按原阅读/焦点与动效选择恢复，导览保持停止。不宣称 GPU 内存同步归零，或覆盖时只剩一个图形上下文。

正式产品不覆写可见性或时钟。浏览器测试中的只读绘制计数、真实输入、受控网络延迟和图形故障均限于测试上下文，原始脚本另存每次运行目录。
