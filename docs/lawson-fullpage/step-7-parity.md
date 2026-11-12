# 第七步：原页与内嵌逐项功能对照

已完成固定原版本的 41 控件、13 条键位记录、17 类拾取及三辆车完整流程对照。原页正常项在正式内嵌中保持可用；原页已有问题单独列明，未修复或包装成通过。候选：`lawson-fullpage-step7-882322e9045fcdba`。

原运行文件保持 46 个、20,332,784 字节，源、公有目录和构建目录 SHA256 一致。主验证为 Chromium 155.0.8059.79、Linux Mesa 软件渲染；原页与子文档匹配 CSS 视口。默认界面 1440×900／1366×768，较重功能对照 960×540；通过原画质按钮选择 low，默认状态在选择前采集。时间、相机、暂停等均使用原输入；调试 API 用于读数或明确标注的观察视角，不代替实际点击。

## 41 个原控件

32 个静态按钮、1 个滑杆、8 个动态灯光控件。控件清单与原 41 个调试 API 清单是两个概念，本次不宣称逐项验证全部开发 API。

| 项目 | 原页 | 内嵌 | 结论 |
|---|---|---|---|
| 原错误重试 | [记录](../evidence/lawson-fullpage-step-7/standalone-native-retry/readiness.json) · `READINESS.retry` | [记录](../evidence/lawson-fullpage-step-7/recovery-chromium/browser.json) · `recovery original fatal retry and host retry` | 通过 |
| 全屏 | [记录](../evidence/lawson-fullpage-step-7/standalone-controls/controls.json) · `BUTTON.btn-fullscreen` | [记录](../evidence/lawson-fullpage-step-7/recheck-embedded-controls/controls.json) · `BUTTON.btn-fullscreen` | 通过 |
| 画质 | [记录](../evidence/lawson-fullpage-step-7/standalone-controls/controls.json) · `BUTTON.btn-settings` | [记录](../evidence/lawson-fullpage-step-7/recheck-embedded-controls/controls.json) · `BUTTON.btn-settings` | 通过 |
| 帮助打开 | [记录](../evidence/lawson-fullpage-step-7/standalone-controls/controls.json) · `BUTTON.help` | [记录](../evidence/lawson-fullpage-step-7/recheck-embedded-controls/controls.json) · `BUTTON.help` | 通过 |
| 帮助关闭 | [记录](../evidence/lawson-fullpage-step-7/standalone-controls/controls.json) · `BUTTON.help` | [记录](../evidence/lawson-fullpage-step-7/recheck-embedded-controls/controls.json) · `BUTTON.help` | 通过 |
| 面板折叠 | [记录](../evidence/lawson-fullpage-step-7/standalone-controls/controls.json) · `BUTTON.panel-collapse` | [记录](../evidence/lawson-fullpage-step-7/recheck-embedded-controls/controls.json) · `BUTTON.panel-collapse` | 通过 |
| 白天 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-supplement/supplement.json) · `ENV.presets` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-supplement/supplement.json) · `ENV.presets` | 通过 |
| 黄昏 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-supplement/supplement.json) · `ENV.presets` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-supplement/supplement.json) · `ENV.presets` | 通过 |
| 夜晚 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-supplement/supplement.json) · `ENV.presets` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-supplement/supplement.json) · `ENV.presets` | 通过 |
| 时间滑杆 | [记录](../evidence/lawson-fullpage-step-7/standalone-controls/controls.json) · `INPUT.time-slider` | [记录](../evidence/lawson-fullpage-step-7/recheck-embedded-controls/controls.json) · `INPUT.time-slider` | 通过 |
| 灯光全开 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-supplement/supplement.json) · `LIGHT.all-actual` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-supplement/supplement.json) · `LIGHT.all-actual` | 通过 |
| 灯光全关 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-supplement/supplement.json) · `LIGHT.all-actual` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-supplement/supplement.json) · `LIGHT.all-actual` | 通过 |
| 店内灯光 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-supplement/supplement.json) · `ACTUAL.LIGHT.StoreInterior` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-supplement/supplement.json) · `ACTUAL.LIGHT.StoreInterior` | 通过 |
| LAWSON 招牌 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-supplement/supplement.json) · `ACTUAL.LIGHT.LawsonSign` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-supplement/supplement.json) · `ACTUAL.LIGHT.LawsonSign` | 通过 |
| 外墙灯带 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-supplement/supplement.json) · `ACTUAL.LIGHT.FacadeStrip` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-supplement/supplement.json) · `ACTUAL.LIGHT.FacadeStrip` | 通过 |
| 路灯 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-supplement/supplement.json) · `ACTUAL.LIGHT.StreetLamp` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-supplement/supplement.json) · `ACTUAL.LIGHT.StreetLamp` | 通过 |
| 冷柜灯光 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-supplement/supplement.json) · `ACTUAL.LIGHT.CoolerLighting` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-supplement/supplement.json) · `ACTUAL.LIGHT.CoolerLighting` | 通过 |
| 售货机灯光 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-supplement/supplement.json) · `ACTUAL.LIGHT.VendingLighting` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-supplement/supplement.json) · `ACTUAL.LIGHT.VendingLighting` | 通过 |
| 墙面暖光 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-supplement/supplement.json) · `ACTUAL.LIGHT.WarmExterior` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-supplement/supplement.json) · `ACTUAL.LIGHT.WarmExterior` | 通过 |
| 车辆灯光 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-supplement/supplement.json) · `ACTUAL.LIGHT.VehicleLights` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-supplement/supplement.json) · `ACTUAL.LIGHT.VehicleLights` | 通过 |
| 车流暂停与恢复 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-supplement/supplement.json) · `TRAFFIC.actual` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-supplement/supplement.json) · `TRAFFIC.actual` | 通过 |
| 车流重置 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-supplement/supplement.json) · `TRAFFIC.actual` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-supplement/supplement.json) · `TRAFFIC.actual` | 通过 |
| 慢速 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-supplement/supplement.json) · `TRAFFIC.actual` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-supplement/supplement.json) · `TRAFFIC.actual` | 通过 |
| 正常速度 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-supplement/supplement.json) · `TRAFFIC.actual` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-supplement/supplement.json) · `TRAFFIC.actual` | 通过 |
| 快速 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-supplement/supplement.json) · `TRAFFIC.actual` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-supplement/supplement.json) · `TRAFFIC.actual` | 通过 |
| 车辆 A | [记录](../evidence/lawson-fullpage-step-7/full-standalone-traffic/traffic.json) · `CYCLE.A` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-traffic/traffic.json) · `CYCLE.A` | 通过 |
| 车辆 B | [记录](../evidence/lawson-fullpage-step-7/full-standalone-traffic/traffic.json) · `CYCLE.B` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-traffic/traffic.json) · `CYCLE.B` | 通过 |
| 车辆 C | [记录](../evidence/lawson-fullpage-step-7/full-standalone-traffic/traffic.json) · `CYCLE.C` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-traffic/traffic.json) · `CYCLE.C` | 通过 |
| 店员 A | [记录](../evidence/lawson-fullpage-step-7/full-standalone-supplement/supplement.json) · `BUTTON.clerk-A` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-supplement/supplement.json) · `BUTTON.clerk-A` | 通过 |
| 店员 B | [记录](../evidence/lawson-fullpage-step-7/full-standalone-supplement/supplement.json) · `BUTTON.clerk-B` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-supplement/supplement.json) · `BUTTON.clerk-B` | 通过 |
| 全景 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-supplement/supplement.json) · `CAMERA.hero` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-supplement/supplement.json) · `CAMERA.hero` | 通过 |
| 正面 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-supplement/supplement.json) · `CAMERA.front` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-supplement/supplement.json) · `CAMERA.front` | 通过 |
| 左侧 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-supplement/supplement.json) · `CAMERA.left` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-supplement/supplement.json) · `CAMERA.left` | 通过 |
| 后侧 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-supplement/supplement.json) · `CAMERA.rear` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-supplement/supplement.json) · `CAMERA.rear` | 通过 |
| 俯视 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-supplement/supplement.json) · `CAMERA.top` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-supplement/supplement.json) · `CAMERA.top` | 通过 |
| 室内 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-supplement/supplement.json) · `CAMERA.interior` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-supplement/supplement.json) · `CAMERA.interior` | 通过 |
| 收银区 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-supplement/supplement.json) · `CAMERA.checkout` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-supplement/supplement.json) · `CAMERA.checkout` | 通过 |
| 车辆镜头 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-supplement/supplement.json) · `CAMERA.vehicle` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-supplement/supplement.json) · `CAMERA.vehicle` | 通过 |
| 屋顶 | [记录](../evidence/lawson-fullpage-step-7/roof-final-standalone/supplement.json) · `BUTTON.roof-actual` | [记录](../evidence/lawson-fullpage-step-7/roof-final-embedded/supplement.json) · `BUTTON.roof-actual` | 通过 |
| 漫游 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-keyboard/keyboard.json) · `POINTER.walk-look` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-keyboard/keyboard.json) · `POINTER.walk-look` | 通过 |
| 重置视角 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-supplement/supplement.json) · `INPUT.orbit` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-supplement/supplement.json) · `INPUT.orbit` | 通过 |

