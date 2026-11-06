"""Actual X11 browser accelerators: Chromium page zoom and Firefox text-only zoom."""
import ctypes,time,argparse,tempfile
parser=argparse.ArgumentParser();parser.add_argument("--engine",choices=["both","chromium","firefox"],default="both");args=parser.parse_args()
from playwright.sync_api import sync_playwright
from step11_common import *
x=ctypes.CDLL('libX11.so.6');xt=ctypes.CDLL('libXtst.so.6');D=ctypes.c_void_p;W=ctypes.c_ulong
x.XOpenDisplay.argtypes=[ctypes.c_char_p];x.XOpenDisplay.restype=D
x.XDefaultRootWindow.argtypes=[D];x.XDefaultRootWindow.restype=W
x.XQueryTree.argtypes=[D,W,ctypes.POINTER(W),ctypes.POINTER(W),ctypes.POINTER(ctypes.POINTER(W)),ctypes.POINTER(ctypes.c_uint)]
x.XFetchName.argtypes=[D,W,ctypes.POINTER(ctypes.c_void_p)];x.XFree.argtypes=[ctypes.c_void_p]
x.XInternAtom.argtypes=[D,ctypes.c_char_p,ctypes.c_int];x.XInternAtom.restype=W
x.XGetWindowProperty.argtypes=[D,W,W,ctypes.c_long,ctypes.c_long,ctypes.c_int,W,ctypes.POINTER(W),ctypes.POINTER(ctypes.c_int),ctypes.POINTER(W),ctypes.POINTER(W),ctypes.POINTER(ctypes.c_void_p)]
x.XSetInputFocus.argtypes=[D,W,ctypes.c_int,W];x.XRaiseWindow.argtypes=[D,W];x.XFlush.argtypes=[D]
x.XKeysymToKeycode.argtypes=[D,W];x.XKeysymToKeycode.restype=ctypes.c_uint
xt.XTestFakeKeyEvent.argtypes=[D,ctypes.c_uint,ctypes.c_int,W]
xt.XTestFakeMotionEvent.argtypes=[D,ctypes.c_int,ctypes.c_int,ctypes.c_int,W]
xt.XTestFakeButtonEvent.argtypes=[D,ctypes.c_uint,ctypes.c_int,W]
x.XTranslateCoordinates.argtypes=[D,W,W,ctypes.c_int,ctypes.c_int,ctypes.POINTER(ctypes.c_int),ctypes.POINTER(ctypes.c_int),ctypes.POINTER(W)]
display=x.XOpenDisplay(os.environ.get('DISPLAY',':99').encode());assert display
root=x.XDefaultRootWindow(display)
def find_named(title,window=root,depth=0):
 name=ctypes.c_void_p()
 if x.XFetchName(display,window,ctypes.byref(name))and name.value:
  text=ctypes.string_at(name).decode(errors='replace');x.XFree(name)
  if title in text:return window
 atom=x.XInternAtom(display,b'_NET_WM_NAME',0);kind=W();fmt=ctypes.c_int();countProp=W();remaining=W();value=ctypes.c_void_p()
 if x.XGetWindowProperty(display,window,atom,0,1024,0,0,ctypes.byref(kind),ctypes.byref(fmt),ctypes.byref(countProp),ctypes.byref(remaining),ctypes.byref(value))==0 and value.value:
  text=ctypes.string_at(value,countProp.value*max(1,fmt.value//8)).decode(errors='replace');x.XFree(value)
  if title in text:return window
 if depth>6:return None
 r=W();parent=W();children=ctypes.POINTER(W)();count=ctypes.c_uint()
 if x.XQueryTree(display,window,ctypes.byref(r),ctypes.byref(parent),ctypes.byref(children),ctypes.byref(count)):
  entries=[children[i]for i in range(count.value)]
  if children:x.XFree(children)
  for child in entries:
   result=find_named(title,child,depth+1)
   if result:return result
 return None
def accelerator(window,key,shift=False):
 x.XRaiseWindow(display,window);x.XSetInputFocus(display,window,2,0);x.XFlush(display)
 control=x.XKeysymToKeycode(display,0xffe3);code=x.XKeysymToKeycode(display,ord(key))
 shiftCode=x.XKeysymToKeycode(display,0xffe1)
 events=[(control,1)]+([(shiftCode,1)]if shift else[])+[(code,1),(code,0)]+([(shiftCode,0)]if shift else[])+[(control,0)]
 for k,on in events:
  xt.XTestFakeKeyEvent(display,k,on,0);x.XFlush(display);time.sleep(.04)
 x.XFlush(display)
def state(page):return page.evaluate('''()=>({inner:[innerWidth,innerHeight],dpr:devicePixelRatio,probe:document.querySelector('.tour-font-probe').getBoundingClientRect().height,bodyFont:getComputedStyle(document.querySelector('.pillar-reading-body')).fontSize,readingMode:document.querySelector('main').dataset.readingMode,overflow:document.documentElement.scrollWidth-innerWidth,capacity:JSON.parse(document.querySelector('main').dataset.readingCapacity||'null'),viewportMeta:document.querySelector('meta[name=viewport]').content})''')
results=[]
with sync_playwright()as p:
 for engine in (['chromium','firefox']if args.engine=='both'else[args.engine]):
  if engine=='chromium':browser=p.chromium.launch(headless=False,executable_path='/usr/bin/chromium',args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--window-size=1440,1000'])
  else:
   nativeProfile=tempfile.TemporaryDirectory(prefix='step11-native-firefox-')
   persistent=p.firefox.launch_persistent_context(nativeProfile.name,headless=False,no_viewport=True,args=['--width=1440','--height=1000'],firefox_user_prefs={'webgl.force-enabled':True,'browser.zoom.full':False,'browser.zoom.siteSpecific':False})
   browser=persistent.browser
  context=browser.new_context(no_viewport=True)if engine=='chromium'else persistent
  page=context.new_page()if engine=='chromium'else(context.pages[0]if context.pages else context.new_page());ready(page,'http://127.0.0.1:4173/?tour=prototype&waterTime=2');page.bring_to_front();page.wait_for_function('document.querySelector("main").dataset.layoutReady==="true"');frames(page)
  name='STEP11 NATIVE '+engine;page.evaluate('(t)=>document.title=t',name);page.wait_for_timeout(400);window=find_named(name);assert window,('No native window',engine)
  ax=ctypes.c_int();ay=ctypes.c_int();child=W();x.XTranslateCoordinates(display,window,root,300,400,ctypes.byref(ax),ctypes.byref(ay),ctypes.byref(child))
  xt.XTestFakeMotionEvent(display,0,ax.value,ay.value,0);xt.XTestFakeButtonEvent(display,1,1,0);xt.XTestFakeButtonEvent(display,1,0,0);x.XFlush(display);page.wait_for_timeout(200)
  page.evaluate('window.__nativeKeys=[];addEventListener("keydown",e=>window.__nativeKeys.push({key:e.key,ctrl:e.ctrlKey,shift:e.shiftKey}))')
  before=state(page);trace=[]
  for i in range(12):
   accelerator(window,'=',shift=engine=='firefox');page.wait_for_timeout(350);frames(page);s=state(page);ratio=s['dpr']/before['dpr']if engine=='chromium'else s['probe']/before['probe'];trace.append({'press':i+1,'ratio':ratio,'state':s})
   if ratio>=1.99:break
  save('native-zoom-trace-'+engine+'.json',{'before':before,'trace':trace,'actualZoomRatio':ratio,'keyEvents':page.evaluate('window.__nativeKeys')})
  assert abs(ratio-2)<.02,(engine,[(r['press'],r['ratio'])for r in trace])
  assert s['readingMode']=='stable'and s['overflow']<=1,(engine,s)
  save('native-zoom-trace-'+engine+'.json',{'before':before,'trace':trace,'actualZoomRatio':ratio,'keyEvents':page.evaluate('window.__nativeKeys')})
  for key in ['A1','A2','A3','B1','B2','B3','B4','C1','C2','C3']:
   article=page.locator(f'.tour-reading-flow [data-flow-anchor={key}]');article.evaluate('e=>e.scrollIntoView({block:"center",behavior:"instant"})');frames(page)
   assert article.is_visible()and article.get_attribute('aria-hidden')=='false'and article.evaluate('e=>!e.inert&&e.scrollWidth<=e.clientWidth+1&&e.scrollHeight<=e.clientHeight+1')
  page.locator('#tour-stop-films').click();frames(page);page.screenshot(path=str(OUT/f'native-{engine}-200percent.png'))
  page.locator('[data-film-station=B1] button').click();page.wait_for_selector('.film-dialog[data-state=ready]');frames(page);r=page.locator('.film-dialog-close').bounding_box();assert r['y']>=0 and r['y']+r['height']<=s['inner'][1]+1
  page.locator('.film-dialog-close').click();frames(page)
  page.locator('#tour-stop-experiments').click();page.locator('[data-project-tab=archive]').click();frames(page);page.screenshot(path=str(OUT/f'native-{engine}-200percent-archive.png'));page.locator('.tour-project-close').click();frames(page)
  accelerator(window,'0');page.wait_for_timeout(400);frames(page);after=state(page);assert abs(after['dpr']-before['dpr'])<.01 and abs(after['probe']-before['probe'])<.1 and after['readingMode']=='stable'
  results.append({'engine':engine,'version':browser.version,'kind':'native browser page zoom'if engine=='chromium'else'native Firefox text-only zoom (browser.zoom.full=false)','actualX11Accelerators':True,'before':before,'trace':trace,'zoom200Verified':True,'tenStationsAndBothDialogsReadable':True,'afterReset':after,'physicalDevice':False});save('native-zoom-'+engine+'.json',{'passed':True,'result':results[-1]});print(engine,'native200% PASS',flush=True);browser.close()
  if engine=='firefox':nativeProfile.cleanup()
save('native-zoom.json',{'passed':True,'results':[json.loads((OUT/('native-zoom-'+e+'.json')).read_text())['result']for e in ['chromium','firefox']if(OUT/('native-zoom-'+e+'.json')).exists()],'notCssTransformOrRemSimulation':True,'environment':'Native browser UI on Linux Xvfb, not real phone OS text sizing'})
