# 第五步验收：完整罗森原网页内嵌

第五步已完成。C2 的“进入完整网页”现在直接运行完整罗森原页面，原控制台和场景保留；加载、慢载入、实际错误、两种重试、退出卸载与阅读恢复已接通。

实际构建和 15 组浏览器验收通过。原网页 46 个运行文件、源仓库和此前五组封存保持原样。本步仅修改工作区，没有提交、推送或发布。

## 1. 本步落地

| 文件 | 完成内容 |
|---|---|
| `src/tour/createLawsonExperience.ts`，新增 | 唯一 iframe 实例、延迟挂载、真实状态观察、文档/实例代次、重试、原生锁定/全屏释放及卸载 |
| `src/tour/createProjectViewer.ts` | 宿主重试入口、慢载入/失败提示、aria-busy、按页签隐藏状态控件；保留原页自己的加载和错误操作 |
| `src/tour/startTourPrototype.ts` | 开/切/关/销毁接入管理器；先停主庭院再创建原页，先卸载原页再恢复庭院 |
| `src/tour/projectHost.css` | 重试按钮、独立反馈行；提示在工具栏内自然增高，不覆盖原控制台或原重试 |

复用第四步的项目身份、URL 解析和稳定挂载节点。真实网页地址仍为 `experiments/lawson/index.html`，根目录和项目子路径均可用。原 HTML、CSS、JS、模型、本地 Three r160、控制台与默认设置没有改写，也没有插入生产桥接脚本或 sandbox。

每次进入 lawson/live 才创建实例；浏览封面、档案、庭院时不创建。离开 live 即卸载，再次进入从原默认状态重新加载；没有增加跨退出的场景状态保存。

## 2. 状态、重试和清理

管理器提供 mount/retry/unmount/dispose；重复 mount 不叠加实例。首次挂载放到下一帧，避开第四步 open 回调发生于 showModal 之前的时序，并校验当前活动身份和实例代次。快速关闭会取消排队挂载。

加载时持续重新读取当前 document/API。原 API error、body error 或实际可见 fatal 优先于 ready；约 12 秒无确定结果进入 slow，HTML load 不当作场景成功。ready 后仍观察错误及文档替换。

原页重试刷新同一 iframe 的文档，重新识别文档代次。宿主重试先失效旧回调、取消计时器和监听、移除旧 iframe，再创建新实例。离开现场同样先清理管理器，再恢复主庭院与阅读。

原生锁定从所属子文档读取和退出；全屏从实际拥有者退出。移除实例后，旧 load/timer 不能修改新状态。原页焦点下保留 Esc 的浏览器行为，宿主返回控件焦点下可用 Esc 关闭。

## 3. 真实页面验收

以实际 dist 提供 HTTP 服务，使用 Chromium 155.0.8059.79、有界面模式和 Mesa 软件 WebGL。浏览器探针只统计实际绘制并调用原方法一次；未更改原时钟、生产文件或原默认画质。

15 组通过结果索引见 [accepted-browser-results.json](../evidence/lawson-fullpage-step-5/accepted-browser-results.json)。

| 验收组 | 实际结果 |
|---|---|
| 完整原页与生命周期 | 实际 ready、原控制台可见、8 组灯光；原昼夜、灯光、俯视、屋顶、店员及车辆入口可操作。切档案卸载，重入为原默认状态，关闭恢复原滚动和触发焦点 |
| 模型失败与两种重试 | 实际拦截模型产生原 fatal；原重试保持 iframe、替换文档并恢复；保留的旧 ready API 不会掩盖新错误；宿主重试替换 iframe；旧节点注入 load 不影响新实例 |
| 慢载入及恢复 | 延迟原 main 模块超过 12 秒，原 API 尚不存在时进入 slow；320 宽返回/独立打开/重试仍可操作，反馈字号 14px；释放真实请求后 ready，反馈收起 |
| 快速关闭与迟到请求 | 同一任务内开关取消挂载且不请求原 runtime；模块未返回时关闭，迟到请求不重新创建实例，主庭院恢复 |
| 原 30 秒超时与错误优先级 | 延迟原模型，原超时 guard 显示 fatal，尽管 API error 仍为 null，宿主正确判错；模型随后成功且 API ready=true 时，可见 fatal 仍优先；原重试恢复 |
| 输入与原生权限 | 原轮滚、拖动及键盘快捷键有效，主站阅读位置不动；原按钮全屏、原漫游按钮鼠标锁定有效；使用真实 X11 Esc 退出，宿主仍打开；强制关闭可释放实例持有的锁定/全屏；宿主焦点下 Esc 关闭 |
| 全屏稳定绘制 | 在全屏切换后等待实际多帧绘制，场景正常显示；核心区域 59,115 种颜色，排除只有界面的空画面。原页退出全屏后宿主仍停绘 |
| 布局，5 组 | 390×844、320×568、844×390、320×568 宿主 200% 根字号、1366×768 项目子路径：iframe 填满工具栏剩余区域，原文档视口与容器吻合；返回无主站横向溢出 |
| 子路径与独立打开 | 项目子路径原页 ready；当前嵌入运行期间独立打开的新页面也 ready，opener=null，宿主仍只有一个 iframe |
| 重复卸载、暂停及尺寸恢复 | 5 次完整进入/退出后，旧原页绘制计数保持不动，无 iframe 或打开 dialog 遗留；原暂停设置保留；现场缩小至手机后主庭院仍停绘，关闭返回稳定阅读 C2，导览不自启 |
| 庭院旧功能 | 原档案视频和两幅早期帧图保留，正常/像素模式可用；庭院不创建罗森实例 |
| 主庭院故障隔离 | 仅使主文档获取 WebGL 失败，原 iframe 仍真实加载、绘制；庭院现场禁用，档案及罗森入口保持可用 |

