# 卡牌入场与轮控改进

本轮按用户确认的七步逐项推进，每步先细化标准，再按指令执行。

1. 统一卡牌区域、输入归属与调试检查。
2. 加强四卡飞入的可见行程、远近与转面。
3. 接入全区域滚轮横移，覆盖自动暂停和分类后的手动状态。
4. 协调悬停、固定、惯性与自动展示偏好。
5. 完善首尾和页面运镜交接。
6. 更新提示及不同输入/减少动态适配。
7. 整体操作验收。

七步已完成。第七步记录了普通访客路线、设备操作和独立解压包验收。

- 第一步：[交互合同](step-1-contract.md) · [验收](step-1-verification.md) · [交接](step-1-handoff.md)。
- 第二步：[入场实现](step-2-entrance.md) · [验收](step-2-verification.md) · [第三步交接](step-2-handoff.md) · [原速演示](evidence/step-2/step-2-entrance-final.mp4)。
- 第三步：[滚轮实现与验收](step-3-wheel.md) · [原速演示](evidence/step-3/step-3-wheel.mp4)。
- 第四步：[阅读与续播验收](step-4-reading.md) · [原速演示](evidence/step-4/step-4-reading.mp4)。
- 第五步：[边界、离场与归位验收](step-5-departure.md) · [原速演示](evidence/step-5/step-5-departure-final.mp4)。
- 第六步：[操作引导与输入适配](step-6-guidance.md) · [桌面操作说明](evidence/step-6/desktop-help.png)。
- 第七步：[整体验收与交付](step-7-acceptance.md) · [普通访客路线原速录屏](evidence/step-7/card-refinement-step-7.mp4)。

普通入口的卡牌区支持滚轮横移。第一步的框线与读数在 `?debug=1` 下查看。第二步的视觉舞台覆盖更宽的画幅，滚轮继续以第一步的输入区为准。入场中的合格输入会先触发快速落位，再推动卡排。

悬停和固定阅读会暂时停住卡排。收起详情或结束手动横移后，按用户的自动展示选择恢复。滚动结束后重新移入卡面即可预览。

有限卡排接近两端时减速，移出区域后新的滚轮交给页面。镜头离开工具阅读区，当前牌面飞出。向反方向进入阅读区时从当前姿态归位。
