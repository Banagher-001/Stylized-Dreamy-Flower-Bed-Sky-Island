"""Separate intentional failures from unexpected errors in adopted browser runs."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/evidence/lawson-fullpage-step-7'
read=lambda p:json.loads(p.read_text());accepted=read(OUT/'accepted-browser-results.json')
events=[]
for report in sorted({c['report']for c in accepted['cases']}):
    d=read(OUT/report);adopted={c['case']for c in accepted['cases']if c['report']==report}
    if 'events'in d:
        events.extend({'report':report,**e}for e in d['events']if e['case']in adopted)
    else:
        for key,kind in [('pageErrors','pageerror'),('console','console'),('requestsFailed','requestfailed'),('httpErrors','response')]:
            for e in d.get(key,[]):
                if e.get('case')not in adopted:continue
                item={'report':report,'kind':kind,**e}
                if key=='console':item['level']=e['type']
                if key=='requestsFailed':item['text']=e['failure']
                events.append(item)
def expected(e):
    kind=e['kind'];text=e.get('text','');url=e.get('url','');case=e['case']
    if kind=='requestfailed'and text=='net::ERR_ABORTED'and any(p in url for p in ['/assets/','/experiments/lawson/','/original/']):return 'intentional document/media lifecycle cancellation'
    if case in ['READINESS.retry','recovery original fatal retry and host retry']:
        if kind=='requestfailed'and text=='net::ERR_FAILED'and url.endswith('/assets/models/lawson_scene.glb'):return 'explicit main-model fetch failure injection'
        if kind=='console'and('net::ERR_FAILED'in text or('[Lawson] fatal:'in text and'lawson_scene.glb'in text)):return 'original error reporting for explicit failed model'
    return None
warnings=[e for e in events if e['kind']=='console'and e.get('level')=='warning']
errors=[e for e in events if e not in warnings];intentional=[];unexpected=[]
for e in errors:
    reason=expected(e)
    (intentional if reason else unexpected).append({**e,**({'expectedReason':reason}if reason else{})})
data={'passed':not unexpected,'adoptedReports':sorted({c['report']for c in accepted['cases']}),'expectedFaultAndLifecycleErrors':intentional,'warnings':warnings,'unexpectedErrors':unexpected,'failedProbeReportsNotReclassifiedAsProductPasses':True,'normalLogsSilenced':False}
(OUT/'event-audit.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'passed':not unexpected,'intentionalErrors':len(intentional),'warnings':len(warnings),'unexpected':unexpected[:5]},ensure_ascii=False))
raise SystemExit(0 if not unexpected else 1)
