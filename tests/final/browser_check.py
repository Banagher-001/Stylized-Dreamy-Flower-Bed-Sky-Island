"""Optional final verification: requires Playwright and Pillow; app runtime stays Node-only."""
from pathlib import Path
from io import BytesIO
import os,json,math,argparse,time
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser();parser.add_argument('--engine',choices=['chromium','firefox','webkit'],required=True);parser.add_argument('--production',default='http://127.0.0.1:4174');parser.add_argument('--development',default='http://127.0.0.1:5173');parser.add_argument('--reference',type=Path);args=parser.parse_args()
OUT=ROOT/'docs/evidence/step-9';OUT.mkdir(parents=True,exist_ok=True);checks=[];issues=[]
def record(name,evidence):checks.append({'check':name,'outcome':'passed','evidence':evidence});print(args.engine+': '+name,flush=True)
def watch(q):
 q.on('pageerror',lambda e:issues.append({'type':'exception','text':str(e)}))
 q.on('console',lambda m:issues.append({'type':m.type,'text':m.text})if m.type in('warning','error')else None)
 q.on('response',lambda r:issues.append({'type':'http','text':f'{r.status} {r.url}'})if r.status>=400 else None)
def ready(q):q.wait_for_selector('#scene-host[data-render-state="ready"]')
def image(q):
 q.evaluate('()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
 return Image.open(BytesIO(q.locator('canvas').screenshot())).convert('RGB')
def same(a,b):return ImageChops.difference(a,b).getbbox()is None
def metrics(q):return q.locator('canvas').evaluate('''c=>{const r=c.getBoundingClientRect();return {width:c.width,height:c.height,cssWidth:r.width,cssHeight:r.height,dpr:devicePixelRatio,...c.dataset,canvasCount:document.querySelectorAll('canvas').length,overflow:document.documentElement.scrollWidth>innerWidth};}''')
def dimensions(m,mode='pixel',profile=384):
 assert m['renderMode']==mode and m['canvasCount']==1 and not m['overflow'],m
 assert abs(m['cssWidth']-m['cssHeight'])<1,m
 assert abs(m['width']-math.floor(m['cssWidth'])*min(2,m['dpr']))<2,m
 assert max(int(m['sampleWidth']),int(m['sampleHeight']))==(min(profile,max(m['width'],m['height']))if mode=='pixel'else max(m['width'],m['height'])),m

HTML='<!doctype html><style>html,body{margin:0}#capture{width:640px;height:640px}canvas{display:block;width:100%;height:100%}canvas[data-render-mode=pixel]{image-rendering:pixelated}</style><div id="capture"></div>'
with sync_playwright()as p:
 kind=getattr(p,args.engine)
 options={'headless':args.engine=='chromium'}
 if args.engine=='chromium':options.update(executable_path=os.environ.get('CHROMIUM_EXECUTABLE','/usr/bin/chromium'),args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 if args.engine=='firefox':options['firefox_user_prefs']={'webgl.force-enabled':True}
 if args.engine=='webkit'and os.environ.get('COURTYARD_WEBKIT_EXECUTABLE'):options['executable_path']=os.environ['COURTYARD_WEBKIT_EXECUTABLE']
 b=kind.launch(**options);c=b.new_context(viewport={'width':1440,'height':1000},device_scale_factor=1);q=c.new_page();watch(q)
 frames={}
 for mode in ['native','pixel']:
  q.goto(args.production+f'/?waterTime=2&render={mode}',wait_until='networkidle');ready(q);dimensions(metrics(q),mode);frames[mode]=image(q);assert len(frames[mode].getcolors(1000000))>32,'Canvas did not visibly present the scene'
  frames[mode].save(OUT/f'{args.engine}-composition-{mode}.png');q.screenshot(path=str(OUT/f'{args.engine}-desktop-{mode}.png'),full_page=True)
  q.goto(args.development+f'/?waterTime=2&render={mode}',wait_until='networkidle');ready(q);assert same(image(q),frames[mode])
  if args.reference:assert same(frames[mode],Image.open(args.reference/f'baseline-{mode}.png').convert('RGB'))
 record('production/native/pixel render and same-engine development equivalence',{'metrics':metrics(q),'sameEnvironmentReferenceExact':bool(args.reference)})
 gpu=q.evaluate("(engine)=>{const g=document.querySelector('canvas').getContext('webgl2'),e=engine==='firefox'?null:g.getExtension('WEBGL_debug_renderer_info');return {version:g.getParameter(g.VERSION),renderer:e?g.getParameter(e.UNMASKED_RENDERER_WEBGL):g.getParameter(g.RENDERER),floatTarget:!!g.getExtension('EXT_color_buffer_float')};}",args.engine)
 record('actual WebGL2 renderer and float capability',gpu)

 q.goto(args.production+'/?waterTime=2',wait_until='networkidle');ready(q)
 for profile in [320,448]:
  q.goto(args.production+f'/?waterTime=2&pixelSize={profile}',wait_until='networkidle');ready(q);dimensions(metrics(q),profile=profile)
 q.goto(args.production+'/?waterTime=2&render=bad&pixelSize=999&finish=bad',wait_until='networkidle');ready(q);dimensions(metrics(q));assert same(image(q),frames['pixel'])
 for query in ['waterTime=','waterTime=-1','waterTime=NaN','waterTime=Infinity','waterTime=86401']:
  q.goto(args.production+'/?'+query,wait_until='networkidle');ready(q);assert q.locator('#scene-host').get_attribute('data-motion-state')=='running',query
 for value in ['0','2','86400']:
  q.goto(args.production+'/?waterTime='+value,wait_until='networkidle');ready(q);assert q.locator('#scene-host').get_attribute('data-motion-state')=='paused';assert float(q.locator('#scene-host').get_attribute('data-scene-time'))==float(value)
 record('valid and invalid review parameters restore or safely fall back',{'profiles':[320,384,448],'validTimes':[0,2,86400],'invalidTimes':['empty',-1,'NaN','Infinity',86401]})

 q.goto(args.production+'/?waterTime=2',wait_until='networkidle');ready(q)
 q.get_by_role('button',name='正常画面',exact=True).focus();q.keyboard.press('Tab');assert q.locator(':focus').get_attribute('data-mode')=='pixel'
 q.keyboard.press('Tab');assert q.locator(':focus').get_attribute('id')=='motion-control';outline=q.locator(':focus').evaluate('e=>({style:getComputedStyle(e).outlineStyle,width:getComputedStyle(e).outlineWidth})');assert outline['style']!='none'and float(outline['width'].replace('px',''))>=2
 q.keyboard.press('Space');q.wait_for_function("Number(document.querySelector('#scene-host').dataset.sceneTime)>2.01")
 q.keyboard.press('Enter');paused=image(q);clock=q.locator('#scene-host').get_attribute('data-scene-time');q.wait_for_timeout(250);assert same(image(q),paused)and q.locator('#scene-host').get_attribute('data-scene-time')==clock
 assert q.locator('#render-status').inner_text()=='场景动效已暂停。'
 record('keyboard, focus, play/pause, frozen scene and accessible status',{'outline':outline,'pausedTime':clock})

 rc=b.new_context(viewport={'width':1280,'height':900},reduced_motion='reduce');r=rc.new_page();watch(r);r.goto(args.production+'/',wait_until='networkidle');ready(r)
 assert r.locator('#scene-host').get_attribute('data-motion-state')=='paused';still=image(r);r.wait_for_timeout(200);assert same(still,image(r))
 r.get_by_role('button',name='播放动效',exact=True).click();r.wait_for_selector('#scene-host[data-motion-state="running"]');r.get_by_role('button',name='暂停动效',exact=True).click();r.emulate_media(reduced_motion='no-preference');r.wait_for_timeout(100);assert r.locator('#scene-host').get_attribute('data-motion-state')=='paused';rc.close()
 record('reduced-motion preference fixture and manual override',{'method':'browser preference emulation','realOSPreferenceTested':False})

 sizes=[]
 for width,height,dpr in [(280,600,1),(320,568,1),(390,844,2),(768,1024,1.5),(1440,1000,1.25),(1920,1080,2),(844,390,3)]:
  kwargs={'viewport':{'width':width,'height':height},'device_scale_factor':dpr,'has_touch':width<700}
  if args.engine!='firefox':kwargs['is_mobile']=width<700
  cc=b.new_context(**kwargs);t=cc.new_page();watch(t);t.goto(args.production+'/?waterTime=2',wait_until='networkidle');ready(t);m=metrics(t);dimensions(m)
  buttons=t.locator('button').evaluate_all('bs=>bs.map(b=>{const r=b.getBoundingClientRect();return {width:r.width,height:r.height}})');assert all(x['width']>=44 and x['height']>=44 for x in buttons)
  if width==390:
   t.screenshot(path=str(OUT/f'{args.engine}-mobile.png'),full_page=True)
   t.get_by_role('button',name='播放动效',exact=True).tap();t.wait_for_function("Number(document.querySelector('#scene-host').dataset.sceneTime)>2.01");t.get_by_role('button',name='暂停动效',exact=True).tap()
  sizes.append(m);cc.close()
 record('seven viewport/DPR combinations, 44px targets and simulated touch',sizes)

 q.goto(args.production+'/?waterTime=2',wait_until='networkidle');ready(q);q.evaluate("window.__loss=document.querySelector('canvas').getContext('webgl2').getExtension('WEBGL_lose_context')")
 if q.evaluate('!!window.__loss'):
  for i in range(2):
   q.evaluate('window.__loss.loseContext()');q.wait_for_selector('#scene-host[data-render-state="context-lost"]');assert q.locator('#scene-notice').is_visible()and q.locator('button:enabled').count()==0
   q.evaluate('window.__loss.restoreContext()');ready(q);assert not q.locator('#scene-notice').is_visible()and q.locator('button:enabled').count()==3;assert same(image(q),frames['pixel'])
  record('two real context losses restore the paused scene and controls',{'cycles':2})
 else:record('context loss capability recorded',{'available':False,'status':'not exercised; extension unavailable'})

 palette=[]
 for storage in ['auto','byte']:
  g=c.new_page();watch(g);g.route('**/__final_palette__',lambda route:route.fulfill(content_type='text/html',body=HTML));g.goto(args.development+'/__final_palette__')
  hexes=g.evaluate((ROOT/'tests/final/palette_setup.js').read_text(),{'storage':storage});native=image(g);native.save(OUT/f'{args.engine}-palette-{storage}-native.png');g.evaluate("window.__test.view.setMode('pixel')");pixel=image(g);pixel.save(OUT/f'{args.engine}-palette-{storage}-pixel.png');stats=g.evaluate('window.__test.view.getStats()');error=0
  for i,hex in enumerate(hexes):
   wanted=tuple(bytes.fromhex(hex[1:]));x,y=80+160*(i%4),80+160*(i//4);a=native.getpixel((x,y));v=pixel.getpixel((x,y));error=max(error,max(abs(v[k]-wanted[k])for k in range(3)),max(abs(v[k]-a[k])for k in range(3)))
  assert error<=2,(storage,error,[(native.getpixel((80+160*(i%4),80+160*(i//4))),pixel.getpixel((80+160*(i%4),80+160*(i//4))))for i in range(16)])
  g.evaluate('window.__test.checker()')
  checker=g.evaluate('''()=>new Promise(resolve=>requestAnimationFrame(()=>{const v=window.__test.view;v.renderOnce();const gl=v.canvas.getContext('webgl2'),a=new Uint8Array(640*640*4);gl.readPixels(0,0,640,640,gl.RGBA,gl.UNSIGNED_BYTE,a);const colors=new Set();let wrong=0;for(let i=0;i<a.length;i+=4)colors.add([a[i],a[i+1],a[i+2]].join(','));for(const y of [0,1,2,97,638,639])for(let x=0;x<640;x++){const i=((639-y)*640+x)*4,wanted=(Math.floor(x/2)+Math.floor(y/2))%2===0?255:0;if(a[i]!==wanted||a[i+1]!==wanted||a[i+2]!==wanted)wrong++;}resolve({colors:[...colors].sort(),wrongCells:wrong,readback:'same-draw GPU framebuffer inside RAF'});}));''')
  assert checker['colors']==['0,0,0','255,255,255']and checker['wrongCells']==0,checker
  palette.append({'requested':storage,'actual':stats['pixel']['storage'],'maxChannelError':error,'checker':checker});g.evaluate('window.__test.dispose()');g.close()
 record('GPU color palette and exact nearest-neighbor cells in both storage paths',palette)

 q.goto(args.development+'/?waterTime=2',wait_until='networkidle');ready(q)
 lifecycle=q.evaluate('''async()=>{const {createScene}=await import('/src/scene/createScene.ts');const {createRenderer}=await import('/src/rendering/createRenderer.ts');const h=document.createElement('div');h.style.cssText='width:96px;height:96px';document.body.append(h);let lost=0;for(let i=0;i<20;i++){const w=createScene(),v=createRenderer(h,'pixel',w.setAspect);v.setAnimating(false);v.start(w.scene,w.camera,()=>w.update(2));await new Promise(requestAnimationFrame);if(v.getStats().calls===0)throw new Error('Cycle did not render');const gl=v.canvas.getContext('webgl2');v.dispose();v.dispose();w.dispose();w.dispose();if(gl.isContextLost())lost++;}h.remove();return {cycles:20,contextsReleased:lost};}''')
 assert lifecycle['contextsReleased']==20,lifecycle;assert q.locator('canvas').count()==1 and q.locator('#scene-host').get_attribute('data-render-state')=='ready'
 record('20 initialization/disposal cycles explicitly release context slots',lifecycle)
 known=[x for x in issues if args.engine=='firefox'and x['type']=='warning'and 'Depth texture comparison requests'in x['text']and 'implementation-defined'in x['text']]
 expectedLoss=[x for x in issues if args.engine=='firefox'and x['type']=='warning'and 'WebGL context was lost.'in x['text']]
 unexpected=[x for x in issues if x not in known and x not in expectedLoss]
 assert not unexpected,{'count':len(unexpected),'first':unexpected[:5]}
 record('normal-workflow diagnostics recorded without hiding browser output',{'unexpectedIssues':unexpected,'knownBrowserWarnings':known,'expectedContextLossDiagnostics':expectedLoss,'zeroWarningTargetMet':not known})
 if known:checks[-1]['outcome']='passed_with_notes'
 result={'engine':args.engine,'browserVersion':b.version,'environment':'Linux software rendering / Xvfb or headless; not real-device acceptance','gpu':gpu,'checks':checks,'issues':issues}
 (OUT/f'verification-{args.engine}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'engine':args.engine,'passed':len(checks),'issues':len(issues)}),flush=True);b.close()
