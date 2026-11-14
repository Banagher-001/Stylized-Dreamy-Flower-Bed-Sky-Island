"""Paired small-screen UI, genuine touchscreen gestures and preserved resize state."""
from harness import *
args=arguments();r=Run(args)
try:
 for key in['phone','landscape','narrow']:
  def view(s,key=key):
   entry=s.snapshot();resizeHistory=[]
   if key=='narrow':
    # Original applyResponsive() expands its panel; a later native resize folds it.
    # Match that real resize history instead of assuming entry event timing is equal.
    c=s.config;target=c['host']if s.side=='embedded'else c['child'];origin=s.evaluate('performance.timeOrigin')
    for width in[target[0]+1,target[0]]:
     s.page.set_viewport_size({'width':width,'height':target[1]});s.page.wait_for_timeout(450);resizeHistory.append(s.snapshot())
    assert s.evaluate('performance.timeOrigin')==origin and s.snapshot()['viewport']==c['child']
   initial=s.snapshot();collapsed=initial['ui']['collapsed'];s.locator('#panel-toggle').tap()if r.args.engine=='chromium'else s.locator('#panel-toggle').click();s.page.wait_for_timeout(350);first=s.snapshot();assert first['ui']['collapsed']is not collapsed;s.locator('#panel-toggle').tap()if r.args.engine=='chromium'else s.locator('#panel-toggle').click();s.page.wait_for_timeout(350);second=s.snapshot();assert second['ui']['collapsed']==collapsed;s.open_panel();s.quality('retro');s.locator('#glassOpacity').scroll_into_view_if_needed();s.slider('glassOpacity',.25);scroll=s.locator('.panel-scroll').evaluate('e=>({top:e.scrollTop,height:e.clientHeight,content:e.scrollHeight})');assert scroll['top']>0;s.picture('small-screen-'+key);gestures=None
   if key=='phone'and r.args.engine=='chromium':
    s.locator('#control-panel [data-action=toggleUI]').tap();s.page.wait_for_timeout(350);before=s.camera();o=s.offset();x=o['x']+130;y=o['y']+220;cdp=s.ctx.new_cdp_session(s.page);cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y,'id':1}]})
    for i in range(1,9):cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x+i*7,'y':y+i*3,'id':1}]});s.page.wait_for_timeout(35)
    cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});s.page.wait_for_timeout(500);orbit=s.camera();assert math.dist(before['position'],orbit['position'])>.02;cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x-35,'y':y,'id':1},{'x':x+35,'y':y,'id':2}]})
    for i in range(1,9):cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x-35-i*4,'y':y,'id':1},{'x':x+35+i*4,'y':y,'id':2}]});s.page.wait_for_timeout(35)
    cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});s.page.wait_for_timeout(500);pinch=s.camera();assert abs(orbit['distance']-pinch['distance'])>.02;gestures={'before':before,'afterOrbit':orbit,'afterPinch':pinch,'nativeCDPTouch':True};s.locator('#restore-ui').tap()
   if s.side=='embedded':assert not s.page.evaluate('document.documentElement.scrollWidth>innerWidth+1')and s.page.locator('.tour-project-close').is_visible()
   return {'entryBeforeMatchingResizeHistory':entry,'nativeResizeHistory':resizeHistory,'initial':initial,'firstToggle':first,'secondToggle':second,'scroll':scroll,'actualAfterInput':s.snapshot(),'gestures':gestures,'comparison':{'collapsedAtMatchedPrecondition':collapsed,'collapseToggledAndRestored':True,'glassOpacity':s.evaluate('__bottleOcean.bottle.glassMaterial.uniforms.uOpacity.value'),'touchOrbitPinchChecked':bool(gestures)}}
  r.pair('VIEW.'+key,[],view,config=key)
 def resize(s):
  s.reset();s.slider('waveHeight',100);old=s.evaluate('performance.timeOrigin');rows=[];config=read(OUT/'pair-conditions.json')
  for key in['landscape','phone','desktop']:
   c=config[key];target=c['host']if s.side=='embedded'else c['child'];s.page.set_viewport_size({'width':target[0],'height':target[1]});s.page.wait_for_timeout(650);s.tick();a=s.snapshot();assert a['viewport']==c['child']and a['diagnostics']['state']['waveHeight']==100 and s.evaluate('performance.timeOrigin')==old;rows.append(a)
  return {'sameOriginalDocument':True,'actualResizes':rows,'comparison':{'childViewports':[x['viewport']for x in rows],'userWaveHeight':[x['diagnostics']['state']['waveHeight']for x in rows]}}
 r.pair('VIEW.resize',[],resize)
finally:r.finish()
