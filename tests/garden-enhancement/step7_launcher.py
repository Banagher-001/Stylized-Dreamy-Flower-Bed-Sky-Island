"""Exercise the actual dependency-free delivery server over local HTTP.
Windows .cmd files are checked statically; Linux Node execution is labelled.
"""
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import hashlib,json,os,queue,shutil,socket,subprocess,tempfile,threading,time
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/evidence/garden-enhancement-step-7'
BUILD=json.loads((OUT/'build-verification.json').read_text());checks=[];responses=[]
def sha(b):return hashlib.sha256(b).hexdigest()
class Server:
    def __init__(self,script,args,cwd):
        self.process=subprocess.Popen(['node',str(script),*args,'--json'],cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        self.lines=[];q=queue.Queue()
        def read():
            for line in self.process.stdout:q.put(line)
        threading.Thread(target=read,daemon=True).start();deadline=time.monotonic()+15
        while time.monotonic()<deadline:
            try:line=q.get(timeout=.2)
            except queue.Empty:
                if self.process.poll()is not None:break
                continue
            self.lines.append(line)
            if line.startswith('SAKAN_PREVIEW_READY '):self.ready=json.loads(line.split(' ',1)[1]);self.url=self.ready['url'];return
        self.close();raise AssertionError('Server did not become ready: '+''.join(self.lines))
    def close(self):
        if self.process.poll()is None:
            self.process.terminate()
            try:self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:self.process.kill();self.process.wait()
    def __enter__(self):return self
    def __exit__(self,*args):self.close()
def request(url,method='GET',headers=None):
    try:r=urlopen(Request(url,method=method,headers=headers or{}),timeout=10)
    except HTTPError as e:r=e
    with r:return r.status,dict(r.headers),r.read()
with tempfile.TemporaryDirectory(prefix='sakan-final-')as tmp:
    folder=Path(tmp)/'中文 空格'/ '成品预览';folder.mkdir(parents=True);shutil.copytree(ROOT/'dist',folder,dirs_exist_ok=True)
    (folder/'scripts').mkdir();shutil.copyfile(ROOT/'scripts/preview-site.mjs',folder/'scripts/preview-site.mjs')
    (folder/'SITE-PACKAGE.txt').write_text('Final static package\n');script=folder/'scripts/preview-site.mjs'
    for base in ['/','/sakan/']:
        with Server(script,['--port','0','--base',base],Path(tmp))as server:
            for name,expected in BUILD['productionSha256'].items():
                relative=name.removeprefix('dist/');status,headers,body=request(server.url+relative)
                assert status==200 and sha(body)==expected,(base,name,status)
                expected_type={'.js':'text/javascript','.css':'text/css','.html':'text/html','.svg':'image/svg+xml','.png':'image/png','.webp':'image/webp','.mp4':'video/mp4'}[Path(name).suffix]
                assert headers['Content-Type'].split(';')[0]==expected_type
                responses.append({'base':base,'path':relative,'status':status,'mime':headers['Content-Type'],'sha256':sha(body),'bytes':len(body)})
            status,headers,body=request(server.url,'HEAD');assert status==200 and not body and int(headers['Content-Length'])>0
            for missing in ['assets/missing.js','assets/missing.webp','missing.html']:
                status,headers,body=request(server.url+missing);assert status==404 and not body
            assert request(server.url,'POST')[0]==405
            assert request(server.url+'%2e%2e%2fpackage.json')[0]==404
            media=next(n for n in BUILD['productionSha256']if n.endswith('.mp4'));raw=(ROOT/media).read_bytes();url=server.url+media.removeprefix('dist/')
            for value,expected in [('bytes=0-31',raw[:32]),('bytes=-16',raw[-16:]),('bytes=15-31',raw[15:32])]:
                status,h,b=request(url,headers={'Range':value});assert status==206 and b==expected and h['Content-Type']=='video/mp4'
            assert request(url,headers={'Range':f'bytes={len(raw)+10}-'})[0]==416
            checks.append({'name':'actual complete site, MIME, HEAD/404, video byte ranges and safe root at'+base,'passed':True,'directory':str(folder),'responses':18})
    occupied=socket.socket();occupied.bind(('127.0.0.1',0));occupied.listen();port=occupied.getsockname()[1]
    try:
        with Server(script,['--port',str(port)],Path(tmp))as server:assert server.ready['url']!=f'http://127.0.0.1:{port}/'
        result=subprocess.run(['node',str(script),'--port',str(port),'--strict-port'],cwd=tmp,text=True,capture_output=True,timeout=10)
        assert result.returncode==1 and '端口' in result.stderr
        assert occupied.getsockname()[1]==port
    finally:occupied.close()
    checks.append({'name':'occupied port chooses another or fails clearly in strict mode; existing service retained','passed':True})
    for extra in [['--dir',str(Path(tmp)/'不存在')],['--port','-1'],['--base','sakan'],['--unknown']]:
        r=subprocess.run(['node',str(script),*extra],cwd=tmp,text=True,capture_output=True,timeout=10);assert r.returncode==1 and '无法启动预览' in r.stderr
    empty=Path(tmp)/'source-empty';(empty/'scripts').mkdir(parents=True);shutil.copyfile(script,empty/'scripts/preview-site.mjs')
    r=subprocess.run(['node',str(empty/'scripts/preview-site.mjs')],cwd=tmp,text=True,capture_output=True,timeout=10)
    assert r.returncode==1 and 'npm.cmd run build' in r.stderr
    checks.append({'name':'missing build/directory and invalid arguments give actionable errors','passed':True})
for name in ['START-PREVIEW.cmd','START-DEV.cmd']:
    body=(ROOT/name).read_bytes();text=body.decode();assert b'\r\n'in body and 'cd /d "%~dp0"'in text and 'where node'in text and 'if errorlevel 1'in text and 'pause'in text
    assert 'ExecutionPolicy'not in text and 'powershell'not in text.lower()
    if name=='START-DEV.cmd':assert 'call npm.cmd ci'in text and 'call npm.cmd run dev'in text
    else:assert 'scripts\\preview-site.mjs'in text and '--open'in text
checks.append({'name':'Windows launchers static CRLF/quoting/npm.cmd/version/error guards; actual Windows execution pending','passed':True,'windowsRuntimeTested':False})
report={'passed':True,'candidateId':BUILD['candidateId'],'checks':checks,'responses':responses,'method':'real child Node process launched from independent Chinese/space directory and unrelated working directory; no npm dependencies installed for static preview; actual local HTTP bytes/ranges/errors; .cmd files static checks only',
    'launcherSha256':{n:sha((ROOT/n).read_bytes())for n in ['scripts/preview-site.mjs','START-PREVIEW.cmd','START-DEV.cmd']},'platform':os.name,'windowsRuntimeTested':False}
(OUT/'launcher-and-http.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('PASS delivery launcher:',len(checks),'groups,36 complete production responses; Chinese/space directory; video seek; port conflict; Windows static only')
