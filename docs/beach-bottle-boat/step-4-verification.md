# 第四步验收：三作品选择、瓶中海洋档案与独立打开

第四步完成。Coding 区按 LAWSON → BOTTLE OCEAN → COURTYARD 排列，默认罗森；瓶中海洋已有真实封面、简介、档案与独立打开入口。主站内显示准确的“可独立体验”准备页，尚未创建瓶中海洋 iframe。未提交、上传或发布。日期：2026-11-13（Asia/Shanghai）。

实际改动：

| 文件 | 改动 |
|---|---|
| projectContent.ts | 三作品统一顺序与身份、真实封面导入、档案/准备页元数据、独立网页类型守卫 |
| createExperimentReader.ts | 按统一顺序生成三个索引；左右循环、Home/End 和当前作品动作 |
| createProjectViewer.ts | 独立网页的静态展示与档案按类型处理；准备页内容随作品更新；动态状态带作品 owner |
| projectHost.css | 三列索引、窄屏换行、独立网页宿主布局、瓶中海洋档案与准备页样式 |
| startTourPrototype.ts | 罗森状态更新显式传入 lawson 身份；运行器与原导览/相机机制保持原样 |

其余 90 项既有生产输入不变，experiment.css 未修改。before/after 快照、实际源文件摘要及完整差异见 [candidate-manifest.json](../evidence/beach-bottle-boat-step-4/candidate-manifest.json) 和 [product.diff](../evidence/beach-bottle-boat-step-4/product.diff)。未来产品源码可按后续授权继续修改，本步封存保存的是独立 after 副本，不把可变源码作为历史封存目标。

实际验收：

| 引擎 / 记录 | 检查数 | 范围 |
|---|---:|---|
| chromium 155.0.8059.79 / chromium | 12 | 主流程、根/子路径、故障、原作品、阅读与尺寸 |
| firefox 153.0 / firefox | 4 | 三作品、键盘、档案、原网页独立打开 |
| webkit 26.5 / webkit | 4 | 三作品、键盘、档案、原网页独立打开 |
| chromium 155.0.8059.79 / guide-motion | 1 | 真实活动导览中断、暂停/播放选择返回 |

21 项实际记录全部通过，对应 16 项执行标准：[final-summary.json](../evidence/beach-bottle-boat-step-4/final-summary.json)。本轮未出现待补核或失败复测，没有用旧截图替代新记录。

- 三项原生点击与方向键循环的标题、封面、摘要、当前项及 aria 归属一致；Home/End、Tab/Shift+Tab、Enter/Space 正常。
- 档案以“让一片海，托起一艘船。”、真实大图和三组编号功能呈现；原罗森内容及庭院片段仍各自保留。
- 真实图片请求被暂停、切换到庭院后再送达，当前作品保持庭院且图片状态正确；图片请求失败时有反馈，档案和独立入口仍可用，原重试按钮可恢复图片。
- 主站在仅浏览预览、档案或准备页时没有请求瓶中海洋运行 HTML，没有其 iframe。准备页为 prepared、aria-busy=false，无无效重试或假 ready。
- 根路径和实际 /portfolio-check/ 前缀均通过真实链接打开新窗口，当前地址正确，取得原 HTML SHA256，原场景就绪并响应波高和镜头原生操作。三个引擎均实际打开原页。
- 罗森原完整现场实际达到 ready；关闭后转到瓶中海洋，旧 iframe 已移除且 prepared 状态没有被旧回调覆盖。
- 庭院正常/像素按钮与动效切换可用；档案片段由真实点击开始播放，currentTime>0，关闭后视频移除。Coding 当前选瓶中海洋时，水潭入口仍打开 courtyard。
- 测试仅对宿主文档禁用 WebGL 创建，实际触发宿主初始化失败；瓶中海洋准备页/独立链接仍可用，庭院现场按原规则禁用而档案可用。这是明确故障注入，不代表真实 GPU 驱动故障。
- 1920×1080、1440×900、1280×720、390×844、844×390、320×740 以及 html 根字号 200% 条件无页面横向溢出，三项至少 44×44，档案可滚动且返回可见。手机模拟用真实触摸点按选择瓶中海洋；不是物理手机或系统文字放大实测。
- 活动导览由原按钮实际启动，随后手动选择瓶中海洋使其停止；作品返回后不自行继续。主站分别处于暂停和播放时打开/关闭作品，返回保留原选择。关闭档案恢复有效焦点及原阅读位置；开发服务下关于我、AI影像章节实际可读。

构建、日志与完整性：

- npm run typecheck 与 npm run build 均成功；新构建 69 个文件，真实封面进入 assets 且与源 PNG 摘要相同。瓶中海洋原 HTML 在 public 和构建产物仍为 941feb2ea6ddd3cc93aad5b0b92dbca52ee66a3e1098fee0dbf16f01ca63d1ef。
- 正常路径没有 pageerror 或 console.error，也没有外部 HTTP 请求尝试。图片故障及宿主 WebGL 禁用产生的日志按 FAULT 场景单列。
- 罗森准备完后主动关闭 iframe，三个延迟车型请求以 net::ERR_ABORTED 取消，这是该次卸载的预期结果；原始记录保留，未归为加载失败。Firefox 的软件 WebGL 深度纹理过滤实现警告有记录，未视作产品脚本异常或硬件兼容证明。
- 原仓库 44 个文件、罗森 46 个运行文件、瓶中海洋 HTML/声明/来源和原封面均不变；8 组既有历史封存及第一、三步封存共 10 组全部校验通过。原 dist 的 65 个文件未覆盖。
- 浏览器均关闭，3 个本步自有服务停止；专用临时构建目录在保存摘要并复核后清理，未停止其他服务。

画面：[桌面档案](../evidence/beach-bottle-boat-step-4/chromium/bottle-archive.png) · [可独立体验页](../evidence/beach-bottle-boat-step-4/chromium/bottle-prepared.png) · [手机档案](../evidence/beach-bottle-boat-step-4/chromium/layout-390x844.png)。

范围：本轮主要使用 Linux Chromium 和软件图形环境；Firefox、Linux WebKit 各 4 项代表操作，不是全量原 34 控件复验或真机 Safari。原页亮度、镜头惯性、图形丢失语义未修改；完整 iframe 输入/生命周期、实际 hidden 恢复、真机与硬件性能继续由后续验证。第二步仍仅有标准，未冒充完成其正式交付。

[第五步交接](step-4-handoff.md)。本步独立封存复核命令：python tests/beach-bottle-boat-step-4/finalize.py --verify-only。此命令核对封存的本步快照及此前历史，不要求未来经授权修改的产品源码仍等于本步候选。
