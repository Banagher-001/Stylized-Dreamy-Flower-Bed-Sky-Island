# 完整功能基线对照表

状态“原页正常”限定于记录的设备、操作和条件。“原页已有问题”表示问题已查明，不表示功能通过。关键条目均有明确结论；未宣称修复原页或完成正式嵌入。

## 原有 41 个控件

32 个静态按钮、1 个滑杆、8 个动态灯光控件；包含平常隐藏的帮助关闭及失败重试。保留原入口，不删减控制台。

| 原控件 | 选择器 | 结论 | 证据 |
|---|---|---|---|
| 重试 | `#fatal-retry` | 原页正常 | [run-9](../evidence/lawson-fullpage-step-1/run-9/readiness.json) · `READY.model-retry` |
| 全屏 | `#btn-fullscreen` | 原页正常 | [run-6](../evidence/lawson-fullpage-step-1/run-6/controls.json) · `BUTTON.btn-fullscreen` |
| 画质 | `#btn-settings` | 原页正常 | [run-1](../evidence/lawson-fullpage-step-1/run-1/controls.json) · `BUTTON.btn-settings` |
| 操作说明 | `#btn-help` | 原页正常 | [run-1](../evidence/lawson-fullpage-step-1/run-1/controls.json) · `BUTTON.help` |
| – | `#panel-collapse` | 原页正常 | [run-1](../evidence/lawson-fullpage-step-1/run-1/controls.json) · `BUTTON.panel-collapse` |
| 白天 | `[data-preset="day"]` | 原页正常 | [lawson-integration-step-1](../evidence/lawson-integration-step-1/core-accepted.json) · `day night eight lighting groups and shortcuts`（复用） |
| 黄昏 | `[data-preset="dusk"]` | 原页正常 | [lawson-integration-step-1](../evidence/lawson-integration-step-1/core-accepted.json) · `day night eight lighting groups and shortcuts`（复用） |
| 夜晚 | `[data-preset="night"]` | 原页正常 | [lawson-integration-step-1](../evidence/lawson-integration-step-1/core-accepted.json) · `day night eight lighting groups and shortcuts`（复用） |
| time-slider | `#time-slider` | 原页正常 | [run-1](../evidence/lawson-fullpage-step-1/run-1/controls.json) · `INPUT.time-slider` |
| 全开 | `#lights-all-on` | 原页正常 | [lawson-integration-step-1](../evidence/lawson-integration-step-1/core-accepted.json) · `day night eight lighting groups and shortcuts`（复用） |
| 全关 | `#lights-all-off` | 原页正常 | [lawson-integration-step-1](../evidence/lawson-integration-step-1/core-accepted.json) · `day night eight lighting groups and shortcuts`（复用） |
| 暂停车辆 | `#traffic-toggle` | 原页正常 | [lawson-integration-step-1](../evidence/lawson-integration-step-1/core-accepted.json) · `moving car pause resume and UI reset`（复用） |
| 重置 | `#traffic-reset` | 原页正常 | [lawson-integration-step-1](../evidence/lawson-integration-step-1/core-accepted.json) · `moving car pause resume and UI reset`（复用） |
| 慢速 | `[data-speed="0.6"]` | 原页正常 | [run-1](../evidence/lawson-fullpage-step-1/run-1/controls.json) · `TRAFFIC.speeds` |
| 正常 | `[data-speed="1"]` | 原页正常 | [run-1](../evidence/lawson-fullpage-step-1/run-1/controls.json) · `TRAFFIC.speeds` |
| 快速 | `[data-speed="1.8"]` | 原页正常 | [run-1](../evidence/lawson-fullpage-step-1/run-1/controls.json) · `TRAFFIC.speeds` |
| 车 A | `[data-car="A"]` | 原页正常 | [run-9](../evidence/lawson-fullpage-step-1/run-9/readiness.json) · `READY.car-A-button` |
| 车 B | `[data-car="B"]` | 原页正常 | [run-8](../evidence/lawson-fullpage-step-1/run-8/traffic.json) · `CYCLE.B` |
| 车 C | `[data-car="C"]` | 原页正常 | [run-8](../evidence/lawson-fullpage-step-1/run-8/traffic.json) · `CYCLE.C` |
| 店员 A | `[data-clerk="A"]` | 原页正常 | [run-9](../evidence/lawson-fullpage-step-1/run-9/readiness.json) · `READY.clerk-buttons` |
| 店员 B | `[data-clerk="B"]` | 原页正常 | [run-9](../evidence/lawson-fullpage-step-1/run-9/readiness.json) · `READY.clerk-buttons` |
| 全景 | `[data-cam="hero"]` | 原页正常 | [lawson-integration-step-1](../evidence/lawson-integration-step-1/core-accepted.json) · `eight camera presets orbit zoom pan reset roof`（复用） |
| 正面 | `[data-cam="front"]` | 原页正常 | [lawson-integration-step-1](../evidence/lawson-integration-step-1/core-accepted.json) · `eight camera presets orbit zoom pan reset roof`（复用） |
| 左侧 | `[data-cam="left"]` | 原页正常 | [lawson-integration-step-1](../evidence/lawson-integration-step-1/core-accepted.json) · `eight camera presets orbit zoom pan reset roof`（复用） |
| 后侧 | `[data-cam="rear"]` | 原页正常 | [lawson-integration-step-1](../evidence/lawson-integration-step-1/core-accepted.json) · `eight camera presets orbit zoom pan reset roof`（复用） |
| 俯视 | `[data-cam="top"]` | 原页正常 | [lawson-integration-step-1](../evidence/lawson-integration-step-1/core-accepted.json) · `eight camera presets orbit zoom pan reset roof`（复用） |
| 室内 | `[data-cam="interior"]` | 原页正常 | [lawson-integration-step-1](../evidence/lawson-integration-step-1/core-accepted.json) · `eight camera presets orbit zoom pan reset roof`（复用） |
| 收银区 | `[data-cam="checkout"]` | 原页正常 | [lawson-integration-step-1](../evidence/lawson-integration-step-1/core-accepted.json) · `eight camera presets orbit zoom pan reset roof`（复用） |
| 车辆 | `[data-cam="vehicle"]` | 原页正常 | [lawson-integration-step-1](../evidence/lawson-integration-step-1/core-accepted.json) · `eight camera presets orbit zoom pan reset roof`（复用） |
| 隐藏屋顶 | `#btn-roof` | 原页正常 | [lawson-integration-step-1](../evidence/lawson-integration-step-1/core-accepted.json) · `eight camera presets orbit zoom pan reset roof`（复用） |
| 室内漫游 | `#btn-walk` | 原页正常 | [run-7](../evidence/lawson-fullpage-step-1/run-7/keyboard.json) · `POINTER.walk-look` |
| 重置视角 | `#btn-reset-cam` | 原页正常 | [run-7](../evidence/lawson-fullpage-step-1/run-7/keyboard.json) · `BOUNDARY.R-in-walk` |
| 知道了 | `#help-close` | 原页正常 | [run-1](../evidence/lawson-fullpage-step-1/run-1/controls.json) · `BUTTON.help` |
| 店内灯光 | `.toggle[data-group="StoreInterior"]` | 原页正常 | [run-1](../evidence/lawson-fullpage-step-1/run-1/controls.json) · `LIGHT.StoreInterior` |
| LAWSON 招牌 | `.toggle[data-group="LawsonSign"]` | 原页正常 | [run-1](../evidence/lawson-fullpage-step-1/run-1/controls.json) · `LIGHT.LawsonSign` |
| 外墙灯带 | `.toggle[data-group="FacadeStrip"]` | 原页正常 | [run-1](../evidence/lawson-fullpage-step-1/run-1/controls.json) · `LIGHT.FacadeStrip` |
| 路灯 | `.toggle[data-group="StreetLamp"]` | 原页正常 | [run-1](../evidence/lawson-fullpage-step-1/run-1/controls.json) · `LIGHT.StreetLamp` |
| 冷柜灯光 | `.toggle[data-group="CoolerLighting"]` | 原页正常 | [run-1](../evidence/lawson-fullpage-step-1/run-1/controls.json) · `LIGHT.CoolerLighting` |
| 售货机灯光 | `.toggle[data-group="VendingLighting"]` | 原页正常 | [run-1](../evidence/lawson-fullpage-step-1/run-1/controls.json) · `LIGHT.VendingLighting` |
| 墙面暖光 | `.toggle[data-group="WarmExterior"]` | 原页正常 | [run-1](../evidence/lawson-fullpage-step-1/run-1/controls.json) · `LIGHT.WarmExterior` |
| 车辆灯光 | `.toggle[data-group="VehicleLights"]` | 原页正常 | [run-1](../evidence/lawson-fullpage-step-1/run-1/controls.json) · `LIGHT.VehicleLights` |

