# 关于我改版 · 第七步交接

状态：第七步完成，2026-11-16T12:29:58.249966+08:00（Asia/Shanghai）。继续第八步前先细化滚轮速度、方向与惯性标准，待用户指令执行。未提交、推送或发布。

[实现说明](step-7-track.md) · [验收](step-7-verification.md) · [主站录像](evidence/step-7/step-7-display.mp4)

## 第八步可直接使用

createCardTrack统一管理基础速度28、逻辑phase、period、单一帧循环、空间bend和原节点循环。对外有present、pause、play、step、position、capture、restore、native、refresh、clear和dispose；createToolBrowser持有唯一控制器，createAboutView.presentToolsTrack由真实宿主驱动。没有现成的滚轮速度API；第八步在同一个tick模型中加入输入速度贡献，不再创建第二套横移循环。

CardTrackSnapshot记录position（anchorId/offsetRatio）、program、cycled、enabled、decided、bend。恢复不使用离开时长，不追赶后台时间。弧度和起速eased分开，不能再次用速度进度覆盖已建立的bend。前景飞入完成后节点归位，轨道才初始化；cancelled/ready不等于自动播放授权。

当前横向手势桥位于createToolBrowser的rail wheel监听：只有程序模式且abs(deltaX)>abs(deltaY)时，把首个事件移交原生位移一次；后续原生事件不重复消费。纵向滚轮没有被截获。第八步应在这里统一输入所有权和边界条件，避免新增重复监听、同一事件消费两次或把详情/全部工具中的滚轮变成轨道输入。

## 必须保留

1. 主导览、环境播放、工具展示分别管理，程序推进不调用onInteraction；用户操作仍停止主导览。
2. 暂停停止帧，继续保留phase和bend；减少动态、后台、手机、大字和模式切换按既定规则处理。
3. 每个工具只有一个真实节点。循环换位必须连同阴影离屏，保持首轮不提前露出末尾牌；不能用复制ID拼无限列表。
4. 只有真实牌面接收指针，编排stage、slot和实体容器不接收指针。键盘焦点可对齐，指针焦点不得在click前搬走局部卡的按钮。
5. 原生手动接管清除过期程序锚点；全部工具返回与快照恢复则保留程序位置、弧度与暂停选择。二者不能混用。
6. 同一position/reading/orientation层持续复用，后续悬停姿态要与轨道基姿态合成，不能直接争写transform。
7. 稳定模式底部边界来自视口，沉浸模式才扣除固定底栏。容量测量不重置或触发轨道，尺寸重测按真实卡牌ID和比例恢复。
8. 查看全部仍为七类22张，默认及分类两套顺序不变；正文不增加项目、奖项、业绩和作品入口。

当前工作区相对本步基线只修改createPillarReader、createAboutView、createToolBrowser和types，新增createCardTrack/cardTrack.css。主站入口与Three场景资源未另改。后续新建基线和证据，不覆盖本步档案。HEAD仍为 823da097c4a945f406ef266362822c2626e9251f；开发运行npm run dev，进入A3观察首批飞入与自动轨道，返回不会重播飞入。
