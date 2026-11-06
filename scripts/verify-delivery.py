"""Verify a Step12 ZIP and extract it into a new directory, without repo fixtures."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

parser = argparse.ArgumentParser()
parser.add_argument('--archive', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
parser.add_argument('--report', type=Path, required=True)
args = parser.parse_args()
assert not args.out.exists(), 'Choose a new empty extraction path.'
with zipfile.ZipFile(args.archive) as z:
    names = z.namelist()
    assert len(names) == len(set(names)) and z.testzip() is None
    for name in names:
        assert not name.startswith('/') and '..' not in Path(name).parts and '\\' not in name
    manifest = json.loads(z.read('PACKAGE-MANIFEST.json'))
    assert set(names) == set(manifest['files']) | {'PACKAGE-MANIFEST.json'}
    for name, meta in manifest['files'].items():
        body = z.read(name)
        assert len(body) == meta['bytes'] and hashlib.sha256(body).hexdigest() == meta['sha256'], name
    z.extractall(args.out)
for name, meta in manifest['files'].items():
    body = (args.out / name).read_bytes()
    assert len(body) == meta['bytes'] and hashlib.sha256(body).hexdigest() == meta['sha256'], name
report = {'passed': True, 'kind': manifest['kind'], 'candidateId': manifest['candidateId'],
    'archive': str(args.archive.resolve()), 'archiveSha256': hashlib.sha256(args.archive.read_bytes()).hexdigest(),
    'archiveBytes': args.archive.stat().st_size, 'filesIncludingManifest': len(names),
    'allEntryCRCAndSha256Verified': True, 'extractedFileSha256Verified': True, 'extraction': str(args.out.resolve())}
args.report.parent.mkdir(parents=True, exist_ok=True)
args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print('PASS', manifest['kind'], len(names), 'entries; CRC + SHA256 + independent extraction')
