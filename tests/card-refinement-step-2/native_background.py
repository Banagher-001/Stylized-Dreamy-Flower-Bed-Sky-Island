"""Native tab visibility with a browser launched outside Playwright defaults."""
from pathlib import Path
import argparse,os,subprocess,tempfile,time,json,signal,shutil,traceback
from playwright.sync_api import sync_playwright
p=argparse.ArgumentParser();p.add_argument('--origin',required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--env-file',type=Path,required=True);p.add_argument('--build-record',type=Path);args=p.parse_args()
args.out.mkdir(parents=True,exist_ok=False);shutil.copyfile(__file__,args.out/'native_background.py.txt')
os.environ.update(json.loads(args.env_file.read_text())['browserEnvironment'])
scratch=Path(tempfile.mkdtemp(prefix='card-native-background-',dir='/tmp'))
result={'complete':False,'nativeBrowser':True,'playwrightNoDefaults':True,'documentPropertiesOverridden':False,'clockModified':False}
if args.build_record:
 build=json.loads(args.build_record.read_text());result.update(candidateId=build['candidateId'],runtimeInputDigest=build['runtimeInputDigest'])
process=None;browser=None
try:
 process=subprocess.Popen(['/usr/bin/chromium','--no-sandbox','--remote-debugging-port=0','--user-data-dir='+str(scratch/'profile'),'--no-first-run','--no-default-browser-check','--disable-background-networking','--disable-component-update','--disable-dev-shm-usage','--use-gl=angle','--use-angle=gl','--ignore-gpu-blocklist','--window-size=1680,1040','about:blank'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
 port_file=scratch/'profile/DevToolsActivePort';deadline=time.monotonic()+12
 while not port_file.exists():
  assert process.poll() is None,'Native Chrome exited before readiness'
  assert time.monotonic()<deadline,'Native Chrome startup timeout'
  time.sleep(.1)
 port=int(port_file.read_text().splitlines()[0])
 with sync_playwright() as pw:
  browser=pw.chromium.connect_over_cdp('http://127.0.0.1:'+str(port),no_defaults=True)
  ctx=browser.contexts[0];page=ctx.pages[0];page.set_viewport_size({'width':1652,'height':949})
  errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(args.origin,wait_until='domcontentloaded')
  page.wait_for_function('document.querySelector("main")?.dataset.layoutReady==="true"&&document.querySelector("#tour-host")?.dataset.renderState==="ready"',timeout=90000)
  page.bring_to_front();visible=page.evaluate('document.visibilityState');assert visible=='visible',visible
  delta=page.evaluate('3.34/12.3*(document.documentElement.scrollHeight-innerHeight)-scrollY')
  page.mouse.move(24,300);page.mouse.wheel(0,delta)
  page.wait_for_function('document.querySelector(".ar-tools-browser").dataset.entranceSubphase==="flying"')
  source_window=ctx.new_cdp_session(page).send('Browser.getWindowForTarget')['windowId']
  other=ctx.new_page();other.goto('about:blank');other.bring_to_front()
  target_window=ctx.new_cdp_session(other).send('Browser.getWindowForTarget')['windowId']
  assert source_window==target_window,('Not tabs in the same native window',source_window,target_window)
  page.wait_for_function('document.hidden',polling=100,timeout=10000)
  page.wait_for_function('document.querySelector(".ar-tools-browser").dataset.entranceReason==="page-hidden"',polling=100)
  hidden=page.evaluate('({visibility:document.visibilityState,data:{...document.querySelector(".ar-tools-browser").dataset},flights:document.querySelectorAll(".ar-flight-stage").length})')
  page.bring_to_front();page.wait_for_function('document.visibilityState==="visible"',polling=100);page.wait_for_timeout(550)
  returned=page.evaluate('({visibility:document.visibilityState,data:{...document.querySelector(".ar-tools-browser").dataset},flights:document.querySelectorAll(".ar-flight-stage").length,cards:document.querySelectorAll(".ar-tools-browser .ar-tool-card").length})')
  assert hidden['visibility']=='hidden' and hidden['flights']==0
  assert returned['flights']==0 and returned['cards']==22 and returned['data']['entranceAttempts']==hidden['data']['entranceAttempts']
  assert returned['data']['entranceFramePending']=='false' and returned['data']['entranceHoldPending']=='false'
  assert not errors,errors
  page.screenshot(path=str(args.out/'native-background-return.png'));other.close()
  result.update(complete=True,version=browser.version,visibleBeforeSwitch=visible,sameNativeWindow=True,sourceWindow=source_window,targetWindow=target_window,hidden=hidden,returned=returned,errors=errors)
  browser.close();browser=None
except Exception as error:
 result.update(error=str(error),traceback=traceback.format_exc())
finally:
 if browser:
  try:browser.close()
  except Exception:pass
 if process:
  if process.poll() is None:os.killpg(os.getpgid(process.pid),signal.SIGTERM)
  try:process.wait(timeout=6)
  except subprocess.TimeoutExpired:os.killpg(os.getpgid(process.pid),signal.SIGKILL);process.wait(timeout=5)
 shutil.rmtree(scratch,ignore_errors=True);result['ownedNativeBrowserStopped']=True
 (args.out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:result[k] for k in ['complete','error','visibleBeforeSwitch','sameNativeWindow','ownedNativeBrowserStopped'] if k in result},ensure_ascii=False),flush=True)
raise SystemExit(0 if result['complete'] else 1)
