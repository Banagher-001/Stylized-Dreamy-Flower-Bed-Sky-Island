# 关于我改版 · 第五步验收

采用版本核对时间：2026-11-15T19:38:30.190286+08:00（Asia/Shanghai）。生产构建含 TypeScript 检查通过，当前工作区卡牌源文件与最终浏览器证据的构建清单一致。

## 最终检查

| 验收项 | 结果 | 依据 |
| --- | --- | --- |
| S5-01 庭院配色与石质层级 | 通过 | 正面、背面和主站最终截图人工核对 |
| S5-02 正文、数量、两套顺序 | 通过 | 21 款工具+1 张能力卡、7 类、首批四张与 G1 分类顺序保持原数据 |
| S5-03 本地图案与来源 | 通过 | 22 个自包含 SVG、SHA 对照、品牌/家族/用途符号区分 |
| S5-04 真实厚度与侧边 | 通过 | 十表面、6px 厚度、八段切角侧边、DOMMatrix 接缝测量 |
| S5-05 背面与侧后阅读控制 | 通过 | 背面无遮挡穿透，装饰隐藏于辅助阅读，侧后正面 inert |
| S5-06 材质与阅读清晰度 | 通过 | 正面平直、颗粒低透明、CSS 3D 链保持、真实 HTML 字号 |
| S5-07 22 张正面/详情及极值 | 通过 | 实体 61 项，包括长名称、斜侧面、背面、窄屏和大字号 |
| S5-08 主站实体及阴影边界 | 通过 | 投影专项 8 项，首末展开及大字号余量通过 |
| S5-09 响应式与全部工具 | 通过 | 组件 49 项，主站 44 项，320—1920px 多视口与 200% 字号 |
| S5-10 原生操作与导览 | 通过 | 原生按键、触摸横滑、返回恢复、真实 A1→A2→A3 导览及 7 项回归 |
| S5-11 空闲与资源 | 通过 | 实体静止像素对照、无自有时钟/Canvas、无新增 WebGLRenderer、开发入口不进入主包 |
| S5-12 构建、历史与收尾 | 通过 | npm run build、git diff --check、1,163 个历史文件 SHA、专属服务关闭 |

## 采用的浏览器证据

| 范围 | 通过 | 最终报告 |
| --- | ---: | --- |
| 同源实体/材质/姿态 | 61/61 | [accepted-cards](evidence/step-5/accepted-cards/browser.json) |
| About 组件与已有控制 | 49/49 | [accepted-components](evidence/step-5/accepted-components/browser.json) |
| 真实主站接入 | 44/44 | [main-final](evidence/step-5/main-final/browser.json) |
| 实际表面及阴影余量 | 8/8 | [projection-final](evidence/step-5/projection-final/browser.json) |
| 站点完整功能回归 | 7/7 | [accepted-regressions](evidence/step-5/accepted-regressions/browser.json) |

7 项回归包括阅读层缩到手机、原生滚轮导航、影像打开返回、罗森 iframe 时间滑杆操作与关闭、瓶中海洋暂停与实际渲染、环境播放暂停恢复，以及未修改时钟的连续自动导览。主站主动模拟 WebGL 不可用时的两条预期报错记录在报告中，降级阅读通过；正常案例没有新增错误。浏览器为 Linux Chromium 155.0.8059.79；手机/平板为浏览器模拟，不代表实机或其他内核验证。

## 可直接检查的交付

- [独立卡牌验收页](step-5-card-preview.html)：同代码、单文件，可切换姿态和全部 22 张卡；不需要额外 WebGL。
- [斜侧面](evidence/step-5/accepted-cards/sample-quarter.png)、[背面](evidence/step-5/accepted-cards/sample-back.png)、[静态详情](evidence/step-5/accepted-cards/sample-detail.png)。
- [主站桌面](evidence/step-5/main-final/desktop-A3.png)、[手机](evidence/step-5/main-final/phone-A3.png)、[大字号修复后](evidence/step-5/projection-final/large-text-detail.png)。
- [资源检查](evidence/step-5/resource-check.json)、[人工视觉核对](evidence/step-5/visual-review.json)、[构建记录](evidence/step-5/build-check.json)、[历史保护](evidence/step-5/protection-final.json)。

独立验收页 SHA256：77828531e9271ce6fb0a7a0d906b916cd00af978b95ec685322108a0148d28a9；组件验收页 SHA256：f1fa9177c4b03fb418bb563454f6d7874f85e89c717e667c5d4a19980240231b。主站仍需 npm run dev 或 HTTP 服务，不把主站声明为双击 HTML 运行。

## 保留的过程记录与修正

早期样本采用轻微默认倾斜，人工核对发现正文重采样与阴影过方，之后改为阅读正面零倾角、正面 z=0，并收柔阴影。首次投影专项 projection-1 为 7/8；200% 字号展开仍沿用 115% 宽度，真实阴影左界超出轨道约 9.2px。已改为大字号保持 100% 宽度、按正文自然长高，projection-final 8/8；最终五组采用检查均在该修复后完成。

specimen-1、smoke-1、cards-final、component-final、accepted-main 和 projection-1 保留为过程记录，不替代最终采用报告。projection-final 没有单独输出源清单，其同一最终构建的对应关系另记于 [投影来源上下文](evidence/step-5/projection-source-context.json)，没有补改原报告。

卡牌没有自有动画循环；测试未进行跨浏览器与物理设备验收，也没有实现下一步飞入与后续自动轨道。已有正文、前三步预览、第四步主站记录和证据未覆盖。仅关闭第五步自有的两个验收服务，未停止其他服务；未上传或发布。
