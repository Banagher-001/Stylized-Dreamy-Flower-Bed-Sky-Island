"""Verify pinned originals/history and select actual, appropriately scoped evidence."""
from pathlib import Path
from datetime import datetime,timezone
import difflib,hashlib,json,subprocess
from harness import ROOT,OUT

MODIFIED={'src/tour/createLawsonExperience.ts','src/tour/createProjectViewer.ts','src/tour/startTourPrototype.ts'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def row(p):return {'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)}
def write(name,data):(OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def git(d,*args):return subprocess.check_output(['git','-C',str(d),*args],text=True).strip()

b=read(OUT/'baseline.json');assert git(ROOT,'rev-parse','HEAD')==b['head']
history=[]
for s in b['oldSeals']:
    p=ROOT/s['path'];assert sha(p)==s['sha256'];d=read(p);assert len(d['files'])==s['fileCount']
    for f in d['files']:assert row(ROOT/f['path'])==f,f['path']
    history.append({**s,'allFilesUnchanged':True})
m_path=ROOT/b['runtimeManifest'];assert sha(m_path)==b['runtimeManifestSHA256'];m=read(m_path)
source=ROOT.parent/'luosen-asset/lawson-blender/out/web_final'
assert git(source,'rev-parse','HEAD')==b['sourceHead']and git(source,'status','--short')==b['sourceStatusBefore']==''
runtime=[]
for directory in [source,ROOT/'public/experiments/lawson',ROOT/'dist/experiments/lawson']:
    if directory!=source:assert sorted(p.relative_to(directory).as_posix()for p in directory.rglob('*')if p.is_file())==sorted(f['path']for f in m['runtimeFiles'])
    for f in m['runtimeFiles']:
        p=directory/f['path'];assert p.stat().st_size==f['bytes']and sha(p)==f['sha256'],p
    runtime.append({'path':str(directory),'fileCount':46,'totalBytes':sum(f['bytes']for f in m['runtimeFiles']),'allSHA256Match':True})
changed=[];unchanged=[]
for before in b['hostInputsBefore']:
    actual=row(ROOT/before['path'])
    (changed if actual!=before else unchanged).append({'before':before,'after':actual}if actual!=before else actual)
assert {c['after']['path']for c in changed}==MODIFIED
build=read(OUT/'build-result.json');assert build['exitCode']==0 and build['includesTypecheck']
for f in build['productionInputs']+build['builtFiles']:assert row(ROOT/f['path'])==f,f['path']
assert read(OUT/'build-delta.json')['changedFromBuild1To2']==['src/tour/createLawsonExperience.ts','src/tour/createProjectViewer.ts']
subprocess.run(['git','-C',str(ROOT),'diff','--check'],check=True)
patch=[]
for path in sorted(MODIFIED):patch.extend(difflib.unified_diff((OUT/'before'/path).read_text().splitlines(keepends=True),(ROOT/path).read_text().splitlines(keepends=True),fromfile='before/'+path,tofile='after/'+path))
(OUT/'host-changes.patch').write_text(''.join(patch))

# Explicitly exclude failed probes and weaker visibility/padding attempts.
selection=[
 ('boundary-final',None,'build2'),
 ('layout-chromium',['layout 1440x900','layout 1366x768','layout 768x1024','layout 390x844','layout 375x812','layout 320x568','layout 844x390','layout continuous rotation and return'],'build1'),
 ('layout-large-recheck',None,'build1'),('layout-firefox',None,'build1'),('layout-webkit',None,'build1'),('network',None,'build1'),
 ('interactions',['touch gestures and panel isolation','stress ten full and twenty cancelled','ownership project media rapid transfer','zoom actual browser two hundred percent'],'build1'),
 ('focus-safe-recheck',['keyboard modal traversal and restoration'],'build2'),('safe-area-final',None,'build2'),
 ('lifecycle',['accessibility reduced motion semantics'],'build1'),('graphics-recheck',None,'build2'),('hmr',None,'isolated Vite copy from build1'),
 ('permissions-final',None,'build2'),('native-visibility-final',None,'build2 native Chrome no_defaults'),
 ('compat-chromium',None,'build2'),('compat-firefox',None,'build2'),('compat-webkit',None,'build2'),
 ('permissions-supported',None,'build2'),('no-webgl',None,'build2'),('history-final',None,'build2'),
]
accepted=[];raw_events=[]
for run,names,version in selection:
    report=read(OUT/run/'browser.json');engine=report.get('engine','chromium-native');selected=[]
    for c in report['checks']:
        if names is None or c['name']in names:
            assert c['passed'],(run,c['name']);selected.append(c['name']);accepted.append({'report':run+'/browser.json','build':version,'engine':engine,'browserVersion':report['browserVersion'],**c})
    if names is not None:assert set(names)==set(selected),(run,selected)
    raw_events.extend({'report':run+'/browser.json',**e}for e in report.get('events',[])if e['case']in selected)
assert len(accepted)==49,len(accepted)
assert len({(c['engine'],c['name'])for c in accepted})==49
native=read(OUT/'native-visibility-final/browser.json')
assert native['noDefaultsCDP']and native['ownedChromeStopped']and native['temporaryProfileRemoved']
for c in native['checks']:assert c['evidence']['actualHidden']['state']=='hidden'and c['evidence']['childActuallyHidden']
safe=next(c for c in accepted if c['name']=='safe area actual env inset emulation')
assert safe['evidence']['CDPSafeAreaProtocolSupported']and safe['evidence']['realEnvInsetsVerified']

def expected(e):
    case=e['case'];kind=e['kind'];text=e.get('text','');url=e.get('url','')
    if kind=='console'and e.get('level')=='warning':return True
    if kind=='requestfailed'and text=='net::ERR_ABORTED'and any(x in url for x in ['/experiments/lawson/','/assets/','/src/']):return True
    if case in ['document wrong HTML','network document 404','network document 500']:
        code=500 if case.endswith('500')else 404
        if kind=='response':return e['status']==code and url.endswith('/experiments/lawson/index.html')
        return kind=='console'and 'Failed to load resource:'in text and str(code)in text
    models=['layout small error and 200 percent','HMR module error','native visibility error']
    if case in models or case=='network car model failure':
        model='car_B.glb'if case=='network car model failure'else'lawson_scene.glb'
        if kind=='requestfailed':return text=='net::ERR_FAILED'and url.endswith('/assets/models/'+model)
        return kind=='console'and('net::ERR_FAILED'in text or('[Lawson] fatal:'in text and model in text))
    if case=='network vendor module failure':
        if kind=='requestfailed':return text=='net::ERR_FAILED'and url.endswith('/vendor/three/three.module.js')
        return kind=='console'and'net::ERR_FAILED'in text
    if case in ['network cold offline and return','network warm offline and return']:
        if kind=='requestfailed':return text=='net::ERR_INTERNET_DISCONNECTED'and'/experiments/lawson/'in url
        return kind=='console'and('net::ERR_INTERNET_DISCONNECTED'in text or('[Lawson] fatal:'in text and'lawson_scene.glb'in text))
    if case=='network restricted embedding':
        return (kind=='requestfailed'and text=='net::ERR_BLOCKED_BY_RESPONSE'and url.endswith('/experiments/lawson/index.html'))or(kind=='console'and'frame-ancestors'in text)
    if case=='permissions denied fullscreen remains usable':return (kind=='pageerror'and text=='Disallowed by permissions policy')or(kind=='console'and'Permissions policy violation: fullscreen'in text)
    if case=='permissions pointer lock without activation':return kind=='pageerror'and text=='A user gesture is required to request Pointer Lock.'
    if case=='graphics browser without WebGL':return kind=='console'and any(s in text for s in ['THREE.WebGLRenderer:','Tour scene initialization failed.','[Lawson] fatal:'])
    return False
errors=[e for e in raw_events if e['kind']!='console'or e.get('level')=='error'];unexpected=[e for e in errors if not expected(e)]
write('event-audit.json',{'passed':not unexpected,'unexpected':unexpected,'expectedFaultErrors':[e for e in errors if expected(e)],'warnings':[e for e in raw_events if e['kind']=='console'and e.get('level')=='warning']})
assert not unexpected,unexpected
attempts=[]
for p in sorted(OUT.glob('*/browser.json')):
    r=read(p);attempts.append({'report':str(p.relative_to(OUT)),'passed':r['passed'],'failedChecks':[c['name']for c in r['checks']if not c['passed']]})
coverage={
 'physicalIOSAndAndroid':'not verified; desktop engines and touch emulation are separate',
 'physicalNotchDynamicAddressBarAndOSScaling':'not verified; actual CSS env emulation and desktop browser zoom verified',
 'BFCacheRestore':'not observed; real history back used full reload and succeeded',
 'screenReaderHardware':'not verified; native keyboard and semantic DOM checks only',
 'hardwareGPUPerformance':'not measured; Mesa software GL and original adaptive quality retained',
 'all41ControlsAnd17Picks':'reserved for step7; count preservation and basic controls verified',
 'actualVisibility':'verified hidden/visible on parent and child in owned native Chrome default context',
 'otherBrowserVisibilityAndNativePermissions':'not exhaustively covered; Firefox/WebKit actual scenes, layout, resize and light controls verified',
}
write('accepted-browser-results.json',{'passed':True,'acceptedGroups':49,'groups':accepted,'allAttemptsPreserved':attempts,'eventAudit':'event-audit.json','coverageBoundaries':coverage,
 'finalBuild':'build-2.log','reuseExplanation':'Build1 and isolated HMR results cover unchanged lifecycle/geometry; build2 only adds actual fullscreen restriction notice, directly verified on all three engines and denied-policy path.','buildDelta':'build-1-to-2.patch',
 'physicalDeviceResultsInvented':False,'originalRuntimeOrClockModified':False})
write('integrity.json',{'passed':True,'capturedAtUTC':datetime.now(timezone.utc).isoformat(),'hostHead':b['head'],'sourceHead':b['sourceHead'],
 'oldSeals':history,'runtime':runtime,'hostInputsBefore':95,'authorizedModifiedInputs':changed,'untouchedInputCount':len(unchanged),'untouchedInputs':unchanged,
 'newProductionFiles':[],'build':'build-2.log','buildPassed':True,'gitDiffCheckPassed':True,'acceptedBrowserGroups':49,'originalWorkingTreeClean':True,'committed':False,'pushed':False,'published':False})
print(json.dumps({'passed':True,'acceptedBrowserGroups':49,'modifiedInputs':len(changed),'untouchedInputs':len(unchanged),'runtimeFilesPerCopy':46,'oldSealCounts':[s['fileCount']for s in history]},ensure_ascii=False))