“重置视角”按钮的正常恢复与 R 快捷键的原有问题分别记录。相机预设测试确认了原按钮反馈，不能解释为拖动后每种时机都能精确复位。

## 快捷键与移动键

| 键 | 结论 | 证据 |
|---|---|---|
| `KeyR` | 原页已有问题 | [run-6b](../evidence/lawson-fullpage-step-1/run-6b/controls.json) · `KEY.KeyR` |
| `Digit1` | 原页正常 | [lawson-integration-step-1](../evidence/lawson-integration-step-1/core-accepted.json) · `day night eight lighting groups and shortcuts`（复用） |
| `Digit2` | 原页正常 | [lawson-integration-step-1](../evidence/lawson-integration-step-1/core-accepted.json) · `day night eight lighting groups and shortcuts`（复用） |
| `Digit3` | 原页正常 | [lawson-integration-step-1](../evidence/lawson-integration-step-1/core-accepted.json) · `day night eight lighting groups and shortcuts`（复用） |
| `Space` | 原页正常 | [run-1](../evidence/lawson-fullpage-step-1/run-1/controls.json) · `KEY.Space` |
| `Escape` | 原页正常 | [run-7](../evidence/lawson-fullpage-step-1/run-7/keyboard.json) · `POINTER.walk-look` |
| `KeyA` | 原页正常 | [run-7](../evidence/lawson-fullpage-step-1/run-7/keyboard.json) · `KEY.KeyA` |
| `KeyD` | 原页正常 | [run-7](../evidence/lawson-fullpage-step-1/run-7/keyboard.json) · `KEY.KeyD` |
| `KeyS` | 原页已有问题 | [run-7b](../evidence/lawson-fullpage-step-1/run-7b/keyboard.json) · `KEY.KeyS` |
| `KeyW` | 原页已有问题 | [run-7b](../evidence/lawson-fullpage-step-1/run-7b/keyboard.json) · `KEY.KeyW` |
| `ShiftLeft` | 原页正常 | [run-7b](../evidence/lawson-fullpage-step-1/run-7b/keyboard.json) · `KEY.ShiftLeft` |
| `ShiftRight` | 原页正常 | [run-7b](../evidence/lawson-fullpage-step-1/run-7b/keyboard.json) · `KEY.ShiftRight` |
| `KeyN (README only)` | 原页已有问题 | [run-1](../evidence/lawson-fullpage-step-1/run-1/controls.json) · `DOC.KeyN` |

