"""Seal the new step-3 delivery without modifying earlier records or deployed code."""
import argparse,ast,struct
from common import *
parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
if args.verify_only:
 data=read(OUT/'evidence-manifest.json')
 for f in data['files']:assert row(ROOT/f['path'])==f,f['path']
 print(json.dumps({'sealedFilesVerified':len(data['files']),'step3DeliveryIntact':True},ensure_ascii=False));raise SystemExit
assert not(OUT/'evidence-manifest.json').exists()
protection=protect_current();baseline=read(OUT/'baseline.json');build=read(OUT/'build.json');b=read(OUT/'browser/browser.json');cleanup=read(OUT/'services-cleanup.json');services=read(OUT/'services-started.json');copied=read(OUT/'copied-files.json')
assert build['exitCode']==0 and b['complete']and len(b['checks'])==17
assert all(c['status']=='通过'for c in b['checks'])
assert not b['pageErrors']and not b['externalAttempts']and not b['failedRequests']and not b['httpErrors']and not[x for x in b['console']if x['type']=='error']
assert cleanup['startupCompleted']and cleanup['scratchRemoved']and not cleanup['ownedBrowsersRemaining']and len(cleanup['services'])==3 and all(s['stopped']for s in cleanup['services'])
assert not Path(baseline['scratch']).exists()
checks={c['id']:c for c in b['checks']}
old={f['path'].removeprefix('dist/'):f['sha256']for f in baseline['existingDistFiles']};new={f['path']:f['sha256']for f in build['productionManifest']};assert all(new.get(k)==v for k,v in old.items())
runtime=[]
for name in['index.html','THIRD_PARTY_NOTICES.md','SOURCE.md']:
 p=RUNTIME/name;item={**row(p),'role':'complete-original-webpage'if name=='index.html'else'original-third-party-notices'if name=='THIRD_PARTY_NOTICES.md'else'new-source-and-running-notes','production':next(r for r in build['runtimeFiles']if r['name']==name)['production']}
 assert item['sha256']==item['production']['sha256']
 if name!='SOURCE.md':assert sha(SOURCE/name)==item['sha256'];item['origin']={'repository':'https://github.com/Banagher-001/Beach-Bottle-Boat','commit':baseline['sourceCommit'],'path':name}
 runtime.append(item)
