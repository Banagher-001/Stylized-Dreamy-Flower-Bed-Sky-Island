"""Own an isolated Vite copy; never mutate the reviewed working source for HMR."""
from pathlib import Path
import json,shutil,tempfile,hashlib
from harness import ROOT,OUT
target=Path(tempfile.mkdtemp(prefix='lawson-step6-hmr-',dir='/tmp'))
for name in ['index.html','package.json','package-lock.json','tsconfig.json','vite.config.ts']:shutil.copyfile(ROOT/name,target/name)
for name in ['src','public']:shutil.copytree(ROOT/name,target/name)
(target/'node_modules').symlink_to(ROOT/'node_modules',target_is_directory=True)
p=target/'vite.config.ts';text=p.read_text();assert 'export default defineConfig({'in text;p.write_text(text.replace('export default defineConfig({',"export default defineConfig({\n  cacheDir: './.vite-step6',",1))
rows=[]
for name in ['src/tour/createLawsonExperience.ts','src/tour/createProjectViewer.ts','src/tour/startTourPrototype.ts','src/tour/projectHost.css']:
    p=target/name;assert p.read_bytes()==(ROOT/name).read_bytes();rows.append({'path':name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
manifest=json.loads((ROOT/'docs/evidence/lawson-fullpage-step-1/runtime-manifest.json').read_text())
for f in manifest['runtimeFiles']:assert hashlib.sha256((target/'public/experiments/lawson'/f['path']).read_bytes()).hexdigest()==f['sha256']
(OUT/'hmr-copy.json').write_text(json.dumps({'path':str(target),'copiedProductionFiles':rows,'runtimeFilesUnchanged':46,'isolatedViteCache':True},ensure_ascii=False,indent=2)+'\n')
print(target)
