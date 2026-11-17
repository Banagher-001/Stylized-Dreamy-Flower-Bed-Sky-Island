"""Publish layout specifications and accurately scoped final review results."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib,json,subprocess

ROOT=Path(__file__).resolve().parents[4]
DOC=ROOT/'docs/about-refresh'
OUT=Path(__file__).parent
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
row=lambda p:{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)}
b=read(OUT/'baseline.json');r=read(OUT/'final-matrix/browser.json');visual=read(OUT/'visual-review.json')
assert r['complete'] and len(r['checks'])==42 and all(c['status']=='通过' for c in r['checks']) and visual['complete']
assert visual['htmlSHA256']==r['htmlSHA256']
assert r['htmlSHA256']==sha(DOC/'step-2-layout-preview.html')
assert all(row(ROOT/f['path'])==f for f in b['step1Files']+b['productionInputs'])
assert not subprocess.check_output(['git','diff','--name-only'],text=True).strip()
assert not subprocess.check_output(['git','diff','--cached','--name-only'],text=True).strip()
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==b['head']
measures={c['id']:read(OUT/'final-matrix'/c['measurement'])for c in r['checks']}
desktop=measures['desktop-A3'];detail=measures['desktop-detail'];selected=next(c for c in detail['cards']if c['expanded'])
mobile=measures['phone-A3'];narrow=measures['narrow-A3'];now=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
matrix_names=[('large','1920×1080'),('desktop','1440×900'),('laptop','1366×768'),('short-laptop','1280×720'),('tablet-landscape','1024×768'),('tablet-portrait','820×1180'),('phone','390×844'),('narrow','320×740'),('short-landscape','844×390')]
matrix='\n'.join('| '+label+' | '+' | '.join('沉浸'if measures[name+'-'+screen]['layout']=='immersive'else'稳定阅读'for screen in['A1','A2','A3'])+' |'for name,label in matrix_names)
spec=f'''# 第二步：三屏整体布局与空间规范

状态：已完成独立静态排版稿和布局核对。时间 {now}（Asia/Shanghai）。以第一步四份原文档为输入，未改写它们，未接入生产网页。

[打开独立预览](step-2-layout-preview.html) · [实际验收](step-2-verification.md) · [后续交接](step-2-handoff.md)

## 画面与信息层级

| 界面 | 默认阅读 | 次级阅读 | 主要布局 |
|---|---|---|---|
| A1 身份 | 姓名、定位、两句简介、三个关键词 | 化名来源 | 桌面石柱旁窄阅读区；小屏顺序阅读 |
| A2 经历与能力 | 三条经历、四个制作环节 | 环节解释、教育背景 | 标签与主体分栏；长职责自然换行 |
| A3 工具与方法 | 标题、介绍、分类、卡牌与操作 | 详情、全部工具 | 宽卡牌区；上下留出控件与退出入口 |

使用真实正文，身份两句简介仍为 50 汉字，22 张卡片为 21 工具与 1 能力。没有新增履历、项目、奖项、业绩或作品跳转。

背景使用现有 courtyard-orb-cover.webp 的原字节，内嵌进 HTML；它是固定背景参照，不代表第 4 步的真实运镜/石柱投影已经接入。没有复制简历的黑白设计风格。

## 可用区域与字号

坐标均为 CSS 像素。预览顶部额外的审阅工具栏、模拟全站导航和底部状态栏都实际扣除；本稿包含审阅栏，因此不是生产页面的最终可用空间测量。布局稿不把窗口宽高直接当正文区。

以 1440×900 为例：审阅栏高 {desktop['review']['height']:.1f}，模拟导航高 {desktop['header']['height']:.1f}，正文区域 y={desktop['stage']['y']:.1f}、高 {desktop['stage']['height']:.1f}；底栏 y={desktop['footer']['y']:.1f}。标题、轨道、操作与继续入口均在该区域中。

正文沿用站点的衬线/系统无衬线方向。实际正文至少 16px，桌面介绍为 18px；辅助文字与标签约 14px。主要触摸/按钮区域至少 44px 高。字体使用 rem，并用实际根字号 32px 检查 200% 大字，没有通过缩小文字强行塞入。

主色为草木绿、浅米白与水蓝。A1/A2 深绿阅读底使用完整透明边缘的羽化，浅色正文清楚；稳定阅读转为浅底深字。A3 标题与操作带采用局部浅色底，保持深浅背景上的辨识度，不给整个场景覆盖一块深色面板。

## A1 / 身份布局

桌面阅读区上限 30rem，即普通字号时 480px。姓名形成主视觉，中文姓名以较小字号合并呈现，定位紧随；两句介绍分段，关键词轻量排列。化名来源以原生展开区域承载。

默认主体与固定导航、底栏保持间隔；小屏改为浅底顺序阅读。展开后若高度不足，使用完整稳定阅读，不裁切介绍。

## A2 / 经历与能力布局

三条经历分别使用“现在、此前、工作室实践”标签，不增加日期。公司/工作室名称突出，职责可换行。四个制作环节在桌面横向排列，窄屏变两列；完整说明和教育信息位于展开区。

完整展开超过可用高度时采用稳定阅读。这是明确的阅读方式，而不是通过降低字号维持沉浸。原生 Enter 可以打开和关闭说明；主站正式接入时还须处理阅读锚点和焦点恢复。

## A3 / 宽幅卡牌区

结构顺序：标题/介绍 → 分类与全部入口 → 卡牌空间 → 前后/自动展示/使用提示 → 明确的继续阅读区。

桌面主体宽上限 1080px；大屏上限 1100px。普通占位实际为 {desktop['cards'][0]['rect']['width']:.0f}×{desktop['cards'][0]['rect']['height']:.0f}；1920 宽时为 240×300。轨道左侧留 44px，卡位间隔 24px。1440 宽实际轨道宽 {desktop['rail']['width']:.1f}，呈现前三张完整加第四张局部，未重复创建首批内容。

首批仍为 Midjourney → ComfyUI → 可灵 → Blender；全量 22 张默认按第一步推荐顺序。主动选择分类后再筛选；“全部”是浏览范围，不是第八个分类。

第一步七个分类保持原名。小屏将分类按钮改为明确的选择入口；“查看全部工具”单独进入静态全量网格。从分类进入时先展示全部 22 张，返回时恢复原分类和横向位置。

## 放大、长名称和边缘阅读空间

详情状态在原卡位中心独立占位，不挤动邻卡。桌面静态放大宽高为普通的 115%，本次实际 {selected['rect']['width']:.1f}×{selected['rect']['height']:.1f}；外侧另有 16px 虚线，用于审阅预留范围。对应轨道高度 {detail['rail']['height']:.1f}，正文和标签未重叠，预留框保持在轨道内。

长名称检查组为 Substance 3D Painter、Marvelous Designer、Adobe Illustrator、Unreal Engine。名称允许自然换行，正文不以省略号截断。详情使用原有完整介绍，没有作品按钮。

原本只部分露出的边缘卡片，在静态阅读状态先放进完整可读范围再显示放大占位。正式聚焦动作由第 9 步设计；本步没有实现悬停跟随、倾斜或移动动画。

后续目标仍为左右 ±8°—10°、上下 ±5°—7°，以及原有抬起效果。16px 审阅框只是此时的空间预留，不能代替真实三维透视、阴影和极值倾斜验收；第 5、9、13 步必须用实际卡牌复测，并按需要增加余量。横向裁切与前景阅读层需分别处理，防止边缘牌面被裁掉。

## 响应式实际结果

| 视口 | A1 默认 | A2 默认 | A3 默认 |
|---|---|---|---|
{matrix}

布局依据宽高、根字号、减少动态偏好和实际内容容量决定，不能只认设备名称。稳定阅读允许纵向滚动，仅卡牌带具有局部横向内容；手机至少一张完整并露出下一张。390 宽实际卡宽 {mobile['cards'][0]['rect']['width']:.1f}；320 宽为 {narrow['cards'][0]['rect']['width']:.1f}。

手机详情向下展开，保持完整阅读，不强制桌面缩放比例。200% 大字时标题、分类与操作区改为更适合阅读的排列，标识占位随字号变化。减少动态偏好下使用静态阅读，同一份内容保持完整。

## 辅助文字增补与原型边界

未修改第一步正文。新增结构用词为：全部、按分类浏览、关于这个名字、制作环节与教育背景。第 3、12 步可统一使用。模拟导航中的“浏览设置”只预留原有控件位置，不接通主站。

顶栏的“静态排版、身份 A1/经历 A2/工具 A3、普通/详情放大/长名称/边缘阅读/全部工具、大字 200%、说明”仅用于审阅，不进入正式网页。字母方块是标识尺寸占位，虚线是空间审阅边界，都不是最终卡牌造型。

本稿可切屏、查看静态状态、使用原生展开、前后查看、分类和全量网格，均用于布局审阅。没有飞入/飞离、自动巡游、滚轮加速、惯性、鼠标倾斜或真实主站导览。
'''
(DOC/'step-2-layout-spec.md').write_text(spec)
criteria=[
 ('S2-01','真实内容与删减范围','第一步四文件摘要、content.json 与 HTML 内嵌数据'),
 ('S2-02','三屏主次清楚','A1/A2/A3 默认与展开截图，人工查看'),
 ('S2-03','自然庭院风格与可读性','原背景摘要、局部浅底/羽化阅读区、人工查看'),
 ('S2-04','A1 默认和次级阅读','三屏尺寸矩阵、desktop-identity-expanded'),
 ('S2-05','A2 经历/流程/教育分层','desktop-experience-expanded、phone-experience-expanded'),
 ('S2-06','A3 宽展示和退出区','desktop-A3、phone-A3、narrow-A3'),
 ('S2-07','放大与倾斜预留','desktop-detail、desktop-edge-reading；仅静态边界，真实 3D 后续复测'),
 ('S2-08','长名称、22 张与总览','desktop-long-name、desktop-all-tools、narrow-all-tools、review-controls'),
 ('S2-09','视口/短横/大字安排','9 档默认矩阵、large-text-A1/A2/A3、reduced-motion'),
 ('S2-10','无横向溢出、字与控件可达','每项实际几何；正文 >=16px，控件 >=44px，内容边界与原生控件检查'),
 ('S2-11','独立预览与证据可追溯','同一最终 HTML 摘要、42 项报告、截图、构建与输入记录'),
 ('S2-12','第一步与生产保持原样','第一步 4 文件、97 生产输入、Git 已跟踪/暂存差异与允许文件范围')]
verification=f'''# 第二步：静态布局验收

第二步完成，时间 {now}。采用最终 HTML 的 42 项 Chromium 静态排版/审阅检查，全部通过。主站未改变，没有把本稿算作三维卡牌或主站兼容性验收。

## 测试对象

HTML：step-2-layout-preview.html。SHA256：{r['htmlSHA256']}。

浏览器 Chromium {r['version']}，Linux 无头模式、DPR1。手机为视口模拟；大字使用实际根字号 32px，减少动态通过真实浏览器偏好。不是系统缩放或真机测试。预览通过只服务该独立 HTML 的本机 HTTP 运行，背景与内容均内嵌，没有外部运行请求、pageerror 或 console.error。

生产代码未变，本步没有重新运行主站构建、三维性能或三个 Coding 体验回归；原版本与第一步保护通过文件摘要和 Git 差异核对。

## 执行标准

| 编号 | 要求 | 实际证据 | 结论 |
|---|---|---|---|
'''
verification+='\n'.join('| '+id+' | '+label+' | '+evidence+' | 通过（按本步范围） |'for id,label,evidence in criteria)
verification+='''

## 最终采用记录

[final-matrix/browser.json](evidence/step-2/final-matrix/browser.json) 包含全部 42 项，逐项链接同目录 measurement.json 和 PNG。所有采用记录的 HTML 摘要与当前预览一致，没有拼接旧版通过项。

九档视口均检查 A1/A2/A3，共 27 项；另外 15 项覆盖身份/经历展开、详情、长名、边缘、全量、手机与窄屏详情、200% 大字、减少动态和预览原生控件。

默认三张完整加第四张局部通过实际交集比例核对；放大状态核对牌面正文、标签以及外侧 16px 预留，不将装饰伪元素的 scrollSize 当成正文裁切。没有放宽正文大小或删减文字来通过。

原生控件检查实际点按前后、查看全部、分类并返回；原分类与横向位置恢复，分类状态进入全部时为 22 张。原生 Enter 打开与关闭简介说明。

## 首次记录与调整

- smoke-1：正文预留虚线被原检查误算成容器溢出；实际文字未裁切。改为测量真实子内容边界，保留装饰 scrollSize 和独立预留框检查。
- smoke-1：A2 展开采用稳定阅读符合设计，最初脚本误要求继续沉浸；修正期待，仍检查全部文字和空间。
- 初次人工查看：A3 标题/提示在深色树影上辨识度不足；仅为预览添加局部浅底，保持场景可见。
- matrix-1：200% 大字标题与标识空间不足，已改为随根字号伸展并调整行高、标题和操作排列；分类进入全部仅有 3 张，已改为全量 22 张，返回恢复原分类。
- smoke-2、targeted-fixes 保留过程复测；最终统一采用 final-matrix 的同版 42 项，不把旧首次报告改成通过。

首次失败、脚本快照、测量、截图和 HTML 摘要均保留。[人工查看记录](evidence/step-2/visual-review.json)。

## 保护和清理

当前分支/提交保持原样；第一步 4 文件和 97 项生产输入逐项一致；Git 已跟踪与暂存差异为空。本步只新增布局稿、规范、验收、交接及 evidence/step-2 下的资料。没有提交、推送、部署或改写旧归档。

每轮独立预览服务器和浏览器由本轮脚本关闭，结果在各 browser.json.cleanup 中；没有停止其他服务。复现时为 review.py 指定新 run 名，避免覆盖已保存记录。

限制：固定背景仅供构图参考；模拟导航并未接通主站；字母标识与卡面是尺寸占位。真实石柱锚点、镜头、3D 材质与飞行、鼠标倾斜、滚轮惯性、真实手机/系统字体和主站全浏览器回归分别由后续步骤处理。
'''
(DOC/'step-2-verification.md').write_text(verification)
handoff=f'''# 第二步完成交接

第二步已完成：三屏静态布局、响应式安排、放大/详情预留及独立预览。时间 {now}。当前生产提交仍为 {b['head']}，第一步四份内容原样保留。本步没有接入主站、提交 Git 或推送 GitHub。

## 可审阅交付

- [独立排版预览](step-2-layout-preview.html)：单文件，背景和 22 张真实内容均内嵌；可切 A1/A2/A3、详情、长名称、边缘、全部和大字。
- [布局规范](step-2-layout-spec.md)：区域、尺寸、默认/展开、分类与辅助标签、响应式规则。
- [实际验收](step-2-verification.md)：12 项标准与最终 42 项静态检查。
- [最终原始记录](evidence/step-2/final-matrix/browser.json)；同目录有实际截图和逐项几何数据。

## 进入后续步骤时保持

三屏仍对应 A1/A2/A3。A1/A2 是窄文字阅读区，A3 是独立宽卡牌区，不把 22 张塞入现有共享 420px 容器。未显示屏不参与当前区域尺寸，沉浸资格应对每站实际占位采样，不能让隐藏 A3 的宽高误撑 A1/A2。

仍是 7 类、21 工具加 1 能力，全部仅是浏览范围。首批为 Midjourney → ComfyUI → 可灵 → Blender。没有项目、奖项、业绩、作品字段或跳转。

## 逐步交接

| 后续步骤 | 本步可用输入 | 留给该步的工作 |
|---|---|---|
| 第 3 步 | content.json、第一步固定 ID、分类/顺序和静态区域 | 建立正式内容结构与静态浏览基础；不整页复制原型全局 CSS |
| 第 4 步 | A1/A2/A3 不同容器与容量规则、展开时稳定阅读安排 | 绑定真实锚点/镜头与站点生命周期；核对全站控件、焦点和阅读位置 |
| 第 5 步 | 普通牌面 232—240×300、文字层级、详情包围范围 | 真正石质卡牌的正侧背面、厚度、材质与受光；字母块不是标识成品 |
| 第 6 步 | 初始四张与轨道可用区域 | 四张三维入场；其余 18 张不参加首轮集中飞入 |
| 第 7 步 | 三张完整加局部的桌面布局、手机一张加局部 | 浅弧轨道与真正自动巡游，原型直排不是最终轨道 |
| 第 8 步 | 展示带与外部阅读区的边界 | 滚轮速度、反向与惯性，未在原型实现 |
| 第 9 步 | 桌面 115% 静态占位、边缘完整阅读位置和 16px 审阅余量 | 真正悬停与倾斜，用真实投影复测余量，必要时增大 |
| 第 10 步 | 原文完整详情、标签和长名称实测 | 正式牌面内容展开，维持可读性与邻卡稳定 |
| 第 11 步 | 区域与继续入口、前景与横向裁切分工 | 真正飞离、停留、折返；本稿没有离场动画 |
| 第 12 步 | 现有操作词表与新增结构标签清单 | 正式提示与控件，去掉审阅工具栏与示意说明 |
| 第 13 步 | 小屏/短横/大字/减少动态的稳定阅读规则 | 真实输入归属、主站导览中断、锚点恢复和设备适配 |
| 第 14 步 | 本步规范、42 项记录与来源 | 对真实完整网页进行集成验收，不能沿用静态稿替代动态功能检查 |

现有源码涉及 src/tour/createPillarReader.ts、tour.css、createReadingLayout.ts 与 startTourPrototype.ts 的共享容器与容量观察，仅作后续接入位置提示，本步没有修改。原型中的全局 html/body、选择器和审阅状态只用于独立页面；正式接入应放在组件作用域，保留原场景与现有 Coding 嵌入网页的生命周期。

## 内容与状态的注意点

A2 展开过高时完整稳定阅读，后续接入要保存焦点和阅读位置。全部工具入口必须解除分类限制以展示 22 张，再在返回时恢复进入前的分类与横向位置。手机详情向下展开，大字不强行维持桌面比例。

背景是原有固定图，未证明相机已经把第一根石柱放到左后方；这是第 4 步的工作。16px 虚线不是极值倾斜或真实阴影证明。自动展示按钮只演示控件状态，继续阅读按钮只显示位置，模拟导航不跳转主站。正式功能按后续对应步骤落实。

允许的制作辅助新增用词：全部、按分类浏览、关于这个名字、制作环节与教育背景。第一步职业正文、工具用途与介绍均未改动。
'''
(DOC/'step-2-handoff.md').write_text(handoff)
save=lambda p,obj:p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
save(OUT/'final-summary.json',{'completedAtShanghai':now,'complete':True,'stage':2,'scope':'Isolated static layout; production website unchanged','html':row(DOC/'step-2-layout-preview.html'),'adoptedRun':'final-matrix','checks':42,'engine':r['engine'],'version':r['version'],'standards':[{'id':id,'status':'通过（静态范围）','evidence':e}for id,_,e in criteria],'step1FilesVerified':4,'productionInputsVerified':97,'trackedFilesUnchanged':True,'committed':False,'pushed':False,'deployed':False,'real3DImplemented':False,'physicalDeviceTested':False})
print(json.dumps({'documentsWritten':3,'finalChecks':42,'productionChanged':False},ensure_ascii=False))
