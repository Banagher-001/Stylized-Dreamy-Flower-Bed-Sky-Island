# 第一步复核方法

这些脚本是核查工具，不属于访客运行资源，也不是罗森的新启动入口。需要本仓库与 `luosen-asset` 的相应版本、Python Playwright、Chromium，以及有 WebGL 的浏览器环境。本轮云环境已有这些依赖，未修改两套场景的依赖或生产配置。

## 目录与版本

- 个人网站：`/workspace/Stylized-Dreamy-Flower-Bed-Sky-Island`，提交 `4a6dd7c5c9c126ab3b9319fab5d8ea16a704dae8`。
- 罗森：`/workspace/luosen-asset`，提交 `95dad9881a7b9d31c0ac635f1f335055d8cb3cc4`。
- 运行副本：`/tmp/lawson-step1-audit/`。由依赖清单复制原始文件，分别放在 root 和 experiments/lawson 下。
- 本步证据：`docs/evidence/lawson-integration-step-1/`。

先运行资源核查，再单独启动静态服务：

```bash
python tests/lawson-integration/step1_assets.py
python tests/lawson-integration/step1_server.py
```

服务只监听 `127.0.0.1:4190`。独立入口 `/root/index.html`，子目录入口 `/experiments/lawson/index.html`，临时嵌入诊断 `/harness.html`。页面内容只来自临时副本，没有读取或公开仓库的 `.git`、Blender 工程等资料。

## 本轮云环境浏览器

默认命令沙箱禁止浏览器需要的部分 socket，本轮浏览器与本地服务使用经工具允许的沙箱外执行。SwiftShader 可加载场景，但本场景持续绘制非常慢；后续使用独立 Xvfb :106、Mesa llvmpipe 和 `LP_NUM_THREADS=3` 继续核查。两者都是软件渲染。

如需复现本环境的显示服务，使用已存在的二进制与动态库：

```bash
LD_LIBRARY_PATH=/workspace/.cache/browser-deps/root/usr/lib/x86_64-linux-gnu \
  /workspace/.cache/browser-deps/root/usr/bin/Xvfb :106 -screen 0 1600x1000x24 -nolisten tcp
```

功能、嵌入、兼容性和性能分开串行执行，每次使用新的 `--run` 名称，避免覆盖历史证据：

```bash
DISPLAY=:106 LIBGL_ALWAYS_SOFTWARE=1 LP_NUM_THREADS=3 \
  python tests/lawson-integration/step1_browser.py --phase core --run local-core --backend mesa

DISPLAY=:106 LIBGL_ALWAYS_SOFTWARE=1 LP_NUM_THREADS=3 \
  python tests/lawson-integration/step1_browser.py --phase embed --run local-embed --backend mesa

DISPLAY=:106 LIBGL_ALWAYS_SOFTWARE=1 LP_NUM_THREADS=3 \
  python tests/lawson-integration/step1_browser.py --phase compat --run local-compat --backend mesa

DISPLAY=:106 LIBGL_ALWAYS_SOFTWARE=1 LP_NUM_THREADS=3 \
  python tests/lawson-integration/step1_browser.py --phase performance --run local-performance --backend mesa
```

`--only` 可以定向复核一项 core 检查，冷/热加载与原有低画质选择仍会执行。具体历史执行以 JSON 内的脚本 SHA256 和旁边保存的脚本快照为准。

## 观测边界

- 仅在验证上下文包装 RAF 和 GL 绘制方法，记录次数和实际时长；原始时间戳照常传入，不加速场景时间。
- 相机等待依据实际场景 callback 所经过的 capped dt，适配源代码的 0.1 秒上限；这是观察计数，未改动源时钟。
- 通过原有设置按钮选择低画质进行功能检查；默认画质加载和软件性能另有记录。
- 完整车辆周期使用原有 UI 的 1.8 倍速度选项，报告保留真实墙钟时间、各阶段及店员任务变化。
- 手机是 Chromium 视口、DPR 与触摸事件模拟；不等于物理 iOS 或 Android 验收。
- 模型加载失败和 WebGL 不可用均为验证上下文主动注入，须与正常路径日志分别判断。
- 关闭 iframe 后观察旧 RAF/绘制计数停止；GPU 内存释放时机没有专用硬件测量。
- 性能取自本云环境软件驱动，不作为访客设备或硬件 GPU 的帧率保证。
- 性能采样通过源页面已有的 setFreeCamera 接口，固定到源配置中的全景、车辆区域和室内预设位置；核对目标投影落在画面中心后，记录实际回调、墙钟时长和自适应画质。此项用于排除飞行过程，不改动画时钟；真实预设切换、跟车和漫游由 core 功能组验证。

本步结束时只清理自己启动的 4190 服务与 :106 显示，其他开发服务保留。未来重跑先启动自己的诊断服务。
