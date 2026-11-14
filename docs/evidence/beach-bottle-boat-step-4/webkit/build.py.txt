"""Build to an owned directory and save the authorized candidate and exact diff."""
import shutil,time
from common import *
assert not(OUT/'build.json').exists();build=Path(read(OUT/'baseline.json')['scratch'])/'production';assert not build.exists();start=now();t=time.monotonic();argv=['npm','run','build','--','--outDir',str(build)]
with(OUT/'build.log').open('w')as log:r=subprocess.run(argv,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
data={'startedAtShanghai':start,'argv':argv,'exitCode':r.returncode,'wallSeconds':time.monotonic()-t,'buildRoot':str(build)};write(OUT/'build.json',data);assert r.returncode==0
assert sha(build/'experiments/bottle-ocean/index.html')==ENTRY_SHA
for name in['THIRD_PARTY_NOTICES.md','SOURCE.md']:assert sha(build/'experiments/bottle-ocean'/name)==sha(ROOT/'public/experiments/bottle-ocean'/name)
cover=ROOT/'src/assets/bottle-ocean-cover.png';emitted=[p for p in(build/'assets').glob('bottle-ocean-cover-*.png')];assert len(emitted)==1 and sha(emitted[0])==sha(cover)
data.update({'productionManifest':tree(build,build),'cover':row(emitted[0],build),'protection':protect_current()});write(OUT/'build.json',data)
for name in ALLOWED:
 dest=OUT/'after'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,dest)
(OUT/'product.diff').write_text(subprocess.check_output(['git','diff','--',*ALLOWED],cwd=ROOT,text=True))
print(json.dumps({'built':True,'coverEmitted':emitted[0].name,'changedProductInputs':len(data['protection']['changedProductionInputs']),'historicalSealsVerified':len(data['protection']['history']['seals'])},ensure_ascii=False))
