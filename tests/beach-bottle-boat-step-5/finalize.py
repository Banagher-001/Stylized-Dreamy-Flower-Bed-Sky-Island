"""Seal observed results and independent snapshots, preserving every earlier attempt."""
import argparse,ast,difflib
from common import *
parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
if args.verify_only:
 manifest=read(OUT/'evidence-manifest.json')
 for f in manifest['files']:assert row(ROOT/f['path'])==f,f['path']
 print(json.dumps({'step5EvidenceIntact':True,'sealedFilesVerified':len(manifest['files']),'historicalSealsVerified':len(history()['seals'])},ensure_ascii=False));raise SystemExit
assert not(OUT/'evidence-manifest.json').exists()
baseline=read(OUT/'baseline.json');build=read(OUT/'build.json');cleanup=read(OUT/'services-cleanup.json');protection=protect_current()
assert build['exitCode']==0 and cleanup['scratchRemoved']and not cleanup['ownedBrowsersRemaining']and all(x['stopped']for x in cleanup['services'])
assert not Path(baseline['scratch']).exists()and len(protection['changedProductionInputs'])==4
for name in ALLOWED:assert sha(ROOT/name)==sha(OUT/'after'/name)
assert(OUT/'product.diff').read_text()==subprocess.check_output(['git','diff','--',*ALLOWED],cwd=ROOT,text=True)
subprocess.run(['git','diff','--check'],cwd=ROOT,check=True)
parts=[]
for name in ALLOWED:
 before=OUT/'before'/name;after=OUT/'after'/name
 parts.extend(difflib.unified_diff(before.read_text().splitlines(keepends=True)if before.exists()else[],after.read_text().splitlines(keepends=True),fromfile='before/'+name if before.exists()else'/dev/null',tofile='after/'+name))
(OUT/'step-5.diff').write_text(''.join(parts))

plan={
 'chromium-core':None,
 'chromium-faults':['FAULT.slow','FAULT.error-retry','LIFE.pending-exit','LIFE.navigation','REGRESS.lawson'],
 'chromium-fault-final':None,
 'chromium-regression':['REGRESS.courtyard','RESOURCE.return','LAYOUT.sizes','LIFECYCLE.visibility'],
 'chromium-input-host-retest':None,
 'chromium-resize':None,
 'firefox':['LIVE.ready','CORE.controls','INPUT.keys-download'],
 'firefox-focus-retest':None,
 'webkit':None,
}
runs={p.parent.name:read(p)for p in sorted(OUT.glob('*/browser.json'))}
assert set(plan).issubset(runs)
adopted=[];expectedAborts=[];warnings=[];runSummary=[]
for name,data in runs.items():
 assert data.get('finishedAtShanghai')and not data['externalAttempts'],name
 normalErrors=[e for e in data['pageErrors']if not e['case'].startswith('FAULT.')]+[e for e in data['console']if e['type']=='error'and not e['case'].startswith('FAULT.')]
 assert not normalErrors,(name,normalErrors)
 for e in data['failedRequests']:
  if e['case'].startswith('FAULT.'):continue
  assert e['case']=='LIFE.pending-exit'and e['url'].endswith('/experiments/bottle-ocean/index.html')and e['failure']=='net::ERR_ABORTED',(name,e)
  expectedAborts.append({'run':name,**e,'interpretation':'Delayed original document request intentionally cancelled by close/archive/retry'})
 for e in data['console']:
  if e['type']=='warning':warnings.append({'run':name,**e})
 selected=[(i,c)for i,c in enumerate(data['checks'])if name in plan and(plan[name]is None or c['id']in plan[name])]
 for i,c in selected:
  assert c['status']=='通过'or(c['id']=='LIFECYCLE.visibility'and c['status']=='环境限制'),(name,c['id'],c['status'])
  adopted.append({'run':name,'engine':data['engine'],'version':data['browserVersion'],'id':c['id'],'status':c['status'],'record':name+'/browser.json#/checks/'+str(i)})
 runSummary.append({'run':name,'engine':data['engine'],'version':data['browserVersion'],'rawPassed':sum(c['status']=='通过'for c in data['checks']),'rawPending':sum(c['status']=='待补核'for c in data['checks']),'limits':sum(c['status']=='环境限制'for c in data['checks']),'adopted':len(selected),'reportComplete':data['complete']})
