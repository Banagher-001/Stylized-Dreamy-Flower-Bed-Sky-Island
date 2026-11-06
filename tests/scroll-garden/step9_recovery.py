"""Same real native visibility/context assertions, current pool and separate receipts."""
from pathlib import Path
source=(Path(__file__).with_name('step7_recovery.py')).read_text().replace('docs/evidence/scroll-garden-step-7','docs/evidence/scroll-garden-step-9').replace('step7-native-','step9-native-').replace('STEP 07','STEP 09')
exec(compile(source,'<Step9 native recovery>','exec'),globals())
