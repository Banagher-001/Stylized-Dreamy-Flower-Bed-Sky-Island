"""Actual complete GPU/reference regression with diagnostic clouds=off.
Frozen prior assertions reused read-only; no old evidence is rewritten.
"""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2];source=ROOT/'tests/garden-enhancement/step4_scope.py'
code=source.read_text().replace('from step4_common import *','from step5_common import *').replace('4176','4178').replace('4177','4179')
code=code.replace('/?waterTime=2','/?waterTime=2&clouds=off').replace('scene-and-background-protection.json','cloud-off-protection.json')
exec(compile(code,str(source),'exec'))
path=OUT/'cloud-off-protection.json';report=json.loads(path.read_text())
report['clouds']='off for current tour; old reference is default unchanged'
report['freshSource']={'file':str(source.relative_to(ROOT)),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'adaptations':'current output/build, ports4178/4179 and clouds=off only; full-canvas exact assertions unchanged'}
path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