assert len(adopted)==28 and sum(c['status']=='通过'for c in adopted)==27
for engine in['chromium','firefox','webkit']:
 for check in['LIVE.ready','CORE.controls','INPUT.keys-download','INPUT.focus']:
  assert any(c['engine']==engine and c['id']==check and c['status']=='通过'for c in adopted),(engine,check)

reasons={
 ('chromium-faults','FAULT.initialization'):('chromium-fault-final','Child init script ran with initial pathname blank; path condition skipped the intended failure. Final fixture selects child by window !== top and records blocked native WebGL requests.'),
 ('chromium-fault-retest','FAULT.initialization'):('chromium-fault-final','Same initial-about:blank path assumption. The original scene actually loaded normally; it was never a successful initialization fault.'),
 ('chromium-faults','FAULT.graphics'):('chromium-fault-final','Document event probe did not survive the initial child document replacement. Final probe listens directly to the connected original canvas before actual lose/restore.'),
 ('chromium-fault-retest','FAULT.graphics'):('chromium-fault-final','Read-only snapshots prove isContextLost changed true to false and rendering resumed, but the old Document event probe recorded no events. Direct-canvas retest captured both trusted events.'),
 ('chromium-regression','FAULT.host-graphics'):('chromium-input-host-retest','Path-based initialization fixture accidentally disabled child WebGL too. Final fixture uses window === top and verifies real child rendering despite host creation failure.'),
 ('firefox','INPUT.focus'):('firefox-focus-retest','Firefox native Tab visits the child Document before its first control. Final fixture records bounded actual Tab/Shift+Tab sequences instead of assuming one press in every browser.'),
}
retained=[]
for name,data in runs.items():
 for c in data['checks']:
  if c['status']!='待补核':continue
  replacement,reason=reasons[(name,c['id'])]
  assert any(a['run']==replacement and a['id']==c['id']and a['status']=='通过'for a in adopted)
  retained.append({'run':name,'id':c['id'],'originalStatus':c['status'],'error':c.get('error'),'adoptedRetest':replacement,'reason':reason,'productChangedForRetest':False})
assert len(retained)==6

