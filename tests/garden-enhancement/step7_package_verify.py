"""Independently extract all three final ZIPs, rebuild source, run packaged tools.
Archive-dependent reports stay outside their archives; no self-hash cycle.
"""
from pathlib import Path
import hashlib,json,os,shutil,stat,subprocess,sys,tempfile,zipfile
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/evidence/garden-enhancement-step-7'
def sha(path):
    h=hashlib.sha256()
    with path.open('rb')as f:
        while b:=f.read(1024*1024):h.update(b)
    return h.hexdigest()
def save(name,data):(OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
build=json.loads((OUT/'build-verification.json').read_text());candidate=build['candidateId'];mp=ROOT/'release'/f'{candidate}-manifest.json';manifest=json.loads(mp.read_text());assert manifest['candidateId']==candidate
work=Path(tempfile.mkdtemp(prefix='sakan-step7-unpacked-'));folders={};integrity={}
for kind,package in manifest['packages'].items():
    path=ROOT/package['file'];assert sha(path)==package['sha256']and path.stat().st_size==package['bytes']
    destination=work/'中文 空格'/kind;destination.mkdir(parents=True);folders[kind]=destination
    with zipfile.ZipFile(path)as z:
        names=z.namelist();assert len(names)==len(set(names))and z.testzip()is None
        for info in z.infolist():
            n=info.filename;assert not n.startswith('/')and'..'not in Path(n).parts and'\\'not in n and':'not in n.split('/')[0]and'\0'not in n
            assert not stat.S_ISLNK(info.external_attr>>16)
        package_manifest=json.loads(z.read('PACKAGE-MANIFEST.json'));assert package_manifest['candidateId']==candidate and package_manifest['kind']==kind
        assert set(names)==set(package_manifest['files'])|{'PACKAGE-MANIFEST.json'}
        for n,meta in package_manifest['files'].items():
            with z.open(n)as f:
                h=hashlib.sha256();count=0
                while b:=f.read(1024*1024):h.update(b);count+=len(b)
            assert h.hexdigest()==meta['sha256']and count==meta['bytes'],n
        z.extractall(destination)
    assert all(sha(destination/n)==v['sha256']and(destination/n).stat().st_size==v['bytes']for n,v in package_manifest['files'].items())
    integrity[kind]={'passed':True,'candidateId':candidate,'kind':kind,'archive':package['file'],'archiveSha256':package['sha256'],'files':len(names),'extraction':str(destination),'CRCAndAllSha256':True,'safePathsAndNoSymlinks':True}
    save(f'unpacked-{kind}-integrity.json',integrity[kind]);print('PASS independent ZIP',kind,len(names),'files',flush=True)
source=folders['source'];assert not(source/'node_modules').exists()
for n,expected in build['buildInputsSha256'].items():assert sha(source/n)==expected,n
cache=work/'npm-cache';existing=Path('/workspace/.cache/npm')
if(existing/'_cacache').is_dir():shutil.copytree(existing/'_cacache',cache/'_cacache')
install=['npm','ci','--offline','--cache',str(cache),'--no-audit','--no-fund']
with(OUT/'unpacked-npm-ci.log').open('w')as log:result=subprocess.run(install,cwd=source,stdout=log,stderr=subprocess.STDOUT)
method='clean source npm ci with a copied official npm content cache, offline'
if result.returncode:
    shutil.copyfile(OUT/'unpacked-npm-ci.log',OUT/'unpacked-npm-ci-initial.log')
    install.remove('--offline')
    with(OUT/'unpacked-npm-ci.log').open('w')as log:subprocess.run(install,cwd=source,stdout=log,stderr=subprocess.STDOUT,check=True)
    method='clean source npm ci; cache miss preserved and retry used inherited network proxy/CA with pinned lock'
with(OUT/'unpacked-source-build.log').open('w')as log:subprocess.run(['npm','run','build'],cwd=source,stdout=log,stderr=subprocess.STDOUT,check=True)
actual={str(p.relative_to(source)):sha(p)for p in sorted((source/'dist').rglob('*'))if p.is_file()}
assert actual==build['productionSha256'],'Clean source rebuild differs from tested application'
assert all(sha(source/n)==expected for n,expected in build['buildInputsSha256'].items())
print('PASS clean source install and strict18-file byte-identical rebuild',flush=True)
browser_reports={}
for kind,site in [('source',source/'dist'),('site',folders['site'])]:
    output=work/f'check-{kind}'
    subprocess.run([sys.executable,str(source/'tests/garden-enhancement/step7_release_check.py'),'--site',str(site),'--out',str(output)],cwd=source,check=True)
    report=json.loads((output/'release-check.json').read_text());assert report['passed']and not report['errors']
    assert {'dist/'+n:v for n,v in report['productionSha256'].items()}==build['productionSha256']
    for frame in output.glob('*.png'):shutil.copyfile(frame,OUT/('unpacked-'+kind+'-'+frame.name))
    report['candidateId']=candidate;report['binding']='all18actual served production hashes verified against final build'
    save(f'unpacked-{kind}-browser.json',report);browser_reports[kind]={'passed':True,'report':f'unpacked-{kind}-browser.json','rootAndRealSubpath':True,'actualProductionFiles':len(report['productionSha256'])}
for kind,folder in folders.items():
    pm=json.loads((folder/'PACKAGE-MANIFEST.json').read_text());assert all(sha(folder/n)==meta['sha256']for n,meta in pm['files'].items())
report={'passed':True,'candidateId':candidate,'independentExtractions':integrity,'sourceInitiallyHadNoNodeModules':True,'sourceInstallMethod':method,'sourceStrictBuildByteIdentical':True,
    'browserChecks':browser_reports,'workspaceBuildInputsUnchanged':all(sha(ROOT/n)==v for n,v in build['buildInputsSha256'].items()),
    'zipEntryIntegrityAfterBuildAndBrowserChecks':True,'workDirectory':str(work),'windowsRuntimeTested':False,'physicalDevice':False,
    'method':'three fresh independent extraction directories with Chinese/space names; CRC/safe entries/full bytes verified; copied npm content cache only (no original node_modules); exact locked install and fresh build; actual packaged standalone checker and preview tool used at root and real subdirectory'}
save('package-verification.json',report)
manifest['independentUnzip']='passed';manifest['verificationReport']='docs/evidence/garden-enhancement-step-7/package-verification.json';manifest['verificationReportSha256']=sha(OUT/'package-verification.json')
mp.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print('PASS final source/site/evidence independent delivery verification; no Git/remote publication',flush=True)
