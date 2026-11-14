"""Sequential real-input A/B sessions; each probe delegates original GL calls once."""
import argparse,math,os,shutil,struct,time,traceback
from playwright.sync_api import sync_playwright
from common import *
from inspection import SNAP,PICK
PROBE=r'''(()=>{const a=window.__parityProbe={draws:0};for(const C of[window.WebGLRenderingContext,window.WebGL2RenderingContext])if(C)for(const name of['drawArrays','drawElements','drawArraysInstanced','drawElementsInstanced']){const raw=C.prototype[name];if(raw)C.prototype[name]=function(...args){a.draws++;return raw.apply(this,args)}}})();'''
EVENTS=r'''()=>{const a=__parityProbe;if(a.eventsInstalled)return;a.eventsInstalled=true;a.inputs=[];a.clicks=[];a.keys=[];document.addEventListener('input',e=>{if(e.target.matches('input'))a.inputs.push({id:e.target.id,value:e.target.value,trusted:e.isTrusted})});document.addEventListener('click',e=>{const b=e.target.closest?.('button');if(b)a.clicks.push({id:b.id,data:{...b.dataset},trusted:e.isTrusted})});document.addEventListener('keydown',e=>a.keys.push({code:e.code,target:e.target.id||e.target.tagName,trusted:e.isTrusted}))}'''
DEFAULTS={'waveHeight':35,'waveSpeed':1,'waveDensity':1.25,'waveDirection':28,'waterLevel':42,'boatResponse':72,'boatDamping':48,'wind':22,'pixelScale':2,'sunset':45,'brightness':.82,'glassOpacity':.15,'lighthouse':True,'spray':True,'dust':True,'quality':'fine','paused':False,'editMode':None}
def arguments():
 p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--engine',default='chromium');p.add_argument('--only',default='');p.add_argument('--headed',action='store_true');p.add_argument('--site-url');p.add_argument('--prefix-url');return p.parse_args()
def close_values(a,b,path=''):
 if isinstance(a,(int,float))and not isinstance(a,bool):assert math.isfinite(a)and math.isfinite(b)and abs(a-b)<=1e-6,(path,a,b)
 elif isinstance(a,dict):
  assert a.keys()==b.keys(),path
  for k in a:close_values(a[k],b[k],path+'.'+k)
 elif isinstance(a,list):
  assert len(a)==len(b),path
  for i,(x,y)in enumerate(zip(a,b)):close_values(x,y,path+'.'+str(i))
 else:assert a==b,(path,a,b)
