"""Re-run frozen Step11 contracts against Step12's actual default entrance.

Only the output directory, entrance URL and test-server port are adapted.
Historical evidence is never overwritten. This suite needs the sibling Step11
test helpers, all included in the source archive; no historical screenshots.
"""
import argparse
import sys
from pathlib import Path
import step11_common

parser = argparse.ArgumentParser()
parser.add_argument('--suite', choices=['browser', 'dialogs', 'renderer', 'faults', 'record'], default='browser')
parser.add_argument('--engine', default='chromium', choices=['chromium', 'firefox', 'webkit'])
parser.add_argument('--url', default='http://127.0.0.1:4175')
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
step11_common.OUT = args.out.resolve()
step11_common.OUT.mkdir(parents=True, exist_ok=True)
script = Path(__file__).with_name(f'step11_{args.suite}.py')
code = script.read_text().replace('?tour=prototype&', '?')
code = code.replace('http://127.0.0.1:4173', args.url.rstrip('/'))
sys.argv = [str(script)]
if args.suite in ['browser', 'dialogs', 'renderer']:
    sys.argv += ['--engine', args.engine]
if args.suite in ['browser', 'dialogs']:
    sys.argv += ['--url', args.url.rstrip('/')]
exec(compile(code, str(script), 'exec'), {'__file__': str(script), '__name__': '__main__'})
