"""Build the host to a new owned directory; check original HTML survives unchanged."""
import shutil,time
from common import *
assert not(OUT/'build.json').exists()
before=read(OUT/'baseline.json');build=Path(before['scratch'])/'production';assert not build.exists()
argv=['npm','run','build','--','--outDir',str(build)];started=time.monotonic()
with(OUT/'build.log').open('w')as log:result=subprocess.run(argv,cwd=ROOT,text=True,stdout=log,stderr=subprocess.STDOUT)
data={'startedAtShanghai':now(),'argv':argv,'exitCode':result.returncode,'wallSeconds':time.monotonic()-started,'buildRoot':str(build),'existingDistNotUsed':True}
write(OUT/'build.json',data)
assert result.returncode==0,'Host build failed; retain build.log'
files=[]
for name in['index.html','THIRD_PARTY_NOTICES.md','SOURCE.md']:
 src=RUNTIME/name;dest=build/'experiments/bottle-ocean'/name;assert sha(src)==sha(dest)
 files.append({'name':name,'public':row(src),'production':row(dest,build),'origin':row(SOURCE/name,SOURCE)if name!='SOURCE.md'else None})
assert sha(build/'experiments/bottle-ocean/index.html')==ENTRY_SHA
data['runtimeFiles']=files;data['productionManifest']=[row(p,build)for p in sorted(build.rglob('*'))if p.is_file()]
data['protectionAfterBuild']=protect_current();write(OUT/'build.json',data)
print(json.dumps({'built':True,'runtimeFilesIdentical':len(files),'productionFiles':len(data['productionManifest']),'wallSeconds':data['wallSeconds']},ensure_ascii=False))
