from pathlib import Path
import json
from playwright.sync_api import sync_playwright
from harness import Harness,arguments,OUT

args=arguments();copy=Path(json.loads((OUT/'hmr-copy.json').read_text())['path']);counter=0
with sync_playwright()as pw:
    h=Harness(pw,args)
    def module_update(phase):
        global counter
        c,p=h.setup(url='http://127.0.0.1:5196/');pending=[];block=[phase=='loading'];fail=[phase=='error']
        def route(r):
            if block[0]:pending.append(r)
            elif fail[0]:r.abort('failed')
            else:r.continue_()
        c.route('**/experiments/lawson/assets/models/lawson_scene.glb',route)
        h.c2(p);h.open(p)
        if phase=='ready':h.ready(p)
        elif phase=='error':h.state(p,'error')
        else:h.child(p);p.wait_for_function('document.querySelector("iframe").contentWindow.__LAWSON__?.ready===false')
        p.evaluate('window.__priorHost=document.querySelector("#tour-host");window.__priorFrame=document.querySelector("iframe");window.__priorAudit=__priorFrame.contentWindow.__audit')
        file=copy/'src/tour/startTourPrototype.ts';counter+=1;file.write_text(file.read_text()+'\n// step6 real HMR '+str(counter)+'\n')
        p.wait_for_function('document.querySelector("#tour-host")!==window.__priorHost&&document.querySelector("main")?.dataset.layoutReady==="true"',timeout=60000,polling=100)
        assert p.locator('iframe').count()==0 and p.locator('dialog[open]').count()==0 and p.locator('#tour-host canvas').count()==1
        assert p.evaluate('!__priorFrame.isConnected&&!document.documentElement.classList.contains("tour-project-open")')
        n=p.evaluate('__priorAudit.draws');p.wait_for_timeout(600);assert p.evaluate('__priorAudit.draws')==n
        block[0]=False;fail[0]=False
        for r in pending:
            try:r.continue_()
            except Exception:pass
        h.c2(p);h.open(p);h.ready(p);assert p.locator('iframe').count()==1;h.close(p)
        return {'phaseBeforeUpdate':phase,'realViteModuleUpdate':True,'oldOriginalUnloadedAndDrawsStopped':True,'oneNewHostCanvas':True,'newExperienceReady':True,'workingRepositoryMutatedForTest':False}
    for phase in ['loading','ready','error']:h.check('HMR module '+phase,lambda phase=phase:module_update(phase))
    def css_update():
        c,p=h.setup(url='http://127.0.0.1:5196/');h.c2(p);h.open(p);h.ready(p);p.evaluate('window.__cssPriorFrame=document.querySelector("iframe")')
        file=copy/'src/tour/projectHost.css';file.write_text(file.read_text()+'\n:root { --step6-css-update: applied; }\n')
        p.wait_for_function('getComputedStyle(document.documentElement).getPropertyValue("--step6-css-update").trim()==="applied"')
        assert p.evaluate('__cssPriorFrame===document.querySelector("iframe")')and p.locator('iframe').count()==1
        assert h.draws(p,p)==0;h.close(p)
        return {'realViteCSSUpdate':True,'liveIframePreserved':True,'hostStillSuspended':True}
    h.check('HMR stylesheet keeps current instance',css_update)
    passed=h.finish()
raise SystemExit(0 if passed else 1)
