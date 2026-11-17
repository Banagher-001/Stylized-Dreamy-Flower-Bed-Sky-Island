# 关于我改版 · 第七步验收

最终版本核对：2026-11-16T12:29:58.249966+08:00（Asia/Shanghai）。采用143项通过检查；npm run build（含TypeScript）、git diff --check通过。所有采用报告的源文件和资源SHA与当前交付一致。

| 范围 | 通过 | 采用报告 |
| --- | ---: | --- |
| 轨道功能、暂停姿态、分类、输入、适配与导览 | 26 | [verified-track](evidence/step-7/verified-track/browser.json)，除速度项 |
| 同一动画帧对齐的基础速度复测 | 1 | [verified-timing](evidence/step-7/verified-timing/browser.json)，返回项为补充复核不重复计数 |
| 原有静态组件功能 | 49 | [delivery-components](evidence/step-7/delivery-components/browser.json) |
| 播放/暂停/全部工具快照、重建和销毁 | 5 | [delivery-state](evidence/step-7/delivery-state/browser.json) |
| 首末牌面实际命中、原生点击与焦点 | 2 | [verified-hit](evidence/step-7/verified-hit/browser.json) |
| 真实主站多视口及原有阅读功能 | 44 | [verified-main采用汇总](evidence/step-7/verified-main/adoption.json) |
| 浅弧形和详情表面、阴影边界 | 8 | [verified-projection](evidence/step-7/verified-projection/browser.json) |
| 影像、罗森、瓶中海洋、环境与连续导览 | 7 | [verified-regressions](evidence/step-7/verified-regressions/browser.json) |
| 真实速度完整22张循环 | 1 | [verified-cycle](evidence/step-7/verified-cycle/browser.json) |

并发的delivery-track运行曾出现基础速度偏低与返回时序检查失败，原记录保留。最终版将返回激活收紧为镜头停稳、牌面可读，轨道交互26项通过。原速度检查跨帧读取距离与时间，仍有采样偏差；改为在同一requestAnimationFrame时间戳读取后，速度与返回两项复测通过，速度实测 28.000px/s，只把速度项另计一次。异常长帧限制用于避免阻塞后猛跳，旧失败没有覆盖或改写。

## 关键结果

完整自然运行 206.83 秒，22个ID全部出现，实例未替换；22次换位均在实际牌面离屏后发生，循环边界前后帧坐标连续，未修改时钟。原始全程录像与逐帧接缝数据保留。普通演示录像包含运行、暂停及原生Enter继续。

返回全部工具保持实际逻辑偏移和牌面弧度；尺寸变化保持卡牌ID与卡位比例；手机操作后恢复宽屏沿用新位置。运行和暂停快照可跨组件重建，旧实例销毁后不再更新。局部露出的第四张卡首次点击可打开完整详情，键盘焦点保持。

主站多视口覆盖1920/1440/1366/1280/1024/820/390/320及横屏、小屏、大字号、减少动态和图形不可用降级。两个嵌入网页通过真实原生操作验证：罗森时间滑杆Home，瓶中海洋暂停及实际渲染诊断；关闭后iframe清理。图形不可用案例保留两条预期错误，常规主站案例无新增运行错误。

[自动展示演示](evidence/step-7/step-7-display.mp4) · [循环接缝](evidence/step-7/step-7-seam.mp4) · [运行画面](evidence/step-7/verified-motion/running.png) · [暂停画面](evidence/step-7/verified-motion/paused.png)

[构建记录](evidence/step-7/build-check.json) · [历史保护](evidence/step-7/protection-final.json) · [视觉核对](evidence/step-7/visual-review.json) · [最终汇总](evidence/step-7/final-summary.json)

## 过程记录与限制

早期过程发现并修复：原生横向首个事件被丢弃、退后牌面被透明父层拦截、归还节点丢失焦点、稳定阅读误用已移位底栏的边界、恢复播放时弧度回零、指针点击局部卡前提前对齐按钮，以及原生接管后保留旧轨道锚点。相关失败、定位日志和被替代的运行目录保留，最终采用只以上表为准。

部分旧主站测试使用scrollLeft判断全部工具返回位置，已按程序模式改查逻辑位置；文字范围与真实牌面投影比较。主站详情测试原本等待移动按钮稳定，改为真实鼠标事件后单项通过；采用汇总明确链接原43项与该1项复测，原超时不覆盖。旧记录器访问已被移除的子节点导致的空引用也保留并修正。较早的自然运行属于调试版本，不替代最终整轮验收。两个被中止的录屏任务在关闭阶段挂起，已核对其命令及父子关系，只清理这些自有进程树；部分录像不纳入采用，见evidence/step-7/cancelled-recorders-cleanup.json。

录像固定环境时间便于核对卡牌，飞入、轨道及导览时钟未加速。浏览器为Linux Chromium，手机为视口模拟；页面隐藏分支明确使用模拟visibility事件，没有宣称物理手机、Safari或Firefox验证。

2,353个第六步及更早文件的SHA原样保留，正文、图案、依赖和嵌入网页未修改。已关闭本次两个专用验收服务，其他服务未停止；未提交、推送或发布。
