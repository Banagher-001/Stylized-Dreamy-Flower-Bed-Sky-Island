# 新版第一步复核方法

## 固定输入

- 主站提交：`4a6dd7c5c9c126ab3b9319fab5d8ea16a704dae8`。
- 罗森提交：`95dad9881a7b9d31c0ac635f1f335055d8cb3cc4`。
- 原入口：`lawson-blender/out/web_final/index.html`。
- [46 个运行文件及 SHA256](../evidence/lawson-fullpage-step-1/runtime-manifest.json)。网页内所有依赖都在本地，Three.js 为 r160；主站使用的版本不参与原页测试。

将运行清单中的文件按原相对路径复制到独立临时目录，通过 HTTP 静态服务器打开，不能直接用 `file://` 代替。此次临时副本是 `/tmp/lawson-fullpage-step1/`，地址为 `http://127.0.0.1:4191/index.html`，它只是核查工具，不是已发布网页。

## 浏览器环境

Python Playwright、系统 Chromium `155.0.8059.79`、独立 Xvfb、Mesa llvmpipe 软件 WebGL。设置 `LIBGL_ALWAYS_SOFTWARE=1`、`LP_NUM_THREADS=3`；浏览器启动参数为 `--no-sandbox --use-gl=angle --use-angle=gl --ignore-gpu-blocklist`。

测试串行运行，避免同时开启多个 3D 场景干扰结果。最初使用独立显示器 `:107`；环境重新启动后使用 `:108`。物理手机、硬件 GPU 帧率、其他浏览器均不在本次实测范围内。

## 测试工具

位于 `tests/lawson-fullpage/`，从主站仓库根目录运行；每次使用新的 `--run` 名，脚本拒绝覆盖已有结果。

```bash
DISPLAY=:108 LIBGL_ALWAYS_SOFTWARE=1 LP_NUM_THREADS=3 python tests/lawson-fullpage/controls.py --run replay-controls
DISPLAY=:108 LIBGL_ALWAYS_SOFTWARE=1 LP_NUM_THREADS=3 python tests/lawson-fullpage/targets.py --run replay-targets
DISPLAY=:108 LIBGL_ALWAYS_SOFTWARE=1 LP_NUM_THREADS=3 python tests/lawson-fullpage/keyboard.py --run replay-keyboard
DISPLAY=:108 LIBGL_ALWAYS_SOFTWARE=1 LP_NUM_THREADS=3 python tests/lawson-fullpage/traffic.py --run replay-traffic
DISPLAY=:108 LIBGL_ALWAYS_SOFTWARE=1 LP_NUM_THREADS=3 python tests/lawson-fullpage/readiness.py --run replay-readiness
```

运行前需启动对应的私有 Xvfb 和 HTTP 服务。`native_keys.py` 只允许向本次核查专用的 `:107` / `:108` 发送系统 Esc 或 Ctrl+T，不操作共享桌面。它通过 X11 `WM_CLASS` 识别可见 Chromium 大窗口；当前 Chromium 没有为该窗口设置旧式 `WM_NAME`，这是早期输入探针失败的原因。

`controls.py --only ID1,ID2`、`keyboard.py --only ID1,ID2` 和 `readiness.py --only ID1,ID2` 支持定向复核；`targets.py --skip sign` 支持中断后只补剩余目标。既有失败、中断、截图和当时的脚本快照全部保留，最终采用项见功能对照表及机器可读汇总。

## 证据规则

1. 默认界面先按原样记录；较重的功能测试随后通过原画质按钮选择 low。车辆快速选项也是原 UI 的 1.8 倍选项。
2. 不改原文件，不修改时钟或 RAF 时间戳，不使用强制店员任务接口制造自主行为。车辆等待可能持续数分钟。
3. 状态 API 用于读数。物件测试只用已有 `setFreeCamera` 定位观察视角，随后通过真实鼠标点击触发原拾取与原处理函数。定位辅助单独记录，不把 API 触发当成点击成功。
4. 观察包装始终以原参数调用原函数一次。记录实际材质、可见性、门位移、镜头、位置或车轮等反馈，不能只看按钮变色。
5. 车辆实时位置采用 `getVehicleState`；`getState().traffic.activePosition` 是 UI 缓存，不用于证明车辆停止或移动。相机 `project()` 为整数 CSS 像素，不采用浮点精度假设。`debugDoor()` 仅公开左门坐标，不伪造右门坐标。
6. 浏览器级全屏 Esc 需要原生系统输入；CDP 的页面 Esc 不等同于浏览器保留键。全屏按钮退出和系统 Esc 均单独验证。
7. 故障重试测试有意中止一次主模型请求；对应请求错误及 fatal 日志属预期注入。其余正常路径的脚本异常另外核对。
8. 41 个开发者 API 是结构清单，不宣称逐一做过交互验收。随机店员行为按实际观察记录，不宣称穷尽全部任务分支。

## 完整性

最终核对原页 46 个文件、主站 91 个监测输入和旧封存的 77 个文件；原仓库跟踪文件的差异应为空。新版封存清单覆盖新增文档、证据及测试脚本，并排除清单自身。旧封存文件不重写。
