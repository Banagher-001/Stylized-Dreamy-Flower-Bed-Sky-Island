"""Step8-only helpers and evidence; old tests and receipts remain untouched."""
from pathlib import Path
import ast,json,os
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/evidence/scroll-garden-step-8';OUT.mkdir(parents=True,exist_ok=True)
tree=ast.parse((ROOT/'tests/scroll-garden/step2_browser.py').read_text())
PROBE=next(ast.literal_eval(n.value)for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='PROBE'for t in n.targets))
STOPS=[('A1',1.74),('A2',2.54),('A3',3.34),('B1',4.95),('B2',5.95),('B3',6.84),('B4',7.64),('C1',9.14),('C2',10.05),('C3',10.83)]
VIEWS=[('O',0),*STOPS,('travel',11.3),('W',11.5),('wide',11.67)]
def launch(p,engine='chromium',extra=None):
 options={'headless':engine=='chromium'}
 if engine=='chromium':options.update(executable_path='/usr/bin/chromium',args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader',*(extra or [])])
 if engine=='firefox':options['firefox_user_prefs']={'webgl.force-enabled':True}
 if engine=='webkit':options['executable_path']=os.environ.get('COURTYARD_WEBKIT_EXECUTABLE','/workspace/.cache/browser-deps/run-webkit.sh')
 return getattr(p,engine).launch(**options)
def data(page):return page.locator('#tour-host').evaluate('e=>({...e.dataset})')
def frames(page):page.evaluate('()=>document.fonts.ready.then(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))))')
def go(page,h):
 page.evaluate('h=>scrollTo({top:h/12.3*(document.documentElement.scrollHeight-innerHeight),behavior:"instant"})',h)
 page.wait_for_function('h=>{const d=document.querySelector("#tour-host").dataset;return d.cameraState==="settled"&&Math.abs(Number(d.displayH)-h)<.003}',arg=h)
def resize(page,w,h):
 old=float(data(page)['displayH']);page.set_viewport_size({'width':w,'height':h});page.wait_for_function('()=>{const e=document.querySelector("#tour-host"),r=e.getBoundingClientRect();return Math.abs(Number(e.dataset.aspect)-r.width/r.height)<.00001}');frames(page);go(page,old)
def ready(page,url):
 page.goto(url,wait_until='networkidle');page.wait_for_selector('#tour-host[data-render-state="ready"]');frames(page)
def save(name,value):(OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
