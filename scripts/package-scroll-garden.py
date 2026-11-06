"""Create local Step12 archives; never commit, push or deploy anything.

Requires a verified production build and finalized handoff documents. Re-running
replaces only scroll-garden-step12-* archives. Final unzip reports and summary
remain outside the evidence ZIP to avoid archive/hash cycles.
"""
from pathlib import Path
import hashlib
import json
import zipfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/evidence/scroll-garden-step-12'
RELEASE = ROOT / 'release'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def encoded(data):
    return (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode()

def archive(kind, files, candidate):
    assert files and 'PACKAGE-MANIFEST.json' not in files
    for name in files:
        assert not name.startswith('/') and '..' not in Path(name).parts
    manifest = {'schema': 1, 'kind': kind, 'candidateId': candidate,
                'files': {n: {'bytes': len(b), 'sha256': sha(b)} for n, b in sorted(files.items())},
                'selfExcluded': 'PACKAGE-MANIFEST.json'}
    entries = {**files, 'PACKAGE-MANIFEST.json': encoded(manifest)}
    target = RELEASE / f'scroll-garden-step12-{kind}.zip'
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, body in sorted(entries.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, body)
    return {'file': str(target.relative_to(ROOT)), 'bytes': target.stat().st_size,
            'sha256': sha(target.read_bytes()), 'files': len(entries),
            'uncompressedBytes': sum(len(b) for b in entries.values())}

def main():
    build = json.loads((OUT / 'build-verification.json').read_text())
    assert build['passed']
    for name, expected in build['buildInputsSha256'].items():
        assert sha((ROOT / name).read_bytes()) == expected, f'Build input changed: {name}'
    dist = {str(p.relative_to(ROOT / 'dist')): p.read_bytes() for p in (ROOT / 'dist').rglob('*') if p.is_file()}
    assert {n: sha(b) for n, b in dist.items()} == build['buildSha256'], 'Rebuild and verify the candidate first.'
    required_docs = ['delivery.md', 'maintenance.md', 'step-12-standard.md', 'step-12-implementation.md', 'step-12-verification.md']
    assert all((ROOT / 'docs/scroll-garden' / n).is_file() for n in required_docs)
    source = {}
    for folder in ['src', 'public', 'scripts', 'tests/scroll-garden']:
        for p in sorted((ROOT / folder).rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts:
                source[str(p.relative_to(ROOT))] = p.read_bytes()
    for name in ['.gitignore', '.nvmrc', 'README.md', 'index.html', 'vite.config.ts', 'tsconfig.json', 'package.json', 'package-lock.json']:
        source[name] = (ROOT / name).read_bytes()
    for p in sorted((ROOT / 'docs').rglob('*.md')):
        if 'evidence' not in p.relative_to(ROOT).parts:
            source[str(p.relative_to(ROOT))] = p.read_bytes()
    source['SOURCE-PACKAGE.txt'] = ('Step12 source candidate. Run npm ci, npm run build.\n'
        'Current independent tests are documented in docs/scroll-garden/delivery.md.\n'
        'Extract the evidence ZIP here to add current reports, baseline and videos.\n'
        'Full historical screenshot fixtures remain in the original workspace; legacy suites may require them.\n'
        'No node_modules, Git history, credentials, browser profiles or old release archives included.\n').encode()
    dist['SITE-README.txt'] = ('sakan / Step12 static courtyard candidate\n'
        'Serve this directory over HTTP, at / or a real subdirectory ending in /.\n'
        'Default: courtyard; ?tour=prototype: compatibility; ?tour=reference: old portfolio.\n'
        'No Node application server, API keys or CDN required at runtime. Do not use file://.\n'
        'Missing assets must return 404, never an index.html fallback.\n'
        'Real personal films remain pending; design samples and early courtyard clip are labelled.\n'
        'This archive has not been deployed or published.\n').encode()
    evidence = {}
    # Final package reports include archive hashes and therefore stay external.
    excluded = {'summary.json', 'package-verification.json', 'unpacked-source-integrity.json', 'unpacked-site-integrity.json', 'unpacked-evidence-integrity.json'}
    for p in sorted(OUT.rglob('*')):
        rel = p.relative_to(OUT)
        if p.is_file() and rel.parts[0] not in excluded and not rel.parts[0].startswith('unpacked-'):
            evidence[str(p.relative_to(ROOT))] = p.read_bytes()
    # Carry the actual cited reports, not only a retelling of historical counts.
    for p in sorted((ROOT / 'docs/evidence/scroll-garden-step-11').rglob('*.json')):
        evidence[str(p.relative_to(ROOT))] = p.read_bytes()
    for n in required_docs:
        p = ROOT / 'docs/scroll-garden' / n
        evidence[str(p.relative_to(ROOT))] = p.read_bytes()
    evidence['EVIDENCE-README.txt'] = ('Step12 evidence, including fresh reports and explicitly inherited Step11 JSON records.\n'
        'Final ZIP integrity/unzip status is external: release/scroll-garden-step12-manifest.json\n'
        'and docs/evidence/scroll-garden-step-12/package-verification.json.\n'
        'Historical screenshots are not duplicated; Step11 baseline source/build is included.\n').encode()
    RELEASE.mkdir(exist_ok=True)
    packages = {k: archive(k, v, build['candidateId']) for k, v in [('source', source), ('site', dist), ('evidence', evidence)]}
    manifest = {'schema': 1, 'createdAtUtc': datetime.now(timezone.utc).isoformat(),
        'candidateId': build['candidateId'], 'buildInputFingerprint': build['buildInputFingerprint'],
        'contentStatus': 'interactive portfolio candidate; real personal AI films not supplied',
        'toolchain': {'node': build['node'], 'npm': build['npm'], 'three': '0.187.0', 'vite': '8.3.5', 'typescript': '7.0.2'},
        'buildInputsSha256': build['buildInputsSha256'], 'productionFilesSha256': build['buildSha256'],
        'packages': packages, 'verification': {'independentUnzip': 'pending'},
        'storage': {'workspaceSaved': True, 'archivesCreated': True, 'gitCommit': None, 'gitPushed': False, 'publishedOrDeployed': False},
        'externalFinalReports': ['docs/evidence/scroll-garden-step-12/summary.json', 'docs/evidence/scroll-garden-step-12/package-verification.json']}
    (RELEASE / 'scroll-garden-step12-manifest.json').write_bytes(encoded(manifest))
    print(json.dumps({'candidateId': build['candidateId'], 'packages': packages}, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
