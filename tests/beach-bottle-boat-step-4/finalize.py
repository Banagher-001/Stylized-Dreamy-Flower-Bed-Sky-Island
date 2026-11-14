"""Seal observed step-4 results and snapshots, not mutable future product sources."""
import argparse,ast
from common import *
parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
if args.verify_only:
 m=read(OUT/'evidence-manifest.json')
 for f in m['files']:assert row(ROOT/f['path'])==f,f['path']
 print(json.dumps({'sealedFilesVerified':len(m['files']),'historicalSealsVerified':len(history()['seals']),'step4EvidenceIntact':True},ensure_ascii=False));raise SystemExit
assert not(OUT/'evidence-manifest.json').exists();protection=protect_current();baseline=read(OUT/'baseline.json');build=read(OUT/'build.json');cleanup=read(OUT/'services-cleanup.json')
assert build['exitCode']==0 and cleanup['scratchRemoved']and not cleanup['ownedBrowsersRemaining']and all(x['stopped']for x in cleanup['services']);assert len(protection['changedProductionInputs'])==5
assert not Path(baseline['scratch']).exists()
for name in ALLOWED:assert sha(ROOT/name)==sha(OUT/'after'/name)
assert(OUT/'product.diff').read_text()==subprocess.check_output(['git','diff','--',*ALLOWED],cwd=ROOT,text=True)
subprocess.run(['git','diff','--check'],cwd=ROOT,check=True)
runs={name:read(OUT/name/'browser.json')for name in['chromium','firefox','webkit','guide-motion']};adopted=[];observations=[];expectedAborts=[];softwareWarnings=[]
for name,data in runs.items():
 assert data['complete']and not data['externalAttempts']
 assert all(c['status']=='通过'for c in data['checks'])
 normalErrors=[x for x in data['pageErrors']if not x['case'].startswith('FAULT.')]+[x for x in data['console']if x['type']=='error'and not x['case'].startswith('FAULT.')];assert not normalErrors,(name,normalErrors)
 for e in data['failedRequests']:
  if e['case'].startswith('FAULT.'):continue
  assert e['case']=='REGRESS.lawson'and e['url'].endswith(('/car_A.glb','/car_B.glb','/car_C.glb'))and e['failure']=='net::ERR_ABORTED',(name,e)
  expectedAborts.append({'run':name,**e,'interpretation':'Original lazy car-model fetch cancelled when the LAWSON iframe was intentionally closed after ready'})
 softwareWarnings.extend({'run':name,**e}for e in data['console']if e['type']=='warning')
 for i,c in enumerate(data['checks']):adopted.append({'run':name,'engine':data['engine'],'version':data['browserVersion'],'id':c['id'],'status':c['status'],'record':name+'/browser.json#/checks/'+str(i)})
 observations.append({'run':name,'engine':data['engine'],'version':data['browserVersion'],'passed':len(data['checks']),'expectedFaults':[c['id']for c in data['checks']if c['id'].startswith('FAULT.')]})
