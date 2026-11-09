"""Fresh resource totals from original enhancement baseline to final candidate.
Original baseline has no guide: report resource totals, not invented matched
guide timing or a sum of historical percentage changes.
"""
import json,hashlib,tarfile,threading
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright
from step7_common import *
class Handler(SimpleHTTPRequestHandler):
    def log_message(self,*a):pass
build=json.loads((OUT/'build-verification.json').read_text());original=ROOT/'docs/evidence/garden-enhancement-step-1'
archive=json.loads((original/'baseline-archive-manifest.json').read_text());path=original/archive['file']
assert hashlib.sha256(path.read_bytes()).hexdigest()==archive['sha256']
destination=Path('/tmp/garden-enhancement-step7-original');destination.mkdir(exist_ok=True)
with tarfile.open(path)as t:t.extractall(destination,filter='data')
errors=[];rows={};servers=[];threads=[]
try:
    for directory in [destination/'dist',ROOT/'dist']:
        server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(directory)));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();servers.append(server);threads.append(thread)
    with sync_playwright()as p:
        browser=launch(p)
        for phase,server in zip(['original','final'],servers):
            context=browser.new_context(viewport={'width':1440,'height':900},device_scale_factor=1);page=context.new_page();watch(page,errors)
            load(page,f'http://127.0.0.1:{server.server_port}/?waterTime=2')
            for mode in ['pixel','native','pixel']:
                page.locator(f'.tour-actions [data-mode={mode}]').click()
                for _,h in VIEWS:visit(page,h)
            rows[phase]=[]
            for mode in ['native','pixel']:
                page.locator(f'.tour-actions [data-mode={mode}]').click()
                for key,h in [('O',0),('A2',2.54),('B2',5.95),('C2',10.05),('W',11.5)]:
                    visit(page,h);d=data(page);s=json.loads(d['rendererStats'])
                    rows[phase].append({'mode':mode,'pose':key,'time':d['sceneTime'],'position':d['cameraPosition'],'target':d['cameraTarget'],'height':d['viewHeight'],
                        'stats':{k:s[k]for k in ['geometries','textures','programs','calls','triangles']}})
            context.close();print('PASS overall resource profile',phase,flush=True)
        browser.close()
    deltas=[]
    for a,b in zip(rows['original'],rows['final']):
        assert a['position']==b['position']and a['target']==b['target']and abs(float(a['height'])-float(b['height']))<.000003
        delta={k:b['stats'][k]-a['stats'][k]for k in a['stats']}
        assert delta['geometries']==1 and delta['textures']==0 and 0<=delta['calls']<=1 and 0<=delta['triangles']<=180,delta
        deltas.append({'mode':a['mode'],'pose':a['pose'],'delta':delta})
    assert not errors,errors
    save(OUT,'overall-resource-cost.json',{'passed':True,'candidateId':build['candidateId'],'originalCandidate':'step12-95740fb789b56da7','originalGitHead':'4d564f3a79e1e4cc84f9d08b043f9ac5b83c69e3',
        'originalArchiveSha256':archive['sha256'],'profiles':rows,'deltas':deltas,'method':'fresh serial same-Chromium/software renderer1440x900DPR1, both modes/full-route prewarmed, same actual original scene time2 and camera, original/final served by identical Python static servers',
        'originalHasNoAutoGuide':True,'timingPercentagesNotSummed':True,'scope':'whole enhancement resource totals; matched final-adjustment timing is the separate Step6-versus-Step7 performance report','errors':errors,'physicalDevice':False})
finally:
    for server in servers:server.shutdown();server.server_close()
