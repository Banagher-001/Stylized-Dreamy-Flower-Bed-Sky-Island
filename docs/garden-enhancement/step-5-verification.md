# 第五步验收：缓慢经过庭院的云影

状态：第五步已执行完成，I01～I16当前环境验收通过，实体设备项目独立待验。当前候选`garden-enhancement-step5-fc6b56eb4157625e`，基线为第四步`garden-enhancement-step4-2b6d5479a1939f3e`。旧Git提交不是本次基线。[最终签收](../evidence/garden-enhancement-step-5/summary.json)、[结果绑定](../evidence/garden-enhancement-step-5/result-binding.json)及[本步封印](../evidence/garden-enhancement-step-5/evidence-manifest.json)对应当前版本。

## 逐项结果

| 编号 | 当前结论 | 实际依据 |
| --- | --- | --- |
| I01 基线保护 | 通过 | 第四步独立104文件快照；前四步895份封印；[基线](../evidence/garden-enhancement-step-5/baseline-version.json)及[范围保护](../evidence/garden-enhancement-step-5/scope-guard.json) |
| I02 视觉目标 | 通过 | 最终实际GPU全景接收表面遮阴覆盖22.233%/22.081%/30.464%/32.140%，对应2/18/40/64环境秒；原正常画面受光最大明度下降约18.18%（含8位量化），原速运动另见录像 |
| I03 世界稳定 | 通过 | 高度/风向/周期参考场误差≤1e-10；实际GL共享漂移符合原环境时间；暂停后O→A2→O完整GPU画面精确还原 |
| I04 跨物体 | 通过 | 14份实际Art材质最终着色后接入同一场及uniform对象；草地、植被、柱身/柱顶、池沿和水体实编译，无额外场景 |
| I05 暗部 | 通过 | O/A2/W原8位正常画面对照，深阴影最大绝对线性明度损失约0.00134，没有新增黑像素；旧树影与建筑阴影轮廓保持 |
| I06 水体与物理 | 通过 | 2/18/60/300秒所有Mesh属性/索引/实例矩阵/世界变换/飞滴涟漪事件逐项一致；原水球/水束/物理源码保持 |
| I07 文字与背景 | 通过 | 实际启用云影时四组About RGBA及属性与第四步精确一致；DOM正文/CSS及GPU魔法组件源码保持，无Art标记的发光材质排除 |
| I08 循环 | 通过 | CPU周期/接点连续；固定原几何时间后真实GPU边界前后最大差1个8位通道级，跨O/A2/W；实际原速正常播放跨过145.4545秒接点 |
| I09 播放/偏好 | 通过 | 实际播放改变共同GL漂移；暂停600ms及运镜返回保持精确画面；真实减少动态偏好及恢复沿用原规则 |
| I10 四种组合 | 通过 | 最终三引擎×三主画幅分别验证，环境暂停时阅读450ms零GL；设置切换保留导览完整停留 |
| I11 隐藏与作品 | 通过 | 真CDP标签页隐藏时冻结原时钟且零绘制，返回不补跑；图像、现场/归档关闭保留位置/焦点、释放视频，导览不自动续播 |
| I12 画幅 | 通过 | 三引擎1440×900/1366×768/390×844；320窄屏、844横屏、DPR1/2/3及CSS200%字压保持阅读，真实手机独立待验 |
| I13 引擎/失败 | 通过 | 最终87组主回归、8组GPU专项、9组原生恢复、2组图形失败/字体；真实context loss前后云影完整画布精确一致，无WebGL仍有十段完整原文及参考入口 |
| I14 资源/性能 | 通过 | 86输入/18成品严格构建；两模式五视角几何/纹理/程序/calls/三角形与基线一致；全部ABBA样本合并后最大p95增幅2.27%＜10% |
| I15 关闭/旧稿 | 通过 | 云影关闭后18组完整GPU画布逐像素一致，四组About实际RGBA一致；两模式旧参考稿整页精确一致，无裁切/掩码/容差 |
| I16 交付绑定 | 通过 | 独立107文件源码/成品、两段实际原速录像及最终证据封印完成；最终构建字节一致，两个成品端口共36次实际HTTP文件核对；不进入第六步 |

最终新跑原始报告：[Chromium](../evidence/garden-enhancement-step-5/browser-chromium.json)、[Firefox](../evidence/garden-enhancement-step-5/browser-firefox.json)、[GTK WebKit](../evidence/garden-enhancement-step-5/browser-webkit.json)、[共同场/材质/物理](../evidence/garden-enhancement-step-5/model-and-materials.json)、[实际GPU](../evidence/garden-enhancement-step-5/gpu-field-and-lighting.json)、[完整关闭/参考对照](../evidence/garden-enhancement-step-5/cloud-off-protection.json)、[真实原生恢复](../evidence/garden-enhancement-step-5/native-guide-recovery.json)、[失败/字体](../evidence/garden-enhancement-step-5/failure-and-font.json)、[串行最终回归签收](../evidence/garden-enhancement-step-5/fresh-regressions.json)。不把初版或历史结果计入本候选的新跑数量。

