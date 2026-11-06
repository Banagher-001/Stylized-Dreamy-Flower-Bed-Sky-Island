"""Same real native visibility/context assertions, current pool and separate receipts."""
from pathlib import Path
source=(Path(__file__).with_name('step7_recovery.py')).read_text().replace('docs/evidence/scroll-garden-step-7','docs/evidence/scroll-garden-step-8').replace('step7-native-','step8-native-').replace('STEP 07','STEP 08')
exec(compile(source,'<Step8 native recovery>','exec'),globals())
