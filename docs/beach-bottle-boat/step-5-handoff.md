# 第五步交接：后续隔离检查与完整功能对照

第五步已把完整瓶中海洋接入 Coding 大尺寸现场。本轮只执行第五步，未提交、上传或发布。原未提交成果保留；第二步仍仅有标准，第六、七步尚未执行。日期：2026-11-13（Asia/Shanghai）。

## 当前可接续的入口

| 项目 | 实际接口 |
|---|---|
| Coding 顺序/默认 | LAWSON → BOTTLE OCEAN → COURTYARD，默认罗森 |
| 瓶中海洋动作 | 选择 bottle-ocean，点击“进入完整网页” |
| 运行/独立入口 | resolveProjectEntry('bottle-ocean') → experiments/bottle-ocean/index.html；两处同一地址 |
| 原成品 | public/experiments/bottle-ocean/index.html，1,979,264 字节，SHA256 941feb2ea6ddd3cc93aad5b0b92dbca52ee66a3e1098fee0dbf16f01ca63d1ef |
| 实例控制 | createEmbeddedPageExperience 的 mount/retry/unmount/dispose；作品 profile 只读原信号 |
| 原页观察 | createBottleOceanExperience；__bottleOcean、#gl、原 renderer、#loader、#loader-error、__bottleError |
| 状态归属 | setEmbeddedStatus(owner,state,message?) 只接受当前同身份现场；共用控制器另核对实例、Document 和 canvas |
| 路由与退出 | syncEmbeddedExperience 先卸载不需要的实例；去档案/关闭/重试移除旧 iframe |
| 覆盖与阅读 | 原 beginOverlay/closeOverlay、covered、syncLoop、readingLayout 快照继续使用 |
| 当前候选 | docs/evidence/beach-bottle-boat-step-5/candidate-manifest.json，97 项生产输入与独立 after 快照 |

本步没有新增依赖或改原场景。原罗森运行文件和工厂入口保留，实际错误重试/退出/切瓶中海洋通过。完整规范见 [状态约定](step-5-state-contract.md)，最终采用记录、失败和环境边界见 [验收](step-5-verification.md)。

## 第六步细化时应承接的事项

1. 以本步实际候选为 before，不回到 git HEAD 重放第四/五步。固定原 HTML、封面、罗森及原仓库，并校验此前 12 组封存（本步新增一组）；不要用旧阶段“全部产品源码不变”的总断言阻止后续授权改动。
2. 扩展系统异常/隔离检查：更快的进入/退出、连续多轮重试/切换、不可访问或意外导航、慢载入中换作品、父/子单独失败与实际图形丢失，观察旧任务是否能污染新作品。已有代表故障通过不替代这些完整边界。
3. 浏览器能力/权限与布局：根据支持条件实际检查全屏/退出、键盘和指针归属、更多最窄尺寸/文字放大/方向变化、父页图形不可用等，记录实际支持范围，不给原页没有的功能造按钮。
4. 在能真实进入 hidden 的环境补后台返回与节流；本次 Xvfb 只得到 visible 标签往返同实例，未观测 hidden。禁止改 hidden 或派发假 visibilitychange 作通过证据。
5. 有条件时补 Windows、真手机和 Safari、硬件 GPU。Linux WebKit 和触摸模拟结论不能替代真机；短时显存读数不能证明资源无泄漏或同步归零。
6. 继续验证主站关于我、AI影像、Coding、导览与阅读恢复，以及罗森和庭院的既有能力；按实际改动扩大必要回归，不把本步代表测试称作全站无影响证明。

## 第七步完整对照的基线

从 [feature-matrix.md](feature-matrix.md) 的 12 滑杆、22 按钮及其他操作逐项对照独立原页和内嵌原页。使用原生输入核对实际对象、相机、轨迹或下载，不能以控件数量和同一标签代替实际功能。

- 本步已经在三个引擎完成代表波高、曝光、玻璃、环境开关、俯视镜头、快捷键、手势、下载；沙盒实际对象/撤销恢复、暂停继续主要在 Chromium。其余参数、全部档位/镜头、拾取、完整重置、双指缩放及边界仍需按第七步矩阵核对。
- 原页参数/镜头结果可能受惯性、相位和取景约束影响，不能直接写状态、相机或时钟来制造一致。短自然轨迹证明联动，不意味着独立/内嵌逐帧坐标相同。
- 原 PNG 只含 WebGL 场景，尺寸按实际 canvas CSS × min(DPR,2)。本步已保留 1440×844/DPR1 和 960×544/DPR2→1920×1088 的真实按钮下载，后续不得固定写为 1920×1080。
- [original-issues.md](original-issues.md) 中亮度步进、standard 精度、镜头剩余惯性、图形丢失旧 ready、原暂停持续绘制和竖屏裁幅等继续作为原基线。若以后授权修原页，须单独变更和验证，不能归为本次接入修复。

## 证据与后续工作区

所有首次失败和复测另目录保存。本步 6 项未通过均来自测试注入/记录或过严焦点顺序假设，未改产品实现；最终按单项记录采用，原报告没有改写。共用代码、状态观察、原控件均有实际浏览器证据。

本步浏览器及 3 个自有服务已退出，临时构建目录清理，原 dist 没有覆盖。下一步若需要运行，按仓库现有 npm 命令启动自己的服务/临时构建，不能使用已清理的本步临时地址作长期预览。

`python tests/beach-bottle-boat-step-5/finalize.py --verify-only` 可独立核对本步封存与此前历史，封存目标为文档、脚本、原始证据和 before/after 副本。当前产品路径仅记录在候选清单，后续授权修改时不需要改写第五步历史或旧验收脚本。