class Session:
 def __init__(self,run,side,config):self.run=run;self.side=side;self.config=config;self.ctx=None;self.page=None;self.surface=None
 def open(self):
  c=self.config;touch=c.get('touch',False)and self.run.args.engine=='chromium';opts={'viewport':{'width':c['host'][0]if self.side=='embedded'else c['child'][0],'height':c['host'][1]if self.side=='embedded'else c['child'][1]},'device_scale_factor':c.get('dpr',1),'accept_downloads':True,'service_workers':'block','has_touch':touch}
  if touch:opts['is_mobile']=True
  self.ctx=self.run.browser.new_context(**opts);self.ctx.add_init_script(PROBE);allowed=[self.run.services[k]for k in['productionOrigin','referenceOrigin','prefixOrigin']]
  def route(r):
   if r.request.url.startswith(('http:','https:'))and not any(r.request.url.startswith(o+'/')for o in allowed):self.run.report['externalAttempts'].append({'case':self.run.case_id,'side':self.side,'url':r.request.url});r.abort('blockedbyclient')
   else:r.continue_()
  self.ctx.route('**/*',route);self.page=self.ctx.new_page();self.page.set_default_timeout(25000);self.run.session=self;self.run.watch(self.page,self.side)
  if self.side=='reference':
   self.entry=self.run.services['referenceOrigin']+'/index.html';self.page.goto(self.entry,wait_until='domcontentloaded');self.surface=self.page
  else:
   self.entry=self.run.services['productionOrigin']+'/experiments/bottle-ocean/index.html';self.page.goto(self.run.services['productionOrigin']+'/',wait_until='domcontentloaded');self.page.wait_for_function('document.querySelector("main")?.dataset.layoutReady==="true"',timeout=90000,polling=100)
   if self.page.locator('main').get_attribute('data-reading-mode')!='stable':self.page.locator('#tour-layout-toggle').click();self.page.wait_for_function('document.querySelector("main").dataset.readingMode==="stable"',polling=100)
   self.page.locator('article[data-experiment-station=C2]').scroll_into_view_if_needed();self.page.locator('[data-project-select=bottle-ocean]').click();self.page.wait_for_function('document.querySelector(".experiment-reading").dataset.coverState==="ready"',timeout=25000,polling=100);self.page.locator('[data-project-tab=live]').click();self.page.wait_for_selector('iframe');assert self.page.locator('iframe').count()==1;self.surface=self.page.locator('iframe').element_handle().content_frame()
  self.surface.wait_for_function('window.__bottleError||document.querySelector("#loader-error")?.textContent?.trim()||(window.__bottleOcean?.ready===true&&getComputedStyle(document.querySelector("#loader")).display==="none")',timeout=120000,polling=100);fatal=self.evaluate('({error:window.__bottleError??null,text:document.querySelector("#loader-error")?.textContent?.trim()})');assert not fatal['error']and not fatal['text'],fatal
  if self.side=='embedded':self.page.wait_for_function('document.querySelector(".tour-project-dialog").dataset.embeddedState==="ready"',timeout=25000,polling=100)
  self.evaluate(EVENTS);self.tick();s=self.snapshot();assert not s['error']and not s['loader']['error']and s['diagnostics']['renderer']['triangles']>1000 and s['canvas']['width']>0
  response=self.ctx.request.get(self.entry);assert response.status==200 and hashlib.sha256(response.body()).hexdigest()==ENTRY_SHA
  self.conditions={'side':self.side,'url':self.surface.url,'entrySHA256':ENTRY_SHA,'viewport':s['viewport'],'canvas':[s['canvas']['width'],s['canvas']['height']],'dpr':s['dpr'],'touch':touch,'timeOrigin':self.evaluate('performance.timeOrigin'),'engineRevision':self.evaluate('__bottleOcean.THREE.REVISION')}
  if c.get('child'):assert s['viewport']==c['child']and all(abs(s['canvas'][d]-v)<1 for d,v in zip(['width','height'],c['child'])),self.conditions
  assert s['dpr']==c.get('dpr',1)
  return self
 def evaluate(self,code,arg=None):return self.surface.evaluate(code,arg)if arg is not None else self.surface.evaluate(code)
 def locator(self,selector):return self.surface.locator(selector)
 def snapshot(self):return self.evaluate(SNAP)
 def tick(self,n=2):
  before=self.evaluate('__parityProbe.draws');self.surface.wait_for_function('n=>__parityProbe.draws>n',arg=before,timeout=60000,polling=100)
  if n>1:self.page.wait_for_timeout(80)
 def frames(self,n):
  self.evaluate('''n=>{const a=__parityProbe.frameWait={count:0,last:-1,done:false};function read(){const k=__parityProbe.draws;if(k!==a.last){if(a.last>=0)a.count++;a.last=k}if(a.count>=n)a.done=true;else requestAnimationFrame(read)}requestAnimationFrame(read)}''',n);self.surface.wait_for_function('__parityProbe.frameWait.done',timeout=90000,polling=100)
 def open_panel(self):
  if self.evaluate('document.body.classList.contains("ui-hidden")'):self.locator('#restore-ui').click();self.page.wait_for_timeout(300)
  if self.locator('#control-panel').evaluate('e=>e.classList.contains("collapsed")'):self.locator('#panel-toggle').click();self.page.wait_for_timeout(300)
 def reset(self,quality='retro'):
  self.open_panel();self.locator('[data-action=reset]').click();self.tick()
  if quality!='fine':self.quality(quality)
 def quality(self,name='retro'):self.open_panel();self.locator('[data-quality='+name+']').click();self.tick();assert self.evaluate('__bottleOcean.state.quality')==name
 def slider(self,name,value):
  self.open_panel();loc=self.locator('#'+name);loc.scroll_into_view_if_needed();lo=float(loc.get_attribute('min'));hi=float(loc.get_attribute('max'));step=float(loc.get_attribute('step'))
  if abs(value-lo)<1e-8:loc.press('Home')
  elif abs(value-hi)<1e-8:loc.press('End')
  else:
   box=loc.bounding_box();self.page.mouse.click(box['x']+box['width']*(value-lo)/(hi-lo),box['y']+box['height']/2);actual=float(loc.input_value());delta=round((value-actual)/step);assert abs(delta)<40,(name,value,actual,box)
   for _ in range(abs(delta)):loc.press('ArrowRight'if delta>0 else'ArrowLeft')
  self.tick();actual=float(loc.input_value());assert abs(actual-value)<step*.01+1e-7 and abs(self.evaluate('n=>__bottleOcean.state[n]',name)-actual)<1e-6
  event=self.evaluate('n=>__parityProbe.inputs.filter(e=>e.id===n).at(-1)',name);assert event and event['trusted'];return {'value':actual,'event':event}
 def offset(self):
  if self.side=='reference':return {'x':0,'y':0}
  b=self.page.locator('iframe').bounding_box();return {'x':b['x'],'y':b['y']}
 def click(self,x,y,double=False):
  o=self.offset()
  if double:self.page.mouse.dblclick(o['x']+x,o['y']+y,delay=95)
  else:self.page.mouse.click(o['x']+x,o['y']+y)
 def drag(self,x,y,dx,dy,button='left'):
  o=self.offset();self.page.mouse.move(o['x']+x,o['y']+y);self.page.mouse.down(button=button);self.page.mouse.move(o['x']+x+dx,o['y']+y+dy,steps=10);self.page.mouse.up(button=button);self.tick()
 def camera(self):return self.evaluate('__bottleOcean.cameraRig.getState()')
 def settle(self):self.page.wait_for_timeout(1450);self.frames(4)
 def props(self):return self.evaluate('''()=>{const a=[];__bottleOcean.scene.traverse(o=>{if(o.userData.propKind)a.push({kind:o.userData.propKind,uuid:o.uuid,position:o.parent.position.toArray()})});return a}''')
 def pick(self,kind):return self.evaluate(PICK,kind)
 def place(self,kind):
  self.open_panel();self.locator('[data-edit='+kind+']').click();point=self.pick('edit');assert point;before=self.props();self.click(point['x'],point['y']);self.tick();after=self.props();assert len(after)==len(before)+1 and after[-1]['kind']==kind;return {'point':point,'before':before,'after':after}
 def picture(self,label):self.page.screenshot(path=str(self.run.folder/(label+'-'+self.side+'.png')))
 def download(self,label,hidden=False):
  before=self.snapshot()
  if hidden:self.locator('[data-action=screenshot]').focus();self.page.keyboard.press('h');assert self.evaluate('document.body.classList.contains("ui-hidden")')
  with self.page.expect_download(timeout=30000)as event:
   if hidden:self.page.keyboard.press('Enter')
   else:self.locator('[data-action=screenshot]').click()
  d=event.value;path=self.run.folder/(label+'-'+self.side+'.png');d.save_as(str(path));raw=path.read_bytes();assert raw[:8]==b'\x89PNG\r\n\x1a\n';size=list(struct.unpack('>II',raw[16:24]));expected=[math.floor(before['canvas'][k]*min(before['dpr'],2)+.5)for k in['width','height']];assert size==expected and not d.failure()and len(raw)>10000
  if hidden:self.locator('#restore-ui').click()
  return {'file':row(path),'name':d.suggested_filename,'PNG':size,'expected':expected,'before':before,'nativeButton':True,'hiddenUIActivation':hidden}
 def close(self):
  result=None
  if self.ctx:
   if self.side=='embedded'and self.page and not self.page.is_closed():
    if self.page.locator('.tour-project-dialog').evaluate('e=>e.open'):self.page.locator('.tour-project-close').click()
    self.page.wait_for_function('!document.querySelector(".tour-project-dialog").open&&document.querySelectorAll("iframe").length===0',polling=100);self.page.wait_for_timeout(180);result=self.page.evaluate('({scrollY,focus:document.activeElement?.getAttribute("data-project-tab")||document.activeElement?.id,projectLock:document.documentElement.classList.contains("tour-project-open")})');assert not result['projectLock']
   self.ctx.unroute_all(behavior='ignoreErrors');self.ctx.close();self.ctx=None
  return result
