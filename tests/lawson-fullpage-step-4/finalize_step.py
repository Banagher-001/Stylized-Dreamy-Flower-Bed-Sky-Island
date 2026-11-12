"""Seal this completed step, or verify its immutable evidence copies."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,re,shutil,subprocess

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/evidence/lawson-fullpage-step-4'
SEAL=OUT/'evidence-manifest.json'
parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())
def row(path):return {'path':path.relative_to(ROOT).as_posix(),'bytes':path.stat().st_size,'sha256':sha(path)}
def write(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def verify(seal):
    assert len(seal['files'])==seal['fileCount']
    for f in seal['files']:assert row(ROOT/f['path'])==f,f['path']
    assert sum(f['bytes']for f in seal['files'])==seal['totalBytes']

if args.verify_only:
    seal=read(SEAL);verify(seal)
    print(json.dumps({'passed':True,'sealedFiles':seal['fileCount'],'totalBytes':seal['totalBytes'],'sealSHA256':sha(SEAL)}))
    raise SystemExit(0)
assert not SEAL.exists(),'Preserve the completed seal; use --verify-only'
baseline=read(OUT/'baseline.json');integrity=read(OUT/'integrity.json')
build=read(OUT/'build-result.json');browser=read(OUT/'accepted-browser-results.json')
assert integrity['passed']and browser['passed']and browser['acceptedGroups']==18
assert len({c['name']for c in browser['groups']})==18
assert all(c['passed']for c in browser['groups'])
assert build['log']=='build-5.log'and build['exitCode']==0 and build['includesTypecheck']
assert read(OUT/'cleanup.json')['passed']
assert subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()==baseline['head']
for previous in baseline['oldSeals']:
    path=ROOT/previous['path'];assert sha(path)==previous['sha256'];verify(read(path))
for f in build['productionInputs']:
    assert row(ROOT/f['path'])==f,f['path']
    target=OUT/'after'/f['path'];target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():assert sha(target)==f['sha256']
    else:shutil.copyfile(ROOT/f['path'],target)
for f in build['builtFiles']:assert row(ROOT/f['path'])==f
for f in integrity['untouchedInputs']:assert row(ROOT/f['path'])==f

write(OUT/'step-5-handoff.json',{
    'schema':1,'completedStep':4,'nextStep':5,'hostCommit':baseline['head'],
    'sourceCommit':integrity['sourceHead'],'hostUIImplemented':True,
    'actualIframeIntegrationImplemented':False,'preparedStateHonest':True,
    'runtimeRoot':'public/experiments/lawson','entryPath':'experiments/lawson/index.html',
    'runtimeFileCount':46,'runtimeBytes':20332784,
    'runtimeManifestSHA256':integrity['runtimeManifestSHA256'],
    'projectModule':'src/tour/projectContent.ts','viewerModule':'src/tour/createProjectViewer.ts',
    'coordinationModule':'src/tour/startTourPrototype.ts',
    'defaultProjectId':'lawson','selectedIdOwner':'createExperimentReader.projectId',
    'openSignature':'open(projectId: ProjectId, tab: ProjectTab, trigger?: HTMLElement)',
    'activeState':'projectViewer.active: Readonly<{id, tab}> | undefined',
    'mountGetter':'projectViewer.embeddedMount','mountSelector':'.tour-project-embed-mount',
    'mountNodeStable':True,'courtyardBoundsGetter':'projectViewer.liveBounds',
    'statusMethod':'projectViewer.setEmbeddedStatus(state, message?)',
    'statusStates':['prepared','loading','slow','error','ready'],
    'statusMethodDoesNotCreateRetryUIOrValidateInstanceGeneration':True,
    'entryResolver':'resolveProjectEntry(projectId)','entryResolverModule':'src/tour/projectContent.ts',
    'verifiedPrefixes':['/','/Stylized-Dreamy-Flower-Bed-Sky-Island/'],
    'lifecycleHooks':['open(active)','change(active)','close()'],
    'openHookBeforeDialogShowModal':True,'closeHookAfterActiveCleared':True,
    'mountOnlyWhen':"active?.id === 'lawson' && active.tab === 'live'",
    'unmountWhen':['archive','other project','closed','dispose'],
    'futureAdapter':'src/tour/createLawsonExperience.ts (not yet created)',
    'adapterMethods':['mount','retry','unmount','dispose'],
    'originalSignals':['window.__LAWSON__.ready','window.__LAWSON__.error','body.dataset.ready','#fatal visibility'],
    'errorBeforeReady':True,'htmlLoadIsNotReady':True,'slowAfterApproxSeconds':12,
    'newBridgeInjected':False,'originalRuntimeChanged':False,
    'preserveNativeFullScreenAndPointerLock':True,'iframeFocusedEscapeNotYetTested':True,
    'hostGardenCoveredDrawsPerSecond':0,'backgroundOriginalRequestsBeforeExplicitOpen':0,
    'acceptedHostBrowserGroups':18,'build':'build-5.log',
    'verificationDoc':'docs/lawson-fullpage/step-4-verification.md',
    'handoffDoc':'docs/lawson-fullpage/step-4-handoff.md',
    'evidenceSeal':'docs/evidence/lawson-fullpage-step-4/evidence-manifest.json',
    'currentProductionHashes':'docs/evidence/lawson-fullpage-step-4/build-result.json',
    'sealedProductionCopies':'docs/evidence/lawson-fullpage-step-4/after/',
    'knownOriginalIssues':'docs/lawson-fullpage/original-issues.md',
    'remaining':'Actual iframe and ready/error/retry lifecycle in step5; devices/faults in step6; full original feature parity in step7.',
    'committed':False,'pushed':False,'published':False,
})

docs=[ROOT/f'docs/lawson-fullpage/step-4-{name}.md'for name in ['standard','verification','handoff']]
for doc in docs:
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',doc.read_text()):
        if '://'not in target and not target.startswith('#'):
            assert (doc.parent/target.split('#')[0]).exists(),(doc,target)
paths=set(docs)
for directory in [OUT,ROOT/'tests/lawson-fullpage-step-4']:
    paths.update(p for p in directory.rglob('*')if p.is_file()and p!=SEAL and '__pycache__'not in p.parts)
files=[row(p)for p in sorted(paths)]
seal={'schema':1,'auditId':'lawson-fullpage-step-4','createdAtUTC':datetime.now(timezone.utc).isoformat(),
    'sourceCommit':integrity['sourceHead'],'hostCommit':baseline['head'],'selfExcluded':True,
    'previousSeals':baseline['oldSeals'],'acceptedBrowserGroups':18,
    'productionSourceSealedAsCopies':True,'runtimeOriginalUnchanged':True,
    'fileCount':len(files),'totalBytes':sum(f['bytes']for f in files),'files':files}
write(SEAL,seal);verify(seal)
print(json.dumps({'passed':True,'sealedFiles':len(files),'totalBytes':seal['totalBytes'],
    'acceptedBrowserGroups':18,'sourceAndHistoricalSealsPreserved':True,'actualIframeDeferredToStep5':True},ensure_ascii=False))
