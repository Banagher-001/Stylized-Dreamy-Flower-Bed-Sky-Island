# 关于我改版 · 第九步交接

第九步实现悬停阅读与倾斜，下一步是第十步的更多内容呈现，需用户先细化并授权执行。本步未修改个人资料或工具正文，也未提交、推送或发布。

[实现说明](step-9-reading.md) · [验收](step-9-verification.md)

## 可继续使用的接口

- ToolCardView.setPose：基础姿态，供飞入与曲轨调用；setReading：阅读 amount、局部 x/y/z、scale、pitch、yaw。统一在工厂中组合后照明与绘制，不争写 transform。restingReadingPose 与 setReading() 恢复基础姿态。
- createCardHover：present(context, entranceReady)、wheel、cancel、focus、blur、escape、dispose。它持有唯一活动卡和按需姿态 RAF，changed 只更新操作提示，不请求主站容量重测。
- createCardTrack.holdReading：临时停住轨道，保留 live intent；释放时按最新选择恢复。显式 pause 仍改变选择。悬停不写快照，恢复后不重放角度或旧输入。
- 工厂 measure：返回十个面的真实 DOMRect 和含阴影的 bounds；已不把未移动的外层 article 当作移动后的真实包围盒。旧的 measureToolCardProjection 包装接口继续可用。

## 第十步承接重点

1. 用户最终要求是悬停放大后显示更多内容。第九步已建立稳定的进入、阅读、离开状态与现有详情入口；第十步需要把完整介绍排布接到该状态。应先测完整内容所需尺寸，再设计空间与显隐，不能直接打开隐藏段落后继续套用 300 px 的旧高度预算。
2. 当前 cardsState.expandedId 的手动展开会转入原生稳定阅读，并令程序轨道和悬停不再接管。新增悬停内容要明确与它的关系，避免一显示内容就触发取消自身的 allowed 条件。
3. 卡牌默认是 232/240 px 宽、300 px 高；普通宽屏卡排预留 40 px 上下空间，1000 px 以上高度预留 56 px。放大仍须同时容纳正文、厚度与阴影，标题/分类/按钮/继续入口保持可用。不要让 hover 每帧触发 capacity 探测或相机模式切换。
4. 阅读默认目标深度是共同轨道前方 36 px，需要抵消边缘牌的负基础 Z。不能退回固定局部 translateZ，否则反向倾斜会被邻卡挡住。缩放同时补偿基础投影，减少边缘牌异常放大。
5. pointerdown 冻结姿态直至原生 click；指针焦点不搬动按钮，只有 :focus-visible 对齐键盘卡。更多内容不能在 pointerdown/pointerup 之间挤走按钮或重建节点。
6. hover.wheel() 必须在合格滚轮事件交给轨道前调用，同一事件接管；浏览器修饰键与原生横向手势保留。停止滚动后等待新的鼠标意图，不能由静止光标下移动的卡牌自动重新占有阅读。
7. 当前临时 hold 不改变自动开关，退出按最新 live intent；键盘阅读、按钮和显式手动操作仍沿用暂停规则。主导览在真正进入阅读时停止，离开不擅自开启主导览。
8. 阴影已移到 entity 内、深度在背面之后并隐藏背向面。阅读时源形状适度内缩，模糊小幅增加。不要重新放回 position 层与前牌面同深度；正文变高后复验阴影像素遮挡和真实包围范围。
9. 激活卡保持原槽位与原节点，轨道相位冻结；回到 amount=0 后才恢复循环换位。增加 pinned/read 状态时不能过早释放 hold。
10. 切类、详情、全部工具、离开章节、后台、尺寸/布局、媒体设置与销毁要清理候选和临时姿态。快照保留分类、位置、方向与开关，不保留 hover。原生焦点滚动后有 180 ms 稳定等待。
11. 透明 stage/slot/article 继续 pointer-events:none，真实 front 为 auto；仍只有一个可访问正面、一个工具一个真实节点。21 款工具和 Vibe Coding 的两套排序、图标与既有正文不改。

本步录像及原始失败探针都在 evidence/step-9。先建立下一步基线，不覆盖前九步档案。开发 npm run dev，生产检查 npm run build；临时验收浏览器与服务在交付前关闭，记录见验收文档。
