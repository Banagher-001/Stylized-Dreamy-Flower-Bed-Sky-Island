"""Fresh Step3 run of the native CDP lifecycle contracts, with isolated outputs.

The transport performs real Target.activateTarget and WEBGL_lose_context calls;
it never assigns document.hidden or dispatches synthetic visibility events.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tests/scroll-garden'))
source = (ROOT / 'tests/scroll-garden/step11_recovery.py').read_text()
source = source.replace("source=Path(__file__).with_name('step7_recovery.py').read_text()", "source=(ROOT/'tests/scroll-garden/step7_recovery.py').read_text()")
source = source.replace("'docs/evidence/scroll-garden-step-11'", "'docs/evidence/garden-enhancement-step-3'")
source = source.replace("'step11-native-'", "'garden-step3-native-'")
source = source.replace('prefix=prefix.replace(', "prefix=prefix.replace('127.0.0.1:4173','127.0.0.1:4177')\nprefix=prefix.replace(", 1)
source = source.replace("assert 'STEP 07'", "assert '张辰翰'")
exec(compile(source, '<fresh Step3 lifecycle contracts>', 'exec'), globals())
