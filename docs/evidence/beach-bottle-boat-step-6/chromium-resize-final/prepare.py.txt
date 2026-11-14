"""Capture the current uncommitted candidate before any step-6 product edits."""
import shutil,tempfile
from common import *
assert not OUT.exists();h=history();candidate=read(ROOT/'docs/evidence/beach-bottle-boat-step-5/candidate-manifest.json')
for f in candidate['productionInputsAfter']:assert row(ROOT/f['path'])==f,f['path']
OUT.mkdir(parents=True);standard=DOC/'step-6-standard.md';shutil.copyfile(standard,OUT/'standard-before.md')
for name in ALLOWED:
 dest=OUT/'before'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,dest)
write(OUT/'baseline.json',{'capturedAtShanghai':now(),'hostCommit':git(ROOT,'rev-parse','HEAD'),'sourceCommit':git(SOURCE,'rev-parse','HEAD'),'hostStatusBefore':git(ROOT,'status','--short'),'trackedChangedBefore':git(ROOT,'diff','--name-only').splitlines(),'historyBefore':h,'productionInputsBefore':candidate['productionInputsAfter'],'existingDistFiles':tree(ROOT/'dist'),'otherDocumentsBefore':[row(p)for p in sorted(DOC.glob('*'))if p.is_file()and p!=standard],'allowedProductFiles':ALLOWED,'scratch':tempfile.mkdtemp(prefix='bottle-ocean-step-6-',dir='/tmp'),'step2Executed':False})
standard.write_text(standard.read_text().replace('状态：已细化，尚未执行。本轮只新增本标准，不修改产品代码、不启动测试服务、不上传或发布。日期：2026-11-13（Asia/Shanghai）。','状态：执行中。用户已授权第六步；执行前标准另存本步 standard-before.md。执行日期：2026-11-14（Asia/Shanghai）。本步不上传或发布。'))
print(json.dumps({'beforeCaptured':True,'productionInputs':len(candidate['productionInputsAfter']),'historicalSeals':len(h['seals']),'originalFiles':h['originalFilesVerified']},ensure_ascii=False))
