"""Fresh native lifecycle regression plus exact clouded pixels on GL recovery.
Old harness and RPC transport are read-only. No fabricated visibility events.
"""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
source=(ROOT/'tests/garden-enhancement/step4_native.py').read_text()
source=source.replace('garden-enhancement-step-4','garden-enhancement-step-6').replace('garden-step4-native-','garden-step6-native-').replace('127.0.0.1:4177','127.0.0.1:4181')
body_start=source.index("body=r'''" )+len("body=r'''")
body_end=source.index("\n'''",body_start)
body=source[body_start:body_end]
canvas=r'''
  def cloud_canvas(name):
   evaluate('window.__cloudIsolation=document.createElement("style");window.__cloudIsolation.textContent="#app *:not(canvas){visibility:hidden!important}#app canvas{visibility:visible!important}";document.head.append(window.__cloudIsolation)')
   settled();result=image(name);evaluate('window.__cloudIsolation.remove()');settled();return result
'''
body=body.replace('  # Native scrollbar',canvas+'\n  # Native scrollbar')
body=body.replace('  before=start(2.54);lose();',"  before=start(2.54);cloud_before=cloud_canvas('native-cloud-before-loss.png');lose();",1)
needle="  record('real context loss retains all text and restores one canvas without guide restart',"
assert needle in body
body=body.replace(needle,"  cloud_after=cloud_canvas('native-cloud-after-restore.png');assert ImageChops.difference(cloud_before,cloud_after).getbbox()is None\n"+needle,1)
extra=r'''
  native_click('#tour-layout-toggle');wait('document.querySelector("main").dataset.readingMode==="immersive"');native_click('#tour-stop-overview');settled()
  native_click('#tour-motion');wait('Number(document.querySelector("#tour-host").dataset.sceneTime)>2.3')
  other=hide();hidden=guide_state();draws=evaluate('window.__tourProbe.draws');time.sleep(.65)
  assert guide_state()['time']==hidden['time']and evaluate('window.__tourProbe.draws')==draws
  show(other);native_click('#tour-motion');after=guide_state()
  assert 0<=float(after['time'])-float(hidden['time'])<.4,(hidden,after)
  record('playing cloud environment freezes in a true hidden target and returns without catch-up',{'hidden':hidden,'after':after,'hiddenWindowMs':650,'zeroHiddenDraws':True,'actualTargetVisibility':True})
'''
body=body.replace("  exceptions=[e['params']",extra+"\n  exceptions=[e['params']")
body=body.replace("'fakeHiddenEventsUsed':False", "'fakeHiddenEventsUsed':False,'exactCloudedCanvasBeforeAfterContextRestore':True,'exactBirdOverviewBeforeAfterContextRestore':True")
body=body.replace("  exceptions=[e['params']", '\n  go(0);before_birds=guide_state();birds_before=cloud_canvas(\'native-birds-overview-before-loss.png\')\n  lose();wait(\'document.querySelector("main").dataset.readingMode==="stable"\');restore();wait(\'document.querySelector("main").dataset.immersiveAvailable==="true"\')\n  native_click(\'#tour-layout-toggle\');wait(\'document.querySelector("main").dataset.readingMode==="immersive"\');go(0);settled()\n  birds_after=cloud_canvas(\'native-birds-overview-after-restore.png\');assert ImageChops.difference(birds_before,birds_after).getbbox()is None\n  assert guide_state()[\'time\']==before_birds[\'time\']\n  record(\'actual complete birded overview survives context loss with frozen wings and cloud state\',{\'before\':before_birds,\'after\':guide_state(),\'fullGpuCanvasExact\':True,\'birdResources\':evaluate(\'JSON.parse(document.querySelector("#tour-host").dataset.birdResources)\')})\n'+"\n  exceptions=[e['params']")
source=source[:body_start]+body+source[body_end:]
exec(compile(source,'<Step5 actual native cloud lifecycle>','exec'),globals())
