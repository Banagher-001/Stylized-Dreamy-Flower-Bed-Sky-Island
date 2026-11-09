"""Actual complete GPU/reference regression with diagnostic birds=off.
Frozen prior assertions reused read-only; no old evidence is rewritten.
"""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2];source=ROOT/'tests/garden-enhancement/step4_scope.py'
code=source.read_text().replace('from step4_common import *','from step6_common import *').replace('4176','4180').replace('4177','4181')
code=code.replace('/?waterTime=2','/?waterTime=2&birds=off').replace('scene-and-background-protection.json','birds-off-protection.json')
exec(compile(code,str(source),'exec'))
path=OUT/'birds-off-protection.json';report=json.loads(path.read_text())
report['birds']='off for current tour; old reference is default unchanged'
report['freshSource']={'file':str(source.relative_to(ROOT)),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'adaptations':'current output/build, ports4180/4181 and birds=off only; full-canvas exact assertions unchanged'}
path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