assert sha(RUNTIME/'index.html')==ENTRY_SHA
assert row(COVER)=={k:v for k,v in copied['cover'].items()if k in['path','bytes','sha256']}
raw=COVER.read_bytes();assert struct.unpack('>II',raw[16:24])==(1920,1080)
assert not any('bottle-ocean-cover'in f['path']for f in build['productionManifest'])
manifest={'schema':1,'capturedAtShanghai':now(),'projectId':'bottle-ocean','displayName':'瓶中海洋','entryPath':'experiments/bottle-ocean/index.html','sourceCommit':baseline['sourceCommit'],'sourceHTMLUnmodified':True,'runtimeFiles':runtime,'cover':copied['cover'],'coverReferencedByHost':False,'sourceDependenciesAddedToHost':False,'originalRebuilt':False}
write(OUT/'runtime-manifest.json',manifest)
write(OUT/'visual-review.json',{'reviewedAtShanghai':now(),'method':'Assistant viewed both actual downloaded PNGs using view_image','files':[row(OUT/'browser/production-download.png'),row(OUT/'browser/prefix-download.png')],'observed':'Both show the rendered bottle, ship, water and terrain; no blank/error frame or DOM control panel. Prefix export is the original top camera view.','imageEdited':False})
notes={'rawReportsPreserved':True,'diagnosticCorrection':'The initial browser report populated nativeModeToggleUsed unconditionally. That field is not used as evidence of a click or as an acceptance condition. Actual stable readingMode, visible/enabled Coding controls, requests, no iframe and no host API assertions support HOST.* results. The script flag is now conditional; saved browser.py.txt preserves the exact executed version. Assertions and tested product are unchanged.','testsRepeated':False}
write(OUT/'report-notes.json',notes)
mapping={'S3-01':['baseline.json','standard-before.md'],'S3-02':['copied-files.json','runtime-manifest.json'],'S3-03':['runtime-manifest.json'],'S3-04':['HTTP.dev','DEV.load'],'S3-05':['build.json'],'S3-06':['HTTP.production'],'S3-07':['HTTP.prefix','PREFIX.load','PREFIX.reload'],'S3-08':['PRODUCTION.motion','PRODUCTION.camera-ui','PRODUCTION.sandbox','PRODUCTION.export'],'S3-09':['PREFIX.motion','PREFIX.camera-ui','PREFIX.export'],'S3-10':['browser/browser.json'],'S3-11':['HOST.dev','HOST.production','HOST.prefix'],'S3-12':['services-cleanup.json','final-summary.json']}
summary={'completedAtShanghai':now(),'conclusion':'第三步完成：完整原页与封面已保存在工作区，通过主站构建和独立访问/代表操作验证；尚未接入Coding或iframe，未提交上传发布','standardChecks':[{'id':k,'status':'通过','records':v}for k,v in mapping.items()],'browserAndHTTPChecks':[{'id':c['id'],'name':c['name'],'status':c['status'],'record':'browser/browser.json#/checks/'+str(i),'sourceEntrySHA256':ENTRY_SHA}for i,c in enumerate(b['checks'])],'buildExitCode':0,'existingProductionFilesIdentical':len(old),'newProductionRuntimeFiles':3,'originalProtected':protection,'runtime':manifest,'cleanup':cleanup,'browser':{'name':b['browser'],'version':b['browserVersion'],'softwareRenderer':checks['PRODUCTION.load']['evidence']['default']['gl']},'scope':{'codingEntryAdded':False,'iframeIntegrated':False,'step2Executed':False,'hostBusinessCodeChanged':False,'committed':False,'pushed':False,'deployed':False},'limits':['Representative copied-page checks in Linux Chromium only; step-1 Firefox/WebKit scope stays as recorded','Physical phones, hardware performance and actual hidden-state resume remain unverified','Full iframe input/lifecycle and host/Lawson regression belong to later steps','Known original brightness, camera inertia and WebGL-failure issues remain unchanged'],'diagnosticNotes':notes}
write(OUT/'final-summary.json',summary)
standard=DOC/'step-3-standard.md';text=standard.read_text();start=text.index('状态：');end=text.index('\n',start);text=text[:start]+'状态：第三步已执行完成。原成品、第三方说明与真实封面已保存，构建、根/子路径独立访问及代表操作通过；验收见 step-3-verification.md。执行前标准保存在本步证据 standard-before.md。日期：2026-11-13（Asia/Shanghai）。第二步仍仅有标准；本步未接通 Coding 或 iframe，未上传或发布。'+text[end:];standard.write_text(text)
motion_root=checks['PRODUCTION.motion']['evidence'];motion_prefix=checks['PREFIX.motion']['evidence'];downloads=[checks[n]['evidence']for n in['PRODUCTION.export','PREFIX.export']]
lines=['# 第三步验收：完整资源保存与独立访问','','第三步完成。新增完整原网页、第三方声明、来源说明和真实封面；主站构建及 17 项 HTTP/浏览器检查通过，12 项执行标准均有结果。未添加 Coding 入口或 iframe，未提交、上传或部署。第二步目前仍仅有已细化标准。日期：2026-11-13（Asia/Shanghai）。','','| 交付 | 位置 / 结果 |','|---|---|','| 完整网页 | public/experiments/bottle-ocean/index.html，1,979,264 字节，与固定原版一致 |','| 第三方说明 | public/experiments/bottle-ocean/THIRD_PARTY_NOTICES.md，按原字节保存 |','| 来源和运行说明 | public/experiments/bottle-ocean/SOURCE.md |','| 真实封面候选 | src/assets/bottle-ocean-cover.png，1920×1080，复制原截图，无编辑；第四步再引用 |','| 运行入口 | experiments/bottle-ocean/index.html |','','原提交 d94c1f911a39143fd8f5efe152b99a87fdc53184；HTML SHA256 为 941feb2ea6ddd3cc93aad5b0b92dbca52ee66a3e1098fee0dbf16f01ca63d1ef。原 HTML 没有重新构建、压缩、替换引擎或注入主站业务。逐文件来源与摘要见 [runtime-manifest.json](../evidence/beach-bottle-boat-step-3/runtime-manifest.json)。','','构建与路径：','','- 使用现有 npm run build，包含 tsc --noEmit 和 Vite 8.3.5，退出码 0。输出至本步专用临时目录，原 dist 未覆盖。Vite 关于 outDir 位于根目录外且不会清空的提示符合预期；目录由本步独占创建。','- 原仓库、公有目录、生产产物和开发/生产 HTTP 正文的 HTML SHA256 均一致。第三方说明原样保留，SOURCE.md 同样复制到产物。',f'- 新生产产物共 {len(build["productionManifest"])} 个文件，其中原有 {len(old)} 个生产文件与现有 dist 对应文件全部字节一致，仅新增 3 个独立资源文件。未引用的封面没有进入主站 bundle。','- 下表为本机验收地址，测试服务已停止，不是当前公网地址：','','| 条件 | 当时入口 | 结果 |','|---|---|---|',f'| 开发 | {services["devOrigin"]}/{entry if False else "experiments/bottle-ocean/index.html"} | 正确正文、完整默认场景 |',f'| 生产根路径 | {services["productionOrigin"]}/experiments/bottle-ocean/index.html | 正确正文、完整默认场景及代表操作 |',f'| 生产子路径 | {services["productionOrigin"]}/portfolio-check/experiments/bottle-ocean/index.html | 实际前缀挂载，正文、刷新、代表操作均通过 |','','生产前缀由严格静态服务器实际映射同一份相对 base 构建产物；没有用主页 200 回退代替正确原页。9 个静态文件响应逐份比较正文摘要。测试浏览器使用新上下文、路由禁用缓存及阻断外部 HTTP；外部请求尝试为 0。','','实际运行与下载：','',f'- Linux Chromium {b["browserVersion"]}，WebGL2 使用 ANGLE/Mesa llvmpipe；软件渲染不代表真机或硬件性能。开发/生产根路径为 1280×720、DPR1；前缀原页为 960×600、DPR2。先记录原 fine 默认画面，再通过原画质按钮使用 retro 做代表操作。','- 原场景实际绘制，3 根桅杆、完整地形、海岸、外海、玻璃、天空与灯塔均有对象和画面证据；12 滑杆、22 按钮与第一步一致。','- 原生键盘将波高从 0 改至 100，连续观察自然模拟与水面/船体，未写时钟、dt 或姿态：','','| 条件 | 实际模拟秒 | 连续不同模拟帧 | 水面高度峰谷差 | 船体高度峰谷差 |','|---|---:|---:|---:|---:|']
for name,d in[('根路径',motion_root),('前缀路径',motion_prefix)]:lines.append(f'| {name} | {d["simSeconds"]:.4f} | {d["distinctSimFrames"]} | {d["range"]["surface"]:.6f} | {d["range"]["rootY"]:.6f} |')
lines+=['','- 原镜头按钮改变实际相机；原 UI 隐藏后可恢复。根路径通过原点击放置石头和贝壳，并核对真实新增对象、撤销和恢复后的集合。','- 两个入口均通过原截图按钮实际下载 PNG，已查看图像，能辨认瓶、船、水与地形，不是空白或错误帧：','','| 条件 | 实际 PNG 尺寸 | 字节数 |','|---|---|---:|']
for name,d in zip(['根路径','前缀路径'],downloads):lines.append(f'| {name} | {d["PNG"][0]}×{d["PNG"][1]} | {d["file"]["bytes"]} |')
lines+=['','尺寸符合画布 CSS×min(DPR,2)，导出不含 DOM 面板。证据：[根路径下载](../evidence/beach-bottle-boat-step-3/browser/production-download.png)、[前缀路径下载](../evidence/beach-bottle-boat-step-3/browser/prefix-download.png)。','','主站边界与完整性：','','- 开发、生产根路径和生产前缀的个人网站均实际浏览到 Coding 区，当前罗森/庭院按钮可用；该阶段没有瓶中海洋网页或封面请求，没有 iframe，也没有主站全局瓶中海洋 API。','- 正常测试无 pageerror、console.error、失败请求或 HTTP 错误。这里只证明静态新增资源没有提前运行，完整主站/罗森内嵌回归仍由后续步骤承担。','- 原仓库 44 文件保持干净，主站 95 项既有生产输入、罗森 46 运行文件、八组旧封存及第一步 253 个封存文件复核通过；第二步标准等既有文档保持原样。','- 本步浏览器关闭，3 个自有服务按 PID/启动时标核对后停止；临时生产文件摘要保存并核对后，删除本步专用临时目录。既有 dist 的 65 个文件全部保持原样。','','判定与范围：','','[final-summary.json](../evidence/beach-bottle-boat-step-3/final-summary.json) 对照 S3-01 至 S3-12，引用 17 项实际记录。首次运行全部通过，没有删除失败或用旧截图充当本轮证据。原始报告保留；其中 HOST.* 的旧诊断字段 nativeModeToggleUsed 为无条件值，不作为实际点击证明，接受依据是稳定阅读模式、可见可用的 Coding 控件、网络和实例断言；脚本已修正该字段，详见 report-notes.json。','', '原亮度读数、镜头惯性及图形丢失语义未修改；后台实际 hidden 恢复、真机和硬件性能仍未验证。当前只做 Linux Chromium 代表复核，不扩写为所有浏览器 34 控件或完整 iframe 接入通过。','','[构建日志](../evidence/beach-bottle-boat-step-3/build.log) · [HTTP/浏览器报告](../evidence/beach-bottle-boat-step-3/browser/browser.json) · [资源清理](../evidence/beach-bottle-boat-step-3/services-cleanup.json) · [交接说明](step-3-handoff.md)。','','本步封存复核：python tests/beach-bottle-boat-step-3/finalize.py --verify-only。此命令只核对本步保存的资料与资源；执行时对现有产品和历史的完整性结论保存在 final-summary.json。','']
(DOC/'step-3-verification.md').write_text('\n'.join(lines))
handoff='''# 第三步交接：第四步入口与第五步现场

第三步已完成资源保存、构建复制、根/真实子路径独立访问及代表操作。代码仍在工作区，未提交 GitHub、未发布；测试服务和临时产物已清理。第二步仍仅有标准，其正式架构审查/生命周期交付没有冒充完成。

| 内容 | 已保存值 |
|---|---|
| 作品身份 | bottle-ocean |
| 展示名 | 瓶中海洋 |
| 体验类型 | embedded-page，原完整网页 |
| 相对 entryPath | experiments/bottle-ocean/index.html |
| 工作区网页 | public/experiments/bottle-ocean/index.html |
| 成品 SHA256 | 941feb2ea6ddd3cc93aad5b0b92dbca52ee66a3e1098fee0dbf16f01ca63d1ef |
| 声明/来源 | 同目录 THIRD_PARTY_NOTICES.md、SOURCE.md |
| 封面候选 | src/assets/bottle-ocean-cover.png |
| 封面尺寸/格式 | 1920×1080 PNG；原生截图，未编辑，不含 DOM 面板 |
| 替代文字 | 黄昏海岸的玻璃瓶中，三桅帆船随微型海浪起伏 |

第四步可以从作品配置导入上述封面，增加第三个作品入口和档案，并把现有二选一键盘逻辑扩展为三作品顺序。iframe 与独立链接须通过同一份入口配置和现有 BASE_URL 解析，不能把运行入口固定成站点根路径。封面目前未导入、未打进主站 assets，待第四步引用后再验证输出和加载。

第四步暂未接通现场时应保持 prepared/独立打开的准确状态，不得误落入庭院或假报 ready。当前主站仍只有罗森和庭院两个作品入口，这是分步范围。

第五步再接通大尺寸 iframe、作品专用状态观察、重试/卸载、焦点和阅读恢复。原瓶中海洋使用 __bottleOcean、bottle-ocean-ready、#gl、__bottleError、#loader/#loader-error；初始就绪须组合当前文档/画布证据。原图形丢失后可能保留 ready=true、没有错误标志且错误遮罩不可见，需观察真实 canvas 故障；原暂停仍持续绘制，退出必须卸载。其余原功能与已知问题见第一步矩阵和第二步标准。

本步 root 与前缀路径均有真实原生输入、自然模拟和 PNG 下载证据；这不替代后续 iframe 中的输入隔离、资源回收、主站/罗森/庭院回归以及真机验证。

以后在项目目录启动 npm run dev 后，使用实际服务地址加 /experiments/bottle-ocean/index.html 可独立访问。生产站点需通过静态服务器提供构建目录；本步记录的临时端口不是长期或公网链接。

本步 runtime-manifest.json 记录原文件/public/构建文件与封面摘要。第一步和历史封存未重写；本步自建 evidence-manifest.json，不把已有封存里旧的阶段进度当成本轮最新状态。
'''
(DOC/'step-3-handoff.md').write_text(handoff)
for p in TEST.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
for p in(TEST/'__pycache__').glob('*'):p.unlink()
if(TEST/'__pycache__').exists():(TEST/'__pycache__').rmdir()
files=[row(DOC/n)for n in['step-3-standard.md','step-3-verification.md','step-3-handoff.md']]+[row(p)for p in sorted(OUT.rglob('*'))if p.is_file()]+[row(p)for p in sorted(TEST.glob('*.py'))]+[row(p)for p in sorted(RUNTIME.glob('*'))if p.is_file()]+[row(COVER)]
assert len({f['path']for f in files})==len(files)
write(OUT/'evidence-manifest.json',{'schema':1,'createdAtShanghai':now(),'scope':'New step-3 docs, scripts, evidence and four newly saved product resources. Earlier sealed records remain independent.','files':sorted(files,key=lambda f:f['path'])})
print(json.dumps({'step3Complete':True,'standardChecksPassed':12,'browserAndHTTPChecksPassed':17,'oldProductionFilesIdentical':len(old),'sealedFiles':len(files),'runtimeEntry':manifest['entryPath'],'pushed':False,'integrated':False},ensure_ascii=False))
