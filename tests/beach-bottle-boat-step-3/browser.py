"""Exercise the saved original through real HTTP and native browser input."""
import argparse,math,os,shutil,struct,time,traceback,urllib.request
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
from common import *
parser=argparse.ArgumentParser();parser.add_argument('--run',required=True);parser.add_argument('--only',default='');args=parser.parse_args()
folder=OUT/args.run;folder.mkdir(exist_ok=False)
for f in TEST.glob('*.py'):shutil.copyfile(f,folder/(f.name+'.txt'))
services=read(OUT/'services-started.json');os.environ.update(services['browserEnvironment'])
dev=services['devOrigin'];prod=services['productionOrigin'];entry='experiments/bottle-ocean/index.html';prefix=services['productionPrefix'];case='setup';page=None;context=None
report={'startedAtShanghai':now(),'browser':'Chromium','checks':[],'requests':[],'pageErrors':[],'console':[],'failedRequests':[],'httpErrors':[],'externalAttempts':[],'routesDisableCache':True,'serviceWorkers':'blocked','originalClockModified':False,'originalFilesModified':False,'scope':'saved original standalone; no Coding entry or iframe integration','sourceEntrySHA256':ENTRY_SHA,'softwareRenderingRequested':services['browserEnvironment']}
PROBE=r'''(()=>{const a=window.__step3={readyEvents:[],inputs:[],clicks:[]};addEventListener('bottle-ocean-ready',()=>a.readyEvents.push({time:performance.now(),ready:window.__bottleOcean?.ready,loader:document.querySelector('#loader')?.className}));document.addEventListener('input',e=>{if(e.target.matches('input'))a.inputs.push({id:e.target.id,value:e.target.value,trusted:e.isTrusted})});document.addEventListener('click',e=>{const b=e.target.closest?.('button');if(b)a.clicks.push({id:b.id,data:{...b.dataset},trusted:e.isTrusted})})})()'''
SNAP=r'''()=>{const b=__bottleOcean,d=b.getDiagnostics(),gl=b.renderer.getContext(),ext=gl.getExtension('WEBGL_debug_renderer_info');return {url:location.href,diagnostics:d,viewport:[innerWidth,innerHeight],dpr:devicePixelRatio,canvas:document.querySelector('#gl').getBoundingClientRect().toJSON(),loader:{display:getComputedStyle(document.querySelector('#loader')).display,error:document.querySelector('#loader-error').textContent},error:window.__bottleError??null,ui:{hidden:document.body.classList.contains('ui-hidden'),collapsed:document.querySelector('#control-panel').classList.contains('collapsed'),buttons:document.querySelectorAll('button').length,sliders:document.querySelectorAll('input[data-control]').length},gl:{version:gl.getParameter(gl.VERSION),renderer:ext?gl.getParameter(ext.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER),lost:gl.isContextLost()},readyEvents:__step3.readyEvents,inputs:__step3.inputs,clicks:__step3.clicks}}'''
def save():write(folder/'browser.json',report)
def selected(id):return not args.only or any(id.startswith(x)for x in args.only.split(','))
def check(id,name,fn,force=False):
 global case
 if not force and not selected(id):return
 case=id
 try:evidence=fn();status=evidence.pop('_status','通过')if isinstance(evidence,dict)else'通过';item={'id':id,'name':name,'status':status,'evidence':evidence};print(status+' '+id,flush=True)
 except Exception as ex:
  item={'id':id,'name':name,'status':'待补核','error':str(ex),'traceback':traceback.format_exc()}
  if page and not page.is_closed():
   try:item['snapshot']=page.evaluate(SNAP)
   except Exception:pass
   try:page.screenshot(path=str(folder/('failure-'+id.replace('.','-')+'.png')))
   except Exception:pass
  print('待补核 '+id+': '+str(ex),flush=True)
 report['checks'].append(item);save()
def http_files(origin,base):
 rows=[]
 for name in['index.html','THIRD_PARTY_NOTICES.md','SOURCE.md']:
  url=origin+base+'experiments/bottle-ocean/'+name
  with urllib.request.urlopen(urllib.request.Request(url,headers={'Accept-Encoding':'identity','Cache-Control':'no-cache'}),timeout=15)as response:
   raw=response.read();mime=response.headers.get_content_type();assert response.status==200
   digest=hashlib.sha256(raw).hexdigest();assert digest==sha(RUNTIME/name)
   if name=='index.html':assert mime=='text/html'and digest==ENTRY_SHA
   rows.append({'url':url,'status':response.status,'type':mime,'bytes':len(raw),'sha256':digest})
 return {'responses':rows,'verifiedActualBodies':True}
