# 第六步交接：第七步最终原版功能对照

第六步宿主核心加固已完成，49组通过，范围和未验证项见 [验收](step-6-verification.md)。第七步接着做原41控件、快捷键和17类场景点击的逐项对照，不重做接入或把控件数量一致当成功能全部通过。

## 1. 当前管理器和状态

createLawsonExperience仍提供mount/retry/unmount/dispose，只在lawson/live按需创建一个原iframe。entry仍用resolveProjectEntry，根目录/项目子路径规则保留；archive/关闭/销毁先卸载再恢复主庭院。

options.status现在是`status(state, message?)`，主站转交查看层setEmbeddedStatus。五种状态不变。可选message区分文档、图形和实际能力限制，查看层可在ready时显示能力说明；该说明不显示重试按钮。

完整文档缺失原#app或canvas#viewport时为“页面未能正常打开”，没有额外HEAD/GET推测HTTP状态。无法读取文档时保留loading/slow和出口；原fatal/API error/body error仍优先于ready。

当前文档canvas的真实lost/restored监听由独立AbortController拥有，文档变更或实例退出即取消。丢失后不信任旧ready，restored仍提示重新载入，由新文档建立可靠就绪边界。不要在第七步为了让断言通过自动清空原error、调用pauseAll或强制恢复原场景API。

父页回到可见或pageshow时立即重读当前文档，不自动重建实例、继续导览或改变原动画选择。后台行为仍由原页/浏览器保持，只有离开live主动卸载。

## 2. 第七步功能基线

以 [feature-matrix.md](feature-matrix.md) 和 [original-issues.md](original-issues.md) 为固定原版依据。41个控件为32静态按钮、1滑杆、8灯光控件；17类拾取绑定保持原行为。

建议先同环境独立原页/内嵌分别核查默认状态和入口，再按灯光/时间、镜头/屋顶、角色/车辆、场景拾取、快捷键、帮助/折叠/画质、错误重试与原生权限逐项记录。原有真实轨迹/时间用原时钟观察，访客操作采用原按钮/输入；调试API只辅助观察/定位，不替代宣称已发生的真实点击。

每项记录原版预期、实际原页、内嵌结果、差异归因及证据。原R惯性/漫游缓存、起点W/S碰撞、N文档差异、车辆帮助无拾取绑定等仍保留；不能一律写“正常”或暗中新增功能后称保全原版。

## 3. 已有证据可复用和必要重查

本步覆盖三种实际引擎的原页/基本灯光、桌面手机布局、连续尺寸变化，Chromium更深入覆盖真实触摸、200%浏览器缩放、actual CSS env安全区、异常与重试、真实hidden/visible、权限成功/拒绝、10完整＋20取消、真实HMR。

第七步修改若影响管理器/查看层状态、输入、返回、资源生命周期，再重跑关联核心项；场景和数值未变不用重复全部历史几何测试。不要修改旧脚本或重跑旧finalizer覆盖结果。本步after/封存源码副本，当前源码允许后续有明确记录的授权变更。

原页/内嵌手机版已同390×796视口比较，41控件和本地布局相同，原品牌/顶栏重叠也相同；不把该原移动问题称已修复。parent字体200%不继承给原文档，真实浏览器缩放则影响两者，测试语义必须分开。

## 4. 浏览器测试接入和工具经验

专用脚本在`tests/lawson-fullpage-step-6/`，接受用例的精确脚本快照、构建来源和选择在`accepted-browser-results.json`。最终构建build2只比build1增加实际全屏限制的能力说明，完整差异另存。HMR使用/tmp隔离副本，生命周期代码与build1一致，未修改主工作区制造热更新。

WebKit缓存启动脚本保留包内路径并加缓存宿主依赖，不改原包；这是Linux引擎，不是Safari真机。复用时先确认缓存路径/版本实际存在，不能无条件复制环境结论。

Playwright默认强制focus/visibility；仅新建辅助CDP session关闭该设置不足以证明真实隐藏。本步用独立Chrome、临时profile、`connect_over_cdp(no_defaults=True)`和默认上下文，实际切标签取得父/子hidden与visible，未改document.hidden或派发事件。原生权限退出用X11 Esc，不用DOM事件代替浏览器按键。

安全区方法名为`Emulation.setSafeAreaInsetsOverride`；早期拼错方法的失败保留，最终实际CSS env模拟通过。物理刘海与地址栏仍须设备。原生Tab可进入浏览器UI，检查document.hasFocus与具体目标，不把地址栏误作背景DOM可操作。主庭院cover离屏时不为获得ready强迫绘制。

## 5. 未验证边界

iOS/Android真机、物理刘海/动态地址栏、OS字号、真实屏幕阅读器、硬件GPU表现未核查。实际历史back成功但发生整页重载，BFCache分支未触发。Firefox/WebKit后台/原生权限全组合未穷举。第七步结果不能把这些自动补成通过。

被策略拒绝的全屏和无激活的指针锁定，原脚本仍有原有Promise拒绝；宿主不锁死且有说明/返回。完整对照时保留这个事实，不能通过吞掉全局异常制造无错误日志。

## 6. 完整性与最终交付

本步只改3个既有生产输入，其余92个保留。源/public/dist原46文件逐字节一致，六组历史封存保持原样。原运行文件、新代码与测试证据均尚未提交或发布。

第七步交付逐项功能对照、缺陷归因、最终构建与独立封存、运行/部署说明及已验证/未验证设备范围。提交GitHub或发布按用户后续明确指示进行；本步没有实施。

机器交接：`docs/evidence/lawson-fullpage-step-6/step-7-handoff.json`。