assert len(adopted)==21
mapping={'S4-01':['baseline.json'],'S4-02':['SELECT.three'],'S4-03':['SELECT.three','LAYOUT.sizes'],'S4-04':['KEYBOARD.cycle'],'S4-05':['FAULT.delayed-cover'],'S4-06':['FAULT.failed-cover','build.json'],'S4-07':['ARCHIVE.prepared'],'S4-08':['ARCHIVE.prepared','REGRESS.lawson'],'S4-09':['OPEN.root'],'S4-10':['OPEN.prefix'],'S4-11':['REGRESS.lawson'],'S4-12':['REGRESS.courtyard-water','FAULT.host-graphics'],'S4-13':['LAYOUT.sizes'],'S4-14':['ARCHIVE.prepared','REGRESS.reading','REGRESS.guide-motion'],'S4-15':['build.json'],'S4-16':['final-summary.json','services-cleanup.json']}
candidate={'capturedAtShanghai':now(),'baseCommit':baseline['hostCommit'],'productionInputsAfter':[row(ROOT/f['path'])for f in baseline['productionInputsBefore']],'authorizedDiff':protection['changedProductionInputs'],'sourceSnapshots':[row(OUT/'after'/name)for name in ALLOWED],'runtimeEntrySHA256':ENTRY_SHA,'coverSourceSHA256':sha(ROOT/'src/assets/bottle-ocean-cover.png'),'builtCover':build['cover'],'buildManifest':build['productionManifest'],'mutableSourcePathsAreRecordedNotHistoricalSealTargets':True}
write(OUT/'candidate-manifest.json',candidate)
write(OUT/'visual-review.json',{'reviewedAtShanghai':now(),'method':'Assistant inspected actual screenshots via view_image','files':[row(OUT/'chromium'/n)for n in['three-works-preview.png','bottle-archive.png','bottle-prepared.png','layout-390x844.png']],'observed':'Three ordered selectors in shared preview; bottle archive has editorial headline and full scene image; prepared panel has independent link; phone archive has readable stacked sections and reachable toolbar. Mobile screenshot is DPR2 and was captured after scrolling to feature sections.','imagesEdited':False})
summary={'completedAtShanghai':now(),'conclusion':'第四步完成：三作品选择、预览、瓶中海洋档案和独立打开入口可用；完整瓶中海洋iframe仍未接通','standardChecks':[{'id':k,'status':'通过','records':v}for k,v in mapping.items()],'adoptedChecks':adopted,'runs':observations,'protection':protection,'cleanup':cleanup,'expectedTeardownAborts':expectedAborts,'softwareWarnings':softwareWarnings,'scope':{'bottleIframeAdded':False,'bottleRuntimeModified':False,'step2Executed':False,'committed':False,'pushed':False,'deployed':False},'limits':['Chromium full step-4 matrix; Firefox/Linux WebKit four representative checks each','390/320 mobile emulation used real touchscreen taps to select bottle-ocean; three-way selection and key cycling exercised on desktop','Font enlargement used test html font-size 200%, not OS/browser zoom or physical-phone accessibility','Original 34-control parity inside a bottle iframe, actual hidden-state recovery and hardware performance belong to later verification'],'sourceEntrySHA256':ENTRY_SHA}
write(OUT/'final-summary.json',summary)
standard=DOC/'step-4-standard.md';text=standard.read_text();a=text.index('状态：');z=text.index('\n',a);text=text[:a]+'状态：第四步已执行完成。三作品选择、真实预览、瓶中海洋档案、准确 prepared 展示和根/子路径独立打开均已验收；结果见 step-4-verification.md。执行前标准另存 standard-before.md。日期：2026-11-13（Asia/Shanghai）。完整瓶中海洋 iframe 仍由第五步接通，未上传或发布。'+text[z:];standard.write_text(text)
lines=['# 第四步验收：三作品选择、瓶中海洋档案与独立打开','','第四步完成。Coding 区按 LAWSON → BOTTLE OCEAN → COURTYARD 排列，默认罗森；瓶中海洋已有真实封面、简介、档案与独立打开入口。主站内显示准确的“可独立体验”准备页，尚未创建瓶中海洋 iframe。未提交、上传或发布。日期：2026-11-13（Asia/Shanghai）。','','实际改动：','','| 文件 | 改动 |','|---|---|','| projectContent.ts | 三作品统一顺序与身份、真实封面导入、档案/准备页元数据、独立网页类型守卫 |','| createExperimentReader.ts | 按统一顺序生成三个索引；左右循环、Home/End 和当前作品动作 |','| createProjectViewer.ts | 独立网页的静态展示与档案按类型处理；准备页内容随作品更新；动态状态带作品 owner |','| projectHost.css | 三列索引、窄屏换行、独立网页宿主布局、瓶中海洋档案与准备页样式 |','| startTourPrototype.ts | 罗森状态更新显式传入 lawson 身份；运行器与原导览/相机机制保持原样 |','','其余 90 项既有生产输入不变，experiment.css 未修改。before/after 快照、实际源文件摘要及完整差异见 [candidate-manifest.json](../evidence/beach-bottle-boat-step-4/candidate-manifest.json) 和 [product.diff](../evidence/beach-bottle-boat-step-4/product.diff)。未来产品源码可按后续授权继续修改，本步封存保存的是独立 after 副本，不把可变源码作为历史封存目标。','','实际验收：','','| 引擎 / 记录 | 检查数 | 范围 |','|---|---:|---|']
for name,data in runs.items():lines.append(f'| {data["engine"]} {data["browserVersion"]} / {name} | {len(data["checks"])} | '+('三作品、键盘、档案、原网页独立打开'if name in['firefox','webkit']else'真实活动导览中断、暂停/播放选择返回'if name=='guide-motion'else'主流程、根/子路径、故障、原作品、阅读与尺寸')+' |')
lines+=['','21 项实际记录全部通过，对应 16 项执行标准：[final-summary.json](../evidence/beach-bottle-boat-step-4/final-summary.json)。本轮未出现待补核或失败复测，没有用旧截图替代新记录。','','- 三项原生点击与方向键循环的标题、封面、摘要、当前项及 aria 归属一致；Home/End、Tab/Shift+Tab、Enter/Space 正常。', '- 档案以“让一片海，托起一艘船。”、真实大图和三组编号功能呈现；原罗森内容及庭院片段仍各自保留。','- 真实图片请求被暂停、切换到庭院后再送达，当前作品保持庭院且图片状态正确；图片请求失败时有反馈，档案和独立入口仍可用，原重试按钮可恢复图片。','- 主站在仅浏览预览、档案或准备页时没有请求瓶中海洋运行 HTML，没有其 iframe。准备页为 prepared、aria-busy=false，无无效重试或假 ready。','- 根路径和实际 /portfolio-check/ 前缀均通过真实链接打开新窗口，当前地址正确，取得原 HTML SHA256，原场景就绪并响应波高和镜头原生操作。三个引擎均实际打开原页。','- 罗森原完整现场实际达到 ready；关闭后转到瓶中海洋，旧 iframe 已移除且 prepared 状态没有被旧回调覆盖。','- 庭院正常/像素按钮与动效切换可用；档案片段由真实点击开始播放，currentTime>0，关闭后视频移除。Coding 当前选瓶中海洋时，水潭入口仍打开 courtyard。','- 测试仅对宿主文档禁用 WebGL 创建，实际触发宿主初始化失败；瓶中海洋准备页/独立链接仍可用，庭院现场按原规则禁用而档案可用。这是明确故障注入，不代表真实 GPU 驱动故障。','- 1920×1080、1440×900、1280×720、390×844、844×390、320×740 以及 html 根字号 200% 条件无页面横向溢出，三项至少 44×44，档案可滚动且返回可见。手机模拟用真实触摸点按选择瓶中海洋；不是物理手机或系统文字放大实测。','- 活动导览由原按钮实际启动，随后手动选择瓶中海洋使其停止；作品返回后不自行继续。主站分别处于暂停和播放时打开/关闭作品，返回保留原选择。关闭档案恢复有效焦点及原阅读位置；开发服务下关于我、AI影像章节实际可读。','','构建、日志与完整性：','','- npm run typecheck 与 npm run build 均成功；新构建 69 个文件，真实封面进入 assets 且与源 PNG 摘要相同。瓶中海洋原 HTML 在 public 和构建产物仍为 941feb2ea6ddd3cc93aad5b0b92dbca52ee66a3e1098fee0dbf16f01ca63d1ef。','- 正常路径没有 pageerror 或 console.error，也没有外部 HTTP 请求尝试。图片故障及宿主 WebGL 禁用产生的日志按 FAULT 场景单列。','- 罗森准备完后主动关闭 iframe，三个延迟车型请求以 net::ERR_ABORTED 取消，这是该次卸载的预期结果；原始记录保留，未归为加载失败。Firefox 的软件 WebGL 深度纹理过滤实现警告有记录，未视作产品脚本异常或硬件兼容证明。','- 原仓库 44 个文件、罗森 46 个运行文件、瓶中海洋 HTML/声明/来源和原封面均不变；8 组既有历史封存及第一、三步封存共 10 组全部校验通过。原 dist 的 65 个文件未覆盖。','- 浏览器均关闭，3 个本步自有服务停止；专用临时构建目录在保存摘要并复核后清理，未停止其他服务。','','画面：[桌面档案](../evidence/beach-bottle-boat-step-4/chromium/bottle-archive.png) · [可独立体验页](../evidence/beach-bottle-boat-step-4/chromium/bottle-prepared.png) · [手机档案](../evidence/beach-bottle-boat-step-4/chromium/layout-390x844.png)。','','范围：本轮主要使用 Linux Chromium 和软件图形环境；Firefox、Linux WebKit 各 4 项代表操作，不是全量原 34 控件复验或真机 Safari。原页亮度、镜头惯性、图形丢失语义未修改；完整 iframe 输入/生命周期、实际 hidden 恢复、真机与硬件性能继续由后续验证。第二步仍仅有标准，未冒充完成其正式交付。','','[第五步交接](step-4-handoff.md)。本步独立封存复核命令：python tests/beach-bottle-boat-step-4/finalize.py --verify-only。此命令核对封存的本步快照及此前历史，不要求未来经授权修改的产品源码仍等于本步候选。','']
(DOC/'step-4-verification.md').write_text('\n'.join(lines))
(DOC/'step-4-handoff.md').write_text('''# 第四步交接：第五步完整瓶中海洋现场

第四步完成三作品入口、封面/简介、档案和准确的 prepared/独立打开流程。当前工作区尚未提交 GitHub 或发布；独立网页原字节不变。本步自有测试服务与临时构建产物已清理，已有 dist 未覆盖。第二步仍仅有已细化标准。

| 已落地接口 | 当前行为 |
|---|---|
| projectOrder / ProjectId | lawson → bottle-ocean → courtyard；统一 DOM 与键盘顺序，默认 lawson |
| projects['bottle-ocean'] | 元数据、真实封面、独立网页体验、档案和准备页内容 |
| isPageProject(item) | 明确区分独立网页与主站庭院的数据形状 |
| resolveProjectEntry(id) | 继续 BASE_URL 相对解析，独立打开和未来 iframe 共用入口 |
| setEmbeddedStatus(owner, state, message?) | 仅接受当前同身份独立网页的状态；现有罗森调用已传 'lawson' |
| dialog.dataset.experienceKind | embedded-page 的大尺寸宿主、档案与准备页布局 |
| 正式入口 | experiments/bottle-ocean/index.html |
| 原 HTML SHA256 | 941feb2ea6ddd3cc93aad5b0b92dbca52ee66a3e1098fee0dbf16f01ca63d1ef |

第五步需完成：

1. 新增/配置瓶中海洋专用原页观察规则，使用当前文档的 __bottleOcean、#gl、加载/错误状态与实际 canvas 图形故障。不能把 iframe load、旧 ready 或仅有 canvas 算就绪。
2. 接通当前项目的现场创建/重试/卸载；startTourPrototype.ts 的 syncLawson、retry、dispose 仍只运行罗森。替换/扩展这些路由时保留 wanted、实例/文档归属与过期回调防护。
3. createProjectViewer.ts 的 refreshEmbeddedFeedback 目前仍限定罗森的动态状态；瓶中海洋目前是 prepared。第五步按当前支持的运行器扩展反馈/重试，真实 ready 后隐藏 prepared，不能让错误按钮暂时无处理。
4. 原 H/Space/Escape、滚轮、拖动、沙盒与真实 PNG 下载保留。一个查看器最多一个活动独立网页；原暂停仍绘制，关闭和去档案必须卸载。
5. 复用主站已验证的覆盖暂停、焦点/阅读恢复和导览停止。实际图形丢失后原 ready 可能仍为真，原错误遮罩可能不可见，重试必须使用可信的新文档边界。

第五步无需重做三作品选择、档案或封面；原网页和 PNG 不重构建、不改默认参数。根路径及真实 /portfolio-check/ 前缀独立打开已通过，后续仍要在实际 iframe 中对照原功能和验证输入/生命周期、主站与罗森回归。

本步证据只针对当前入口/档案和独立原页。手机为浏览器触摸模拟，放大条件为根字号测试；实际 hidden、真机及硬件性能未验证。旧封存与本步 after 副本独立保存，允许后续授权修改当前产品源码而不改写这些历史记录。
''')
for p in TEST.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
for p in(TEST/'__pycache__').glob('*'):p.unlink()
if(TEST/'__pycache__').exists():(TEST/'__pycache__').rmdir()
files=[row(DOC/n)for n in['step-4-standard.md','step-4-verification.md','step-4-handoff.md']]+[row(p)for p in sorted(OUT.rglob('*'))if p.is_file()]+[row(p)for p in sorted(TEST.glob('*.py'))]
assert len(files)==len({f['path']for f in files})
write(OUT/'evidence-manifest.json',{'schema':1,'createdAtShanghai':now(),'scope':'Step-4 docs/scripts/evidence and immutable before/after snapshots; mutable product files are recorded in candidate-manifest, not seal targets','files':sorted(files,key=lambda f:f['path'])})
print(json.dumps({'step4Complete':True,'standardChecksPassed':16,'browserChecksPassed':len(adopted),'authorizedProductFilesChanged':len(protection['changedProductionInputs']),'historicalSealsVerified':len(protection['history']['seals']),'sealedFiles':len(files),'bottleIframeAdded':False,'pushed':False},ensure_ascii=False))
