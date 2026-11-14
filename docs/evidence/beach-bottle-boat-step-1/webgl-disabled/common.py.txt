"""Standalone real-input observations; original files and simulation clocks stay untouched."""
from pathlib import Path
import argparse,hashlib,json,math,os,shutil,struct,time,traceback
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];SOURCE=ROOT.parent/'Beach-Bottle-Boat';OUT=ROOT/'docs/evidence/beach-bottle-boat-step-1';BASE='http://127.0.0.1:4201'
PROBE=r'''(()=>{
 const a=window.__baseline={draws:0,frames:0,readyEvents:[],visibility:[],inputs:[],clicks:[],keys:[],context:[]};
 const raf=requestAnimationFrame.bind(window);window.requestAnimationFrame=cb=>raf(t=>{if(cb.name==='tick')a.frames++;return cb.call(window,t)});
 for(const C of[window.WebGLRenderingContext,window.WebGL2RenderingContext])if(C)for(const k of['drawArrays','drawElements','drawArraysInstanced','drawElementsInstanced']){const raw=C.prototype[k];if(raw)C.prototype[k]=function(...v){a.draws++;return raw.apply(this,v)}}
 addEventListener('bottle-ocean-ready',()=>a.readyEvents.push({time:performance.now(),ready:window.__bottleOcean?.ready,loader:document.querySelector('#loader')?.className}));
 document.addEventListener('visibilitychange',()=>a.visibility.push({state:document.visibilityState,time:performance.now()}));
 document.addEventListener('input',e=>{if(e.target.matches('input'))a.inputs.push({id:e.target.id,value:e.target.value,trusted:e.isTrusted,time:performance.now()})});
 document.addEventListener('click',e=>{const b=e.target.closest?.('button');if(b)a.clicks.push({id:b.id,data:{...b.dataset},text:b.innerText,trusted:e.isTrusted,time:performance.now()})});
 addEventListener('keydown',e=>a.keys.push({code:e.code,target:e.target.id||e.target.tagName,trusted:e.isTrusted}));
 document.addEventListener('webglcontextlost',e=>a.context.push({kind:'lost',trusted:e.isTrusted,time:performance.now()}),true);
 document.addEventListener('webglcontextrestored',e=>a.context.push({kind:'restored',trusted:e.isTrusted,time:performance.now()}),true);
})()'''
SNAP=r'''()=>{
 const b=__bottleOcean,d=b.getDiagnostics(),e=b.environment,ps=b.post.getState(),sails=[];
 b.boat.model.traverse(o=>{if(o.isMesh&&o.userData.phase!==undefined)sails.push({name:o.name,rotation:o.rotation.toArray().slice(0,3)})});
 return {diagnostics:d,post:{quality:ps.quality,scale:ps.scale,levels:ps.levels,dither:ps.dither,pixelWidth:ps.pixelWidth,pixelHeight:ps.pixelHeight,exposure:ps.uniforms.uExposure.value},
  actual:{waveParams:{...b.waterField.params},amplitude:b.waterField.amplitude,baseLevel:b.waterField.baseLevel,waves:b.waterField.waves.map(w=>({dx:w.dx,dz:w.dz,k:w.k,omega:w.omega,amplitude:w.amplitude})),glassOpacity:b.bottle.glassMaterial.uniforms.uOpacity.value,
   sunIntensity:e.sunLight.intensity,sunColor:e.sunLight.color.toArray(),sunPosition:e.sunLight.position.toArray(),wind:e.skyUniforms.uWind.value,lighthouse:e.lighthouse.isEnabled,spray:e.spray.visible,dust:e.dust.visible,sails},
  ui:{hidden:document.body.classList.contains('ui-hidden'),collapsed:document.querySelector('#control-panel').classList.contains('collapsed'),edit:document.body.classList.contains('edit-active'),pauseLabel:document.querySelector('#pause-label').textContent,sliders:[...document.querySelectorAll('input[data-control]')].map(i=>({id:i.id,value:i.value,output:document.querySelector('[data-output="'+i.id+'"]').textContent,min:i.min,max:i.max,step:i.step}))},
  viewport:[innerWidth,innerHeight],dpr:devicePixelRatio,frames:__baseline.frames,draws:__baseline.draws,
  canvas:document.querySelector('#gl').getBoundingClientRect().toJSON(),loader:{hidden:document.querySelector('#loader').className,display:getComputedStyle(document.querySelector('#loader')).display,error:document.querySelector('#loader-error').textContent},error:window.__bottleError??null};
}'''
def arguments():
 p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--engine',default='chromium');p.add_argument('--only',default='');p.add_argument('--no-webgl',action='store_true');return p.parse_args()
