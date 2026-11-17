from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from threading import Thread
import os,json,argparse,hashlib,shutil,traceback,ast
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).parent
ap=argparse.ArgumentParser();ap.add_argument('run');ap.add_argument('--main',action='store_true');ap.add_argument('--only',nargs='*');args=ap.parse_args();run=OUT/args.run;run.mkdir(exist_ok=False)
save=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
shutil.copy2(__file__,run/'test.py.txt');sources=[p for p in (ROOT/'src/tour').rglob('*') if p.is_file()]+list((ROOT/'src/assets/tool-marks').glob('*.svg'))+[ROOT/'dist/index.html']+list((ROOT/'dist/assets').glob('startTourPrototype*'))
save(run/'source-manifest.json',[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sources])
report={'startedAtShanghai':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'checks':[],'events':[],'complete':False,'clockModified':False,'physicalDevice':False,'main':args.main};failed=[];server=None
old=ast.parse((OUT.parent/'step-11/verify-departure.py').read_text());BASE=next(ast.literal_eval(n.value) for n in old.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='READ' for t in n.targets));(run/'base-read.js.txt').write_text(BASE)
READ='''()=>{const m=('''+BASE+''')(),r=document.querySelector('.ar-tools-browser'),p=r.querySelector('.ar-tool-help-panel'),b=r.querySelector('[data-action=help]'),h=r.querySelector('.ar-current-hint'),rect=e=>e.getBoundingClientRect().toJSON();return{...m,hint:{text:h.textContent,id:h.id,visible:getComputedStyle(h).display!=='none'&&getComputedStyle(h).visibility!=='hidden',described:document.getElementById(r.querySelector('.ar-tool-rail').getAttribute('aria-describedby'))?.textContent},controls:rect(r.querySelector('.ar-tool-controls')),help:{hidden:p.hidden,presentation:p.dataset.presentation,rect:rect(p),height:p.clientHeight,scrollHeight:p.scrollHeight,scrollTop:p.scrollTop,trigger:rect(b),expanded:b.getAttribute('aria-expanded'),rows:[...p.querySelectorAll('.ar-tool-help-item')].map(x=>x.textContent),note:p.querySelector('.ar-tool-help-note').textContent,headingFocus:document.activeElement===p.querySelector('h3'),close:rect(p.querySelector('[data-action=help-close]')),font:parseFloat(getComputedStyle(p).fontSize),scrollHint:!p.querySelector('.ar-tool-help-scroll-hint').hidden,live:p.getAttribute('aria-live')},root:rect(r),leave:document.querySelector('.ar-continue-slot .ar-hint')?.textContent,countLabel:r.querySelector('.ar-card-count').getAttribute('aria-label'),countLive:r.querySelector('.ar-card-count').getAttribute('aria-live'),helpNodes:r.querySelectorAll('.ar-tool-help-panel').length}}'''
if args.main:
 s=json.loads((OUT/'services-started.json').read_text());os.environ.update(s['browserEnvironment']);os.environ['PLAYWRIGHT_BROWSERS_PATH']='/workspace/.cache/ms-playwright';origin=s['origin']
else:
 payload=(OUT/'component-preview.html').read_bytes();save(run/'build.json',json.loads((OUT/'component-build.json').read_text()));(run/'loaded-component.html').write_bytes(payload)
 class Handler(BaseHTTPRequestHandler):
  def log_message(self,*a):pass
  def do_GET(self):self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers();self.wfile.write(payload)
 server=ThreadingHTTPServer(('127.0.0.1',0),Handler);Thread(target=server.serve_forever,daemon=True).start();origin=f'http://127.0.0.1:{server.server_port}'