def new(url,w=1280,h=720,dpr=1):
 global context,page
 if context:context.unroute_all(behavior='ignoreErrors');context.close()
 context=browser.new_context(viewport={'width':w,'height':h},device_scale_factor=dpr,accept_downloads=True,service_workers='block');context.add_init_script(PROBE)
 def route(r):
  url=r.request.url
  if url.startswith(('http:','https:'))and not any(url.startswith(o+'/')for o in[dev,prod]):report['externalAttempts'].append({'case':case,'url':url});r.abort('blockedbyclient')
  else:r.continue_()
 context.route('**/*',route);page=context.new_page();page.set_default_timeout(25000)
 page.on('request',lambda q:report['requests'].append({'case':case,'url':q.url,'type':q.resource_type}))
 page.on('pageerror',lambda e:report['pageErrors'].append({'case':case,'text':str(e)}))
 page.on('console',lambda m:report['console'].append({'case':case,'type':m.type,'text':m.text})if m.type in['warning','error']else None)
 page.on('requestfailed',lambda q:report['failedRequests'].append({'case':case,'url':q.url,'failure':q.failure}))
 page.on('response',lambda q:report['httpErrors'].append({'case':case,'url':q.url,'status':q.status})if q.status>=400 else None)
 response=page.goto(url,wait_until='domcontentloaded');assert response.status==200;return response
def ready():
 page.wait_for_function('window.__bottleOcean?.ready===true&&getComputedStyle(document.querySelector("#loader")).display==="none"',timeout=120000,polling=100);s=page.evaluate(SNAP);assert not s['error']and not s['loader']['error']and not s['gl']['lost'];assert s['diagnostics']['renderer']['calls']>0 and s['diagnostics']['renderer']['triangles']>1000;assert s['ui']['buttons']==22 and s['ui']['sliders']==12;return s
def frames(n=2):
 start=page.evaluate('__bottleOcean.getDiagnostics().simTime');page.wait_for_function('t=>__bottleOcean.getDiagnostics().simTime>=t',arg=start+n*.05,timeout=60000,polling=100)
def picture(name):page.screenshot(path=str(folder/(name+'.png')))
def quality():page.locator('[data-quality=retro]').click();frames();assert page.evaluate('__bottleOcean.state.quality')=='retro'
def load(url,label,w=1280,h=720,dpr=1):
 t=time.monotonic();response=new(url,w,h,dpr);s=ready();raw=response.body();assert hashlib.sha256(raw).hexdigest()==ENTRY_SHA;picture(label+'-default');s['scene']=page.evaluate('''()=>{const b=__bottleOcean,e=b.environment;let meshes=0;b.scene.traverse(o=>{if(o.isMesh)meshes++});return {masts:b.boat.masts.length,terrainVertices:e.terrain.geometry.attributes.position.count,meshes,ocean:!!e.ocean,sky:!!e.skyMesh,lighthouse:!!e.lighthouse,glass:!!b.bottle.glassMesh}}''');assert s['scene']['masts']==3 and s['scene']['terrainVertices']>1000 and s['scene']['meshes']>20;return {'wallSeconds':time.monotonic()-t,'bodySHA256':ENTRY_SHA,'default':s}
def motion(label):
 quality();page.locator('#waveHeight').press('Home');frames();calm=page.evaluate(SNAP);assert calm['diagnostics']['state']['waveHeight']==0 and calm['diagnostics']['water']['amplitude']==0
 page.locator('#waveHeight').press('End');frames();assert page.evaluate('__bottleOcean.state.waveHeight')==100
 page.evaluate('''()=>{const a=__step3.motion={rows:[],done:false};function observe(){const b=__bottleOcean,d=b.getDiagnostics();a.rows.push({wall:performance.now(),simTime:d.simTime,boat:d.boat,water:d.water,gpuTime:b.waterField.uniforms.uTime.value});if(a.rows.length>=40&&d.simTime-a.rows[0].simTime>=2.5)a.done=true;else requestAnimationFrame(observe)}requestAnimationFrame(observe)}''')
 deadline=time.monotonic()+120
 while not page.evaluate('__step3.motion.done'):
  assert time.monotonic()<deadline;page.wait_for_timeout(1000);write(folder/(label+'-motion-partial.json'),page.evaluate('__step3.motion'))
 rows=page.evaluate('__step3.motion.rows');assert len({r['simTime']for r in rows})>=40;assert all(abs(r['simTime']-r['gpuTime'])<1e-8 for r in rows)
 ranges={n:max(r['boat'][n]for r in rows)-min(r['boat'][n]for r in rows)for n in['rootY','pitch','roll']};ranges['surface']=max(r['water']['heightAtBoat']for r in rows)-min(r['water']['heightAtBoat']for r in rows);assert ranges['surface']>.01 and ranges['rootY']>.005 and max(ranges['pitch'],ranges['roll'])>.005
 evidence={'calm':calm,'after':page.evaluate(SNAP),'simSeconds':rows[-1]['simTime']-rows[0]['simTime'],'distinctSimFrames':len(rows),'range':ranges,'rows':rows};write(folder/(label+'-motion.json'),evidence);picture(label+'-strong-waves');return {k:v for k,v in evidence.items()if k!='rows'}
