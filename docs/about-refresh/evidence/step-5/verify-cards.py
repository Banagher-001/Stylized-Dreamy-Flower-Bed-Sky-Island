from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from threading import Thread
import json,hashlib,argparse,shutil,traceback
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).parent
ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);args=ap.parse_args();run=OUT/args.run;run.mkdir(exist_ok=False)
html=ROOT/'docs/about-refresh/step-5-card-preview.html';payload=html.read_bytes();report={'startedAtShanghai':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'htmlSHA256':hashlib.sha256(payload).hexdigest(),'checks':[],'events':[],'complete':False}
save=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
shutil.copy2(__file__,run/'verify-cards.py.txt');shutil.copy2(OUT/'review-build.json',run/'build.json')
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  if self.path=='/favicon.ico':self.send_response(204);self.end_headers();return
  self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers();self.wfile.write(payload)
server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=Thread(target=server.serve_forever,daemon=True);thread.start()
MEASURE=r'''()=>{const api=window.__toolCardReview,c=api.specimen.element,front=c.querySelector('.ar-card-front');const box=e=>e.getBoundingClientRect().toJSON();return {...api.capture(),root:box(c),front:box(front),faceCount:c.querySelectorAll('[data-card-face]').length,frontInert:front.inert,frontHidden:front.getAttribute('aria-hidden'),depthCSS:getComputedStyle(c).getPropertyValue('--ar-card-depth'),mark:{kind:c.dataset.markKind,ready:c.dataset.markState,complete:c.querySelector('img').complete,naturalWidth:c.querySelector('img').naturalWidth},closure:(()=>{const sides=[...c.querySelectorAll('.ar-card-side')];let gap=0;const pts=sides.map(e=>{const t=new DOMMatrixReadOnly(getComputedStyle(e).transform),w=parseFloat(getComputedStyle(e).width),h=parseFloat(getComputedStyle(e).height);return [new DOMPoint(0,0,0).matrixTransform(t),new DOMPoint(w,0,0).matrixTransform(t),new DOMPoint(0,h,0).matrixTransform(t),new DOMPoint(w,h,0).matrixTransform(t)]});for(let i=0;i<pts.length;i++){const a=pts[i],b=pts[(i+1)%pts.length];gap=Math.max(gap,Math.hypot(a[1].x-b[0].x,a[1].y-b[0].y,a[1].z-b[0].z),Math.hypot(a[3].x-b[2].x,a[3].y-b[2].y,a[3].z-b[2].z))}return {maximumSeamGap:gap,frontZ:new DOMMatrixReadOnly(getComputedStyle(front).transform).m43,backZ:new DOMMatrixReadOnly(getComputedStyle(c.querySelector('.ar-card-back')).transform).m43}})(),styles:[...c.querySelectorAll('.ar-card-position,.ar-card-reading,.ar-card-orientation,.ar-card-entity')].map(e=>({class:e.className,preserve:getComputedStyle(e).transformStyle})),text:[...c.querySelectorAll('.ar-card-front h3,.ar-card-front p,.ar-card-front li,.ar-card-front button')].filter(e=>e.getClientRects().length).map(e=>({text:e.textContent,box:box(e),scrollHeight:e.scrollHeight,clientHeight:e.clientHeight,font:parseFloat(getComputedStyle(e).fontSize)})),domWidth:document.documentElement.scrollWidth,viewport:[innerWidth,innerHeight]}}'''
try:
 with sync_playwright() as play:
  browser=play.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);report['version']=browser.version
  try:
   page=browser.new_page(viewport={'width':1440,'height':1050});page.on('pageerror',lambda e:report['events'].append(str(e)));page.on('console',lambda m:report['events'].append(m.text) if m.type=='error' else None)
   page.goto(f'http://127.0.0.1:{server.server_port}/',wait_until='load');page.wait_for_function('!!window.__toolCardReview')
   def case(name,id,pose):
    entry={'id':name,'tool':id,'pose':pose}
    try:
     page.select_option('select',id);page.locator('[data-card-review-pose='+pose+']').click();page.wait_for_function('window.__toolCardReview.specimen.element.dataset.geometryReady==="true"&&window.__toolCardReview.specimen.element.dataset.markState==="ready"');page.wait_for_timeout(90)
     m=page.evaluate(MEASURE);save(run/(name+'-measurement.json'),m)
     assert m['faceCount']==10 and m['depth']==6
     assert m['closure']['maximumSeamGap']<.04,m['closure']
     assert abs(m['closure']['frontZ'])<.001 and abs(m['closure']['backZ']+6)<.001,m['closure']
     assert all(s['preserve']=='preserve-3d' for s in m['styles'])
     assert m['mark']['complete'] and m['mark']['naturalWidth']>0
     assert m['domWidth']<=m['viewport'][0]+1
     if pose in ['front','detail']:
      assert not m['frontInert']
      for text in m['text']:assert text['scrollHeight']<=text['clientHeight']+2,(text['text'],text)
     if pose in ['back','side']:assert m['frontInert'] and m['frontHidden']=='true'
     if pose=='back':assert page.locator('.ar-review-specimen-slot .ar-card-back svg text').text_content()=='sakan'
     assert not report['events'],report['events']
     page.locator('.ar-review-theatre').screenshot(path=str(run/(name+'.png')))
     entry.update(status='通过',measurement=name+'-measurement.json',screenshot=name+'.png')
    except Exception as e:
     entry.update(status='失败',error=str(e),traceback=traceback.format_exc());page.screenshot(path=str(run/(name+'-failure.png')))
    report['checks'].append(entry);save(run/'browser.json',report)
   for pose in ['front','quarter','side','back','detail','left','right']:case('sample-'+pose,'midjourney',pose)
   ids=page.locator('select option').evaluate_all('(es)=>es.map(e=>e.value)')
   assert len(ids)==22
   for id in ids:
    case(id+'-front',id,'front');case(id+'-detail',id,'detail')
   for id in ['comfyui','kling','blender']:
    case(id+'-quarter',id,'quarter');case(id+'-back',id,'back')
   page.select_option('select','midjourney');page.locator('[data-card-review-pose=front]').click();page.wait_for_timeout(250)
   stage=page.locator('.ar-review-theatre');before=stage.screenshot();page.wait_for_timeout(500);after=stage.screenshot()
   idle={'sameRenderedImage':hashlib.sha256(before).hexdigest()==hashlib.sha256(after).hexdigest(),'cssAnimations':page.evaluate('document.getAnimations().length'),'canvasCount':page.locator('canvas').count()}
   assert idle['sameRenderedImage'] and idle['cssAnimations']==0 and idle['canvasCount']==0,idle
   save(run/'idle.json',idle);report['checks'].append({'id':'static-idle','status':'通过','evidence':'idle.json'})
   page.set_viewport_size({'width':320,'height':740});case('narrow-front','midjourney','front');case('narrow-detail','substance-painter','detail')
   page.set_viewport_size({'width':800,'height':600});page.locator('[data-card-review-large]').click();case('large-text-detail','vibe-coding','detail')
   page.locator('[data-card-review-large]').click();page.set_viewport_size({'width':1440,'height':1050})
   page.locator('[data-card-review-pose=front]').click();page.screenshot(path=str(run/'first-four-gallery.png'),full_page=True)
   report['complete']=all(c['status']=='通过' for c in report['checks'])
  finally:browser.close();report['browserClosed']=True
finally:
 server.shutdown();server.server_close();thread.join();report['serverClosed']=not thread.is_alive();save(run/'browser.json',report)
print(json.dumps({'checks':len(report['checks']),'passed':sum(c['status']=='通过' for c in report['checks']),'complete':report['complete'],'failures':[{'id':c['id'],'error':c.get('error')} for c in report['checks'] if c['status']!='通过']},ensure_ascii=False))
if not report['complete']:raise SystemExit(1)
