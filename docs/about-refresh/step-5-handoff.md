# 关于我改版 · 第五步交接

状态：第五步完成，2026-11-15T19:38:30.190286+08:00（Asia/Shanghai）。后续应从本工作区版本继续，先细化第六步，再按用户指令执行；本次未提交、推送或发布。

[外观说明](step-5-appearance.md) · [验收](step-5-verification.md) · [独立姿态检查](step-5-card-preview.html)

## 第六步可直接使用

| 位置 | 已完成的职责 |
| --- | --- |
| src/tour/about-refresh/createToolCard.ts | 同一正文的正背面、侧边几何、尺寸观察、姿态、可读性、销毁与投影范围 |
| src/tour/about-refresh/toolCards.css | 石质材质、6px 厚度/切角、独立 3D 层、阴影、前景容器与大字号规则 |
| src/tour/about-refresh/toolMarks.ts | 22 张本地图案，brand/family/purpose 类型明确 |
| src/tour/about-refresh/createToolBrowser.ts | 卡实例生命周期、分类/位置/详情恢复、原有键盘/触摸/查看全部控制 |
| src/tour/createPillarReader.ts | 主站阅读与容量协调；导览仅读可见卡正面 |
| dev/about-cards/index.html | 开发姿态检查；开发全局与审阅样式没有进入主包 |

createToolCard 返回 element、setPose、setExpanded、measure、dispose。setPose 接收 pitch/yaw 角度与可选 scale/lift，当前约束 pitch±80°、yaw±180°、scale 0.7—1.3。转到侧后角度时正面 inert，正面朝向恢复后可读、可操作。每张卡通过 ResizeObserver 更新八段侧边，销毁时 disconnect 与 abort。

position 层使用 --ar-card-x/y/z；reading 层使用 --ar-card-read-scale 与 --ar-card-lift；orientation 层使用 --ar-card-pitch/yaw。不要让多个阶段同时写入同一个 transform；统一协调姿态与侧面光照，避免只改 CSS 角度后没有更新辅助阅读状态。

## 第六步飞入设计的承接约束

1. 首批只有 Midjourney→ComfyUI→可灵→Blender 四张；全轨道 22 张与分类顺序来自原 content.ts。不能把 22 张同时飞入。
2. 本步 .ar-card-foreground 为空，位于同一 .ar-tools-browser 内，pointer-events:none，子卡可操作。它只是下一步的挂载位置，没有完成移动或动画。
3. 飞入应移动同一张真实卡，不复制可聚焦正文。移动前保留原 slot 占位并锁住实际宽高，在浏览器内部前景层确定定位参考系；原位置不能因移出卡而塌陷。
4. 飞入完成后归还节点及交互状态，取消飞入、反向离开、分类/查看全部/返回/销毁时也应先归还或清理。既有点击委托属于工具浏览器，移动到其外部会丢失委托。
5. 需要统一的时间驱动与可取消状态，不给每张卡各建永久循环。姿态不能把文字和点击保留在不可见背面；减少动态效果与窄屏仍能完整阅读。
6. 当前普通阅读保持零倾角，动态期间的透视/包围范围需按真实表面复测。measure 已包含十个面的投影并为阴影预留左右各10、上4、下18px；它不是所有未来飞行动作的安全证明。
7. 原有主站导览仅读卡片正面；以后必须等待首批卡实际到达且可读后再计阅读时间，离开或中断及时取消。不能只在动画开始时设置“完成”。
8. A3 目前 1440×900 沉浸布局为 1080×652.265625px，依赖原有阅读容量测量。额外运动空间需协调并复测，不能硬挤压 300px 基础卡高。

## 保留的限制与行为

本步是 CSS 3D 石质实体与静态光照，没有第二个 WebGLRenderer，也没有真正世界空间阴影。原生横滑/对齐、前后按钮、点击详情、全部工具、返回焦点、稳定阅读、原生 dialog 与手动操作打断主导览继续有效。未来自动轨道要明确与原生 scroll-snap 的启停关系；滚轮速度与惯性仍属第八步，悬停跟随属第九步，飞离属第十一步。

22 个正文和分类、身份/经历均保持前四步内容，不增加项目、奖项、业绩或相关作品入口。现有 AI 影像、罗森与瓶中海洋照常保留。图案来源见资源记录，不将五个用途符号描述为官方 Logo。

第六步需新建基线及证据，不覆盖本步和以前归档。最终采用检查为实体61、组件49、主站44、投影8、回归7项全部通过。开发可运行 npm run dev，主站 /，实体检查 /dev/about-cards/index.html，独立组件 /dev/about-refresh/index.html。
