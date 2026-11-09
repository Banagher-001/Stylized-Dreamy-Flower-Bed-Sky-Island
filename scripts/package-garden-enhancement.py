"""Create new final local archives. Historical release files are never replaced.
Final ZIP verification, seals and archive hashes remain external to avoid cycles.
"""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,re,zipfile
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/evidence/garden-enhancement-step-7';RELEASE=ROOT/'release'
EXTERNAL={'summary.json','evidence-manifest.json','result-binding.json','scope-guard.json','package-verification.json','service-lifecycle.json','packaging-inputs.json'}
def digest(path):
    h=hashlib.sha256()
    with path.open('rb')as f:
        while b:=f.read(1024*1024):h.update(b)
    return h.hexdigest()
def encoded(value):return(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
def metadata(value):return{'bytes':len(value),'sha256':hashlib.sha256(value).hexdigest()}if isinstance(value,bytes)else{'bytes':value.stat().st_size,'sha256':digest(value)}
def add(files,path):
    assert path.is_file()and not path.is_symlink(),path
    name=path.relative_to(ROOT).as_posix();assert not name.startswith('/')and'..'not in Path(name).parts
    files[name]=path
def archive(kind,files,candidate):
    assert files and'PACKAGE-MANIFEST.json'not in files
    manifest={'schema':1,'kind':kind,'candidateId':candidate,'files':{n:metadata(p)for n,p in sorted(files.items())},'selfExcluded':'PACKAGE-MANIFEST.json'}
    target=RELEASE/f'{candidate}-{kind}.zip'
    entries={**files,'PACKAGE-MANIFEST.json':encoded(manifest)}
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as z:
        for name,value in sorted(entries.items()):
            info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0));info.external_attr=0o100644<<16
            info.compress_type=zipfile.ZIP_STORED if Path(name).suffix.lower()in{'.png','.webp','.mp4','.gz','.zip'}else zipfile.ZIP_DEFLATED
            with z.open(info,'w')as dest:
                if isinstance(value,bytes):dest.write(value)
                else:
                    with value.open('rb')as source:
                        while b:=source.read(1024*1024):dest.write(b)
    return{'file':target.relative_to(ROOT).as_posix(),'bytes':target.stat().st_size,'sha256':digest(target),'files':len(entries),
        'uncompressedBytes':sum(m['bytes']for m in manifest['files'].values())+len(encoded(manifest))}
