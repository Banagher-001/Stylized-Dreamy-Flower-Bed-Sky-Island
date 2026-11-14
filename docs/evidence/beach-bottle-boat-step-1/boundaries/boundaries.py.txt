"""Record original camera reset inertia, editing rays and hidden-UI export."""
import math,struct
from common import Run,arguments
args=arguments();r=Run(args,'boundaries');c,p=r.new(1280,720);r.ready();r.quality('retro')
def cam():return p.evaluate('__bottleOcean.cameraRig.getState()')
def count():return p.evaluate('''()=>{let n=0;__bottleOcean.scene.traverse(o=>{if(o.userData.propKind)n++});return n}''')
try:
 def inertia():
  r.reset();p.wait_for_timeout(1450);r.frames(4);before=cam();p.mouse.move(200,230);p.mouse.down();p.mouse.move(360,255,steps=8);p.mouse.up();r.frames(4);p.locator('[data-action=resetCamera]').click();p.wait_for_timeout(1450);r.frames(4);early=cam();r.frames(80);late=cam();error=math.dist(late['position'],[.55,2.15,6.5]);r.picture('camera-reset-after-damping');return {'_status':'原页已有问题'if error>.01 else'通过','before':before,'afterTween':early,'after80MoreRenderedFrames':late,'positionErrorVsDeclaredCinema':error,'input':'Native rotate followed by native resetCamera; no direct camera write','note':'OrbitControls residual delta is not cleared by preset tween; active preset label may be cinema while final coordinates drift'}
 r.check('CAMERA.reset-inertia','原恢复镜头后的残余惯性',inertia)
 def editing_rules():
  r.reset();p.wait_for_timeout(1450);r.frames(4);p.locator('[data-edit=rock]').click();p.locator('#control-panel [data-action=toggleUI]').click();p.wait_for_timeout(500);rows=[]
  for kind in['bottle-centered','external-ocean','upper-sky']:
   target=p.evaluate('''kind=>{const b=__bottleOcean,e=b.environment,T=b.THREE,ray=new T.Raycaster(),blocked=new Set([e.ocean,...e.lighthouse.hitObjects]),targets=[e.terrain,e.rocks].filter(Boolean);for(const o of e.raycastTargets)if(o&&!blocked.has(o)&&!blocked.has(o.parent)&&o.name!=='birds'&&o.name!=='seaBirds'&&!o.material?.transparent&&!targets.includes(o))targets.push(o);let pos;if(kind==='upper-sky')pos={x:innerWidth*.3,y:innerHeight*.08};else{const v=kind==='bottle-centered'?b.bottle.root.position.clone():new T.Vector3(-3,.05,-20);v.project(b.camera);pos={x:(v.x+1)*innerWidth/2,y:(1-v.y)*innerHeight/2}}ray.setFromCamera(new T.Vector2(pos.x/innerWidth*2-1,1-pos.y/innerHeight*2),b.camera);const hit=ray.intersectObjects(targets,true)[0];return {...pos,canvasHit:document.elementFromPoint(pos.x,pos.y)===b.renderer.domElement,rayHit:hit?{object:hit.object.name,point:hit.point.toArray(),insideBottle:b.bottle.isInsideCavity(hit.point,.02)}:null}}''',kind)
   assert target['canvasHit'];before=count();p.mouse.click(target['x'],target['y']);r.frames(3);after=count();toast=p.locator('#toast').text_content();rows.append({'region':kind,'nativePoint':target,'countBefore':before,'countAfter':after,'toast':toast});r.picture('editing-'+kind)
  p.locator('#restore-ui').click();p.locator('[data-action=resetProps]').click();p.keyboard.press('Escape');return {'representativeClicks':rows,'note':'Editing ray excludes ocean itself and tests underlying opaque ground. Clicking visible ocean can still place on terrain below; clicking bottle is not sufficient to prove actual ray point lies inside cavity. UI exposes rock and shell only; limit/all pixels not tested.'}
 r.check('SANDBOX.representative-rules','瓶中、外海和天空代表点的真实编辑射线',editing_rules)
 def hidden_export():
  r.reset();p.locator('[data-action=screenshot]').focus();p.keyboard.press('h');assert p.evaluate('document.body.classList.contains("ui-hidden")');active=p.evaluate('({tag:document.activeElement.tagName,action:document.activeElement.dataset.action})')
  with p.expect_download(timeout=15000)as wait:p.keyboard.press('Enter')
  d=wait.value;path=r.folder/'hidden-ui-native-keyboard-export.png';d.save_as(str(path));raw=path.read_bytes();size=list(struct.unpack('>II',raw[16:24]));assert size==[1280,720];assert p.evaluate('document.body.classList.contains("ui-hidden")');p.locator('#restore-ui').click();return {'focusBeforeActivation':active,'nativeSequence':'Focus original screenshot button; H hides UI; Enter activates still-focused original button','download':d.suggested_filename,'PNG':size,'bytes':len(raw),'exportIncludesDOMPanel':False}
 r.check('EXPORT.hidden-ui-keyboard','隐藏UI后原截图按钮的真实键盘导出',hidden_export)
finally:r.finish()
