"""Build each candidate separately; switch only the owned server's build symlink."""
import argparse,os,shutil,time
from common import *
parser=argparse.ArgumentParser();parser.add_argument('--run',required=True);args=parser.parse_args();assert args.run.replace('-','').isalnum()
record=OUT/('build-'+args.run+'.json');assert not record.exists();scratch=Path(read(OUT/'baseline.json')['scratch']);build=scratch/('production-'+args.run);assert not build.exists();start=now();t=time.monotonic();argv=['npm','run','build','--','--outDir',str(build)]
with(OUT/('build-'+args.run+'.log')).open('w')as log:r=subprocess.run(argv,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
data={'startedAtShanghai':start,'argv':argv,'exitCode':r.returncode,'wallSeconds':time.monotonic()-t,'buildRoot':str(build)};write(record,data);assert r.returncode==0
assert sha(build/'experiments/bottle-ocean/index.html')==ENTRY_SHA
emitted=list((build/'assets').glob('bottle-ocean-cover-*.png'));assert len(emitted)==1 and sha(emitted[0])==sha(ROOT/'src/assets/bottle-ocean-cover.png')
data.update({'productionManifest':tree(build,build),'cover':row(emitted[0],build),'protection':protect_current(),'productionInputs':[row(ROOT/f['path'])for f in read(OUT/'baseline.json')['productionInputsBefore']]});write(record,data)
snap=OUT/('build-'+args.run+'-sources')
for name in ALLOWED:
 dest=snap/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,dest)
pending=scratch/'next-current';pending.symlink_to(build);os.replace(pending,scratch/'current');write(OUT/'active-build.json',{'run':args.run,'record':record.name,'buildRoot':str(build),'switchedAtShanghai':now()})
print(json.dumps({'built':True,'run':args.run,'files':len(data['productionManifest']),'changedProductInputs':len(data['protection']['changedProductionInputs'])},ensure_ascii=False))
