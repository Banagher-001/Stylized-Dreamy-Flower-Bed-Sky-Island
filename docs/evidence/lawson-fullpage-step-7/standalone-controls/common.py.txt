"""Matched original/embedded native-input runner. Never changes app clocks/files."""
from pathlib import Path
import ast,hashlib,json,os,shutil,time,traceback
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/evidence/lawson-fullpage-step-7'
BASE='http://127.0.0.1:4197';MODE=os.environ.get('LAWSON_MODE','standalone')
def constant(path,name):
    tree=ast.parse(path.read_text())
    return next(ast.literal_eval(n.value)for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id==name for t in n.targets))
PROBE=constant(ROOT/'tests/lawson-integration/step1_browser.py','PROBE')
INSTALL=constant(ROOT/'tests/lawson-fullpage/common.py','INSTALL')

class Mouse:
    def __init__(self,target):self.target=target
    def point(self,x,y):
        if self.target.frame==self.target.owner:return x,y
        b=self.target.owner.locator('.tour-project-embed-mount > iframe').bounding_box();return x+b['x'],y+b['y']
    def move(self,x,y,**kw):return self.target.owner.mouse.move(*self.point(x,y),**kw)
    def click(self,x,y,**kw):return self.target.owner.mouse.click(*self.point(x,y),**kw)
    def down(self,**kw):return self.target.owner.mouse.down(**kw)
    def up(self,**kw):return self.target.owner.mouse.up(**kw)
    def wheel(self,x,y):return self.target.owner.mouse.wheel(x,y)
class Target:
    def __init__(self,owner):self.owner=owner;self.frame=owner;self.mouse=Mouse(self);self.keyboard=owner.keyboard
    def __getattr__(self,key):return getattr(self.frame,key)
    def set_viewport_size(self,size):
        w,h=size['width'],size['height'];bar=48 if w<=767 or h+56<=480 else 56
        self.owner.set_viewport_size({'width':w,'height':h+(bar if MODE=='embedded'else 0)})
        if MODE=='embedded'and self.frame!=self.owner:self.frame.wait_for_function('s=>innerWidth===s.width&&innerHeight===s.height',arg=size,polling=100)

