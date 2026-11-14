"""Record original defaults, native controls and their real scene effects."""
import json,time
from common import Run,arguments,SNAP
args=arguments();r=Run(args,'controls');p=None
def load():
 global p
 started=time.monotonic();c,p=r.new(1920,1080);s=r.ready(p);r.picture('default-1920x1080');gl=p.evaluate('''()=>{const gl=__bottleOcean.renderer.getContext(),e=gl.getExtension('WEBGL_debug_renderer_info');return {version:gl.getParameter(gl.VERSION),renderer:e?gl.getParameter(e.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER)}}''')
 return {'wallSeconds':time.monotonic()-started,'default':s,'actualGL':gl,'readyEvents':p.evaluate('__baseline.readyEvents')}
try:
 r.check('LOAD.http-cold','HTTP新上下文完整原页',load)
 def inventory():
  rows=p.locator('button,input').evaluate_all('''es=>es.map(e=>({tag:e.tagName,id:e.id,type:e.type,value:e.value??null,data:{...e.dataset},text:e.textContent.trim(),title:e.title,rect:e.getBoundingClientRect().toJSON()}))''')
  assert len(rows)==34 and sum(x['tag']=='BUTTON'for x in rows)==22
  s=r.snapshot();mismatches=[{'id':v['id'],'input':float(v['value']),'state':s['diagnostics']['state'][v['id']],'output':v['output']}for v in s['ui']['sliders']if abs(float(v['value'])-s['diagnostics']['state'][v['id']])>1e-6]
  scene=p.evaluate('''()=>{const b=__bottleOcean,e=b.environment,c={meshes:0,points:0,lights:0};b.scene.traverse(o=>{if(o.isMesh)c.meshes++;if(o.isPoints)c.points++;if(o.isLight)c.lights++});return {objects:c,masts:b.boat.masts.length,terrainVertices:e.terrain.geometry.attributes.position.count,ocean:!!e.ocean,lighthouse:!!e.lighthouse,sky:!!e.skyMesh,glass:!!b.bottle.glassMesh}}''')
  assert scene['masts']==3 and scene['terrainVertices']>1000 and scene['objects']['meshes']>20
  return {'_status':'原页已有问题'if mismatches else'通过','controls':rows,'actualDefault':s,'defaultInputStateMismatches':mismatches,'completeScene':scene,'note':'Input/state discrepancy observed in original; no host present and no correction applied'}
 r.check('UI.default-inventory','34控件、完整场景、声明值和浏览器实际值',inventory)
 def again():
  p.reload(wait_until='domcontentloaded');s=r.ready();assert s['diagnostics']['state']['waveHeight']==35
  return {'freshDocumentDefaults':s,'requestsObserved':True,'cacheNotClaimedBecauseOriginalServerNoStore':True}
 r.check('LOAD.http-again','再次加载回到原默认状态',again)
 def view1440():
  p.set_viewport_size({'width':1440,'height':900});r.frames(3);s=r.snapshot();assert s['canvas']['width']==1440 and s['canvas']['height']==900;r.picture('default-1440x900');return s
 r.check('VIEW.default-1440','第二桌面尺寸原默认画面',view1440)
 p.set_viewport_size({'width':1024,'height':768});r.frames(3);r.quality('retro');r.report['functionalSetup']={'viewport':[1024,768],'qualitySelectedThroughNativeButton':'retro','defaultBeforeQualitySelectionCaptured':True};r.save()
 ranges=[('waveHeight',0,50,100),('waveSpeed',.2,1.6,3),('waveDensity',.5,1.75,3),('waveDirection',0,180,360),('waterLevel',0,50,100),('boatResponse',0,50,100),('boatDamping',0,50,100),('wind',0,50,100),('pixelScale',1,3,5),('sunset',0,50,100),('brightness',.6,1.1,1.6),('glassOpacity',.04,.22,.4)]
 for name,low,middle,high in ranges:
  def slider(name=name,low=low,middle=middle,high=high):
   r.reset();rows=[]
   for value in [low,middle,high]:
    event=r.slider(name,value);s=r.snapshot();rows.append({'value':value,'input':event,'actual':s})
   loc=p.locator('#'+name);loc.press('ArrowLeft');r.frames();step=float(loc.get_attribute('step'));assert abs(float(loc.input_value())-(high-step))<1e-6
   actual=[x['actual']['actual']for x in rows]
   if name=='waveHeight':assert actual[0]['amplitude']<actual[-1]['amplitude']
   if name=='waveSpeed':assert actual[0]['waves'][0]['omega']<actual[-1]['waves'][0]['omega']
   if name=='waveDensity':assert actual[0]['waves'][0]['k']<actual[-1]['waves'][0]['k']
   if name=='waveDirection':assert actual[0]['waves'][0]['dx']!=actual[1]['waves'][0]['dx']
   if name=='waterLevel':assert actual[0]['baseLevel']<actual[-1]['baseLevel']
   if name=='pixelScale':assert rows[0]['actual']['post']['pixelWidth']>rows[-1]['actual']['post']['pixelWidth']
   if name=='sunset':assert actual[0]['sunColor']!=actual[-1]['sunColor']
   if name=='brightness':assert rows[0]['actual']['post']['exposure']<rows[-1]['actual']['post']['exposure']
   if name=='glassOpacity':assert actual[0]['glassOpacity']<actual[-1]['glassOpacity']
   if name=='wind':assert actual[0]['wind']<actual[-1]['wind']
   r.reset();return {'parameter':name,'samples':rows,'nativeArrowStep':step,'restored':r.snapshot(),'responseAndDampingContinuousEffectRecordedSeparately':name in['boatResponse','boatDamping']}
  r.check('SLIDER.'+name,name+'低中高、真实步进与恢复',slider)
 def qualities():
  r.reset();rows=[]
  for name,scale,levels in [('fine',2,48),('standard',2.85,26),('retro',3.8,12)]:
   r.quality(name);s=r.snapshot();assert s['post']['scale']==scale and s['post']['levels']==levels;rows.append(s)
  return {'nativeQualityButtons':rows,'inputRoundingRecordedNotChanged':True}
 r.check('BUTTON.quality','三档画质的实际分辨率与色阶',qualities)
 for name in ['lighthouse','spray','dust']:
  def toggle(name=name):
   r.reset();rows=[]
   for _ in range(2):
    before=r.snapshot();p.locator('[data-toggle='+name+']').click();r.frames();after=r.snapshot();assert after['actual'][name]is not before['actual'][name];assert after['diagnostics']['state'][name]==after['actual'][name];rows.append({'before':before['actual'][name],'after':after['actual'][name]})
   return {'nativeToggle':name,'actualOriginalObjectState':rows}
  r.check('BUTTON.toggle-'+name,name+'原对象关闭与恢复',toggle)
 def panel():
  r.reset();before=p.locator('#control-panel').bounding_box();p.locator('#panel-toggle').click();assert p.locator('#control-panel').evaluate('e=>e.classList.contains("collapsed")');p.wait_for_timeout(400);collapsed=p.locator('#control-panel').bounding_box();p.locator('#panel-toggle').click();p.wait_for_timeout(400);assert not p.locator('#control-panel').evaluate('e=>e.classList.contains("collapsed")');return {'before':before,'collapsed':collapsed,'restored':p.locator('#control-panel').bounding_box()}
 r.check('BUTTON.panel','控制台折叠与恢复',panel)
 def hidden():
  p.locator('#control-panel [data-action=toggleUI]').click();assert p.evaluate('document.body.classList.contains("ui-hidden")');p.wait_for_timeout(500);r.picture('ui-hidden');p.locator('#restore-ui').click();assert not p.evaluate('document.body.classList.contains("ui-hidden")');return {'nativeHideAndRestoreButtons':True,'originalEvents':p.evaluate('__baseline.clicks.slice(-2)')}
 r.check('BUTTON.ui-hide-restore','原按钮隐藏并恢复UI',hidden)
finally:r.finish()
