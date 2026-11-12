# 第四步验收：双作品入口、正式宿主与庭院恢复

第四步已完成：真实主站的第三根柱子可选择罗森或庭院；罗森具有占满视口的大尺寸作品层、独立打开和项目档案；作品覆盖时庭院实际停绘，返回保留阅读位置及播放设置。

当前罗森现场显示“完整网页可独立打开，嵌入体验正在准备。”。完整原网页可从真实链接独立运行；将它放进当前作品层是第五步。本步没有创建 iframe，没有把准备态记为原页加载或就绪。改动仅在工作区，未提交、推送或发布。

## 1. 实际实现

| 位置 | 完成内容 |
|---|---|
| `src/tour/projectContent.ts`，新增 | `lawson` / `courtyard` 注册表、共用身份/页签类型、相对站点 base 的真实原页 URL 解析 |
| `src/assets/lawson-cover.png`，新增 | 第二步确认的真实罗森截图，原字节复制，429,796 字节 |
| `src/tour/createExperimentReader.ts` | 默认罗森、双作品选择、单份预览、带身份的打开回调、方向键/Home/End、封面请求归属及稳定阅读可用性 |
| `src/tour/experimentReading.ts` | 仅将 C2 显示标签更新为“交互作品”，保留 ID、9.5–10.5 区间和 stop 10.05 |
| `src/tour/autoGuide.ts` | C2 导览提示同步为“交互作品”，不改停留时长或逻辑 |
| `src/tour/createProjectViewer.ts` | 单一作品 dialog、罗森准备态与稳定挂载区、真实独立入口、分作品档案、焦点和媒体清理 |
| `src/tour/projectHost.css`，新增 | C2 选择及正式作品层样式、56/48px 工具栏、大字号自然换行、移动端及减少动态适配 |
| `src/tour/startTourPrototype.ts` | 从查看层活动快照派生绘制状态、覆盖停绘、明确庭院入口、导览停止及阅读恢复 |
| `src/tour/createMediaViewer.ts` | 旧影像层关闭后的延迟焦点恢复检查当前模态所有者，避免干扰新打开的作品层 |

最后一项是在媒体互斥检查时确认需要的关联修正；最终文案检查也同步了导览提示与主画布的可访问说明。原 `readerFlow` / `createReadingLayout` 无需改写：在 flow 保存/恢复属性后重应用当前作品可用性，继续复用原 capture/restore、容量检测和锚点规则。场景、renderer、水球、鸟、云影、路由数值和既有作品资料未改。

C2 article 和预览容器保持原 DOM 身份；切作品时只替换封面图节点并更新文字。封面监听归属于当前图节点，并在换图时取消，旧图的 load/error 不能更新新作品状态。导览的图片解码记录也按当前资源判断。

## 2. 调用链和资源所有者

- C2 调用 `open(projectId, tab, trigger)`；稳定阅读水潭入口显式传 `courtyard`，不跟随 C2 当前选择。
- 查看层的 `active` 是活动作品的权威来源；主站不再维护另一份 `projectTab`。只有 `courtyard + live` 使用庭院现场构图。
- `covered`、`offscreen`、`syncLoop`、`applyCamera`、鸟的构图和体验区域 resize 均按作品身份判断。覆盖使用原 `setSuspended` / `setAnimating`，不强制修改访客的播放选择。
- 作品和影像层沿用同一 overlay capture/restore；开作品停止导览，关闭不自动继续。两者关闭后的焦点回调均检查是否有新模态框。
- 两种档案分别初始化；庭院保留完整介绍、功能、12 秒片段和两幅早期帧图。切页签保留档案滚动，离开清理视频和旧媒体回调。切作品重建档案并取消旧图片监听。

## 3. 构建与真实页面核查

最终 `npm run build` 成功，包含 `tsc --noEmit`；`git diff --check` 通过。最终日志为 [build-5.log](../evidence/lawson-fullpage-step-4/build-5.log)，构建输入/输出哈希见 [build-result.json](../evidence/lawson-fullpage-step-4/build-result.json)。此后没有修改产品源码。

真实构建通过 HTTP 在根目录和 `/Stylized-Dreamy-Flower-Bed-Sky-Island/` 下核查。浏览器为 Chromium 155.0.8059.79，以有界面模式运行 Mesa 软件 WebGL；不是第二步静态样稿。

18 组验收全部通过，索引见 [accepted-browser-results.json](../evidence/lawson-fullpage-step-4/accepted-browser-results.json)：

