"""Fresh Step4 interaction regression with cloud receivers enabled on Step5.
Reuse the frozen actual-input harness read-only; no historical report is copied.
"""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'tests/garden-enhancement/step4_browser.py'
code=source.read_text().replace('from step4_common import *','from step6_common import *').replace('http://127.0.0.1:4177','http://127.0.0.1:4181')
exec(compile(code,str(source), 'exec'))
path=OUT/f'browser-{args.engine}.json';report=json.loads(path.read_text())
report['freshRegressionSource']={'file':str(source.relative_to(ROOT)),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'adaptations':'output directory, current build identity and localhost4181 only; all original real input/readiness assertions retained; current birds and cloud materials enabled'}
path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
