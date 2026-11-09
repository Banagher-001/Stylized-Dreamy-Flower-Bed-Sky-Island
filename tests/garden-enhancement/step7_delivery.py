"""Freeze byte-identical final build and original-video provenance before ZIPs."""
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import quote
import hashlib,json,mimetypes,subprocess
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/evidence/garden-enhancement-step-7'
def read(name):return json.loads((OUT/name).read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,data):(OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
build=read('build-verification.json');candidate=build['candidateId']
assert all(sha(ROOT/n)==v for n,v in build['buildInputsSha256'].items())
with(OUT/'build.log').open('w')as log:subprocess.run(['npm','run','build'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
assert{str(p.relative_to(ROOT)):sha(p)for p in sorted((ROOT/'dist').rglob('*'))if p.is_file()}==build['productionSha256']
build['finalRebuildByteIdenticalToTestedBuild']=True;save('build-verification.json',build)
responses=[]
for port in [4183,4173]:
    for name,expected in build['productionSha256'].items():
        relative=Path(name).relative_to('dist').as_posix()
        with urlopen(f'http://127.0.0.1:{port}/'+quote(relative),timeout=10)as r:
            body=r.read();mime=r.headers.get_content_type();assert r.status==200 and hashlib.sha256(body).hexdigest()==expected
            assert mime==mimetypes.guess_type(relative)[0]or(relative.endswith('.js')and mime in ['application/javascript','text/javascript'])
            responses.append({'port':port,'path':relative,'status':200,'mime':mime,'sha256':expected,'bytes':len(body)})
with urlopen('http://127.0.0.1:5173/',timeout=10)as r:assert r.status==200
save('production-preview-verification.json',{'passed':True,'candidateId':candidate,'responses':responses,'dev5173Http200':True,'published':False})
full=read('recording-full.json');controls=read('recording-controls.json');endurance=read('endurance.json')
assert all(d['passed']and d['candidateId']==candidate for d in [full,controls,endurance])
assert endurance['wallSeconds']>=600 and endurance['interactionCycles']==20 and endurance['continuousOverviewEnvironmentSpan']>=150
assert all(r['observedPhaseWraps']>=1 and r['flapAndGlide']for r in endurance['birdCycles'])
trace=full['actualMutationTrace'];readings=[(i,r)for i,r in enumerate(trace)if r['guide'].get('guidePhase')=='reading'];durations=[]
assert[r['guide']['guideStation']for _,r in readings]==['O','A1','A2','A3','B1','B2','B3','B4','C1','C2','C3','W','S99']
for index,row in readings:
    d=row['guide'];later=next(r for r in trace[index+1:]if r['guide']['guidePhase']!='reading')
    assert later['at']>=float(d['guideDeadline'])-.1
    durations.append({'station':d['guideStation'],'readyAt':float(d['guideReadyAt']),'deadline':float(d['guideDeadline']),'leftAt':later['at'],'minimumSeconds':float(d['guideReadSeconds']),'actualReadingSeconds':(later['at']-float(d['guideReadyAt']))/1000})
origins=[];videos={}
for d in [full,controls]:
    original=float(d['originalMetadata']['format']['duration']);output=float(d['outputMetadata']['format']['duration']);assert abs(original-output)<.12 and not d['errors']
    videos[d['kind']]={'file':d['file'],'originalSeconds':original,'outputSeconds':output,'differenceSeconds':output-original,'sha256':sha(OUT/d['file'])}
    def time_of(text):return next(r['wallSeconds']for r in d['actions']if text in r['label'])
    selected=[(5,'opening'),(time_of('complete reading A2')+3,'about'),(time_of('complete reading W')+3,'water')]if d['kind']=='full'else[
        ((time_of('live pane opened')+time_of('live pane real'))/2,'live'),(time_of('ten-minute endurance begins')+100,'clouds'),(time_of('completed20 real interaction')+3,'repeat')]
    for seconds,label in selected:
        assert 0<seconds<output
        name=f'video-{d["kind"]}-{label}.png'
        subprocess.run(['ffmpeg','-y','-loglevel','error','-ss',str(seconds),'-i',str(OUT/d['file']),'-frames:v','1',str(OUT/name)],check=True)
        origins.append({'frame':name,'sha256':sha(OUT/name),'source':d['file'],'sourceSha256':sha(OUT/d['file']),'seconds':seconds,'operations':'decode/select one full1440x900 source frame; no crop/mask/retouch/overlays'})
save('video-timing-verification.json',{'passed':True,'candidateId':candidate,'videos':videos,'actualReadingHolds':durations,'enduranceWallSeconds':endurance['wallSeconds'],
    'continuousOverviewEnvironmentSpan':endurance['continuousOverviewEnvironmentSpan'],'cloudCycleSeconds':32/.22,'birdPeriodsSeconds':[48,54,61],
    'method':'actual guide transition timestamps and original environment time; explicit600wall-second endurance after warmup;150continuous original environment seconds; original video durations retained','accelerated':False,'hardwareFPSProof':False})
save('video-frame-origins.json',{'candidateId':candidate,'frames':origins,'visualReviewFile':'video-frame-review.json'})
print('PASS final identical build;36 actual HTTP files;13original reading holds;600s endurance;6full-frame origins')