def main():
    build=json.loads((OUT/'build-verification.json').read_text());candidate=build['candidateId'];assert build['passed']and build['finalRebuildByteIdenticalToTestedBuild']
    assert all(digest(ROOT/n)==v for n,v in build['buildInputsSha256'].items())
    assert all(digest(ROOT/n)==v for n,v in build['productionSha256'].items())
    required=['delivery.md','quickstart.md','maintenance.md','step-7-standard.md','step-7-implementation.md','step-7-verification.md']
    assert all((ROOT/'docs/garden-enhancement'/n).is_file()for n in required)
    snapshot=json.loads((OUT/'candidate-archive-manifest.json').read_text());source={}
    for name in snapshot['files']:
        if not name.startswith('dist/')and name!='README.md':add(source,ROOT/name)
    for name in ['START-PREVIEW.cmd','START-DEV.cmd','scripts/preview-site.mjs','scripts/package-garden-enhancement.py']:add(source,ROOT/name)
    for folder in ['tests/garden-enhancement','tests/scroll-garden','tests/final']:
        for p in sorted((ROOT/folder).rglob('*')):
            if p.is_file()and'__pycache__'not in p.parts and p.suffix in{'.py','.mjs','.js','.json','.txt'}:add(source,p)
    for name in ['delivery.md','quickstart.md','maintenance.md']:add(source,ROOT/'docs/garden-enhancement'/name)
    source['QUICKSTART.md']=ROOT/'docs/garden-enhancement/quickstart.md'
    source['README.md']=('# sakan / 张辰翰 庭院网页\n\n当前候选：`'+candidate+'`。\n\n先阅读[快速上手](QUICKSTART.md)。Windows修改用START-DEV.cmd，已有构建的预览用START-PREVIEW.cmd；Node建议LTS24。\n\n[维护说明](docs/garden-enhancement/maintenance.md) · [交付说明](docs/garden-enhancement/delivery.md)。\n\n源码可独立安装、严格构建和运行；当前报告与基线在单独evidence包，完整历史套件的fixture需求见维护说明。未包含node_modules、Git历史、凭据或浏览器用户目录。本包没有自动提交Git、推送或上线。\n').encode()
    source['SOURCE-PACKAGE.txt']=('Build: npm ci; npm run build. Preview: node scripts/preview-site.mjs.\n'
        'Standalone check: python tests/garden-enhancement/step7_release_check.py --site dist --out /tmp/sakan-check (requires Playwright/Chromium).\n'
        'Historical scope/seal/performance suites require their evidence/baseline and native Linux tooling; not a promise of all historical tests on a bare Windows machine.\n').encode()
    site={Path(n).relative_to('dist').as_posix():ROOT/n for n in build['productionSha256']}
    site['scripts/preview-site.mjs']=ROOT/'scripts/preview-site.mjs';site['START-PREVIEW.cmd']=ROOT/'START-PREVIEW.cmd';site['QUICKSTART.md']=ROOT/'docs/garden-enhancement/quickstart.md'
    site['SITE-PACKAGE.txt']=('sakan final static courtyard / '+candidate+'\nWindows: extract everything and run START-PREVIEW.cmd with Node LTS24 installed. No npm dependency install needed for this static preview.\n'
        'For static hosting upload index.html,assets,favicon.svg,share-cover.webp; no file:// or SPA fallback required. Source/evidence have separate archives.\n').encode()
    evidence={};historical=[];external=[]
    for step in range(1,7):
        folder=ROOT/f'docs/evidence/garden-enhancement-step-{step}';seal=json.loads((folder/'evidence-manifest.json').read_text())
        for n,m in seal['files'].items():
            path=ROOT/n;assert digest(path)==m['sha256'],n;add(evidence,path)
        for name in ['evidence-manifest.json','summary.json']:
            if(folder/name).is_file():add(evidence,folder/name)
        historical.append({'step':step,'candidateId':seal.get('candidateId'),'sealedFiles':len(seal['files']),'manifestSha256':digest(folder/'evidence-manifest.json')})
    for p in sorted(OUT.rglob('*')):
        if p.is_file()and p.name not in EXTERNAL and not p.name.startswith('unpacked-'):add(evidence,p)
    for p in (ROOT/'docs/garden-enhancement').glob('*.md'):
        if p.name!='progress.md':add(evidence,p)
    # Include local documentation dependencies; mutable progress and old release
    # ZIPs remain explicit external references, not duplicate old deliveries.
    visited=set()
    while True:
        pending=[p for p in evidence.values()if isinstance(p,Path)and p.suffix=='.md'and p not in visited]
        if not pending:break
        for p in pending:
            visited.add(p)
            for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',p.read_text()):
                target=target.strip('<>').split('#')[0]
                if not target or target.startswith(('http:','https:','skill:','mailto:')):continue
                local=(p.parent/target).resolve()
                try:name=local.relative_to(ROOT).as_posix()
                except ValueError:continue
                if name.startswith('release/')or name=='docs/garden-enhancement/progress.md'or(local.parent==OUT and local.name in EXTERNAL):
                    external.append({'document':p.relative_to(ROOT).as_posix(),'target':target,'reason':'external final report, mutable progress or historical release; authoritative data retained outside archive'});continue
                if local.is_file():add(evidence,local)
                elif local.is_dir():
                    for child in local.rglob('*'):
                        if child.is_file()and child.name not in EXTERNAL:add(evidence,child)
                else:raise AssertionError(('Broken packaged documentation dependency',p,target))
    evidence['HISTORICAL-REFERENCES.json']=encoded({'inheritedSeals':historical,'externalReferences':external,'freshStep7Directory':'docs/evidence/garden-enhancement-step-7','historicalOutputsAreNotFreshRuns':True})
    evidence['EVIDENCE-README.md']=('# 验收附件\n\n本包含第七步封包前新报告/原速视频、独立基线，以及前六步1428份封印中的历史文件和来源清单。历史报告保留其原候选身份，不计作本轮新跑。\n\n最终ZIP解压验证、签收摘要与封印在包外，由release中同名前缀的manifest.json和原工作区docs/evidence/garden-enhancement-step-7/summary.json登记，以避免ZIP包含自身最后哈希。progress.md是可变入口，不归档。HISTORICAL-REFERENCES.json列出包外引用。\n').encode()
    RELEASE.mkdir(exist_ok=True)
    packages={kind:archive(kind,files,candidate)for kind,files in [('source',source),('site',site),('evidence',evidence)]}
    manifest={'schema':1,'candidateId':candidate,'createdAtUtc':datetime.now(timezone.utc).isoformat(),'baselineId':build['baselineId'],
        'buildInputFingerprint':build['buildInputFingerprint'],'buildInputsSha256':build['buildInputsSha256'],'productionFilesSha256':build['productionSha256'],
        'toolchain':{'node':build['node'],'npm':build['npm'],'three':'0.187.0','vite':'8.3.5','typescript':'7.0.2'},
        'packages':packages,'deliveryInputsSha256':{n:digest(ROOT/n)for n in ['START-PREVIEW.cmd','START-DEV.cmd','scripts/preview-site.mjs','scripts/package-garden-enhancement.py',*[f'docs/garden-enhancement/{n}'for n in required]]},
        'contentStatus':'real user identity; second-pillar images labelled design samples; archival12s silent clip labelled earlier study; real personal films not supplied',
        'independentUnzip':'pending','physicalDevicePending':True,'windowsRuntimeTested':False,
        'storage':{'workspaceSaved':True,'archivesCreated':True,'gitCommit':None,'gitPushed':False,'publishedOrDeployed':False},
        'externalFinalReports':['docs/evidence/garden-enhancement-step-7/package-verification.json','docs/evidence/garden-enhancement-step-7/summary.json']}
    path=RELEASE/f'{candidate}-manifest.json';path.write_bytes(encoded(manifest));print(json.dumps({'manifest':path.relative_to(ROOT).as_posix(),'packages':packages},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
