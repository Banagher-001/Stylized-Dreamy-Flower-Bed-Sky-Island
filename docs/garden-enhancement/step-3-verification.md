# 第三步验收：球面流纹、波峰与起伏

状态：**第三步已完成，当前环境G01～G18均通过。** 实体设备项目独立列在文末，未写成已验证。

候选`garden-enhancement-step3-79dad8c41ee79a61`，基线`garden-enhancement-step2-3a477d247f5475fe`。以下均为本步新跑结果，前两步证明只作为保留依据，不计作新检查。环境为Linux软件渲染，未将桌面浏览器模拟画幅写成实体手机或硬件FPS证明。

## 代表画面

[修改后原速演示，56.96秒](../evidence/garden-enhancement-step-3/water-orb-after.mp4) · [第二步真实基线原速对照，56.00秒](../evidence/garden-enhancement-step-3/water-orb-before.mp4)。两片均为1440×900、DPR1、初始时间2秒，使用相同控件与操作顺序。正常W与像素W各连续播放至少7.4个场景秒且至少8个真实秒，并展示暂停、继续、模式切换、O开场及C2现场体验。软件渲染下真实耗时不同，原速保留，不加速或强行重定时。

[录像原始时间与状态](../evidence/garden-enhancement-step-3/water-orb-recording-after.json)、[真实视频抽帧审阅](../evidence/garden-enhancement-step-3/video-frame-review.json)保留，未改动旧封面或旧影片来代替新效果。

- [正常画面：水潭W，时间2秒](../evidence/garden-enhancement-step-3/chromium-1440-native-W-t2-after.png)、[时间4秒](../evidence/garden-enhancement-step-3/chromium-1440-native-W-t4-after.png)、[时间6秒](../evidence/garden-enhancement-step-3/chromium-1440-native-W-t6-after.png)。
- [默认384像素画面：W](../evidence/garden-enhancement-step-3/chromium-1440-pixel-W-t4-after.png)、[O开场](../evidence/garden-enhancement-step-3/chromium-1440-pixel-O-t2-after.png)、[现场体验](../evidence/garden-enhancement-step-3/chromium-1440-pixel-live-after.png)。
- [手机尺寸正常W](../evidence/garden-enhancement-step-3/chromium-390-native-W-t2-after.png)、[手机尺寸像素W](../evidence/garden-enhancement-step-3/chromium-390-pixel-W-t2-after.png)、[介绍背景保护](../evidence/garden-enhancement-step-3/chromium-390-About-protected.png)。
- [WebKit正常W](../evidence/garden-enhancement-step-3/webkit-1440-native-W-t4-after.png)、[Firefox默认开场](../evidence/garden-enhancement-step-3/firefox-1440-pixel-O-t2-after.png)。

均为未改画面的真实完整页面截图，保持原相机、名义球体大小和采样档位；没有用放大裁图替代原始尺寸。三引擎共78张主要固定帧，第二步真实基线另有26张匹配帧。现场体验在1440宽样本的记录时间为6秒，其余主画幅为2秒，清单逐张记录真实时间。

## G01～G18执行表

