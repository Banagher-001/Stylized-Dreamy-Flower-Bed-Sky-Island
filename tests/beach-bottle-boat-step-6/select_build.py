"""Select a preserved local build for causal before/after browser verification."""
import argparse,os
from common import *
parser=argparse.ArgumentParser();parser.add_argument('run');args=parser.parse_args();assert args.run.replace('-','').isalnum()
info=read(OUT/('build-'+args.run+'.json'));scratch=Path(read(OUT/'baseline.json')['scratch']);target=Path(info['buildRoot']);assert target.parent==scratch and tree(target,target)==info['productionManifest']
pending=scratch/'next-current';assert not pending.exists();pending.symlink_to(target);os.replace(pending,scratch/'current');record={'run':args.run,'record':'build-'+args.run+'.json','buildRoot':str(target),'switchedAtShanghai':now()};write(OUT/'active-build.json',record)
with(OUT/'build-selections.jsonl').open('a')as f:f.write(json.dumps(record)+'\n')
print(json.dumps({'selectedOwnedBuild':args.run,'productSourcesChanged':False},ensure_ascii=False))
