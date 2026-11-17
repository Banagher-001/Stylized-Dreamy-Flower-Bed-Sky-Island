# 关于我与工具卡维护

当前运行内容位于 src，浏览器不读取 docs/evidence。不要将历史证据当作运行资产，也不要用旧归档覆盖新版。

## 正文与资产

`src/tour/about-refresh/content.ts` 是关于我、经历、22 张卡及七类分类的当前正文。姓名、公司、教育与能力描述按已确认事实维护；不新增未经确认的项目、奖项、熟练程度、量化业绩或客户成果。当前 About 没有项目/奖项区。AI 影像的样片标记由 `src/tour/filmContent.ts` 维护，真实作品替换时同时填写职责和准确说明。

工具图标在 `src/assets/tool-marks/`。每工具保留一个实体与稳定 ID；分类、固定阅读、全量列表返回依赖该 ID。新增卡时同步分类、顺序、详情与可访问名称，不用克隆卡片制造无尽滚动。

`src/tour/projectContent.ts` 与 `experimentContent.ts` 管理 Coding 入口和档案。罗森、瓶中海洋原网页在 public/experiments 下，与主站通过独立文档隔离。替换原网页应验证它自己的相机、控制台、键盘、截图及资源路径；不向原网页强行注入主站滚轮处理。

## 动态与输入约束

工具控制器位于 `src/tour/about-refresh/`。入场只播放首批四卡，其后使用既有横向轨道；悬停、固定阅读、帮助、全量列表、离场、布局转换分别持有自己的暂停，不得在关闭某个面板时覆盖用户主动暂停。

保留第十三步的衔接：触摸按钮持有原生 click 目标，超过 8px 才交给滑动；鼠标识别使用捕获阶段，确保首次悬停可用。原生触摸/滚动时内容容量探测延后至滚动安静；视口、字体变化保留强制测量。详情用真实 DOM 展开，减少动态时不强行飞行。

`createReadingLayout.ts` 按真实可用空间判断稳定/沉浸模式，不以降低正文安全边界换取效果。切换要保留分类、固定对象、有效阅读位置和可达焦点；不恢复旧指针坐标、旧惯性与未完成飞行。WebGL 恢复的 restored / ready 分别表示连接与首帧，不得为刷新状态强行滚回封面。

## 验证与重新交付

1. `npm run build`：严格类型与生产构建。
2. 用 HTTP 生产服务器验证变更相关路线；正文、按钮、图片不能被新效果遮挡。
3. 根据变化选择 `tests/about-refresh-final/browser.py`、`embedded.py`、`stability.py`；脚本参数见下方。Playwright 为外部验收工具，不是网站运行依赖。
4. 更新版本身份与清单，生成新 ZIP；不覆盖历史包。解压到新目录，源码独立 npm ci / build，并用根路径和子路径打开成品。

```bash
python tests/about-refresh-final/browser.py --origin http://127.0.0.1:4173/ --out /tmp/garden-check
python tests/about-refresh-final/embedded.py --origin http://127.0.0.1:4173/ --out /tmp/garden-originals
python tests/about-refresh-final/stability.py --origin http://127.0.0.1:4173/ --out /tmp/garden-ten-minutes --seconds 600
```

每次使用新的输出目录。浏览器脚本需 Python Playwright 与 Chromium；可设 CHROMIUM_EXECUTABLE。`--engine firefox` 可检查第二引擎，`--only` 选择完整路线名称。环境专属的 DISPLAY/图形库可通过 `--env-file` 提供；普通机器通常不需要。

本次包内不含大体积历史证据。仓库中的第十四步报告将通过记录链接到构建、真实输入截图、连续运行、包内文件哈希、独立安装/构建与清理结果。前十三步和此前作品接入报告保持原样。
