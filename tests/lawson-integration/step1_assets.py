"""Read-only dependency/GLB audit; only writes this step's evidence and a /tmp copy."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import argparse, hashlib, json, re, shutil, struct

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'docs/evidence/lawson-integration-step-1'
SOURCE = Path('/workspace/luosen-asset/lawson-blender/out/web_final')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Entry(HTMLParser):
    def __init__(self):
        super().__init__()
        self.references = []
        self.import_map = {}
        self.in_map = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'script' and attrs.get('type') == 'importmap':
            self.in_map = True
        for key in ['src', 'href']:
            if key in attrs:
                self.references.append(attrs[key])

    def handle_data(self, value):
        if self.in_map:
            self.import_map = json.loads(value)['imports']

    def handle_endtag(self, tag):
        if tag == 'script':
            self.in_map = False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', default='/tmp/lawson-step1-audit')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    entry = Entry()
    entry.feed((SOURCE / 'index.html').read_text())
    missing, external, unresolved, edges = [], [], [], []
    pending, found = ['index.html'], set()

    def reference(owner, spec, module=False):
        if spec.startswith(('data:', 'blob:', '#')):
            return
        if urlsplit(spec).scheme or spec.startswith('//'):
            external.append({'from': owner, 'url': spec})
            return
        if module and not spec.startswith(('.', '/')):
            mapped = entry.import_map.get(spec)
            if mapped is None:
                for prefix, target in entry.import_map.items():
                    if prefix.endswith('/') and spec.startswith(prefix):
                        mapped = target + spec[len(prefix):]
                        break
            if mapped is None:
                unresolved.append({'from': owner, 'specifier': spec})
                return
            path = SOURCE / mapped
        else:
            path = (SOURCE / spec.lstrip('/')) if spec.startswith('/') else (SOURCE / owner).parent / spec
        path = Path(unquote(str(path).split('?', 1)[0].split('#', 1)[0])).resolve()
        if not path.is_relative_to(SOURCE):
            missing.append({'from': owner, 'specifier': spec, 'reason': 'outside runtime root'})
            return
        rel = str(path.relative_to(SOURCE))
        edges.append({'from': owner, 'to': rel})
        if not path.is_file():
            missing.append({'from': owner, 'specifier': spec, 'resolved': rel})
        elif rel not in found:
            pending.append(rel)

    while pending:
        rel = pending.pop()
        if rel in found:
            continue
        found.add(rel)
        path = SOURCE / rel
        if rel == 'index.html':
            for spec in entry.references:
                reference(rel, spec)
        elif path.suffix == '.js':
            text = path.read_text()
            # Only actual module statements, not URLs in Three.js documentation.
            pattern = r"(?:\b(?:import|export)\s+(?:[^;'\"]*?\s+from\s*)?|\bimport\s*\()\s*['\"]([^'\"]+)['\"]"
            for spec in re.findall(pattern, text):
                reference(rel, spec, module=True)
            if rel == 'js/config/assetManifest.js':
                for spec in re.findall(r"\burl\s*:\s*['\"]([^'\"]+)['\"]", text):
                    # GLTFLoader receives strings resolved against the document.
                    reference('index.html', spec)
        elif path.suffix == '.css':
            for spec in re.findall(r"url\(\s*['\"]?([^)'\"\s]+)", path.read_text()):
                reference(rel, spec)

    glbs = []
    for rel in sorted(found):
        path = SOURCE / rel
        if path.suffix != '.glb':
            continue
        data = path.read_bytes()
        magic, version, size = struct.unpack_from('<4sII', data)
        assert magic == b'glTF' and version == 2 and size == len(data), rel
        offset, document = 12, None
        while offset < len(data):
            length, kind = struct.unpack_from('<II', data, offset)
            offset += 8
            if kind == 0x4E4F534A:
                document = json.loads(data[offset:offset + length])
            offset += length
        assert document is not None, rel
        uris = [item['uri'] for group in ['buffers', 'images'] for item in document.get(group, []) if 'uri' in item]
        for uri in uris:
            reference(rel, uri)
        names = {node.get('name') for node in document.get('nodes', [])}
        glbs.append({'path': rel, 'bytes': len(data), 'sha256': digest(path),
                     'nodes': len(document.get('nodes', [])), 'meshes': len(document.get('meshes', [])),
                     'materials': len(document.get('materials', [])), 'images': len(document.get('images', [])),
                     'animations': len(document.get('animations', [])), 'externalOrDataURIs': uris,
                     'extensionsRequired': document.get('extensionsRequired', []),
                     'importantNodes': {name: name in names for name in ['roofRoot', 'slideDoorLeft_pivot', 'slideDoorRight_pivot', 'clerkA_root', 'clerkB_root']} if 'lawson_scene' in rel else {}})

    # No GLB external references currently; reject one until recursive handling is verified.
    assert all(not model['externalOrDataURIs'] for model in glbs), 'Inspect new external model dependencies'
    assert not missing and not external and not unresolved, (missing, external, unresolved)
    files = [{'path': rel, 'bytes': (SOURCE / rel).stat().st_size, 'sha256': digest(SOURCE / rel)} for rel in sorted(found)]
    all_runtime = {str(p.relative_to(SOURCE)) for p in SOURCE.rglob('*') if p.is_file() and (p.relative_to(SOURCE).parts[0] in ['js', 'css', 'assets', 'vendor'] or p.name == 'index.html')}
    candidates = ['screenshots_clerk/cherry_final_hero.png', 'screenshots/03_hero_night.png', 'screenshots/08_interior.png', 'screenshots/09_checkout.png']
    result = {'schema': 1, 'passed': True, 'sourceRoot': str(SOURCE), 'entry': 'index.html', 'importMap': entry.import_map,
              'runtimeFiles': files, 'runtimeFileCount': len(files), 'runtimeBytes': sum(f['bytes'] for f in files),
              'modelBytes': sum(model['bytes'] for model in glbs), 'models': glbs, 'dependencyEdges': edges,
              'missing': missing, 'externalNetworkDependencies': external, 'unresolvedImports': unresolved,
              'unreferencedRuntimeFiles': sorted(all_runtime - found),
              'threeRevision': re.search(r"const REVISION = ['\"]([^'\"]+)", (SOURCE / 'vendor/three/three.module.js').read_text()).group(1),
              'hostThreeVersion': json.loads((ROOT / 'package.json').read_text())['dependencies']['three'],
              'archiveImageCandidates': [{'path': str(SOURCE / p), 'sha256': digest(SOURCE / p), 'provenance': 'existing source archive; not a new runtime verification'} for p in candidates]}
    (OUT / 'asset-manifest.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    stage = Path(args.stage)
    for prefix in ['root', 'experiments/lawson']:
        for item in files:
            target = stage / prefix / item['path']
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(SOURCE / item['path'], target)
            assert digest(target) == item['sha256']
    print(json.dumps({key: result[key] for key in ['passed', 'runtimeFileCount', 'runtimeBytes', 'modelBytes', 'threeRevision', 'hostThreeVersion', 'unreferencedRuntimeFiles']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
