"""Pin the uncommitted step-4 candidate before adding its embedded runtime."""
import shutil,tempfile
from common import *
assert not OUT.exists();h=history();candidate=read(ROOT/'docs/evidence/beach-bottle-boat-step-4/candidate-manifest.json')
for f in candidate['productionInputsAfter']:assert row(ROOT/f['path'])==f
OUT.mkdir(parents=True);standard=DOC/'step-5-standard.md';shutil.copyfile(standard,OUT/'standard-before.md')
for name in ALLOWED:
 p=ROOT/name
 if p.exists():
  dest=OUT/'before'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
write(OUT/'baseline.json',{'capturedAtShanghai':now(),'hostCommit':git(ROOT,'rev-parse','HEAD'),'sourceCommit':git(SOURCE,'rev-parse','HEAD'),'hostStatusBefore':git(ROOT,'status','--short'),'trackedChangedBefore':git(ROOT,'diff','--name-only').splitlines(),'historyBefore':h,'productionInputsBefore':candidate['productionInputsAfter'],'existingDistFiles':tree(ROOT/'dist'),'otherDocumentsBefore':[row(p)for p in sorted(DOC.glob('*'))if p.is_file()and p!=standard],'allowedProductFiles':ALLOWED,'newProductFiles':[n for n in ALLOWED if not(ROOT/n).exists()],'scratch':tempfile.mkdtemp(prefix='bottle-ocean-step-5-',dir='/tmp'),'step2Executed':False})
print(json.dumps({'beforeCaptured':True,'historicalSeals':len(h['seals']),'currentProductionInputsPinned':len(candidate['productionInputsAfter']),'previousChangesPreserved':True},ensure_ascii=False))
