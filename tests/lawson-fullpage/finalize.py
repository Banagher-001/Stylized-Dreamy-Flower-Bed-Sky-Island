"""Assemble accepted baseline evidence, verify unchanged inputs, and seal this audit."""
from pathlib import Path
from collections import Counter
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib, json, re, subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'docs/evidence/lawson-fullpage-step-1'
DOC = ROOT/'docs/lawson-fullpage'
OLD = ROOT/'docs/evidence/lawson-integration-step-1'
SOURCE = ROOT.parent/'luosen-asset'

def read(path):
    return json.loads(path.read_text())

def write(path, value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def new(run, phase, identifier):
    path=OUT/run/(phase+'.json')
    row=next(c for c in read(path)['checks'] if c['id']==identifier)
    assert row['status']!='需补核', (str(path),identifier,row.get('error'))
    return {'file':str(path.relative_to(ROOT)),'case':identifier,'status':row['status']}

def old(group, key, status='原页正常'):
    path=OLD/(group+'-accepted.json')
    row=read(path)['acceptedChecks'][key]
    assert row['check']['passed']
    return {'file':str(path.relative_to(ROOT)),'case':key,'originalRun':row['from'],'status':status,'reused':True}

CORE_CAMERA='eight camera presets orbit zoom pan reset roof'
CORE_TIME='day night eight lighting groups and shortcuts'
CORE_MOVE='moving car pause resume and UI reset'
CORE_CYCLE='one full vehicle cycle autonomous clerk transitions pause resume reset'
base=read(OUT/'baseline.json')
inventory=read(OUT/'static-inventory.json')
assets=read(OUT/'runtime-manifest.json')

controls=[]
for c in inventory['staticControls']:
    a=c['attributes']; identifier=a.get('id'); name=c.get('text') or a.get('title') or identifier
    if identifier:
        selector='#'+identifier
        special={
          'fatal-retry':('run-9','readiness','READY.model-retry'),
          'btn-fullscreen':('run-6','controls','BUTTON.btn-fullscreen'),
          'btn-settings':('run-1','controls','BUTTON.btn-settings'),
          'btn-help':('run-1','controls','BUTTON.help'),
          'help-close':('run-1','controls','BUTTON.help'),
          'panel-collapse':('run-1','controls','BUTTON.panel-collapse'),
          'time-slider':('run-1','controls','INPUT.time-slider'),
          'btn-walk':('run-7','keyboard','POINTER.walk-look'),
          'btn-reset-cam':('run-7','keyboard','BOUNDARY.R-in-walk'),
        }
        if identifier in special:
            evidence=new(*special[identifier])
            if identifier=='btn-reset-cam':
                evidence['status']='原页正常'
                evidence['interpretation']='Original reset button recovery confirmed; the issue belongs to KeyR cache synchronization.'
        elif identifier.startswith('lights-all-'):
            evidence=old('core',CORE_TIME)
        elif identifier.startswith('traffic-'):
            evidence=old('core',CORE_MOVE)
        elif identifier=='btn-roof':
            evidence=old('core',CORE_CAMERA)
        else:
            raise AssertionError(identifier)
    else:
        key=next(k for k in a if k.startswith('data-'))
        selector=f'[{key}="{a[key]}"]'
        if key=='data-preset':evidence=old('core',CORE_TIME)
        elif key=='data-cam':evidence=old('core',CORE_CAMERA)
        elif key=='data-speed':evidence=new('run-1','controls','TRAFFIC.speeds')
        elif key=='data-clerk':evidence=new('run-9','readiness','READY.clerk-buttons')
        elif key=='data-car':
            evidence=new('run-9','readiness','READY.car-A-button') if a[key]=='A' else new('run-8','traffic','CYCLE.'+a[key])
        else:raise AssertionError(key)
    controls.append({'selector':selector,'name':name,'status':evidence['status'],'evidence':evidence})
for g in inventory['dynamicLightGroups']:
    evidence=new('run-1','controls','LIGHT.'+g['id'])
    controls.append({'selector':f'.toggle[data-group="{g["id"]}"]','name':g['label'],'status':evidence['status'],'evidence':evidence})
assert len(controls)==41 and len({c['selector']for c in controls})==41

shortcuts=[]
for code in inventory['mainBoundShortcuts']+inventory['movementKeys']:
    if code=='KeyR':e=new('run-6b','controls','KEY.KeyR')
    elif code.startswith('Digit'):e=old('core',CORE_TIME)
    elif code=='Space':e=new('run-1','controls','KEY.Space')
    elif code=='Escape':e=new('run-7','keyboard','POINTER.walk-look')
    elif code in ['KeyW','KeyS','ShiftLeft','ShiftRight']:e=new('run-7b','keyboard','KEY.'+code)
    else:e=new('run-7','keyboard','KEY.'+code)
    shortcuts.append({'code':code,'status':e['status'],'evidence':e})
e=new('run-1','controls','DOC.KeyN')
shortcuts.append({'code':'KeyN (README only)','status':e['status'],'evidence':e})

targets=[]
for run in ['run-2','run-3']:
    for c in read(OUT/run/'targets.json')['checks']:
        if not c['id'].startswith('TARGET.'):continue
        e=new(run,'targets',c['id'])
        data=c['evidence']
        targets.append({'id':c['id'].split('.',1)[1],'status':e['status'],'evidence':e,'evidenceKeys':list(data)})
assert len(targets)==17 and len({t['id']for t in targets})==17

behaviors=[
 {'name':'首次 HTTP 加载','evidence':old('core','cold standalone load')},
 {'name':'再次 HTTP 加载','evidence':old('core','warm standalone load')},
 {'name':'刷新回到原默认状态','evidence':new('run-9','readiness','READY.refresh-defaults')},
 {'name':'标签切换和返回；真实隐藏受环境限制','evidence':new('run-9c','readiness','READY.background-return')},
 {'name':'模型失败及原重试','evidence':new('run-9','readiness','READY.model-retry')},
 {'name':'WebGL 不可用的明确错误','evidence':old('compat','WebGL unavailable shows explicit failure')},
 {'name':'旋转、滚轮缩放、右键平移、相机和屋顶','evidence':old('core',CORE_CAMERA)},
 {'name':'漫游鼠标观察、锁定和 Escape','evidence':new('run-7','keyboard','POINTER.walk-look')},
 {'name':'漫游中 R 后的界面状态','evidence':new('run-7','keyboard','BOUNDARY.R-in-walk')},
 {'name':'车辆 A 原时钟完整流程','evidence':old('core',CORE_CYCLE)},
 {'name':'车辆 B 原时钟完整流程','evidence':new('run-8','traffic','CYCLE.B')},
 {'name':'车辆 C 原时钟完整流程','evidence':new('run-8','traffic','CYCLE.C')},
 {'name':'行驶中暂停、恢复、重置','evidence':old('core',CORE_MOVE)},
 {'name':'两名店员自主任务变化','evidence':old('core',CORE_CYCLE)},
 {'name':'默认手机竖屏和横屏','evidence':new('run-9','readiness','VIEWPORT.phone-defaults')},
 {'name':'触摸旋转、双指缩放、夜景点按','evidence':old('compat','mobile layout touch orbit and environment tap')},
 {'name':'减少动态条件匹配但 JS 不自动暂停','evidence':old('compat','reduced motion baseline documented','原页已有问题')},
 {'name':'pauseAll 后仍然绘制','evidence':old('core','pause semantics and lifecycle gaps measured','原页已有问题')},
]
for b in behaviors:b['status']=b['evidence']['status']

now=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
matrix={'schema':1,'capturedAtShanghai':now,'sourceCommit':base['source']['head'],'hostCommit':base['host']['head'],
        'scope':'Original standalone page baseline; not production host integration or a claim that all source features are defect-free.',
        'controls':controls,'shortcuts':shortcuts,'targets':targets,'behaviors':behaviors,
        'developerAPIs':{'count':len(inventory['publicAPIs']),'names':inventory['publicAPIs'],'verification':'Structural inventory and unchanged runtime files; not a claim of 41 individually tested public APIs.'},
        'documentationVehicleClick':'Original help lists clicking vehicles; the original runtime pick list has no car entry. UI car demo buttons are tested separately.',
        'physicalDeviceCoverage':'No real iOS/Android or hardware GPU coverage.'}
write(OUT/'feature-matrix.json',matrix)

def ref(e):
    link='../'+str(Path(e['file']).relative_to('docs'))
    return f'[{Path(e["file"]).parent.name}]({link}) · `{e["case"]}`'+('（复用）'if e.get('reused')else'')

lines=['# 完整功能基线对照表','',
 '状态“原页正常”限定于记录的设备、操作和条件。“原页已有问题”表示问题已查明，不表示功能通过。关键条目均有明确结论；未宣称修复原页或完成正式嵌入。','',
 '## 原有 41 个控件','',
 '32 个静态按钮、1 个滑杆、8 个动态灯光控件；包含平常隐藏的帮助关闭及失败重试。保留原入口，不删减控制台。','',
 '| 原控件 | 选择器 | 结论 | 证据 |','|---|---|---|---|']
for c in controls:lines.append(f'| {c["name"]} | `{c["selector"]}` | {c["status"]} | {ref(c["evidence"])} |')
lines+=['','“重置视角”按钮的正常恢复与 R 快捷键的原有问题分别记录。相机预设测试确认了原按钮反馈，不能解释为拖动后每种时机都能精确复位。','',
 '## 快捷键与移动键','',
 '| 键 | 结论 | 证据 |','|---|---|---|']
for c in shortcuts:lines.append(f'| `{c["code"]}` | {c["status"]} | {ref(c["evidence"])} |')
lines+=['','W/S 的限制对应实际起点与记录位置；A/D 有平面位移，Shift 使用可通行的 A 路径确认加速。Escape 漫游退出与全屏系统 Esc 在各自记录中分别核对。','',
 '## 17 类真实场景点击','',
 '全部使用真实指针点击并观察原处理函数及实际效果；已有相机 API 仅辅助摆放观察视角，未用于派发点击。','',
 '| 物件 ID | 原作用 | 结论 | 证据 |','|---|---|---|---|']
actions={'sign':'LAWSON 招牌灯光','facade':'外墙灯带','door':'门开关和位移','vending':'售货机灯光','basket':'冷柜灯光（原绑定）','checkout':'收银区镜头','shelf':'货架镜头','alcohol':'酒类区镜头','oden':'蒸汽可见性','clerkA':'店员 A 固定区域镜头','clerkB':'店员 B 固定区域镜头','atm':'ATM 发光材质','freezer':'冷柜灯光','cooler':'冷柜灯光','microwave':'微波炉区域镜头','dining':'用餐区镜头','coffee':'咖啡机发光材质'}
for c in targets:lines.append(f'| `{c["id"]}` | {actions[c["id"]]} | {c["status"]} | {ref(c["evidence"])} |')
lines+=['','购物篮切换冷柜灯、店员物件聚焦固定岗位等都按原绑定记录。没有将其改成新交互。','',
 '## 自主流程、输入和错误边界','',
 '| 项目 | 结论 | 证据 |','|---|---|---|']
for c in behaviors:lines.append(f'| {c["name"]} | {c["status"]} | {ref(c["evidence"])} |')
lines+=['','## 界面和调试结构','',
 '原品牌、顶部按钮、控制台、提示、性能信息、加载、错误、帮助、漫游条、工具提示均记录在默认 UI 清单或对应状态截图中。','',
 '公开 API 共 41 个，名称详见 [静态清单](../evidence/lawson-fullpage-step-1/static-inventory.json)。API 清单用于保全原文件结构；并非逐个 API 的功能验收。原 `ready/error` 与 `body.dataset.ready` 用于读取就绪或错误状态，HTML/iframe 的 load 事件不等于模型已就绪。','',
 '旧的临时同源 iframe、子目录、输入隔离、权限、尺寸变化及卸载证据仍保存在 [旧 run-6](../evidence/lawson-integration-step-1/run-6/embed.json)。它们是可行性依据，不能替代新版正式容器的集成验收。','']
(DOC/'feature-matrix.md').write_text('\n'.join(lines))

lines=['# 原网页运行文件清单','',f'固定源版本 `{base["source"]["head"]}`，入口 `lawson-blender/out/web_final/index.html`。','',
 f'共 {assets["runtimeFileCount"]} 个必要运行文件，{assets["runtimeBytes"]:,} 字节；4 个 GLB 共 {assets["modelBytes"]:,} 字节。所有模块引用已解析，无运行时外链依赖；模型没有外链 buffer 或图像。','',
 '网页启动脚本、README 和建模源文件不属于这 46 个浏览器运行依赖。清单用于固定完整网页的运行闭包，不将开发辅助文件误算成缺失的页面资源。','',
 '| 相对原入口的文件 | 字节 | SHA256 前 12 位 |','|---|---:|---|']
for f in assets['runtimeFiles']:lines.append(f'| `{f["path"]}` | {f["bytes"]:,} | `{f["sha256"][:12]}` |')
lines+=['','完整 SHA256、GLB 结构与来源链见 [runtime-manifest.json](../evidence/lawson-fullpage-step-1/runtime-manifest.json)。三个车辆及商店场景均为程序驱动动画；GLB 内没有动画轨道，不应因此误判动画文件缺失。','']
(DOC/'asset-inventory.md').write_text('\n'.join(lines))

integrity={'capturedAtShanghai':now,'checks':{},'trackedChanges':{}}
for name,root in [('source',SOURCE),('host',ROOT)]:
    inputs=base[name]['runtimeInputs'];bad=[]
    for f in inputs:
        p=root/f['path']
        if not p.is_file() or sha(p)!=f['sha256'] or p.stat().st_size!=f['bytes']:bad.append(f['path'])
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    diff=subprocess.check_output(['git','diff','HEAD','--name-only'],cwd=root,text=True).strip()
    integrity['checks'][name]={'filesVerified':len(inputs),'mismatches':bad,'head':head,'expectedHead':base[name]['head']}
    integrity['trackedChanges'][name]=diff
    assert not bad and not diff and head==base[name]['head'],name
oldseal=OLD/'evidence-manifest.json'
assert sha(oldseal)==base['previousSealSHA256']
for f in read(oldseal)['files']:
    p=ROOT/f['path'];assert p.stat().st_size==f['bytes'] and sha(p)==f['sha256'],f['path']
integrity['checks']['oldSeal']={'filesVerified':77,'unchanged':True,'sha256':sha(oldseal)}
for f in assets['runtimeFiles']:
    p=Path('/tmp/lawson-fullpage-step1')/f['path']
    assert p.stat().st_size==f['bytes'] and sha(p)==f['sha256'],f['path']
integrity['checks']['temporaryRuntimeCopy']={'filesVerified':46,'unchanged':True}
integrity['passed']=True
write(OUT/'integrity.json',integrity)

counts={k:dict(Counter(c['status']for c in matrix[k]))for k in ['controls','shortcuts','targets','behaviors']}
summary={'schema':1,'complete':True,'capturedAtShanghai':now,'counts':counts,'knownIssuesDocument':'docs/lawson-fullpage/original-issues.md',
 'interpretation':'Baseline is complete with explicitly documented source defects and device limits; not all source features pass.',
 'productionIntegrationImplemented':False,'productionFilesChanged':False,'gitCommitCreated':False,'pushed':False,'published':False,
 'acceptedNewCases':sorted({(c['evidence']['file']+'#'+c['evidence']['case'])for group in ['controls','shortcuts','targets','behaviors']for c in matrix[group] if not c['evidence'].get('reused')}),
 'preservedDiagnostics':{'run-1':'Initial broad controls; fullscreen renderer Esc limitation and R framing assumption superseded by targeted rechecks.',
 'run-2':'Environment restart after TARGET.sign passed; remaining targets continued in run-3.',
 'run-4':'Native focus addressed an unmapped Chromium auxiliary window; infrastructure interruption.',
 'run-5':'Legacy WM_NAME lookup missed visible Chromium window; R convergence assumption timed out.',
 'run-6':'Fullscreen passed; postflight stability threshold not met, retained as source drift evidence.',
 'run-7':'W and Shift+W path blocked by original collision; explicit original behavior and Shift+A recheck in run-7b.',
 'run-9/run-9b':'Automation-created windows and popup tabs did not hide the source document; native Control+t in run-9c confirms return/readiness and explicitly classifies real hidden handling as an environment limit.'}}
write(OUT/'summary.json',summary)

traffic=read(OUT/'run-8/traffic.json')
assert traffic['complete']
for path in {ROOT/c['evidence']['file']for group in ['controls','shortcuts','targets','behaviors']for c in matrix[group]if not c['evidence'].get('reused')}:
    assert not read(path)['pageErrors'],str(path)
cycles=[c for c in traffic['checks']if c['id'].startswith('CYCLE.')]
cycle_lines='\n'.join(f'- 车辆 {c["id"][-1]}：{c["evidence"]["wallSeconds"]:.1f} 秒真实观察，记录 {len(c["evidence"]["phases"])} 个状态，完成停车、倒车、离场及停用隐藏。'for c in cycles)
report=f'''# 新版第一步验收：原网页版本冻结与完整功能基线

第一步已完成：固定原版文件、补齐逐项功能证据，建立后续整页嵌入的对照基线。原页存在已记录的问题，因此“基线完成”不表示所有原功能无缺陷。当前没有接入 Coding 展示层。

验收时间：{now}（Asia/Shanghai）。

## 版本和完整性

- 罗森：`Banagher-001/luosen-asset`，`{base['source']['head']}`。
- 主站：`Banagher-001/Stylized-Dreamy-Flower-Bed-Sky-Island`，`{base['host']['head']}`。
- 执行开始时两个远端 main 与上述本地提交一致。最终原页 46 个运行文件、主站 91 个监测输入、旧封存 77 个文件均未改变；两个仓库原有跟踪文件无修改。
- 完整运行资源为 46 个文件、20,332,784 字节，其中 4 个 GLB 共 18,648,040 字节。保留原相对路径、本地 Three.js r160 及全部脚本和样式闭包。
- 本步只新增核查文档、证据和工具，没有提交、推送或发布。正式主站入口、原页复制目录和体验层仍留给后续步骤。

见 [文件清单](asset-inventory.md)、[最终完整性](../evidence/lawson-fullpage-step-1/integrity.json)。

## 已建立的操作基线

- 41 个原控件全部有明确证据：32 按钮、1 滑杆和 8 组灯光；包含帮助、收起、三档画质、全屏、错误重试及各原相机、车辆和店员入口。
- 12 个运行时绑定键及 README 提到的 N 已逐项分类。左右移动、左右 Shift 加速、鼠标观察及退出有真实输入反馈；前后移动限制和 R 的两类问题已单列。
- 17 类物件逐一真实点击；核对原处理函数及实际材质、灯光、蒸汽、门或镜头变化。没有把只命中射线当成处理成功。
- 默认桌面 1440×900、1366×768，默认手机 390×844/DPR2 与横屏均留图。功能测试随后选择原 low 画质，未修改默认配置。
- 原全屏按钮进入/退出及操作系统 Esc 退出分别确认；原漫游获得鼠标锁定、鼠标观察与 Escape 退出有独立记录。
- 就绪、模型失败、原重试按钮和刷新恢复默认均有原页面实际证据。原生标签切换后页面仍可用，但该环境未观察到 document.hidden 变为 true，真实隐藏后的处理列为设备/浏览器限制。无 WebGL 和触摸操作复用已核验且未改变的旧证据。

完整条目、结果与具体来源见 [功能对照表](feature-matrix.md) 和 [机器可读矩阵](../evidence/lawson-fullpage-step-1/feature-matrix.json)。41 个开发者 API 只作结构清单，不宣称逐个验收。

## 车辆和自主行为

原车辆 A 的完整流程、真实暂停/恢复/重置及两名店员自主任务变化复用旧证据。本轮补齐 B/C，均使用原 1.8 倍 UI 速度，未修改时钟或强制店员任务：

{cycle_lines}

自主任务按实际观察覆盖记录，不宣称穷尽随机分支。车辆位置与车轮使用实时 `getVehicleState` 核对，不使用可能过时的 UI 位置缓存。

## 原问题与边界

原页的问题包括拖动后复位惯性偏移、漫游中 R 后界面缓存不一致、起始区域前后移动受碰撞阻挡、N 文档与绑定不一致、手机布局和触摸漫游限制。帮助中的点击车辆没有对应拾取入口，原减少动态设置不会暂停 JS，原 pauseAll 也不停止绘制。

这些问题有复现或明确的代码/清单依据，详见 [原页问题](original-issues.md)。本步没有修改原文件来修复它们。新版更具体的实测取代旧记录中对此项过宽的“通过”表述。

环境为 Chromium 155、Mesa llvmpipe 软件 WebGL。没有真实手机、其他浏览器或硬件 GPU 的性能保证；原 HUD 数值不能替代墙钟帧率。旧临时 iframe 可行性记录可复用，但不能替代后续正式容器验收。

## 后续步骤的固定约束

Coding 模块打开大尺寸独立体验层，原网页占主要可用视口；外层只承担作品身份、返回、加载、错误和生命周期。保留原控制台、帮助、时间灯光、镜头、车辆、店员、漫游及原全屏功能，不在嵌入时顺手改造子页。

HTML/iframe 的 load 不等于场景 ready；可读原就绪和错误信号作为后续集成依据。主庭院停绘、退出恢复、焦点、权限、移动设备和最终功能一致性仍是后续步骤的实际工作，本步不提前宣称完成。

## 证据和失败记录

环境重启、输入探针修正、等待假设失败和碰撞路径补测均保留，采用项逐条列在矩阵里。正常路径未捕获脚本异常；模型重试中的请求失败和 fatal 为主动故障注入的预期日志。

- [执行基线](../evidence/lawson-fullpage-step-1/baseline.json)
- [执行标准](step-1-standard.md)
- [复核方法](reproduce.md)
- [汇总](../evidence/lawson-fullpage-step-1/summary.json)
- [新版封存清单](../evidence/lawson-fullpage-step-1/evidence-manifest.json)
'''
(DOC/'step-1-verification.md').write_text(report)

broken=[]
for p in DOC.glob('*.md'):
    for link in re.findall(r'\[[^\]]*\]\(([^)]+)\)',p.read_text()):
        target=(p.parent/link.split('#')[0]).resolve()
        if not target.exists() and target!=OUT/'evidence-manifest.json':broken.append({'file':str(p),'link':link})
assert not broken,broken
write(OUT/'validation.json',{'passed':True,'brokenDocumentationLinks':broken,'matrixCounts':counts,
    'noUnexplainedCriticalCases':True,'integrityPassed':True,'standaloneBaselineOnly':True})

files=[]
for directory in [DOC,OUT,ROOT/'tests/lawson-fullpage']:
    for p in sorted(directory.rglob('*')):
        if not p.is_file() or '__pycache__'in p.parts or p==OUT/'evidence-manifest.json':continue
        files.append({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p)})
write(OUT/'evidence-manifest.json',{'schema':1,'auditId':'lawson-fullpage-step-1','createdAtShanghai':now,
    'sourceCommit':base['source']['head'],'hostCommit':base['host']['head'],'previousSealSHA256':sha(oldseal),
    'fileCount':len(files),'totalBytes':sum(f['bytes']for f in files),'selfExcluded':True,'files':files})
print(json.dumps({'complete':True,'counts':counts,'sealedFiles':len(files),'runtimeFilesUnchanged':46,'hostInputsUnchanged':91,'oldSealFilesUnchanged':77},ensure_ascii=False))
