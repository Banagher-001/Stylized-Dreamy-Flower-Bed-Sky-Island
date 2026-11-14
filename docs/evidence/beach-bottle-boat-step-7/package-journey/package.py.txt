"""Create portable site/source archives outside the repository, with exact manifests."""
import shutil,zipfile
from common import *
assert read(OUT/'functional-summary.json')['complete'];assert not(OUT/'delivery-manifest.json').exists();protection=protect_current();config=read(OUT/'delivery-config.json');active=read(OUT/'active-build.json');build=Path(active['buildRoot']);b=read(OUT/active['record']);scratch=Path(read(OUT/'baseline.json')['scratch']);delivery=Path(config['deliveryDirectory']);assert not delivery.exists();delivery.mkdir(parents=True)
assert [row(ROOT/f['path'])for f in read(OUT/'baseline.json')['productionInputsBefore']]==b['productionInputs']
stage=scratch/'package-stage';site=stage/'site';source=stage/'source';shutil.copytree(build,site);source.mkdir(parents=True)
for name in['src','public']:shutil.copytree(ROOT/name,source/name)
rootFiles=['package.json','package-lock.json','index.html','vite.config.ts','.nvmrc','.gitignore','README.md','START-DEV.cmd']+[p.name for p in ROOT.glob('tsconfig*.json')]
for name in sorted(set(rootFiles)):
 if(ROOT/name).is_file():shutil.copyfile(ROOT/name,source/name)
for name in['preview-site.mjs','serve-dist.mjs']:
 dest=source/'scripts'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/'scripts'/name,dest)
preview=site/'scripts/preview-site.mjs';preview.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/'scripts/preview-site.mjs',preview)
guide=(DOC/'step-7-run-guide.md').read_text()
for directory in[site,source]:(directory/'QUICKSTART.md').write_text(guide)
dest=source/'docs/beach-bottle-boat/step-7-run-guide.md';dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(DOC/'step-7-run-guide.md',dest)
(site/'SITE-PACKAGE.txt').write_text('Current three-project static site\nCandidate: '+config['candidateId']+'\nOriginal bottle HTML SHA256: '+ENTRY_SHA+'\nHTTP preview required; see QUICKSTART.md\n')
(source/'SOURCE-PACKAGE.txt').write_text('Current application source, not full Git history or historical evidence archives.\nCandidate: '+config['candidateId']+'\nAll 97 production input hashes match the reviewed working tree.\nRun npm ci and npm run build. See QUICKSTART.md.\n')
cmd='''@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
where node >nul 2>nul
if errorlevel 1 goto no_node
node "scripts\\preview-site.mjs" --open %*
if errorlevel 1 goto failed
exit /b 0
:no_node
echo 请先安装 Node.js LTS 24，然后重新双击本文件。
:failed
echo 请保留上方错误信息，查看 QUICKSTART.md。
pause
exit /b 1
''';(site/'START-PREVIEW.cmd').write_bytes(cmd.replace('\n','\r\n').encode('utf-8'))
for filename in['LICENSE','LICENSE.md','LICENSE.txt','NOTICE']:
 if(ROOT/filename).is_file():
  for directory in[site,source]:shutil.copyfile(ROOT/filename,directory/filename)
for f in b['productionInputs']:assert row(source/f['path'],source)==f,f['path']
for f in b['productionManifest']:assert row(site/f['path'],site)==f,f['path']
assert sha(site/'experiments/bottle-ocean/index.html')==sha(source/'public/experiments/bottle-ocean/index.html')==ENTRY_SHA
def archive(directory,name):
 target=delivery/name;manifest=tree(directory,directory)
 with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as z:
  for f in manifest:z.write(directory/f['path'],f['path'])
 with zipfile.ZipFile(target)as z:
  assert z.testzip()is None and sorted(z.namelist())==sorted(f['path']for f in manifest)
  for f in manifest:
   assert not any(p in['.git','node_modules','.cache','.aws']for p in Path(f['path']).parts)
   raw=z.read(f['path']);assert len(raw)==f['bytes']and hashlib.sha256(raw).hexdigest()==f['sha256']
  for f in manifest:
   if f['path'].endswith('.js'):assert b'__parityProbe'not in z.read(f['path'])and b'__embeddedTest'not in z.read(f['path'])
 return {'fileName':name,'absolutePath':str(target),'bytes':target.stat().st_size,'sha256':sha(target),'files':manifest}
artifacts={'site':archive(site,config['siteName']),'source':archive(source,config['sourceName'])}
manifest={'createdAtShanghai':now(),'candidateId':config['candidateId'],'baseCommit':git(ROOT,'rev-parse','HEAD'),'committed':False,'pushed':False,'deployed':False,'runtimeEntrySHA256':ENTRY_SHA,'productionInputs':b['productionInputs'],'buildManifest':b['productionManifest'],'artifacts':artifacts,'sourceExcludesHistoricalEvidence':True,'windowsLauncher':'Provided and statically inspected; runtime Node preview tested on Linux, no Windows-device claim','packageValidationStatus':'See the separate package-validation.json and final verification report; archive bytes remain fixed'}
write(delivery/'manifest.json',manifest);write(OUT/'delivery-manifest.json',manifest);(delivery/'SHA256SUMS').write_text(''.join(a['sha256']+'  '+a['fileName']+'\n'for a in artifacts.values()))
write(OUT/'package-stages.json',{'site':str(site),'source':str(source),'deliveryDirectory':str(delivery),'runtimeInputsVerified':97,'productionFilesVerified':len(b['productionManifest'])})
print(json.dumps({'packagesCreated':True,'candidateId':config['candidateId'],'siteBytes':artifacts['site']['bytes'],'sourceBytes':artifacts['source']['bytes'],'deliveryDirectory':str(delivery)},ensure_ascii=False))
