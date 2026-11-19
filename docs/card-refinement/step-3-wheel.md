# 卡牌改进 · 第三步滚轮横移

在「工具与方法」把鼠标放在卡面、间隙或卡牌区两侧留白，向下滚轮查看后面的卡，向上回看前面的卡。也可以暂停自动展示后再滚动。原生轨道到首尾后停在边界，移出卡牌区继续滚动页面。全部卡片已放下的分类直接浏览页面。

[原速操作演示](evidence/step-3/step-3-wheel.mp4) · [构建记录](evidence/step-3/build.json) · [采用结果](evidence/step-3/adoption.json)

## 实现和交接

- `createToolBrowser.ts` 的单个可取消滚轮监听覆盖第一步的完整区域。使用 `inspect` 查归属，归一化后由一条路径消费。接手时取消排队的位置恢复，解除预览或固定，分类切换保留自动开关。帮助、全文、导航和浏览器组合手势沿各自路径处理。
- `createCardTrack.ts` 的同一帧循环负责手动和自动位移。原生卡排累计浮点偏移并写 `scrollLeft`，在实际首尾夹紧。程序轨道继续使用当前环形相位。停手后，暂停状态归零并停止轨道帧，自动开启时回到既有的 28 CSS px/s。
- `cardWheelInput.ts` 使用 100ms 样本计算强度，上限 560 CSS px/s。80ms 的输入保持后，200ms 内按实际速度平滑收尾。在持续帧率较低的环境中，停止会在随后的绘制帧被观测到。明显反向优先制动。触控板横向以原始输入位移推进，减少动态使用直接位移。
- 飞入中，接收的位移暂存在当前卡槽上。`createCardEntrance.ts` 的 140ms 快速归槽结束后应用一遍。分类、布局变更、退出和弹层会清理待处理输入。切换到触摸时恢复原生滚动吸附。
- 固定状态和继续浏览的现有提示已跟随新归属修正。第四步接着处理滚完后恢复预览的时机和自动展示的临时持有。第五步承接首尾动效和离开第三屏的镜头时机。

## 数据

1652×949 普通入口的基线在 G6 原生暂停态实测。四个位置的下滚各使页面前进 120px，卡排位移为 0。用下一张移动到中段再上滚，页面后退 120px，卡排仍没有响应。 [改动前的实测](evidence/step-3/before/original-native-wheel-gap-data.json)

最终构建以同样的 120px 输入测到如下位移。响应时间定义为实际 `scrollLeft` 达到 8px 的首帧。测试中卡排接管后，页面纵向位置和镜头目标保持原位。 [实际输入和帧数据](evidence/step-3/final-checks/paused-native-four-points-and-reverse-data.json)

| 位置 | 响应时间 | 停稳后的横向位移 |
| --- | ---: | ---: |
| 牌面 | 129.1ms | +22px |
| 卡片间隙 | 136.7ms | +22px |
| 左侧留白 | 107.9ms | +25px |
| 右侧留白 | 114.5ms | +25px |
| 牌面反向 | 114.5ms | −24px |

慢组和快组各发送五笔 60px 的可信浏览器事件，目标节拍分别为 200ms 和 40ms。峰值速度分别为 130.4 和 447.9 CSS px/s，约 3.4 倍。两组停止运动的第一帧均在最后输入后约 0.32 秒。软件渲染下实际接收节拍略有波动，时间与位移保存在测试记录中。减少动态测试中一笔 120px 输入直接移动 120px。 [节拍实测](evidence/step-3/cadence-final/result.json) · [减少动态数据](evidence/step-3/final-checks/reduced-motion-direct-data.json)

飞入中滚动一次，在卡片归槽后观察到横移 26px。软件渲染中的采样在约 220ms 确认归槽，在约 265ms 看到横移。分类抢先切换时，新的五卡排从分类自己的起点开始。 [飞入交接](evidence/step-3/final-checks/one-wheel-during-flight-data.json) · [切分类清理](evidence/step-3/final-checks/discard-flight-input-on-category-data.json)

## 复验

用 `npm run build` 构建，然后以生产目录 HTTP 预览。`tests/card-refinement-step-3/verify.py` 使用 `--origin`、新 `--out` 目录、`--env-file` 和 `--build-record`。`cadence.py` 按节拍并行发送可信轮控事件，记录发送和实际接收的时间。稳定阅读、减少动态与手机触控使用浏览器条件仿真。特殊的行、页、不可取消和组合键事件用明确的模拟验证归属。

最终检查覆盖暂停和自动、分类、反向、飞入、两端、帮助和全文、稳定阅读以及输入单位。帮助面板在标准尺寸下完整显示，全部工具的原生弹层实测独立上下滚动。另复验第二步的正常飞入、取消操作和区域稳定，以及第一步的手机原生触控、文字选择、键盘和大字阅读。最终候选合计通过 21 项，采用记录链接各用例。 [最终检查](evidence/step-3/final-checks/browser.json) · [帮助及全文复验](evidence/step-3/reading-final/browser.json) · [四卡入场回归](evidence/step-3/entrance-regression/browser.json) · [输入回归](evidence/step-3/input-regression/browser.json)
