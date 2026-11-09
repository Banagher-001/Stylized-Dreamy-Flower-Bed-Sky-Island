"""Standalone check of an extracted final site; no historical fixture needed.
Requires Node and Python Playwright/Chromium. Writes only the requested output.
"""
from pathlib import Path
from urllib.request import urlopen
from urllib.error import HTTPError
import argparse,hashlib,json,os,queue,shutil,subprocess,tempfile,threading,time
from playwright.sync_api import sync_playwright
parser=argparse.ArgumentParser();parser.add_argument('--site',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
site=args.site.resolve();out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
root=Path(__file__).resolve().parents[2];script=site/'scripts/preview-site.mjs'
if not script.is_file():script=root/'scripts/preview-site.mjs'
assert(site/'index.html').is_file()and script.is_file()
production={str(p.relative_to(site)):hashlib.sha256(p.read_bytes()).hexdigest()for p in site.rglob('*')if p.is_file()and(p.name=='index.html'or p.parts[len(site.parts)]=='assets'or p.name in ['favicon.svg','share-cover.webp'])}
assert len(production)>=3
checks=[];responses=[];errors=[]
class Server:
    def __init__(self,base):
        self.child=subprocess.Popen(['node',str(script),'--dir',str(site),'--port','0','--base',base,'--json'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        q=queue.Queue();self.log=[]
        def read():
            for line in self.child.stdout:q.put(line)
        threading.Thread(target=read,daemon=True).start();deadline=time.monotonic()+15
        while time.monotonic()<deadline:
            try:line=q.get(timeout=.2)
            except queue.Empty:
                if self.child.poll()is not None:break
                continue
            self.log.append(line)
            if line.startswith('SAKAN_PREVIEW_READY '):self.url=json.loads(line.split(' ',1)[1])['url'];return
        self.close();raise AssertionError(self.log)
    def close(self):
        if self.child.poll()is None:
            self.child.terminate()
            try:self.child.wait(timeout=5)
            except subprocess.TimeoutExpired:self.child.kill();self.child.wait()
    def __enter__(self):return self
    def __exit__(self,*a):self.close()
def options(extra=None):
    value={'headless':True,'args':['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader',*(extra or[])]}
    executable=os.environ.get('CHROMIUM_EXECUTABLE')or shutil.which('chromium')or shutil.which('chromium-browser')
    if executable:value['executable_path']=executable
    return value
def data(page):return page.locator('#tour-host').evaluate('e=>({...e.dataset})')
def frames(page):page.evaluate('()=>document.fonts.ready.then(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))))')
def ready(page,url):
    page.goto(url,wait_until='networkidle');page.wait_for_selector('#tour-host[data-render-state=ready]');page.wait_for_function('document.querySelector("main").dataset.layoutReady==="true"');frames(page)
def visit(page,h):
    page.evaluate('h=>scrollTo({top:h/12.3*(document.documentElement.scrollHeight-innerHeight),behavior:"instant"})',h)
    page.wait_for_function('h=>{let d=document.querySelector("#tour-host").dataset;return d.cameraState==="settled"&&Math.abs(Number(d.displayH)-h)<.003}',arg=h);frames(page)
def watch(page):
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('response',lambda r:errors.append(str(r.status)+' '+r.url)if r.status>=400 else None)
with sync_playwright()as p:
    for base in ['/','/sakan/']:
        with Server(base)as server:
            for name,expected in production.items():
                with urlopen(server.url+name,timeout=10)as response:
                    body=response.read();assert response.status==200 and hashlib.sha256(body).hexdigest()==expected
                    mime=response.headers.get_content_type();expected_mime={'.html':'text/html','.js':'text/javascript','.css':'text/css','.mp4':'video/mp4','.svg':'image/svg+xml','.png':'image/png','.webp':'image/webp'}[Path(name).suffix]
                    assert mime==expected_mime,(name,mime)
                    responses.append({'base':base,'path':name,'sha256':expected,'status':200,'mime':mime})
            try:urlopen(server.url+'assets/missing.js',timeout=10)
            except HTTPError as e:assert e.code==404
            else:raise AssertionError('Missing asset did not404')
            browser=p.chromium.launch(**options());context=browser.new_context(viewport={'width':1440,'height':900});page=context.new_page();watch(page)
            ready(page,server.url);assert data(page)['guideState']=='manual'and page.locator('canvas').count()==1
            resources=json.loads(data(page)['birdResources']);assert resources['birds']==3 and resources['maximumColorDrawCalls']==1
            assert page.locator('.tour-stops button').count()==5
            if data(page)['motionState']=='running':page.locator('#tour-motion').click();frames(page)
            # Hidden articles still belong to the original semantic content.
            text=page.locator('.tour-reading-flow').text_content()
            assert all(s in text for s in ['张辰翰','枫叶互动','游族网络','网页设计样片'])
            page.evaluate('window.__releaseCanvas=document.querySelector("canvas")')
            page.locator('#tour-stop-about').click();page.wait_for_function('document.querySelector("#tour-host").dataset.cameraState==="settled"');frames(page)
            page.locator('#tour-guide').click();page.wait_for_function('document.querySelector("#tour-guide").getAttribute("aria-pressed")==="true"')
            page.mouse.move(1100,350);page.mouse.wheel(0,-100);page.wait_for_function('document.querySelector("#tour-guide").getAttribute("aria-pressed")==="false"')
            for mode in ['native','pixel']:page.locator(f'.tour-actions [data-mode={mode}]').click();frames(page)
            visit(page,10.05);page.locator('[data-project-tab=live]').click();frames(page)
            assert page.locator('canvas').count()==1 and page.evaluate('window.__releaseCanvas===document.querySelector("canvas")')
            page.screenshot(path=str(out/('root-live.png'if base=='/'else'subpath-live.png')))
            page.locator('.tour-project-close').click();frames(page)
            page.locator('[data-project-tab=archive]').click();page.locator('.tour-project-play').click();page.wait_for_function('document.querySelector("video")?.currentTime>.15')
            page.locator('.tour-project-close').click();frames(page);assert page.locator('video').count()==0
            assert page.locator('#tour-guide').get_attribute('aria-pressed')=='false'
            page.set_viewport_size({'width':390,'height':844});frames(page)
            if page.locator('main').get_attribute('data-reading-mode')!='stable':page.locator('#tour-layout-toggle').click();frames(page)
            assert page.locator('.tour-reading-flow article[aria-hidden=false]').count()==10
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
            page.screenshot(path=str(out/('root-reading.png'if base=='/'else'subpath-reading.png')))
            context.close()
            context=browser.new_context(viewport={'width':1440,'height':900});page=context.new_page();watch(page)
            ready(page,server.url+'?tour=prototype&waterTime=2');assert page.locator('canvas').count()==1
            page.goto(server.url+'?tour=reference&waterTime=2',wait_until='networkidle');page.wait_for_selector('#scene-host[data-render-state=ready]');assert page.locator('canvas').count()==1
            context.close()
            context=browser.new_context(viewport={'width':390,'height':844},reduced_motion='reduce');page=context.new_page();watch(page);ready(page,server.url)
            held=data(page)['sceneTime'];page.wait_for_timeout(500);assert data(page)['sceneTime']==held and data(page)['guideState']=='blocked'
            assert page.locator('.tour-reading-flow article[aria-hidden=false]').count()==10
            context.close();browser.close()
            failed=p.chromium.launch(**options(['--disable-webgl']));page=failed.new_page(viewport={'width':390,'height':844});exceptions=[];page.on('pageerror',lambda e:exceptions.append(str(e)))
            page.goto(server.url,wait_until='networkidle');page.wait_for_function('document.querySelector("main").dataset.readingMode==="stable"')
            assert page.locator('.tour-reading-flow article[aria-hidden=false]').count()==10 and page.locator('#tour-reference').is_visible()and not exceptions
            failed.close();checks.append({'base':base,'passed':True,'actualDefaultAndPrototype':True,'nativeGuideTakeover':True,'oneCanvasLive':True,'videoDecodeAndRelease':True,'mobileFullReading':True,'legacyReference':True,'reducedMotion':True,'actualWebGLUnavailableFallback':True})
            print('PASS extracted site',base,'complete HTTP/native controls/media/reading/fallback',flush=True)
assert not errors,errors
assert all(hashlib.sha256((site/n).read_bytes()).hexdigest()==v for n,v in production.items())
(out/'release-check.json').write_text(json.dumps({'passed':True,'site':str(site),'checks':checks,'productionSha256':production,'responses':responses,'errors':errors,
    'method':'actual extracted files and dependency-free preview tool on OS-selected loopback ports; real page/buttons/wheel; setup native scroll API explicitly separate; no historical fixtures, forced shaders or clocks','physicalDevice':False,'windowsRuntimeTested':False},ensure_ascii=False,indent=2)+'\n')
