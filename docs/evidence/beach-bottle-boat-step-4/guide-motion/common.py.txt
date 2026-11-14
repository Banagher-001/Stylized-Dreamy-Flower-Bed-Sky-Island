"""Current step-4 candidate and independent historical seals have separate guards."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[2];SOURCE=ROOT.parent/'Beach-Bottle-Boat';OUT=ROOT/'docs/evidence/beach-bottle-boat-step-4';DOC=ROOT/'docs/beach-bottle-boat';TEST=Path(__file__).parent
ENTRY_SHA='941feb2ea6ddd3cc93aad5b0b92dbca52ee66a3e1098fee0dbf16f01ca63d1ef'
ALLOWED=['src/tour/projectContent.ts','src/tour/createExperimentReader.ts','src/tour/createProjectViewer.ts','src/tour/projectHost.css','src/tour/experiment.css','src/tour/startTourPrototype.ts']
def now():return datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
def read(p):return json.loads(p.read_text())
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def row(p,base=ROOT):return {'path':p.relative_to(base).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)}
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],text=True).strip()
def tree(p,base=ROOT):return[row(f,base)for f in sorted(p.rglob('*'))if f.is_file()and'.git'not in f.parts]
def history():
 first=read(ROOT/'docs/evidence/beach-bottle-boat-step-1/baseline.json');seals=first['oldSeals']+[{'path':'docs/evidence/beach-bottle-boat-step-1/evidence-manifest.json'},{'path':'docs/evidence/beach-bottle-boat-step-3/evidence-manifest.json'}];verified=[]
 for s in seals:
  p=ROOT/s['path'];data=read(p)
  if'sha256'in s:assert sha(p)==s['sha256']
  for f in data['files']:assert row(ROOT/f['path'])==f,f['path']
  verified.append({'path':s['path'],'sha256':sha(p),'filesVerified':len(data['files'])})
 assert tree(SOURCE,SOURCE)==first['originalFiles'];assert git(SOURCE,'status','--short')==''
 return {'seals':verified,'originalFilesVerified':len(first['originalFiles']),'sourceClean':True}
def protect_current():
 b=read(OUT/'baseline.json');h=history();assert h==b['historyBefore'];assert git(ROOT,'rev-parse','HEAD')==b['hostCommit'];assert git(SOURCE,'rev-parse','HEAD')==b['sourceCommit']
 assert tree(ROOT/'dist')==b['existingDistFiles']
 changed=[]
 for f in b['productionInputsBefore']:
  actual=row(ROOT/f['path'])
  if actual!=f:
   assert f['path']in ALLOWED,f['path'];changed.append({'before':f,'after':actual})
 for f in b['otherDocumentsBefore']:assert row(ROOT/f['path'])==f
 tracked=git(ROOT,'diff','--name-only').splitlines();assert set(tracked).issubset(ALLOWED),tracked
 return {'checkedAtShanghai':now(),'history':h,'changedProductionInputs':changed,'unchangedProductionInputs':len(b['productionInputsBefore'])-len(changed),'existingDistFilesUnchanged':len(b['existingDistFiles']),'trackedChanges':tracked}