## 原速演示与成品核对

[全景84.44秒](../evidence/garden-enhancement-step-5/clouds-overview.mp4)从正常首页进入，环境沿原设置播放、导览默认手动；原始环境时间从约2.27秒到64.49秒，观察跨度超过60环境秒，实际墙钟约80秒，随后明确暂停。没有缩短原50ms推进上限或加速画面。

[循环/水潭55.92秒](../evidence/garden-enhancement-step-5/clouds-loop-water.mp4)明确使用原有`waterTime=144`初始时间，随后正常播放至145.67秒跨过接点，继续至149秒暂停；原导航到水潭并切正常画面不重置环境，近景实际播放、导览停留与环境暂停独立、真实wheel接管、从新位置继续运镜到终章均保留。初始时间设置与性能诊断的受控时间戳分开标记。

两段MP4与原始记录时长相同，仅H264编码转换；[时间核对](../evidence/garden-enhancement-step-5/video-timing-verification.json)、[四张完整帧来源](../evidence/garden-enhancement-step-5/video-frame-origins.json)和[直接视觉审阅](../evidence/garden-enhancement-step-5/video-frame-review.json)保留。没有裁切、补帧、覆盖、变速或修图；抽帧加实际操作记录不冒充逐帧审查或实体帧率。

[最终HTTP核对](../evidence/garden-enhancement-step-5/production-preview-verification.json)对4179与4173各18份成品检查状态、MIME与SHA，最终严格重构建与已测18份字节一致。交付时发现用户5173/4173服务均已退出，已用原npm脚本恢复并核对最新成品；只停止本步4178/4179和自建X103，保留用户预览。[服务记录](../evidence/garden-enhancement-step-5/service-lifecycle.json)明确区分恢复与清理。

## 诊断图与实际画面的区分

覆盖率诊断通过测试工具替换实际片元最终输出为云影场强度标记，保留原世界投影、深度和实例关系，记录完整原始栅格。接点诊断仅在测试工具中覆盖GL漂移uniform，使其从31.999999到0.000001，原几何/风/水固定同一2秒。两者均为明确的数值诊断图，不是正常视觉或原速运动证明，普通入口不识别这些测试控制。

正常明暗对照使用未经修改的实际生产着色，完整GPU画布只等量隐藏DOM以隔离三维内容；所有GPU字样/水潭都保留。关闭云影的精确对照无裁切/掩码/容差；1级通道差仅是接点连续性诊断的量化界限，不能挪用到基线保护。介绍背景用真实RGBA，不通过修改原遮罩来制造对照。

## 性能口径

同一Chromium155/Linux SwiftShader，单浏览器，任何时刻只测一个页面，完整路线/两模式预热；没有其他浏览器、截图或录像并行。真实30次原生wheel p95为195.6→190.5ms（约−2.61%）。

导览测试在前/后/后/前顺序中，让两版原控制器从H3.8向B1推进，同时环境播放。测试包装器仅给已辨认的原渲染RAF回调传入相同240个运动时间戳；真实performance.now和原生RAF实际时间戳不改写。相同中间168帧/轮，两版各合并336个脚本工作及334个间隔样本，不选最好轮；实际H/相机坐标与动态环境时间误差为0。此控制是同路径性能诊断，不作为原速演示。

| 项目 | 第四步基线p95 | 当前p95 | 变化 |
| --- | --- | --- | --- |
| 像素：脚本/提交工作 | 4.4ms | 4.5ms | +2.27% |
| 像素：原生帧间隔 | 66.7ms | 66.8ms | +0.15% |
| 正常：脚本/提交工作 | 5.2ms | 2.4ms | −53.85% |
| 正常：原生帧间隔 | 199.9ms | 183.3ms | −8.30% |

正常模式平均间隔109.18→118.21ms，中位数100→116.6ms；软件数据存在波动，不能把p95通过解释成所有统计都加速。所有原始样本及各轮保存在[最终性能报告](../evidence/garden-enhancement-step-5/performance-comparison.json)，不是设备GPU完成计时或真机FPS保证。

首候选`1c195311be269c29`间隔p95超阈值的原始[报告](../evidence/garden-enhancement-step-5/versions/garden-enhancement-step5-1c195311be269c29/pre-optimization-reports/performance-comparison.json)、源码成品和全部初版回归保留。复用同一PCF采样、提前跳过透明区域后，源码冻结到当前候选，再完整复跑实际专项和三引擎。没有覆盖或删除首轮问题记录。

## 实体边界与范围

Chromium155、Firefox153、GTK WebKit26.5为本轮实际引擎，GTK WebKit不等于iPhone Safari。真实iOS/Android、设备GPU帧率、浏览器地址栏、OS字体/缺口安全区、VoiceOver/TalkBack、实体触控板/APZ未提供相应设备，单独待验；桌面画幅、CSS字压和浏览器输入模拟不冒充这些项目。

工作保存在当前工作区，不Git提交、推送、部署、发布或重封旧release ZIP。飞鸟与第七步综合交付未开始。
