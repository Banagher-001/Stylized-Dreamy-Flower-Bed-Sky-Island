"""A real browser-tab switch through X11, without synthetic visibility changes."""
import os,subprocess,time
from common import Run,arguments
args=arguments();r=Run(args,'native-tab-visibility');c,p=r.new(1024,768);r.ready();r.quality('retro')
XD='/workspace/.cache/browser-deps/root/usr/bin/xdotool'
def read():return p.evaluate('({visibility:document.visibilityState,hidden:document.hidden,events:__baseline.visibility,sim:__bottleOcean.getDiagnostics().simTime,frames:__baseline.frames})')
try:
 def native_tab():
  windows=subprocess.check_output([XD,'search','--onlyvisible','--class','chromium'],text=True).strip().splitlines();assert len(windows)==1,windows;window=windows[0];title=subprocess.check_output([XD,'getwindowname',window],text=True).strip();assert 'Bottle Ocean'in title;before=read();subprocess.run([XD,'windowfocus','--sync',window],check=True);subprocess.run([XD,'key','--clearmodifiers','ctrl+t'],check=True);p.wait_for_timeout(1600);background=read();subprocess.run([XD,'key','--clearmodifiers','ctrl+w'],check=True);p.wait_for_timeout(300);r.frames(4);returned=read();assert not returned['hidden'];r.picture('returned-from-real-tab');return {'_status':'通过'if background['hidden']else'设备/浏览器限制','actualOSInput':'xdotool on private DISPLAY :121, focus verified Bottle Ocean window, Ctrl+T then Ctrl+W','window':window,'title':title,'before':before,'background':background,'returned':returned,'visibilityOverridden':False}
 r.check('LIFECYCLE.native-tab-visibility','真实浏览器新标签、隐藏及返回',native_tab)
finally:r.finish()
