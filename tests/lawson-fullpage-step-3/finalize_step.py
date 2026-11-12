"""Assemble verified migration evidence and seal only this step's outputs."""
from pathlib import Path
import hashlib,json,re,subprocess
from runtime_files import ROOT,OUT,SOURCE,PUBLIC,BUILT,manifest,verify,write,read,sha,now

DOC=ROOT/'docs/lawson-fullpage';TEST=ROOT/'tests/lawson-fullpage-step-3'
baseline=read(OUT/'baseline.json');prior=read(ROOT/baseline['priorBaseline']);m=manifest();time=now()
assert sha(ROOT/baseline['priorBaseline'])==baseline['priorBaselineSHA256']
build=read(OUT/'build-1-result.json');assert build['exitCode']==0 and build['typecheckIncluded']and build['publicVerifiedBeforeBuild']
http=read(OUT/'http-verification.json');assert http['passed']and all(v['all46Correct']for v in http['routes'].values())
assert len(http['negativeControls'])==4
runs={run:read(OUT/run/'browser.json')for run in ['run-1','run-2']}
assert runs['run-2']['passed']and not any(runs['run-2'][k]for k in ['pageErrors','httpErrors','failedRequests','externalRequests'])
selected={
    'root.load':'run-2','root.time':'run-1','root.sign':'run-1','root.camera':'run-1','root.roof':'run-1','root.traffic':'run-1',
    'root.network-bytes':'run-2','project.load':'run-2','project.ui':'run-1','project.network-bytes':'run-2',
}
accepted={}
for identifier,run in selected.items():
    row=next(c for c in runs[run]['checks']if c['id']==identifier);assert row['passed']
    accepted[identifier]={'from':run+'/browser.json','check':row}
assert not runs['run-1']['httpErrors']and not runs['run-1']['failedRequests']and not runs['run-1']['externalRequests']
assert all(e['text']=="Cannot read properties of null (reading 'classList')"and '/Stylized-Dreamy-Flower-Bed-Sky-Island/'in e['url']for e in runs['run-1']['pageErrors'])
for identifier in ['root.network-bytes','project.network-bytes']:
    assert accepted[identifier]['check']['evidence']['actualResponsesMatchingManifest']==46
write(OUT/'browser-accepted.json',{'passed':True,'acceptedChecks':accepted,'diagnosticsPreserved':'run-1/browser.json',
    'diagnosticInterpretation':'Root original UI cases passed. One original-loader removal assumption raised a UtilityScript error in the project-path helper; two body reads exceeded the default inspector cache. Run-2 corrects only the helper/null guard and observer buffers; runtime files were not changed.',
    'correctedRecheck':'run-2/browser.json','unclassifiedSceneErrors':[]})

integrity={'capturedAtShanghai':time,'sourceRuntimeFilesUnchanged':46,'newPublicRuntimeFiles':46,'builtRuntimeFiles':46,'protectedInputs':{},'oldSeals':[]}
for directory in [SOURCE,PUBLIC,BUILT]:verify(directory,m,exact=directory!=SOURCE)
for name,root in [('source',ROOT.parent/'luosen-asset'),('host',ROOT)]:
    b=prior[name]
    for f in b['runtimeInputs']:
        p=root/f['path'];assert p.stat().st_size==f['bytes']and sha(p)==f['sha256'],f['path']
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    changes=subprocess.check_output(['git','diff','HEAD','--name-only'],cwd=root,text=True).strip()
    assert head==b['head']and not changes
    integrity['protectedInputs'][name]={'head':head,'filesVerified':len(b['runtimeInputs']),'trackedChanges':changes,'unchanged':True}
for seal in baseline['oldSeals']:
    p=ROOT/seal['path'];assert sha(p)==seal['sha256']
    previous=read(p)
    for f in previous['files']:
        q=ROOT/f['path'];assert q.stat().st_size==f['bytes']and sha(q)==f['sha256'],f['path']
    integrity['oldSeals'].append({**seal,'unchanged':True})
for f in baseline['distBefore']:
    p=ROOT/'dist'/f['path'];assert p.is_file()and p.stat().st_size==f['bytes']and sha(p)==f['sha256']
