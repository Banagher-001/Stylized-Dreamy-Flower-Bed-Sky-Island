"""Independently unzip both artifacts and rebuild the source with a fresh dependency tree."""
import shutil,time,zipfile
from common import *
assert not(OUT/'package-validation.json').exists();baseline=read(OUT/'baseline.json');scratch=Path(baseline['scratch']);manifest=read(OUT/'delivery-manifest.json');base=scratch/'独立 解压验证';assert not base.exists();base.mkdir();result={'startedAtShanghai':now(),'freshExtraction':True,'unicodeAndSpacesInPaths':True,'archives':{},'commands':[]}
for kind,name in[('site','成品 网站'),('source','源码 项目')]:
 a=manifest['artifacts'][kind];archive=Path(a['absolutePath']);assert sha(archive)==a['sha256'];destination=base/name;destination.mkdir()
 with zipfile.ZipFile(archive)as z:
  assert z.testzip()is None
  for member in z.infolist():assert(destination/member.filename).resolve().is_relative_to(destination)
  z.extractall(destination)
 assert tree(destination,destination)==a['files'];result['archives'][kind]={'path':str(destination),'filesVerified':len(a['files']),'archiveSHA256':a['sha256']}
source=Path(result['archives']['source']['path']);assert not(source/'node_modules').exists()and not(source/'dist').exists();result['sourceHadNoNodeModulesOrDist']=True
commands=[('npm-ci',['npm','ci','--cache','/workspace/.cache/npm','--prefer-offline','--no-audit','--fund=false']),('source-build',['npm','run','build'])]
for label,argv in commands:
 start=now();wall=time.monotonic()
 with(OUT/(label+'.log')).open('w')as log:p=subprocess.run(argv,cwd=source,stdout=log,stderr=subprocess.STDOUT)
 rowdata={'label':label,'argv':argv,'cwd':str(source),'startedAtShanghai':start,'exitCode':p.returncode,'wallSeconds':time.monotonic()-wall};result['commands'].append(rowdata);write(OUT/'package-validation-partial.json',result);assert p.returncode==0,(label,p.returncode)
actual=tree(source/'dist',source/'dist');assert actual==manifest['buildManifest'],'Independent source rebuild differs from final build'
for f in manifest['productionInputs']:assert row(source/f['path'],source)==f,f['path']
site=Path(result['archives']['site']['path']);assert sha(site/'experiments/bottle-ocean/index.html')==sha(source/'dist/experiments/bottle-ocean/index.html')==ENTRY_SHA
cmd=(site/'START-PREVIEW.cmd').read_text();assert 'cd /d "%~dp0"'in cmd and 'node "scripts\\preview-site.mjs" --open'in cmd and 'SetExecutionPolicy'not in cmd
result.update({'finishedAtShanghai':now(),'sourceBuildByteIdentical':True,'rebuiltFilesVerified':len(actual),'runtimeInputsVerifiedAfterInstallAndBuild':97,'nodeVersion':subprocess.check_output(['node','--version'],text=True).strip(),'npmVersion':subprocess.check_output(['npm','--version'],text=True).strip(),'windowsLauncherStaticCheck':True,'windowsActuallyExecuted':False,'complete':True})
write(OUT/'package-validation.json',result);print(json.dumps({'independentSourceInstalledAndBuilt':True,'rebuildByteIdentical':True,'rebuiltFiles':len(actual),'extractedSite':str(site),'extractedSource':str(source)},ensure_ascii=False))
