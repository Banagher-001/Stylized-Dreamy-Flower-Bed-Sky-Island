# 第一步验收：罗森场景运行核查与接入资产整理

**结论：第一步完成，可以进入第二步展位设计。** 本结论覆盖独立运行基线、依赖完整性、临时嵌入可行性及后续适配边界。正式网站展位和正式作品体验层尚未接入；本步新增核查文档、证据与工具。

完成时间：2026-11-10T01:12:24.841768+08:00（Asia/Shanghai）。

## 版本和范围

- 罗森源仓库：`Banagher-001/luosen-asset`，`95dad9881a7b9d31c0ac635f1f335055d8cb3cc4`。
- 个人网站：`Banagher-001/Stylized-Dreamy-Flower-Bed-Sky-Island`，`4a6dd7c5c9c126ab3b9319fab5d8ea16a704dae8`。
- 两个远端 main 在执行开始时均与本地一致，执行前工作区干净。源目录为 `lawson-blender/out/web_final/`。
- 临时运行副本只放在 `/tmp/lawson-step1-audit/`，依赖文件逐字节复制；站点 src/public 没有新增罗森资源。
- 源仓库 46 个运行文件和主站 91 个受监测输入的 SHA256 均未改变；两个仓库原有跟踪文件均无修改，提交也未变化。
- 本步没有提交、推送 GitHub，也没有部署网站。

## 交付资源

- 46 个必要文件，20,332,784 字节（20.33 MB）。
- 四个 GLB 共 18,648,040 字节（18.65 MB）；没有外链 buffer 或图像依赖。
- 本地 vendor、脚本和样式闭包完整，未发现关键文件缺失、未解析模块或外部网络依赖。
- 罗森 Three.js r160 与主站 0.187.0 分开运行，支持后续同站独立页面嵌入。
- [完整清单](asset-inventory.md) · [逐文件 SHA256 与依赖图](../evidence/lawson-integration-step-1/asset-manifest.json)。

## 实际功能核查

完成 27 组浏览器核查记录：核心 11 组、嵌入 6 组、兼容性基线 6 组、性能记录 4 组。性能与兼容性基线的“记录完成”不代表最终设备适配已经完成。

| 功能 | 本次结果 |
|---|---|
| 冷/热加载 | 原始 HTTP 页面可进入场景；root 与子目录均可运行 |
| 场景对象 | 3 辆车、2 名店员、17 类交互对象、146 个屋顶/顶棚目标、34 个程序灯光 |
| 昼夜与灯光 | 白天/黄昏/夜晚、8 组灯光、全开/全关与数字快捷键通过；场景区域截图像素确实变化 |
| 相机 | 8 个预设、真实拖动旋转、滚轮缩放、右键平移、恢复全景、屋顶切换通过 |
| 漫游 | 真实点击进入、键盘移动、鼠标锁定、Esc 退出通过 |
| 门与物件 | 公开左门坐标确认开/关位移；节点与截图记录右门；真实指针点击命中交互物件并改变对应状态 |
| 画质 | 原有 high/medium/low 三档均可切换 |
| 车辆 | 完整进场、停车、倒车、离场与下一车辆交接；行驶中位置与车轮暂停、继续、重置通过 |
| 店员 | 两位店员都自主完成任务转换，未用强制任务接口制造转换 |
| 暂停语义 | 已实测全局暂停后仍有绘制；将其列为正式接入的生命周期工作 |

车辆和店员连续观察约 191.1 秒，使用原 UI 的 1.8 倍车辆速度选项，场景时钟未加速。A 记录到 `bag_check, observe_entrance, tidy_counter`；B 记录到 `cooler_check, restock`。车辆 A 覆盖 12 个状态。

相机公开 project() 返回整数，重置后的三个世界点最大投影误差在 2 CSS 像素以内。源 debugDoor 只提供左门坐标，记录没有伪造 rightPos。

核心通过项及各自来源见 [core-accepted.json](../evidence/lawson-integration-step-1/core-accepted.json)。昼夜截图场景区域的 RGB 差异 RMS 约 57.6 / 70.9 / 88.0，见 [像素分析](../evidence/lawson-integration-step-1/day-night-pixel-check.json)。

## 临时嵌入验证

六项均通过，见 [run-6/embed.json](../evidence/lawson-integration-step-1/run-6/embed.json)：

