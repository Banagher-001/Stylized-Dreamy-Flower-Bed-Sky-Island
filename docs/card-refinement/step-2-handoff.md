# 第二步交接至第三步

四卡入场强化已完成，当前候选为 `card-refinement-step2-e000401dbd3d7074`。源码、测试与记录留在工作区，未提交、推送、发布，也未重新生成 r3 历史交付包。

[实现说明](step-2-entrance.md) · [最终验收](step-2-verification.md) · [第一步输入合同](step-1-contract.md)

## 已接入的位置

- createCardEntrance.ts：四卡错峰、宽视觉舞台、资源与可见性门槛、2350ms 时间表、原卡恢复及打断清理。root.dataset 中可查 entrance、entranceSubphase、entranceReason、entranceFramePending、entranceHoldPending 和 entrancePauseComplete。
- createToolBrowser.ts：向入场传入 `containsInput: event => interactionRegion.inspect(event).inside`，仅在入场中判定快速落位区域。原轨道 wheel handler 未改。
- createCardTrack.ts：首次正常入场已有阅读停留时跳过旧的 500ms 等待。其他恢复仍用旧等待，显式自动偏好保持原语义。
- cardEntrance.css：范围限定在入场舞台，正常落定后的卡牌外观保持原样。

入场使用比交互区域更宽的 fixed 视觉窗口。不要用飞行卡的 BCR 推导逻辑内容宽度，也不要将视觉窗口当作输入区域。第一步的 cardInteractionRegion.ts 和 createCardRegionDebug.ts 仍是原版本。

## 第三步需要实现

1. 在原生 wheel 路由中使用第一步 inspect，覆盖整张卡、卡间隙与约定留白。cards / page / overlay / browser 按合同分派，只有事件可取消且实际由卡排接管时才消费一次。
2. 补齐自动关闭、分类筛选后和未创建程序舞台的 native/manual 状态；不能以 autoplay 已启动或入场 playing 为横移前提。
3. 将纵向滚轮的方向和输入量映射到横向速度；快滚更快、停止后有缓冲。按后续标准处理 deltaMode、触控板和边界，避免一份输入同时移动页面和卡排。
4. 承接现有临时悬停、固定详情和显式自动偏好，区分用户暂停与临时持有。实际协调细节留给第四步，首尾和镜头交接留给第五步。
5. 保持浏览器组合手势、模态/帮助/全文、分类/导航按钮和区域外页面滚动；移动触摸保留原生行为。

第二步的入场 wheel 监听为 passive capture，只做 140ms 快速落位。第三步接入时需统一本次输入的处理次序，避免短收尾与新横移相互清除。不要把当前“滚轮打断通过”解释为横向滚动已经实现。

## 复验入口

普通 HTTP 入口进入 A3；`?debug=1` 可查看第一步只读框线。测试脚本使用 `--origin`、新的 `--out` 目录和 `--build-record`；云图形环境另传 `--env-file`。

四卡入场及打断由 tests/card-refinement-step-2/verify.py 复验；真正后台标签切换另用 native_background.py，不能依赖 Playwright 默认焦点模拟。保留本次原速录像、最终候选证据和此前各步证据，不覆盖旧目录。

本步服务已停止；后续预览请新建自己的服务并记录归属，不复用已关闭的测试端口。
