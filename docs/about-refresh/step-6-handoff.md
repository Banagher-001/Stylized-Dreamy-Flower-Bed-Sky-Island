# 关于我改版 · 第六步交接

状态：第六步完成，2026-11-16T10:21:44.840023+08:00（Asia/Shanghai）。应从此工作区继续第七步，先细化、待用户指令执行；本次未提交、推送或发布。

[实现说明](step-6-entrance.md) · [验收](step-6-verification.md) · [实际录像](evidence/step-6/step-6-entrance.mp4)

## 可复用接口

| 位置 | 当前职责 |
| --- | --- |
| createCardEntrance.ts | 一次性四张飞入、资源准备、投影起点、有限帧循环、归还和取消 |
| cardEntrance.css | 独立裁切窗口与共享透视舞台；运动期间禁用轨道 snap |
| createToolBrowser.ts | 入场控制器与已有分类/详情/全部工具/状态恢复衔接 |
| createAboutView.ts | presentToolsEntrance、cancelToolsEntrance、toolsEntranceReady 转发 |
| createPillarReader.ts | 实际 A3 触发、静态 IntersectionObserver、排除 measuring 的调度 |
| startTourPrototype.ts | 就绪唤醒与 A3 导览阅读门槛，其他站点图片检查保留 |
| createToolCard.ts / toolCards.css | 原实体增加 roll 姿态，阴影跟随定位层，静态阅读外观保留 |

presentEntrance 接收 active、enabled、revealed；cancelEntrance(reason) 结束待播/飞行并静态归位；entranceReady 表示可以阅读。AboutViewOptions.onEntranceChange 负责就绪状态通知，宿主只唤醒导览或单次渲染，不发起容量重测。数据属性 entrance、entranceReady、entranceReason、entrancePlays、entranceFramePending 可用于检查。

## 第七步自动轨道的接入约束

1. 入口 preparing/playing 时不能启动轨道。ready/completed 后才允许按第七步的播放规则开始。cancelled 也表示可阅读，但不代表可以自动恢复用户已中断的展示。
2. 下一步必须独立区分主站自动导览、工具自动展示和环境播放；不要把它们绑定同一个暂停状态。
3. 全 22 张默认顺序与七类顺序继续来自原 content.ts。入场只处理首批四张，其他卡仍在原轨道正常占位。
4. 飞行结束已把同一节点放回 slot，清空 foreground 并移除临时宽高；轨道应以归位后的真实尺寸初始化。
5. 卡牌 position、reading、orientation 分层保持。当前 roll 扩展会更新侧边受光；未来轨道倾角与悬停不能争写同一 transform。
6. 原生 scroll-snap 在手机正常启用，仅 playing 时临时关闭。第七步须明确程序轨道与原生滚动的拥有关系；滚轮速度和惯性仍由第八步实现。
7. 分类、下一张、全部工具和焦点可以中断入场，且首个操作生效。未来轨道启停同样要保留这些行为、焦点恢复和原分类/位置/详情状态。
8. 静态降级 ready/static-reading 不播放完整飞入；减少动态和窄屏的自动展示策略需由第七步明确，不能仅因 ready 就强制自动运动。
9. measuring=true 的容量探测不消费首次入场，也不能在未来启动或重置自动轨道。真实主站 A3 阅读容量与阴影余量仍需保持。
10. 入场使用有限独立时钟，环境暂停不影响落位；当前没有自动横移、滚轮加速、鼠标跟随或飞离。第七步不得提前吞并第八至十一步的交互。

后续新增基线与证据，不覆盖本步或旧记录。当前 HEAD 仍为 823da097c4a945f406ef266362822c2626e9251f，修改保存在工作区；生产构建和 81 项检查通过。开发运行 npm run dev，从主站第三屏首次进入可观察完整飞入；刷新可重新验收，返回 A3 本身不重播。
