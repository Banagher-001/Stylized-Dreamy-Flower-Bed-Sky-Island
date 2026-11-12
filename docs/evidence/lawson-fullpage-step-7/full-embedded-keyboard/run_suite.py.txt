"""Run 3D comparisons serially, preserving every attempt and its output."""
from pathlib import Path
import argparse,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/evidence/lawson-fullpage-step-7'
p=argparse.ArgumentParser();p.add_argument('--prefix',default='full');p.add_argument('--phases',default='controls,supplement,keyboard,targets,traffic');p.add_argument('--modes',default='standalone,embedded');p.add_argument('--skip-completed-standalone-controls',action='store_true');args=p.parse_args()
path=OUT/(args.prefix+'-suite.json');assert not path.exists()
results=[]
for phase in args.phases.split(','):
    for mode in args.modes.split(','):
        if args.skip_completed_standalone_controls and phase=='controls'and mode=='standalone':continue
        run=args.prefix+'-'+mode+'-'+phase;log=OUT/(run+'.log');assert not log.exists()
        env=dict(os.environ,LAWSON_MODE=mode);cmd=[sys.executable,'-u',str(Path(__file__).parent/(phase+'.py')),'--run',run]
        if phase=='traffic':cmd+=['--cars','A,B,C']
        print('START '+run,flush=True);started=time.monotonic()
        with log.open('w')as output:
            child=subprocess.Popen(cmd,env=env,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
            for line in child.stdout:output.write(line);output.flush();print(line,end='',flush=True)
            code=child.wait()
        results.append({'phase':phase,'mode':mode,'run':run,'exitCode':code,'wallSeconds':time.monotonic()-started,'log':log.name})
        path.write_text(json.dumps({'complete':False,'results':results},ensure_ascii=False,indent=2)+'\n')
path.write_text(json.dumps({'complete':True,'allExitCodesZero':all(r['exitCode']==0 for r in results),'results':results},ensure_ascii=False,indent=2)+'\n')
raise SystemExit(0 if all(r['exitCode']==0 for r in results)else 1)