灯光除了 UI 状态，还记录真实光源和发光材质。屋顶记录实际可绘制节点、祖先可见性、显式 roofRoot 及原目标计数；空分组自身的 visible 不等于可见几何体。重置按钮的实际镜头恢复与原 R 惯性问题分别记录，未承诺所有拖动时机像素精确复位。

## 13 条键位记录

| 项目 | 原页 | 内嵌 | 结论 |
|---|---|---|---|
| R | [记录](../evidence/lawson-fullpage-step-7/standalone-controls/controls.json) · `KEY.KeyR` | [记录](../evidence/lawson-fullpage-step-7/recheck-embedded-controls/controls.json) · `KEY.KeyR` | 原页已有问题 |
| 1 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-supplement/supplement.json) · `KEY.123` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-supplement/supplement.json) · `KEY.123` | 通过 |
| 2 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-supplement/supplement.json) · `KEY.123` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-supplement/supplement.json) · `KEY.123` | 通过 |
| 3 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-supplement/supplement.json) · `KEY.123` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-supplement/supplement.json) · `KEY.123` | 通过 |
| Space | [记录](../evidence/lawson-fullpage-step-7/standalone-controls/controls.json) · `KEY.Space` | [记录](../evidence/lawson-fullpage-step-7/recheck-embedded-controls/controls.json) · `KEY.Space` | 通过 |
| Escape | [记录](../evidence/lawson-fullpage-step-7/full-standalone-keyboard/keyboard.json) · `POINTER.walk-look` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-keyboard/keyboard.json) · `POINTER.walk-look` | 通过 |
| W | [记录](../evidence/lawson-fullpage-step-7/full-standalone-keyboard/keyboard.json) · `KEY.KeyW` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-keyboard/keyboard.json) · `KEY.KeyW` | 原页已有问题 |
| A | [记录](../evidence/lawson-fullpage-step-7/full-standalone-keyboard/keyboard.json) · `KEY.KeyA` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-keyboard/keyboard.json) · `KEY.KeyA` | 通过 |
| S | [记录](../evidence/lawson-fullpage-step-7/full-standalone-keyboard/keyboard.json) · `KEY.KeyS` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-keyboard/keyboard.json) · `KEY.KeyS` | 原页已有问题 |
| D | [记录](../evidence/lawson-fullpage-step-7/full-standalone-keyboard/keyboard.json) · `KEY.KeyD` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-keyboard/keyboard.json) · `KEY.KeyD` | 通过 |
| 左 Shift | [记录](../evidence/lawson-fullpage-step-7/full-standalone-keyboard/keyboard.json) · `KEY.ShiftLeft` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-keyboard/keyboard.json) · `KEY.ShiftLeft` | 通过 |
| 右 Shift | [记录](../evidence/lawson-fullpage-step-7/full-standalone-keyboard/keyboard.json) · `KEY.ShiftRight` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-keyboard/keyboard.json) · `KEY.ShiftRight` | 通过 |
| N（原说明提及、实际未绑定） | [记录](../evidence/lawson-fullpage-step-7/standalone-controls/controls.json) · `DOC.KeyN` | [记录](../evidence/lawson-fullpage-step-7/recheck-embedded-controls/controls.json) · `DOC.KeyN` | 原页已有问题 |

