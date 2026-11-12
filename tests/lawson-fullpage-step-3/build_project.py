"""Run the existing build once and preserve its actual result."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import argparse,json,subprocess,time
from runtime_files import manifest,verify,PUBLIC
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/evidence/lawson-fullpage-step-3'
parser=argparse.ArgumentParser();parser.add_argument('--run',default='build-1');args=parser.parse_args()
assert (OUT/'copy-verification.json').is_file(),'Migration must complete before the accepted build'
verify(PUBLIC,manifest())
result_path=OUT/(args.run+'-result.json');log_path=OUT/(args.run+'.log')
assert not result_path.exists() and not log_path.exists(),'Keep previous build evidence'
start=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat();clock=time.monotonic()
with log_path.open('w')as log:
    result=subprocess.run(['npm','run','build'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
record={'command':['npm','run','build'],'startedAtShanghai':start,'finishedAtShanghai':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'wallSeconds':time.monotonic()-clock,'exitCode':result.returncode,'typecheckIncluded':True,'packageOrConfigModified':False}
record['publicVerifiedBeforeBuild']=True
result_path.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(record,ensure_ascii=False));raise SystemExit(result.returncode)
