"""Final byte-identical rebuild, actual served bytes and original-video evidence.
This does not publish, commit or change product source. Visual review is separate.
"""
import hashlib,json,mimetypes,subprocess
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/evidence/garden-enhancement-step-4'
def read(n):return json.loads((OUT/n).read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):(OUT/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')

build=read('build-verification.json');candidate=build['candidateId']
assert all(sha(ROOT/n)==v for n,v in build['buildInputsSha256'].items())
with (OUT/'build.log').open('w')as log:
    subprocess.run(['npm','run','build'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
actual={str(p.relative_to(ROOT)):sha(p)for p in sorted((ROOT/'dist').rglob('*'))if p.is_file()}
assert actual==build['productionSha256']
assert all(sha(ROOT/n)==v for n,v in build['buildInputsSha256'].items())
build['finalRebuildByteIdenticalToTestedBuild']=True
build['finalRebuildSourceCount']=len(build['buildInputsSha256'])
build['finalRebuildProductionCount']=len(actual)
save('build-verification.json',build)
print('PASS final strict rebuild byte-identical',candidate,flush=True)

responses=[]
for port in [4177,4173]:
    for name,expected in actual.items():
        relative=str(Path(name).relative_to('dist'))
        with urlopen(f'http://127.0.0.1:{port}/'+quote(relative),timeout=10)as response:
            body=response.read();mime=response.headers.get_content_type()
            assert response.status==200
            assert hashlib.sha256(body).hexdigest()==expected,(port,name)
            guessed=mimetypes.guess_type(relative)[0]
            assert mime==guessed or (relative.endswith('.js')and mime in ['application/javascript','text/javascript']),(relative,mime,guessed)
            responses.append({'port':port,'path':relative,'status':200,'mime':mime,'bytes':len(body),'sha256':expected})
with urlopen('http://127.0.0.1:5173/',timeout=10)as response:
    assert response.status==200 and response.headers.get_content_type()=='text/html'
save('production-preview-verification.json',{'passed':True,'candidateId':candidate,'responses':responses,'dev5173Http200':True,'published':False})
print('PASS production and preview 36 real HTTP byte/MIME responses',flush=True)

full=read('auto-guide-recording-full.json');takeover=read('auto-guide-recording-takeover.json')
assert full['passed']and takeover['passed']and full['candidateId']==takeover['candidateId']==candidate
trace=full['actualMutationTrace'];holds=[]
for i,row in enumerate(trace):
    d=row['guide']
    if d['guidePhase']!='reading':continue
    following=next(r for r in trace[i+1:]if r['guide']['guidePhase']in ['moving','finished'])
    ready=float(d['guideReadyAt']);seconds=float(d['guideReadSeconds']);deadline=float(d['guideDeadline'])
    assert deadline>=ready+seconds*1000-.001
    assert following['at']>=deadline
    holds.append({'station':d['guideStation'],'minimumSeconds':seconds,'actualReadyAtMs':ready,'deadlineMs':deadline,'observedDepartureAtMs':following['at'],'observedHoldSeconds':(following['at']-ready)/1000})
assert [r['station']for r in holds]==['O','A1','A2','A3','B1','B2','B3','B4','C1','C2','C3','W','S99']
durations={}
for report in [full,takeover]:
    source=float(report['originalMetadata']['format']['duration']);output=float(report['outputMetadata']['format']['duration'])
    assert abs(source-output)<.12
    durations[report['kind']]={'originalSeconds':source,'mp4Seconds':output,'durationDifferenceSeconds':output-source,'fileSha256':sha(OUT/report['file'])}
save('video-timing-verification.json',{'passed':True,'candidateId':candidate,'method':'original real performance.now mutation trace; each actual departure compared with its full original deadline; full/takeover videos retain original duration with H264 conversion only','holds':holds,'durations':durations,'accelerated':False,'timeInjected':False,'hardwareFPSProof':False})

frames=[]
for station,offset in [('A2',3),('B2',3),('W',2),('S99',2)]:
    action=next(r for r in full['actions']if r['label']=='complete reading '+station)
    frames.append((full['file'],round(action['wallSeconds']+offset,3),f'video-full-{station}.png'))
frames.append((takeover['file'],10,'video-takeover-native.png'))
origins=[]
for source,seconds,target in frames:
    subprocess.run(['ffmpeg','-y','-loglevel','error','-ss',str(seconds),'-i',str(OUT/source),'-frames:v','1',str(OUT/target)],check=True)
    origins.append({'source':source,'sourceSha256':sha(OUT/source),'seconds':seconds,'frame':target,'sha256':sha(OUT/target),'operations':'decode and select one full original-resolution frame; no crop, masks, overlays, resize or retouch'})
save('video-frame-origins.json',{'candidateId':candidate,'frames':origins,'visualReviewFile':'video-frame-review.json'})
print('PASS all 13 real minimum holds, original durations and five full-frame extractions',flush=True)