class Run:
    def __init__(self,phase,run,width=960,height=540):
        assert MODE in ['standalone','embedded']
        self.phase=phase;self.run=run;self.folder=OUT/run;self.folder.mkdir(exist_ok=False)
        self.path=self.folder/(phase+'.json');self.case_id='setup';self.only=None
        self.report={'phase':phase,'run':run,'mode':MODE,'checks':[],'pageErrors':[],'console':[],'requestsFailed':[],'httpErrors':[],
          'scope':'untouched independent original'if MODE=='standalone'else'actual production personal website iframe',
          'sourceFilesModified':False,'clockModified':False,'physicalDevice':False,'environment':{'DISPLAY':os.environ.get('DISPLAY'),'backend':'Mesa llvmpipe software GL','hardwareFPSProof':False}}
        for p in Path(__file__).parent.glob('*.py'):shutil.copyfile(p,self.folder/(p.name+'.txt'))
        self.pw=sync_playwright().start();self.browser=self.pw.chromium.launch(executable_path='/usr/bin/chromium',headless=False,args=['--no-sandbox','--use-gl=angle','--use-angle=gl','--ignore-gpu-blocklist'])
        self.report['browserVersion']=self.browser.version
        bar=48 if width<=767 or height+56<=480 else 56
        self.context=self.browser.new_context(viewport={'width':width,'height':height+(bar if MODE=='embedded'else 0)},device_scale_factor=1)
        self.context.add_init_script(PROBE);self.owner=self.context.new_page();self.owner.set_default_timeout(30000);self.watch(self.owner)
        self.page=Target(self.owner)
    def watch(self,p):
        p.on('pageerror',lambda e:self.report['pageErrors'].append({'case':self.case_id,'text':str(e)}))
        p.on('console',lambda m:self.report['console'].append({'case':self.case_id,'type':m.type,'text':m.text,'location':m.location})if m.type in ['warning','error']else None)
        p.on('requestfailed',lambda r:self.report['requestsFailed'].append({'case':self.case_id,'url':r.url,'failure':r.failure}))
        p.on('response',lambda r:self.report['httpErrors'].append({'case':self.case_id,'url':r.url,'status':r.status})if r.status>=400 else None)
    def save(self):self.path.write_text(json.dumps(self.report,ensure_ascii=False,indent=2)+'\n')
    def case(self,identifier,name,fn):
        if self.only and identifier not in self.only and not identifier.startswith('LOAD.')and not identifier.endswith('.load'):return
        self.case_id=identifier
        try:
            evidence=fn();status=evidence.pop('_status','原页正常')if isinstance(evidence,dict)else'原页正常'
            row={'id':identifier,'name':name,'status':status,'evidence':evidence}
            print(status+' '+MODE+' '+identifier,flush=True)
        except Exception as e:
            row={'id':identifier,'name':name,'status':'需补核','error':str(e),'traceback':traceback.format_exc()}
            try:row['snapshot']=self.state();self.picture('failure-'+identifier.replace('.','-'))
            except Exception:pass
            print('需补核 '+MODE+' '+identifier+': '+str(e),flush=True)
        self.report['checks'].append(row);self.save()
    def load(self,page=None):
        started=time.monotonic();p=self.owner
        if MODE=='standalone':p.goto(BASE+'/original/index.html',wait_until='domcontentloaded');self.page.frame=p
        else:
            p.goto(BASE+'/',wait_until='domcontentloaded');p.wait_for_function('document.querySelector("main")?.dataset.layoutReady==="true"',timeout=60000,polling=100)
            if p.locator('main').get_attribute('data-reading-mode')=='stable':p.locator('article[data-experiment-station=C2]').scroll_into_view_if_needed()
            else:
                p.evaluate('scrollTo({top:(document.documentElement.scrollHeight-innerHeight)*10.05/12.3,behavior:"instant"})')
                p.wait_for_function('Math.abs(Number(document.querySelector("#tour-host").dataset.displayH)-10.05)<.005',timeout=30000,polling=100)
            p.locator('[data-project-tab=live]').click();p.wait_for_selector('.tour-project-embed-mount > iframe',state='attached')
            self.page.frame=p.locator('.tour-project-embed-mount > iframe').element_handle().content_frame()
        f=self.page;f.wait_for_function('window.__LAWSON__?.ready===true',timeout=90000,polling=100)
        f.locator('#loader').wait_for(state='hidden',timeout=20000);assert not f.locator('#fatal').is_visible()
        if MODE=='embedded':p.wait_for_function('document.querySelector(".tour-project-dialog").dataset.embeddedState==="ready"',timeout=15000,polling=100)
        state=f.evaluate('({state:__LAWSON__.api.getState(),stats:__LAWSON__.api.getStats(),camera:__LAWSON__.debugDoor().cam,viewport:[innerWidth,innerHeight],controls:document.querySelectorAll("button,input,.toggle").length})')
        self.report['matchedOriginalViewport']=state['viewport']
        return {'readySeconds':time.monotonic()-started,'stateAtReady':state,'observationsInstalled':f.evaluate(INSTALL)}
    def low(self,page=None):
        p=page or self.page;clicks=[]
        while p.evaluate('__LAWSON__.api.getState().quality')!='low'and len(clicks)<3:
            before=p.evaluate('__LAWSON__.api.getStats()');p.locator('#btn-settings').click();clicks.append({'before':before,'after':p.evaluate('__LAWSON__.api.getStats()')})
        assert p.evaluate('__LAWSON__.api.getState().quality')=='low'
        return {'qualitySelectedWithOriginalUI':clicks,'reason':'cloud software GL functional checks after original default evidence'}
    def state(self,page=None):return (page or self.page).evaluate('__fullpageAudit.state()')
    def observed(self,seconds=1.6,page=None):
        p=page or self.page;begin=p.evaluate('__lawsonAudit.observedCappedSeconds')
        p.wait_for_function('b=>__lawsonAudit.observedCappedSeconds>=b.s+b.d',arg={'s':begin,'d':seconds},timeout=120000,polling=100)
    def picture(self,name,page=None):(page.owner if isinstance(page,Target)else page or self.owner).screenshot(path=str(self.folder/(name+'.png')))
    def last_click(self,selector,page=None):
        p=page or self.page;p.locator(selector).click();return p.evaluate('__fullpageAudit.events.filter(e=>e.kind==="click").at(-1)')
    def finish(self):
        self.report['complete']=bool(self.report['checks'])and all(c['status']!='需补核'for c in self.report['checks'])
        self.report['knownOriginalIssues']=[c['id']for c in self.report['checks']if c['status']=='原页已有问题']
        if MODE=='embedded':
            try:
                n=self.owner.evaluate('__lawsonAudit.draws');self.owner.wait_for_timeout(1100);self.report['hostDrawsWhileOriginalActive']=self.owner.evaluate('__lawsonAudit.draws')-n
                assert self.report['hostDrawsWhileOriginalActive']==0
                self.owner.locator('.tour-project-close').click();self.owner.wait_for_function('document.querySelectorAll(".tour-project-embed-mount > iframe").length===0');self.report['hostClosedAndIframeRemoved']=True
            except Exception as e:self.report['complete']=False;self.report['hostCleanupError']=str(e)
        self.save();self.browser.close();self.pw.stop()
        print(json.dumps({'phase':self.phase,'mode':MODE,'complete':self.report['complete'],'checks':len(self.report['checks']),'knownOriginalIssues':self.report['knownOriginalIssues']},ensure_ascii=False),flush=True)
        if not self.report['complete']:raise SystemExit(1)
