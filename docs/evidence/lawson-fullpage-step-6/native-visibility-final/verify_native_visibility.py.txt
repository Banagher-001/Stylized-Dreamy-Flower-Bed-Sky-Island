"""Use an owned Chrome default context with no automation focus overrides."""
from pathlib import Path
import json,subprocess,tempfile,time,shutil,traceback
from playwright.sync_api import sync_playwright
from harness import arguments,OUT,AUDIT

args=arguments();folder=OUT/args.run;folder.mkdir(exist_ok=False);shutil.copyfile(__file__,folder/'verify_native_visibility.py.txt')
profile=Path(tempfile.mkdtemp(prefix='lawson-step6-native-',dir='/tmp'))
report={'checks':[],'events':[],'noDefaultsCDP':True,'documentPropertiesOrEventsFaked':False,'physicalDevice':False}
log=(folder/'chrome.log').open('w')
command=['/usr/bin/chromium','--no-sandbox','--no-first-run','--no-default-browser-check','--disable-background-networking','--disable-component-update','--use-gl=angle','--use-angle=gl','--ignore-gpu-blocklist','--window-size=1440,1000','--remote-debugging-port=0','--user-data-dir='+str(profile),'about:blank']
process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
def save():(folder/'browser.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
try:
    port_file=profile/'DevToolsActivePort';deadline=time.monotonic()+20
    while not port_file.exists()and process.poll()is None and time.monotonic()<deadline:time.sleep(.1)
    assert port_file.exists(),'Chrome debug port unavailable'
    port=int(port_file.read_text().splitlines()[0]);report.update(ownedChromePID=process.pid,browserDebugPort=port)
    with sync_playwright()as pw:
        browser=pw.chromium.connect_over_cdp('http://127.0.0.1:'+str(port),no_defaults=True);report['browserVersion']=browser.version
        context=browser.contexts[0];context.add_init_script(AUDIT)
        for phase in ['loading','ready','error']:
            page=context.new_page();page.set_default_timeout(20000);pending=[];block=[phase=='loading'];bad=[phase=='error']
            page.on('pageerror',lambda e,tag=phase:report['events'].append({'case':'native visibility '+tag,'kind':'pageerror','text':str(e)}))
            page.on('requestfailed',lambda r,tag=phase:report['events'].append({'case':'native visibility '+tag,'kind':'requestfailed','text':r.failure,'url':r.url}))
            page.on('console',lambda m,tag=phase:report['events'].append({'case':'native visibility '+tag,'kind':'console','level':m.type,'text':m.text})if m.type in ['error','warning']else None)
            def route(r):
                if block[0]:pending.append(r)
                elif bad[0]:r.abort('failed')
                else:r.continue_()
            context.route('**/experiments/lawson/assets/models/lawson_scene.glb',route)
            try:
                page.goto('http://127.0.0.1:4196/',wait_until='domcontentloaded');page.wait_for_function('document.querySelector("main")?.dataset.layoutReady==="true"',timeout=60000,polling=100)
                if page.locator('main').get_attribute('data-reading-mode')=='stable':page.locator('article[data-experiment-station=C2]').scroll_into_view_if_needed()
                else:
                    page.evaluate('scrollTo({top:(document.documentElement.scrollHeight-innerHeight)*10.05/12.3,behavior:"instant"})');page.wait_for_function('Math.abs(Number(document.querySelector("#tour-host").dataset.displayH)-10.05)<.005',polling=100)
                page.locator('[data-project-tab=live]').click();page.wait_for_selector('iframe',state='attached')
                if phase!='loading':page.wait_for_function('s=>document.querySelector(".tour-project-dialog").dataset.embeddedState===s',arg='ready'if phase=='ready'else'error',timeout=90000,polling=100)
                page.evaluate('window.__savedIframe=document.querySelector("iframe")')
                other=context.new_page();other.goto('about:blank');other.bring_to_front()
                page.wait_for_function('document.hidden===true',timeout=10000,polling=100)
                hidden=page.evaluate('({state:document.visibilityState,events:__audit.visibility})')
                child_hidden=page.locator('iframe').element_handle().content_frame().evaluate('document.hidden')
                wait_ms=13000 if phase=='loading'else 500;page.wait_for_timeout(wait_ms)
                hidden_state=page.locator('.tour-project-dialog').get_attribute('data-embedded-state')
                assert hidden_state!='error'or phase=='error',hidden_state
                other.close();page.bring_to_front();page.wait_for_function('!document.hidden',polling=100)
                assert page.evaluate('document.querySelector("iframe")===__savedIframe')
                if phase=='loading':
                    page.wait_for_function('document.querySelector(".tour-project-dialog").dataset.embeddedState==="slow"',timeout=3000,polling=100)
                    block[0]=False
                    for r in pending:r.continue_()
                elif phase=='error':bad[0]=False;page.locator('.tour-project-retry').click()
                page.wait_for_function('document.querySelector(".tour-project-dialog").dataset.embeddedState==="ready"',timeout=90000,polling=100)
                assert page.locator('#tour-guide').get_attribute('aria-pressed')=='false'
                n=page.evaluate('__audit.draws');page.wait_for_timeout(1000);assert page.evaluate('__audit.draws')==n
                shows=page.evaluate('__audit.visibility');page.locator('.tour-project-close').click();page.wait_for_timeout(250);assert page.locator('iframe').count()==0
                report['checks'].append({'name':'native visibility '+phase,'passed':True,'evidence':{'actualHidden':hidden,'childActuallyHidden':child_hidden,'backgroundWaitMS':wait_ms,'stateWhileHidden':hidden_state,'returnedEvents':shows,'sameInstanceAcrossTabSwitch':True,'stateUsableAfterReturn':True,'parentCoveredDraws':0}});print('PASS native visibility '+phase,flush=True)
            except Exception as e:
                try:page.screenshot(path=str(folder/('failure-'+phase+'.png')))
                except Exception:pass
                report['checks'].append({'name':'native visibility '+phase,'passed':False,'error':str(e),'traceback':traceback.format_exc()});print('FAIL native visibility '+phase+': '+str(e),flush=True)
            finally:
                context.unroute_all(behavior='ignoreErrors');page.close();save()
        browser.close()
finally:
    if process.poll()is None:process.terminate()
    try:process.wait(timeout=8)
    except subprocess.TimeoutExpired:process.kill();process.wait()
    log.close();shutil.rmtree(profile,ignore_errors=True)
    report['ownedChromeStopped']=process.poll()is not None;report['temporaryProfileRemoved']=not profile.exists();report['passed']=len(report['checks'])==3 and all(c['passed']for c in report['checks']);save()
print(json.dumps({'passed':report['passed'],'checks':len(report['checks'])}),flush=True)
raise SystemExit(0 if report['passed']else 1)
