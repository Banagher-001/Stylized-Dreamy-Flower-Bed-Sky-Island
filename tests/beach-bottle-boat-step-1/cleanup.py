"""Stop only the two services whose PID, argv and start time were pinned."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json,os,signal,time
OUT=Path(__file__).resolve().parents[2]/'docs/evidence/beach-bottle-boat-step-1';target=OUT/'services-cleanup.json';assert not target.exists()
def identity(pid):
 p=Path('/proc')/str(pid)
 if not p.exists():return None
 try:
  fields=p.joinpath('stat').read_text().split(') ')[1].split();return {'pid':pid,'argv':p.joinpath('cmdline').read_bytes().decode().strip('\0').split('\0'),'startTicks':fields[19],'state':fields[0]}
 except FileNotFoundError:return None
remaining=[];scanErrors=[]
for path in Path('/proc').iterdir():
 if not path.name.isdigit():continue
 pid=int(path.name)
 try:
  args=path.joinpath('cmdline').read_bytes().decode(errors='replace');candidate=any(v in args for v in['/usr/lib/chromium/','/usr/bin/chromium','/firefox-','/webkit-','WebKitWebProcess','WebKitNetworkProcess','playwright/driver'])
  if not candidate:continue
  env=path.joinpath('environ').read_bytes().split(b'\0');state=identity(pid)
  if b'DISPLAY=:121'in env and state and state['state']!='Z':remaining.append(state)
 except FileNotFoundError:pass
 except PermissionError:scanErrors.append(pid)
assert not remaining,remaining
rows=[]
for old in json.loads((OUT/'services-started.json').read_text())['ownedServices']:
 now=identity(old['pid']);assert now and all(now[k]==old[k]for k in['pid','argv','startTicks']),{'expected':old,'actual':now};os.kill(old['pid'],signal.SIGTERM)
 deadline=time.monotonic()+8
 while time.monotonic()<deadline:
  after=identity(old['pid'])
  if not after or after['state']=='Z':break
  time.sleep(.1)
 assert not after or after['state']=='Z',after;rows.append({'identityVerifiedBeforeStop':old,'signal':'SIGTERM','stopped':True,'after':after})
result={'capturedAtShanghai':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'ownedBrowsersRemaining':remaining,'scanPermissionErrorsForUnrelatedProcesses':scanErrors,'services':rows,'otherServicesStopped':False};target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'ownedBrowsersRemaining':len(remaining),'ownedServicesStopped':len(rows)},ensure_ascii=False))
