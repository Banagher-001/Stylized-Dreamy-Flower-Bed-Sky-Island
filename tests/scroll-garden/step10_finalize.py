"""Seal current Step10 receipts against the final TS/CSS runtime and Step9 baseline."""
import hashlib
from datetime import datetime,timezone
from step10_common import *
def receipt(name):return json.loads((OUT/name).read_text())
runtime={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest()for f in(ROOT/'src').rglob('*')if f.suffix in ['.ts','.css']}
counts={};versions={};uiContrast={}
for engine in ['chromium','firefox','webkit']:
 for kind,name in [('journey',f'journey-verification-{engine}.json'),('chapter',f'regression-chapter/verification-{engine}.json'),('about',f'regression-about/about-verification-{engine}.json'),('films',f'regression-films/verification-{engine}.json')]:
  result=receipt(name);assert result['passed']and all(c['passed']for c in result['checks']);counts[kind+'-'+engine]=len(result['checks']);versions[engine]=result['version']
  if kind=='journey':
   samples=next(c['evidence']for c in result['checks']if c['check'].startswith('new heading'));uiContrast[engine]=min(c['minimumRatio']for pose in samples for c in pose['contrast'])
for name in ['build-verification.json','demo-recording.json']:assert receipt(name)['runtimeSourceSha256']==runtime,(name,'runtime changed after proof')
assert receipt('build-verification.json')['exitCode']==0
assert not receipt('demo-recording.json')['unhandledExceptions']and receipt('demo-recording.json')['decoderReleased']
for name in ['geometry-continuity.json','scope-guard.json','paired-scene-isolation.json','webkit-scroll-precision.json']:assert receipt(name)['passed'],name
native=receipt('native-recovery.json');assert native['passed']and len(native['checks'])==9
fallback=['fallback-decoration-font.json','fallback-no-webgl.json','fallback-cover.json','fallback-video.json'];assert all(receipt('fallback/'+name)['passed']for name in fallback)
paired=receipt('paired-scene-isolation.json');assert len(paired['pairs'])==96 and all(r['pixelsExact']and not r['maskUsed']for r in paired['pairs'])
assert len(paired['defaultReference'])==2 and all(r['pixelsExact']for r in paired['defaultReference'])
geometry=receipt('geometry-continuity.json');assert geometry['geometricSamples']==15015 and geometry['stageCount']==16 and geometry['totalH']==12.3 and len(geometry['protectedViews'])==78
for phase in ['before','after']:
 assert len(receipt('latency-'+phase+'.json')['samplesMs'])==30 and len(receipt('latency-'+phase+'.json')['routes'])==5
 assert len(receipt('baseline-'+phase+'.json')['views'])==len(VIEWS)*6
old=receipt('latency-before.json');new=receipt('latency-after.json');change=100*(new['p95Ms']/old['p95Ms']-1);assert change<=10,('performance requires investigation',change)
for a,b in zip(receipt('baseline-before.json')['fullWarmCaches'],receipt('baseline-after.json')['fullWarmCaches']):assert all(a[k]==b[k]for k in ['geometries','textures','programs','calls']),(a,b)
runs=receipt('regression-runs.json');assert len(runs)==14 and all(r['exitCode']==0 for r in runs)
summary={'passed':True,'completedStep':10,'step11Or12Started':False,'generatedAtUtc':datetime.now(timezone.utc).isoformat(),'versions':versions,'checkGroups':counts,'functionalGroups':sum(counts.values()),'nativeRecoveryGroups':len(native['checks']),'fallbackGroups':len(fallback),'geometrySamples':15015,'protectedCameraChecks':78,'unchangedFullScenePairs':96,'defaultReferenceExactModes':2,'originalFileCount':receipt('scope-guard.json')['originalFiles'],'minimumGlobalUIContrastByEngine':uiContrast,'latency':{'beforeP95Ms':old['p95Ms'],'afterP95Ms':new['p95Ms'],'changePercent':change,'beforeMaxMs':old['maxMs'],'afterMaxMs':new['maxMs'],'perVersionSamples':30,'hardwareFPSProof':False},'finalRuntimeSourceSha256':runtime,'publishedOrDeployed':False,'gitCommitOrPush':False,'releaseRepackaged':False,'preservedCover':'Step9 actual O cover; source/provenance unchanged; fixed O scene pixels exact','limits':['software rendering','simulated portrait','GTK WebKit is not Apple Safari','full mobile/landscape/physical device/trackpad/APZ/200% text in later steps']}
save('summary.json',summary);print('PASS: final Step10 runtime sealed;',summary['functionalGroups'],'functional,9native,4fallback;96scene pairs; p95 change',round(change,2),'%',flush=True)