class Run:
 def __init__(self,args,phase):
  self.args=args;self.phase=phase;self.folder=OUT/args.run;self.folder.mkdir(exist_ok=False);self.file=self.folder/'browser.json';self.contexts=[];self.page=None;self.case_id='setup'
  for f in Path(__file__).parent.glob('*.py'):shutil.copyfile(f,self.folder/(f.name+'.txt'))
  self.report={'phase':phase,'engine':args.engine,'checks':[],'events':[],'requests':[],'externalAttempts':[],'sourceFilesModified':False,'clockModified':False,'scope':'standalone original only; no host integration','physicalDevice':False,'DISPLAY':os.environ.get('DISPLAY')}
  self.pw=sync_playwright().start();opts={'headless':False}
  if args.engine=='chromium':opts.update(executable_path='/usr/bin/chromium',args=['--no-sandbox','--use-gl=angle','--use-angle=gl','--ignore-gpu-blocklist']+(['--disable-webgl']if args.no_webgl else[]))
  elif args.engine=='webkit':opts['executable_path']=str(ROOT/'docs/evidence/lawson-fullpage-step-7/webkit-run.sh')
  self.browser=getattr(self.pw,args.engine).launch(**opts);self.report['browserVersion']=self.browser.version
 def save(self):self.file.write_text(json.dumps(self.report,ensure_ascii=False,indent=2)+'\n')
 def context(self,w=1440,h=900,dpr=1,**options):
  c=self.browser.new_context(viewport={'width':w,'height':h},device_scale_factor=dpr,accept_downloads=True,**options);c.add_init_script(PROBE);self.contexts.append(c)
  def route(r):
   url=r.request.url
   if url.startswith(('http:','https:'))and not url.startswith(BASE+'/'):
    self.report['externalAttempts'].append({'case':self.case_id,'url':url});r.abort('blockedbyclient')
   else:r.continue_()
  c.route('**/*',route);return c
 def new(self,w=1440,h=900,dpr=1,url=None,**options):
  for previous in self.contexts:
   try:previous.unroute_all(behavior='ignoreErrors');previous.close()
   except Exception:pass
  self.contexts=[]
  c=self.context(w,h,dpr,**options);p=c.new_page();self.page=p;p.set_default_timeout(25000)
  p.on('request',lambda q:self.report['requests'].append({'case':self.case_id,'url':q.url,'type':q.resource_type}))
  p.on('pageerror',lambda e:self.report['events'].append({'case':self.case_id,'kind':'pageerror','text':str(e)}))
  p.on('console',lambda m:self.report['events'].append({'case':self.case_id,'kind':'console','level':m.type,'text':m.text})if m.type in['warning','error']else None)
  p.on('requestfailed',lambda q:self.report['events'].append({'case':self.case_id,'kind':'requestfailed','url':q.url,'text':q.failure}))
  p.on('response',lambda q:self.report['events'].append({'case':self.case_id,'kind':'response','url':q.url,'status':q.status})if q.status>=400 else None)
  p.goto(url or BASE+'/index.html',wait_until='domcontentloaded');return c,p
 def ready(self,p=None):
  p=p or self.page;p.wait_for_function('window.__bottleOcean?.ready===true&&getComputedStyle(document.querySelector("#loader")).display==="none"',timeout=120000,polling=100)
  p.wait_for_function('__baseline.frames>1',timeout=60000,polling=100);assert not p.evaluate('!!window.__bottleError');return p.evaluate(SNAP)
 def frames(self,n=2,p=None):
  p=p or self.page;start=p.evaluate('__baseline.frames');p.wait_for_function('a=>__baseline.frames>=a.start+a.n',arg={'start':start,'n':n},timeout=60000,polling=100)
 def snapshot(self,p=None):return(p or self.page).evaluate(SNAP)
 def picture(self,name,p=None):(p or self.page).screenshot(path=str(self.folder/(name+'.png')))
 def quality(self,name='retro',p=None):
  p=p or self.page;p.locator('[data-quality='+name+']').click();self.frames(p=p);assert p.evaluate('__bottleOcean.state.quality')==name
 def reset(self,p=None,quality='retro'):
  p=p or self.page
  if p.evaluate('document.body.classList.contains("ui-hidden")'):p.locator('#restore-ui').click()
  if p.locator('#control-panel').evaluate('e=>e.classList.contains("collapsed")'):p.locator('#panel-toggle').click()
  p.locator('[data-action=reset]').click();self.frames(p=p)
  if quality!='fine':self.quality(quality,p)
 def slider(self,name,value,p=None):
  p=p or self.page;loc=p.locator('#'+name);loc.scroll_into_view_if_needed();lo=float(loc.get_attribute('min'));hi=float(loc.get_attribute('max'));step=float(loc.get_attribute('step'))
  if abs(value-lo)<1e-8:loc.press('Home')
  elif abs(value-hi)<1e-8:loc.press('End')
  else:
   box=loc.bounding_box();p.mouse.click(box['x']+box['width']*(value-lo)/(hi-lo),box['y']+box['height']/2)
   actual=float(loc.input_value());delta=round((value-actual)/step)
   assert abs(delta)<35,(name,value,actual,box)
   for _ in range(abs(delta)):loc.press('ArrowRight'if delta>0 else'ArrowLeft')
  actual=float(loc.input_value());assert abs(actual-value)<step*.01+1e-7,(name,value,actual)
  self.frames(p=p);assert abs(p.evaluate('n=>__bottleOcean.state[n]',name)-actual)<1e-6
  return {'inputValue':actual,'originalTrustedInput':p.evaluate('n=>__baseline.inputs.filter(e=>e.id===n).at(-1)',name)}
 def draw_delta(self,ms=1000,p=None):
  p=p or self.page;n=p.evaluate('__baseline.draws');p.wait_for_timeout(ms);return p.evaluate('__baseline.draws')-n
 def check(self,id,name,fn):
  if self.args.only and not any(id.startswith(x)for x in self.args.only.split(',')):return
  self.case_id=id
  try:
   e=fn();status=e.pop('_status','通过')if isinstance(e,dict)else'通过';entry={'id':id,'name':name,'status':status,'evidence':e};print(status+' '+id,flush=True)
  except Exception as ex:
   entry={'id':id,'name':name,'status':'待补核','error':str(ex),'traceback':traceback.format_exc()}
   if self.page and not self.page.is_closed():
    try:entry['snapshot']=self.snapshot();self.picture('failure-'+id.replace('.','-'))
    except Exception:pass
   print('待补核 '+id+': '+str(ex),flush=True)
  self.report['checks'].append(entry);self.save()
 def finish(self):
  for c in self.contexts:
   try:c.unroute_all(behavior='ignoreErrors');c.close()
   except Exception:pass
  self.browser.close();self.pw.stop();self.report['complete']=bool(self.report['checks'])and all(c['status']!='待补核'for c in self.report['checks']);self.report['externalRequestsAttempted']=len(self.report['externalAttempts']);self.save()
  print(json.dumps({'complete':self.report['complete'],'checks':len(self.report['checks']),'knownIssues':[c['id']for c in self.report['checks']if c['status']=='原页已有问题'],'externalAttempts':len(self.report['externalAttempts'])},ensure_ascii=False),flush=True)
  if not self.report['complete']:raise SystemExit(1)