| 类别 | 实际结果 |
|---|---|
| 入口、身份与原庭院 | 默认罗森；键盘切庭院；两种档案身份正确；庭院视频实际播放，切现场后视频移除；正常/像素模式和动效可用；水潭固定庭院；5 次交替开关后无打开模态框或视频遗留 |
| 导览、停绘和返回 | 运行中导览在选择/打开时停止，关闭后不自启；罗森现场及档案连续至少 1 秒 WebGL draw 计数为 0；覆盖状态 resize 后再次计数为 0；播放与暂停起点均保留；同视口滚动/焦点恢复，缩小至手机后返回稳定阅读 C2 |
| 旧封面回调 | 等待真实封面载入后，在已退休的图片上注入 load/error，当前作品和封面状态不被覆盖；Home/End 可切换 |
| 媒体互斥与键盘 | 强制快速双向所有者交接后仅一个模态框，焦点属于新窗口；Tab/Shift+Tab 可遍历，Esc 关闭后滚动锁清除 |
| 常规布局，7 组 | 1920×1080、1440×900、1366×768、768×1024、390×844、320×568、844×390 均符合下表 |
| 大字号，2 组 | 390×844、320×568 在根字号 32px 下换行，按钮保持至少 44×44，档案可滚动、页签切换保留档案位置、返回无横向溢出 |
| 减少动态 | 宿主无新增动态过渡，阅读/准备态/档案/返回可用 |
| 故障，2 组 | 主站 WebGL 获取失败时，罗森入口、准备态和档案继续可用，仅庭院现场禁用；封面请求失败不封死入口 |
| 真实独立打开，2 组 | 根目录及项目子路径均打开实际原页，`__LAWSON__.ready` 为 true、无 fatal/error，新标签 `window.opener === null`，主站继续停绘 |

在最终构建上的主页面网络记录中，罗森 runtime 请求为 0，iframe 数量为 0；独立打开的新页面才请求原运行文件。主页面没有未捕获异常、意外 HTTP 错误或意外请求失败；封面故障请求是显式注入的预期失败。

过程记录保留在 run-1/2/3/4/5：首次稳定阅读定位器匹配了两个节点，随后一项恢复断言使用了 `playing`，实际既有状态名称为 `running`；文案检查也将隐藏 tooltip 的 innerText 改为读取实际按钮 title。这些均修正于检查脚本，未覆盖失败记录，也未为修正断言改变产品行为。build-4 上 18 组分别在 run-2（17 组）和 run-3（1 组）通过；最终 build-5 仅改两处文字说明，精确差异见 [label-audit/result.json](../evidence/lawson-fullpage-step-4/label-audit/result.json)，并在 run-5 重新通过导览/缩放/恢复组及新文案断言。最终索引采用 run-2 的未受影响 17 组与 run-5 的 1 组。

## 4. 实测尺寸与截图

| 视口 | 工具栏高度 | 罗森内容区 |
|---|---:|---:|
| 1920×1080 | 56 | 1920×1024 |
| 1440×900 | 56 | 1440×844 |
| 1366×768 | 56 | 1366×712 |
| 768×1024 | 56 | 768×968 |
| 390×844 | 48 | 390×796 |
| 320×568 | 48 | 320×520 |
| 844×390 | 48 | 844×342 |

200% 根字号下，390 宽工具栏自然长为 57px，320 宽为两行 115px；内容区使用实际剩余高度。没有用固定比例、最大卡片宽度或 scale 缩小挂载区。

- [真实 C2 罗森入口](../evidence/lawson-fullpage-step-4/run-2/desktop-C2.png)
- [桌面大尺寸宿主准备态](../evidence/lawson-fullpage-step-4/run-2/desktop-lawson-host.png)
- [手机宿主](../evidence/lawson-fullpage-step-4/run-2/host-390x844.png)
- [320 宽、200% 字号档案](../evidence/lawson-fullpage-step-4/run-2/archive-320x568-200.png)
- [跨尺寸返回 C2](../evidence/lawson-fullpage-step-4/run-5/resize-return-C2.png)

## 5. 原页和历史完整性

[integrity.json](../evidence/lawson-fullpage-step-4/integrity.json) 核验通过：

- 源仓库 HEAD 保持 `95dad9881a7b9d31c0ac635f1f335055d8cb3cc4`，源工作区干净。
- 源/public/dist 的 46 个原运行文件逐一匹配已锁定 SHA-256，每份 20,332,784 字节；public/dist 没有多余运行文件。
- 前四组历史封存 77/109/115/95 文件及其 manifest 保持原字节。
- 执行前 91 个主站输入中，6 个为本步授权修改，其余 85 个不变；新增产品文件 3 个。修改前版本和 diff 独立保存在本步目录，没有倒写旧基线。
- 主仓库 HEAD 保持 `4a6dd7c5c9c126ab3b9319fab5d8ea16a704dae8`。本步没有执行提交、推送或发布。

## 6. 本步边界及后续

当前验证覆盖正式宿主及独立运行原页；没有提前证明 iframe 内原控件、真实全屏/鼠标锁定/Esc、模型失败/重试、移动设备或原页对照回归。手机为浏览器视口模拟，大字号为根字体放大，不能等同物理手机或操作系统字体测试。停绘计数来自软件 WebGL，不代表硬件 GPU 性能结论。

旧封面事件和跨模态所有者重叠使用了明确标注的人工故障注入，其余打开、页签、视频和键盘路径均操作真实页面。原版已知问题继续按 [原页问题](original-issues.md) 记录，没有在本步改动原逻辑。

第五步从 [接口交接](step-4-handoff.md) 接入按需原页实例即可，不需要重做 C2、宿主布局、分项目档案或主庭院停绘。
