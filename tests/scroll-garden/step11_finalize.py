"""Seal Step11's actual acceptance receipts and retain explicit hardware limits."""
import hashlib
from datetime import datetime,timezone
from step11_common import *
runtime={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest()for f in(ROOT/'src').rglob('*')if f.suffix in ['.ts','.css']}
def read(name):return json.loads((OUT/name).read_text())
counts={};versions={}
for engine in ['chromium','firefox','webkit']:
 for kind,name in [('browser',f'browser-{engine}.json'),('dialogs',f'dialogs-{engine}.json'),('renderer',f'renderer-{engine}.json'),('about',f'regression-about/about-verification-{engine}.json'),('films',f'regression-films/verification-{engine}.json'),('chapter',f'regression-chapter/verification-{engine}.json')]:
  r=read(name);assert r['passed']and r['runtimeSourceSha256']==runtime,(name,'not final runtime')
  counts[kind+'-'+engine]=len(r['checks']);versions[engine]=r.get('version',versions.get(engine))
for name in ['native-zoom.json','native-recovery.json','overlay-resize.json','media-faults.json','geometry-continuity.json','paired-scene-isolation.json','demo-recording.json','build-verification.json']:
 r=read(name);assert r['passed']and r['runtimeSourceSha256']==runtime,(name,'final-runtime receipt missing')
assert all(x['exitCode']==0 for group in ['browser','legacy','final']for x in read('runs-'+group+'.json'))
paired=read('paired-scene-isolation.json');assert len(paired['pairs'])==108 and all(x['pixelsExact']and not x['maskUsed']for x in paired['pairs']);assert len(paired['defaultReference'])==2
geometry=read('geometry-continuity.json');assert geometry['stageCount']==16 and geometry['totalH']==12.3 and geometry['geometricSamples']==15015
old,new=read('latency-before.json'),read('latency-after.json');assert len(old['samplesMs'])==len(new['samplesMs'])==30;change=100*(new['p95Ms']/old['p95Ms']-1);assert change<=10,('controlled performance regression',change)
for a,b in zip(read('baseline-before.json')['fullWarmCaches'],read('baseline-after.json')['fullWarmCaches']):assert all(a[k]==b[k]for k in ['geometries','textures','programs','calls']),(a,b)
for rel,digest in read('build-verification.json')['buildSha256'].items():assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==digest,rel
assert read('scope-guard.json')['passed']
limits=['No physical iOS Safari / Android Chrome','No physical notch, system browser-toolbar or OS text-size proof','No actual VoiceOver / TalkBack screen-reader run','No physical trackpad / Firefox APZ smoothness or hardware FPS proof','GTK fixedLayout emulation has a viewport/screen rotation lag: rotation uses touch-enabled real CSS layout viewports; separate fixed is_mobile cases tested; mobile WebKit wheel API explicitly unavailable, PageDown and normal-layout wheel checked instead','Real personal AI films and contact links remain not supplied; website design samples and early courtyard clip remain labelled']
summary={'passed':True,'completedStep':11,'completionScope':'implementation and all executable cloud-environment acceptance; physical-device review remains pending','step12Started':False,'generatedAtUtc':datetime.now(timezone.utc).isoformat(),'versions':versions,'checkGroups':counts,'functionalGroups':sum(counts.values()),'nativeRecoveryGroups':len(read('native-recovery.json')['checks']),'nativeZoomCases':len(read('native-zoom.json')['results']),'modalResizeEngines':len(read('overlay-resize.json')['checks']),'mediaFaultEngines':len(read('media-faults.json')['checks']),'geometrySamples':geometry['geometricSamples'],'exactScenePairs':108,'exactDefaultReferenceModes':2,'protectedOriginalFiles':read('scope-guard.json')['baselineFiles'],'latency':{'beforeP95Ms':old['p95Ms'],'afterP95Ms':new['p95Ms'],'changePercent':change,'beforeMaxMs':old['maxMs'],'afterMaxMs':new['maxMs'],'perVersionSamples':30,'hardwareFPSProof':False},'recordings':[{'file':r['name']+'.mp4','seconds':float(r['outputMetadata']['format']['duration']),'viewport':r['viewport']}for r in read('demo-recording.json')['recordings']],'runtimeSourceSha256':runtime,'publishedOrDeployed':False,'gitCommitOrPush':False,'releaseRepackaged':False,'limits':limits}
save('summary.json',summary);print(json.dumps({k:summary[k]for k in ['passed','functionalGroups','nativeRecoveryGroups','nativeZoomCases','modalResizeEngines','exactScenePairs','latency','recordings']},ensure_ascii=False,indent=2))
