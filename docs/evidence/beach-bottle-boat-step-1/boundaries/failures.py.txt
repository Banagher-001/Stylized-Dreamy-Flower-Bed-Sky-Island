"""Original WebGL failures, real visibility and reduced-motion behavior."""
import json,time
from common import Run,arguments
args=arguments();r=Run(args,'failures');c,p=r.new(1024,768)
def raw():return p.evaluate('''()=>({ready:window.__bottleOcean?.ready,error:window.__bottleError??null,frames:window.__baseline.frames,draws:window.__baseline.draws,loaderClass:document.querySelector('#loader').className,loaderDisplay:getComputedStyle(document.querySelector('#loader')).display,errorDisplay:getComputedStyle(document.querySelector('#loader-error')).display,errorText:document.querySelector('#loader-error').textContent,contextEvents:window.__baseline.context})''')
try:
 if args.no_webgl:
  def blocked():
   p.wait_for_function('!!window.__bottleError',timeout=30000);s=raw();r.picture('webgl-disabled-error');assert not s['ready']and s['error']and s['loaderDisplay']!='none'and s['errorDisplay']!='none';return {'injection':'Actual Chromium --disable-webgl launch flag','actual':s,'readyEvents':p.evaluate('__baseline.readyEvents'),'expectedConsoleErrors':True}
  r.check('FAILURE.webgl-disabled','真实禁用WebGL的原初始化失败界面',blocked)
 else:
  r.ready();r.quality('retro')
  def visibility():
   p.bring_to_front();p.wait_for_timeout(350);before=p.evaluate('({state:document.visibilityState,sim:__bottleOcean.getDiagnostics().simTime,events:__baseline.visibility})');blank=c.new_page();blank.goto('about:blank');blank.bring_to_front();p.wait_for_timeout(1200);hidden=p.evaluate('({state:document.visibilityState,sim:__bottleOcean.getDiagnostics().simTime,events:__baseline.visibility})');p.bring_to_front();p.wait_for_timeout(350);r.frames(4);after=p.evaluate('({state:document.visibilityState,sim:__bottleOcean.getDiagnostics().simTime,events:__baseline.visibility})');blank.close();return {'_status':'通过'if hidden['state']=='hidden'and after['state']=='visible'else'设备/浏览器限制','before':before,'background':hidden,'returned':after,'documentHiddenOverridden':False,'eventManuallyDispatched':False,'note':'Chromium headful automation may keep both pages visible; only actual state is evidence'}
  r.check('LIFECYCLE.visibility','实际标签切换与返回',visibility)
  def reduced():
   global c,p
   c,p=r.new(1024,768,reduced_motion='reduce');default=r.ready();r.quality('retro');assert p.evaluate('matchMedia("(prefers-reduced-motion: reduce)").matches');a=r.snapshot();r.frames(12);b=r.snapshot();assert b['diagnostics']['simTime']>a['diagnostics']['simTime']and b['draws']>a['draws'];return {'preferenceActuallyMatched':True,'default':default,'before':a,'after':b,'originalBehavior':'CSS animations/transitions shortened; 3D simulation and drawing continue'}
  r.check('LIFECYCLE.reduced-motion','实际减少动态偏好的原语义',reduced)
  def loss():
   before=r.snapshot();available=p.evaluate('!!__bottleOcean.renderer.getContext().getExtension("WEBGL_lose_context")');assert available;p.evaluate('__bottleOcean.renderer.getContext().getExtension("WEBGL_lose_context").loseContext()');p.wait_for_function('__baseline.context.some(e=>e.kind==="lost")',timeout=10000);p.wait_for_timeout(250);lost=raw();r.picture('context-lost');assert lost['contextEvents'];assert '丢失'in lost['errorText'];p.reload(wait_until='domcontentloaded');restored=r.ready();r.picture('reload-after-loss');assert restored['diagnostics']['ready']and restored['loader']['display']=='none';return {'_status':'原页已有问题','injection':'Actual WEBGL_lose_context.loseContext(); trusted WebGL canvas loss event','before':before,'lost':lost,'reloaded':restored,'note':'Original ready remains true; __bottleError is not set. showError removes hidden class but loader.style.display stays none after boot; error text exists without visible overlay. Refresh restores original.'}
  r.check('FAILURE.context-loss-reload','图形丢失、陈旧ready、错误可见性与刷新恢复',loss)
finally:r.finish()
