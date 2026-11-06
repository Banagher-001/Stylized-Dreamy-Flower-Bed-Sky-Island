# 可选最终验收工具

应用本身只需要 Node.js / npm。这里的工具用于工程复验，需要 Python 3、Playwright 1.62.0 和 Pillow 13.0.0；不加入应用依赖。

## 启动

仓库根目录中，分别在后台运行开发与生产复验服务：

```bash
npm ci
npm run dev -- --port 5173 --strictPort
npm run build
node scripts/serve-dist.mjs dist 4174
```

`serve-dist.mjs` 只监听本机，实际发送 gzip，哈希资源使用 immutable 缓存，入口重新验证。它用于本地产物复验；生产网站可直接托管 `dist/`。

另行准备可选工具：

```bash
python -m pip install -r tests/final/requirements.txt
python -m playwright install --with-deps firefox webkit
```

Chromium 默认使用 `/usr/bin/chromium`，可设置 `CHROMIUM_EXECUTABLE`。Linux 下 Firefox/WebKit 的有界面测试需要显示服务，例如 Xvfb。其他系统应按实际环境配置显示与浏览器依赖。

## 功能与 GPU 检查

```bash
python tests/final/browser_check.py --engine chromium
python tests/final/browser_check.py --engine firefox
python tests/final/browser_check.py --engine webkit
```

可通过 `--production`、`--development` 指定服务地址。`--reference <目录>` 只用于同浏览器/同渲染环境的精确回归；目录应包含 `baseline-native.png` 和 `baseline-pixel.png`。跨设备采用色板、关键区域和容差检查。

采样棋盘在绘制同帧直接读取 GPU 帧缓冲，检查仅黑白两色及严格 2×2 格。GTK WebKit 的临时测试画布截图可能滞后，不能用旧截图替代同帧数据。真实场景另行检查可见颜色、截图、按钮和恢复行为。

Firefox 会为合法的线性深度比较产生一类上游 PCF 提示；全部日志保留在结果中，和故障注入时预期的上下文丢失日志分开。未识别的异常、警告或 HTTP 失败仍使脚本失败。Firefox 的零警告目标单列为未满足，不能声称所有平台零警告。

本次云环境的 WebKit 使用 Linux GTK、Xvfb 和软件 OpenGL，不是 Safari 实机。报告中的 `Apple GPU` 是引擎返回的匿名化字符串，不能证明物理 GPU。临时启动器仅补充工作区动态库路径；实际 WebGL 渲染与像素回读均已验证。

## 其他复验

```bash
python tests/final/lifecycle_check.py
python tests/final/fallback_check.py
python tests/final/network_check.py
python tests/final/clean_build_check.py
python tests/final/stability_check.py
```

- `lifecycle_check.py` 检查暂停/隐藏后停止持续绘制，以及 20 次销毁后监听器和观察器归零。
- `fallback_check.py` 真实禁用 WebGL，检查可读提示、控件禁用和画布清理；预期故障日志单列。
- `network_check.py` 使用实际 gzip 服务和 1.6Mbps / 150ms 限速，三次禁用 HTTP 缓存测量。记录实际响应体字节及场景可见/可操作时间。
- `clean_build_check.py` 在隔离临时目录复装依赖并比较 `dist/` 摘要。可用 `COURTYARD_NPM_CACHE` 指定可写 npm 缓存。
- `stability_check.py` 连续运行真实墙钟 10 分钟，再进行 50 次模式变化。资源与软件帧间隔属于云环境诊断；不会计为硬件 FPS 达标。

运行前应创建 `docs/evidence/step-9/`。脚本会更新该目录中的结果，请先保留需要的既有证据。长时间检查每 30 秒输出进度，无需额外截图或录屏。

## 真实设备补验

参见 `docs/step-9-platform-matrix.md`。在真实设备前台播放，预热 5 秒后，可在开发者工具中加载 `measure_frames.js`，运行：

```js
await measureCourtyardFrames(60000)
```

重复三次，另记机型、系统、GPU、刷新率、电源状态及观看模式。该工具只观察应用实际 RAF，不自己生成动画；测试期间离开页面会使可见性标记无效。它不取代实际硬件、触控或 Safari 验证。