W/S 的限制对应实际起点与记录位置；A/D 有平面位移，Shift 使用可通行的 A 路径确认加速。Escape 漫游退出与全屏系统 Esc 在各自记录中分别核对。

## 17 类真实场景点击

全部使用真实指针点击并观察原处理函数及实际效果；已有相机 API 仅辅助摆放观察视角，未用于派发点击。

| 物件 ID | 原作用 | 结论 | 证据 |
|---|---|---|---|
| `sign` | LAWSON 招牌灯光 | 原页正常 | [run-2](../evidence/lawson-fullpage-step-1/run-2/targets.json) · `TARGET.sign` |
| `facade` | 外墙灯带 | 原页正常 | [run-3](../evidence/lawson-fullpage-step-1/run-3/targets.json) · `TARGET.facade` |
| `door` | 门开关和位移 | 原页正常 | [run-3](../evidence/lawson-fullpage-step-1/run-3/targets.json) · `TARGET.door` |
| `vending` | 售货机灯光 | 原页正常 | [run-3](../evidence/lawson-fullpage-step-1/run-3/targets.json) · `TARGET.vending` |
| `basket` | 冷柜灯光（原绑定） | 原页正常 | [run-3](../evidence/lawson-fullpage-step-1/run-3/targets.json) · `TARGET.basket` |
| `checkout` | 收银区镜头 | 原页正常 | [run-3](../evidence/lawson-fullpage-step-1/run-3/targets.json) · `TARGET.checkout` |
| `shelf` | 货架镜头 | 原页正常 | [run-3](../evidence/lawson-fullpage-step-1/run-3/targets.json) · `TARGET.shelf` |
| `alcohol` | 酒类区镜头 | 原页正常 | [run-3](../evidence/lawson-fullpage-step-1/run-3/targets.json) · `TARGET.alcohol` |
| `oden` | 蒸汽可见性 | 原页正常 | [run-3](../evidence/lawson-fullpage-step-1/run-3/targets.json) · `TARGET.oden` |
| `clerkA` | 店员 A 固定区域镜头 | 原页正常 | [run-3](../evidence/lawson-fullpage-step-1/run-3/targets.json) · `TARGET.clerkA` |
| `clerkB` | 店员 B 固定区域镜头 | 原页正常 | [run-3](../evidence/lawson-fullpage-step-1/run-3/targets.json) · `TARGET.clerkB` |
| `atm` | ATM 发光材质 | 原页正常 | [run-3](../evidence/lawson-fullpage-step-1/run-3/targets.json) · `TARGET.atm` |
| `freezer` | 冷柜灯光 | 原页正常 | [run-3](../evidence/lawson-fullpage-step-1/run-3/targets.json) · `TARGET.freezer` |
| `cooler` | 冷柜灯光 | 原页正常 | [run-3](../evidence/lawson-fullpage-step-1/run-3/targets.json) · `TARGET.cooler` |
| `microwave` | 微波炉区域镜头 | 原页正常 | [run-3](../evidence/lawson-fullpage-step-1/run-3/targets.json) · `TARGET.microwave` |
| `dining` | 用餐区镜头 | 原页正常 | [run-3](../evidence/lawson-fullpage-step-1/run-3/targets.json) · `TARGET.dining` |
| `coffee` | 咖啡机发光材质 | 原页正常 | [run-3](../evidence/lawson-fullpage-step-1/run-3/targets.json) · `TARGET.coffee` |

