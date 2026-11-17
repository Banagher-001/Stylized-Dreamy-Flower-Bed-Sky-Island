# 关于我改版 · 第六步验收

采用版本核对时间：2026-11-16T10:21:44.840023+08:00（Asia/Shanghai）。81 项浏览器检查通过，npm run build（含 TypeScript）通过，git diff --check 通过。

| 范围 | 结果 | 最终证据 |
| --- | ---: | --- |
| 飞入实体、触发、中断、适配和导览门槛 | 21/21 | [entrance-2](evidence/step-6/entrance-2/browser.json) |
| 装饰资源超时后的真实导览阅读 | 1/1 | [accepted-resource-guide](evidence/step-6/accepted-resource-guide/browser.json) |
| 主站多视口与完整阅读功能 | 44/44 | [accepted-main](evidence/step-6/accepted-main/browser.json) |
| 表面投影、阴影、首末展开、大字号 | 8/8 | [accepted-projection](evidence/step-6/accepted-projection/browser.json) |
| 影像、罗森、瓶中海洋、环境及连续导览 | 7/7 | [accepted-regressions](evidence/step-6/accepted-regressions/browser.json) |

五组检查均有源文件与生产资源清单，当前内容逐项 SHA 一致。主站检查的 A3 静态截图会等待真实入口 ready；飞行中的检查由专项逐帧完成，不以最终截图替代动画证据。

## 主要验收结果

- 初始四张实体表面完整位于视口外，实际画内出场顺序正确；飞行中有深度位移、旋转与可见背纹，不采用牌面淡入。
- 录像实际入场 1466.8ms；原 slot 在飞行到归位之间最大移动 0.0000px，节点未复制，重复 ID 为零。
- 分类首击、原生 Enter 下一张、全部工具首击和 Escape、继续浏览首击、滚动离开、窗口缩到手机和阅读模式切换均正常；返回不重播。
- 原生窗口探测和阅读容量测量不触发；准备中离开再回来仍能首次播放。
- 390/320px、1366×768 稳定模式、200% 字号及减少动态效果直接阅读；运动中切换减少动态设置也能收尾。
- 自动导览在飞入时尚无阅读截止时间，落位后 readyAt 不早于 entranceFinishedAt；点击分类仍停止导览。资源准备超时后也能开始真实阅读。
- 实际罗森 iframe 的时间滑杆 Home、瓶中海洋暂停按钮与渲染诊断、关闭后 iframe 清理、影像返回及环境播放暂停恢复均通过。
- 等待或完成时不保留入场帧循环；卡牌节点归还原位，前景容器清空，临时尺寸移除。组件销毁路径另做源码检查：取消帧、代际令牌失效、AbortController 与观察器清理；未另称已进行浏览器内组件反复销毁压力测试。

[真实主站录像](evidence/step-6/step-6-entrance.mp4) · [飞入前段/背纹](evidence/step-6/accepted-motion/early.png) · [飞入中段](evidence/step-6/accepted-motion/middle.png) · [落位后](evidence/step-6/accepted-main/desktop-A3.png) · [手机](evidence/step-6/accepted-main/phone-A3.png)

[逐帧核对](evidence/step-6/motion-validation.json) · [录像版本上下文](evidence/step-6/accepted-motion-source-context.json) · [人工视觉核对](evidence/step-6/visual-review.json) · [构建](evidence/step-6/build-check.json) · [历史保护](evidence/step-6/protection-final.json)

## 过程记录和实际限制

inspection-1 显示初版起点过远，后发卡牌可能先进入画内；改为按实际投影边缘求解画外起点，并延后背面转正，使背纹在画内可见。inspection-2 未成功建立录屏页，原因是录屏工具默认缓存路径，之后使用工作区已有 ffmpeg 完成，不下载新依赖。

entrance-1 为 11/21。实际发现稳定阅读在环境暂停时没有刷新入场就绪状态，已加入独立的交叉观察触发。其余失败来自检查工具取到轨道尾部卡牌、全部网格没有 slot 时的记录器空引用、原生 focus 先于 click 中断以及导览 moving/arriving 的阶段断言；均修正记录器或断言后保留原始失败文件。当前源文件随后通过 entrance-2 21/21 和全部最终回归。

浏览器为 Linux Chromium 155.0.8059.79，视口模拟不代表物理手机或 Safari/Firefox。页面隐藏分支使用明确标记的模拟 visibilitychange；资源延迟通过测试页面临时覆盖图像 complete 属性，不修改生产代码。主动禁用 WebGL 的主站降级案例有两条预期报错，普通案例没有新增运行错误。

2,003 个第五步及更早的历史文件 SHA 未变化。正文、22 个本地图案、依赖和两个嵌入网页未更改。已关闭本次两个专用验收服务，端口关闭，其他服务未停止；未提交、推送或发布。
