"""Package an explicitly reviewed build. Archives are never overwritten.
Usage: python scripts/package-about-refresh.py --build-record /path/build.json
"""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import argparse, hashlib, json, shutil, subprocess, tempfile, zipfile

ROOT = Path(__file__).resolve().parents[1]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def row(p, base): return {'path':p.relative_to(base).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)}
def write(p, obj): p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def copy(src, target):
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(src,target)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--build-record',type=Path,required=True)
    ap.add_argument('--outdir',type=Path,default=ROOT/'release')
    ap.add_argument('--revision',type=int,default=1,help='New delivery revision for guide/check changes; runtime identity stays fixed')
    args=ap.parse_args();build=json.loads(args.build_record.read_text())
    candidate=build['candidateId'];out=args.outdir.resolve();out.mkdir(parents=True,exist_ok=True)
    assert args.revision>=1
    delivery=candidate+('-r'+str(args.revision) if args.revision>1 else '')
    names={kind:delivery+'-'+kind+'.zip' for kind in ['site','source']}
    manifest_path=out/(delivery+'-manifest.json');sums=out/(delivery+'-SHA256SUMS')
    assert not any((out/name).exists() for name in names.values()) and not manifest_path.exists() and not sums.exists(), 'Choose a new release identity; existing archives are immutable'
    assert build['buildPassed']
    frozen=Path(build['siteRoot'])
    for f in build['inputs']: assert row(ROOT/f['path'],ROOT)==f, 'Changed runtime input: '+f['path']
    for f in build['production']: assert row(frozen/f['path'],frozen)==f, 'Changed reviewed production file: '+f['path']
    scratch=Path(tempfile.mkdtemp(prefix='sakan-step14-package-',dir='/tmp'))
    site,source=scratch/'site',scratch/'source'
    shutil.copytree(frozen,site);source.mkdir()
    for f in build['inputs']: copy(ROOT/f['path'],source/f['path'])
    for filename in ['START-DEV.cmd','START-PREVIEW.cmd','.gitignore']:
        copy(ROOT/filename,source/filename)
    copy(ROOT/'START-PREVIEW.cmd',site/'START-PREVIEW.cmd')
    for filename in ['preview-site.mjs','serve-dist.mjs','package-about-refresh.py']:
        copy(ROOT/'scripts'/filename,source/'scripts'/filename)
    copy(ROOT/'scripts/preview-site.mjs',site/'scripts/preview-site.mjs')
    for filename in ['run-guide.md','maintenance.md']:
        copy(ROOT/'docs/about-refresh'/filename,source/'docs/about-refresh'/filename)
    for p in sorted((ROOT/'tests/about-refresh-final').glob('*.py')):
        copy(p,source/'tests/about-refresh-final'/p.name)
    guide=(ROOT/'docs/about-refresh/run-guide.md').read_text()
    for target in [site,source]:
        (target/'QUICKSTART.md').write_text(guide)
        write(target/'DELIVERY-VERSION.json',{'candidateId':candidate,'deliveryId':delivery,'runtimeInputDigest':build['runtimeInputDigest'],'productionFiles':build['production'],'runtimeInputs':build['inputs'],'committed':False,'pushed':False,'deployed':False})
    (site/'SITE-PACKAGE.txt').write_text('sakan current static site\nCandidate: '+candidate+'\nHTTP preview required. Run START-PREVIEW.cmd or node scripts/preview-site.mjs --open\nSee QUICKSTART.md. No npm installation required.\n')
    (source/'SOURCE-PACKAGE.txt').write_text('Current source and lightweight maintenance/browser checks; no Git history or historical evidence archives.\nCandidate: '+candidate+'\nRuntime input SHA256 is in DELIVERY-VERSION.json. Run npm ci, then npm run build.\n')
    (source/'README.md').write_text('# sakan · 张辰翰的创作庭院\n\n当前源码交付：**'+candidate+'**。包含关于我、22 张三维工具卡与 LAWSON / BOTTLE OCEAN / COURTYARD 三作品。尚未提交、推送或部署。\n\n[使用与操作](docs/about-refresh/run-guide.md) · [维护与验收脚本](docs/about-refresh/maintenance.md)\n\n'+guide+'\n包内 DELIVERY-VERSION.json 提供运行输入与生产文件的 SHA256，可用于核对重新构建结果。完整历史与本轮原始证据留在原工作区/后续仓库保存，不随该源码包复制。\n')
    artifacts={}
    for kind,target in [('site',site),('source',source)]:
        files=[row(p,target) for p in sorted(target.rglob('*')) if p.is_file()]
        write(target/'PACKAGE-MANIFEST.json',{'candidateId':candidate,'deliveryId':delivery,'kind':kind,'selfExcluded':'PACKAGE-MANIFEST.json','files':files})
        files.append(row(target/'PACKAGE-MANIFEST.json',target));files.sort(key=lambda f:f['path'])
        path=out/names[kind]
        with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for f in files:
                assert not set(Path(f['path']).parts)&{'.git','node_modules','.cache','__pycache__'}
                z.write(target/f['path'],f['path'])
        with zipfile.ZipFile(path) as z:
            assert z.testzip() is None
            assert sorted(z.namelist())==[f['path'] for f in files]
            for f in files:
                raw=z.read(f['path']);assert len(raw)==f['bytes'] and hashlib.sha256(raw).hexdigest()==f['sha256']
        artifacts[kind]={'fileName':path.name,'path':path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path),'bytes':path.stat().st_size,'sha256':sha(path),'files':files}
    manifest={'createdAtShanghai':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'candidateId':candidate,'deliveryId':delivery,'runtimeInputDigest':build['runtimeInputDigest'],'baseCommit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'committed':False,'pushed':False,'deployed':False,'production':build['production'],'inputs':build['inputs'],'artifacts':artifacts,'sourceREADME':'Generated portable guide; repository README and full historical evidence remain in workspace','verification':'See docs/about-refresh/step-14-verification.md in repository; validation records do not alter archive bytes'}
    write(manifest_path,manifest)
    sums.write_text(''.join(f['sha256']+'  '+f['fileName']+'\n' for f in artifacts.values()))
    print(json.dumps({'candidateId':candidate,'deliveryId':delivery,'artifacts':{k:{x:v[x] for x in ['path','bytes','sha256']} for k,v in artifacts.items()},'manifest':str(manifest_path),'staging':str(scratch)},ensure_ascii=False))
if __name__=='__main__': main()
