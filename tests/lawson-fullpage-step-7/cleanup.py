"""Stop only this audit's exact owned services and remove its clean-build copy."""
from pathlib import Path
import json,os,shutil,signal,socket,time
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/evidence/lawson-fullpage-step-7'
read=lambda p:json.loads(p.read_text());ownership=read(OUT/'owned-services.json');results=[]
def argv(pid):
    try:return (Path('/proc')/str(pid)/'cmdline').read_bytes().decode().rstrip('\0').split('\0')
    except FileNotFoundError:return None
def live(pid):
    try:return (Path('/proc')/str(pid)/'stat').read_text().split(') ',1)[1][0]!='Z'
    except FileNotFoundError:return False
for item in ownership['ownedServices']:
    pid=item['pid'];actual=argv(pid)
    if live(pid):assert actual==item['argv'],(pid,actual);os.kill(pid,signal.SIGTERM)
    deadline=time.monotonic()+5
    while live(pid)and time.monotonic()<deadline:time.sleep(.05)
    assert not live(pid),pid;results.append({**item,'stopped':True,'onlyExactOwnedCommandSignalled':True})
temporary=Path(read(OUT/'clean-install-1.json')['temporaryCopy'])
assert temporary.parent==Path('/tmp')and temporary.name.startswith('lawson-step7-clean-')
if temporary.exists():shutil.rmtree(temporary)
assert not temporary.exists()
with socket.socket()as s:s.settimeout(1);portClosed=s.connect_ex(('127.0.0.1',4197))!=0
assert portClosed
remaining=[]
for proc in Path('/proc').iterdir():
    if not proc.name.isdigit()or not live(proc.name):continue
    try:
        env=(proc/'environ').read_bytes().split(b'\0');args=argv(proc.name)
        if b'DISPLAY=:117'in env and args and any(n in Path(args[0]).name.lower()for n in ['chromium','firefox','minibrowser','webkit']):remaining.append({'pid':proc.name,'argv':args})
    except (FileNotFoundError,PermissionError,ProcessLookupError):pass
assert not remaining,remaining
data={'passed':True,'ownedServices':results,'localPortClosed':portClosed,'temporaryCleanInstallCopyRemoved':str(temporary),'remainingLivePrivateDisplayBrowsers':remaining,'sharedProcessesStopped':False,'originalRepositoryModified':False,'committed':False,'pushed':False,'published':False}
(OUT/'cleanup.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'passed':True,'ownedServicesStopped':len(results),'port4197Closed':True,'ownedTemporaryCopyRemoved':True}))
