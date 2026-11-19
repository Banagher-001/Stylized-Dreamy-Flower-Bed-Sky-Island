"""Same-build pairs for independent scenes and the in-place production window."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import sys
import traceback
from contextlib import suppress
from urllib.parse import urlsplit

from playwright.sync_api import Error, sync_playwright

TESTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TESTS / 'about-refresh-final'))
from support import now, save


DESKTOP = (1440, 900)
PHONE = (390, 844)
LANDSCAPE = (844, 390)
CHILD = {DESKTOP: (1198, 559), PHONE: (337, 473), LANDSCAPE: (779, 380)}
STAGE = '.experiment-window-stage'
IFRAME = STAGE + ' iframe'
LAWSON = 'lawson'
BOTTLE = 'bottle-ocean'


def literal(path, name):
    """Reuse the diagnostic probes without running the historical journeys."""
    tree = ast.parse((TESTS / path).read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise KeyError((path, name))


def arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--origin', required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--env-file', type=Path, required=True)
    parser.add_argument('--build-record', type=Path, required=True)
    parser.add_argument('--only', nargs='*')
    return parser.parse_args()


def position(page):
    return page.evaluate('''() => {
      const host=document.querySelector('#tour-host');
      return {url:location.href,y:scrollY,h:host?.dataset.displayH,camera:host?.dataset.cameraTarget,
        frames:document.querySelectorAll('iframe').length,dialogs:document.querySelectorAll('dialog[open]').length};
    }''')


def ready_main(page, origin):
    page.goto(origin, wait_until='domcontentloaded')
    page.wait_for_function('document.querySelector("main")?.dataset.layoutReady==="true" && document.querySelector("#tour-host")?.dataset.renderState==="ready"', timeout=90000, polling=100)


def visit_window(page):
    if page.locator('main').get_attribute('data-reading-mode') == 'stable':
        page.locator('article[data-experiment-station=C2]').evaluate('''article => scrollBy({
          top:article.getBoundingClientRect().top-document.querySelector('.tour-header').getBoundingClientRect().bottom-16,
          behavior:'instant'
        })''')
    else:
        delta = page.evaluate('10.05/12.3*(document.documentElement.scrollHeight-innerHeight)-scrollY')
        page.mouse.move(23,300)
        if abs(delta) >= 1:
            page.mouse.wheel(0,delta)
        page.wait_for_function('''() => {
          const h=document.querySelector('#tour-host');
          return Math.abs(Number(h.dataset.displayH)-10.05)<.006 && h.dataset.cameraState==='settled';
        }''', polling=100, timeout=45000)


def wait_child(page, project):
    item = page.locator(f'{IFRAME}[src$="/experiments/{project}/index.html"]')
    item.wait_for(state='visible', timeout=120000)
    assert page.locator(STAGE).get_attribute('data-scene-state') == 'ready'
    assert page.locator('iframe').count() == 1 and not page.locator('dialog[open]').count()
    return item.element_handle().content_frame()


def wait_original(surface, project):
    api = 'window.__LAWSON__' if project == LAWSON else 'window.__bottleOcean'
    surface.wait_for_function(f'{api}?.ready===true', timeout=120000, polling=100)
    surface.locator('#loader').wait_for(state='hidden', timeout=45000)
    if project == LAWSON:
        assert surface.locator('#fatal').is_hidden()
    else:
        assert not surface.evaluate('window.__bottleError||document.querySelector("#loader-error").textContent.trim()')


class BrowserRun:
    def __init__(self, headed=False):
        self.args = arguments()
        self.out = self.args.out.resolve()
        self.out.mkdir(parents=True, exist_ok=False)
        self.origin = self.args.origin.rstrip('/') + '/'
        self.environment = json.loads(self.args.env_file.read_text())['browserEnvironment']
        os.environ.update(self.environment)
        self.build = json.loads(self.args.build_record.read_text())
        self.hashes = {item['path']:item['sha256'] for item in self.build['production']}
        self.pw = sync_playwright().start()
        self.browser = self.pw.chromium.launch(executable_path='/usr/bin/chromium', headless=not headed,
            args=['--no-sandbox','--use-gl=angle','--use-angle=gl','--ignore-gpu-blocklist','--window-size=1652,1030'])
        self.report = {'candidateId':self.build['candidateId'], 'runtimeInputDigest':self.build['runtimeInputDigest'],
                       'browserVersion':self.browser.version,'headed':headed,'engine':'chromium', 'clockModified':False,
                       'physicalDevice':False,'origin':self.origin,'startedAtShanghai':now(),'checks':[],'complete':False}

    def selected(self, name):
        return not self.args.only or name in self.args.only

    def context(self, size, touch=False, dpr=1, probe=None):
        context = self.browser.new_context(viewport={'width':size[0],'height':size[1]}, device_scale_factor=dpr,
            has_touch=touch, is_mobile=touch, service_workers='block', accept_downloads=True)
        if probe:
            context.add_init_script(probe)
        page = context.new_page()
        page.set_default_timeout(60000)
        allowed = urlsplit(self.origin).netloc
        events = {'external':[],'errors':[],'unexpectedHttp':[],'failures':[]}

        def local(route):
            request = route.request
            if request.url.startswith(('http:','https:')) and urlsplit(request.url).netloc != allowed:
                events['external'].append(request.url)
                route.abort('blockedbyclient')
            else:
                route.continue_()

        context.route('**/*', local)
        page.on('pageerror',lambda e:events['errors'].append(str(e)))
        page.on('console',lambda e:events['errors'].append(e.text) if e.type=='error' else None)
        page.on('response',lambda e:events['unexpectedHttp'].append([e.status,e.url]) if e.status>=400 else None)
        page.on('requestfailed',lambda e:events['failures'].append([e.failure,e.url]))
        return context, page, events

    def open(self, page, project, embedded, touch=False):
        entry=f'experiments/{project}/index.html'
        if embedded:
            ready_main(page,self.origin)
            # Park the host environment through its own control to give both originals comparable GL time.
            if page.locator('#tour-motion').is_visible() and page.locator('#tour-motion').inner_text()=='暂停环境':
                (page.locator('#tour-motion').tap if touch else page.locator('#tour-motion').click)()
            visit_window(page)
            tab=page.locator(f'[data-project-select={project}]')
            if tab.get_attribute('aria-selected')!='true':
                (tab.tap if touch else tab.click)()
            surface=wait_child(page,project)
        else:
            page.goto(self.origin+entry,wait_until='domcontentloaded')
            surface=page
        wait_original(surface,project)
        assert surface.url==self.origin+entry
        response=page.request.get(surface.url)
        digest=hashlib.sha256(response.body()).hexdigest()
        assert response.ok and digest==self.hashes[entry]
        conditions=surface.evaluate('() => ({viewport:[innerWidth,innerHeight],dpr:devicePixelRatio,clock:performance.timeOrigin})')
        conditions['sourceSHA256']=digest
        return surface, conditions

    def record(self, name, fn):
        if not self.selected(name):
            return
        row={'id':name,'status':'需复核'}
        try:
            row.update(status='通过', results=fn())
        except Exception as e:
            row.update(status='需复核',error=str(e),traceback=traceback.format_exc())
        self.report['checks'].append(row)
        save(self.out/'browser.json',self.report)
        print(name,row['status'],row.get('error','')[:300],flush=True)

    def pairs(self, name, project, action, host=DESKTOP, *, touch=False, dpr=1, probe=None):
        def execute():
            sides={}
            for embedded in (False,True):
                side='embedded' if embedded else 'reference'
                context,page,events=self.context(host if embedded else CHILD[host],touch,dpr,probe)
                try:
                    surface,conditions=self.open(page,project,embedded,touch)
                    assert conditions['viewport']==list(CHILD[host]) and conditions['dpr']==dpr,conditions
                    data=action(page,surface,side)
                    assert not (events['external'] or events['errors'] or events['unexpectedHttp']),events
                    assert all(error=='net::ERR_ABORTED' for error,_ in events['failures']),events
                    sides[side]={'conditions':conditions,'observations':data,'network':events}
                    save(self.out/f'{name}-{side}.json',sides[side])
                    print(name,side,'captured',flush=True)
                except Exception:
                    if not page.is_closed():
                        with suppress(Error):
                            page.screenshot(path=str(self.out/f'{name}-{side}-failure.png'),timeout=12000)
                    raise
                finally:
                    context.close()
            assert sides['reference']['observations']['comparison']==sides['embedded']['observations']['comparison'],name
            return sides
        self.record(name,execute)

    def finish(self):
        self.browser.close()
        self.pw.stop()
        self.report.update(finishedAtShanghai=now(),browserClosed=True,
            complete=bool(self.report['checks']) and all(c['status']=='通过' for c in self.report['checks']))
        save(self.out/'browser.json',self.report)
        return self.report['complete']
