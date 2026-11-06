"""Seal current Step9 receipts against the final runtime and original file manifest."""
import hashlib
from datetime import datetime,timezone
from step9_common import *
def receipt(name):return json.loads((OUT/name).read_text())
runtime={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest()for f in(ROOT/'src').rglob('*.ts')}
counts={};versions={}
for engine in ['chromium','firefox','webkit']:
 for kind,name in [('orb',f'orb-verification-{engine}.json'),('chapter',f'regression-chapter/verification-{engine}.json')]:
  result=receipt(name);assert result['passed']and all(c['passed']for c in result['checks']);counts[kind+'-'+engine]=len(result['checks']);versions[engine]=result['version']
for kind,name in [('about','regression-about/about-verification-chromium.json'),('films','regression-films/verification-chromium.json'),('native','native-recovery.json')]:
 result=receipt(name);assert result['passed']and all(c['passed']for c in result['checks']);counts[kind]=len(result['checks'])
fallback=['fallback-decoration-font.json','fallback-no-webgl.json','fallback-cover.json','fallback-video.json'];assert all(receipt('fallback/'+name)['passed']for name in fallback);counts['fallback']=len(fallback)
for name in ['build-verification.json','cover-provenance.json','demo-recording.json']:
 assert receipt(name)['runtimeSourceSha256']==runtime,(name,'source changed after proof')
assert receipt('cover-provenance.json')['assetSha256']==hashlib.sha256((ROOT/'src/assets/courtyard-orb-cover.webp').read_bytes()).hexdigest()
assert receipt('build-verification.json')['exitCode']==0
assert not receipt('demo-recording.json')['unhandledExceptions']
for name in ['geometry-physics.json','scope-guard.json','paired-scene-isolation.json','project-pause-diagnostic.json']:assert receipt(name)['passed'],name
geometry=receipt('geometry-physics.json');assert geometry['geometrySamples']==30001 and geometry['sampledRangeSeconds']==[0,600]
assert all(10<=s['whiteDominantPercent']<=20 for s in receipt('highlight-coverage.json')['samples'])
paired=receipt('paired-scene-isolation.json');assert len(paired['pairs'])==30 and all(r['outsideEffectsMaximumChannelDifference']==0 and r['legacyPixelsExact']for r in paired['pairs'])
assert len(paired['defaultReference'])==2 and all(r['pixelsExact']for r in paired['defaultReference'])
for phase in ['before','after']:
 assert len(receipt('latency-'+phase+'.json')['samplesMs'])==30
 assert len(receipt('baseline-'+phase+'.json')['views'])==84
old=receipt('latency-before.json');new=receipt('latency-after.json');change=100*(new['p95Ms']/old['p95Ms']-1);assert change<=10,('latency requires investigation',change)
assert len(receipt('regression-runs.json'))==10 and all(r['exitCode']==0 for r in receipt('regression-runs.json'))
build=receipt('build-verification.json');cover=receipt('cover-provenance.json')
assetBuild=list((ROOT/'dist/assets').glob('courtyard-orb-cover-*.webp'));assert len(assetBuild)==1 and hashlib.sha256(assetBuild[0].read_bytes()).hexdigest()==cover['assetSha256']
summary={'passed':True,'completedStep':9,'nextStep10Started':False,'generatedAtUtc':datetime.now(timezone.utc).isoformat(),'versions':versions,'checkGroups':counts,'functionalGroups':sum(v for k,v in counts.items()if k not in ['native','fallback']),'geometrySamples':geometry['geometrySamples'],'trajectoryPoints':geometry['flightSamples'],'scopeOriginalFiles':receipt('scope-guard.json')['originalFiles'],'scenePairs':30,'legacyExactPairs':30,'defaultExactModes':2,'latency':{'beforeP95Ms':old['p95Ms'],'afterP95Ms':new['p95Ms'],'changePercent':change,'beforeMaxMs':old['maxMs'],'afterMaxMs':new['maxMs'],'samplesPerVersion':30,'hardwareFPSProof':False},'finalRuntimeSourceSha256':runtime,'currentCoverSha256':cover['assetSha256'],'publishedOrDeployed':False,'gitCommitOrPush':False,'releaseRepackaged':False,'deviceLimits':['software graphics','simulated portrait','Linux GTK WebKit, not Apple Safari','physical devices/trackpad/APZ/landscape/200% text remain in later steps']}
save('summary.json',summary);print('PASS: final source sealed;',summary['functionalGroups'],'functional groups;',counts['native'],'native;',counts['fallback'],'fallback; p95 change',round(change,2),'%',flush=True)
