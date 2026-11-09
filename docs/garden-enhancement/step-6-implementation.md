# 第六步实现记录：庭院飞鸟

状态：第六步已完成，J01～J16当前环境验收通过；实体设备项目独立待验。当前候选`garden-enhancement-step6-487410d10d8ad600`。基线第五步`garden-enhancement-step5-fc6b56eb4157625e`。本步只增加三只飞鸟和必要的文字避让，沿用原场景、相机、画布、环境时钟和播放入口。

## 画面与运动

三只立体低多边形小鸟，包含头喙、身体、完整上下表面的翅膀和短叉尾。暖米白受光面配灰青阴面、少量深色翼尖，使用原太阳和环境光，没有新增灯光或发光效果。鸟群不消耗原草花分布的随机数。当前翼展比例0.34/0.32/0.33单位；两种画面模式保持同一世界几何。

三条错相的平滑弧形航线，周期48/54/61环境秒，分别位于4.45/5.10/5.75单位附近，方向和相位不同。实际微起伏后高度约4.38～5.82，速度约0.50～1.04单位/环境秒；椭圆长短轴使速度自然变化。先拍翼两至三次，再滑翔约3.6～3.8环境秒；肩部转动与身体连续相接。身体沿航线切线朝向前方，约5～10度轻倾。相较最初8～15度试值，最终采用较小倾角，避免小尺寸轮廓在像素画面中过度跳变。

位置、姿态、翼角和拍翼包络由绝对环境时间直接采样，不逐帧累加路径，也不重新抽取随机状态。航线和拍翼周期各自平滑衔接。暂停后滚动、切换正常/像素画面和返回全景，只改变相机投影与可见性，不改变鸟的世界位置或翼角；恢复播放从暂停时刻继续。

## 阅读保护与资源

正交相机靠近石柱时，鸟不会因世界距离自动缩小，因此按完整身体和翼尖的保守包围球投影避让。正文、作品、标题、页眉页脚、章节导航和GPU魔法字样都有安全区，桌面20px、窄屏14px；进入安全区之前，额外26px范围平滑淡出。航线继续运行，不在屏幕边缘重新生成。现场体验继续用原画布，安全范围使用其实际pane边界。

固定UI边界按布局缓存；三个阅读面板复用原定位器已写入的left/top与缓存尺寸。ResizeObserver只在尺寸改变时使缓存失效，当前段落和标题变化也重新测量。原环境循环不活动时只请求必要的一次绘制，没有新增持续RAF、定时器或轮询。稳定阅读隐藏飞鸟，保留原零闲置绘制行为。

鸟身、左翼、右翼合并成一个实例批次，合计一个几何、一份共享材质，最多一个新增颜色绘制调用、180三角形。顶点中的肩部铰链使用原采样翼角，与原分部矩阵得到相同姿态；每只鸟只上传一次身体矩阵。纹理、全屏pass和鸟影均为零。材质保留真实深度测试；完整实体外表面只绘制正面，透明渐隐不新增双面pass。像素与正常输出最多产生两个着色程序变体，仍是一份共享材质。

| 文件 | 实际范围 |
| --- | --- |
| `src/config/birds.ts` | 三航线、配色、尺度、安全区和渐隐参数 |
| `src/animation/birdMotion.ts` | 绝对时间位置、切线、轻倾、拍翼和滑翔 |
| `src/geometry/createBirdGeometry.ts` | 鸟身与完整实体双翼的顶点、颜色和法线 |
| `src/materials/createBirdMaterial.ts` | 共享原光照材质、肩部铰链与实例渐隐 |
| `src/scene/createBirds.ts` | 单实例批次、投影、状态、资源释放 |
| `src/tour/birdVisibility.ts` | 实际UI/GPU字样安全区和布局缓存 |
| `src/scene/createScene.ts` | 可选创建、同环境时间更新、释放 |
| `src/tour/startTourPrototype.ts` | 当前庭院启用、避让接入、原循环和诊断状态 |

当前庭院显式开启，独立诊断`birds=off`关闭；旧参考稿默认不开启。`birds=inspect`仅暴露被动状态，不增加访客界面、改变时钟或强制动作。全局`env=off`不创建飞鸟资源。释放会断开尺寸观察器、释放共享材质及几何，重复释放安全。

## 性能定位和交付边界

首轮`garden-enhancement-step6-3171e6fa0a9fe255`保留在[试作目录](../evidence/garden-enhancement-step-6/versions/garden-enhancement-step6-3171e6fa0a9fe255/archive-manifest.json)。初测发现避让每帧查询计算样式和实际边界，在原阅读面板写入位置后引发同步布局，像素绘制开销超出目标。已改为复用原定位值和缓存尺寸，再独立复测；首轮完整原始样本和未通过标记保留，不用最终结果覆盖。

缓存后的首次复测仍有尾部耗时超限，完整报告另存[未限制CPU的复测](../evidence/garden-enhancement-step-6/versions/garden-enhancement-step6-b1c21e4a6491ee54/unrestricted-cpu-profile/performance-comparison.json)。[分段诊断](../evidence/garden-enhancement-step-6/versions/garden-enhancement-step6-b1c21e4a6491ee54/before-single-batch/performance-cost-isolation.json)中，飞鸟呈现平均约0.068ms、p95约0.20ms，样式查询为零，边界查询p95为零；基线本身也有明显长尾。云环境暴露五核亲和性，但cgroup只允许四核CPU配额，测试期间频繁发生节流。将两侧都限制在相同三核后不再新增节流，帧间隔恢复基线附近，但三批绘制的脚本p95仍超目标。完整[同CPU配置复测](../evidence/garden-enhancement-step-6/versions/garden-enhancement-step6-b1c21e4a6491ee54/before-single-batch/performance-comparison.json)保留。

最终再将三部分合并为一次实例提交，流式上传姿态，鸟群完全不可见时跳过上传。合并几何的实际属性与原分部矩阵在600环境秒逐顶点比对，CPU双精度参考中的肩部姿态等价误差约2×10⁻¹⁵单位；实际GPU单精度视觉和投影另以浏览器验证。最终比较继续在两侧相同三核下执行，保留原网页、画面质量、软件图形驱动及全部样本；这属于云环境软件渲染对比，不代表实体GPU帧率。

最终单批版本已通过同条件匹配性能比较，全部p95增幅符合10%目标。最终构建、三引擎回归、原速录像和历史保护结论见[第六步验收](step-6-verification.md)。本步工作保存在本地，不提交或推送Git，不部署、发布或重写旧release文件；第七步未开始。

[全景原速演示](../evidence/garden-enhancement-step-6/birds-overview.mp4)87.12秒，覆盖62.76个实际环境秒，三只鸟各观察到一次航线相位接点及拍翼/滑翔；[暂停、接管与现场体验](../evidence/garden-enhancement-step-6/birds-controls.mp4)56.60秒。两段均保留原记录时长。最终源码成品、原始试作与全部验收证据见[封印清单](../evidence/garden-enhancement-step-6/evidence-manifest.json)。
