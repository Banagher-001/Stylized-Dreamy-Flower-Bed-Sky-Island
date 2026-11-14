"""Verify immutable products/history, publish a determinate baseline and seal new evidence."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from collections import Counter
import argparse,ast,hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[2];SOURCE=ROOT.parent/'Beach-Bottle-Boat';OUT=ROOT/'docs/evidence/beach-bottle-boat-step-1';DOC=ROOT/'docs/beach-bottle-boat';TEST=Path(__file__).parent
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def git(p,*args):return subprocess.check_output(['git','-C',str(p),*args],text=True).strip()
def row(p,base=ROOT):return {'path':p.relative_to(base).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)}
def protect():
 baseline=read(OUT/'baseline.json');assert git(ROOT,'rev-parse','HEAD')==baseline['hostCommit'];assert git(SOURCE,'rev-parse','HEAD')==baseline['sourceCommit'];assert git(SOURCE,'status','--short')=='';assert git(ROOT,'diff','--name-only')==''
 current=[row(p,SOURCE)for p in sorted(SOURCE.rglob('*'))if p.is_file()and'.git'not in p.parts];assert current==baseline['originalFiles']
 for f in baseline['hostProductionInputs']:assert row(ROOT/f['path'])==f,f['path']
 for f in baseline['lawsonRuntimeFiles']:
  p=ROOT/'public/experiments/lawson'/f['path'];assert p.stat().st_size==f['bytes']and sha(p)==f['sha256']
 old=[]
 for s in baseline['oldSeals']:
  p=ROOT/s['path'];assert sha(p)==s['sha256'];manifest=read(p);assert len(manifest['files'])==s['fileCount']
  for f in manifest['files']:assert row(ROOT/f['path'])==f,f['path']
  old.append({'path':s['path'],'sha256':s['sha256'],'filesVerified':len(manifest['files'])})
 for p in TEST.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
 return {'sourceFilesVerified':len(current),'sourceClean':True,'hostProductionInputsVerified':len(baseline['hostProductionInputs']),'lawsonRuntimeFilesVerified':len(baseline['lawsonRuntimeFiles']),'oldSealsVerified':old,'sourceEntrySHA256':sha(SOURCE/'index.html'),'trackedHostChanges':git(ROOT,'diff','--name-only'),'sourceCommit':baseline['sourceCommit'],'hostCommit':baseline['hostCommit'],'hostStatus':git(ROOT,'status','--short')}
parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
if args.verify_only:
 manifest=read(OUT/'evidence-manifest.json')
 for f in manifest['files']:assert row(ROOT/f['path'])==f,f['path']
 result=protect();print(json.dumps({'verifiedNewFiles':len(manifest['files']),'productsAndHistory':result},ensure_ascii=False));raise SystemExit
assert not(OUT/'evidence-manifest.json').exists(),'Do not overwrite sealed evidence'
protection=protect();cleanup=read(OUT/'services-cleanup.json');assert cleanup['ownedBrowsersRemaining']==[] and all(x['stopped']for x in cleanup['services'])
selection=[('controls',None),('interactions',{'exclude':['POINTER.scene-picking']}),('interactions-picking-retest',None),('physics',{'exclude':['MOTION.wind']}),('physics-wind-retest',None),('chromium-compat',{'include':['ENGINE.representative']}),('chromium-mobile-file-retest',None),('firefox-compat',None),('webkit-compat',None),('firefox-file',None),('webgl-disabled',None),('failures',{'exclude':['LIFECYCLE.visibility']}),('boundaries',None),('native-tab-visibility',None)]
adopted=[]
for name,filter in selection:
 data=read(OUT/name/'browser.json')
 for i,c in enumerate(data['checks']):
  if filter and c['id']in filter.get('exclude',[]):continue
  if filter and'include'in filter and c['id']not in filter['include']:continue
  assert c['status']!='待补核',(name,c['id']);adopted.append({'engine':data['engine'],'browserVersion':data['browserVersion'],'id':c['id'],'name':c['name'],'status':c['status'],'record':f'{name}/browser.json#/checks/{i}','sourceEntrySHA256':protection['sourceEntrySHA256']})
required={'LOAD.http-cold','LOAD.http-again','UI.default-inventory','VIEW.default-1440','BUTTON.quality','BUTTON.panel','BUTTON.ui-hide-restore','CAMERA.five-presets','CAMERA.pointer-reset','POINTER.scene-picking','KEYBOARD.original','PLAYBACK.freeze-resume','PLAYBACK.full-reset','SANDBOX.real-props','EXPORT.native-download','MOTION.directions','MOTION.boatResponse','MOTION.boatDamping','MOTION.wind','MOTION.strong-water-safety','ENGINE.representative','LOAD.file-cold','VIEW.mobile-touch','FAILURE.webgl-disabled','FAILURE.context-loss-reload','LIFECYCLE.reduced-motion','LIFECYCLE.native-tab-visibility','CAMERA.reset-inertia','SANDBOX.representative-rules','EXPORT.hidden-ui-keyboard'}|{'MOTION.height-'+str(v)for v in[0,50,100]}|{'BUTTON.toggle-'+n for n in['lighthouse','spray','dust']}|{'SLIDER.'+n for n in['waveHeight','waveSpeed','waveDensity','waveDirection','waterLevel','boatResponse','boatDamping','wind','pixelScale','sunset','brightness','glassOpacity']}
assert required.issubset({r['id']for r in adopted});assert {r['engine']for r in adopted if r['id']=='ENGINE.representative'}=={'chromium','firefox','webkit'}
allruns=[]
for p in sorted(OUT.glob('*/browser.json')):
 data=read(p);assert not data['externalAttempts'];normalErrors=[x for x in data['events']if x.get('kind')=='pageerror'or x.get('level')=='error']
 if p.parent.name!='webgl-disabled':assert not normalErrors,(p,normalErrors)
 allruns.append({'run':p.parent.name,'rawComplete':data.get('complete',False),'rawStatuses':dict(Counter(c['status']for c in data['checks'])),'externalAttempts':len(data['externalAttempts']),'expectedFaultInjectionConsoleErrors':len(normalErrors)if p.parent.name=='webgl-disabled'else 0})
counts=dict(Counter(r['status']for r in adopted));summary={'completedAtShanghai':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'conclusion':'第一步独立原版基线完成，含原有问题及明确的环境限制；不表示全部兼容路径通过或主站接入完成','adoptedCounts':counts,'adoptedCases':adopted,'rawRuns':allruns,'protection':protection,'scope':{'originalRebuilt':False,'productModified':False,'codingIntegrated':False,'committed':False,'pushed':False,'deployed':False},'remainingBoundaries':['Managed Chromium file URL policy; Firefox file load passed','No actual hidden state observed; background resume/throttling not validated','Physical devices, non-Linux platforms and hardware performance unverified','All terrain pixels, prop cap, all parameter combinations and actual cavity rejection hit not exhaustively tested','Host iframe isolation, lifecycle and regression belong to later steps']}
(OUT/'final-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
# Explicitly count DOM controls, rather than treating grouped test cases as controls.
data=read(OUT/'controls/browser.json');inventory=next(c for c in data['checks']if c['id']=='UI.default-inventory')['evidence'];controls=inventory['controls'];assert len(controls)==34
def mapping(c):
 d=c['data'];tag=c['tag'];id=c['id']
 if tag=='INPUT':return 'SLIDER.'+id,'原页已有问题（默认读数）；输入通过'if id=='brightness'else'通过'
 if'quality'in d:return 'BUTTON.quality','通过'
 if'toggle'in d:return 'BUTTON.toggle-'+d['toggle'],'通过'
 if'preset'in d:return 'CAMERA.five-presets','通过'
 if'edit'in d:return 'SANDBOX.real-props','通过'
 action=d['action'];ids={'togglePanel':'BUTTON.panel','toggleUI':'BUTTON.ui-hide-restore','undoProp':'SANDBOX.real-props','resetProps':'SANDBOX.real-props','pause':'PLAYBACK.freeze-resume','reset':'PLAYBACK.full-reset','resetCamera':'CAMERA.pointer-reset / CAMERA.reset-inertia','screenshot':'EXPORT.native-download'}
 return ids[action],'原页已有问题（残余惯性）；操作通过'if action=='resetCamera'else'通过'
lines=['# 第一步：34 个原控件与操作基线','','原生输入后核对原状态、场景对象、相机、连续模拟或实际下载。主功能在 Chromium 独立 HTTP 页面验证；完整逐项记录见 [验收报告](step-1-verification.md) 和 [机器汇总](../evidence/beach-bottle-boat-step-1/final-summary.json)。','','12 个滑杆与 22 个按钮共 34 个 DOM 控件。下表每行对应一个控件；分组测试 ID 可覆盖多个同类按钮，不重复计算为新控件。','','| 控件 ID | DOM / 原功能 | 实际对应记录 | 判定 |','|---|---|---|---|']
for i,c in enumerate(controls,1):
 test,status=mapping(c);identity='#'+c['id']if c['id']else', '.join(k+'='+str(v)for k,v in c['data'].items());label=(c['text']or c['title']or c['id']).replace('|','/').replace('\n',' ');lines.append(f'| CTL-{i:02d} | {identity} · {label} | {test} | {status} |')
lines+=['','按钮与滑杆的更多实际效果：','','| 组 | 原操作与实际证据 |','|---|---|','| 12 滑杆 | 各低/中/高、原生方向键步进、原按钮恢复；波场振幅/频率/方向/水位、后处理尺寸/曝光、灯色、玻璃透明度与风均读取实际对象。船体响应/阻尼另有连续轨迹 |','| 画质 | fine / standard / retro 实际 scale=2 / 2.85 / 3.8，levels=48 / 26 / 12；standard 滑杆取整区别单列 |','| 环境开关 | 灯塔、浪花、沙尘实际对象关闭并恢复；画面灯塔拾取也实测 |','| 镜头 | 五原预设、左旋右移滚轮、瓶/地形双击、灯塔单/双击；镜头恢复后的原惯性单列 |','| 沙盒 | 石头/贝壳由原画布点击新增真实对象；撤销末次、再放置、恢复；拖动和非编辑点击没有新增；Escape 退出 |','| 播放/重置 | 暂停模拟冻结而绘制继续，相机可操作；继续推进。原总重置恢复 12 参数、画质、机位、编辑、用户装饰与播放状态 |','| 下载 | 原截图按钮实际 PNG 下载；隐藏 UI 后保留焦点的原按钮也可由真实 Enter 激活；尺寸按原规则，场景不含 DOM 面板 |','','其他必验操作：','','| 记录 ID | 范围与结果 |','|---|---|','| KEYBOARD.original | H/Space/Escape；输入焦点保护、按钮 Space 原生激活均通过 |','| MOTION.height-0/50/100 | 每档 ≥8 实际 simTime 秒、≥40 不同渲染帧；水面和船体连续联动通过 |','| MOTION.directions | 0/90/180/270 原方向向量和连续姿态均已保存 |','| MOTION.boatResponse/boatDamping/wind | 原生 UI 0/100 与真实轨迹；风力零值保留自然衰减，不强制归零 |','| MOTION.strong-water-safety | 强浪、水位 0/100、风力 100 代表组合数值有效，原安全检查为真；非穷举 |','| ENGINE.representative | Chromium、Firefox、Linux WebKit 的加载、滑杆、镜头、界面和 PNG 代表路径通过 |','| VIEW.mobile-touch | 390×844 与 844×390，原生触摸点按、单指旋转、双指缩放，面板可折叠展开与滚动；手机模拟，不是真机 |','| LOAD.file-cold | Firefox 原文件冷启动通过；受管 Chromium 策略阻止，记设备/浏览器限制 |','| FAILURE.webgl-disabled | 真正禁用 WebGL 后 ready=false、原错误界面显示，通过故障基线 |','| FAILURE.context-loss-reload | 真实 contextlost 及刷新恢复已记录；原 ready/错误遮罩缺陷单列 |','| LIFECYCLE.reduced-motion | 实际匹配减少动态偏好，CSS 动画缩短，3D 继续；原语义已记录 |','| LIFECYCLE.native-tab-visibility | 实际标签切换尝试没有观察到 hidden；后台恢复/节流未验证，不计通过 |','','原问题、文档差异及未覆盖边界见 [original-issues.md](original-issues.md)。所有记录只针对独立原页；内嵌保留性仍需后续对照。','']
(DOC/'feature-matrix.md').write_text('\n'.join(lines))
physics=[]
for h in[0,50,100]:
 d=read(OUT/'physics'/('height-'+str(h)+'.json'));assert d['simSeconds']>=8 and d['distinctRenderedFrames']>=40;physics.append(d)
versions={r['engine']:r['browserVersion']for r in adopted if r['id']=='ENGINE.representative'}
report=['# 第一步验收：独立原页基线','','第一步基线完成，原有问题与环境限制已单列；这不表示所有路径通过，也不表示已接入 Coding。日期：2026-11-13（Asia/Shanghai）。执行仅新增文档、测试脚本与证据，原成品、个人网站和罗森运行文件保持原样，未提交、上传或部署。','','| 结果 | 数量 / 说明 |','|---|---|',f'| 采用的检查记录 | {len(adopted)} |']
for status,count in counts.items():report.append(f'| {status} | {count} |')
report+=['| DOM 控件 | 12 滑杆 + 22 按钮，逐项均有操作与确定结果；其中默认亮度和镜头恢复的原问题另外保留 |','','版本与环境：','','- 原提交 d94c1f911a39143fd8f5efe152b99a87fdc53184，成品 SHA256 941feb2ea6ddd3cc93aad5b0b92dbca52ee66a3e1098fee0dbf16f01ca63d1ef；两 HTML 字节一致，未重构建。',f'- Linux；Chromium {versions["chromium"]}、Firefox {versions["firefox"]}、Linux WebKit {versions["webkit"]}，均实际启动有界面浏览器。','- Chromium WebGL2 为 ANGLE/Mesa llvmpipe；Firefox 报告 llvmpipe；运行环境设置 LIBGL_ALWAYS_SOFTWARE=1。WebKit 的隐私化 renderer 字符串为 Apple GPU，不代表真 Apple 硬件或 Safari 真机。','- 先在 1920×1080、1440×900 / DPR1 记录原 fine 默认画面；主要控件/模拟检查随后通过原按钮选 retro，1024×768。代表兼容为 1280×720，手机模拟 390×844 与 844×390 / DPR3。','- 所有浏览器外部 HTTP 尝试为 0；原服务 no-store、测试路由关闭缓存，再次加载不声称是热缓存验证。未安装/升级原产品依赖，未执行旧 QA 替代本轮验收。','','主要结果：','','- HTTP 首次/再次加载和 Firefox file:// 冷启动呈现完整世界；实际场景含三桅船、瓶内水、玻璃、天空、沙地、外海和灯塔，并有真实绘制。','- 34 控件、原指针/按键、沙盒对象、播放/全局恢复、镜头和实际 PNG 下载详见 [功能矩阵](feature-matrix.md)。Firefox/WebKit 只覆盖代表操作，没有冒充全量 34 控件复验。','- 原生截图按钮生成了 1920×1080 PNG；960×600 / DPR3 生成 1920×1200，证实 DPR 上限 2。已查看真实下载图像，包含场景且不含 DOM 面板。隐藏 UI 后仍聚焦原按钮的键盘导出也有实测。','- 实际故障注入覆盖 Chromium 禁用 WebGL 与 WEBGL_lose_context；前者有预期初始化错误日志，正常路径没有 pageerror 或 console.error；后者刷新恢复。','','连续联动：','','| 原波高 | 实际模拟窗口（秒） | 不同渲染帧 | 采样墙钟（秒） | 水面峰谷差 | 船体高度峰谷差 |','|---|---:|---:|---:|---:|---:|']
for d in physics:report.append(f'| {d["initial"]["diagnostics"]["state"]["waveHeight"]} | {d["simSeconds"]:.4f} | {d["distinctRenderedFrames"]} | {d["wallSeconds"]:.2f} | {d["range"]["surface"]:.6f} | {d["range"]["rootY"]:.6f} |')
report+=['','原生 UI 设置、自然过渡后逐真实渲染帧只读取数；simTime 与 GPU 水面时间一致。方向、响应/阻尼/风力、代表强浪/水位组合亦有连续样本和截图。没有改 dt、时钟、RAF 回调参数、物理系数、随机数或船体姿态；部分观测包装以原参数调用原函数一次。脚本数据只能支持已测组合，不能证明所有条件绝不穿模或硬件 60 FPS。','','原问题与未验证：','','- 原亮度默认值与 range 步进差异；运行中图形丢失后旧 ready、错误标志与遮罩的缺口；镜头恢复的残余惯性，详见 [原问题清单](original-issues.md)。','- 受管 Chromium 禁止 file://；Firefox 文件直开通过。两种真实标签切换方式仍未观测到 hidden，后台恢复/节流未验证。手机为触摸模拟；真机、其他系统、硬件性能与穷举边界未验证。','- 完整 iframe 接入、资源回收和主站隔离属于后续步骤，本步不预先宣布这些通过。','','复测和证据：','','- 初次灯塔点选遮挡、风力断言过严、手机操作未展开面板等失败原始记录均保留；复测分别采用 interactions-picking-retest、physics-wind-retest、chromium-mobile-file-retest，没有覆盖首次失败。','- [final-summary.json](../evidence/beach-bottle-boat-step-1/final-summary.json) 逐条列出采用记录、浏览器版本、成品摘要和 JSON 位置；rawRuns 保留每轮原始状态。环境限制不计通过。','- [默认 1920 画面](../evidence/beach-bottle-boat-step-1/controls/default-1920x1080.png)、[默认 1440 画面](../evidence/beach-bottle-boat-step-1/controls/default-1440x900.png)、[真实场景下载](../evidence/beach-bottle-boat-step-1/interactions/export-1920x1080-ui-visible.png)、[原始证据目录](../evidence/beach-bottle-boat-step-1)、[本步脚本](../../tests/beach-bottle-boat-step-1)。','','完整性和收尾：','',f'- 原仓库 {protection["sourceFilesVerified"]} 个文件摘要和提交不变，git status 干净；主站 {protection["hostProductionInputsVerified"]} 项生产输入、罗森 {protection["lawsonRuntimeFilesVerified"]} 个运行文件、八组旧封存及各自文件全部复核一致。','- 本步浏览器均关闭，专用 HTTP 服务和 Xvfb 按启动 PID、参数和启动时标核对后停止；未停止其他服务，见 [清理记录](../evidence/beach-bottle-boat-step-1/services-cleanup.json)。','- 本步资料和证据另建 SHA256 清单 [evidence-manifest.json](../evidence/beach-bottle-boat-step-1/evidence-manifest.json)；复核命令：python tests/beach-bottle-boat-step-1/finalize.py --verify-only。','','下一步承接见 [step-1-handoff.md](step-1-handoff.md)。第二步仍待用户细化/执行指示。','']
(DOC/'step-1-verification.md').write_text('\n'.join(report))
standard=DOC/'step-1-standard.md';text=standard.read_text();start=text.index('状态：');end=text.index('\n',start);text=text[:start]+'状态：第一步独立原版基线完成（含已登记的原问题与环境限制）。执行依据为用户授权，执行前标准保存在 standard-before.md；结果见 step-1-verification.md。仅新增资料，主站与原成品不变，后续步骤尚未执行。日期：2026-11-13（Asia/Shanghai）。'+text[end:];text=text.replace('执行后计划形成以下资料；当前仅编写标准，不表示这些结果已生成：','以下资料现已生成，逐项实际结果以验收报告及原始证据为准：');standard.write_text(text)
plan=DOC/'integration-plan.md';text=plan.read_text();start=text.index('状态：');end=text.index('\n',start);text=text[:start]+'状态：第一步独立原版基线已执行并形成验收资料，包含原问题及环境限制；第二至七步仍为方案，未接入 Coding、未修改个人网站功能、未上传或部署。用户继续采用逐步细化、逐步授权执行的方式。'+text[end:];text=text.replace('图形上下文丢失后也会显示错误，但旧 ready 不一定自动清除，必须按当前事件/文档确认。','本轮实测图形丢失后旧 ready 保留、错误遮罩未重新显示，必须观察当前 canvas 真实故障，详见 original-issues.md。');text=text.replace('本轮只形成以上方案。后续按用户指示逐步细化与实施，','第一步结果见 [验收报告](step-1-verification.md)。其余步骤按用户指示逐步细化与实施，');plan.write_text(text)
for p in (TEST/'__pycache__').glob('*'):p.unlink()
if(TEST/'__pycache__').exists():(TEST/'__pycache__').rmdir()
new=[]
for base in[DOC,OUT,TEST]:
 for p in sorted(base.rglob('*')):
  if p.is_file()and p.name!='evidence-manifest.json':new.append(row(p))
manifest={'schema':1,'createdAtShanghai':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'scope':'Only new step-1 docs, evidence and scripts; original products/history are separately pinned in baseline.json','files':sorted(new,key=lambda r:r['path'])};(OUT/'evidence-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'baselineCompleted':True,'adoptedCases':len(adopted),'statusCounts':counts,'sealedNewFiles':len(new),'originalAndHostUnchanged':True},ensure_ascii=False))
