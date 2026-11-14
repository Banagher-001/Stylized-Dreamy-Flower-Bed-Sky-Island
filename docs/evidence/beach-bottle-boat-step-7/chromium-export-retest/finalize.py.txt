"""Seal independent evidence, product snapshots and external deliverable identities."""
import argparse,difflib,shutil
from common import *
p=argparse.ArgumentParser();p.add_argument('--verify-only',action='store_true');p.add_argument('--seal',action='store_true');args=p.parse_args()
if args.verify_only:
 m=read(OUT/'evidence-manifest.json')
 for f in m['files']:assert row(ROOT/f['path'])==f,f['path']
 for a in m['externalArtifacts']:
  target=Path(a['absolutePath']);assert target.is_file()and target.stat().st_size==a['bytes']and sha(target)==a['sha256']
 h=history();assert len(h['seals'])==13
 print(json.dumps({'step7EvidenceIntact':True,'sealedFiles':len(m['files']),'historicalSealsVerified':13,'deliverableArtifactsIntact':len(m['externalArtifacts'])}));raise SystemExit
assert args.seal and not(OUT/'evidence-manifest.json').exists()
b=read(OUT/'baseline.json');protection=protect_current();functional=read(OUT/'functional-summary.json');packages=read(OUT/'package-validation.json');delivery=read(OUT/'delivery-manifest.json');visual=read(OUT/'visual-review.json');cleanup=read(OUT/'services-cleanup.json');pc=read(OUT/'package-preview-cleanup.json');journey=read(OUT/'package-journey/browser.json');build=read(OUT/'build-final.json')
assert functional['complete']and functional['pairedChecks']==68 and functional['uniqueOriginalControls']==34
assert journey['complete']and len(journey['checks'])==2 and not journey['externalAttempts']
assert not[e for e in journey['events']if e['kind']in['pageerror','error']],journey['events']
assert packages['complete']and packages['sourceBuildByteIdentical']and packages['rebuiltFilesVerified']==69
assert visual['complete']and all(row(ROOT/f['file']['path'])==f['file']for f in visual['images'])
assert cleanup['scratchRemoved']and not cleanup['ownedBrowsersRemaining']and len(cleanup['services'])==4 and all(s['stopped']for s in cleanup['services'])
assert len(pc['services'])==2 and all(s['stopped']for s in pc['services'])and not Path(b['scratch']).exists()
assert not protection['changedProductionInputs']and len(build['productionInputs'])==97 and build['exitCode']==0
assert [row(ROOT/f['path'])for f in b['productionInputsBefore']]==build['productionInputs']
subprocess.run(['git','diff','--check'],cwd=ROOT,check=True)
snap=OUT/'after';snap.mkdir(exist_ok=False)
for name in ALLOWED:
 dest=snap/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,dest)
before=(OUT/'before/README.md').read_text();after=(ROOT/'README.md').read_text();(OUT/'README.diff').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='before/README.md',tofile='after/README.md')))
artifacts=[]
for key,a in delivery['artifacts'].items():
 target=Path(a['absolutePath']);assert sha(target)==a['sha256']and target.stat().st_size==a['bytes'];artifacts.append({k:a[k]for k in['absolutePath','bytes','sha256']})
for name in['manifest.json','SHA256SUMS']:
 target=Path(read(OUT/'delivery-config.json')['deliveryDirectory'])/name;artifacts.append({'absolutePath':str(target),'bytes':target.stat().st_size,'sha256':sha(target)})
