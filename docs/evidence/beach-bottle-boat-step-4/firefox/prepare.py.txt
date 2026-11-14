"""Capture the authorized before candidate, retaining all original deliveries."""
import shutil,tempfile
from common import *
assert not OUT.exists();h=history();first=read(ROOT/'docs/evidence/beach-bottle-boat-step-1/baseline.json')
for f in first['hostProductionInputs']:assert row(ROOT/f['path'])==f
OUT.mkdir(parents=True);standard=DOC/'step-4-standard.md';shutil.copyfile(standard,OUT/'standard-before.md')
for name in ALLOWED:
 dest=OUT/'before'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,dest)
write(OUT/'baseline.json',{'capturedAtShanghai':now(),'hostCommit':git(ROOT,'rev-parse','HEAD'),'sourceCommit':git(SOURCE,'rev-parse','HEAD'),'hostStatusBefore':git(ROOT,'status','--short'),'historyBefore':h,'productionInputsBefore':first['hostProductionInputs'],'existingDistFiles':tree(ROOT/'dist'),'otherDocumentsBefore':[row(p)for p in sorted(DOC.glob('*'))if p.is_file()and p!=standard],'allowedProductFiles':ALLOWED,'scratch':tempfile.mkdtemp(prefix='bottle-ocean-step-4-',dir='/tmp'),'step2Executed':False})
print(json.dumps({'beforeCaptured':True,'historicalSealsVerified':len(h['seals']),'productionInputsPinned':len(first['hostProductionInputs']),'authorizedFiles':len(ALLOWED)},ensure_ascii=False))