integrity['existingHostBuildFilesUnchanged']=len(baseline['distBefore'])
integrity['standardStatusUpdate']={'beforeSHA256':baseline['standardSHA256Before'],'afterSHA256':sha(DOC/'step-3-standard.md'),'reason':'Update only third-step completion status and report link; not a prior sealed file.'}
integrity['stagingDirectoriesRemaining']=[str(p)for p in PUBLIC.parent.glob('.lawson-step3-stage-*')]
assert not integrity['stagingDirectoriesRemaining']
assert read(OUT/'cleanup.json')['complete']
integrity['passed']=True;write(OUT/'integrity.json',integrity)

handoff={'schema':1,'completedStep':3,'nextStep':4,'capturedAtShanghai':time,'sourceCommit':baseline['sourceHead'],'hostCommit':baseline['hostHead'],
    'publicRoot':'public/experiments/lawson','builtRoot':'dist/experiments/lawson','entryPath':'experiments/lawson/index.html',
    'runtimeFiles':46,'runtimeBytes':m['runtimeBytes'],'threeWayManifest':'docs/evidence/lawson-fullpage-step-3/source-public-dist.json',
    'runtimeManifestSHA256':baseline['runtimeManifestSHA256'],'designContract':'docs/evidence/lawson-fullpage-step-2/design-contract.json',
    'projectIds':['lawson','courtyard'],'defaultProjectId':'lawson','openSignature':'open(projectId, tab, trigger?)',
    'urlRule':'Resolve entryPath against the Vite site base. One resolver for iframe and independent open. No localhost or private GitHub URLs in product data.',
    'verifiedDeploymentPrefixes':['/','/Stylized-Dreamy-Flower-Bed-Sky-Island/'],
    'sourceHasExistingReadyErrorSignals':True,'newBridgeInjected':False,
    'hostUIImplemented':False,'actualIframeIntegrationImplemented':False,
    'remaining':{'step4':'Host entry, project identity, dialog, focus, garden rendering and reading restoration','step5':'Mount original iframe, original ready/error/retry, permissions and cleanup','step6':'Devices and failure/rapid-open cases','step7':'Full original vs integrated parity regression'},
    'knownIssues':'docs/lawson-fullpage/original-issues.md','statusInGit':'New working-tree files; not committed, pushed or published'}
write(OUT/'step-4-handoff.json',handoff)

