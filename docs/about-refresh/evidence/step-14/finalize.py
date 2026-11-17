"""Publish local verification documents only after all final records pass."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json,hashlib
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).parent;DOC=OUT.parents[1]
def read(p):return json.loads(p.read_text())
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
checks=[]
for folder in ['journeys-2','keyboard-4','embedded-1','firefox-1']:
    record=OUT/folder/'browser.json';d=read(record)
    for c in d['checks']:
        if folder=='journeys-2' and c['id']=='keyboard-complete-route':continue
        assert c['status']=='通过'
        checks.append({'id':c['id'],'engine':d['engine'],'record':str(record.relative_to(ROOT)),'recordSHA256':hashlib.sha256(record.read_bytes()).hexdigest(),'status':'通过'})
portable=read(OUT/'package-final-r3/portable-validation.json');assert portable['complete'] and len(portable['checks'])==4
for c in portable['checks']:
    record=OUT/'package-final-r3'/c['browserRecord'];d=read(record);assert d['complete']
    checks.append({'id':'portable-'+c['label'],'engine':d['engine'],'record':str(record.relative_to(ROOT)),'recordSHA256':hashlib.sha256(record.read_bytes()).hexdigest(),'status':'通过'})
stability=read(OUT/'stability-review/browser.json');assert stability['complete']
clock=read(OUT/'stability-review/ten-minute-record-review-and-actual-track-movement-data.json');assert clock['actualWallSeconds']>=600
record=OUT/'stability-review/browser.json'
checks.append({'id':'ten-minute-real-clock-stability-reviewed','engine':stability['engine'],'record':str(record.relative_to(ROOT)),'recordSHA256':hashlib.sha256(record.read_bytes()).hexdigest(),'status':'通过'})
assert len(checks)==14
build=read(OUT/'build.json');audit=read(OUT/'integrity.json');assert audit['complete']
packages=read(OUT/'package-final-r3/package-validation.json');assert packages['complete'] and packages['sameProductionBytes']
cleanup=read(OUT/'services-cleanup.json');assert cleanup['portClosed'] and cleanup['servicesStopped']==2
for file in [OUT/'package-services-cleanup.json',OUT/'package-final/package-services-cleanup.json',OUT/'package-final-r3/package-services-cleanup.json']:
    clean=read(file);assert clean['stoppedOwnedProcesses']==4 and all(x['closed'] for x in clean['ports'])
packaging=read(OUT/'packaging-final.json');manifest=read(Path(packaging['manifest']))
adoption={'completedAtShanghai':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'candidateId':build['candidateId'],'deliveryId':manifest['deliveryId'],'runtimeInputDigest':build['runtimeInputDigest'],'checks':checks,'adoptedChecks':len(checks),'complete':True,'step13ReferencedChecks':161,'step13RecountedAsNew':False,'unchangedRuntimeFiles':197,'productionFiles':69,'actualTenMinuteWallSeconds':clock['actualWallSeconds'],'stabilitySamples':clock['sampleCount'],'stabilityVerificationMethod':'Full real-clock raw samples reviewed with recorded program distance plus a real browser card-position check; original erroneous native-scroll assertion remains failed in its raw record','committed':False,'pushed':False,'deployed':False,'intermediateFailuresRetained':True,'finalPackages':{k:{field:a[field] for field in ['path','bytes','sha256']} for k,a in manifest['artifacts'].items()},'cleanup':{'ownedProcessesStopped':14,'allOwnedPortsClosed':True,'otherServicesStopped':False}}
save(OUT/'adoption.json',adoption)
rows='\n'.join('| '+c['id']+' | '+c['engine']+' | [通过]('+str(Path(c['record']).relative_to('docs/about-refresh'))+') |' for c in checks)
resource=clock['finalResources'];duration=clock['actualWallSeconds'];sample_count=clock['sampleCount']
verification=f'''# 关于我改版 · 第十四步整体验收

十四步本轮收尾完成。当前站点候选 **{build['candidateId']}**，最终下载交付 **{manifest['deliveryId']}**。{adoption['completedAtShanghai']}（上海时间）。当前改版保存在工作区，未提交、推送或部署。

## 版本与范围

本步建立独立基线，严格构建成功。197 个运行输入与第十三步完成状态一致，69 个生产文件冻结后用于整体验收；本步新增完整路线、交付脚本、说明与包，没有重做已验收的视觉和交互。源码/公共资源、旧包与前十三步记录保持。当前 About 使用确认后的身份、经历与制作流程，不列场景为正式项目，不加奖项。第三屏保留 22 张工具卡、七类筛选与已批准的完整交互。

[基线](evidence/step-14/baseline.json) · [构建身份与文件清单](evidence/step-14/build.json) · [构建日志](evidence/step-14/build-1.txt) · [最终采用记录](evidence/step-14/adoption.json)

第十三步 161 项适配结果沿用其原证据，不计作本步新增通过。此次新增采用 **14 项完整路线/交付/持续运行检查**，每项包含多个真实操作；不把子断言数、前期失败尝试或旧包结果叠加计数。

## 采用的最终记录

| 路线或验证 | 引擎 | 记录 |
| --- | --- | --- |
{rows}

Chromium {read(OUT/'journeys-2/browser.json')['version']}；Firefox {read(OUT/'firefox-1/browser.json')['version']}。默认 HTTP 入口进入当前庭院，没有使用调试时钟或替换 RAF。触控为 390×844 的浏览器原生触摸仿真，并检查横竖切换。

完整桌面路线覆盖环境真实播放、导览接管、A1/A2 默认正文、四卡入场、自动横排、滚轮强弱、七类筛选、固定阅读、帮助/全部工具 Esc 优先级、实际飞离、样片、三作品、结束和重播。轮速样本峰值约 93.2 / 382.9，与输入强弱一致，未触及 560 的上限。快速阅读验证展开姓名和教育、材质类固定卡、查看作品后返回保留分类与正文。键盘路线使用原生 Tab / Enter / Esc 和标签的左右方向键，不用程序强制焦点代替导航。

[入场录像](evidence/step-14/journeys-2/video/page@540fe4f9ca826eba2a13cacbfed4b275.webm) · [卡片画面复核](evidence/step-14/visual-review-cards.png) · [手机固定卡与说明](evidence/step-14/journeys-2/mobile-complete-journey-touch-help.png)

## 原网页与隔离

罗森原生 41 控件、瓶中海洋 34 控件保持。此次实际操作罗森的时间、灯光、屋顶、相机、帮助与控制台；瓶中海洋的画质、滑块、场景开关、相机、沙盒放置/撤回、暂停和原生截图下载。子网页 Esc 留给其编辑模式；切换档案和关闭项目会移除 iframe。独立打开实际载入成功，opener 为 null。重新进入瓶中海洋恢复其原始默认状态。庭院早期视频可使用原生控件播放，返回后无遗留视频/iframe。完整原网页逐项对照沿用此前接入阶段证据，本步没有把代表性操作声称为全部物理参数重新测试。

51 个 public 文件逐一保持原 SHA256。运行不连接 GitHub 或 CDN；采用记录无页面错误、意外脚本/样式请求失败或 HTTP 错误。媒体/图片主动关闭时的 ERR_ABORTED 分开记录，保留原始日志；浏览器关于 allow/allowfullscreen 的提示不视为功能失败。

## 十分钟真实运行

最终连续运行 **{duration:.3f} 秒**，{sample_count} 次真实时钟采样，原始 runner 已执行完全部时间，随后由专项复核检查原始样本并补证实际卡片移动。九组穿插操作：轮速/帮助、罗森进入返回、窄屏再返回、全部工具列表返回及瓶中海洋进入返回。没有加速时钟或替换 RAF。

预热后与结束时主场景资源均为几何体 {resource['geometries']}、纹理 {resource['textures']}、程序 {resource['programs']}。正常显示时始终每工具一个当前实体，共 22 张；布局转换保留实体，全量列表切换按现有设计销毁并重建视图，返回后没有累积副本。卡排与环境时间继续前进，关闭子页后 iframe 为零。该检查支持本次操作范围内的稳定性结论；未以软件渲染环境推算硬件 FPS 或宣称长期堆内存永不增长。

[真实采样与操作](evidence/step-14/stability-3/samples.json) · [原始 runner 记录](evidence/step-14/stability-3/browser.json) · [采样复核与实际位置补证](evidence/step-14/stability-review/ten-minute-record-review-and-actual-track-movement-data.json)

## 最终两个下载包

最终采用 r3。它修订持续运行脚本的三维轨道观测，补充已保存采样的专项复核脚本，并校正首个键盘入口名称；运行输入与首版草稿一致。首版未采用包原字节保留在 [superseded-package](evidence/step-14/superseded-package/README.md)，旧包的通过记录不替代最终包验证。

最终成品 75 个文件，源码 {len(manifest['artifacts']['source']['files'])} 个文件。各 ZIP 校验 CRC、文件数量、每个文件大小及 SHA256，并在新中文/空格目录独立解压。源码从无 node_modules / dist 的状态运行 npm ci 和 npm run build，重建 69 个生产文件与冻结版本逐字节一致。成品和重建源码分别检查根目录及 /portfolio-check/ 子路径，实际载入两原网页并下载 PNG；HTML / JS MIME、视频 Range 206、缺失文件 404 均通过。没有从原工作区补资源。

[最终解压、安装与重建](evidence/step-14/package-final-r3/package-validation.json) · [四入口与 HTTP 检查](evidence/step-14/package-final-r3/portable-validation.json) · [最终包清单](../../{Path(packaging['manifest']).relative_to(ROOT)})

成品不需要 npm 安装；Windows 启动文件检查了真实 CRLF 和目录引用，实际预览进程在 Linux 验证。没有把此项写成实体 Windows 双击通过。源码包提供运行与维护文档、当前代码、锁文件和可复用验收脚本，不含 Git 历史、私人简历、历史大附件或嵌套发布包。

## 排查记录、边界与清理

中间失败记录保留，不采用为最终通过：首次选择器同时匹配 host 与正文；媒体关闭需等待 close 清理和焦点回调；作品标签需使用左右方向键；卡排间隙滚动可能交还页面，继续操作前应返回工具屏；全量目录返回会合法重建视图，持续运行需核对每工具唯一当前实体，而非要求旧 DOM 永久不变。修订的是验收脚本，本步运行源码未改变。第三次持续运行从零完成完整 600 秒；其末尾原生 scrollLeft 断言误判了使用 transform 的轨道，原始失败记录保留。最终采用对全部 21 次原始采样的复核，使用已记录的 trackDistance，并在同一构建补查卡片屏幕位置确实移动；不改写原始 runner 为通过。

本步新增实测范围为 Linux Chromium / Firefox、触摸仿真、减少动态和独立包 HTTP 浏览。没有新增 WebKit 实测；实体手机、系统浏览器栏/刘海、辅助阅读器与硬件性能仍应在实际发布设备复核。

已关闭本步拥有的 14 个服务进程及其监听端口，未关闭其他服务。Git HEAD / 本地 origin/main 均保持 {audit['head']}。8265 个受保护历史文件、51 个公共资源与全部 197 个运行输入保持，git diff --check 通过。

[完整性审计](evidence/step-14/integrity.json) · [主服务清理](evidence/step-14/services-cleanup.json) · [首版包服务清理](evidence/step-14/package-services-cleanup.json) · [最终包服务清理](evidence/step-14/package-final-r3/package-services-cleanup.json)
'''
(DOC/'step-14-verification.md').write_text(verification)
site=manifest['artifacts']['site'];source=manifest['artifacts']['source']
handoff=f'''# 关于我改版 · 第十四步交接

本轮十四步完成，交付版本 **{manifest['deliveryId']}**，站点候选 **{build['candidateId']}**。严格构建、14 项最终路线与交付检查、{duration:.3f} 秒真实连续运行、两个包独立解压与源码重建通过。没有提交、推送或部署。

[验收报告](step-14-verification.md) · [最终采用记录](evidence/step-14/adoption.json) · [运行说明](run-guide.md) · [维护说明](maintenance.md)

## 下载与启动

- [最终成品 ZIP](../../{site['path']})，{site['bytes']:,} 字节（约 {site['bytes']/1048576:.2f} MiB）。完整解压、安装 Node.js 后，Windows 双击 START-PREVIEW.cmd。
- [最终源码 ZIP](../../{source['path']})，{source['bytes']:,} 字节（约 {source['bytes']/1048576:.2f} MiB）。Windows 双击 START-DEV.cmd，或 PowerShell 运行 npm.cmd ci / npm.cmd run dev。
- [包内清单与版本](../../release/{manifest['deliveryId']}-manifest.json) · [SHA256SUMS](../../release/{manifest['deliveryId']}-SHA256SUMS)。

成品 SHA256：{site['sha256']}。源码 SHA256：{source['sha256']}。两个包均需要通过 HTTP 查看，不能直接双击 HTML。本机 localhost 地址不会自动成为可供其他人访问的网址。

## 本轮最终状态

个人身份、经历、流程与 22 张卡沿用批准内容；不添加项目/奖项或未经确认的业绩。四卡入场、随轮速加速和缓冲、倾斜预览、固定正文、全量列表、操作说明、飞离与返回均进入完整路线检查。AI 影像保留设计样片标记。LAWSON / BOTTLE OCEAN / COURTYARD 的完整网页、档案与主站返回保持。

本步以第十三步完成源码建立基线，没有继续改变已验收的页面表现。新增 README、运行/维护/验收文档、可复用脚本和本次 ZIP；前十三步、以前发布包和原网页文件保持。r3 更新交付侧脚本，首次草稿包保留在本步证据中，不作为当前下载入口。

全部 197 个运行输入与 69 个站点输出以 SHA256 追溯。源码包从干净中文/空格目录安装构建，输出与站点完全一致。源码包采用独立的便携 README，只附轻量运行/维护资料与脚本；完整历史证据保存在工作区，后续仓库保存时可按当时用户指示纳入。

## 后续边界

当前仓库 HEAD / 本地 origin/main 仍为 {audit['head']}，本轮修改尚未保存到 GitHub。上传仓库与部署等待用户后续指示，不因本步验收完成自动执行。真实作品和联系方式可在用户提供后另开修改；真实手机与辅助阅读器仍保留实机验收范围。
'''
(DOC/'step-14-handoff.md').write_text(handoff)
print(json.dumps({'complete':True,'adoptedChecks':len(checks),'actualWallSeconds':duration,'deliveryId':manifest['deliveryId']},ensure_ascii=False),flush=True)
