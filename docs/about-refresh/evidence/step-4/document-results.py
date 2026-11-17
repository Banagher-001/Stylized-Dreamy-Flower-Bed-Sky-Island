from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json,hashlib,subprocess
ROOT=Path(__file__).resolve().parents[4];DOC=ROOT/'docs/about-refresh';OUT=Path(__file__).parent
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
main=read(OUT/'accepted-main/browser.json');components=read(OUT/'component-final/browser.json');reg=read(OUT/'accepted-regressions/browser.json');baseline=read(OUT/'baseline.json')
assert main['complete'] and len(main['checks'])==44 and all(c['status']=='通过' for c in main['checks'])
assert components['complete'] and len(components['checks'])==49
assert reg['complete'] and len(reg['checks'])==7 and read(OUT/'build-check.json')['exitCode']==0
for folder in ['accepted-main','accepted-regressions']:
 assert all(sha(ROOT/f['path'])==f['sha256'] for f in read(OUT/folder/'source-manifest.json'))
assert all(sha(ROOT/f['path'])==f['sha256'] for f in read(OUT/'component-build.json')['sources'])
now=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
measure=lambda id:read(OUT/'accepted-main'/f'{id}-measurement.json')
names=[('large','1920×1080'),('desktop','1440×900'),('laptop','1366×768'),('short-laptop','1280×720'),('tablet-landscape','1024×768'),('tablet-portrait','820×1180'),('phone','390×844'),('narrow','320×740'),('short-landscape','844×390')]
matrix='\n'.join('| '+label+' | '+('沉浸浏览' if measure(key+'-A1')['main']['readingMode']=='immersive' else '稳定阅读')+' |' for key,label in names)
about=measure('desktop-A3');guide=read(OUT/'accepted-regressions/automatic-A1-A2-A3-data.json')['actualAutomaticReading']
seconds=' → '.join(g['station']+'（'+f"{float(g['seconds']):.2f}"+' 秒）' for g in guide)
integration=f'''# 关于我改版 · 第四步主站接入

状态：第四步完成。时间 {now}（Asia/Shanghai）。新版三屏已经接入工作区主站。未提交、推送或部署。

[实际验收](step-4-verification.md) · [第五步交接](step-4-handoff.md) · [主站工具屏截图](evidence/step-4/accepted-main/desktop-A3.png)

## 主站行为

第一根柱子的 A1/A2/A3 分别呈现身份、经历与制作能力、工具与方法。第二根柱子的 AI 影像和第三根柱子的交互作品保持原有内容。旧关于我不再渲染；正式数据继续引用 about-refresh/content.ts，没有复制另一份正文。

沉浸浏览沿第一根柱子向下阅读。A1/A2 使用窄阅读区；A3 使用独立宽区域，暂时隐藏重复的主站浮动章节标题，为卡片让出空间。A3 的 viewHeight 从 3.6 调整到 4.8，screenX 从 .34 调整到 .20；沿原有 A2/A3 下滑区间平滑加入宽构图，离开时使用同一个 A3 端点连接 AI 影像。

1440×900 的 A3 实际面板为 {about['bounds']['width']:.0f}×{about['bounds']['height']:.2f} CSS px，处于主站实际导航、标题和底栏之间的安全区。原生前后、分类、详情和全部列表已可操作；卡片正反面、厚度、飞行、自动横移、滚轮加速和指针倾斜尚未实现，按后续步骤制作。

## 组件与主站职责

| 位置 | 实际修改 |
|---|---|
| createPillarReader.ts | 复用 createAboutView；投影、独立宽窄区域、显现节奏、连续阅读、原生工具阅读层和清理 |
| about-refresh/createAboutView.ts | 连续阅读接口、站点节点与工具浏览器重挂载接口 |
| about-refresh/createToolBrowser.ts / types.ts | 全部/卡片模式通知与关闭接口，保留原有状态结构 |
| about-refresh/aboutRefresh.css | 手机原生横向停稳对齐，便于完整阅读 |
| about-refresh/host.css | 主站局部定位、显现、阅读层、稳定阅读浅绿纸底 |
| createReadingLayout.ts | 仅识别真实站点，并提供内容变化后的重新测量 |
| readerFlow.ts / readingLayout.css | 限定旧章节规则，工具卡不会被当成章节或覆盖其布局 |
| startTourPrototype.ts | 真实回调、阅读层协调、导览就绪与可见阅读文字、逐站独立测量 |
| route.ts / reading.ts / autoGuide.ts | 连续 A3 构图、正文来源说明与工具站导览名称；原章节身份与导览最短时长不变 |
| birdVisibility.ts | 原鸟群避让识别新的关于我阅读外壳 |

主站没有导入 preview.ts、预览工具栏或固定庭院背景。主站使用原有实时场景、相机和渲染器；正式路径中没有 window.__aboutRefreshPreview。没有增加依赖或修改嵌入网页内部代码。

## 两种阅读模式

沉浸模式只显示当前站点；稳定阅读中同一组节点连续呈现 A1/A2/A3。真实章节锚点仅为 opening、A1—A3、B1—B4、C1—C3、water、ending；工具卡不拥有章节锚点。

稳定阅读为新版关于我区域使用局部浅绿纸底，保证分类提示和深绿文字对比清楚；没有重设其他章节的背景。手机横滑由浏览器原生滚动和对齐完成，本步没有加入自定义速度或惯性模型。

真实主站默认结果：

| 视口 | 默认阅读模式 |
|---|---|
{matrix}

主站比独立预览拥有更多控件，以主站真实测量为准。展开后过高、200% 大字、减少动态或图形不可用时采用稳定阅读，完整内容和阅读位置保留；不自动强行切回沉浸。

## 全部工具阅读层

沉浸浏览从任何分类进入全部，使用原生 dialog 阅读层，并把同一个工具浏览器节点移入其中；没有复制第二份 22 张正文。背景滚动和相机暂停，列表可以纵向阅读。返回或 Esc 关闭后，工具浏览器移回 A3，分类、活动卡片、详情、横向位置和入口焦点恢复，滚动限制解除。

稳定模式中，全部列表在 A3 正常展开。窗口在阅读层打开期间缩到手机尺寸，也能关闭并进入完整稳定阅读。阅读层与既有作品查看器使用同一宿主遮罩协调，用户操作始终停止导览。

## 自动导览与测量

正文显现、相机到位且空间可读后才开始停留。A3 的阅读文字由标题和完整进入视野的卡片组成，不把轨道外 18 张及隐藏详情全部计入。完整原时长观察结果：{seconds}。自动经过三站后主动停止，未改时钟、RAF 或生产导览速度。

分类、前后、详情、次级阅读和全部工具操作均可中断导览；关闭阅读层或结束操作后不自动续播。“继续浏览 AI 影像”在沉浸模式定位 B1，在稳定阅读模式定位对应章节。

空间测量按被测站点独立设置其标题处理，完成后恢复当前站点与主站呈现状态，避免当前 A3 的标题隐藏影响 A1/A2 的测量。测量不重置工具分类、详情或横向位置，也不作为用户输入。

## 验证与边界

最终同版主站 44 项通过；当前组件 49 项通过；主站与原作品/动效 7 项回归通过。类型检查和生产构建通过。手机为 Chromium 视口及触摸模拟，尚未做真机、WebKit/Firefox 全站验收。

工作区运行 npm run dev 即可查看接入后的主站；第三步独立开发入口仍保留。历史前三步文档、预览及证据共 404 项原样保留。没有上传 GitHub、部署、改写旧交付包或替换原嵌入网页。
'''
(DOC/'step-4-integration.md').write_text(integration)
criteria=[('S4-01','主站显示新版且无重复旧介绍','主站根节点、三屏正文与旧面板数量'),('S4-02','第一根柱子的三个阅读位置','A1/A2/A3 完整截图、真实相机状态'),('S4-03','连续正反和跨章节运镜','camera-reversal，原生滚轮与章节导航'),('S4-04','宽展示与主站控件安全空间','九档实际边界与安全区；桌面三张完整及局部展示'),('S4-05','工具卡不是章节锚点','13 个真实锚点有序且工具卡锚点数为 0'),('S4-06','连续稳定阅读','手机、短横、大字与减少动态，三屏可读且无 inert'),('S4-07','展开和模式切换保留状态','card-detail、experience-expanded、reading-mode-roundtrip'),('S4-08','全部 22 张及关闭恢复','overview-return/escape/offset/resize，跨手机尺寸关闭与焦点恢复'),('S4-09','导览就绪与人工接管','guide-interrupt，真实 A1→A2→A3 自动运行'),('S4-10','真实下一章节','continue-immersive/continue-stable 到达 B1'),('S4-11','原场景与作品功能','影像、罗森、瓶中海洋、环境播放暂停恢复共用主站回归'),('S4-12','构建、保护与归档','build-check.json、原有 404 项交付、允许源码变更与清理记录')]
verification=f'''# 关于我改版 · 第四步验收

第四步完成，时间 {now}（Asia/Shanghai）。采用最终构建的 44 项主站接入检查、49 项组件检查、7 项主站与作品回归，全部通过。类型检查和生产构建退出码 0。没有推送或部署。

[主站接入说明](step-4-integration.md) · [后续交接](step-4-handoff.md)

## 执行标准

| 编号 | 标准 | 实际证据 | 结论 |
|---|---|---|---|
'''+ '\n'.join('| '+id+' | '+name+' | '+e+' | 通过（本步范围） |' for id,name,e in criteria)+'''

## 采用记录

- [accepted-main/browser.json](evidence/step-4/accepted-main/browser.json)：最终构建 44 项；27 项九档三屏，加 17 项展开、阅读层、恢复、模式、导览、反向运镜与图形回退等检查。
- [component-final/browser.json](evidence/step-4/component-final/browser.json)：49 项原组件功能与排版检查；使用本步组件另建预览，没有改写第三步归档。
- [accepted-regressions/browser.json](evidence/step-4/accepted-regressions/browser.json)：原生滚轮、跨手机尺寸关闭阅读层、影像打开返回、罗森时间滑杆、瓶中海洋暂停按钮、环境播放/暂停/恢复、原时长三站自动导览。
- [build-check.json](evidence/step-4/build-check.json)：npm run build 含类型检查，实际输出在对应文本文件。

主站和回归记录各保存源文件、构建 HTML/主入口资源摘要；组件记录保存内嵌预览摘要和对应源码摘要。采用项与最终代码一致，没有拿不同版本的通过项拼成结论。

正常场景没有 pageerror 或 console.error；图形不可用用例主动让 WebGL 创建失败，其预期错误单列，验证完整稳定阅读仍可用。九档视口是模拟尺寸；手机原生触摸通过 CDP 实际输入，非真机。自动导览没有改时钟、缩短停留或替换 RAF。

## 过程记录和修正

1. 首轮主站检查把主站当前阅读位置的数据标记误计为章节锚点。检查范围改为阅读文档内部，保留首轮记录；正式章节仍为 13 个，工具卡为 0。
2. 手机原生横滑可能停在两张卡片之间，补充原生对齐；触摸检查等待真实 scrollend 后验收，避免把仍在移动的瞬间当作停稳。
3. 瓶中海洋首轮检查误读后处理末次绘制的三角形数；改为原网页 getDiagnostics().renderer.triangles，并完成原生暂停按钮及关闭返回验证。原网页没有修改。
4. 人工查看发现原稳定阅读深色背景使分类提示对比不足，仅为新版关于我补充浅绿纸底，随后复测最终构建。
5. 完整自动导览发现 A3 的共享标题隐藏状态影响 A1/A2 探测，触发不必要的导览停止。修正为逐站独立呈现后测量，最后恢复原状态；先做原时长专项复测，再重新执行最终主站和回归检查。

smoke、matrix、regressions 和专项目录保留过程结果，未覆盖首次失败。早期专项复测仅用于定位，不用于最终源码一致性结论；采用结果只使用上列三份报告。

## 保护与清理

前三步 404 项文件逐项保留；允许的主站和组件文件修改已记录，其他已跟踪文件、嵌入网页、资产、依赖和配置没有改动。未暂存、提交、推送或部署。当前源码的正文仍取自第三步固定 content.ts。

所有浏览器由各检查脚本关闭；本轮静态预览服务与私有图形显示由 services.py 管理并关闭，只处理本轮记录的进程组。详见 services-cleanup.json 与最终保护记录。

## 限制

卡牌目前是静态实体尺寸占位，尚无最终正侧背面、厚度、三维入场/离场、自动横移、自定义滚轮惯性或指针倾斜；这些属于第五步及后续步骤。没有把本步接入验收算作第十四步的全站最终验收。没有验证 file:// 双击运行主站。
'''
(DOC/'step-4-verification.md').write_text(verification)
handoff=f'''# 关于我改版 · 第四步交接

状态：第四步完成，{now}（Asia/Shanghai）。新版关于我已接入工作区主站；本次修改尚未上传 GitHub，未提交、推送或部署。

[接入说明](step-4-integration.md) · [验收](step-4-verification.md) · [工具屏实际画面](evidence/step-4/accepted-main/desktop-A3.png)

## 第五步可以直接使用

- src/tour/about-refresh/content.ts：同一份 22 张正文、唯一 ID、分类与两套顺序。
- createAboutView / createToolBrowser：真实控件、连续阅读、状态恢复、工具阅读层挂载和关闭接口。
- createPillarReader：真实投影与宽窄区域、基础显现、稳定阅读、原生 dialog 和宿主协调。
- .ar-tool-slot / .ar-tool-card：普通、静态展开和占位结构，桌面普通宽 232—240、高至少 300，静态展开宽 115%；真实高度可随文字增加。

## 第五步范围

下一步制作符合庭院风格的卡牌实体：正面、背面、侧边、厚度、材质、受光、标识与文字层级。不得把当前字母方块或平面投影当作最终标识与三维材质。

本步已占据真实主站空间。实体厚度、透视、阴影加入后需要复测放大卡片和边缘卡片的真实包围范围，按需增加余量；不能直接沿用平面 115% 尺寸当成最终极值证明。飞入、轨道、滚轮、悬停、详情、飞离仍分别归属第 6—11 步。

## 必须保留的行为

1. A1/A2/A3 仍属于第一根柱子的三个站点；A3 宽构图与离开端点共用，避免镜头跳变。
2. 真正的章节元素拥有 data-flow-anchor，卡片不拥有章节锚点。旧章节通用样式只作用于原影像/交互站点。
3. 沉浸模式只显示当前站，稳定模式使用相同节点连续显示全部三屏；稳定阅读当前章节以主站 flow-anchor 为准。
4. 全部工具在沉浸模式中使用原生阅读层，移动同一工具浏览器，不复制卡片；稳定模式正常展开。返回保留原分类、卡片、详情、位置与焦点。
5. 系统测量按被测站点设置标题处理并恢复现场，不能触发用户交互、重置内容或令自动导览误停。
6. 手动操作停止主站导览，结束后不自动续播。卡片自动展示尚未启用，以后与主站导览分别管理。
7. 手机原生横滑有停稳对齐。未来第 7、8 步加入自动轨道时，需明确原生对齐与程序移动的启用关系。
8. 鸟群避让识别 about-pillar-reader；修改卡片区域时保留正确的避让与可见区域测量。
9. 正文不增加项目、奖项、业绩或相关作品按钮。现有 AI 影像和 Coding 展示内容继续保留。

## 复测与归档

最终主站 44、组件 49、回归 7 项通过，构建含类型检查通过。过程失败与专项定位记录保留，最终采用目录见验收文档。

前三步文档、预览与证据原样保留；本步修改前的主站和组件快照位于 evidence/step-4/before。后续改动需要新的基线与记录，不能覆盖本步归档。运行 npm run dev 查看当前主站，独立组件开发入口仍为 /dev/about-refresh/index.html。
'''
(DOC/'step-4-handoff.md').write_text(handoff)
(OUT/'final-summary.json').write_text(json.dumps({'complete':True,'completedAtShanghai':now,'stage':4,'productionIntegration':True,'mainChecks':44,'componentChecks':49,'regressionChecks':7,'buildExitCode':0,'standards':[{'id':id,'status':'通过（本步范围）'} for id,_,_ in criteria],'historicalArtifactsPreserved':404,'committed':False,'pushed':False,'deployed':False,'physicalDevicesTested':False,'final3DCardMaterialImplemented':False},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'documentsWritten':3,'mainChecks':44,'componentChecks':49,'regressionChecks':7},ensure_ascii=False))