root_e=accepted['root.load']['check']['evidence'];project_e=accepted['project.load']['check']['evidence']
check_rows='\n'.join(f'| `{identifier}` | 通过 | [{run}](../evidence/lawson-fullpage-step-3/{run}/browser.json) |'for identifier,run in selected.items())
verification=f'''# 第三步验收：原网页迁入、构建一致性与独立运行

**第三步已完成。** 罗森原网页已作为真实运行资源进入主站，构建后的原页面在根目录和项目子目录均能独立运行。正式 Coding 入口、作品外层和 iframe 仍由第四、第五步实现。

完成时间：{time}（Asia/Shanghai）。

## 实际新增及版本

- 原版本：`95dad9881a7b9d31c0ac635f1f335055d8cb3cc4`；主站 HEAD 仍为 `4a6dd7c5c9c126ab3b9319fab5d8ea16a704dae8`。
- 新增 `public/experiments/lawson/`，46 个运行文件、20,332,784 字节。原 HTML、CSS、JS、import map、本地 Three.js r160 与模型内容均未改写。
- 四个 GLB 共 18,648,040 字节，保留商店及 A/B/C 三辆车。
- 构建生成 `dist/experiments/lawson/`，同一套 46 个文件与源/public 全部逐字节一致。
- 既有主站源码、配置、依赖和 91 个监测输入未变，原 dist 的 18 个主站文件也与执行前一致。
- 当前新增内容保存在工作区，尚未提交、推送 GitHub 或发布网站。

见 [三方文件表](../evidence/lawson-fullpage-step-3/source-public-dist.json)、[复制记录](../evidence/lawson-fullpage-step-3/copy-verification.json)。

## 构建结果

Node {baseline['nodeVersion']}、npm {baseline['npmVersion']}，使用已有匹配依赖，未重装或修改 package/锁文件。迁入后执行 `npm run build`，包含 `tsc --noEmit`；退出码 0。

本步采用 [build-1.log](../evidence/lawson-fullpage-step-3/build-1.log) 及 [构建结果](../evidence/lawson-fullpage-step-3/build-1-result.json)，该次构建前已验证 public 文件完整。

## 实际构建输出的 HTTP 核查

同一份 dist 通过临时本机静态服务分别映射为：

| 模式 | 页面路径 | 结果 |
|---|---|---|
| 根目录 | `/experiments/lawson/index.html` | 原页真实就绪及首帧通过 |
| 项目子目录 | `/Stylized-Dreamy-Flower-Bed-Sky-Island/experiments/lawson/index.html` | 原页真实就绪及首帧通过 |

两种前缀共 92 个运行资源 URL 的状态、字节长度和 MIME 检查通过；两份主站首页可访问且与实际构建一致。4 个缺失资源对照返回预期 404，未将其混入正常页面错误。

浏览器实际接收的每种路径下全部 46 个响应内容也已逐项计算 SHA256，与源文件一致；不是只检查 HTTP 200。正常浏览器请求没有 HTTP 错误、请求失败或外部依赖。

见 [HTTP 核查](../evidence/lawson-fullpage-step-3/http-verification.json) 与 [采用的浏览器证据](../evidence/lawson-fullpage-step-3/browser-accepted.json)。测试服务已停止，本机测试端口不是发布地址。

## 就绪、默认状态与首帧

环境为 Chromium {runs['run-2']['browserVersion']}、专用 Xvfb :109、Mesa llvmpipe LLVM 19.1.7 软件 WebGL2、LP_NUM_THREADS=3。两种路径串行核查，初始视口 1440×900、DPR 1。

确认原 ready 为 true、error 为空、body ready 为 1，原 fatal 未显示，实际 GL 绘制发生并取得场景截图。原黄昏 18.5、8 组灯光开启、控制台展开、屋顶可见、漫游关闭、初始相机位置及 orbit UI 状态均符合基线；3 辆车、2 名店员、17 类交互入口与 41 控件结构仍在，原自动车流启动。

从导航到完成默认记录的墙钟约为根目录 {root_e['readySeconds']:.2f} 秒、项目目录 {project_e['readySeconds']:.2f} 秒，只描述本次本机条件，不是线上加载或硬件性能承诺。原默认画质和自适应变化如实记录；根目录操作抽查随后经原设置按钮选择 low、960×540，未修改原默认配置。

- [根目录默认原页](../evidence/lawson-fullpage-step-3/run-2/root-default-original.png)
- [项目目录默认原页](../evidence/lawson-fullpage-step-3/run-2/project-default-original.png)
- [夜景](../evidence/lawson-fullpage-step-3/run-1/root-time-night.png)
- [黄昏恢复](../evidence/lawson-fullpage-step-3/run-1/root-time-dusk.png)

## 原 UI 操作抽查

| 条目 | 结论 | 采用来源 |
|---|---|---|
{check_rows}

时间按钮切夜晚再回黄昏；招牌开关观察原灯光和发光材质实际变化；相机按钮到正面再回全景；屋顶按钮核对原 roofRoot 可见性；原车 A 按钮、暂停和恢复核对实时位置及车轮。暂停期间绘制帧仍增加，说明不是通过停止测试进程制造静止。项目子路径的原控制台收起/展开也有实际反馈。

观察包装以原实参调用原灯光函数一次，时钟和场景文件不变。车辆使用 getVehicleState 而非 UI 位置缓存。原控件完整保全不等于本步重新穷举了 41 控件及 17 类点击；最终集成对照留给第七步。

## 诊断、修正和原问题

早期复制工具错误地要求整个源目录仅有运行文件，因源目录还有截图、报告与启动辅助文件而拒绝复制。已修正为源端按清单子集校验，目标和构建目录仍严格等于 46 文件；没有扩大复制范围。最初命令随后执行的构建发生在复制前，只保留作诊断，未作为迁入验收。工具已加入迁入校验前置条件，正式构建为 build-1。

浏览器 run-1 中原按钮抽查通过，但响应内容读取超过默认调试缓存，且项目路径的加载等待表达式未兼容原页移除 loader，产生测试 UtilityScript 空引用。原页面已 ready，原控制台没有场景脚本错误。run-2 使用专用 64MB/32MB 调试缓存并修正空节点判断，仅补核两条加载及网络内容项，四项全部通过、未捕获脚本异常为 0。未修改运行代码或时钟来通过检查，所有原记录和当时脚本保留。

原版 R、碰撞、N、车体点击说明、手机布局及动画暂停语义等继续按 [原问题表](original-issues.md) 留档。真实手机、其他浏览器、真实后台隐藏和硬件 GPU 性能未在本步新增验证；真实 iframe 权限、Esc、输入隔离、主庭院停绘和返回由后续步骤核对。

## 完整性与交接

源 46 文件、主站原 91 输入及历史 77/109/115 三组封存均未变化。仅新增真实运行目录与本步资料，构建产物按既有流程生成。测试浏览器、专用服务器、虚拟显示器和本步备份目录已清理。

- [完整性](../evidence/lawson-fullpage-step-3/integrity.json)
- [第四/第五步交接](step-3-handoff.md)
- [机器交接](../evidence/lawson-fullpage-step-3/step-4-handoff.json)
- [独立封存](../evidence/lawson-fullpage-step-3/evidence-manifest.json)

第三步到此完成：完整原网页已在项目内，并可从真实构建产物独立运行。正式网站里的作品入口及大尺寸嵌入继续按既定步骤实施。
'''
(DOC/'step-3-verification.md').write_text(verification)

