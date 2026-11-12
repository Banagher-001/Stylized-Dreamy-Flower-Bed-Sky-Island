"""Native original retry on a real failed model fetch in the independent page."""
import argparse
from common import Run,INSTALL,MODE
p=argparse.ArgumentParser();p.add_argument('--run',required=True);args=p.parse_args();assert MODE=='standalone'
r=Run('readiness',args.run);page=r.page
try:
    r.case('READINESS.load','独立原页默认加载',r.load)
    def retry():
        bad=[True];r.context.route('**/assets/models/lawson_scene.glb',lambda route:route.abort('failed')if bad[0]else route.continue_())
        page.evaluate('location.reload()');page.locator('#fatal').wait_for(state='visible',timeout=40000)
        assert page.evaluate('__LAWSON__.error!==null&&!__LAWSON__.ready');message=page.locator('#fatal-msg').inner_text();r.picture('original-fatal')
        page.evaluate('window.__failedOriginalDocument=true');bad[0]=False;page.locator('#fatal-retry').click();page.wait_for_function('window.__LAWSON__?.ready===true',timeout=90000,polling=100);page.locator('#loader').wait_for(state='hidden')
        assert page.evaluate('window.__failedOriginalDocument===undefined')and page.locator('#fatal').is_hidden();page.evaluate(INSTALL)
        r.picture('original-fatal-retry-ready')
        return {'realOriginalModelFetchAborted':True,'originalError':message,'nativeOriginalFatalRetry':True,'newDocumentReady':True,'defaultsAfterRetry':r.state()}
    r.case('READINESS.retry','独立原页资源失败与原重试',retry)
finally:r.finish()
