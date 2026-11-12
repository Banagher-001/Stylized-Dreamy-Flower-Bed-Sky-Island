"""Seal step-6 evidence and immutable source copies, leaving working code mutable."""
from datetime import datetime
from zoneinfo import ZoneInfo
import argparse,hashlib,json,re,shutil,subprocess
from harness import ROOT,OUT

SEAL=OUT/'evidence-manifest.json';p=argparse.ArgumentParser();p.add_argument('--verify-only',action='store_true');args=p.parse_args()
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
assert not SEAL.exists(),'Preserve this seal; use --verify-only'
b=read(OUT/'baseline.json');integrity=read(OUT/'integrity.json');build=read(OUT/'build-result.json');browser=read(OUT/'accepted-browser-results.json')
assert integrity['passed']and browser['passed']and browser['acceptedGroups']==49
assert read(OUT/'event-audit.json')['passed']and read(OUT/'cleanup.json')['passed']
assert subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()==b['head']
for old in b['oldSeals']:
    file=ROOT/old['path'];assert sha(file)==old['sha256'];verify(read(file))
for f in build['productionInputs']:
    assert row(ROOT/f['path'])==f
    target=OUT/'after'/f['path'];target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():assert sha(target)==f['sha256']
    else:shutil.copyfile(ROOT/f['path'],target)
for f in build['builtFiles']+integrity['untouchedInputs']:assert row(ROOT/f['path'])==f
write(OUT/'step-7-handoff.json',{
    'schema':1,'completedStep':6,'nextStep':7,'coreHostHardeningCompleted':True,'allPhysicalDevicesVerified':False,
    'hostCommit':b['head'],'sourceCommit':b['sourceHead'],'runtimeFiles':46,'runtimeBytes':20332784,'originalRuntimeChanged':False,
    'manager':'src/tour/createLawsonExperience.ts','methods':['mount','retry','unmount','dispose'],
    'statusSignature':'status(state: EmbeddedProjectState, message?: string)',
    'wrongDocumentDetection':'Completed navigation missing original #app or canvas#viewport; generic error, no guessed HTTP status',
    'graphicsDetection':'Current child canvas trusted lost/restored events; listeners aborted on document replacement/unmount',
    'graphicsRecoveryBoundary':'After context restore, require explicit reload/new original document rather than trusting old API ready',
    'capabilityNotice':'Actual document.fullscreenEnabled === false; scene remains ready, explanatory notice, no pointless retry',
    'visibilityAndPageshow':'Immediately reobserve current document; preserve instance, no guide auto-resume',
    'fullOriginalEmbedded':True,'singleIframe':True,'sourceBridgeInjected':False,'sourceCSSOrAPIMutated':False,
    'acceptedCoreBrowserGroups':49,'eventAuditPassed':True,
    'engines':['Chromium 155.0.8059.79','Firefox 153.0','WebKit 26.5 Linux package'],
    'realBrowserZoom200Verified':True,'rootFont200SeparatelyVerified':True,'realCSSEnvInsetsEmulationVerified':True,'physicalNotchVerified':False,
    'nativeVisibilityParentAndChildVerified':True,'nativeVisibilityMethod':'Owned Chrome default context, connect_over_cdp(no_defaults=True), actual tab activation, hidden/visible events',
    'backgroundLoadingWaitMS':13000,'BFCacheRestoreActuallyObserved':False,'historyBackFullReloadUsable':True,
    'successfulLoadedCycles':10,'sameTaskCancelledCycles':20,'realIsolatedViteHMRPhases':['loading','ready','error','stylesheet'],
    'sourceControlsCountPreserved':41,'sourcePickCategoriesForStep7':17,'fullFunctionalParityVerified':False,
    'knownOriginalIssues':'docs/lawson-fullpage/original-issues.md','functionalBaseline':'docs/lawson-fullpage/feature-matrix.md',
    'coverageBoundaries':browser['coverageBoundaries'],
    'step7Goal':'Full original vs embedded controls/keyboard/17 picks parity, final build and run/deployment documentation; no automatic publication',
    'verification':'docs/lawson-fullpage/step-6-verification.md','handoff':'docs/lawson-fullpage/step-6-handoff.md',
    'finalBuild':'docs/evidence/lawson-fullpage-step-6/build-result.json','browserResults':'docs/evidence/lawson-fullpage-step-6/accepted-browser-results.json',
    'sourceCopies':'docs/evidence/lawson-fullpage-step-6/after/','seal':'docs/evidence/lawson-fullpage-step-6/evidence-manifest.json',
    'committed':False,'pushed':False,'published':False,
})
docs=[ROOT/f'docs/lawson-fullpage/step-6-{n}.md'for n in ['standard','verification','handoff']]
for doc in docs:
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',doc.read_text()):
        if '://'not in target and not target.startswith('#'):assert (doc.parent/target.split('#')[0]).exists(),(doc,target)
paths=set(docs)
for directory in [OUT,ROOT/'tests/lawson-fullpage-step-6']:
    paths.update(f for f in directory.rglob('*')if f.is_file()and f!=SEAL and '__pycache__'not in f.parts)
files=[row(f)for f in sorted(paths)]
seal={'schema':1,'auditId':'lawson-fullpage-step-6','createdAtShanghai':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'hostCommit':b['head'],'sourceCommit':b['sourceHead'],
    'selfExcluded':True,'productionSourcesSealedAsCopies':True,'previousSeals':b['oldSeals'],'coreHostHardeningCompleted':True,'physicalDeviceCoverageNotInvented':True,
    'acceptedBrowserGroups':49,'fileCount':len(files),'totalBytes':sum(f['bytes']for f in files),'files':files}
write(SEAL,seal);verify(seal)
print(json.dumps({'passed':True,'sealedFiles':len(files),'totalBytes':seal['totalBytes'],'acceptedCoreGroups':49,'nextStep':7},ensure_ascii=False))
