"""Document the actual isolated component implementation and adopted results."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib,json
ROOT=Path(__file__).resolve().parents[4];DOC=ROOT/'docs/about-refresh';OUT=Path(__file__).parent
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=read(OUT/'matrix-1/browser.json');b=read(OUT/'build.json');c=read(OUT/'content-check.json');v=read(OUT/'visual-review.json');dev=read(OUT/'entrypoints.json');build=read(OUT/'build-check.json')
assert r['complete'] and len(r['checks'])==49 and all(x['status']=='通过' for x in r['checks'])
assert dev['complete'] and build['exitCode']==0 and c['complete'] and v['complete']
assert r['htmlSHA256']==dev['htmlSHA256']==v['htmlSHA256']==sha(DOC/'step-3-preview.html')==b['output']['sha256']
assert all(sha(ROOT/f['path'])==f['sha256'] for f in b['sources'])
now=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
measure=lambda id:read(OUT/'matrix-1'/f'{id}-measurement.json')
normal=measure('desktop-A3');detail=measure('desktop-detail')
names=[('large','1920×1080'),('desktop','1440×900'),('laptop','1366×768'),('short-laptop','1280×720'),('tablet-landscape','1024×768'),('tablet-portrait','820×1180'),('phone','390×844'),('narrow','320×740'),('short-landscape','844×390')]
matrix='\n'.join('| '+label+' | '+' | '.join('沉浸排版' if measure(name+'-'+screen)['layout']=='immersive' else '稳定阅读' for screen in ['A1','A2','A3'])+' |' for name,label in names)
implementation=f'''# 关于我改版 · 第三步实现与内容接口

状态：第三步完成。时间 {now}（Asia/Shanghai）。正式组件和独立开发入口已建立；原个人网页尚未接入新组件。

[打开独立静态组件预览](step-3-preview.html) · [实际验收](step-3-verification.md) · [第四步交接](step-3-handoff.md)

## 输入与内容

第一步固定文案为正文依据，第二步布局为尺寸与空间依据，原文件均保留。21 款工具、1 张能力卡、7 类，分类数量为 3/2/2/6/3/5/1。关于我内容没有项目、奖项、业绩、作品关联或跳转；游族网络没有补写岗位或日期。

正式数据在 src/tour/about-refresh/content.ts。正文转换脚本只在制作阶段读定稿文件；运行组件不读取 docs 或 evidence，也不包含简历原件与来源备注。

| 结构 | 用途 |
|---|---|
| identity | 章节、姓名、职业定位、两句介绍、关键词、化名说明 |
| experience | 三条经历、四个制作环节及完整说明、教育背景 |
| tools | 工具屏标题与介绍 |
| categories | 七类固定 ID、名称及类内 cardIds |
| cards | 唯一 ID、名称、用途、详情、两个标签、类型、分类、两套顺序、首批序位、标识占位 |
| controls | 第一步确定的操作词表，仅启用本步已有功能 |

推荐轨道按 recommendationOrder；分类按 categoryOrder，全部列表按 categories/cardIds 分组。默认首批仍为 Midjourney → ComfyUI → 可灵 → Blender；G1 内部为 Midjourney → 即梦 → ComfyUI，不混用推荐顺序。每张正文只有一份，所有视图按同一 ID 读取。

## 实际文件职责

| 文件 | 职责 |
|---|---|
| src/tour/about-refresh/types.ts | 内容、分类、视图与恢复状态类型 |
| src/tour/about-refresh/content.ts | 正式运行数据、两套排序与首批 ID |
| src/tour/about-refresh/dom.ts | 局部 DOM 创建与边界辅助 |
| src/tour/about-refresh/createAboutView.ts | 三屏、原生次级阅读、宿主接口与清理 |
| src/tour/about-refresh/createToolBrowser.ts | 分类、前后、详情、全部列表、位置与焦点恢复 |
| src/tour/about-refresh/aboutRefresh.css | 组件局部样式与响应式 |
| src/tour/about-refresh/preview.ts / preview.css | 独立开发页的切屏、大字、排版判断与检查入口 |
| dev/about-refresh/index.html | 已有 Vite 下的独立开发入口 |
| docs/about-refresh/step-3-preview.html | 同源组件编译得到的独立单文件预览 |

没有修改主站入口、旧 aboutContent、相机/滚动代码、package.json、锁文件或 Vite 配置。没有增加依赖。

## 三屏与静态操作

A1 默认显示身份、职业定位、两句介绍与关键词，化名来源通过原生 details 展开。A2 默认显示三条经历和四个制作环节，完整说明与教育背景在次级区域。A3 使用独立宽卡牌区。

隐藏屏同时使用 hidden、inert 与 aria-hidden，不参与当前布局和键盘操作。切屏时若焦点仍在即将隐藏的内容，转到新屏标题。

上一张/下一张移动一张并完整呈现对应卡片；首尾有明确禁用状态，不循环。详情按钮可通过点击、Enter 或 Space 展开完整正文，同一时间保留一个卡片详情。静态放大不挤动相邻卡位；手机采用自然向下展开。

桌面当前普通卡片 {normal['cards'][0]['rect']['width']:.0f}×{normal['cards'][0]['rect']['height']:.0f}，桌面放大宽度为 115%，真实高度可随完整内容增加，不硬裁文字。该静态样式不代替第 5 步卡牌实体和第 9、10 步正式悬停/详情设计。

当前提示为“使用前后按钮浏览，按 Enter 展开详情。”或手机的“左右滑动浏览 · 点按查看详情”。自动展示、滚轮加速提示尚未启用。主站继续入口仅在宿主提供 onContinue 时显示；独立预览保留对应空间。

## 全部列表与恢复规则

从任何分类进入全部，均按七类展示 22 张完整正文。轨道和列表不会同时保留两套重复卡牌 DOM。

返回恢复 category、activeId、expandedId，以及锚点卡片与偏移比例；尺寸未变时保留横向位置，尺寸变化时按原锚点卡片重新计算并限制在可用范围。返回焦点放回“查看全部工具”。当次浏览保留状态，刷新按默认开始。

状态是可复制的普通数据：AboutSnapshot 保存屏幕、A1/A2 展开状态和工具浏览状态；ToolBrowserSnapshot 保存 cards/all 模式与 CardsSnapshot；TrackPosition 保存 anchorId、offsetRatio、scrollLeft、viewportWidth。

## 正式宿主接口

createAboutView(host, options) 挂载组件，返回：root、station、setStation、setLayout、measure、captureState、restoreState、dispose。

setStation 只切换内容，不移动相机、不改变主站滚动坐标。setLayout 接收 immersive/stable 及可用高度；measure 返回当前屏幕的实际内容高度和所需高度。宿主负责真实安全区域、全站控件及容量判断。

options.onInteraction 用于通知真实用户操作；恢复状态不作为一次用户输入。options.onLayoutChange 通知次级内容/分类/详情改变；options.onContinue 由宿主注入真实章节跳转。独立预览没有导览回调或主站跳转。

宿主在大字布局时设置 root.dataset.largeText，并据实际字体与可用空间选择稳定阅读。preview.ts 中只演示独立页的容量判断；第四步不能直接把预览页高度当成主站安全高度。

销毁会中止本组件监听、断开 ResizeObserver、取消待执行的恢复帧并移除节点。组件没有自动播放时钟、滚轮监听、全局键盘监听或三维渲染循环。仅独立开发入口拥有预览窗口/字体监听和检查接口。

## 响应式实际结果

| 视口 | A1 | A2 | A3 |
|---|---|---|---|
{matrix}

这是独立预览的容量结果，未计入真实主站全部控件。手机、短横、大字及减少动态均可稳定阅读；正文至少 16px，主要操作至少 44px。背景为已有庭院封面图，主站实时场景和运镜由第四步接入。

## 开发与单文件预览

运行项目现有 npm run dev，访问终端给出的地址后加 /dev/about-refresh/index.html。该 URL 已在真实 Vite 中验证 A3 → G5 三张 → 全部 22 张 → 返回 G5 三张。

单文件预览由 evidence/step-3/build-preview.mjs 使用现有 Vite 编译同一套组件，再内嵌脚本、样式与原背景，不需要 CDN 或运行时证据文件。49 项采用记录通过本地 HTTP 检查该单文件；云浏览器禁止 file://，因此没有把直接双击 HTML 记为验证通过。
'''
(DOC/'step-3-implementation.md').write_text(implementation)
criteria=[('S3-01','定稿正文与范围','content-check.json，逐卡原文一致，无删去的公开字段'),('S3-02','唯一 ID、数量与分类','22 个唯一 ID，21/1 类型，七类计数与卡片归属'),('S3-03','两套顺序与首批','category-orders、推荐全量和四个首批 ID'),('S3-04','A1/A2 阅读与次级信息','九档三屏、identity-expanded、experience-expanded、phone-experience-expanded'),('S3-05','实际浏览控件','desktop-detail、edge-detail、track-boundaries、分类与前后操作'),('S3-06','任意分类进入全量','catalog-return-G5、narrow-all-tools、开发入口复核'),('S3-07','返回状态与焦点','catalog-return、catalog-return-G5、catalog-resize-return，保存前后数据'),('S3-08','完整文字与长名称','long-name、详情、逐项文字边界与人工截图查看'),('S3-09','九档与大字','27 项默认矩阵、large-text-A1/A2/A3、reduced-motion'),('S3-10','键盘和隐藏屏','native-keys，原生 Enter/Space，逐项 hidden/inert/aria-hidden'),('S3-11','生命周期','remount-cards/remount-all，重复挂载、单次回调、销毁旧按钮不再响应'),('S3-12','构建与保护','npm run build 含类型检查；252 项前置交付、97 项生产输入与 Git 范围核对')]
verification=f'''# 关于我改版 · 第三步验收

第三步完成，时间 {now}（Asia/Shanghai）。最终采用 matrix-1 的同版 49 项 Chromium 功能与静态布局检查，全部通过；开发入口另有 1 项通过。npm run build（包含类型检查）退出码 0。

[组件预览](step-3-preview.html) · [实现说明](step-3-implementation.md) · [下一步交接](step-3-handoff.md)

## 执行标准

| 编号 | 标准 | 实际依据 | 结论 |
|---|---|---|---|
'''+ '\n'.join('| '+id+' | '+name+' | '+e+' | 通过（本步范围） |'for id,name,e in criteria)+f'''

## 最终采用结果

[原始浏览器记录](evidence/step-3/matrix-1/browser.json)：Chromium {r['version']}、Linux、DPR1；49 项均通过，无 pageerror、console.error 或外部请求尝试。每项有测量数据和实际截图；输入与构建摘要随记录保存。

单文件 SHA256：{r['htmlSHA256']}。当前组件源码与 build.json 中摘要一致，采用报告和人工查看均对应此版预览。smoke-1 的 9 项先行检查也通过，保留为过程记录，不重复计入最终 49 项。

49 项 = 27 项九档三屏默认布局 + 22 项功能与特殊状态，涵盖次级阅读、七类排序、全部与返回、跨尺寸恢复、详情、长名、200% 根字号、减少动态、键盘、首尾边界、触摸、滚轮与重复挂载。

触摸使用 Chromium 原生 CDP 触摸输入，非脚本直接设置 scrollLeft。键盘使用真实 Enter/Space，检查展开及焦点保留。滚轮使用真实 mouse.wheel，确认未阻止原生纵向滚动；不表示主站运镜已经接入。

[开发入口记录](evidence/step-3/entrypoints.json)：通过现有 Vite 配置实际运行独立 URL，核对 G5 三张与全量 22 张往返。[构建记录](evidence/step-3/build-check.json)及 build-final.txt 包含实际命令输出。[内容记录](evidence/step-3/content-check.json)核对公开正文、数量和排序。[人工查看](evidence/step-3/visual-review.json)包含六张直接打开的截图及观察。

## 过程中的边界与未采用项

首次内容转换的数量断言发现操作表头被计入数据，输出写入前已阻止；修正为排除表头，正式操作词表为 13 条。没有修改第一步原文。

入口检查首次尝试 file://，被云浏览器以 ERR_BLOCKED_BY_ADMINISTRATOR 拦截；不视为组件功能失败，也不绕过环境限制。首轮记录及脚本在 entrypoints-first.json、verify-entrypoints-first.py.txt 保留，未采用为通过记录。最终入口验证改用已有开发 URL，单文件仍采用本地 HTTP 的 49 项结果。

首次入口脚本异常路径未写出显式 browserClosed 确认；最终脚本已用 finally 显式关闭浏览器与临时 Vite。独立浏览器套件两轮和最终开发入口均记录关闭结果；仅清理本轮启动的服务。

## 范围和保护

主站入口、旧关于我、运镜、庭院、影像与 Coding 代码保持原样。前两步 252 项文件和 97 项生产输入逐项核对；原已跟踪文件与暂存区无差异。新增文件仅为独立组件、开发入口和本步文档/证据，没有增加依赖，没有提交、推送或部署。

限制：手机为浏览器视口和触摸模拟，并非真机；仅 Chromium，尚未做 WebKit/Firefox 全站回归；背景是固定封面。真实相机、石柱锚点、导览中断、3D 材质、飞行、横向自动展示、惯性与鼠标倾斜不属于本步通过范围。普通卡片及标识仍为尺寸占位。
'''
(DOC/'step-3-verification.md').write_text(verification)
handoff=f'''# 关于我改版 · 第三步交接

状态：第三步完成。时间 {now}（Asia/Shanghai）。正式静态组件可用，独立预览验证通过；个人网站当前仍显示原版关于我，尚未接入这些组件。未提交、推送或部署。

[预览](step-3-preview.html) · [接口与实现](step-3-implementation.md) · [验收](step-3-verification.md)

## 第四步可直接使用

- src/tour/about-refresh/createAboutView.ts：挂载三屏、切换屏幕、测量、捕获/恢复状态与销毁。
- content.ts：正式正文、22 个 ID、两套排序及四个首批标记。新页面不应再维护第二份工具文案。
- types.ts：AboutSnapshot、ToolBrowserSnapshot、CardsSnapshot 与 TrackPosition。
- 局部 CSS 与真实控件：分类、前后、原生次级阅读、详情、全量、焦点恢复。

## 第四步需要实际完成

1. 将新组件接入真实阅读宿主，替换旧关于我呈现；完成后移除重复旧内容，不能同时渲染两套介绍。
2. A1/A2 使用窄阅读空间，A3 使用独立宽区域；不把宽卡牌塞进现有共享 420px 面板。
3. 按真实镜头和石柱锚点放置三屏，保持 A1/A2/A3 的现有章节身份；本步未改 scroll station 数值。
4. 重新校准真实主站的标题、导航、底部控件及卡牌空间；只测当前屏幕，隐藏屏不撑大容量。
5. 使用 setLayout/measure 与实际根字号判断阅读模式，更新 data-large-text；展开过高时稳定阅读，并保存位置和焦点。
6. 注入 onInteraction、onLayoutChange、onContinue，接通导览中断、容量刷新和“继续浏览 AI 影像”。恢复状态不能被当成新的手动输入。
7. 检查进入/离开关于我、窗口变化与生命周期；保护现有影像、Coding 嵌入网页及其资源释放。

预览专属的工具栏、背景、window.__aboutRefreshPreview、窗口监听和容量演示不进入主站。生产只导入 createAboutView 及其正式依赖，不导入 preview.ts，也不整页复制 HTML。

## 后续动效仍按原 14 步推进

| 步骤 | 本步提供 | 尚需完成 |
|---|---|---|
| 5 | 普通/详情尺寸、文字层级、局部样式 | 正侧背面、厚度、材质与受光 |
| 6 | 四个首批固定 ID；其余 18 张共用数据 | 真正四张三维飞入 |
| 7 | 默认轨道顺序、局部横向空间 | 浅弧轨道与自动展示 |
| 8 | 局部浏览区、原生滚轮不被拦截 | 输入归属、速度、反向与惯性 |
| 9 | 静态放大与边缘完整阅读位置 | 悬停抬起、跟随鼠标倾斜、真实投影余量 |
| 10 | 完整详情及原生按钮状态 | 正式牌面展开、悬停/点按关系 |
| 11 | 可恢复的分类、卡片与阅读状态 | 三维飞离、折返与中断 |
| 12 | 原操作词表、实际按钮及可达名称 | 功能齐备后的统一提示与布局 |
| 13 | 字号/小屏规则、状态恢复与销毁接口 | 全站适配、真实输入和导览协作 |
| 14 | 同版 49 项记录、内容与保护证据 | 完整主站集成验收 |

全部列表不受当前分类限制；返回保留分类、详情、锚点和焦点。顺序区分默认推荐与类内顺序。没有作品字段、按钮或跳转。卡片自动展示与主站自动导览仍是不同系统。

## 本步验证和复现

类型检查及现有项目构建通过；49 项同版浏览器检查通过，开发入口往返另行通过。npm run dev 后访问 /dev/about-refresh/index.html。独立单文件用本地 HTTP 验证，未验证 file:// 双击运行。

检查脚本为 evidence/step-3/verify-browser.py，每次指定新的 --run 名称，保留原记录；不要覆盖前两步或首次记录。第四步接入后需要重新验收真实主站，不能把独立预览通过等同于主站已完成。
'''
(DOC/'step-3-handoff.md').write_text(handoff)
(OUT/'final-summary.json').write_text(json.dumps({'completedAtShanghai':now,'complete':True,'stage':3,'checks':49,'developmentEntryChecks':1,'standards':[{'id':id,'status':'通过（本步范围）'} for id,_,_ in criteria],'previewSHA256':r['htmlSHA256'],'productionIntegration':False,'sourceFiles':b['sources'],'buildExitCode':0,'committed':False,'pushed':False,'deployed':False,'physicalDevicesTested':False,'directFileNavigationVerified':False},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'documentsWritten':3,'adoptedChecks':49,'developmentEntryChecks':1,'stage':3},ensure_ascii=False))
