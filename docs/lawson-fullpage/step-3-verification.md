# 第三步验收：原网页迁入、构建一致性与独立运行

**第三步已完成。** 罗森原网页已作为真实运行资源进入主站，构建后的原页面在根目录和项目子目录均能独立运行。正式 Coding 入口、作品外层和 iframe 仍由第四、第五步实现。

完成时间：2026-11-10T18:37:55.302448+08:00（Asia/Shanghai）。

## 实际新增及版本

- 原版本：`95dad9881a7b9d31c0ac635f1f335055d8cb3cc4`；主站 HEAD 仍为 `4a6dd7c5c9c126ab3b9319fab5d8ea16a704dae8`。
- 新增 `public/experiments/lawson/`，46 个运行文件、20,332,784 字节。原 HTML、CSS、JS、import map、本地 Three.js r160 与模型内容均未改写。
- 四个 GLB 共 18,648,040 字节，保留商店及 A/B/C 三辆车。
- 构建生成 `dist/experiments/lawson/`，同一套 46 个文件与源/public 全部逐字节一致。
- 既有主站源码、配置、依赖和 91 个监测输入未变，原 dist 的 18 个主站文件也与执行前一致。
- 当前新增内容保存在工作区，尚未提交、推送 GitHub 或发布网站。

见 [三方文件表](../evidence/lawson-fullpage-step-3/source-public-dist.json)、[复制记录](../evidence/lawson-fullpage-step-3/copy-verification.json)。

## 构建结果

Node v24.22.1、npm 11.9.0，使用已有匹配依赖，未重装或修改 package/锁文件。迁入后执行 `npm run build`，包含 `tsc --noEmit`；退出码 0。

本步采用 [build-1.log](../evidence/lawson-fullpage-step-3/build-1.log) 及 [构建结果](../evidence/lawson-fullpage-step-3/build-1-result.json)，该次构建前已验证 public 文件完整。

## 实际构建输出的 HTTP 核查

同一份 dist 通过临时本机静态服务分别映射为：

| 模式 | 页面路径 | 结果 |
|---|---|---|
| 根目录 | `/experiments/lawson/index.html` | 原页真实就绪及首帧通过 |
| 项目子目录 | `/Stylized-Dreamy-Flower-Bed-Sky-Island/experiments/lawson/index.html` | 原页真实就绪及首帧通过 |

两种前缀共 92 个运行资源 URL 的状态、字节长度和 MIME 检查通过；两份主站首页可访问且与实际构建一致。4 个缺失资源对照返回预期 404，未将其混入正常页面错误。

浏览器实际接收的每种路径下全部 46 个响应内容也已逐项计算 SHA256，与源文件一致；不是只检查 HTTP 200。正常浏览器请求没有 HTTP 错误、请求失败或外部依赖。

见 [HTTP 核查](../evidence/lawson-fullpage-step-3/http-verification.json) 与 [采用的浏览器证据](../evidence/lawson-fullpage-step-3/browser-accepted.json)。测试服务已停止，本机测试端口不是发布地址。

## 就绪、默认状态与首帧

环境为 Chromium 155.0.8059.79、专用 Xvfb :109、Mesa llvmpipe LLVM 19.1.7 软件 WebGL2、LP_NUM_THREADS=3。两种路径串行核查，初始视口 1440×900、DPR 1。

确认原 ready 为 true、error 为空、body ready 为 1，原 fatal 未显示，实际 GL 绘制发生并取得场景截图。原黄昏 18.5、8 组灯光开启、控制台展开、屋顶可见、漫游关闭、初始相机位置及 orbit UI 状态均符合基线；3 辆车、2 名店员、17 类交互入口与 41 控件结构仍在，原自动车流启动。

从导航到完成默认记录的墙钟约为根目录 7.78 秒、项目目录 5.90 秒，只描述本次本机条件，不是线上加载或硬件性能承诺。原默认画质和自适应变化如实记录；根目录操作抽查随后经原设置按钮选择 low、960×540，未修改原默认配置。