def cameras_ui(label):
 before=page.evaluate('__bottleOcean.cameraRig.getState()');page.locator('[data-preset=top]').click();page.wait_for_timeout(1500);frames();top=page.evaluate('__bottleOcean.cameraRig.getState()');assert top['preset']=='top'and math.dist(before['position'],top['position'])>.1
 page.locator('#control-panel [data-action=toggleUI]').click();assert page.evaluate('document.body.classList.contains("ui-hidden")');page.wait_for_timeout(450);picture(label+'-top-without-ui');page.locator('#restore-ui').click();assert not page.evaluate('document.body.classList.contains("ui-hidden")');return {'before':before,'top':top,'nativeUIRestored':True,'trustedButtonEvents':page.evaluate('__step3.clicks')}
def props():return page.evaluate('''()=>{const a=[];__bottleOcean.scene.traverse(o=>{if(o.userData.propKind)a.push({uuid:o.uuid,kind:o.userData.propKind,position:o.parent.position.toArray()})});return a}''')
def ground_point():return page.evaluate('''()=>{const b=__bottleOcean,T=b.THREE,e=b.environment,ray=new T.Raycaster(),blocked=new Set([e.ocean,...e.lighthouse.hitObjects]),targets=[e.terrain,e.rocks].filter(Boolean);for(const o of e.raycastTargets)if(o&&!blocked.has(o)&&!blocked.has(o.parent)&&o.name!=='birds'&&o.name!=='seaBirds'&&!o.material?.transparent&&!targets.includes(o))targets.push(o);for(const z of[4,2,6,0,8,-2])for(const x of[-3,-1,1,3,-5,5]){const v=new T.Vector3(x,e.getSandHeight(x,z),z).project(b.camera),px=(v.x+1)*innerWidth/2,py=(1-v.y)*innerHeight/2;if(px<20||py<90||px>innerWidth-20||py>innerHeight-30||document.elementFromPoint(px,py)!==b.renderer.domElement)continue;ray.setFromCamera(new T.Vector2(px/innerWidth*2-1,1-py/innerHeight*2),b.camera);const hit=ray.intersectObjects(targets,true)[0];if(!hit||b.bottle.isInsideCavity(hit.point,.02)||hit.point.x< -24||hit.point.x>24||hit.point.z< -8||hit.point.z>14)continue;return {x:px,y:py,world:hit.point.toArray(),object:hit.object.name}}return null}''')
def sandbox():
 page.locator('[data-action=reset]').click();quality();page.wait_for_timeout(1500);frames();assert not props();rows=[]
 for kind in['rock','shell']:
  page.locator('[data-edit='+kind+']').click();point=ground_point();assert point;before=props();page.mouse.click(point['x'],point['y']);frames();after=props();assert len(after)==len(before)+1 and after[-1]['kind']==kind;rows.append({'kind':kind,'nativePoint':point,'before':before,'after':after});picture('production-placed-'+kind)
 page.locator('[data-action=undoProp]').click();frames();undo=props();assert len(undo)==1 and undo[0]['kind']=='rock';page.locator('[data-action=resetProps]').click();frames();assert not props();page.keyboard.press('Escape');assert page.evaluate('__bottleOcean.state.editMode')is None;return {'nativePlacements':rows,'afterUndo':undo,'afterReset':props(),'trustedActions':page.evaluate('__step3.clicks')}
def export(label):
 before=page.evaluate(SNAP)
 with page.expect_download(timeout=30000)as event:page.locator('[data-action=screenshot]').click()
 download=event.value;path=folder/(label+'-download.png');download.save_as(str(path));raw=path.read_bytes();assert raw[:8]==b'\x89PNG\r\n\x1a\n';size=list(struct.unpack('>II',raw[16:24]));expected=[round(before['canvas'][x]*min(before['dpr'],2))for x in['width','height']];assert size==expected and len(raw)>10000 and not download.failure();return {'filename':download.suggested_filename,'file':row(path),'PNG':size,'before':before,'downloadError':download.failure(),'originalButtonTrusted':page.evaluate('__step3.clicks.at(-1)')}
