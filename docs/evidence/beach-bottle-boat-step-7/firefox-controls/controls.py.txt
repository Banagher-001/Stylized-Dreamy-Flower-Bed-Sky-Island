"""Paired original/embedded native controls and actual scene/material effects."""
from harness import *
args=arguments();r=Run(args)
RANGES=[('waveHeight',3,0,50,100),('waveSpeed',4,.2,1.6,3),('waveDensity',5,.5,1.75,3),('waveDirection',6,0,180,360),('waterLevel',7,0,50,100),('boatResponse',8,0,50,100),('boatDamping',9,0,50,100),('wind',10,0,50,100),('pixelScale',14,1,3,5),('sunset',15,0,50,100),('brightness',16,.6,1.1,1.6),('glassOpacity',17,.04,.22,.4)]
def bound(s,name):
 a=s['actual'];p=s['post'];v=s['diagnostics']['state'][name]
 if name=='waveHeight':return {'state':v,'amplitude':a['amplitude']}
 if name=='waveSpeed':return {'state':v,'omega':a['waves'][0]['omega']}
 if name=='waveDensity':return {'state':v,'waveNumber':a['waves'][0]['k']}
 if name=='waveDirection':return {'state':v,'dx':a['waves'][0]['dx'],'dz':a['waves'][0]['dz']}
 if name=='waterLevel':return {'state':v,'baseLevel':a['baseLevel']}
 if name=='wind':return {'state':v,'actualWind':a['wind']}
 if name=='pixelScale':return {'state':v,'scale':p['scale'],'pixels':[p['pixelWidth'],p['pixelHeight']]}
 if name=='sunset':return {'state':v,'sunColor':a['sunColor'],'sunIntensity':a['sunIntensity']}
 if name=='brightness':return {'state':v,'exposure':p['exposure']}
 if name=='glassOpacity':return {'state':v,'opacity':a['glassOpacity']}
 return {'state':v}
try:
 def inventory(s):
  data=s.snapshot();rows=s.locator('button,input').evaluate_all('es=>es.map(e=>({tag:e.tagName,id:e.id,data:{...e.dataset},type:e.type,value:e.value??null}))');assert len(rows)==34 and sum(x['tag']=='BUTTON'for x in rows)==22 and len(data['ui']['sliders'])==12;assert data['diagnostics']['state']==DEFAULTS
  mismatch=[x for x in data['ui']['sliders']if abs(float(x['value'])-data['diagnostics']['state'][x['id']])>1e-6];assert [x['id']for x in mismatch]==['brightness'];s.picture('default-original-scene');return {'default':data,'controls':rows,'originalDefaultPrecisionIssue':mismatch,'comparison':{'state':data['diagnostics']['state'],'controls':rows,'post':data['post']}}
 r.pair('BASE.inventory',[],inventory)
 for name,ctl,lo,mid,hi in RANGES:
  def slider(s,name=name,lo=lo,mid=mid,hi=hi):
   s.reset();rows=[]
   for value in[lo,mid,hi]:
    event=s.slider(name,value);actual=s.snapshot();rows.append({'value':value,'input':event,'actual':actual,'binding':bound(actual,name)});write(r.folder/(name+'-'+s.side+'-partial.json'),rows)
   loc=s.locator('#'+name);loc.press('ArrowLeft');s.tick();step=float(loc.get_attribute('step'));assert abs(float(loc.input_value())-(hi-step))<1e-6
   b=[row['binding']for row in rows]
   if name=='waveHeight':assert b[0]['amplitude']<b[-1]['amplitude']
   if name=='waveSpeed':assert b[0]['omega']<b[-1]['omega']
   if name=='waveDensity':assert b[0]['waveNumber']<b[-1]['waveNumber']
   if name=='waveDirection':assert b[0]['dx']!=b[1]['dx']
   if name=='waterLevel':assert b[0]['baseLevel']<b[-1]['baseLevel']
   if name=='wind':assert b[0]['actualWind']<b[-1]['actualWind']
   if name=='pixelScale':assert b[0]['pixels'][0]>b[-1]['pixels'][0]
   if name=='sunset':assert b[0]['sunColor']!=b[-1]['sunColor']
   if name=='brightness':assert b[0]['exposure']<b[-1]['exposure']
   if name=='glassOpacity':assert b[0]['opacity']<b[-1]['opacity']
   s.reset();return {'samples':rows,'nativeStep':step,'restored':s.snapshot(),'continuousEvidence':'DYN.'+name if name in['boatResponse','boatDamping']else None,'comparison':{'bindings':b,'step':step}}
  r.pair('SLIDER.'+name,[ctl],slider)
 def qualities(s):
  s.reset();rows=[]
  for name,scale,levels in[('fine',2,48),('standard',2.85,26),('retro',3.8,12)]:
   s.quality(name);a=s.snapshot();assert a['post']['scale']==scale and a['post']['levels']==levels;rows.append(a);s.picture('quality-'+name)
  return {'states':rows,'comparison':[{'scale':x['post']['scale'],'levels':x['post']['levels'],'pixels':[x['post']['pixelWidth'],x['post']['pixelHeight']],'range':next(v for v in x['ui']['sliders']if v['id']=='pixelScale')}for x in rows]}
 r.pair('BUTTON.qualities',[11,12,13],qualities)
 for name,ctl in[('lighthouse',18),('spray',19),('dust',20)]:
  def toggle(s,name=name):
   s.reset();rows=[]
   for _ in range(2):
    before=s.snapshot();s.locator('[data-toggle='+name+']').click();s.tick();after=s.snapshot();assert after['actual'][name]is not before['actual'][name]and after['diagnostics']['state'][name]==after['actual'][name];rows.append({'before':before['actual'][name],'after':after['actual'][name]})
   return {'actualObjectToggle':rows,'events':s.evaluate('__parityProbe.clicks.slice(-2)'),'comparison':rows}
  r.pair('BUTTON.toggle-'+name,[ctl],toggle)
 def interface(s):
  s.reset();before=s.locator('#control-panel').bounding_box();s.locator('#panel-toggle').click();s.page.wait_for_timeout(400);assert s.evaluate('document.querySelector("#control-panel").classList.contains("collapsed")');collapsed=s.locator('#control-panel').bounding_box();s.locator('#panel-toggle').click();s.page.wait_for_timeout(400);assert not s.evaluate('document.querySelector("#control-panel").classList.contains("collapsed")');s.locator('#control-panel [data-action=toggleUI]').click();assert s.evaluate('document.body.classList.contains("ui-hidden")');s.page.wait_for_timeout(350);s.picture('ui-hidden');s.locator('#restore-ui').click();assert not s.evaluate('document.body.classList.contains("ui-hidden")');s.tick();return {'panelBefore':before,'panelCollapsed':collapsed,'events':s.evaluate('__parityProbe.clicks.slice(-4)'),'restored':s.snapshot(),'comparison':{'collapsedThenExpanded':True,'hiddenThenRestored':True}}
 r.pair('BUTTON.interface',[1,2,34],interface)
finally:r.finish()
