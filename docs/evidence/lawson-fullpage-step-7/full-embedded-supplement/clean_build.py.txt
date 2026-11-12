"""Verify installation/build in an owned clean copy with the existing lockfile."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,os,shutil,subprocess,tempfile,time
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/evidence/lawson-fullpage-step-7'
p=argparse.ArgumentParser();p.add_argument('--attempt',required=True);args=p.parse_args();report=OUT/(args.attempt+'.json');assert not report.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
baseline=read(OUT/'baseline.json');copy=Path(tempfile.mkdtemp(prefix='lawson-step7-clean-'))
paths=[f['path']for f in baseline['productionInputs']]+['public/experiments/lawson/'+f['path']for f in read(ROOT/baseline['runtimeManifest'])['runtimeFiles']]
for name in paths:
    target=copy/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
data={'startedAtUTC':datetime.now(timezone.utc).isoformat(),'temporaryCopy':str(copy),'productionPathsCopied':len(paths),'originalLockSHA256':sha(ROOT/'package-lock.json'),'commands':[],'passed':False}
def save():report.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
save()
for name,cmd in [('install',['npm','ci','--cache','/workspace/.cache/npm','--no-audit','--no-fund']),('build',['npm','run','build'])]:
    started=time.monotonic();log=OUT/(args.attempt+'-'+name+'.log')
    with log.open('w')as f:
        child=subprocess.Popen(cmd,cwd=copy,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        for line in child.stdout:f.write(line);f.flush();print(line,end='',flush=True)
        code=child.wait()
    data['commands'].append({'cwd':str(copy),'command':cmd,'exitCode':code,'wallSeconds':time.monotonic()-started,'log':log.name});save()
    if code:raise SystemExit(code)
assert sha(copy/'package-lock.json')==data['originalLockSHA256']
expected=read(OUT/'build-result.json')['builtFiles'];actual=[]
for f in expected:
    target=copy/f['path'];assert target.is_file()and sha(target)==f['sha256'],str(target)
    actual.append(f)
data.update(passed=True,lockUnchanged=True,builtFilesExactlyMatchFinalBuild=len(actual),newDependencyVersionsIntroduced=False)
save();print(json.dumps({'cleanInstallAndBuildPassed':True,'matchingBuiltFiles':len(actual)}),flush=True)