正常场景中，主庭院连续 1 秒的实际 draw 计数为 **0**；同一原页面另一段 1 秒采样为 **3,805** 次。该数据用于证明两个页面的绘制隔离，不是硬件性能或 FPS 结论。卸载检查还保留旧计数对象，移除 iframe 后观察 500ms，计数未继续增加。

正常桌面内容区为 1440×844、工具栏 56px；手机工具栏正常 48px。slow/error 出现反馈行时工具栏自然增高，原网页使用实际剩余高度。没有通过缩放或固定比例缩小原页面。

## 4. 构建、尝试记录与截图

最终 `npm run build` 成功，包含 `tsc --noEmit`；`git diff --check` 通过。见 [build-2.log](../evidence/lawson-fullpage-step-5/build-2.log) 及 [build-result.json](../evidence/lawson-fullpage-step-5/build-result.json)。

run-1 完成正常集成，run-2 进行批量检查。run-2 的两项脚本问题分别是：在解除网络拦截后重复处理同一 route，以及误认为父文档的 pointerLockElement 必须指向 iframe。修正后从实际所属子文档核查锁定，run-3 六组均通过，失败记录保留。

第一轮截图发现反馈文本被旧 header 规则压为 10px，最终 build-2 只增强该反馈规则的选择器，使预期 14px 生效；JavaScript 与 build-1 相同，精确差异见 [build-delta.json](../evidence/lawson-fullpage-step-5/build-delta.json)。所有状态相关检查在最终构建重做，其他未受影响结果保留。

原一次全屏事件后的即时截图为空帧，因此没有用它作为完整绘制证据；run-4 补充等待实际多帧并检查稳定场景。最终 15 组由各组最后通过结果组成，原始尝试全部保留，没有覆盖失败日志。

- [桌面完整原网页](../evidence/lawson-fullpage-step-5/run-1/desktop-ready.png)
- [手机完整原网页](../evidence/lawson-fullpage-step-5/run-2/layout-390x844.png)
- [最终手机慢载入反馈](../evidence/lawson-fullpage-step-5/run-3/mobile-slow.png)
- [原页实际超时界面](../evidence/lawson-fullpage-step-5/run-3/original-timeout-fatal.png)
- [全屏稳定场景](../evidence/lawson-fullpage-step-5/run-4/fullscreen-steady-scene.png)

没有未预期的页面异常、HTTP 错误、请求失败或控制台错误。模型拦截和主 WebGL 故障的预期错误按具体来源保留；关闭导致的请求取消单独识别。

## 5. 完整性与边界

[integrity.json](../evidence/lawson-fullpage-step-5/integrity.json) 核验源/public/dist 每份 46 文件、20,332,784 字节，均匹配固定 SHA-256；public/dist 没有新增原运行文件。源仓库 HEAD 保持 `95dad9881a7b9d31c0ac635f1f335055d8cb3cc4`，工作区干净。

前五组封存 77/109/115/95/95 文件和各自 manifest 保留。本步开始的 94 个主站输入中仅修改 3 个，其余 91 个不变，另新增一个管理器。主仓库 HEAD 保持 `4a6dd7c5c9c126ab3b9319fab5d8ea16a704dae8`，没有提交、推送或发布。

手机尺寸和宿主字号为浏览器模拟，不是物理设备核查；全屏/锁定已在此 Chromium 的真实窗口完成，不代表所有浏览器。原移动控制台与顶栏的既有布局、键盘漫游能力等按 [原页问题](original-issues.md) 保留。根字体放大作用于宿主，iframe 保留自己的原文档样式。

本步验证基本原功能及内嵌生命周期，没有将其记为全部 41 控件、17 类点击的完整对照。第六步继续设备和异常加固，第七步完成最终原版功能回归，具体入口见 [交接](step-5-handoff.md)。
