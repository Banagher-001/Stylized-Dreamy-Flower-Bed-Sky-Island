# 关于我改版 · 第三步实现与内容接口

状态：第三步完成。时间 2026-11-15T14:51:56.240900+08:00（Asia/Shanghai）。正式组件和独立开发入口已建立；原个人网页尚未接入新组件。

[打开独立静态组件预览](step-3-preview.html) · [实际验收](step-3-verification.md) · [第四步交接](step-3-handoff.md)

## 输入与内容

第一步固定文案为正文依据，第二步布局为尺寸与空间依据，原文件均保留。21 款工具、1 张能力卡、7 类，分类数量为 3/2/2/6/3/5/1。关于我内容没有项目、奖项、业绩、作品关联或跳转；游族网络没有补写岗位或日期。

正式数据在 src/tour/about-refresh/content.ts。正文转换脚本只在制作阶段读定稿文件；运行组件不读取 docs 或 evidence，也不包含简历原件与来源备注。

| 结构 | 用途 |
|---|---|
| identity | 章节、姓名、职业定位、两句介绍、关键词、化名说明 |
| experience | 三条经历、四个制作环节及完整说明、教育背景 |
| tools | 工具屏标题与介绍 |
| categories | 七类固定 ID、名称及类内 cardIds |
| cards | 唯一 ID、名称、用途、详情、两个标签、类型、分类、两套顺序、首批序位、标识占位 |
| controls | 第一步确定的操作词表，仅启用本步已有功能 |

推荐轨道按 recommendationOrder；分类按 categoryOrder，全部列表按 categories/cardIds 分组。默认首批仍为 Midjourney → ComfyUI → 可灵 → Blender；G1 内部为 Midjourney → 即梦 → ComfyUI，不混用推荐顺序。每张正文只有一份，所有视图按同一 ID 读取。

## 实际文件职责

| 文件 | 职责 |
|---|---|
| src/tour/about-refresh/types.ts | 内容、分类、视图与恢复状态类型 |
| src/tour/about-refresh/content.ts | 正式运行数据、两套排序与首批 ID |
| src/tour/about-refresh/dom.ts | 局部 DOM 创建与边界辅助 |
| src/tour/about-refresh/createAboutView.ts | 三屏、原生次级阅读、宿主接口与清理 |
| src/tour/about-refresh/createToolBrowser.ts | 分类、前后、详情、全部列表、位置与焦点恢复 |
| src/tour/about-refresh/aboutRefresh.css | 组件局部样式与响应式 |
| src/tour/about-refresh/preview.ts / preview.css | 独立开发页的切屏、大字、排版判断与检查入口 |
| dev/about-refresh/index.html | 已有 Vite 下的独立开发入口 |
| docs/about-refresh/step-3-preview.html | 同源组件编译得到的独立单文件预览 |

没有修改主站入口、旧 aboutContent、相机/滚动代码、package.json、锁文件或 Vite 配置。没有增加依赖。

## 三屏与静态操作

A1 默认显示身份、职业定位、两句介绍与关键词，化名来源通过原生 details 展开。A2 默认显示三条经历和四个制作环节，完整说明与教育背景在次级区域。A3 使用独立宽卡牌区。

隐藏屏同时使用 hidden、inert 与 aria-hidden，不参与当前布局和键盘操作。切屏时若焦点仍在即将隐藏的内容，转到新屏标题。

上一张/下一张移动一张并完整呈现对应卡片；首尾有明确禁用状态，不循环。详情按钮可通过点击、Enter 或 Space 展开完整正文，同一时间保留一个卡片详情。静态放大不挤动相邻卡位；手机采用自然向下展开。

桌面当前普通卡片 232×300，桌面放大宽度为 115%，真实高度可随完整内容增加，不硬裁文字。该静态样式不代替第 5 步卡牌实体和第 9、10 步正式悬停/详情设计。

当前提示为“使用前后按钮浏览，按 Enter 展开详情。”或手机的“左右滑动浏览 · 点按查看详情”。自动展示、滚轮加速提示尚未启用。主站继续入口仅在宿主提供 onContinue 时显示；独立预览保留对应空间。

## 全部列表与恢复规则

从任何分类进入全部，均按七类展示 22 张完整正文。轨道和列表不会同时保留两套重复卡牌 DOM。

返回恢复 category、activeId、expandedId，以及锚点卡片与偏移比例；尺寸未变时保留横向位置，尺寸变化时按原锚点卡片重新计算并限制在可用范围。返回焦点放回“查看全部工具”。当次浏览保留状态，刷新按默认开始。

状态是可复制的普通数据：AboutSnapshot 保存屏幕、A1/A2 展开状态和工具浏览状态；ToolBrowserSnapshot 保存 cards/all 模式与 CardsSnapshot；TrackPosition 保存 anchorId、offsetRatio、scrollLeft、viewportWidth。

## 正式宿主接口

createAboutView(host, options) 挂载组件，返回：root、station、setStation、setLayout、measure、captureState、restoreState、dispose。

setStation 只切换内容，不移动相机、不改变主站滚动坐标。setLayout 接收 immersive/stable 及可用高度；measure 返回当前屏幕的实际内容高度和所需高度。宿主负责真实安全区域、全站控件及容量判断。

options.onInteraction 用于通知真实用户操作；恢复状态不作为一次用户输入。options.onLayoutChange 通知次级内容/分类/详情改变；options.onContinue 由宿主注入真实章节跳转。独立预览没有导览回调或主站跳转。

宿主在大字布局时设置 root.dataset.largeText，并据实际字体与可用空间选择稳定阅读。preview.ts 中只演示独立页的容量判断；第四步不能直接把预览页高度当成主站安全高度。

销毁会中止本组件监听、断开 ResizeObserver、取消待执行的恢复帧并移除节点。组件没有自动播放时钟、滚轮监听、全局键盘监听或三维渲染循环。仅独立开发入口拥有预览窗口/字体监听和检查接口。

## 响应式实际结果

| 视口 | A1 | A2 | A3 |
|---|---|---|---|
| 1920×1080 | 沉浸排版 | 沉浸排版 | 沉浸排版 |
| 1440×900 | 沉浸排版 | 沉浸排版 | 沉浸排版 |
| 1366×768 | 沉浸排版 | 沉浸排版 | 稳定阅读 |
| 1280×720 | 沉浸排版 | 沉浸排版 | 稳定阅读 |
| 1024×768 | 稳定阅读 | 稳定阅读 | 稳定阅读 |
| 820×1180 | 稳定阅读 | 稳定阅读 | 稳定阅读 |
| 390×844 | 稳定阅读 | 稳定阅读 | 稳定阅读 |
| 320×740 | 稳定阅读 | 稳定阅读 | 稳定阅读 |
| 844×390 | 稳定阅读 | 稳定阅读 | 稳定阅读 |

这是独立预览的容量结果，未计入真实主站全部控件。手机、短横、大字及减少动态均可稳定阅读；正文至少 16px，主要操作至少 44px。背景为已有庭院封面图，主站实时场景和运镜由第四步接入。

## 开发与单文件预览

运行项目现有 npm run dev，访问终端给出的地址后加 /dev/about-refresh/index.html。该 URL 已在真实 Vite 中验证 A3 → G5 三张 → 全部 22 张 → 返回 G5 三张。

单文件预览由 evidence/step-3/build-preview.mjs 使用现有 Vite 编译同一套组件，再内嵌脚本、样式与原背景，不需要 CDN 或运行时证据文件。49 项采用记录通过本地 HTTP 检查该单文件；云浏览器禁止 file://，因此没有把直接双击 HTML 记为验证通过。
