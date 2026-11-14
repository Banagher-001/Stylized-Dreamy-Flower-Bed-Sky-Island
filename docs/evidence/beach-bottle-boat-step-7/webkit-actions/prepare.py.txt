"""Pin the actual Stage-6 working tree, without replaying older changes."""
import shutil,tempfile
from common import *
assert not OUT.exists();h=history();candidate=read(ROOT/'docs/evidence/beach-bottle-boat-step-6/candidate-manifest.json')
for f in candidate['productionInputsAfter']:assert row(ROOT/f['path'])==f,f['path']
OUT.mkdir(parents=True);standard=DOC/'step-7-standard.md';shutil.copyfile(standard,OUT/'standard-before.md')
for name in ALLOWED:
 dest=OUT/'before'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,dest)
support=list((ROOT/'scripts').glob('*.mjs'))+list(ROOT.glob('START*.cmd'))+[ROOT/'.nvmrc']
write(OUT/'baseline.json',{'capturedAtShanghai':now(),'hostCommit':git(ROOT,'rev-parse','HEAD'),'sourceCommit':git(SOURCE,'rev-parse','HEAD'),'hostStatusBefore':git(ROOT,'status','--short'),'trackedChangedBefore':git(ROOT,'diff','--name-only').splitlines(),'historyBefore':h,'productionInputsBefore':candidate['productionInputsAfter'],'existingDistFiles':tree(ROOT/'dist'),'otherDocumentsBefore':[row(p)for p in sorted(DOC.glob('*'))if p.is_file()and p!=standard],'supportFilesBefore':[row(p)for p in sorted(set(support))],'allowedProductFiles':ALLOWED,'scratch':tempfile.mkdtemp(prefix='bottle-ocean-step-7-',dir='/tmp'),'deliveryParent':'/workspace/deliverables/beach-bottle-boat-step-7','stage2Executed':False})
t=standard.read_text();a=t.index('状态：');z=t.index('\n',a);standard.write_text(t[:a]+'状态：执行中。用户已授权第七步；执行前标准另存本步 standard-before.md。日期：2026-11-14（Asia/Shanghai）。不上传或发布。'+t[z:])
print(json.dumps({'beforeCaptured':True,'productionInputs':len(candidate['productionInputsAfter']),'historicalSeals':len(h['seals']),'originalFiles':h['originalFilesVerified']},ensure_ascii=False))
