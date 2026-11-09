# 第五步实现记录：共享世界投影云影

状态：第五步已完成，I01～I16当前环境验收通过；实体设备项目独立待验。当前候选`garden-enhancement-step5-fc6b56eb4157625e`，基线为第四步`garden-enhancement-step4-2b6d5479a1939f3e`。

## 实际改动

新增两种不规则柔边云影轮廓，周期性地沿原风向移动。当前滚动庭院显式启用，`clouds=off`可独立诊断关闭，`env=off`也关闭；旧参考稿调用保持默认关闭。现场体验继续使用当前唯一场景与画布。

每个接收点先按太阳方向投影到统一基准平面：`world.xz - world.y * (8.5/11, -1/11)`，再投影到原风向及其垂直方向。世界周期32单位，速度0.22单位/环境秒，13单位庭院跨度约59.09环境秒；完整场重复约145.45环境秒。云影形状与其局部坐标一起周期化，周期接点位于该轮廓已完全透明的区域。独立环境时间不增加；只在原world.update中更新一个有界漂移uniform。

两轮廓使用不同尺度、横向位置及密度，以有上限的柔和并集组合。草地最大系数0.18、石材0.14、植被0.13、花0.10、池水0.075、水球0.05、水束/飞滴0.045；原树影/建筑暗部降低附加遮阴，水体高光另受保护。保持原材质最终色彩和体积，再轻度改变其受光输出。实际8位画面数值包括量化，须以验收数据结合观看判断。

材质采用实例局部包装：场景原材质及专用池水/池沿/水球先完成自身着色扩展，再接入共享云影；柱子替换材质后再发现一次接收者。重复绑定不重复包装。GPU魔法字样及其他无Art接收标记的材质不参与。没有修改正文、CSS背景、读者布局、导览控制器、几何、物理、随机分布或素材。

| 文件 | 范围 |
| --- | --- |
| `src/config/cloudShadows.ts` | 形状、周期、速度与各材质响应系数 |
| `src/animation/cloudShadows.ts` | 有界漂移、太阳/风向投影与诊断参考采样 |
| `src/materials/applyCloudShadows.ts` | 最终着色接入、共享uniform、实例缓存键、绑定与释放 |
| `src/scene/createScene.ts` | 显式可选启用、同一环境时间更新及dispose |
| `src/tour/startTourPrototype.ts` | 当前庭院启用/诊断关闭，替换柱材质后的绑定 |

云影不增加几何、纹理、全屏通道、绘制调用、RAF或interval；原静态建筑阴影更新策略保持。异常扩展缺少锚点时保留原着色，禁用共享云影活动量；缺少锚点专项为明确注入的测试，不冒充生产图形故障。真实上下文丢失和无WebGL沿用原阅读回退。

## 性能定位记录

第一候选`garden-enhancement-step5-1c195311be269c29`通过功能/投影/视觉检查，但匹配ABBA测试中像素、正常画面绘制间隔p95分别约+24.89%/+33.42%，没有签收。完整首轮源码成品与所有原始报告保存在[首轮目录](../evidence/garden-enhancement-step-5/versions/garden-enhancement-step5-1c195311be269c29/archive-manifest.json)及其`pre-optimization-reports/`内。

定位到石材/水体的原明暗响应与新遮阴响应重复调用同一建筑阴影PCF采样。现缓存这一结果供两者复用；云影完全透明的区域也提前退出形状计算。抗锯齿导数在分支之前求值，保持有效的片元导数。当前候选已按相同条件完成ABBA复测，全部样本合并后最大p95增幅约2.27%；首轮超阈值样本保留。不同统计仍有波动，完整口径见[验收记录](step-5-verification.md)。源码固定后七份最终回归报告均已重新跑通。

严格构建、86输入/18成品指纹见[构建记录](../evidence/garden-enhancement-step-5/build-verification.json)，独立107文件快照见[快照清单](../evidence/garden-enhancement-step-5/candidate-archive-manifest.json)。本步不Git提交、推送、部署、发布或改写旧release ZIP；飞鸟与综合打包未开始。

[全景原速演示](../evidence/garden-enhancement-step-5/clouds-overview.mp4)84.44秒，覆盖超过60个原始环境秒；[循环/水潭/接管演示](../evidence/garden-enhancement-step-5/clouds-loop-water.mp4)55.92秒，采用明确的原有初始时间144秒后正常播放跨过循环点，再展示暂停、运镜和原生滚轮接管。两段只转换编码，保留原记录时长。本步文档、脚本及全部初版/最终证据见[封印清单](../evidence/garden-enhancement-step-5/evidence-manifest.json)。
