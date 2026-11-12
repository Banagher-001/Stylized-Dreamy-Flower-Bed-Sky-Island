# 第二步验收：Coding 展位与大尺寸原网页体验层设计

**第二步已完成。** 交付了设计定稿、可操作静态样稿、接口契约、第三步迁入清单和浏览器检查证据。本结论仅覆盖设计，不表示原网页已接入正式主站。

完成时间：2026-11-10T17:54:59.273645+08:00（Asia/Shanghai）。

## 交付与查看

- [静态交互样稿](../evidence/lawson-fullpage-step-2/design-preview.html)
- [设计定稿](step-2-design.md) · [接口契约](step-2-interface.md) · [第三步交接](step-2-handoff.md)
- [桌面展位](../evidence/lawson-fullpage-step-2/run-4/entry-1440x900.png) · [桌面体验层](../evidence/lawson-fullpage-step-2/run-4/live-1440x900.png)
- [手机体验层](../evidence/lawson-fullpage-step-2/run-4/live-390x844.png) · [手机档案](../evidence/lawson-fullpage-step-2/run-4/archive-390x844.png)
- [状态示例](../evidence/lawson-fullpage-step-2/run-4/state-error.png) · [大字号](../evidence/lawson-fullpage-step-2/run-4/font-200-320x568.png)

样稿可切换罗森/庭院、打开现场布局、切档案、返回、演示状态及 200% 文字。原网页区域由真实静态截图示意，页面明确标注设计样稿，没有 iframe、WebGL 或模型加载。“独立打开”在样稿中也只打开静态参考。

## 执行表

| 项目 | 完成结果 |
|---|---|
| 2.1 当前结构 | 明确固定庭院数据、open 回调、live 绘制、阅读恢复与故障入口的关系 |
| 2.2 C2 入口 | 默认罗森，庭院可切，单份预览，文案与真实封面对应 |
| 2.3 大尺寸布局 | 常规 56px、紧凑 48px 工具栏，页面占满其余空间；字号放大换行 |
| 2.4 交互状态 | 定稿打开、档案、加载、慢载入、错误、原全屏/Esc、返回与焦点规则 |
| 2.5 接口 | 冻结作品 ID、入口、实例、就绪错误、停绘与恢复契约 |
| 2.6 样稿 | 独立 HTML/CSS/JS，可查看状态，五张原图逐字节复制 |
| 2.7 核验交接 | 最终 13 组浏览器设计检查通过，46 文件逐项迁入映射已交付 |

## 实测可用区域

| 视口 | 工具栏 | 页面区域 |
|---|---:|---:|
| 1920×1080 | 56px | 1920×1024 |
| 1440×900 | 56px | 1440×844 |
| 1366×768 | 56px | 1366×712 |
| 768×1024 | 56px | 768×968 |
| 390×844 | 48px | 390×796 |
| 320×568 | 48px | 320×520 |
| 844×390 | 48px | 844×342 |

上述是宿主设计区域尺寸，原参考图保留比例；它不是实时原网页已经按这些尺寸通过功能测试的证明。主要外层按钮和展位入口至少 44×44 CSS px，检查了可见性及横向溢出。

200% 文字采用根字体从 16px 调整至 32px，不冒充物理浏览器缩放：

- 1440×900：工具栏自然高度 99px，主要操作仍在视口内。
- 390×844：工具栏自然高度 183px，主要操作仍在视口内。
- 320×568：工具栏自然高度 183px，主要操作仍在视口内。

## 浏览器检查

Chromium 155.0.8059.79，headless，DPR 1。最终 [run-4/design-checks.json](../evidence/lawson-fullpage-step-2/run-4/design-checks.json) 的 13 组全部通过：七种常规尺寸、作品身份/键盘/Esc、状态和独立参考/反复打开、三组大字号、减少动态。

未捕获脚本异常 0，HTTP 错误 0，请求失败 0，模型或原 runtime JS 请求 0，外部请求 0。减少动态时打开动画为 none。键盘检查确认作品切换、档案身份、关闭后的选择/焦点恢复及样稿参考区 Esc 优先级。

这些都是静态样稿检查。真实 iframe 焦点、全屏、鼠标锁定、原 41 控件和 17 类点击、主庭院实际停绘、跨尺寸返回和物理设备功能仍由第四至第七步完成。

## 修正及保留的记录

- run-1：工具栏边框导致高度多 1px；320px、200% 字体时顶栏横向溢出。修正为边框计入目标高度、顶栏自然换行，没有缩小文字。
- run-2：常规尺寸及交互通过；三组大字号在记录测量结果时引用了遗漏的脚本变量，用例保留为失败，没有删除。
- run-3：仅修正记录变量并定向复核大字号，三组通过。
- run-4：增加原手机/横屏截图参考后，对最终版本完整复核，13 组通过。最终样稿及验证脚本与该轮快照哈希一致。

## 文件与范围完整性

原运行文件 46 个、主站监测输入 91 个、旧封存 77 个及新版第一步封存 109 个均未变化，两个仓库原跟踪文件无差异。第一步封存清单未重写。

第二步只新增文档、静态证据和验证工具，并更新第二步标准的完成状态。没有创建 public/experiments/lawson，没有修改 src，没有提交、推送或发布。

- [完整性记录](../evidence/lawson-fullpage-step-2/integrity.json)
- [机器设计契约](../evidence/lawson-fullpage-step-2/design-contract.json)
- [第三步逐文件交接](../evidence/lawson-fullpage-step-2/step-3-handoff.json)
- [第二步封存](../evidence/lawson-fullpage-step-2/evidence-manifest.json)

## 复核方法

静态样稿使用普通脚本，可连同同目录 CSS、JS 和 assets 直接打开；这不改变正式主站和原页仍需 HTTP 的运行要求。自动化复核可在本地静态服务 4192 下运行：

```bash
python -m http.server 4192 --bind 127.0.0.1 --directory docs/evidence/lawson-fullpage-step-2
python tests/lawson-fullpage-step-2/verify_design.py --run new-run-name
```

每轮使用新目录保存结果与当时脚本/样稿快照；不要覆盖历史轮次。封存后只校验文件，不重跑第一步或第二步 finalizer 重写时间戳。
