"""Final byte-identical rebuild, actual served files and original-video frames.
No source, remote, release or Git changes. Direct visual review is separate.
"""
import hashlib,json,mimetypes,subprocess
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/evidence/garden-enhancement-step-5'
def read(n):return json.loads((OUT/n).read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):(OUT/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
build=read('build-verification.json');candidate=build['candidateId']
assert all(sha(ROOT/n)==v for n,v in build['buildInputsSha256'].items())
with(OUT/'build.log').open('w')as log:subprocess.run(['npm','run','build'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
assert {str(p.relative_to(ROOT)):sha(p)for p in sorted((ROOT/'dist').rglob('*'))if p.is_file()}==build['productionSha256']
assert all(sha(ROOT/n)==v for n,v in build['buildInputsSha256'].items())
build['finalRebuildByteIdenticalToTestedBuild']=True;save('build-verification.json',build)
responses=[]
for port in [4179,4173]:
    for name,expected in build['productionSha256'].items():
        relative=str(Path(name).relative_to('dist'))
        with urlopen(f'http://127.0.0.1:{port}/'+quote(relative),timeout=10)as response:
            body=response.read();mime=response.headers.get_content_type()
            assert response.status==200 and hashlib.sha256(body).hexdigest()==expected,(port,name)
            assert mime==mimetypes.guess_type(relative)[0]or(relative.endswith('.js')and mime in ['application/javascript','text/javascript'])
            responses.append({'port':port,'path':relative,'status':200,'mime':mime,'sha256':expected,'bytes':len(body)})
with urlopen('http://127.0.0.1:5173/',timeout=10)as response:assert response.status==200
save('production-preview-verification.json',{'passed':True,'candidateId':candidate,'responses':responses,'dev5173Http200':True,'published':False})
origins=[];durations={}
for kind in ['overview','loop-water']:
    d=read(f'clouds-recording-{kind}.json');assert d['passed']and d['candidateId']==candidate
    original=float(d['originalMetadata']['format']['duration']);output=float(d['outputMetadata']['format']['duration'])
    assert abs(original-output)<.12
    durations[kind]={'originalSeconds':original,'mp4Seconds':output,'differenceSeconds':output-original,'sha256':sha(OUT/d['file'])}
    selected=[(5,'early'),(min(output-2,next(r['wallSeconds']for r in d['actions']if 'reaches 32' in r['label'])+1),'crossing')]if kind=='overview'else[(5,'loop'),(next(r['wallSeconds']for r in d['actions']if 'water closeup' in r['label'])-.5,'water')]
    for seconds,label in selected:
        target=f'video-{kind}-{label}.png'
        subprocess.run(['ffmpeg','-y','-loglevel','error','-ss',str(seconds),'-i',str(OUT/d['file']),'-frames:v','1',str(OUT/target)],check=True)
        origins.append({'source':d['file'],'sourceSha256':sha(OUT/d['file']),'seconds':seconds,'frame':target,'sha256':sha(OUT/target),'operations':'decode/select one full original-resolution frame; no crop/mask/resize/overlays/retouch'})
overview=read('clouds-recording-overview.json')['actions']
start=float(overview[0]['scene']['sceneTime']);end=float(overview[-2]['scene']['sceneTime'])
assert end-start>60 and overview[0]['scene']['guideState']=='manual'
loop=read('clouds-recording-loop-water.json')['actions']
assert float(loop[0]['scene']['sceneTime'])==144
cross=next(r for r in loop if 'crosses cloud cycle' in r['label'])
assert float(cross['scene']['sceneTime'])>32/.22
save('video-timing-verification.json',{'passed':True,'candidateId':candidate,'durations':durations,'overviewEnvironmentStart':start,'overviewEnvironmentEnd':end,'overviewObservedWallSeconds':overview[-2]['wallSeconds']-overview[0]['wallSeconds'],'crossingEnvironmentTime':cross['scene']['sceneTime'],'cycleSeconds':32/.22,'method':'normal root overview advances more than60 original environment seconds; loop clip explicitly initializes at144 then crosses repeat in original playback; original durations unchanged; no clock/phase overrides','accelerated':False,'hardwareFPSProof':False})
save('video-frame-origins.json',{'candidateId':candidate,'frames':origins,'visualReviewFile':'video-frame-review.json'})
print('PASS final identical build,36 actual HTTP files,original video timing and4full-frame origins')
