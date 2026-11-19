# 第一步实现交接

本轮七步的第一步建立统一区域与只读输入合同。当前页面的入场时长、卡片样式、轨道、wheel、悬停/固定和自动状态管理仍采用之前的实现。新的动作名称是供第三步接入的计划，不代表此时已经收起详情或推动卡排。

## 代码入口

- `src/tour/about-refresh/cardInteractionRegion.ts`：createCardInteractionRegion(...).inspect(input?)，只读地返回当前区域与建议归属。宽度使用卡槽 offsetWidth 加间距和内边距，避免 hover/flight transform 影响。模态、帮助、全文、原生输入与浏览器组合手势优先。
- `src/tour/about-refresh/createCardRegionDebug.ts`：仅 debug=1 创建 body 内的只读显示；所有输入监听 passive，不调用 preventDefault，不写回工具状态。观察模式、分类、阅读和布局，单帧合并更新，dispose 清理。
- `src/tour/about-refresh/createToolBrowser.ts`：只添加两个导入、判定对象、调试开关和销毁接点。旧 wheel handler 保持逐字一致。

开发服务器或生产 HTTP 预览打开 `/?debug=1`，进入 A3 工具区，检查虚线与左下角“只读，不接管输入”。普通 URL 没有这个检查层。界面状态改变后，读数在下一次合并的浏览器绘制帧更新；检查应等待更新，不以弹层 close 属性变化的同一瞬间读取旧值。

## 第二步承接

第二步只细化并执行飞入：扩大可见飞行舞台、四卡错峰、侧背转正、落位和短暂停留。首批仍为原定四张，实际可见后才消耗首次机会，主动操作可以接管，保留已有分类与当前位置。

入场的视觉舞台可以比第一步的目标卡排区域宽；飞行卡的运动不能改变本步交互边界。第二步不把动画是否正在播放当作未来手动横移的开关。

## 第三步承接

在原生 wheel 路由中调用统一 inspect。cards 只消费一次，page / overlay / browser 保留相应行为；实际接管还需检查原生事件是否可取消，避免同时发生页面滚动和额外横移。

补齐 native/manual/分类后未创建程序舞台的状态。按合同接入预览/固定收起、明确自动偏好与临时持有、首尾阻尼及移出交接。不要把当前只读诊断结果当作已经完成的横移功能。

本步交付在工作区，不提交、不推送，不改历史包。验证与适用范围见 [本步验收](step-1-verification.md)。