购物篮切换冷柜灯、店员物件聚焦固定岗位等都按原绑定记录。没有将其改成新交互。

## 自主流程、输入和错误边界

| 项目 | 结论 | 证据 |
|---|---|---|
| 首次 HTTP 加载 | 原页正常 | [lawson-integration-step-1](../evidence/lawson-integration-step-1/core-accepted.json) · `cold standalone load`（复用） |
| 再次 HTTP 加载 | 原页正常 | [lawson-integration-step-1](../evidence/lawson-integration-step-1/core-accepted.json) · `warm standalone load`（复用） |
| 刷新回到原默认状态 | 原页正常 | [run-9](../evidence/lawson-fullpage-step-1/run-9/readiness.json) · `READY.refresh-defaults` |
| 标签切换和返回；真实隐藏受环境限制 | 设备/浏览器限制 | [run-9c](../evidence/lawson-fullpage-step-1/run-9c/readiness.json) · `READY.background-return` |
| 模型失败及原重试 | 原页正常 | [run-9](../evidence/lawson-fullpage-step-1/run-9/readiness.json) · `READY.model-retry` |
| WebGL 不可用的明确错误 | 原页正常 | [lawson-integration-step-1](../evidence/lawson-integration-step-1/compat-accepted.json) · `WebGL unavailable shows explicit failure`（复用） |
| 旋转、滚轮缩放、右键平移、相机和屋顶 | 原页正常 | [lawson-integration-step-1](../evidence/lawson-integration-step-1/core-accepted.json) · `eight camera presets orbit zoom pan reset roof`（复用） |
| 漫游鼠标观察、锁定和 Escape | 原页正常 | [run-7](../evidence/lawson-fullpage-step-1/run-7/keyboard.json) · `POINTER.walk-look` |
| 漫游中 R 后的界面状态 | 原页已有问题 | [run-7](../evidence/lawson-fullpage-step-1/run-7/keyboard.json) · `BOUNDARY.R-in-walk` |
| 车辆 A 原时钟完整流程 | 原页正常 | [lawson-integration-step-1](../evidence/lawson-integration-step-1/core-accepted.json) · `one full vehicle cycle autonomous clerk transitions pause resume reset`（复用） |
| 车辆 B 原时钟完整流程 | 原页正常 | [run-8](../evidence/lawson-fullpage-step-1/run-8/traffic.json) · `CYCLE.B` |
| 车辆 C 原时钟完整流程 | 原页正常 | [run-8](../evidence/lawson-fullpage-step-1/run-8/traffic.json) · `CYCLE.C` |
| 行驶中暂停、恢复、重置 | 原页正常 | [lawson-integration-step-1](../evidence/lawson-integration-step-1/core-accepted.json) · `moving car pause resume and UI reset`（复用） |
| 两名店员自主任务变化 | 原页正常 | [lawson-integration-step-1](../evidence/lawson-integration-step-1/core-accepted.json) · `one full vehicle cycle autonomous clerk transitions pause resume reset`（复用） |
| 默认手机竖屏和横屏 | 原页已有问题 | [run-9](../evidence/lawson-fullpage-step-1/run-9/readiness.json) · `VIEWPORT.phone-defaults` |
| 触摸旋转、双指缩放、夜景点按 | 原页正常 | [lawson-integration-step-1](../evidence/lawson-integration-step-1/compat-accepted.json) · `mobile layout touch orbit and environment tap`（复用） |
| 减少动态条件匹配但 JS 不自动暂停 | 原页已有问题 | [lawson-integration-step-1](../evidence/lawson-integration-step-1/compat-accepted.json) · `reduced motion baseline documented`（复用） |
| pauseAll 后仍然绘制 | 原页已有问题 | [lawson-integration-step-1](../evidence/lawson-integration-step-1/core-accepted.json) · `pause semantics and lifecycle gaps measured`（复用） |

## 界面和调试结构

原品牌、顶部按钮、控制台、提示、性能信息、加载、错误、帮助、漫游条、工具提示均记录在默认 UI 清单或对应状态截图中。

公开 API 共 41 个，名称详见 [静态清单](../evidence/lawson-fullpage-step-1/static-inventory.json)。API 清单用于保全原文件结构；并非逐个 API 的功能验收。原 `ready/error` 与 `body.dataset.ready` 用于读取就绪或错误状态，HTML/iframe 的 load 事件不等于模型已就绪。

旧的临时同源 iframe、子目录、输入隔离、权限、尺寸变化及卸载证据仍保存在 [旧 run-6](../evidence/lawson-integration-step-1/run-6/embed.json)。它们是可行性依据，不能替代新版正式容器的集成验收。
