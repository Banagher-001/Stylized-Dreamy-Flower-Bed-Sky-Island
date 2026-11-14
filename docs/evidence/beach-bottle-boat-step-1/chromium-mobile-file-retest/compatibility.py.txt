"""Independent engine, viewport and genuine Chromium touch protocol observations."""
import json,math,struct,time
from common import Run,arguments
args=arguments();r=Run(args,'compatibility');c,p=r.new(1280,720)
def camera():return p.evaluate('__bottleOcean.cameraRig.getState()')
def export(label):
 before=r.snapshot()
 with p.expect_download(timeout=30000)as wait:p.locator('[data-action=screenshot]').click()
 d=wait.value;path=r.folder/(label+'.png');d.save_as(str(path));raw=path.read_bytes();assert raw[:8]==b'\x89PNG\r\n\x1a\n';size=list(struct.unpack('>II',raw[16:24]));expected=[round(before['canvas'][a]*min(before['dpr'],2))for a in['width','height']];assert size==expected;return {'filename':d.suggested_filename,'size':size,'bytes':len(raw),'before':before}
try:
 def key_path():
  started=time.monotonic();default=r.ready();r.picture('original-default-1280x720');r.quality('retro');r.slider('waveHeight',60);p.locator('[data-preset=top]').click();p.wait_for_timeout(1450);r.frames(4);assert camera()['preset']=='top';p.locator('#panel-toggle').click();assert p.locator('#control-panel').evaluate('e=>e.classList.contains("collapsed")');p.locator('#panel-toggle').click()
  p.locator('#control-panel [data-action=toggleUI]').click();assert p.evaluate('document.body.classList.contains("ui-hidden")');p.locator('#restore-ui').click();assert not p.evaluate('document.body.classList.contains("ui-hidden")')
  p.locator('#glassOpacity').scroll_into_view_if_needed();r.slider('glassOpacity',.25);scroll=p.locator('.panel-scroll').evaluate('e=>({top:e.scrollTop,height:e.clientHeight,content:e.scrollHeight})');r.picture('native-controls-1280x720');shot=export('native-download-1280x720');assert scroll['top']>0;gl=p.evaluate('''()=>{const gl=__bottleOcean.renderer.getContext(),e=gl.getExtension('WEBGL_debug_renderer_info');return {version:gl.getParameter(gl.VERSION),renderer:e?gl.getParameter(e.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER)}}''');return {'default':default,'afterNativeActions':r.snapshot(),'panelScroll':scroll,'export':shot,'actualGL':gl,'wallSeconds':time.monotonic()-started,'coverage':'Representative load, slider, camera, collapse, hide/restore and download; not full 34 controls on this engine'}
 r.check('ENGINE.representative',args.engine+'独立加载及关键操作',key_path)
 def file_load():
  global c,p
  from common import SOURCE
  from playwright.sync_api import Error
  try:c,p=r.new(1280,720,url=(SOURCE/'index.html').as_uri())
  except Error as ex:
   if 'ERR_BLOCKED_BY_ADMINISTRATOR'in str(ex):return {'_status':'设备/浏览器限制','entry':(SOURCE/'index.html').as_uri(),'actualNavigationError':str(ex),'note':'Managed Chromium blocks file URLs; policy not bypassed; not an original page defect'}
   raise
  s=r.ready();r.picture('file-direct-default');assert s['diagnostics']['renderer']['triangles']>1000;return {'entry':p.url,'snapshot':s,'actualRequests':r.report['requests'],'externalBlockedAttempts':r.report['externalAttempts']}
 r.check('LOAD.file-cold','file直开原单文件成品',file_load)
 if args.engine=='chromium':
  def phone():
   global c,p
   c,p=r.new(390,844,3,is_mobile=True,has_touch=True);default=r.ready();r.picture('phone-default-390x844');initialCollapsed=default['ui']['collapsed'];p.locator('#panel-toggle').tap();p.wait_for_timeout(450);first=r.snapshot();p.locator('#panel-toggle').tap();p.wait_for_timeout(450);second=r.snapshot();assert first['ui']['collapsed']is not initialCollapsed and second['ui']['collapsed']==initialCollapsed
   if second['ui']['collapsed']:p.locator('#panel-toggle').tap();p.wait_for_timeout(450)
   r.quality('retro')
   p.locator('#glassOpacity').scroll_into_view_if_needed();p.locator('#glassOpacity').press('End');r.frames();assert p.evaluate('__bottleOcean.state.glassOpacity')==.4
   p.locator('#control-panel [data-action=toggleUI]').tap();assert p.evaluate('document.body.classList.contains("ui-hidden")');p.wait_for_timeout(500)
   p.evaluate('''()=>{__baseline.touchEvents=[];for(const type of['touchstart','touchmove','touchend','pointerdown','pointerup'])document.querySelector('#gl').addEventListener(type,e=>__baseline.touchEvents.push({type:e.type,trusted:e.isTrusted,pointerType:e.pointerType||null,touches:e.touches?.length??null}),{passive:true})}''')
   session=c.new_cdp_session(p);before=camera();session.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':100,'y':270,'id':1}]})
   for i in range(1,9):session.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':100+i*10,'y':270+i*4,'id':1}]});p.wait_for_timeout(35)
   session.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});r.frames(10);rotated=camera();assert math.dist(before['position'],rotated['position'])>.02
   session.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':145,'y':320,'id':1},{'x':245,'y':320,'id':2}]})
   for i in range(1,9):session.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':145-i*5,'y':320,'id':1},{'x':245+i*5,'y':320,'id':2}]});p.wait_for_timeout(35)
   session.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});r.frames(10);zoomed=camera();assert abs(zoomed['distance']-rotated['distance'])>.05
   p.locator('#restore-ui').tap();r.picture('phone-after-touch-390x844');events=p.evaluate('__baseline.touchEvents');assert any(x['type']=='touchmove'and x['trusted']for x in events)
   portrait=r.snapshot();p.set_viewport_size({'width':844,'height':390});r.frames(4);landscape=r.snapshot();r.picture('phone-landscape-844x390');assert [landscape['canvas']['width'],landscape['canvas']['height']]==[844,390]
   p.locator('#panel-toggle').tap();collapsed=r.snapshot();p.locator('#panel-toggle').tap();restored=r.snapshot();assert collapsed['ui']['collapsed']is not restored['ui']['collapsed'];overflow=p.evaluate('({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,height:innerHeight,scrollHeight:document.documentElement.scrollHeight})')
   return {'portraitDefault':default,'defaultAutoFoldObserved':initialCollapsed,'nativeTapsAndPanelStates':[first['ui'],second['ui']],'touchCamera':[before,rotated,zoomed],'trustedTouchEvents':events,'portraitAfter':portrait,'landscape':landscape,'layout':overflow,'identity':'Linux Chromium mobile/touch emulation; not physical phone or Safari/iOS','note':'Actual default collapse recorded; no assumption based solely on applyResponsive code ordering'}
  r.check('VIEW.mobile-touch','手机横竖屏、原生触摸点按旋转和双指缩放',phone)
finally:r.finish()