class Run:
 def __init__(self,args):
  self.args=args;self.folder=OUT/args.run;self.folder.mkdir(exist_ok=False);self.services=read(OUT/'services-started.json');os.environ.update(self.services['browserEnvironment']);self.case_id='setup';self.session=None
  if args.site_url:self.services['productionOrigin']=args.site_url.rstrip('/')
  if args.prefix_url:self.services['prefixOrigin']=args.prefix_url.rstrip('/')
  for f in TEST.glob('*.py'):shutil.copyfile(f,self.folder/(f.name+'.txt'))
  self.report={'startedAtShanghai':now(),'engine':args.engine,'headed':args.headed,'checks':[],'requests':[],'events':[],'externalAttempts':[],'clockModified':False,'RAFReplaced':False,'originalFilesModified':False,'physicalDevice':False,'comparisonTolerance':1e-6,'buildRecord':read(OUT/'active-build.json')['record']}
  self.pw=sync_playwright().start();opts={'headless':not args.headed}
  if args.engine=='chromium':opts.update(executable_path='/usr/bin/chromium',args=['--no-sandbox','--use-gl=angle','--use-angle=gl','--ignore-gpu-blocklist'])
  elif args.engine=='webkit':opts['executable_path']=str(ROOT/'docs/evidence/lawson-fullpage-step-7/webkit-run.sh')
  self.browser=getattr(self.pw,args.engine).launch(**opts);self.report['version']=self.browser.version
 def watch(self,p,side):
  p.on('request',lambda q:self.report['requests'].append({'case':self.case_id,'side':side,'url':q.url,'type':q.resource_type}));p.on('pageerror',lambda e:self.report['events'].append({'case':self.case_id,'side':side,'kind':'pageerror','text':str(e)}));p.on('console',lambda m:self.report['events'].append({'case':self.case_id,'side':side,'kind':m.type,'text':m.text})if m.type in['error','warning']else None);p.on('requestfailed',lambda q:self.report['events'].append({'case':self.case_id,'side':side,'kind':'requestfailed','url':q.url,'text':q.failure}))
 def save(self):write(self.folder/'browser.json',self.report)
 def selected(self,id):return not self.args.only or any(id.startswith(x)for x in self.args.only.split(','))
 def pair(self,id,ctls,fn,config='desktop'):
  if not self.selected(id):return
  self.case_id=id;cfg=read(OUT/'pair-conditions.json')[config];sides={}
  for side in['reference','embedded']:
   s=Session(self,side,cfg)
   try:
    s.open();data=fn(s);entry={'status':'通过','conditions':s.conditions,'evidence':data}
   except Exception as e:
    entry={'status':'待补核','error':str(e),'traceback':traceback.format_exc()}
    if s.page and not s.page.is_closed():
     try:entry['snapshot']=s.snapshot();s.picture('failure-'+id.replace('.','-'))
     except Exception:pass
   finally:
    try:returned=s.close()
    except Exception as e:
     entry['status']='待补核';entry['closeError']=str(e)
     if s.ctx:s.ctx.close();s.ctx=None
   if entry['status']=='通过':entry['returned']=returned
   sides[side]=entry;write(self.folder/(id.replace('.','-')+'-'+side+'.json'),entry);print(side+' '+entry['status']+' '+id,flush=True)
  result={'id':id,'ctls':ctls,'status':'配对通过'if all(x['status']=='通过'for x in sides.values())else'待补核','sides':sides}
  if result['status']=='配对通过':
   try:close_values(sides['reference']['evidence'].get('comparison'),sides['embedded']['evidence'].get('comparison'));close_values(sides['reference']['conditions']['viewport'],sides['embedded']['conditions']['viewport']);close_values(sides['reference']['conditions']['dpr'],sides['embedded']['conditions']['dpr'])
   except Exception as e:result['status']='待补核';result['comparisonError']=str(e)
  self.report['checks'].append(result);self.save();print(result['status']+' '+id,flush=True)
 def finish(self):
  if self.session and self.session.ctx:
   try:self.session.close()
   except Exception:self.session.ctx.close()
  self.browser.close();self.pw.stop();self.report['finishedAtShanghai']=now();self.report['complete']=bool(self.report['checks'])and all(c['status']in['配对通过','通过']for c in self.report['checks']);self.save();print(json.dumps({'run':self.args.run,'complete':self.report['complete'],'checks':len(self.report['checks'])},ensure_ascii=False),flush=True)
  if not self.report['complete']:raise SystemExit(1)