docs=[DOC/('step-3-'+name+'.md')for name in ['standard','handoff','verification']]
broken=[]
for p in docs:
    for link in re.findall(r'\[[^\]]*\]\(([^)]+)\)',p.read_text()):
        if '://'in link:continue
        target=(p.parent/link.split('#')[0]).resolve()
        if not target.exists()and target!=OUT/'evidence-manifest.json':broken.append({'file':str(p),'link':link})
assert not broken,broken
summary={'schema':1,'complete':True,'step':3,'capturedAtShanghai':time,'newRuntimeFiles':46,'runtimeBytes':m['runtimeBytes'],'buildPassed':True,
    'sourcePublicDistAllMatch':True,'httpRuntimeURLsVerified':92,'browserBodyHashesVerified':92,'acceptedBrowserChecks':10,
    'rootAndProjectPageReady':True,'existingHostBuildFilesUnchanged':18,'existingHostInputsUnchanged':91,'oldSealFilesUnchanged':[77,109,115],
    'actualIframeIntegrationImplemented':False,'hostCodingUIImplemented':False,'committed':False,'pushed':False,'published':False,
    'runtimeEntryPath':'experiments/lawson/index.html','nextStepHandoff':'docs/evidence/lawson-fullpage-step-3/step-4-handoff.json'}
write(OUT/'summary.json',summary)
write(OUT/'validation.json',{'passed':True,'brokenDocumentationLinks':broken,'selectedBrowserChecks':10,'threeWayFiles':46,'oldSealsUnchanged':True,'publicRuntimeAdded':True,'sourceAndExistingHostPreserved':True})
files=[]
for p in [*docs,*sorted(OUT.rglob('*')),*sorted(TEST.rglob('*')),*sorted(PUBLIC.rglob('*'))]:
    if not p.is_file()or '__pycache__'in p.parts or p==OUT/'evidence-manifest.json':continue
    files.append({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p)})
assert len(files)==len({f['path']for f in files})
write(OUT/'evidence-manifest.json',{'schema':1,'auditId':'lawson-fullpage-step-3','createdAtShanghai':time,'sourceCommit':baseline['sourceHead'],'hostCommit':baseline['hostHead'],
    'previousSeals':baseline['oldSeals'],'selfExcluded':True,'fileCount':len(files),'totalBytes':sum(f['bytes']for f in files),'includesNewPublicRuntime':True,'files':files})
print(json.dumps({'step3Complete':True,'runtimeFiles':46,'httpURLsVerified':92,'browserBodiesVerified':92,'acceptedChecks':10,'sealedFiles':len(files),'sourceAndExistingHostChanged':False},ensure_ascii=False))