| 编号 | 当前结果 | 依据 |
| --- | --- | --- |
| G01 正确基线 | 通过 | 第二步独立101文件快照校验；79份第一步与355份第二步封存记录完整；[基线](../evidence/garden-enhancement-step-3/baseline-version.json) |
| G02 本步范围 | 通过 | 4份球相关源码修改加1份球面帮助模块；不含自动导览、云影或飞鸟；[实现](step-3-implementation.md) |
| G03 O/W/现场体验 | 通过 | 三引擎、1440×900/1366×768/390×844、正常/像素共78个主要固定帧；开场最小8.15采样像素、W最小14.83采样像素 |
| G04 曲面连续流纹 | 通过 | 连续局部三维方向采样，主波/次波与缓慢绕转共用场景时间；多时间真实画面、[连续场检查](../evidence/garden-enhancement-step-3/surface-field-highlights.json) |
| G05 高光与蓝青体积 | 通过 | 原生产Shader白色混合因子≥0.5的可见面积最大19.47%；384/1024采样、O/W、0～12秒四分之一秒步长，共196次诊断渲染；不新增生产绘制通道 |
| G06 形体、法线、包络 | 通过 | 30,001次真实网格更新覆盖0～600秒；总径向上界3.4%；实际最大局部包络1.046344＜保守1.046408；有限差分法线的`1−点积`误差约1.25e−10 |
| G07 接缝、极点与低采样 | 通过 | 1,625个方向/时间样本含南北极，825次真实网格接缝/极点检查，最大缝隙2.55e−16；次波在不可辨像素尺寸时衰减 |
| G08 水束衔接 | 通过 | 球底与石台实际最小间距0.12513≥0.08；保守全相位间距0.11804；实际最小重叠0.025，水束下端保持石台出水点 |
| G09 32滴与接触 | 通过 | 384组出生、8,064个飞行采样，另有4,992次实际变形三角网格邻近/内外检查；球面间距最小0.00342，底座0.30959、池壁0.51475；接触方程误差＜1e−15；[几何与飞行](../evidence/garden-enhancement-step-3/geometry-physics.json) |
| G10 真实落水波纹 | 通过 | 原8槽、32滴、种子与重力保留；600秒网格扫查中逐帧验证可见波纹位置、年龄与真实落水事件对应，池体及基础水材质保护 |
| G11 时间、暂停与模式 | 通过 | 三引擎共9组主画幅验证：暂停连续450ms零绘制，正常/像素往返及手动相机往返像素一致；播放后时间前进，减少动态及移除偏好均保持选择 |
| G12 生命周期 | 通过 | 真实标签页隐藏、离屏停绘、媒体覆盖、现场体验和减少动态6组[原生恢复](../evidence/garden-enhancement-step-3/native-recovery.json)；另有新球W/现场体验真实上下文恢复，整个GPU画布逐像素一致；[新球恢复与长时间](../evidence/garden-enhancement-step-3/orb-context-longtime.json)；所属资源重复dispose各只触发一次 |
| G13 跳点与长时间 | 通过 | 0/2/6/60/600/3600/86400及正反跳点对独立重建逐项一致；各周期边界20微秒邻域连续；18次实际长时间生产渲染，含24小时附近 |
| G14 页面与世界保护 | 通过 | 82对象的实际几何/实例/变换/材质/光照摘要与路线一致，喷泉父变换保持；[世界保护](../evidence/garden-enhancement-step-3/world-protection.json)；4份完整旧参考/历史喷泉页面及4组介绍实际RGBA背景逐像素一致；[完整页面与背景对照](../evidence/garden-enhancement-step-3/protected-raster-pairs.json) |
| G15 资源与复用 | 通过 | 原117顶点/168三角形；新增静态属性1404字节，新增纹理/球体/绘制通道均0；三引擎各3画幅各10轮模式/现场体验切换，匹配模式后资源数不增长 |
| G16 当次性能 | 通过 | 原30次wheel p95减少6.16%；四组桌面按ABBA顺序复测并合并全部样本，回调/帧间隔p95增幅最大7.12%＜10%，两组手机代表亦通过；[最终性能判断](../evidence/garden-enhancement-step-3/performance-comparison.json) |
| G17 构建、Shader、资源 | 通过 | 三引擎实际生产页面无Shader/HTTP/未处理错误；严格类型检查和最终生产构建通过，81输入与18产物和测试版本完全一致；[构建指纹](../evidence/garden-enhancement-step-3/build-verification.json)、[36个实际HTTP响应](../evidence/garden-enhancement-step-3/production-preview-verification.json) |
| G18 证据与版本 | 通过 | 独立102文件源码/成品快照、原速前后片、性能结论及[全部证据清单](../evidence/garden-enhancement-step-3/evidence-manifest.json)通过摘要绑定；[范围保护](../evidence/garden-enhancement-step-3/scope-guard.json)保留旧档与Git位置。未启动第四步 |

## 测试口径与修正记录