R 拖动后惯性、起点 W/S 碰撞与 N 未绑定均在两页复现，归为原页问题。漫游中 R 后再触发 UI 同步的缓存问题另见 [原页](../evidence/lawson-fullpage-step-7/full-standalone-keyboard/keyboard.json) · `BOUNDARY.R-in-walk`／[内嵌](../evidence/lawson-fullpage-step-7/full-embedded-keyboard/keyboard.json) · `BOUNDARY.R-in-walk`。A/D 和左右 Shift 加速采用真实平面位移，未把上下摆动作为 W/S 行走成功。

## 17 类场景拾取

| 项目 | 原页 | 内嵌 | 结论 |
|---|---|---|---|
| 招牌 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-targets/targets.json) · `TARGET.sign` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-targets/targets.json) · `TARGET.sign` | 通过 |
| 外墙灯带 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-targets/targets.json) · `TARGET.facade` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-targets/targets.json) · `TARGET.facade` | 通过 |
| 门 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-targets/targets.json) · `TARGET.door` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-targets/targets.json) · `TARGET.door` | 通过 |
| 售货机 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-targets/targets.json) · `TARGET.vending` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-targets/targets.json) · `TARGET.vending` | 通过 |
| 购物篮：原绑定冷柜灯 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-targets/targets.json) · `TARGET.basket` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-targets/targets.json) · `TARGET.basket` | 通过 |
| 收银台 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-targets/targets.json) · `TARGET.checkout` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-targets/targets.json) · `TARGET.checkout` | 通过 |
| 货架 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-targets/targets.json) · `TARGET.shelf` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-targets/targets.json) · `TARGET.shelf` | 通过 |
| 酒类区 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-targets/targets.json) · `TARGET.alcohol` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-targets/targets.json) · `TARGET.alcohol` | 通过 |
| 关东煮蒸汽 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-targets/targets.json) · `TARGET.oden` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-targets/targets.json) · `TARGET.oden` | 通过 |
| 店员 A 固定岗位 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-targets/targets.json) · `TARGET.clerkA` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-targets/targets.json) · `TARGET.clerkA` | 通过 |
| 店员 B 固定岗位 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-targets/targets.json) · `TARGET.clerkB` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-targets/targets.json) · `TARGET.clerkB` | 通过 |
| ATM | [记录](../evidence/lawson-fullpage-step-7/full-standalone-targets/targets.json) · `TARGET.atm` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-targets/targets.json) · `TARGET.atm` | 通过 |
| 卧式冰柜 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-targets/targets.json) · `TARGET.freezer` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-targets/targets.json) · `TARGET.freezer` | 通过 |
| 饮料冷藏柜 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-targets/targets.json) · `TARGET.cooler` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-targets/targets.json) · `TARGET.cooler` | 通过 |
| 微波炉 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-targets/targets.json) · `TARGET.microwave` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-targets/targets.json) · `TARGET.microwave` | 通过 |
| 用餐区 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-targets/targets.json) · `TARGET.dining` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-targets/targets.json) · `TARGET.dining` | 通过 |
| 咖啡机 | [记录](../evidence/lawson-fullpage-step-7/full-standalone-targets/targets.json) · `TARGET.coffee` | [记录](../evidence/lawson-fullpage-step-7/full-embedded-targets/targets.json) · `TARGET.coffee` | 通过 |

