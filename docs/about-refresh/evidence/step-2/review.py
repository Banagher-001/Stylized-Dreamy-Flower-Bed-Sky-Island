"""Check actual static layout geometry and native review controls; no production app."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import argparse, hashlib, json, os, shutil, socket, threading, traceback
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[4]
DOC = ROOT / 'docs/about-refresh'
OUT = Path(__file__).parent
parser = argparse.ArgumentParser()
parser.add_argument('--run', required=True)
parser.add_argument('--suite', choices=['smoke', 'matrix'], default='smoke')
parser.add_argument('--only', default='')
args = parser.parse_args()
folder = OUT / args.run
folder.mkdir(exist_ok=False)
for file in ['review.py', 'build-preview.py', 'preview-template.html']:
    shutil.copyfile(OUT / file, folder / (file + '.txt'))

def now():
    return datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()

def save(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')

payload = (DOC / 'step-2-layout-preview.html').read_bytes()
report = {'startedAtShanghai': now(), 'suite': args.suite, 'engine': 'chromium',
          'htmlSHA256': hashlib.sha256(payload).hexdigest(), 'checks': [], 'requests': [],
          'events': [], 'externalAttempts': [], 'productionAppStarted': False,
          'physicalDevice': False, 'originalTimingModified': False}

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        path = self.path.split('?')[0]
        report['requests'].append({'path': self.path, 'method': 'GET'})
        if path == '/step-2-layout-preview.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(payload)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(payload)
        elif path == '/favicon.ico':
            self.send_response(204)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

MEASURE = r'''()=>{
const rect=e=>{if(!e)return null;const r=e.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height,right:r.right,bottom:r.bottom}};
const visible=e=>!!e&&getComputedStyle(e).display!=='none'&&getComputedStyle(e).visibility!=='hidden'&&e.getBoundingClientRect().width>0&&e.getBoundingClientRect().height>0;
const area=document.querySelector('#rail'),rr=rect(area),stage=rect(document.querySelector('#stage'));
const active=document.querySelector('#screen-'+document.body.dataset.page);
const cards=[...active.querySelectorAll('.tool-card')].map(e=>{const r=rect(e),d=e.querySelector('.card-detail'),tags=e.querySelector('.card-tags'),children=[...e.children].filter(visible).map(rect);return {id:e.dataset.toolId,rect:r,detail:visible(d),detailRect:rect(d),tagsRect:rect(tags),expanded:e.classList.contains('is-detail'),decoratedScrollSize:[e.scrollWidth,e.scrollHeight],intrinsicOverflow:children.some(c=>c.x<r.x-1||c.right>r.right+1||c.y<r.y-1||c.bottom>r.bottom+1),textOverflow:[...e.querySelectorAll('h3,p,.card-tags')].filter(visible).filter(p=>p.scrollHeight>p.clientHeight+2||p.scrollWidth>p.clientWidth+2).map(p=>p.className||p.tagName),visibleFraction:rr?Math.max(0,Math.min(rr.right,r.right)-Math.max(rr.x,r.x))/r.width:0}});
const text=[...active.querySelectorAll('.intro,.experience-text,.detail-body,.tools-intro,.card-use,.card-detail')].filter(visible).map(e=>({class:e.className,font:parseFloat(getComputedStyle(e).fontSize),lineHeight:getComputedStyle(e).lineHeight,rect:rect(e)}));
const controls=[...active.querySelectorAll('button,select,summary')].filter(visible).map(e=>({id:e.id||e.dataset.category||e.textContent.trim(),rect:rect(e)}));
return {viewport:[innerWidth,innerHeight],dpr:devicePixelRatio,rootFont:parseFloat(getComputedStyle(document.documentElement).fontSize),reducedMotion:matchMedia('(prefers-reduced-motion:reduce)').matches,page:document.body.dataset.page,state:document.body.dataset.reviewState,layout:document.body.dataset.layout,reason:document.querySelector('#layout-status').textContent,document:{width:document.documentElement.scrollWidth,height:document.documentElement.scrollHeight,scrollY},review:rect(document.querySelector('.review-bar')),header:rect(document.querySelector('.site-header')),footer:rect(document.querySelector('.site-footer')),stage,active:rect(active),panel:rect(active.querySelector('.prose-panel')),rail:rr,railScroll:area?.scrollLeft,cards,text,controls,openDetails:[...active.querySelectorAll('.reading-details[open]')].map(e=>e.querySelector('summary').textContent),initialData:JSON.parse(document.querySelector('#content-data').textContent).cards.slice(0,4).map(c=>c.id),dataCount:JSON.parse(document.querySelector('#content-data').textContent).cards.length,activeScreens:[...document.querySelectorAll('.screen')].filter(e=>!e.hidden).map(e=>e.id)};
}'''

smoke = [
    ('wide-identity', 1440, 900, 'A1', 'normal', False),
    ('wide-experience', 1440, 900, 'A2', 'normal', False),
    ('wide-experience-expanded', 1440, 900, 'A2', 'normal', True),
    ('wide-tools', 1440, 900, 'A3', 'normal', False),
    ('wide-tools-detail', 1440, 900, 'A3', 'detail', False),
    ('wide-long-name', 1440, 900, 'A3', 'long', False),
    ('wide-edge-reading', 1440, 900, 'A3', 'edge', False),
    ('phone-tools', 390, 844, 'A3', 'normal', False),
    ('narrow-tools-detail', 320, 740, 'A3', 'detail', False),
]
matrix = []
for name, width, height in [('large',1920,1080),('desktop',1440,900),('laptop',1366,768),
                            ('short-laptop',1280,720),('tablet-landscape',1024,768),
                            ('tablet-portrait',820,1180),('phone',390,844),('narrow',320,740),
                            ('short-landscape',844,390)]:
    for page in ['A1','A2','A3']:
        matrix.append((name+'-'+page,width,height,page,'normal',False))
matrix += [('desktop-identity-expanded',1440,900,'A1','normal',True),
           ('desktop-experience-expanded',1440,900,'A2','normal',True),
           ('desktop-detail',1440,900,'A3','detail',False),
           ('desktop-long-name',1440,900,'A3','long',False),
           ('desktop-edge-reading',1440,900,'A3','edge',False),
           ('desktop-all-tools',1440,900,'A3','all',False),
           ('phone-experience-expanded',390,844,'A2','normal',True),
           ('phone-detail',390,844,'A3','detail',False),
           ('narrow-detail',320,740,'A3','detail',False),
           ('narrow-all-tools',320,740,'A3','all',False),
           ('large-text-A1',800,600,'A1','normal',True),
           ('large-text-A2',800,600,'A2','normal',True),
           ('large-text-A3',800,600,'A3','detail',False),
           ('reduced-motion',1440,900,'A3','normal',False),
           ('review-controls',1440,900,'A3','normal',False)]
cases = smoke if args.suite == 'smoke' else matrix
if args.only:
    cases = [c for c in cases if c[0] in args.only.split(',')]
assert cases
server = ThreadingHTTPServer(('127.0.0.1',0),Handler)
port = server.server_address[1]
thread = threading.Thread(target=server.serve_forever,daemon=True)
thread.start()
origin = 'http://127.0.0.1:'+str(port)
report['server'] = {'origin': origin, 'pid': os.getpid(), 'servesOnlyIsolatedHTML': True}
browser = None
current = 'setup'
try:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
        report['version'] = browser.version
        for case, width, height, pageid, view, expanded in cases:
            current = case
            large = case.startswith('large-text')
            reduced = case == 'reduced-motion'
            ctx = browser.new_context(viewport={'width':width,'height':height},device_scale_factor=1,
                reduced_motion='reduce' if reduced else 'no-preference',service_workers='block')
            def route(route):
                if route.request.url.startswith(('http:','https:')) and not route.request.url.startswith(origin+'/'):
                    report['externalAttempts'].append({'case':current,'url':route.request.url})
                    route.abort()
                else:
                    route.continue_()
            ctx.route('**/*',route)
            p = ctx.new_page()
            p.on('pageerror',lambda e:report['events'].append({'case':current,'kind':'pageerror','text':str(e)}))
            p.on('console',lambda m:report['events'].append({'case':current,'kind':m.type,'text':m.text}) if m.type in ['warning','error'] else None)
            try:
                p.goto(origin+'/step-2-layout-preview.html',wait_until='networkidle')
                p.wait_for_function('document.body.dataset.layoutReady==="true"')
                if pageid!='A1':p.locator('[data-screen='+pageid+']').click()
                if large:p.locator('#large-font').click()
                if view!='normal':p.select_option('#review-state',view)
                if expanded:p.locator('#screen-'+pageid+' .reading-details summary').click()
                p.wait_for_timeout(160)
                m = p.evaluate(MEASURE)
                save(folder/(case+'-measurement.json'),m)
                assert m['dataCount']==22 and m['initialData']==['midjourney','comfyui','kling','blender']
                assert len(m['activeScreens'])==1
                assert m['document']['width']<=width+1,('document overflow',m['document'])
                assert all(t['font']>=16 for t in m['text']),('small body text',m['text'])
                assert all(c['rect']['height']>=43.5 for c in m['controls']),('short controls',[(c['id'],c['rect']['height'])for c in m['controls']])
                assert not[c for c in m['cards']if c['intrinsicOverflow']or c['textOverflow']],('card text clipped',[(c['id'],c['intrinsicOverflow'],c['textOverflow'])for c in m['cards']if c['intrinsicOverflow']or c['textOverflow']])
                if large:assert m['rootFont']==32 and m['layout']=='flow'
                if reduced:assert m['reducedMotion']and m['layout']=='flow'
                if width in [1440,1920]and height>=900 and not reduced and view!='all'and not expanded:
                    assert m['layout']=='immersive',('expected spacious immersive',m['layout'],m['reason'])
                if m['layout']=='immersive':
                    assert m['document']['height']<=height+2,('vertical viewport overflow',m['document'])
                    if pageid in ['A1','A2']:
                        a=m['panel'];assert a['y']>=m['header']['bottom']+8 and a['bottom']<=m['footer']['y']-8
                    elif view!='all':
                        rail=m['rail'];assert rail['height']>=345+32
                        for c in m['cards']:
                            if c['expanded']:
                                a=c['rect'];assert a['y']-16>=rail['y']-1 and a['bottom']+16<=rail['bottom']+1,('vertical expansion reserve',a,rail)
                                assert a['x']-16>=rail['x']-1 and a['right']+16<=rail['right']+1,('horizontal expansion reserve',a,rail)
                                assert c['detailRect']['bottom']<=c['tagsRect']['y']+1,('details overlap tags',c)
                        if view=='normal':
                            fractions=[c['visibleFraction']for c in m['cards']]
                            assert all(v>.99 for v in fractions[:3])and .15<fractions[3]<.85,('three plus partial',fractions[:5])
                elif pageid=='A3'and view!='all':
                    assert any(c['visibleFraction']>.99 for c in m['cards']),('no complete card',m['cards'])
                if view=='all':assert len(m['cards'])==22 and all(c['detail']for c in m['cards'])
                if case=='review-controls':
                    actions=[]
                    p.locator('#next-card').click()
                    p.locator('#next-card').click()
                    p.wait_for_timeout(100)
                    before=p.locator('#rail').evaluate('e=>e.scrollLeft')
                    assert before>0
                    p.locator('#show-all').click()
                    p.wait_for_timeout(160)
                    assert p.locator('#catalog .tool-card').count()==22
                    p.locator('#show-all').click()
                    p.wait_for_timeout(160)
                    returned=p.locator('#rail').evaluate('e=>e.scrollLeft')
                    assert abs(before-returned)<1
                    actions.append({'action':'all-and-return','beforeRail':before,'returnedRail':returned,'count':22})
                    save(folder/'review-controls-actions.json',actions)
                    p.locator('[data-category=G5]').click()
                    p.wait_for_timeout(160)
                    assert p.locator('#rail-track .tool-card').count()==3
                    p.locator('#show-all').click()
                    p.wait_for_timeout(160)
                    count=p.locator('#catalog .tool-card').count()
                    actions.append({'action':'all-from-filtered-category','actualCount':count})
                    save(folder/'review-controls-actions.json',actions)
                    assert count==22,('all tools from a category must show full list',count)
                    p.locator('#show-all').click()
                    p.wait_for_timeout(160)
                    assert p.locator('[data-category=G5]').get_attribute('aria-pressed')=='true'
                    assert p.locator('#rail-track .tool-card').count()==3
                    p.locator('[data-screen=A1]').click()
                    summary=p.locator('#identity-panel .reading-details summary')
                    summary.focus()
                    p.keyboard.press('Enter')
                    p.wait_for_timeout(160)
                    assert p.locator('#identity-panel details').get_attribute('open')is not None
                    p.keyboard.press('Enter')
                    assert p.locator('#identity-panel details').get_attribute('open')is None
                    actions.append({'action':'category-restored-and-native-keyboard-details','categoryRestored':'G5','nativeEnterOpenedAndClosed':True})
                    save(folder/'review-controls-actions.json',actions)
                p.screenshot(path=str(folder/(case+'.png')),full_page=(view!='all' or width>=1000))
                if view=='all'and width<1000:
                    p.evaluate('scrollTo(0,document.documentElement.scrollHeight)')
                    p.screenshot(path=str(folder/(case+'-bottom.png')))
                entry={'id':case,'status':'通过','viewport':[width,height],'page':pageid,'view':view,
                       'expanded':expanded,'measurement':case+'-measurement.json','layout':m['layout']}
            except Exception as error:
                entry={'id':case,'status':'待修正','viewport':[width,height],'page':pageid,'view':view,
                       'error':str(error),'traceback':traceback.format_exc()}
                try:p.screenshot(path=str(folder/(case+'-failure.png')),full_page=True)
                except Exception:pass
            finally:
                ctx.close()
            report['checks'].append(entry)
            save(folder/'browser.json',report)
            print(entry['status']+' '+case+(' '+entry.get('error','')[:280]),flush=True)
        browser.close()
        browser = None
finally:
    server.shutdown()
    server.server_close()
    thread.join(timeout=3)
    report['finishedAtShanghai']=now()
    report['cleanup']={'serverClosed':not thread.is_alive(),'browserClosed':browser is None,'otherServicesStopped':False}
    report['complete']=bool(report['checks'])and all(c['status']=='通过'for c in report['checks'])and not report['externalAttempts']and not[e for e in report['events']if e['kind']in['pageerror','error']]
    save(folder/'browser.json',report)
    print(json.dumps({'run':args.run,'checks':len(report['checks']),'complete':report['complete']},ensure_ascii=False),flush=True)
if not report['complete']:
    raise SystemExit(1)
