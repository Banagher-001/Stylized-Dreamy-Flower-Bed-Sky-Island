"""Validate and seal step-2 design outputs without rewriting either step-1 seal."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib,json,re,subprocess

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/evidence/lawson-fullpage-step-2'
DOC=ROOT/'docs/lawson-fullpage'
TEST=ROOT/'tests/lawson-fullpage-step-2'
SOURCE=ROOT.parent/'luosen-asset'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,data):p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
now=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
baseline=read(OUT/'baseline.json')
prior=read(ROOT/baseline['referenceBaseline'])
assets=read(OUT/'asset-manifest.json')
runtime_path=ROOT/'docs/evidence/lawson-fullpage-step-1/runtime-manifest.json'
runtime=read(runtime_path)
accepted=read(OUT/'run-4/design-checks.json')
assert accepted['passed'] and len(accepted['checks'])==13
for name in ['design-preview.html','design-preview.css','design-preview.js']:
    assert sha(OUT/name)==sha(OUT/'run-4'/(name+'.txt')),name
assert sha(TEST/'verify_design.py')==sha(OUT/'run-4/verify_design.py.txt')
assert sha(ROOT/baseline['referenceBaseline'])==baseline['referenceBaselineSHA256']

integrity={'capturedAtShanghai':now,'scope':'Step 2 documents, design prototype, tests only','protectedInputs':{},'oldSeals':[]}
for name,root in [('source',SOURCE),('host',ROOT)]:
    data=prior[name]
    for f in data['runtimeInputs']:
        p=root/f['path'];assert p.stat().st_size==f['bytes'] and sha(p)==f['sha256'],f['path']
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    diff=subprocess.check_output(['git','diff','HEAD','--name-only'],cwd=root,text=True).strip()
    assert head==data['head'] and not diff,(name,head,diff)
    integrity['protectedInputs'][name]={'head':head,'filesVerified':len(data['runtimeInputs']),'trackedDiff':diff,'unchanged':True}
for row in baseline['oldSeals']:
    p=ROOT/row['path'];assert sha(p)==row['sha256']
    sealed=read(p)
    for f in sealed['files']:
        q=ROOT/f['path'];assert q.stat().st_size==f['bytes'] and sha(q)==f['sha256'],f['path']
    integrity['oldSeals'].append({'path':row['path'],'sha256':row['sha256'],'filesVerified':len(sealed['files']),'unchanged':True})
for a in assets['assets']:
    p=ROOT/a['path'];source=Path(a['sourcePath'])
    assert p.stat().st_size==a['bytes'] and sha(p)==a['sha256'] and sha(source)==a['sha256']
assert not (ROOT/'public/experiments/lawson').exists()
integrity['productionLawsonDirectoryCreated']=False
integrity['referenceImageCopiesByteIdentical']=len(assets['assets'])
integrity['standardStatusUpdate']={'beforeSHA256':baseline['standardSHA256'],'afterSHA256':sha(DOC/'step-2-standard.md'),'reason':'Update step-2 status and link completed verification; not a sealed step-1 file.'}
integrity['passed']=True
write(OUT/'integrity.json',integrity)

handoff={'schema':1,'createdAtShanghai':now,'nextStep':3,'sourceRepository':'Banagher-001/luosen-asset','sourceCommit':baseline['sourceHead'],
    'hostRepository':'Banagher-001/Stylized-Dreamy-Flower-Bed-Sky-Island','hostCommit':baseline['hostHead'],
    'sourceRuntimeRoot':'/workspace/luosen-asset/lawson-blender/out/web_final',
    'targetRuntimeRoot':'public/experiments/lawson','buildRuntimeRoot':'dist/experiments/lawson','entryPath':'experiments/lawson/index.html',
    'manifestSource':str(runtime_path.relative_to(ROOT)),'manifestSHA256':sha(runtime_path),
    'runtimeFileCount':runtime['runtimeFileCount'],'runtimeBytes':runtime['runtimeBytes'],'modelBytes':runtime['modelBytes'],
    'targetExistsAtStep2Completion':False,'preserveBytes':True,'preserveRelativePaths':True,
    'urlRule':'Resolve from the Vite site base and current site document; same resolver for iframe and independent open; test root and subpath builds.',
    'knownIssuesDocument':'docs/lawson-fullpage/original-issues.md','designContract':'docs/evidence/lawson-fullpage-step-2/design-contract.json',
    'forbiddenDuringCopy':['rewrite source JS/CSS/HTML','merge Three.js versions','remove original UI','inject bridge','silently fix source defects'],
    'requiredVerification':['all target file hashes and byte sizes','production build','all built runtime file hashes','direct HTTP original ready/fatal/default state','root and subpath asset resolution'],
    'files':[{'source':'lawson-blender/out/web_final/'+f['path'],'target':'public/experiments/lawson/'+f['path'],'build':'dist/experiments/lawson/'+f['path'],'bytes':f['bytes'],'sha256':f['sha256']}for f in runtime['runtimeFiles']]}
assert len(handoff['files'])==46 and len({f['target']for f in handoff['files']})==46
write(OUT/'step-3-handoff.json',handoff)

contract={'schema':1,'status':'design-finalized-not-production-implemented','projectIds':['lawson','courtyard'],'defaultProjectId':'lawson',
    'station':{'id':'C2','start':9.5,'end':10.5,'stop':10.05,'label':'交互作品'},
    'openSignature':'open(projectId, tab, trigger?)','projectTabs':['live','archive'],
    'experience':{'lawson':{'kind':'embedded-page','entryPath':'experiments/lawson/index.html'},'courtyard':{'kind':'host-scene'}},
    'toolbar':{'regularHeight':56,'compactHeight':48,'compactWhen':'width <= 767 or height <= 480','textEnlargement':'Allow natural wrapping; use measured height','controls':['project name','live/archive','independent open','return']},
    'body':{'width':'100% of available viewport','height':'remaining dynamic viewport after actual toolbar and safe areas','productionIframeScaling':False,'productionIframeAspectLock':False},
    'lifecycle':{'mountWhen':'lawson live only','maximumIframes':1,'unmountOn':['archive','close','dispose'],'stopGardenDuringLawson':True,'stopGuideOnOpenOrProjectSelection':True,'resumeGuideAutomatically':False,'restorePriorEnvironmentPlayback':True,'preserveUnloadedChildState':False},
    'availability':{'hostFailureDisablesLawsonAttempt':False,'archiveAndReturnAlwaysAvailable':True},
    'readySignals':{'mode':'same-origin readonly observation','errorHasPriority':True,'signals':['original fatal visibility','__LAWSON__.error','body.dataset.ready','__LAWSON__.ready'],'iframeLoadMeansReady':False,'slowAfterSeconds':12,'injectBridge':False,'guardStaleInstancesAndDocuments':True},
    'escape':'Preserve source Escape while focus is inside frame; host cancel must not close that interaction. Host-focused Escape may close.',
    'prototypeOnly':['static reference image object-fit','design status menu','standalone query route','__STEP2_DESIGN__','fake background context'],
    'productionImplementationSteps':{'copy':3,'host':4,'iframe':5,'deviceCases':6,'parityRegression':7}}
write(OUT/'design-contract.json',contract)

layout=[c['evidence']for c in accepted['checks']if c['name'].startswith('layout ')]
large=[c['evidence']for c in accepted['checks']if c['name'].startswith('200 percent text')]
geometry_rows='\n'.join(f'| {r["viewport"][0]}×{r["viewport"][1]} | {r["toolbar"]["height"]:g}px | {r["pageArea"]["width"]:g}×{r["pageArea"]["height"]:g} |'for r in layout)
font_rows='\n'.join(f'- {r["viewport"][0]}×{r["viewport"][1]}：工具栏自然高度 {r["toolbar"]["height"]:g}px，主要操作仍在视口内。'for r in large)

verification=f'''# 第二步验收：Coding 展位与大尺寸原网页体验层设计

**第二步已完成。** 交付了设计定稿、可操作静态样稿、接口契约、第三步迁入清单和浏览器检查证据。本结论仅覆盖设计，不表示原网页已接入正式主站。

完成时间：{now}（Asia/Shanghai）。

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
{geometry_rows}

上述是宿主设计区域尺寸，原参考图保留比例；它不是实时原网页已经按这些尺寸通过功能测试的证明。主要外层按钮和展位入口至少 44×44 CSS px，检查了可见性及横向溢出。

200% 文字采用根字体从 16px 调整至 32px，不冒充物理浏览器缩放：

{font_rows}

## 浏览器检查

Chromium {accepted['browser']}，headless，DPR 1。最终 [run-4/design-checks.json](../evidence/lawson-fullpage-step-2/run-4/design-checks.json) 的 13 组全部通过：七种常规尺寸、作品身份/键盘/Esc、状态和独立参考/反复打开、三组大字号、减少动态。

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
'''
(DOC/'step-2-verification.md').write_text(verification)

required=[DOC/('step-2-'+n+'.md')for n in ['standard','design','interface','handoff','verification']]
broken=[]
for p in required:
    assert p.is_file()
    for link in re.findall(r'\[[^\]]*\]\(([^)]+)\)',p.read_text()):
        if '://'in link:continue
        target=(p.parent/link.split('#')[0]).resolve()
        if not target.exists() and target!=OUT/'evidence-manifest.json':broken.append({'file':str(p.relative_to(ROOT)),'link':link})
assert not broken,broken
summary={'schema':1,'complete':True,'step':2,'scope':'Design, static prototype, contracts and handoff only','createdAtShanghai':now,'acceptedBrowserRun':'run-4','browserChecksPassed':13,
    'runtimeFilesUnchanged':46,'hostInputsUnchanged':91,'oldSealFilesUnchanged':[77,109],
    'productionIntegrationImplemented':False,'sourceRuntimeCopiedToPublic':False,'actualIframeVerifiedInStep2':False,'committed':False,'pushed':False,'published':False,
    'outputs':[str(p.relative_to(ROOT))for p in required],'prototype':'docs/evidence/lawson-fullpage-step-2/design-preview.html','nextStepHandoff':'docs/evidence/lawson-fullpage-step-2/step-3-handoff.json',
    'limits':['Static screenshot reference is not interactive source webpage','No physical mobile or GPU evidence','Actual fullscreen/pointer lock/input isolation and garden suspension remain future integration checks']}
write(OUT/'summary.json',summary)
write(OUT/'validation.json',{'passed':True,'brokenLinks':broken,'acceptedBrowserChecks':13,'acceptedPrototypeMatchesSnapshots':True,'protectedFilesUnchanged':True,'handoffFiles':len(handoff['files']),'step2Only':True})

files=[]
for p in [*required,*sorted(OUT.rglob('*')),*sorted(TEST.rglob('*'))]:
    if not p.is_file() or '__pycache__'in p.parts or p==OUT/'evidence-manifest.json':continue
    files.append({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p)})
assert len(files)==len({f['path']for f in files})
write(OUT/'evidence-manifest.json',{'schema':1,'auditId':'lawson-fullpage-step-2','createdAtShanghai':now,'sourceCommit':baseline['sourceHead'],'hostCommit':baseline['hostHead'],'previousSeals':baseline['oldSeals'],'selfExcluded':True,'fileCount':len(files),'totalBytes':sum(f['bytes']for f in files),'files':files})
print(json.dumps({'step2Complete':True,'browserChecks':13,'sealedFiles':len(files),'handoffFiles':46,'productionFilesChanged':False,'oldSealsUnchanged':[77,109]},ensure_ascii=False))