- [根目录默认原页](../evidence/lawson-fullpage-step-3/run-2/root-default-original.png)
- [项目目录默认原页](../evidence/lawson-fullpage-step-3/run-2/project-default-original.png)
- [夜景](../evidence/lawson-fullpage-step-3/run-1/root-time-night.png)
- [黄昏恢复](../evidence/lawson-fullpage-step-3/run-1/root-time-dusk.png)

## 原 UI 操作抽查

| 条目 | 结论 | 采用来源 |
|---|---|---|
| `root.load` | 通过 | [run-2](../evidence/lawson-fullpage-step-3/run-2/browser.json) |
| `root.time` | 通过 | [run-1](../evidence/lawson-fullpage-step-3/run-1/browser.json) |
| `root.sign` | 通过 | [run-1](../evidence/lawson-fullpage-step-3/run-1/browser.json) |
| `root.camera` | 通过 | [run-1](../evidence/lawson-fullpage-step-3/run-1/browser.json) |
| `root.roof` | 通过 | [run-1](../evidence/lawson-fullpage-step-3/run-1/browser.json) |
| `root.traffic` | 通过 | [run-1](../evidence/lawson-fullpage-step-3/run-1/browser.json) |
| `root.network-bytes` | 通过 | [run-2](../evidence/lawson-fullpage-step-3/run-2/browser.json) |
| `project.load` | 通过 | [run-2](../evidence/lawson-fullpage-step-3/run-2/browser.json) |
| `project.ui` | 通过 | [run-1](../evidence/lawson-fullpage-step-3/run-1/browser.json) |
| `project.network-bytes` | 通过 | [run-2](../evidence/lawson-fullpage-step-3/run-2/browser.json) |

时间按钮切夜晚再回黄昏；招牌开关观察原灯光和发光材质实际变化；相机按钮到正面再回全景；屋顶按钮核对原 roofRoot 可见性；原车 A 按钮、暂停和恢复核对实时位置及车轮。暂停期间绘制帧仍增加，说明不是通过停止测试进程制造静止。项目子路径的原控制台收起/展开也有实际反馈。

观察包装以原实参调用原灯光函数一次，时钟和场景文件不变。车辆使用 getVehicleState 而非 UI 位置缓存。原控件完整保全不等于本步重新穷举了 41 控件及 17 类点击；最终集成对照留给第七步。

## 诊断、修正和原问题

早期复制工具错误地要求整个源目录仅有运行文件，因源目录还有截图、报告与启动辅助文件而拒绝复制。已修正为源端按清单子集校验，目标和构建目录仍严格等于 46 文件；没有扩大复制范围。最初命令随后执行的构建发生在复制前，只保留作诊断，未作为迁入验收。工具已加入迁入校验前置条件，正式构建为 build-1。

浏览器 run-1 中原按钮抽查通过，但响应内容读取超过默认调试缓存，且项目路径的加载等待表达式未兼容原页移除 loader，产生测试 UtilityScript 空引用。原页面已 ready，原控制台没有场景脚本错误。run-2 使用专用 64MB/32MB 调试缓存并修正空节点判断，仅补核两条加载及网络内容项，四项全部通过、未捕获脚本异常为 0。未修改运行代码或时钟来通过检查，所有原记录和当时脚本保留。

原版 R、碰撞、N、车体点击说明、手机布局及动画暂停语义等继续按 [原问题表](original-issues.md) 留档。真实手机、其他浏览器、真实后台隐藏和硬件 GPU 性能未在本步新增验证；真实 iframe 权限、Esc、输入隔离、主庭院停绘和返回由后续步骤核对。

## 完整性与交接

源 46 文件、主站原 91 输入及历史 77/109/115 三组封存均未变化。仅新增真实运行目录与本步资料，构建产物按既有流程生成。测试浏览器、专用服务器、虚拟显示器和本步备份目录已清理。

- [完整性](../evidence/lawson-fullpage-step-3/integrity.json)
- [第四/第五步交接](step-3-handoff.md)
- [机器交接](../evidence/lawson-fullpage-step-3/step-4-handoff.json)
- [独立封存](../evidence/lawson-fullpage-step-3/evidence-manifest.json)

第三步到此完成：完整原网页已在项目内，并可从真实构建产物独立运行。正式网站里的作品入口及大尺寸嵌入继续按既定步骤实施。
