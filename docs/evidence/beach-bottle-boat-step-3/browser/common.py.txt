"""Step-3 paths and read-only integrity checks. Never write step-1 evidence."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT.parent/'Beach-Bottle-Boat'
OUT=ROOT/'docs/evidence/beach-bottle-boat-step-3'
DOC=ROOT/'docs/beach-bottle-boat'
TEST=Path(__file__).parent
RUNTIME=ROOT/'public/experiments/bottle-ocean'
COVER=ROOT/'src/assets/bottle-ocean-cover.png'
ENTRY_SHA='941feb2ea6ddd3cc93aad5b0b92dbca52ee66a3e1098fee0dbf16f01ca63d1ef'
COVER_SOURCE=ROOT/'docs/evidence/beach-bottle-boat-step-1/interactions/export-1920x1080-ui-visible.png'
def now():return datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,data):p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def git(p,*args):return subprocess.check_output(['git','-C',str(p),*args],text=True).strip()
def row(p,base=ROOT):return {'path':p.relative_to(base).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)}
def tree(path):return [row(p)for p in sorted(path.rglob('*'))if p.is_file()]
def verify_history():
 data=json.loads(subprocess.run(['python','tests/beach-bottle-boat-step-1/finalize.py','--verify-only'],cwd=ROOT,text=True,capture_output=True,check=True).stdout)
 assert data['verifiedNewFiles']==253
 return data
def protect_current():
 before=read(OUT/'baseline.json');history=verify_history()
 assert git(ROOT,'rev-parse','HEAD')==before['hostCommit']
 assert git(SOURCE,'rev-parse','HEAD')==before['sourceCommit']
 assert tree(ROOT/'dist')==before['existingDistFiles']
 for f in before['otherExistingDocuments']:assert row(ROOT/f['path'])==f,f['path']
 return {'checkedAtShanghai':now(),'history':history,'existingDistFilesUnchanged':len(before['existingDistFiles']),'otherExistingDocumentsUnchanged':len(before['otherExistingDocuments']),'hostCommitUnchanged':True,'sourceCommitUnchanged':True}