copies=[('original',SOURCE/'index.html'),('public',ROOT/'public/experiments/bottle-ocean/index.html')]
assert all(sha(path)==ENTRY_SHA for _,path in copies)
candidate={'capturedAtShanghai':now(),'candidateId':delivery['candidateId'],'baseCommit':b['hostCommit'],'sourceCommit':b['sourceCommit'],'productionInputs':build['productionInputs'],'productionManifest':build['productionManifest'],'changedProductionInputs':[],'readmeBefore':row(OUT/'before/README.md'),'readmeAfter':row(snap/'README.md'),'sourceEntrySHA256':ENTRY_SHA,'originalCopiesIdentical':True,'buildAndArchiveCopiesVerifiedBy':['build-final.json','delivery-manifest.json','package-validation.json'],'cover':row(ROOT/'src/assets/bottle-ocean-cover.png'),'protectedHistory':protection['history'],'existingDistFilesUnchanged':65,'stage2SeparatelyExecuted':False,'gitCommittedThisStep':False,'gitPushedThisStep':False,'publishedThisStep':False,'externalArtifacts':artifacts}
write(OUT/'candidate-manifest.json',candidate);write(OUT/'protection-final.json',protection)
mapping={
 'S7-01':['baseline.json','protection-final.json','candidate-manifest.json'],
 'S7-02':['pair-conditions.json','functional-summary.json'],
 'S7-03':['functional-summary.json#/controlLedger'],
 'S7-04':['chromium-controls/browser.json','dynamic-analysis.json','original-physics-responsive-source.json'],
 'S7-05':['BUTTON.interface','INPUT.keyboard'],
 'S7-06':['BUTTON.qualities','SLIDER.pixelScale','visual-review.json'],
 'S7-07':['BUTTON.toggle-lighthouse','BUTTON.toggle-spray','BUTTON.toggle-dust'],
 'S7-08':['CAMERA.presets','CAMERA.pointer-reset','POINTER.picking'],
 'S7-09':['SANDBOX.props','SANDBOX.boundaries'],
 'S7-10':['PLAYBACK.pause','PLAYBACK.reset-all'],
 'S7-11':['chromium-dynamics/browser.json','dynamic-analysis.json'],
 'S7-12':['dynamic-analysis.json','visual-review.json'],
 'S7-13':['INPUT.keyboard','PACKAGE.core-flow'],
 'S7-14':['VIEW.phone','VIEW.landscape','VIEW.narrow','VIEW.resize'],
 'S7-15':['chromium-export-retest/browser.json','EXPORT.hidden','visual-review.json'],
 'S7-16':['firefox-controls/browser.json','firefox-actions/browser.json','webkit-controls/browser.json','webkit-actions/browser.json'],
 'S7-17':['PACKAGE.core-flow','../beach-bottle-boat-step-6/final-summary.json'],
 'S7-18':['build-final.json','PACKAGE.prefix','package-validation.json'],
 'S7-19':['delivery-manifest.json','package-validation.json','package-journey/browser.json'],
 'S7-20':['candidate-manifest.json','services-cleanup.json','package-preview-cleanup.json','sealed-documents','sealed-tests']}
summary={'completedAtShanghai':now(),'conclusion':'第七步完成：已验证范围内原功能配对保留，当前源码/成品包独立解压、重建及运行通过；不含上传或部署。','candidateId':delivery['candidateId'],'standardChecks':[{'id':id,'status':'通过（范围与原问题见报告）','records':records}for id,records in mapping.items()],'pairedFunctionalChecks':68,'byEngine':functional['byEngine'],'uniqueOriginalControls':34,'dynamicConditions':17,'packageJourneyChecks':2,'productionInputsUnchanged':97,'productionFiles':69,'historicalSealsVerified':13,'existingDistFilesUnchanged':65,'artifacts':artifacts,'limitations':functional['additionalLimits'],'firstAttemptsRetained':functional['firstAttemptsRetained'],'currentProductPathsAreNotSealTargets':True,'committed':False,'pushed':False,'deployed':False,'published':False}
write(OUT/'final-summary.json',summary)
standard=DOC/'step-7-standard.md';text=standard.read_text();old='状态：执行中。用户已授权第七步；执行前标准另存本步 standard-before.md。日期：2026-11-14（Asia/Shanghai）。不上传或发布。';assert old in text;standard.write_text(text.replace(old,'状态：已执行完成（已验证范围与限制见 step-7-verification.md）。执行前标准保存在本步 standard-before.md。日期：2026-11-14（Asia/Shanghai）。未上传或发布。',1))
for src,dest in[(TEST,OUT/'sealed-tests'),(DOC,OUT/'sealed-documents')]:
 dest.mkdir(exist_ok=False)
 for f in sorted(src.glob('*.py'if src==TEST else'step-7-*.md')):shutil.copyfile(f,dest/f.name)
files=[row(f)for f in sorted(OUT.rglob('*'))if f.is_file()and'__pycache__'not in f.parts and f.name!='evidence-manifest.json']
write(OUT/'evidence-manifest.json',{'sealedAtShanghai':now(),'candidateId':delivery['candidateId'],'files':files,'externalArtifacts':artifacts,'historicalSeals':protection['history']['seals'],'note':'Historical evidence and independent snapshots are sealed. Current product source/README paths are deliberately not seal targets; later authorized product edits do not rewrite this history.'})
print(json.dumps({'step7Complete':True,'sealedFiles':len(files),'pairedChecks':68,'controls':34,'independentPackages':2,'historicalSeals':13},ensure_ascii=False))
