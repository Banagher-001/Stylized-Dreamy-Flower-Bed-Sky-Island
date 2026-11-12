"""Seal immutable step-5 evidence, including copies of mutable host sources."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import argparse,hashlib,json,re,shutil,subprocess

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/evidence/lawson-fullpage-step-5';SEAL=OUT/'evidence-manifest.json'
parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def row(p):return {'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)}
def write(p,data):p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def verify(s):
    assert len(s['files'])==s['fileCount']
    for f in s['files']:assert row(ROOT/f['path'])==f,f['path']
    assert sum(f['bytes']for f in s['files'])==s['totalBytes']
if args.verify_only:
    s=read(SEAL);verify(s);print(json.dumps({'passed':True,'sealedFiles':s['fileCount'],'sealSHA256':sha(SEAL)}));raise SystemExit(0)
assert not SEAL.exists(),'Preserve this step; use --verify-only after sealing'
b=read(OUT/'baseline.json');integrity=read(OUT/'integrity.json');build=read(OUT/'build-result.json');browser=read(OUT/'accepted-browser-results.json')
assert integrity['passed']and browser['passed']and browser['acceptedGroups']==15
assert read(OUT/'cleanup.json')['passed']
assert subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()==b['head']
for seal_info in b['oldSeals']:
    p=ROOT/seal_info['path'];assert sha(p)==seal_info['sha256'];verify(read(p))
for f in build['productionInputs']:
    assert row(ROOT/f['path'])==f
    target=OUT/'after'/f['path'];target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():assert sha(target)==f['sha256']
    else:shutil.copyfile(ROOT/f['path'],target)
for f in build['builtFiles']+integrity['untouchedInputs']:assert row(ROOT/f['path'])==f
write(OUT/'step-6-handoff.json',{
    'schema':1,'completedStep':5,'nextStep':6,'hostCommit':b['head'],'sourceCommit':b['sourceHead'],
    'actualIframeIntegrationImplemented':True,'sourceRuntimeChanged':False,'runtimeFiles':46,'runtimeBytes':20332784,
    'manager':'src/tour/createLawsonExperience.ts','methods':['mount','retry','unmount','dispose'],
    'managerOptions':['container','entry','wanted','status'],'activeSource':'projectViewer.active',
    'mountCondition':"active?.id === 'lawson' && active.tab === 'live'",
    'entryResolver':'resolveProjectEntry(lawson)','entryPath':'experiments/lawson/index.html',
    'mountNode':'projectViewer.embeddedMount','singleIframe':True,'mountAfterModalLayout':True,
    'statusStates':['prepared','loading','slow','error','ready'],'loadingPollMS':200,'readyPollMS':500,'slowAfterMS':12000,
    'originalFatalAndErrorBeforeReady':True,'originalRetryReobservesNewDocument':True,'hostRetryReplacesIframe':True,
    'oldInstanceAndDocumentCallbacksInvalidated':True,'htmlLoadNotUsedAsReady':True,
    'fullscreenAllowed':True,'sandboxAdded':False,'productionBridgeInjected':False,
    'nativeFullscreenPointerLockAndEscapeVerified':True,'nativeEscapeMethod':'X11 Escape in headful Chromium',
    'pointerLockOwner':'iframe.contentDocument; parent getter was null in this browser',
    'unmountBeforeGardenResume':True,'reentryRestoresOriginalDefaults':True,'sceneStatePersistenceAdded':False,
    'hostGardenCoveredDrawsPerSecond':0,'acceptedBrowserGroups':15,'browser':'Chromium 155.0.8059.79',
    'backend':'Mesa software WebGL; no hardware FPS proof','physicalDevicesVerified':False,
    'verifiedPrefixes':['/','/Stylized-Dreamy-Flower-Bed-Sky-Island/'],
    'verifiedViewports':['1440x900','1366x768','390x844','320x568','844x390','320x568 with parent root font 32px'],
    'pendingStep6':['Physical devices/browser differences','Touch/safe areas and original mobile limitations','More transport and document failure boundaries','Visibility/background behavior','Rapid owner transfers and permission/focus variations','Actual dev HMR disposal regression'],
    'pendingStep7':'Full original 41 controls and 17 pick categories parity; preserve documented original issues',
    'knownOriginalIssues':'docs/lawson-fullpage/original-issues.md',
    'verification':'docs/lawson-fullpage/step-5-verification.md','handoff':'docs/lawson-fullpage/step-5-handoff.md',
    'build':'docs/evidence/lawson-fullpage-step-5/build-result.json','integrity':'docs/evidence/lawson-fullpage-step-5/integrity.json',
    'sourceCopies':'docs/evidence/lawson-fullpage-step-5/after/','seal':'docs/evidence/lawson-fullpage-step-5/evidence-manifest.json',
    'committed':False,'pushed':False,'published':False,
})
docs=[ROOT/f'docs/lawson-fullpage/step-5-{n}.md'for n in ['standard','verification','handoff']]
for doc in docs:
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',doc.read_text()):
        if '://'not in target and not target.startswith('#'):assert (doc.parent/target.split('#')[0]).exists(),(doc,target)
paths=set(docs)
for directory in [OUT,ROOT/'tests/lawson-fullpage-step-5']:
    paths.update(p for p in directory.rglob('*')if p.is_file()and p!=SEAL and '__pycache__'not in p.parts)
files=[row(p)for p in sorted(paths)]
seal={'schema':1,'auditId':'lawson-fullpage-step-5','createdAtShanghai':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
    'hostCommit':b['head'],'sourceCommit':b['sourceHead'],'selfExcluded':True,'previousSeals':b['oldSeals'],
    'productionSourceSealedAsCopies':True,'actualIframeImplemented':True,'originalRuntimeUnchanged':True,
    'acceptedBrowserGroups':15,'fileCount':len(files),'totalBytes':sum(f['bytes']for f in files),'files':files}
write(SEAL,seal);verify(seal)
print(json.dumps({'passed':True,'sealedFiles':len(files),'totalBytes':seal['totalBytes'],'acceptedBrowserGroups':15,'nextStep':6},ensure_ascii=False))
