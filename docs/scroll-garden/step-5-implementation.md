# 第 5 步实现与使用：第一柱「关于我」

第一柱已从三段验证短文改为正式个人介绍：上部身份铭文、中部经历轴、下部创作方向。继续使用第四步深色石材、贴面符印和魔法显示，当前停在第五步验收点。标准见 [第五步执行标准](step-5-standard.md)，检查结果及限制见 [验收记录](step-5-verification.md)。

## 进入与阅读

在当前预览地址后加 `?tour=prototype`，已有参数时用 `&tour=prototype`。默认参考作品集保留。

- 向下滚动，靠近第一柱上部读取身份，再沿柱下降读取经历、创作方向；继续滚动进入第二柱当前预留区域。
- 「01 关于我」定位到 A1 的完整阅读区；已有「镜头数据」内 A1/A2/A3 可分别定位三站。
- 停滚保持当前显示状态，向上滚动反向恢复。环境暂停、正常/像素模式和返回参考稿继续可用。
- `?tour=prototype&waterTime=2` 固定共享环境时间，方便同位置比较；它不是强制观看时长。
- 第一柱内容区改用身份/经历/创作章标。原型标识更新为 `ABOUT / INSCRIPTIONS`，工程阶段继续在页面标题和既有调试数据中标识。

## 三种内容编排

| 站点 | 内容 | 编排 |
| --- | --- | --- |
| A1／身份 | sakan；张辰翰／萨坎；专注 AIGC 的创作者；化名取自《战锤 40K》的角色 | 突出的名字、姓名行、定位、独立注脚 |
| A2／经历 | 现在：枫叶互动，AI 动画制作；此前：游族网络 | 短经历轴，淡金当前节点、水蓝此前节点 |
| A3／创作 | 图像构建／AI 图像；影像制作／AI 视频与动画；交互表达／Vibe Coding | 三行方向图，桌面轻微缩进，手机纵向对齐 |

A3 底部为「继续向下，进入 AI 影像。」的文字提示，直接继续滚动即可，不额外增加按钮。没有新增任职年份、以前的工作职责、具体项目、奖项、商业效果或联系信息。

正式内容集中在 [aboutContent.ts](../../src/tour/aboutContent.ts)，与 [reading.ts](../../src/tour/reading.ts) 中坐标、区间和定位点分开。没有修改旧参考页的 [portfolio.ts](../../src/content/portfolio.ts)，也没有把其作品媒体导入第一柱。

## 字体与容量

- A1 主标题：桌面 40px、手机 30px，沿用现有衬线字体回退。
- A2/A3 标题：桌面 27px、手机 22px。
- 正文、公司名、方向说明：桌面 18px、手机 16px，行高 1.7/1.65；化名注脚和末尾引导为 16px。
- 辅助经历标签为 12px，英文 NOW/BEFORE 为 9px；实质信息保持正文尺寸。
- 文字仍为清晰 DOM 文本。经历采用有序列表，方向采用列表；文本可选择、复制，空装饰线不参与阅读。

共用承托继续为桌面 420px、390px 竖屏下 358px。三个 article 共用一个网格区域，按实际最高内容预留空间，切换站点不改变该尺寸。Chromium 的桌面/手机高度约 288/245px，Firefox 手机约 246.4px；完整布局、边界和字体回退数据见验收记录。

雾影沿用现有局部静态遮罩，字行下保持深色核心，不新增全屏滤镜。三种结构的注脚、标签和方向说明纳入真实背景对比度测量。

## 滚动与隐藏

| 站点 | 区间 H | 完整阅读区 H | 定位 H |
| --- | --- | --- | --- |
| A1 | 1.3～2.1 | 1.54～1.94 | 1.74 |
| A2 | 2.1～2.9 | 2.34～2.74 | 2.54 |
| A3 | 2.9～3.7 | 3.14～3.54 | 3.34 |

标题/章标沿用标题状态，姓名、经历、方向、注脚和末尾提示统一属于正文组。依然是符印→标题→正文，完整阅读稳定，正文先退出。新装饰与所属正文同步显隐，不加自动轮播、打字定时器或第二个时钟。

非当前 article 保持 `aria-hidden`/`inert`；正文隐藏时整个正文组及其后代同步退出可访问内容。滚动不抢焦点。已有 ResizeObserver 在字体或窗口造成尺寸变化时重新定位，稳定阅读时使用原有更新缓存。

## 实现范围与保护

| 文件 | 本步改动 |
| --- | --- |
| [aboutContent.ts](../../src/tour/aboutContent.ts) | 新增单一正式内容模块 |
| [reading.ts](../../src/tour/reading.ts) | 移出旧验证文案，所有坐标、区间、定位点和采样算法保持 |
| [createPillarReader.ts](../../src/tour/createPillarReader.ts) | 复用三 article，接入三种内容结构与语义 |
| [tour.css](../../src/tour/tour.css) | 姓名层级、经历轴、方向图与手机纵向样式 |
| [startTourPrototype.ts](../../src/tour/startTourPrototype.ts) | 更新本原型的章节说明与阶段标题 |

相机路线、材质、符印贴面坐标、几何、草花、水体、灯光、全局色板、渲染器、共享时钟、媒体和应用依赖保持。没有新增 GPU 资源；同模式预热仍为 54 几何、4 纹理、10 程序，两模式缓存为 18 程序。第二柱/第三柱正式内容、新水潭和水球继续按后续步骤处理。

## 交付与限制

- [实际双向滚轮演示](../evidence/scroll-garden-step-5/about-reading-demo.mp4)
- [A1 身份](../evidence/scroll-garden-step-5/chromium-A1.png)、[A2 经历](../evidence/scroll-garden-step-5/chromium-A2.png)、[A3 创作](../evidence/scroll-garden-step-5/chromium-A3.png)
- [手机身份](../evidence/scroll-garden-step-5/chromium-mobile-A1.png)、[手机经历](../evidence/scroll-garden-step-5/chromium-mobile-A2.png)、[手机创作](../evidence/scroll-garden-step-5/chromium-mobile-A3.png)
- [验收记录](step-5-verification.md)、[证据索引](../evidence/scroll-garden-step-5/README.md)

当前通过的手机范围是模拟目标竖屏的真实短内容。第四步长文压力样本、狭矮横屏、200% 文字缩放及完整静态章节适配仍需后续处理，不能据此写成已通过。Linux 软件图形与 GTK WebKit 不等于真实手机、Apple Safari 或物理 GPU 性能验收。

成果保存在云工作区。完成后停在第五步用户审阅点，未发布、部署、Git 提交或推送，旧 `release/` 归档保留。
