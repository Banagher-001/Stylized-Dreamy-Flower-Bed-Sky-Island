"""Same real native visibility/context assertions, current pool and separate receipts."""
from pathlib import Path
source=(Path(__file__).with_name('step7_recovery.py')).read_text().replace('docs/evidence/scroll-garden-step-7','docs/evidence/scroll-garden-step-10').replace('step7-native-','step10-native-').replace('STEP 07','张辰翰')
ending='''  go(12.3);wait('document.querySelector(".tour-heading").dataset.kind==="closing"&&document.querySelector(".tour-heading").dataset.opacity==="1.0000000"')
  if evaluate('document.querySelector("#tour-host").dataset.motionState')!='paused':native_click('#tour-motion')
  evaluate('window.__endingCanvas=document.querySelector("canvas")');before=state();pic=image('native-ending-before-hide.png');other=hide();time.sleep(.35);show(other)
  assert state()==before and ImageChops.difference(pic,image('native-ending-after-show.png')).getbbox()is None
  assert evaluate('[...document.querySelectorAll("[data-tour-replay]")].every(b=>!b.disabled)')
  record('ending real hidden/return preserves exact paused story, replay controls and pixels',{'actualDocumentHiddenObserved':True,'sameState':before,'pixelsExact':True})
  pic=image('native-ending-before-loss.png');lose();assert evaluate('[...document.querySelectorAll("[data-tour-replay]")].every(b=>b.disabled)&&!document.querySelector("#tour-reference").hidden')
  restore();wait('document.querySelector("#tour-host").dataset.renderState==="ready"');settled()
  assert state()==before and ImageChops.difference(pic,image('native-ending-after-loss.png')).getbbox()is None
  native_click('[data-tour-replay=overview]');wait('Math.abs(Number(document.querySelector("#tour-host").dataset.displayH))<.003&&document.querySelector("#tour-host").dataset.cameraState==="settled"');settled()
  assert evaluate('document.activeElement.id==="tour-stop-overview"&&window.__endingCanvas===document.querySelector("canvas")')
  assert evaluate('document.querySelector("#tour-host").dataset.sceneTime')==before['time']
  record('ending context recovery restores replay and returns opening with same canvas/time/focus',{'pixelsExact':True,'replayDisabledWhileLost':True,'fallbackReferenceVisibleWhileLost':True,'oneCanvas':True,'clockUnchanged':True,'focus':'tour-stop-overview'})
'''
source=source.replace("  exceptions=[e['params']for e in events",ending+"  exceptions=[e['params']for e in events",1).replace('Seven native visibility/context recovery groups passed.','Nine native visibility/context/ending recovery groups passed.')
exec(compile(source,'<Step10 native recovery>','exec'),globals())
