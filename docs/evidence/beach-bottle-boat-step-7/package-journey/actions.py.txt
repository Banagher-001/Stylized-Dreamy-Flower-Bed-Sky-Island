"""Paired native camera, sandbox, playback, picking, keys and original downloads."""
from harness import *
args=arguments();r=Run(args)
try:
 def presets(s):
  s.reset();s.locator('[data-preset=top]').click();s.settle();s.surface.wait_for_function('Math.abs(__bottleOcean.cameraRig.getState().fov-44)<.01',timeout=60000,polling=100);rows=[]
  for name in['cinema','side','top','closeup','panorama']:
   before=s.camera();s.locator('[data-preset='+name+']').click();s.settle();expected={'cinema':42,'side':39,'top':44,'closeup':36,'panorama':47}[name];s.surface.wait_for_function('v=>Math.abs(__bottleOcean.cameraRig.getState().fov-v)<.01',arg=expected,timeout=60000,polling=100);after=s.camera();assert after['preset']==name and abs(after['fov']-expected)<.01;assert math.dist(before['position'],after['position'])>.01;rows.append({'name':name,'before':before,'after':after});s.picture('camera-'+name)
  return {'presets':rows,'comparison':[{'name':x['name'],'fov':x['after']['fov'],'preset':x['after']['preset']}for x in rows],'actualCameraCoordinatesRecorded':True,'phaseIdenticalClaimed':False}
 r.pair('CAMERA.presets',[21,22,23,24,25],presets)
 def pointer_reset(s):
  s.reset();s.settle();rows=[]
  for action in['rotate','pan','zoom']:
   before=s.camera()
   if action=='zoom':o=s.offset();s.page.mouse.move(o['x']+270,o['y']+230);s.page.mouse.wheel(0,350)
   else:s.drag(270,230,140,55,'right'if action=='pan'else'left')
   s.frames(16);after=s.camera();assert math.dist(before['position'],after['position'])>.005
   if action=='pan':assert math.dist(before['target'],after['target'])>.005
   if action=='zoom':assert abs(before['distance']-after['distance'])>.05
   rows.append({'action':action,'before':before,'after':after})
  s.locator('[data-action=resetCamera]').click();s.settle();early=s.camera();s.frames(80);late=s.camera();assert late['preset']=='cinema'and abs(late['fov']-42)<.01;error=math.dist(late['position'],[.55,2.15,6.5]);s.picture('camera-restored-after-inertia');return {'nativeInputs':rows,'afterTween':early,'after80RenderedFrames':late,'declaredCinemaPositionError':error,'knownOriginalIssue':'O-03: residual inertia/ground constraints; actual poses retained, no direct camera reset','comparison':{'actions':[x['action']for x in rows],'preset':late['preset'],'fov':late['fov']}}
 r.pair('CAMERA.pointer-reset',[32],pointer_reset)
 def picking(s):
  rows=[]
  for kind in['bottle','ground','lighthouse']:
   s.reset();s.settle()
   if kind=='lighthouse':s.locator('#control-panel [data-action=toggleUI]').click();s.page.wait_for_timeout(400)
   pt=s.pick(kind);assert pt,kind+' has no unobscured actual raycast candidate';before=s.camera();light=s.evaluate('__bottleOcean.state.lighthouse')
   if kind=='lighthouse':s.click(pt['x'],pt['y']);s.tick();assert s.evaluate('__bottleOcean.state.lighthouse')is not light
   else:s.click(pt['x'],pt['y'],double=True);s.settle();assert math.dist(before['target'],s.camera()['target'])>.05
   rows.append({'kind':kind,'actualRay':pt,'before':before,'after':s.camera(),'lightBefore':light,'lightAfter':s.evaluate('__bottleOcean.state.lighthouse')})
  point=s.pick('lighthouse');assert point;before=s.camera();s.click(point['x'],point['y'],double=True);s.settle();after=s.camera();rows.append({'kind':'lighthouse-double','actualRay':point,'before':before,'after':after,'lightAfter':s.evaluate('__bottleOcean.state.lighthouse')});return {'nativePicking':rows,'comparison':{'kinds':[x['kind']for x in rows],'singleLighthouseToggled':True,'bottleAndTerrainFocused':True},'nativeDoubleClickIncludesOriginalPointerUpSequence':True}
 r.pair('POINTER.picking',[],picking)
 def sandbox(s):
  s.reset();s.settle();assert not s.props();placed=[s.place(k)for k in['rock','shell']];s.locator('[data-action=undoProp]').click();s.tick();undo=s.props();assert len(undo)==1 and undo[0]['kind']=='rock';point=s.pick('edit');assert point;s.drag(point['x'],point['y'],45,-15);s.tick();assert len(s.props())==1;s.page.keyboard.press('Escape');assert s.evaluate('__bottleOcean.state.editMode')is None;point=s.pick('edit');assert point;s.click(point['x'],point['y']);s.tick();assert len(s.props())==1;s.place('shell');assert len(s.props())==2;s.locator('[data-action=resetProps]').click();s.tick();assert not s.props();s.page.keyboard.press('Escape');s.picture('sandbox-restored');return {'placements':placed,'undoResult':undo,'dragAndOrdinaryClickDidNotPlace':True,'afterRestore':s.props(),'comparison':{'placedKinds':[x['after'][-1]['kind']for x in placed],'afterUndoKinds':[x['kind']for x in undo],'afterRestore':[]}}
 r.pair('SANDBOX.props',[26,27,28,29],sandbox)
 def boundaries(s):
  s.reset();s.settle();s.locator('[data-edit=rock]').click();s.locator('#control-panel [data-action=toggleUI]').click();s.page.wait_for_timeout(400);rows=[]
  for kind in['bottle-centered','external-ocean','upper-sky']:
   point=s.evaluate('''kind=>{const b=__bottleOcean,e=b.environment,T=b.THREE,ray=new T.Raycaster(),blocked=new Set([e.ocean,...e.lighthouse.hitObjects]),targets=[e.terrain,e.rocks].filter(Boolean);for(const o of e.raycastTargets)if(o&&!blocked.has(o)&&!blocked.has(o.parent)&&o.name!=='birds'&&o.name!=='seaBirds'&&!o.material?.transparent&&!targets.includes(o))targets.push(o);let pos;if(kind==='upper-sky')pos={x:innerWidth*.3,y:innerHeight*.08};else{const v=kind==='bottle-centered'?b.bottle.root.position.clone():new T.Vector3(-3,.05,-20);v.project(b.camera);pos={x:(v.x+1)*innerWidth/2,y:(1-v.y)*innerHeight/2}}ray.setFromCamera(new T.Vector2(pos.x/innerWidth*2-1,1-pos.y/innerHeight*2),b.camera);const hit=ray.intersectObjects(targets,true)[0];return {...pos,canvasHit:document.elementFromPoint(pos.x,pos.y)===b.renderer.domElement,rayHit:hit?{object:hit.object.name,point:hit.point.toArray(),insideBottle:b.bottle.isInsideCavity(hit.point,.02)}:null}}''',kind);assert point['canvasHit'];before=s.props();s.click(point['x'],point['y']);s.tick();after=s.props();rows.append({'region':kind,'actualRay':point,'beforeCount':len(before),'afterCount':len(after),'toast':s.locator('#toast').text_content()})
   if kind=='upper-sky':assert len(before)==len(after)
  s.open_panel();s.locator('[data-action=resetProps]').click();s.page.keyboard.press('Escape');return {'representativeClicks':rows,'bottleCavityBranchActuallyHit':any(x['actualRay']['rayHit']and x['actualRay']['rayHit']['insideBottle']for x in rows),'notExhaustive':'All pixels, prop cap and unreachable cavity branch are not claimed; visible ocean may raycast opaque terrain below','comparison':{'regions':[x['region']for x in rows],'countDeltas':[x['afterCount']-x['beforeCount']for x in rows]}}
 r.pair('SANDBOX.boundaries',[],boundaries)
 def playback(s):
  s.reset();s.settle();s.locator('[data-action=pause]').click();s.tick();a=s.snapshot();s.frames(10);b=s.snapshot();assert a['diagnostics']['simTime']==b['diagnostics']['simTime']and a['diagnostics']['boat']==b['diagnostics']['boat']and b['draws']>a['draws'];s.drag(270,230,65,20);s.frames(6);c=s.snapshot();assert c['diagnostics']['simTime']==a['diagnostics']['simTime']and math.dist(a['diagnostics']['camera']['position'],c['diagnostics']['camera']['position'])>.01;s.locator('[data-action=pause]').click();s.frames(6);d=s.snapshot();assert d['diagnostics']['simTime']>b['diagnostics']['simTime'];return {'pausedStart':a,'pausedEnd':b,'cameraMovedWhilePaused':c,'resumed':d,'comparison':{'simulationFrozen':True,'drawingContinued':True,'cameraUsable':True,'resumed':True}}
 r.pair('PLAYBACK.pause',[30],playback)
 def reset_all(s):
  s.reset();s.slider('waveHeight',100);s.slider('brightness',1.6);s.locator('[data-toggle=dust]').click();s.locator('[data-preset=top]').click();s.settle();s.place('rock');s.locator('[data-action=pause]').click();assert s.evaluate('__bottleOcean.state.paused');before=s.snapshot();s.locator('[data-action=reset]').click();s.settle();after=s.snapshot();assert after['diagnostics']['state']==DEFAULTS and not s.props()and after['diagnostics']['camera']['preset']=='cinema'and not after['ui']['edit'];return {'changedBeforeReset':before,'actualAfterReset':after,'afterProps':s.props(),'comparison':{'state':after['diagnostics']['state'],'preset':after['diagnostics']['camera']['preset'],'props':[]}}
 r.pair('PLAYBACK.reset-all',[31],reset_all)
 def keyboard(s):
  s.reset();s.click(100,190);s.page.keyboard.press('h');assert s.evaluate('document.body.classList.contains("ui-hidden")');s.page.keyboard.press('h');assert not s.evaluate('document.body.classList.contains("ui-hidden")');s.locator('#waveHeight').focus();before=s.evaluate('__bottleOcean.state.paused');s.page.keyboard.press('h');s.page.keyboard.press('Space');assert not s.evaluate('document.body.classList.contains("ui-hidden")')and s.evaluate('__bottleOcean.state.paused')==before;s.click(100,190);s.page.keyboard.press('Space');assert s.evaluate('__bottleOcean.state.paused');s.page.keyboard.press('Space');assert not s.evaluate('__bottleOcean.state.paused');s.locator('[data-action=pause]').focus();s.page.keyboard.press('Space');assert s.evaluate('__bottleOcean.state.paused');s.page.keyboard.press('Space');assert not s.evaluate('__bottleOcean.state.paused');s.locator('[data-edit=rock]').click();s.locator('#waveHeight').focus();s.page.keyboard.press('Escape');assert s.evaluate('__bottleOcean.state.editMode')is None;keys=s.evaluate('__parityProbe.keys');trace=[]
  if s.side=='embedded':
   original=s.page.evaluate('({scrollY,displayH:document.querySelector("#tour-host").dataset.displayH,targetH:document.querySelector("#tour-host").dataset.targetH})');s.page.locator('button[data-project-view=live]').click()
   for _ in range(48):
    s.page.keyboard.press('Tab');s.page.wait_for_timeout(70);inside=s.page.evaluate('document.activeElement===document.querySelector("iframe")');at=s.evaluate('({tag:document.activeElement.tagName,id:document.activeElement.id})');trace.append({'key':'Tab','inside':inside,'child':at})
    if inside and at['tag']not in['BODY','HTML']:break
   assert inside and at['tag']not in['BODY','HTML']
   for _ in range(48):
    s.page.keyboard.press('Shift+Tab');s.page.wait_for_timeout(70);toolbar=s.page.evaluate('!!document.activeElement.closest(".tour-project-header")');trace.append({'key':'Shift+Tab','toolbar':toolbar})
    if toolbar:break
   assert toolbar;now=s.page.evaluate('({scrollY,displayH:document.querySelector("#tour-host").dataset.displayH,targetH:document.querySelector("#tour-host").dataset.targetH})');assert original==now;s.page.locator('button[data-project-view=live]').click();s.page.keyboard.press('Escape');s.page.wait_for_function('!document.querySelector(".tour-project-dialog").open',polling=100)
  return {'originalKeys':keys,'hostNativeTabTrace':trace,'comparison':{'HHiddenRestored':True,'inputProtected':True,'buttonSpaceOnce':True,'EscapeExitedEdit':True}}
 r.pair('INPUT.keyboard',[],keyboard)
 def exports(s):
  s.open_panel();s.quality('retro');d=s.download(r.case_id.replace('.','-')+'-original-button-export');return {'download':d,'comparison':{'PNG':d['PNG'],'native':True}}
 r.pair('EXPORT.desktop',[33],exports)
 r.pair('EXPORT.phone',[33],exports,config='phone')
 def hidden_export(s):
  s.reset();s.open_panel();d=s.download('hidden-ui-keyboard-export',hidden=True);return {'download':d,'comparison':{'PNG':d['PNG'],'hiddenOriginalButtonActivated':True}}
 r.pair('EXPORT.hidden',[],hidden_export)
finally:r.finish()
