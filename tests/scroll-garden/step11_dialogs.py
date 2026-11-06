"""Difficult viewer layouts, native modal ownership, pinch and full graphic-failure reading."""
import argparse
from playwright.sync_api import sync_playwright
from step11_common import *
parser=argparse.ArgumentParser();parser.add_argument('--engine',choices=['chromium','firefox','webkit'],default='chromium');parser.add_argument('--url',default='http://127.0.0.1:4173');args=parser.parse_args();rows=[]
def frames_ready(page):
 page.wait_for_function('document.querySelector("main").dataset.layoutReady==="true"');frames(page)
def position(page):return page.evaluate('({y:scrollY,anchor:document.querySelector("main").dataset.flowAnchor,mode:document.querySelector("main").dataset.readingMode})')
def visible_control(page,selector):
 r=page.locator(selector).bounding_box();assert r and r['width']>=44 and r['height']>=44 and r['y']>=-.1 and r['y']+r['height']<=page.evaluate('innerHeight')+.5,(selector,r);return r
def choose_flow(page):
 if page.locator('main').get_attribute('data-reading-mode')!='stable':page.locator('#tour-layout-toggle').click()
 frames(page)
def click_from_flow(page,selector):
 page.locator(selector).evaluate('e=>e.scrollIntoView({block:"center",behavior:"instant"})');frames(page);before=position(page);page.locator(selector).click();frames(page);return before
def returned(page,before):
 page.wait_for_function('document.querySelector("#tour-host").dataset.overlayState==="closed"');frames(page);after=position(page);assert after['mode']=='stable'and after['anchor']==before['anchor']and abs(after['y']-before['y'])<=1,(before,after);return after
