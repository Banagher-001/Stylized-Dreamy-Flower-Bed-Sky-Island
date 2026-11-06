"""Actual previous fallback/media assertions on the current pool, with new evidence."""
from pathlib import Path
source=(Path(__file__).with_name('step7_fallback.py')).read_text()
source=source.replace('from step7_common import *',"from step7_common import *\nimport step7_common as shared\nshared.OUT=ROOT/'docs/evidence/scroll-garden-step-10/fallback';shared.OUT.mkdir(parents=True,exist_ok=True);OUT=shared.OUT")
source=source.replace('courtyard-interactive-cover','courtyard-orb-cover')
exec(compile(source,'<Step10 fallback>','exec'),globals())