1. 同一套原文件从 `experiments/lawson/` 子目录直接运行。
2. iframe 模型实际 ready，父/子页面模块与样式保持隔离。
3. 场景内滚轮缩放不滚动父页面，子页面快捷键不触发父页面的键盘监听。
4. 真实点击可获得鼠标锁定与全屏权限，Esc 可退出漫游。
5. 容器高度变化后画布与渲染尺寸更新；卸载 iframe 后旧 RAF/绘制计数停止。
6. 主模型请求主动失败时，父层关闭仍可操作；恢复请求后重新打开能加载成功。

卸载后回调停止不单独证明显卡内存的回收时机。正式接入还需要作品身份、ready/error 握手、主庭院停绘、全屏返回控件及阅读位置恢复，详见 [接口边界](integration-feasibility.md)。

## 手机和降级现状

- Chromium 390×844、DPR 2、触摸模拟中，单指旋转、双指缩放与点按夜景通过；双指操作后世界轴投影放大约 1.36 倍。
- 844×390 横屏时画布与渲染尺寸同步；390×844 竖屏未出现横向页面溢出。
- 展开的控制台宽 200px，占手机宽度约 51.3%；顶部品牌与按钮重叠，38 个被测控件至少一边小于 44 CSS 像素，原页面没有触摸漫游方向按钮。
- 减少动态媒体条件确实匹配，但原 JS 场景并未自动暂停，实测仍有持续绘制。此项是后续适配工作，不作为已实现功能宣传。
- 模拟全部 WebGL 别名不可用后，显示明确错误：`无法创建 WebGL 渲染器：Error creating WebGL context.`，重试入口可见，appReady 为 false。
- 物理 iOS/Android、真实触摸屏和硬件 GPU 未在本步验证。

手机与降级记录见 [compat-accepted.json](../evidence/lawson-integration-step-1/compat-accepted.json)，已知问题与归属见 [issues.md](issues.md)。

## 软件渲染性能基线

环境：Chromium 155.0.8059.79、独立 Xvfb :106、Mesa llvmpipe LLVM 19.1.7、LP_NUM_THREADS=3，软件 WebGL2。功能测试通过原设置按钮选择 low；性能采样另开单浏览器，保留原默认 high 与自适应降级。使用已有 setFreeCamera 固定原配置视角，动画保持原始时间。

| 固定视角 | 采样墙钟秒 | 完成的场景回调 | 实际回调/秒 | 观察到的画质 |
|---|---:|---:|---:|---|
| default auto-quality | 13.40 | 28 | 2.09 | high |
| vehicle area, original preset fixed pose | 12.95 | 30 | 2.32 | high → medium |
| interior | 12.07 | 29 | 2.40 | medium |

这些是云端软件驱动下的实际回调观察，**不是硬件 GPU 帧率证明，也不是“性能达标”的宣称**。原 HUD 数值保留在 JSON，未替代墙钟计数。已观察到 high→medium 自适应降级。后续以按点击加载、只绘制可见场景、弱设备初始画质和档案回退为设计依据，真实设备性能留给后续验收。

见 [run-8/performance.json](../evidence/lawson-integration-step-1/run-8/performance.json)。

## 失败记录与完整性

原始超时、中断、探针假设修正及临时容器尺寸问题均保留，详见 [问题记录](issues.md)。验收采用有明确修正原因的定向复核，没有修改场景源码或动画时间戳来制造通过。正常核心路径与已接受试验没有未捕获脚本异常，关键运行请求没有 HTTP 错误；主动故障注入的错误消息按预期保留。

临时容器控制台的一条辅助 404 已单独定位为 `/favicon.ico`，不开场景也能复现；给诊断页增加 data 图标后辅助请求复核通过。它不属于罗森的 46 个运行文件，原记录保留于 [定位结果](../evidence/lawson-integration-step-1/harness-auxiliary-request.json) 和 [修正复核](../evidence/lawson-integration-step-1/harness-auxiliary-request-fixed.json)。

- [执行基线](../evidence/lawson-integration-step-1/baseline.json)
- [最终输入完整性](../evidence/lawson-integration-step-1/integrity.json)
- [机器可读汇总](../evidence/lawson-integration-step-1/summary.json)
- [复核命令与环境说明](reproduce.md)

第一步的剩余事项是已分配给后续步骤的正式接入与适配工作；本步没有遗留无法打开、关键资源缺失或核心交互不可用的阻塞。