with sync_playwright()as p:
 browser=launch(p,args.engine)
 for w,h,textScale in [(390,844,1),(844,390,1),(320,568,2)]:
  kw={'viewport':{'width':w,'height':h},'device_scale_factor':2,'has_touch':True}
  if args.engine!='firefox':kw['is_mobile']=True
  context=browser.new_context(**kw);context.add_init_script(PROBE);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  ready(page,args.url+'/?tour=prototype&waterTime=2');frames_ready(page)
  if textScale==2:
   page.evaluate('document.documentElement.style.fontSize="200%"');page.wait_for_function('document.documentElement.classList.contains("tour-large-text")');page.wait_for_timeout(200)
  choose_flow(page)
  before=click_from_flow(page,'[data-film-station=B1] button');page.wait_for_selector('.film-dialog[data-state=ready]');close=visible_control(page,'.film-dialog-close');page.screenshot(path=str(OUT/f'{args.engine}-dialog-film-{w}-{h}-text{textScale}.png'))
  shell=page.locator('.film-dialog-shell');shell.evaluate('e=>e.scrollTop=e.scrollHeight');frames(page);visible_control(page,'.film-dialog-close');page.locator('.film-dialog-close').click();after=returned(page,before)
  beforeProject=click_from_flow(page,'[data-project-tab=live]');closeProject=visible_control(page,'.tour-project-close');live=page.locator('.tour-project-live-space').bounding_box();assert live and live['height']>=160,(w,h,live)
  assert page.locator('canvas').count()==1 and page.locator('canvas').is_visible()
  hidden=page.locator('.tour-reading-flow article').evaluate_all('es=>es.every(e=>getComputedStyle(e).visibility==="hidden"&&[...e.querySelectorAll("h2,[class$=-body]")].every(n=>getComputedStyle(n).visibility==="hidden"))');assert hidden,'background inscriptions paint through live scene'
  current=page.evaluate('scrollY');page.mouse.move(200,min(h-30,200))
  if args.engine=='webkit':page.keyboard.press('PageDown') # Mobile WebKit explicitly rejects the wheel API; native layout-wheel is tested in the chapter regression.
  else:page.mouse.wheel(0,80)
  page.wait_for_timeout(180);assert page.evaluate('scrollY')==current
  pinch=None
  if args.engine=='chromium'and w==390:
   session=context.new_cdp_session(page);prior=page.evaluate('visualViewport.scale')
   session.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':130,'y':400,'id':0},{'x':250,'y':400,'id':1}]})
   for left,right in [(120,260),(110,270),(100,280),(90,290),(80,300)]:
    session.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':left,'y':400,'id':0},{'x':right,'y':400,'id':1}]});page.wait_for_timeout(60)
   session.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});page.wait_for_timeout(300);scale=page.evaluate('visualViewport.scale');assert scale>prior+.1
   # Reset only the test's page-scale emulation after proving the native gesture.
   session.send('Emulation.setPageScaleFactor',{'pageScaleFactor':prior});page.wait_for_timeout(200)
   pinch={'before':prior,'after':scale,'reset':page.evaluate('visualViewport.scale'),'nativeCdpTwoPointTouch':True,'physicalFingers':False}
  page.screenshot(path=str(OUT/f'{args.engine}-dialog-live-{w}-{h}-text{textScale}.png'))
  page.locator('.tour-project-shell').evaluate('e=>e.scrollTop=100');frames(page);visible_control(page,'.tour-project-close')
  page.locator('[data-project-view=archive]').click();frames(page);page.locator('.tour-project-play').click();page.wait_for_function('document.querySelector("video")?.currentTime>.1&&!document.querySelector("video").paused');assert page.locator('video').count()==1
  video=page.locator('video').evaluate('v=>({duration:v.duration,width:v.videoWidth,height:v.videoHeight,controls:v.controls,inline:v.playsInline,loop:v.loop})');assert abs(video['duration']-12)<.1 and video['controls']and video['inline']and not video['loop']
  visible_control(page,'.tour-project-close');page.screenshot(path=str(OUT/f'{args.engine}-dialog-archive-{w}-{h}-text{textScale}.png'));page.locator('.tour-project-close').click();afterProject=returned(page,beforeProject);assert page.locator('video').count()==0
  # Reopening starts the archive at its beginning, including the short-shell scroller.
  beforeReopen=click_from_flow(page,'[data-project-tab=archive]');assert page.locator('.tour-project-shell').evaluate('e=>e.scrollTop')==0 and page.locator('.tour-project-archive').evaluate('e=>e.scrollTop')==0
  page.keyboard.press('Escape');returned(page,beforeReopen)
  rows.append({'viewport':[w,h],'textScale':textScale,'film':{'close':close,'before':before,'after':after},'project':{'close':closeProject,'liveBounds':live,'before':beforeProject,'after':afterProject,'underlyingTextHidden':hidden,'backgroundInput':'PageDown; mobile WebKit wheel API unsupported'if args.engine=='webkit'else'native wheel','video':video,'decoderReleased':True,'reopenAtStart':True},'pinch':pinch,'errors':errors});assert not errors;context.close();print(args.engine,w,h,textScale,'viewer PASS',flush=True)
 # A real WebGL creation failure must expose all three chapters, not only C.
 context=browser.new_context(viewport={'width':390,'height':844});context.add_init_script('''(()=>{const original=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(type,...rest){if(String(type).startsWith('webgl'))return null;return original.call(this,type,...rest)}})()''')
 page=context.new_page();page.goto(args.url+'/?tour=prototype&waterTime=2',wait_until='networkidle');page.wait_for_selector('#tour-host[data-render-state=error]');frames_ready(page);assert page.locator('main').get_attribute('data-reading-mode')=='stable';assert page.locator('canvas').count()==0
 text=page.locator('.tour-reading-flow').inner_text();assert all(t in text for t in ['张辰翰','枫叶互动','游族网络','网页设计样片','交互实验'])
 assert page.locator('.tour-reading-flow article').evaluate_all('es=>es.length===10&&es.every(e=>!e.hidden&&!e.inert&&e.getAttribute("aria-hidden")==="false")')
 assert page.locator('[data-project-tab=live]').is_disabled()and page.locator('[data-project-tab=archive]').is_enabled()
 page.locator('#tour-stop-about').click();frames(page);assert page.locator('main').get_attribute('data-flow-anchor')=='A1'
 before=click_from_flow(page,'[data-film-station=B1] button');page.wait_for_selector('.film-dialog[data-state=ready]');page.locator('.film-dialog-close').click();returned(page,before)
 before=click_from_flow(page,'[data-project-tab=archive]');assert page.locator('[data-project-view=live]').is_disabled();page.locator('.tour-project-close').click();returned(page,before)
 page.screenshot(path=str(OUT/f'{args.engine}-no-webgl-full-reading.png'));rows.append({'noWebGL':True,'tenStationsAccessible':True,'factsAndSourceLabelsPresent':True,'filmAndArchiveWork':True,'liveExplainedDisabled':True});browser.close()
save(f'dialogs-{args.engine}.json',{'passed':True,'engine':args.engine,'checks':rows,'physicalDevice':False});print(args.engine,'all difficult viewer and full fallback groups PASS',flush=True)