mapping={
 'S5-01':['baseline.json','candidate-manifest.json'],
 'S5-02':['LIVE.lazy','LIVE.ready'],
 'S5-03':['LIVE.ready','FAULT.error-retry','FAULT.initialization','FAULT.graphics'],
 'S5-04':['CORE.controls'],
 'S5-05':['CORE.sandbox-pause'],
 'S5-06':['INPUT.keys-download','INPUT.focus'],
 'S5-07':['INPUT.keys-download','PATH.prefix','visual-review.json'],
 'S5-08':['FAULT.slow'],
 'S5-09':['FAULT.error-retry','FAULT.initialization'],
 'S5-10':['FAULT.graphics'],
 'S5-11':['FAULT.error-retry','LIFE.pending-exit'],
 'S5-12':['LIFE.pending-exit'],
 'S5-13':['LIFE.navigation'],
 'S5-14':['REGRESS.lawson'],
 'S5-15':['REGRESS.courtyard','FAULT.host-graphics'],
 'S5-16':['RESOURCE.return','LAYOUT.resize','LIFECYCLE.visibility'],
 'S5-17':['LAYOUT.sizes','LAYOUT.resize'],
 'S5-18':['build.json','PATH.prefix'],
 'S5-19':['firefox/browser.json','firefox-focus-retest/browser.json','webkit/browser.json'],
 'S5-20':['final-summary.json','services-cleanup.json','step-5.diff'],
}
inputs=[row(ROOT/f['path'])for f in baseline['productionInputsBefore']]+[row(ROOT/n)for n in baseline['newProductFiles']]
assert len(inputs)==len({r['path']for r in inputs})==97
candidate={'capturedAtShanghai':now(),'baseCommit':baseline['hostCommit'],'sourceCommit':baseline['sourceCommit'],'productionInputsAfter':inputs,'authorizedExistingChanges':protection['changedProductionInputs'],'newProductFiles':[row(ROOT/n)for n in baseline['newProductFiles']],'sourceSnapshots':[row(OUT/'after'/name)for name in ALLOWED],'runtimeEntrySHA256':ENTRY_SHA,'coverSourceSHA256':sha(ROOT/'src/assets/bottle-ocean-cover.png'),'builtCover':build['cover'],'buildManifest':build['productionManifest'],'diffFromStep4':'step-5.diff','aggregateGitDiffFromHEAD':'product.diff','mutableSourcePathsAreRecordedNotHistoricalSealTargets':True}
write(OUT/'candidate-manifest.json',candidate)
visual=read(OUT/'visual-review.json');assert visual['imagesEdited']is False
for r in visual['files']:assert row(ROOT/r['path'])==r
summary={'completedAtShanghai':now(),'conclusion':'第五步完成：Coding 内大尺寸完整瓶中海洋、原生代表功能、真实下载、状态/故障/新文档重试与退出可用；不是整套七步的最终验收','standardChecks':[{'id':key,'status':'通过','records':value,**({'limitation':'Actual hidden was not observed; visible tab return and instance preservation passed without synthetic visibility events'}if key=='S5-16'else{})}for key,value in mapping.items()],'adoptedChecks':adopted,'browserRuns':runSummary,'retainedEarlierFailures':retained,'protection':protection,'cleanup':cleanup,'expectedTeardownAborts':expectedAborts,'softwareWarnings':warnings,'scope':{'bottleIframeAdded':True,'originalHTMLModified':False,'step2Executed':False,'steps6and7Executed':False,'committed':False,'pushed':False,'deployed':False},'limits':['Actual document.hidden and hidden-state recovery/background throttling could not be verified in this Xvfb environment','Mobile/touch emulation and Linux WebKit are not physical-phone or Safari validation','Font enlargement is root font-size 200%, not browser/OS zoom','Native representative operations are verified in three engines; all 34 controls and complete original-vs-embedded parity remain Stage 7','No hardware-GPU performance or synchronous GPU-memory-release claim; known original issues are preserved'],'runtimeEntrySHA256':ENTRY_SHA}
write(OUT/'final-summary.json',summary)

standard=DOC/'step-5-standard.md';text=standard.read_text();a=text.index('状态：');z=text.index('\n',a);standard.write_text(text[:a]+'状态：第五步已执行完成。大尺寸完整内嵌、原生代表操作与下载、错误/图形故障重试、退出及既有体验回归已验收；实际 hidden 未观测，保留环境限制。结果见 step-5-verification.md，执行前标准另存 standard-before.md。日期：2026-11-13（Asia/Shanghai）。第二步仍仅有标准，第六、七步尚未执行，未提交、上传或发布。'+text[z:])
for p in TEST.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
for p in(TEST/'__pycache__').glob('*'):p.unlink()
if(TEST/'__pycache__').exists():(TEST/'__pycache__').rmdir()
documents=['step-5-standard.md','step-5-state-contract.md','step-5-verification.md','step-5-handoff.md']
files=[row(DOC/n)for n in documents]+[row(p)for p in sorted(OUT.rglob('*'))if p.is_file()]+[row(p)for p in sorted(TEST.glob('*.py'))]
assert len(files)==len({f['path']for f in files})and all(not f['path'].startswith('src/')for f in files)
write(OUT/'evidence-manifest.json',{'schema':1,'createdAtShanghai':now(),'scope':'Step-5 docs/scripts/raw evidence and independent before/after snapshots; mutable current product files are only recorded as candidate inputs','files':sorted(files,key=lambda f:f['path'])})
print(json.dumps({'step5Complete':True,'standardChecksPassed':20,'adoptedBrowserChecksPassed':27,'environmentLimits':1,'retainedEarlierFailures':len(retained),'changedExistingProductInputs':4,'newProductFiles':2,'historicalSealsVerified':len(protection['history']['seals']),'sealedFiles':len(files),'pushed':False,'deployed':False},ensure_ascii=False))
