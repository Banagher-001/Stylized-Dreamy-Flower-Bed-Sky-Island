# 当前个人作品集复验

此目录验证个人作品集页面。`tests/final/` 保留第九步独立场景的历史检查，涉及旧页面按钮计数等假设；当前页面回归使用本目录，不将旧报告当作新增布局的通过证据。

应用使用 Node.js；浏览器检查另需 Python、Playwright 和 Pillow，版本见 `tests/final/requirements.txt`。本地先执行 `npm ci`、`npm run build`，并在另一个终端运行 `npm run preview -- --port 4173 --strictPort`。

```bash
python tests/portfolio/browser_check.py --engine chromium
python tests/portfolio/browser_check.py --engine firefox
python tests/portfolio/browser_check.py --engine webkit
```

可用 `--url` 更换本地复验地址。Chromium 默认使用 `/usr/bin/chromium`，可设置 `CHROMIUM_EXECUTABLE`；Firefox/WebKit 需安装 Playwright 浏览器和原生依赖，Linux 下还需显示服务。可选 `COURTYARD_WEBKIT_EXECUTABLE` 适用于当前云环境已配置的 GTK 启动器。详情参见原 [工具说明](../final/README.md)。

每引擎 9 组验证：可见庭院/个人资料/样片标注、实际模式画面回切、分类、键盘与弹窗焦点、媒体结构、真实滚动停绘与时钟冻结、响应式与锚点、上下文恢复、原始诊断。Chromium 覆盖 8 组尺寸/DPR，另两引擎覆盖桌面和手机模拟各一组。

视频实际解码播放和关闭停播在 Chromium 测试；Firefox/WebKit 的报告记录支持字符串与结构，不把未播放判为已经验证。真实手机、Safari 和物理 GPU 性能不在当前云端验收范围。Firefox 已知 PCF 深度过滤提示与故障注入日志保留，未识别异常会失败。

结果写入 `docs/evidence/portfolio/`，重跑会更新对应引擎记录和截图。不要把软件渲染、模拟手机或既有按时间采样的视频当作硬件性能证据。
