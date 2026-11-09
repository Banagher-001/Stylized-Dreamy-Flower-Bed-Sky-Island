# 第二步实现：关于我背景羽化

本步按[执行标准](step-2-standard.md)修改第一柱A1/A2/A3的背景。应用候选为 **garden-enhancement-step2-3a477d247f5475fe**，源码/产物摘要见本步[构建证明](../evidence/garden-enhancement-step-2/build-verification.json)。最终签收以[验收记录](step-2-verification.md)和本步summary为准。

## 实际修改

`src/tour/tour.css`中背景仍是原`.pillar-reading::before`，与正文分离。固定420×240、内部模糊的SVG遮罩改为两个按CSS像素计算的渐隐梯度，交集形成统一二维透明度。边缘用平滑渐变逐步到透明，四角相乘不会出现多层暗色相加。末端有2CSS px透明安全带。

背景保留`#223b33`，最大不透明度为原`--veil-opacity`的0.9倍。桌面羽化36px、背景外扩12px；1000px以下羽化24px、外扩8px。正文盒、padding、标题与正文位置、原魔法显隐及相机锚点均保持，外扩仅作用于绝对定位装饰层。没有给文字或整个面板增加模糊。

背景`pointer-events:none`，不加入DOM/读屏节点。稳定阅读沿用原规则隐藏背景伪元素，三段原正文完整展开。标准或WebKit遮罩合成可用时采用渐隐；不支持合成时保留规整可读的深绿圆角底。当前三引擎均实际使用并通过了渐隐分支；没有伪称旧浏览器/真实iOS兼容已测。

此外，`src/tour/readingLayout.css`增加两条仅用于稳定阅读的规则：允许开场网格子项收缩，允许画面模式按钮换行。验收发现原版与初始候选在320px、200%rem时都溢出约8px，原因是开场最小内容宽度受不换行的按钮组撑大。新规则让其自然换行到320px内，保留字体、文字和按钮，不通过隐藏横向内容来处理。[诊断](../evidence/garden-enhancement-step-2/preexisting-overflow-diagnostic.json)保留修改前两边一致的记录。

## 保持范围

运行时只改两份CSS，全部TypeScript、个人事实、图像/视频、依赖、路线、场景、着色器、环境时钟及原查看器逻辑保持。水球、自动导览、云影和鸟没有在本步新增。旧参考稿继续作为固定视角对照。

正文仍是原节点；文字原来的局部显隐遮罩继续保留，新羽化只在背景层。三引擎检查比较了实际文字、三段边界/字框、aria/inert状态、相机与时间，正反向相同H处均与基线一致。

## 实际验证与测量方法

三引擎各108个站点/阶段/方向条件，共324个；54组修改前后实际尺寸背景测量，另有4个容量/DPR边界样本。全部新外缘为0，保守文字对比度最低约5.56:1，超过4.5:1目标。

Chromium/WebKit使用实际背景层透明PNG；Firefox当前截图后端不支持透明截屏，使用保持同一遮罩/颜色/尺寸的黑白底实际截图差分解算alpha，原黑白截图保留。对比度按每个可见字符范围内背景与最不利白底的合成计算；Firefox直接使用实际白底渲染值。正式页面的未处理截图另存，没有二次羽化或裁去背景边缘。

还检查窄屏/横屏/DPR3、200%rem、稳定阅读往返、减少动态、实际WebGL创建失败、原生选择及可信copy事件、键盘导航、手机tap及Chromium实际触摸拖动。手机画幅/触摸与rem缩放是工具模拟，OS选字手柄、系统剪贴板及真机读屏等仍需实机复核。

## 审阅与运行

- [桌面修改前](../evidence/garden-enhancement-step-2/chromium-1440-pixel-A1-read-before.png)
- [桌面修改后](../evidence/garden-enhancement-step-2/chromium-1440-pixel-A1-read-after.png)
- [手机修改后](../evidence/garden-enhancement-step-2/chromium-390-pixel-A1-read-after.png)
- [原速手动滚动演示](../evidence/garden-enhancement-step-2/about-feather-demo.mp4)

使用现有5173开发预览或4173生产预览。新构建已经写入dist；本机测试用4176/4177仅作基线/候选对照，收尾清理这些测试服务，保留正常预览。

本步新增资料和两份CSS保存在工作区，未提交/推送GitHub、未发布或重封旧ZIP。第一步已签收文件和旧归档保持原字节；此前起步目录是第一步签收快照，当前进度以本步验收为准。第二步完成后停在审阅点，第三步水球尚未开始。
