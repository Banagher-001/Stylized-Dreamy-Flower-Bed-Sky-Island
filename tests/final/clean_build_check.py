from pathlib import Path
import subprocess,tempfile,shutil,hashlib,json,time,os
root=Path(__file__).resolve().parents[2];out=root/'docs/evidence/step-9';clean=Path(tempfile.mkdtemp(prefix='courtyard-step9-clean-',dir='/tmp'))
for name in ['package.json','package-lock.json','index.html','tsconfig.json','vite.config.ts','.nvmrc']:
 shutil.copy2(root/name,clean/name)
for name in ['src','public']:shutil.copytree(root/name,clean/name)
logs=[]
for command in [['node','--version'],['npm','--version'],['npm','ci','--cache',os.environ.get('COURTYARD_NPM_CACHE',str(Path(tempfile.gettempdir())/'courtyard-npm-cache')),'--no-fund','--no-audit'],['npm','run','build']]:
 r=subprocess.run(command,cwd=clean,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);logs.append({'command':command,'exitCode':r.returncode,'output':r.stdout});print(' '.join(command),'exit',r.returncode,flush=True);assert r.returncode==0,r.stdout
reference={str(p.relative_to(root/'dist')):hashlib.sha256(p.read_bytes()).hexdigest()for p in(root/'dist').rglob('*')if p.is_file()}
rebuilt={str(p.relative_to(clean/'dist')):hashlib.sha256(p.read_bytes()).hexdigest()for p in(clean/'dist').rglob('*')if p.is_file()}
assert reference==rebuilt,(reference,rebuilt)
result={'isolatedDirectory':str(clean),'installUsedExistingNodeModules':False,'artifactHashesMatch':True,'artifacts':reference,'commands':logs}
(out/'clean-build.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');Path('/tmp/courtyard-step9-clean-root').write_text(str(clean));print('isolated install/build identical',len(reference),'files',flush=True)