def host(url,label):
 new(url);page.wait_for_function('document.querySelector("main")?.dataset.layoutReady==="true"',timeout=90000,polling=100)
 toggled=False
 if page.locator('main').get_attribute('data-reading-mode')!='stable':page.locator('#tour-layout-toggle').click();toggled=True;page.wait_for_function('document.querySelector("main").dataset.readingMode==="stable"',timeout=15000)
 page.locator('article[data-experiment-station=C2]').scroll_into_view_if_needed();page.wait_for_timeout(800);page.locator('[data-project-select=lawson]').wait_for(state='visible');assert page.locator('[data-project-select=lawson]').is_enabled();assert page.locator('[data-project-select=courtyard]').is_enabled();picture(label+'-coding')
 own=[r for r in report['requests']if r['case']==case];bottle=[r for r in own if'/experiments/bottle-ocean/'in r['url']or'bottle-ocean-cover'in r['url']];assert not bottle;assert page.locator('iframe').count()==0;assert page.evaluate('typeof window.__bottleOcean')=='undefined'
 return {'url':page.url,'readingMode':page.locator('main').get_attribute('data-reading-mode'),'currentWorks':page.locator('[data-project-select]').evaluate_all('es=>es.map(e=>({id:e.dataset.projectSelect,enabled:!e.disabled}))'),'requests':own,'bottleRequests':bottle,'iframeCount':0,'bottleAPIInHost':False,'nativeModeToggleUsed':toggled}
pw=sync_playwright().start();browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=False,args=['--no-sandbox','--use-gl=angle','--use-angle=gl','--ignore-gpu-blocklist']);report['browserVersion']=browser.version
try:
 for id,origin,base in[('HTTP.dev',dev,'/'),('HTTP.production',prod,'/'),('HTTP.prefix',prod,prefix)]:check(id,'正确HTTP正文和静态文件闭包',lambda origin=origin,base=base:http_files(origin,base))
 if any(selected(x)for x in['DEV.load']):check('DEV.load','开发服务独立完整载入',lambda:load(dev+'/'+entry,'dev'))
 if any(selected(x)for x in['PRODUCTION.load','PRODUCTION.motion','PRODUCTION.camera-ui','PRODUCTION.sandbox','PRODUCTION.export']):
  check('PRODUCTION.load','构建根路径完整默认场景',lambda:load(prod+'/'+entry,'production'),force=True);check('PRODUCTION.motion','自然波场与船体连续响应',lambda:motion('production'));check('PRODUCTION.camera-ui','原镜头与界面隐藏恢复',lambda:cameras_ui('production'));check('PRODUCTION.sandbox','原生石头贝壳放置、撤销、恢复',sandbox);check('PRODUCTION.export','根路径原按钮真实PNG下载',lambda:export('production'))
 if any(selected(x)for x in['PREFIX.load','PREFIX.reload','PREFIX.motion','PREFIX.camera-ui','PREFIX.export']):
  check('PREFIX.load','真实项目前缀完整原页',lambda:load(prod+prefix+entry,'prefix',960,600,2),force=True)
  def reload():
   response=page.reload(wait_until='domcontentloaded');s=ready();assert hashlib.sha256(response.body()).hexdigest()==ENTRY_SHA;assert page.url==prod+prefix+entry;return {'afterReload':s,'bodySHA256':ENTRY_SHA}
  check('PREFIX.reload','前缀原入口刷新保持身份',reload);check('PREFIX.motion','前缀波场与船体真实响应',lambda:motion('prefix'));check('PREFIX.camera-ui','前缀镜头与界面',lambda:cameras_ui('prefix'));check('PREFIX.export','前缀原按钮真实PNG下载',lambda:export('prefix'))
 for id,url,label in[('HOST.dev',dev+'/','host-dev'),('HOST.production',prod+'/','host-production'),('HOST.prefix',prod+prefix,'host-prefix')]:check(id,'主站Coding区不提前运行新作品',lambda url=url,label=label:host(url,label))
finally:
 if context:context.unroute_all(behavior='ignoreErrors');context.close()
 browser.close();pw.stop();report['complete']=bool(report['checks'])and all(c['status']=='通过'for c in report['checks']);report['finishedAtShanghai']=now();save();print(json.dumps({'complete':report['complete'],'checks':len(report['checks']),'externalAttempts':len(report['externalAttempts']),'pageErrors':len(report['pageErrors']),'consoleErrors':sum(x['type']=='error'for x in report['console'])},ensure_ascii=False),flush=True)
if not report['complete']:raise SystemExit(1)