实际测试过程中校正了四个工具假设，没有因此改动产品：作品焦点必须在再次点击暂停按钮前检查；现场体验改变画布尺寸后，正常画面释放原像素缓冲，因此须按相同模式比较；横屏稳定阅读的封面可高于视口，DPR上限须相对实际CSS容器计算；访客`waterTime`参数沿用0～86400，超过24小时的正邻域由独立场采样验证，不扩展访客参数范围。

图片解码或弹窗布局可能发出有限的最后重绘，暂停检查先等待收敛，再要求连续450ms零绘制；整个等待期场景时间必须始终不变，超过4.5秒仍不收敛则失败。没有放宽碰撞、池壁、石台或落水方程阈值，也没有为通过检查遮掉整潭。

资源统计按实际路径解释：充分预热后58份几何、22个程序；现场体验尺寸往返后正常5张纹理/像素6张纹理，与第二步匹配路径完全相同。像素render target随实际尺寸变化重新分配的累计次数不等于存活资源增长。原模式缓存、纹理生命周期及像素采样规则未改动。

## 性能对照过程

首轮当次独立测量的30次原滚轮响应p95为189.8→178.1ms，约减少6.16%。六组球可见播放中，四组桌面条件的部分回调/帧间隔p95变化超过10%，因此首轮[比较文件](../evidence/garden-enhancement-step-3/performance-initial-comparison.json)明确保留`passed:false`，没有直接签收。手机代表的两组变化未超过阈值。

随后用前/后/后/前顺序隔离水球成本，保留全部样本：原有完整喷泉CPU更新平均0.00691→0.00966ms，增加约0.00275ms；同原始投影像素尺寸的单球阻塞完成均值O为0.0489→0.0717ms、W为0.0406→0.0603ms。该诊断隐藏其他网格和阴影通道、使用128像素局部画幅及固定解析时刻，属于原因定位，**不替代生产整帧验收，也不代表实体GPU计时**。[原始隔离数据](../evidence/garden-enhancement-step-3/performance-cost-isolation.json)说明绝对新增成本与整帧波动应分开评估。

生产页面已按前/后/后/前单独完成四组桌面复测，每组每版合并两轮全部240个回调、238个帧间隔样本，不选择最好一轮。四组回调/帧间隔p95增幅均低于10%，最大增幅为正常O帧间隔7.12%；原手机代表两组亦通过。首轮及复测均保留软件渲染限制，不据此承诺真实设备帧率。原始[ABBA数据](../evidence/garden-enhancement-step-3/performance-recheck.json)及[最终判断](../evidence/garden-enhancement-step-3/performance-comparison.json)均保留。

| 桌面条件 | 回调p95，前→后（ms） | 绘制帧间隔p95，前→后（ms） | 帧间隔变化 |
| --- | --- | --- | --- |
| 像素O | 2.9→2.4 | 66.6→66.7 | +0.15% |
| 像素W | 1.5→1.5 | 66.7→66.7 | 约0% |
| 正常O | 6.7→5.2 | 233.4→250.0 | +7.12% |
| 正常W | 4.1→4.0 | 299.9→299.9 | 0% |

回调计时包含原应用更新、绘制提交及驱动等待；帧间隔取真实绘制RAF的时间戳。两者均为本次SwiftShader环境的对比数据，绝非硬件GPU完成时间或真机帧率承诺。

## 当前环境与实体设备边界

本步实际运行Chromium 155、Firefox 153、GTK WebKit 26.5。GTK WebKit并非实体iPhone Safari；390/320宽及触摸能力、DPR2/3为桌面浏览器测试条件。真实iOS/Android、设备GPU帧率、系统级字体缩放、屏幕缺口、VoiceOver/TalkBack及实体触控板仍需对应设备，未提供，单列待验证。

本地工作区保留所有修改，未Git提交、推送、部署或发布，旧release ZIP不变。临时测试服务与测试显示器已关闭，用户开发5173及成品预览4173保留可用。第三步完成后停在审阅点，第四步仍须另行细化并明确开始。