PRESENT='''h=>{const v=__aboutRefreshPreview.view,a=h>=2.9&&h<3.7,p=(h-2.9)/.8;v.presentToolsDeparture({active:a,enabled:innerWidth>=1180&&!matchMedia('(prefers-reduced-motion:reduce)').matches,progress:p,readable:a&&p>=.3&&p<=.8});v.presentToolsTrack({active:a&&p>=.3&&p<=.8,allowed:innerWidth>=1180,automatic:false,top:70,bottom:innerHeight-40})}'''
try:
 with sync_playwright() as play:
  browser=play.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']+(['--use-gl=angle','--use-angle=gl','--ignore-gpu-blocklist'] if args.main else []));report['version']=browser.version
  def read(p):return p.evaluate(READ)
  def go(p,h=3.34):
   if args.main:
    if p.locator('main').get_attribute('data-reading-mode')=='stable':p.locator('.tour-reading-flow [data-flow-anchor='+('A3' if h<3.7 else 'B1')+']').scroll_into_view_if_needed();p.wait_for_timeout(250)
    else:
     p.evaluate('h=>scrollTo({top:h/12.3*(document.documentElement.scrollHeight-innerHeight),behavior:"instant"})',h);p.wait_for_function('h=>Math.abs(Number(document.querySelector("#tour-host").dataset.displayH)-h)<.001&&document.querySelector("#tour-host").dataset.cameraState==="settled"',arg=h,timeout=25000)
   else:p.evaluate(PRESENT,h)
  def setup(p,program=True,paused=False):
   p.goto(origin+('/?waterTime=2' if args.main else '/'),wait_until='domcontentloaded')
   if args.main:
    p.wait_for_function('document.querySelector("main")?.dataset.layoutReady==="true"',timeout=90000);go(p);p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.entranceReady==="true"',timeout=15000)
   else:
    p.wait_for_function('!!window.__aboutRefreshPreview');p.locator('[data-preview-station=A3]').click();p.wait_for_timeout(150);p.evaluate('()=>__aboutRefreshPreview.view.presentToolsEntrance({active:true,enabled:false,revealed:true})');go(p)
    if program:p.locator('[data-action=auto]').click()
   if program:
    p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.trackState==="running"');p.wait_for_timeout(900)
    if paused:p.locator('[data-action=auto]').click()
   p.mouse.move(10,80)
  def case(name,fn,paused=False,program=True,size=None,touch=False,video=False):
   if args.only and name not in args.only:return
   size=size or ((1440,900) if args.main else (1440,1100));opts={'viewport':{'width':size[0],'height':size[1]},'has_touch':touch,'is_mobile':touch}
   if video:opts.update(record_video_dir=str(run/'video'),record_video_size=opts['viewport'])
   ctx=browser.new_context(**opts);p=ctx.new_page();p.set_default_timeout(12000);errors=[];p.on('pageerror',lambda e:errors.append(str(e)));item={'id':name,'viewport':list(size),'status':'失败','touch':touch}
   try:
    setup(p,program,paused);data=fn(p);assert not errors,errors
    if p.locator('.ar-tools-browser').count():
     m=read(p);assert not m['duplicates'] and m['overflow']<=1,m;assert m['helpNodes']==1;assert m['hint']['visible'] and m['hint']['text']==m['hint']['described'];assert m['countLive']=='off'
    save(run/(name+'-data.json'),data);p.screenshot(path=str(run/(name+'.png')));item.update(status='通过',data=name+'-data.json')
   except Exception as e:
    failed.append(name);item.update(error=str(e),traceback=traceback.format_exc())
    try:save(run/(name+'-failure.json'),read(p));p.screenshot(path=str(run/(name+'-failure.png')))
    except Exception:pass
   finally:
    report['checks'].append(item);report['events'].extend(errors);save(run/'browser.json',report);ctx.close()
    if video:item['video']=str(Path(p.video.path()).relative_to(run));save(run/'browser.json',report)
  def open_help(p,keyboard=False):
   if keyboard:p.locator('[data-action=help]').focus();p.keyboard.press('Enter')
   else:p.locator('[data-action=help]').click()
   p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.helpOpen==="true"');p.wait_for_timeout(120);return read(p)
  def close_help(p,escape=False):
   if escape:p.keyboard.press('Escape')
   else:p.locator('[data-action=help-close]').click()
   p.wait_for_timeout(150);m=read(p);assert m['help']['hidden'] and m['help']['expanded']=='false';return m
  def card(m,id):return next(c for c in m['cards'] if c['id']==id)
  def same(a,b):assert [(c['id'],c['instance']) for c in a['cards']]==[(c['id'],c['instance']) for c in b['cards']];assert a['canvas']==b['canvas']
  def hover(p,pin=False):
   b=p.locator('.ar-tool-card[data-tool-id=comfyui] .ar-card-front').bounding_box();p.mouse.move(b['x']+b['width']/2,b['y']+b['height']*.45);p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.hoverState==="reading"')
   if pin:
    b=p.locator('.ar-tool-card[data-tool-id=comfyui] button').bounding_box();p.mouse.click(b['x']+b['width']/2,b['y']+b['height']/2);p.wait_for_timeout(400)
   return read(p)
  def geometry(a,b):
   assert abs(a['root']['height']-b['root']['height'])<.6 and abs(a['rail']['height']-b['rail']['height'])<.6
   for key in ['left','top','right','bottom']:assert abs(a['rail'][key]-b['rail'][key])<.6,(a['rail'],b['rail'])
   assert a.get('mode')==b.get('mode')
  def automatic(p):
   a=read(p);assert a['hint']['text']=='自动展示已开启 · 滚轮调速';b=open_help(p);assert b['d']['trackEnabled']=='true' and b['d']['trackFramePending']=='false';geometry(a,b);p.wait_for_timeout(650);c=read(p);assert b['d']['trackOffset']==c['d']['trackOffset'];d=close_help(p);assert d['d']['trackEnabled']=='true';p.wait_for_timeout(1100);e=read(p);same(a,e);assert float(e['d']['trackSpeed'])>25;return {'before':a,'open':b,'held':c,'closed':d,'resumed':e}
  def paused(p):
   a=read(p);assert a['hint']['text']=='已暂停 · 滚轮仍可浏览';b=open_help(p);c=close_help(p,True);p.wait_for_timeout(850);d=read(p);assert d['d']['trackEnabled']=='false' and d['d']['trackFramePending']=='false' and a['d']['trackOffset']==d['d']['trackOffset'];return {'before':a,'open':b,'closed':c,'still':d}
  def preview_hold(p):
   a=hover(p);assert a['hint']['text']=='临时阅读 · 移开后继续展示';b=open_help(p);p.wait_for_timeout(800);c=read(p);assert c['d']['trackEnabled']=='true' and c['d']['trackFramePending']=='false' and c['d']['detailMode']=='summary';assert b['d']['trackOffset']==c['d']['trackOffset'];close_help(p);p.wait_for_timeout(1200);d=read(p);assert float(d['d']['trackSpeed'])>25;return {'preview':a,'open':b,'heldAfterPreviewClosed':c,'resumed':d}
  def pin_help(p):
   a=hover(p,True);assert a['hint']['text']=='已固定 · 滚轮浏览页面';b=open_help(p);assert b['d']['readingId']=='comfyui' and not card(b,'comfyui')['body']['hidden'];c=close_help(p,True);assert c['d']['detailMode']=='pinned' and c['focus']['action']=='help';p.keyboard.press('Escape');p.wait_for_timeout(550);d=read(p);assert d['d']['detailMode']=='summary' and d['d']['trackEnabled']=='false';return {'pinned':a,'open':b,'firstEscape':c,'secondEscape':d}
  def outside(p,kind):
   a=open_help(p)
   if kind=='category':p.locator('[data-category=G4]').click()
   elif kind=='auto':p.locator('[data-action=auto]').click()
   else:
    b=p.locator('.ar-tool-card[data-tool-id=midjourney] button').bounding_box();p.mouse.click(b['x']+b['width']/2,b['y']+b['height']/2)
   p.wait_for_timeout(700);m=read(p);assert m['help']['hidden']
   if kind=='category':assert m['d']['category']=='G4' and len(m['cards'])==6
   elif kind=='auto':assert m['d']['trackEnabled']=='false'
   else:assert m['d']['detailMode']=='pinned' and m['d']['readingId']=='midjourney'
   return {'open':a,'afterFirstClick':m}
  def keyboard(p):
   a=read(p);b=open_help(p,True);assert b['help']['headingFocus'] and b['d']['trackEnabled']==a['d']['trackEnabled'];p.keyboard.press('Tab');p.wait_for_timeout(100);c=read(p);assert c['focus']['action']=='help-close';d=close_help(p,True);assert d['focus']['action']=='help' and d['d']['trackEnabled']==a['d']['trackEnabled'];assert d['hint']['text']=='Tab 选择 · Enter 操作';return {'before':a,'opened':b,'tabbed':c,'escaped':d}
  def panel_wheel(p):
   a=open_help(p);assert a['help']['presentation']=='popover' and a['help']['scrollHint'];r=a['help']['rect'];p.mouse.move(r['x']+r['width']/2,r['y']+r['height']*.72);p.mouse.wheel(0,220);p.wait_for_timeout(250);b=read(p);assert b['help']['scrollTop']>20 and b['y']==a['y'] and b['d']['trackOffset']==a['d']['trackOffset'];return {'beforeWheel':a,'afterWheel':b}
  def panel_keys(p):
   a=open_help(p,True);p.keyboard.press('PageDown');p.wait_for_timeout(300);b=read(p);assert b['help']['scrollTop']>20 and b['y']==a['y'];return {'opened':a,'afterPageDown':b}
  def small_category(p):
   p.locator('[data-category=G2]').click();p.wait_for_timeout(200);a=open_help(p);assert len(a['cards'])==2 and all('自动展示' not in row for row in a['help']['rows']);assert '滚轮控制' not in a['help']['rows'][0];assert p.locator('[data-action=auto]').is_hidden();return a
  def all_tools(p):
   hover(p,True);a=open_help(p);p.locator('[data-action=all]').click();p.wait_for_timeout(200);assert p.locator('.ar-catalog .ar-card-detail:not([hidden])').count()==22;assert p.locator('.ar-catalog-instruction').inner_text()=='已列出全部工具，返回后接续原浏览位置。';p.locator('.ar-all-tools [data-action=return]').first.click();p.wait_for_timeout(600);b=read(p);assert b['help']['hidden'] and b['d']['readingId']=='comfyui' and b['d']['detailMode']=='pinned';return {'open':a,'returned':b}
  def caption_motion(p):
   a=hover(p);p.evaluate('''()=>{window.__texts=[];window.__oldHint=document.querySelector('.ar-current-hint').firstChild;window.__oldRows=[...document.querySelector('.ar-tool-help-list').children];window.__mo=new MutationObserver(records=>__texts.push(...records.map(r=>r.type)));__mo.observe(document.querySelector('.ar-tool-controls'),{subtree:true,childList:true,characterData:true});__mo.observe(document.querySelector('.ar-tool-help-list'),{subtree:true,childList:true,characterData:true})}''');f=card(a,'comfyui')['front']
   for x,y in [(.3,.3),(.7,.3),(.7,.7),(.5,.5)]:p.mouse.move(f['left']+f['width']*x,f['top']+f['height']*y);p.wait_for_timeout(170)
   result=p.evaluate('()=>{__mo.disconnect();return{mutations:__texts,sameHint:__oldHint===document.querySelector(".ar-current-hint").firstChild,sameRows:__oldRows.every((n,i)=>n===document.querySelector(".ar-tool-help-list").children[i])}}');assert not result['mutations'] and result['sameHint'] and result['sameRows'],result;return {'preview':a,'mutationCheck':result,'after':read(p)}
  def hints_departure(p):
   go(p,3.56);p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.departure==="exiting"');a=read(p);assert a['hint']['text']=='正在离开工具卡片';p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.departure==="departed"');go(p);p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.departure==="returning"');b=read(p);assert b['hint']['text']=='返回中 · 可移入卡面暂停';p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.departure==="idle"');return {'exiting':a,'returning':b,'settled':read(p)}
  def lifecycle(p,kind):
   hover(p,True);a=open_help(p)
   if kind=='resize':p.set_viewport_size({'width':390,'height':844})
   elif kind=='reduced':p.emulate_media(reduced_motion='reduce')
   elif kind=='font':p.evaluate('document.documentElement.style.fontSize="200%"');p.evaluate('()=>window.__aboutRefreshPreview?.fit()')
   else:p.evaluate('Object.defineProperty(document,"hidden",{configurable:true,get:()=>true});document.dispatchEvent(new Event("visibilitychange"))');p.wait_for_timeout(70);p.evaluate('delete document.hidden;document.dispatchEvent(new Event("visibilitychange"))')
   p.wait_for_timeout(850);b=read(p);assert b['help']['hidden'] and b['d']['helpOpen']=='false' and b['d']['readingId']=='comfyui' and not card(b,'comfyui')['body']['hidden'];return {'before':a,'after':b,'simulatedHidden':kind=='hidden'}
  def snapshot(p):
   hover(p,True);open_help(p);a=read(p);p.evaluate('()=>{window.__old=__aboutRefreshPreview.view.toolsElement;window.__snap=__aboutRefreshPreview.view.captureState();__aboutRefreshPreview.remount(__snap)}');p.wait_for_timeout(120);p.evaluate('()=>__aboutRefreshPreview.view.presentToolsEntrance({active:true,enabled:false,revealed:true})');go(p);p.wait_for_timeout(600);b=read(p);assert b['help']['hidden'] and b['d']['readingId']=='comfyui' and b['d']['detailMode']=='pinned';assert 'help' not in json.dumps(b['snapshot']);return {'open':a,'restored':b,'old':p.evaluate('({...__old.dataset})')}
  def dispose(p):
   open_help(p);p.evaluate('()=>{window.__old=__aboutRefreshPreview.view.toolsElement;__aboutRefreshPreview.view.dispose()}');p.wait_for_timeout(400);m=p.evaluate('({connected:__old.isConnected,d:{...__old.dataset}})');assert not m['connected'] and m['d']['helpOpen']=='false' and m['d']['trackFramePending']=='false';return m
  def native(p,large=False,wide=False):
   if wide:p.locator('#tour-layout-toggle').click();p.wait_for_timeout(450);go(p)
   if large:p.evaluate('document.documentElement.style.fontSize="200%"');p.wait_for_timeout(500);p.evaluate('()=>window.__aboutRefreshPreview?.fit()')
   p.locator('[data-action=help]').scroll_into_view_if_needed();p.locator('[data-action=help]').tap() if p.evaluate('navigator.maxTouchPoints>0') else p.locator('[data-action=help]').click();p.wait_for_timeout(500);a=read(p);assert not a['help']['hidden'] and a['help']['presentation']=='inline';p.locator('.ar-tool-help-panel').scroll_into_view_if_needed();p.wait_for_timeout(250);b=read(p);assert not b['help']['hidden'] and b['help']['font']>=16 and b['help']['close']['height']>=44 and b['help']['trigger']['height']>=44;assert b['help']['rect']['width']<=p.viewport_size['width']-24;p.screenshot(path=str(run/('native-large-open.png' if large else 'native-wide-open.png' if wide else f'native-{p.viewport_size["width"]}-open.png')));close_help(p);return {'opened':a,'scrolledToHelp':b,'closed':read(p)}
  def guided_help(p):
   p.locator('#tour-guide').click();p.wait_for_function('document.querySelector("#tour-host").dataset.guidePhase==="reading"');a=open_help(p);assert p.locator('#tour-guide').get_attribute('aria-pressed')=='false' and a['d']['trackEnabled']=='true';close_help(p);p.wait_for_timeout(1100);b=read(p);assert float(b['d']['trackSpeed'])>25 and p.locator('#tour-guide').get_attribute('aria-pressed')=='false';return {'open':a,'closed':b}
  def entrance_help(p):
   p.goto(origin+'/?waterTime=2');p.wait_for_function('document.querySelector("main")?.dataset.layoutReady==="true"',timeout=90000);go(p);p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.entrance==="playing"');a=open_help(p);assert a['d']['entrance']=='cancelled';b=close_help(p);assert b['d']['trackEnabled']=='false';go(p,4.95);go(p);p.wait_for_timeout(500);c=read(p);assert c['d']['entrancePlays']==a['d']['entrancePlays'];return {'openedDuringEntrance':a,'closed':b,'returned':c}
  def continue_help(p):
   hover(p,True);a=open_help(p);p.locator('[data-action=continue]').click();p.wait_for_function('document.querySelector("#tour-host").dataset.filmStation==="B1"&&document.querySelector("#tour-host").dataset.cameraState==="settled"');assert read(p)['help']['hidden'];go(p);p.wait_for_timeout(650);b=read(p);assert b['d']['detailMode']=='pinned' and b['d']['readingId']=='comfyui';return {'open':a,'returned':b}
  def bio(p):
   a=open_help(p);go(p,1.74);p.locator('[data-about-details=identity] summary').focus();p.keyboard.press('Enter');assert p.locator('[data-about-details=identity]').get_attribute('open') is not None;go(p,2.54);p.locator('[data-about-details=experience] summary').focus();p.keyboard.press('Enter');assert p.locator('[data-about-details=experience]').get_attribute('open') is not None;go(p);p.wait_for_timeout(300);b=read(p);assert b['help']['hidden'];return {'open':a,'returned':b}
  def demo(p):
   a=open_help(p);p.wait_for_timeout(500);r=a['help']['rect'];p.mouse.move(r['x']+r['width']/2,r['y']+r['height']*.7);p.mouse.wheel(0,200);p.wait_for_timeout(500);close_help(p,True);p.wait_for_timeout(900);hover(p,True);b=open_help(p);p.wait_for_timeout(700);c=close_help(p,True);assert c['d']['detailMode']=='pinned';p.wait_for_timeout(400);return {'open':a,'pinnedOpen':b,'closed':c}
  def hybrid_touch(p):
   assert p.evaluate('matchMedia("(hover:hover) and (pointer:fine)").matches');a=read(p);assert a['d']['trackMode']=='program'
   p.locator('[data-action=help]').dispatch_event('pointerdown',{'pointerType':'touch','pointerId':7,'isPrimary':True,'buttons':1});p.locator('[data-action=help]').dispatch_event('click',{'detail':1});p.wait_for_timeout(300);b=read(p);assert b['d']['toolInput']=='touch' and not b['help']['hidden'];assert '滚轮' not in b['help']['rows'][0] and '移入' not in next(r for r in b['help']['rows'] if r.startswith('返回卡片'))
   return {'simulatedHybridTouch':True,'before':a,'touchInstructions':b}
  def native_handoff(p):
   a=read(p);r=a['rail'];p.mouse.move((r['left']+r['right'])/2,(r['top']+r['bottom'])/2);p.mouse.wheel(110,0);p.wait_for_timeout(220);b=read(p);assert b['d']['trackMode']=='native' and b['railX']>30 and '滚轮调速' not in b['hint']['text'];c=open_help(p);assert '滚轮' not in c['help']['rows'][0] and '上一张' in c['help']['rows'][0];close_help(p);p.locator('[data-action=auto]').click();p.wait_for_timeout(1600);d=read(p);assert d['d']['trackMode']=='program' and d['hint']['text']=='自动展示已开启 · 滚轮调速';return {'before':a,'native':b,'nativeHelp':c,'programAgain':d}
  def help_return(p):
   a=read(p);go(p,3.56);p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.departure==="departed"');go(p);p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.departure==="returning"');b=open_help(p);assert b['d']['departureOwned']=='false' and b['d']['trackDepartureHeld']=='false' and b['d']['hoverDepartureHeld']=='false' and b['d']['trackEnabled']=='false';same(a,b);c=close_help(p);assert c['d']['trackEnabled']=='false' and c['d']['departureFramePending']=='false';return {'before':a,'openedDuringReturn':b,'closed':c}
  def touch_return(p):
   go(p,3.56);p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.departure==="departed"');p.locator('.ar-tools-browser').dispatch_event('pointerdown',{'pointerType':'touch','pointerId':9,'isPrimary':True});go(p);p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.departure==="returning"');a=read(p);assert a['d']['toolInput']=='touch' and a['hint']['text']=='正在返回原浏览位置';p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.departure==="idle"');return {'simulatedHybridTouch':True,'returning':a,'returned':read(p)}
  case('hybrid-touch-instructions-follow-last-input',hybrid_touch);case('native-horizontal-handoff-updates-instructions',native_handoff);case('first-help-click-interrupts-return',help_return,paused=True);case('hybrid-touch-return-caption',touch_return,paused=True)
  case('automatic-help-holds-and-restores',automatic);case('paused-help-stays-paused',paused,paused=True);case('preview-and-help-holds-combine',preview_hold);case('fixed-reading-escape-priority',pin_help);case('outside-category-first-click',lambda p:outside(p,'category'));case('outside-auto-first-click',lambda p:outside(p,'auto'));case('outside-card-first-click',lambda p:outside(p,'card'));case('keyboard-open-tab-escape-preserves-choice',keyboard);case('panel-wheel-stays-in-help',panel_wheel);case('panel-pagedown-stays-in-help',panel_keys);case('fitting-category-accurate-instructions',small_category);case('all-tools-copy-and-fixed-return',all_tools);case('hover-no-caption-or-help-dom-churn',caption_motion);case('departure-and-return-captions',hints_departure,paused=True);case('resize-closes-help-preserves-pin',lambda p:lifecycle(p,'resize'));case('reduced-closes-help-preserves-pin',lambda p:lifecycle(p,'reduced'));case('font-closes-help-preserves-pin',lambda p:lifecycle(p,'font'));case('hidden-closes-help-preserves-pin',lambda p:lifecycle(p,'hidden'))
  if args.main:
   case('help-stops-guide-only',guided_help);case('entrance-first-help-interrupts-once',entrance_help);case('continue-closes-help-preserves-pin',continue_help);case('identity-experience-native-details',bio);case('wide-stable-inline-help',lambda p:native(p,wide=True));case('phone-touch-inline-help',native,size=(390,844),program=False,touch=True);case('narrow-touch-inline-help',native,size=(320,740),program=False,touch=True);case('large-text-inline-help',lambda p:native(p,large=True),size=(800,600),program=False);case('large-desktop-popup',automatic,size=(1920,1080));case('actual-guidance-demonstration',demo,video=True)
  else:case('snapshot-restores-reading-with-help-closed',snapshot);case('dispose-open-help-cleans-listeners',dispose)
  report['complete']=not failed;browser.close();report['browserClosed']=True
finally:
 if server:server.shutdown();server.server_close();report['serverClosed']=True
 report['finishedAtShanghai']=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat();save(run/'browser.json',report)
print(json.dumps({'checks':len(report['checks']),'passed':len(report['checks'])-len(failed),'failures':failed},ensure_ascii=False));raise SystemExit(1 if failed else 0)
