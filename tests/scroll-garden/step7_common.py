"""Shared browser helpers; probes remain test-only."""
from pathlib import Path
import ast, json, os

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/evidence/scroll-garden-step-7'
OUT.mkdir(parents=True,exist_ok=True)
tree=ast.parse((ROOT/'tests/scroll-garden/step2_browser.py').read_text())
PROBE=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PROBE' for t in n.targets))
STOPS=[('C1',9.14,2.75),('C2',10.05,1.8),('C3',10.83,.85)]
OLD=[('A1',1.74),('A2',2.54),('A3',3.34),('B1',4.95),('B2',5.95),('B3',6.84),('B4',7.64)]

def launch(p,engine='chromium'):
    options={'headless':engine=='chromium'}
    if engine=='chromium':options.update(executable_path='/usr/bin/chromium',args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
    if engine=='firefox':options['firefox_user_prefs']={'webgl.force-enabled':True}
    if engine=='webkit' and os.environ.get('COURTYARD_WEBKIT_EXECUTABLE'):options['executable_path']=os.environ['COURTYARD_WEBKIT_EXECUTABLE']
    return getattr(p,engine).launch(**options)
def data(page):return page.locator('#tour-host').evaluate('e=>({...e.dataset})')
def frames(page):page.evaluate('()=>document.fonts.ready.then(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))))')
def settled(page,h):page.wait_for_function('h=>{const d=document.querySelector("#tour-host").dataset;return d.cameraState==="settled"&&Math.abs(Number(d.displayH)-h)<.003}',arg=h)
def go(page,h):
    page.evaluate('h=>scrollTo({top:h/12.3*(document.documentElement.scrollHeight-innerHeight),behavior:"instant"})',h)
    settled(page,h)
def resize(page,w,h):
    prior=float(data(page)['displayH']);page.set_viewport_size({'width':w,'height':h})
    page.wait_for_function('()=>{const e=document.querySelector("#tour-host"),r=e.getBoundingClientRect();return Math.abs(Number(e.dataset.aspect)-r.width/r.height)<.00001}')
    frames(page);settled(page,prior)
def save(name,value):(OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