通过真实指针命中原物件，读取原处理结果及实际材质、灯光、门位移、蒸汽或镜头变化。观察包装以原参数调用原函数一次；没有用 clickAt、activate 或业务 API 派发替代用户点击。购物篮切冷柜灯、店员聚焦固定岗位均保留原绑定。车辆不属于原 17 类拾取，仍通过原车辆按钮演示。

## 连续车辆与店员流程

| 车辆 | 原页完整流程墙钟 | 内嵌完整流程墙钟 | 结果 |
|---|---:|---:|---|
| 车辆 A 完整流程 | 131.1 秒 | 129.8 秒 | 通过 |
| 车辆 B 完整流程 | 114.3 秒 | 115.1 秒 | 通过 |
| 车辆 C 完整流程 | 100.1 秒 | 102.3 秒 | 通过 |

每辆车均实际经过进场、停靠、倒车、离场和变为非活动/不可见的完整周期，记录车轮和倒车灯。使用原 UI 的 1.8 档，未改变原时钟、RAF、dt 或强行完成任务；采样未宣称穷举每一短暂中间状态。云端墙钟时间不作为访客设备性能或硬件 FPS 的承诺。

两名店员在连续流程中的实际任务：

- 原页店员 A：check_display, impulse_tidy, nearby_shelf, short_wait。
- 原页店员 B：floor_clean, restock, shelf_inspect。
- 内嵌店员 A：bag_check, impulse_tidy, look_around, nearby_shelf, observe_entrance, short_wait, tidy_counter。
- 内嵌店员 B：dining_tidy, hotfood_check, shelf_inspect。

两页保留随机自主行为，观察到的任务顺序和种类不同；没有调用强制任务接口，也不宣称所有随机分支已穷举。

原有问题总表保留在 [原版记录](original-issues.md)，本次最终验收及边界见 [验收报告](step-7-verification.md)。
