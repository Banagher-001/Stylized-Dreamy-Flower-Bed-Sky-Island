from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json,hashlib,subprocess,shutil
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).parent;DOC=OUT.parents[1]
now=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();save=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
base=json.loads((OUT/'baseline.json').read_text());freeze=json.loads((OUT/'candidate-freeze.json').read_text());assert all(sha(ROOT/v['path'])==v['sha256'] for v in freeze['sources']+freeze['production'])
changed=[v['path'] for v in base['sources'] if sha(ROOT/v['path'])!=v['sha256']];assert set(changed)=={'src/tour/about-refresh/createCardHover.ts','src/tour/about-refresh/createToolBrowser.ts','src/tour/createReadingLayout.ts','src/tour/startTourPrototype.ts'},changed
for kind in ['protectedHistory','publicAssets']:assert all((ROOT/v['path']).is_file() and sha(ROOT/v['path'])==v['sha256'] for v in base[kind]),kind
runs=[('accepted5-adaptation-main',30),('accepted5-first-mouse-main',1),('accepted5-input-measurement',2),('accepted5-component-lifecycle-final',4),('accepted5-adaptation-firefox',5),('accepted5-browser-zoom-final',1),('accepted5-guidance-main',32),('accepted5-detail-main',26),('accepted5-departure-main',28),('accepted5-wheel',15),('accepted5-existing',7),('accepted5-projection',8),('accepted5-cycle',2)]
groups=[]
for name,count in runs:
 folder=OUT/name;d=json.loads((folder/'browser.json').read_text());assert d['complete'] and len(d['checks'])==count and all(v['status']=='通过' for v in d['checks']),name;assert not d.get('events'),name;assert d.get('browserClosed',d.get('cleanup',{}).get('browserClosed')),name
 for c in d['checks']:
  if c.get('consoleErrors'):assert c['id']=='graphics-unavailable-reading',c
 records=json.loads((folder/'source-manifest.json').read_text()) if (folder/'source-manifest.json').exists() else []
 if (folder/'build.json').exists():
  b=json.loads((folder/'build.json').read_text());assert sha(ROOT/b['output']['path'])==b['output']['sha256'];records+=b['sources']
  if (folder/'loaded-component.html').exists():assert sha(folder/'loaded-component.html')==b['output']['sha256']
 assert records and all(sha(ROOT/v['path'])==v['sha256'] for v in records),name
 groups.append({'run':name,'checks':count,'ids':[v['id'] for v in d['checks']],'finalSourcesMatch':True})
total=sum(v['checks'] for v in groups);assert total==161
assert '✓ built in' in (OUT/'build-5.txt').read_text();subprocess.run(['git','diff','--check'],cwd=ROOT,check=True);subprocess.run(['git','diff','--cached','--quiet'],cwd=ROOT,check=True)
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();remote=subprocess.check_output(['git','rev-parse','refs/remotes/origin/main'],cwd=ROOT,text=True).strip();assert head==base['head']==remote
cleanup=json.loads((OUT/'services-cleanup.json').read_text());assert cleanup['portClosed'] and cleanup['servicesStopped']==2;s=json.loads((OUT/'services-started.json').read_text());assert all(not Path('/proc',str(v['pid'])).exists() for v in s['services'])
video=json.loads((OUT/'video-metadata.json').read_text());assert sha(ROOT/video['source'])==video['sourceSHA256'] and sha(ROOT/video['target'])==video['targetSHA256'];visual=json.loads((OUT/'visual-review.json').read_text());assert visual['accepted'] and all((OUT/v).is_file() for v in visual['reviewed'])
get=lambda folder,name:json.loads((OUT/folder/(name+'-data.json')).read_text())
tap=get('accepted5-adaptation-main','hybrid-first-tap');drag=get('accepted5-adaptation-main','hybrid-first-swipe');measure=get('accepted5-input-measurement','gesture-defers-capacity-probes');priority=get('accepted5-input-measurement','font-change-takes-priority-over-gesture');graphics=get('accepted5-adaptation-main','graphics-loss-and-recovery');life=get('accepted5-component-lifecycle-final','remount-does-not-multiply-input');first_mouse=get('accepted5-component-lifecycle-final','first-mouse-hover-after-touch-swipe');assert first_mouse['hoverState']=='reading' and first_mouse['toolInput']=='mouse';keys=get('accepted5-adaptation-main','keyboard-and-targets');zoom=json.loads((OUT/'accepted5-browser-zoom-final/zoom-data.json').read_text());geometry=get('accepted5-adaptation-main','viewport-1440x900')
button=lambda m:next(v['button'] for v in m['cards'] if v['id']=='comfyui');a,b=button(tap['before']),button(tap['fingerDown']);error=max(abs(a[k]-b[k]) for k in ['left','top','right','bottom'])
metrics={'firstMouseHoverAfterTouch':first_mouse['hoverState'],'touchButtonMaxMoveWhileHeldPx':error,'touchFixedId':tap['after']['d']['readingId'],'touchFixedBodyHidden':next(v['bodyHidden'] for v in tap['after']['cards'] if v['id']=='comfyui'),'nativeDragStartEndPx':[drag['before']['railX'],drag['after']['railX']],'capacityProbesWhileFingerHeld':len(measure['heldProbes']),'capacityProbesDuringDrag':len(measure['duringProbes']),'capacityProbesAfterQuiet':len(measure['afterProbes']),'fontChangeProbesDuringGesture':len(priority['duringProbes']),'graphicsRestoredOffscreen':graphics['restoredOffscreen']['host']['renderState'],'graphicsReadyWhenVisible':graphics['firstVisibleFrame']['host']['renderState'],'oldNoticeHiddenAfterTimeout':graphics['noticeAfterOldTimeout']['hidden'],'freshRemountedCallbacks':[life['freshActionCallbacks'],life['remountedActionCallbacks']],'remountedOldRoots':len(life['old']),'minimumPaletteContrast':min(v['ratio'] for v in keys['paletteContrast']),'minimumTargetCSSPx':min(min(v['w'],v['h']) for v in keys['buttons']),'controlsBeforeOpenPx':geometry['initial']['controls']['height'],'controlsWithHelpPx':geometry['help']['controls']['height'],'zoomWidths':[zoom['before']['width'],zoom['large']['width'],zoom['restored']['width']],'zoomDPR':[zoom['before']['dpr'],zoom['large']['dpr'],zoom['restored']['dpr']],'nativeZoomHeaderHit':zoom['large']['headerHit']}
assert error<.6 and metrics['touchFixedId']=='comfyui' and not metrics['touchFixedBodyHidden'];assert metrics['capacityProbesDuringDrag']==0 and metrics['capacityProbesAfterQuiet']>0;assert metrics['nativeZoomHeaderHit']
excluded=['inspection-baseline.json','inspection-touch-fix.json','touch-focused-1','touch-focused-2','adaptation-main-1','adaptation-firefox-1','browser-zoom-1','accepted-component-lifecycle','accepted-browser-zoom','inspect-first-mouse',*[v['run'] for v in json.loads((OUT/'versions/build-4/adoption.json').read_text())['groups']]]
notes=['最终结果仅采纳 build-5 上的 161 项。中间构建、定位重跑和脚本失败不累计。','build-4 的 159 项通过后补查发现，触摸滑动后首个鼠标移动在悬停判断之后才更新输入方式；build-5 将识别移至捕获阶段，新增第一次停留回归，并重新执行全部最终检查。','修改前首次触摸导致按钮移位，固定阅读落空；修复后按住期间四边最大位移见 metrics，原生点击固定成功。','touch-focused-1 定位到测量中断原生拖动，事件顺序见 drag-diagnosis.json；最终同时验证拖动中不测量、结束后补测、字号变化优先适配。','图形连接恢复后，屏幕外画布按可见性等待首帧；旧测试等待立即 ready 不符合该约定。实际修复结束未清理的超时/提示，并验证 restored、超过原超时后提示仍隐藏、可见后 ready。','Firefox 容量不足时正确保留稳定阅读；最终往返测试在扩大实际空间后才操作沉浸入口，不降低安全边界。','重复挂载测试改与干净实例回调次数比较：一次前后导航兼有显式操作和固定阅读回调，不能硬编码为一次。','真实缩放通过 X11 浏览器快捷键执行，视口宽度减半且 DPR 翻倍；另以窗口截图和命中检查复核。','组件内部的计时、浏览器模拟和物理设备范围如验收记录所述；未冒充真机或 Safari 验收。']
save(OUT/'adoption.json',{'total':total,'allPassed':True,'build':'build-5','groups':groups,'excludedDevelopmentRecords':excluded,'notes':notes})
save(OUT/'source-freeze.json',{'checkedAtShanghai':now,**freeze,'buildPassed':True,'pushed':False,'published':False})
save(OUT/'protection-final.json',{'checkedAtShanghai':now,'changedRuntime':changed,'newRuntime':[],'otherBaselineSourcesUnchanged':len(base['sources'])-len(changed),'historicalFilesUnchanged':len(base['protectedHistory']),'publicAssetsUnchanged':len(base['publicAssets']),'contentAndMarksUnchanged':True,'head':head,'localOriginMain':remote,'indexUnchanged':True,'pushed':False,'published':False,'servicesClosed':True})
save(OUT/'final-summary.json',{'completedAtShanghai':now,'step':13,'status':'completed','acceptedChecks':total,'metrics':metrics,'physicalHardwareTested':False,'video':video['target'],'nextStep':14,'unpublished':True})
(DOC/'step-13-verification.md').write_text(f'''# 关于我改版 · 第十三步验收

完成：{now}（Asia/Shanghai）。第十三步已完成，第十四步未开始；代码保存在工作区，未提交、推送或发布。

[实现说明](step-13-adaptation.md) · [第十四步交接](step-13-handoff.md) · [原速演示](evidence/step-13/step-13-adaptation.mp4)

## 结果

**{total} 项最终检查通过**，生产构建、类型检查与 git diff --check 通过。采纳结果逐一匹配最终 build-5 的源码、生产资源或实际组件载荷哈希。前期定位与中间版本没有累计进入通过数。

| 范围 | 检查数 |
| --- | ---: |
| 主站尺寸、输入、模式、字体、减少动态、后台、图形和操作目标 | 30 |
| 手势期间延后测量、字号变化优先处理 | 2 |
| 首次鼠标悬停的真实主站衔接 | 1 |
| 触摸中销毁/恢复、十次重挂及首次鼠标悬停 | 4 |
| Firefox 布局、模式往返、减少动态与键盘 | 5 |
| 原生浏览器 200% 缩放往返 | 1 |
| 第十二步操作说明与状态提示回归 | 32 |
| 全文详情、固定阅读与键盘回归 | 26 |
| 飞离返回、首次操作与生命周期回归 | 28 |
| 滚轮速度、方向、首事件与环境独立性 | 15 |
| 原有 AI 影像、罗森、漂流瓶及主站交互 | 7 |
| 手机、大字、宽屏及首末卡片投影边界 | 8 |
| 22 张与五张分类的双向整圈 | 2 |

[逐项采纳与诊断说明](evidence/step-13/adoption.json) · [源码冻结](evidence/step-13/source-freeze.json) · [保护核对](evidence/step-13/protection-final.json)

## 关键实测

- 鼠标预览后第一次真实浏览器触摸，按住期间按钮四边最大移动 **{error:.3f} px**，随后固定 ComfyUI 正文成功；取消、横向滑动与切回鼠标也通过。触摸滑动后的第一次鼠标停留即可展开，不需要再次移动或额外点击。没有合成点击或复制卡片。
- 横向拖动前后位置为 **{metrics['nativeDragStartEndPx'][0]} → {metrics['nativeDragStartEndPx'][1]} px**。按住与拖动期间容量探测均为 **0 次**，滚动安静后完成 **{metrics['capacityProbesAfterQuiet']} 次**补测；字号变化期间则能优先测量并切换稳定阅读。
- 1440×900 的默认控制栏与说明展开时均为 **{metrics['controlsBeforeOpenPx']} px**，没有为本步增加默认高度。320×740、390×844、430×932、844×390、768×1024、1024×768、1280×720、1440×900、1920×1080 与 1179/1180/1181 临界宽度均完成浏览、说明和详情检查。
- 固定阅读在窄屏、横竖屏、200% 字号、减少动态与模式往返中保留。能力恢复不擅自开启自动；同一模式内调整尺寸可保留有效的自动选择。背景返回不补跑旧惯性。
- 图形连接在屏幕外恢复为 **{metrics['graphicsRestoredOffscreen']}**，等待超过原四秒超时后中断提示仍隐藏；画布可见后成为 **{metrics['graphicsReadyWhenVisible']}**，返回阅读仍保留固定对象和节点身份。
- 十次重挂后，当前工具浏览器只有一个；一次相同操作的有效回调次数与干净实例均为 **{metrics['freshRemountedCallbacks']}**，旧实例已销毁。卡片/说明静止后的状态与任务清理经专项和既有回归核对。
- 按实际 CSS 盒检查的最小操作目标为 **{metrics['minimumTargetCSSPx']} px**；已检查的正文/按钮色板配对最低对比度 **{metrics['minimumPaletteContrast']:.2f}:1**，焦点轮廓满足对应检查。键盘与 Escape 优先级通过；不等同于辅助软件完整认证。

## 浏览器与缩放

Chromium 155.0.8059.79 与 Firefox 153.0。Firefox 在一次 1440×900 返回中按实际文字占用判断空间不足，保留稳定阅读；扩大到 1440×1100 后可选择沉浸浏览，未降低安全边界。

真实缩放在有界面的 Chromium 中通过 X11 浏览器快捷键完成，没有用 CSS 字号或视口仿真替代：宽度 **{metrics['zoomWidths']}**，DPR **{metrics['zoomDPR']}**；200% 时固定正文保持、页头命中有效，恢复后保留稳定阅读和暂停选择。[实际窗口画面](evidence/step-13/accepted5-browser-zoom-final/browser-zoom-200-desktop.png)

触摸由 Chromium 原生输入通道或浏览器触摸仿真执行；混合设备、后台、初始图形不可用等模拟在记录中标记。图形中断使用实际 WEBGL_lose_context 扩展。未做实体手机、屏幕阅读器或 Safari 实测；本环境 WebKit 缺少 libGLESv2.so.2，未计入支持浏览器验收。

## 视觉与交付

[桌面](evidence/step-13/accepted5-adaptation-main/viewport-1440x900.png) · [小屏](evidence/step-13/accepted5-adaptation-main/viewport-320x740.png) · [手机固定阅读](evidence/step-13/accepted5-adaptation-main/pinned-phone-orientation.png) · [首次触摸固定](evidence/step-13/accepted5-adaptation-main/hybrid-first-tap.png) · [Firefox 沉浸返回](evidence/step-13/accepted5-adaptation-firefox/pinned-mode-roundtrip.png)

录像 {float(video['deliveryMetadata']['format']['duration']):.2f} 秒，未加速或改写卡片动画时钟；固定世界时间仅便于观察界面，世界播放独立性另经回归核对。缩放直接窗口留档与自动截图的取样差异保留在视觉记录中。

本步仅修改四个衔接文件，其他 **{len(base['sources'])-len(changed)} 个**基线源码/配置、**{len(base['protectedHistory'])} 个**既有档案及开发文件、**{len(base['publicAssets'])} 个**公共资源保持原哈希。没有修改个人资料、工具正文/标识、场景美术、运镜路线或嵌入作品源码。

专用测试浏览器与服务已关闭，[清理记录](evidence/step-13/services-cleanup.json)。HEAD 与本地 origin/main 均保持 `{head}`，暂存区为空。第十四步按后续指示先细化再执行。
''')
cache=OUT/'__pycache__'
if cache.exists():shutil.rmtree(cache)
files=[p for p in OUT.rglob('*') if p.is_file() and p.name!='evidence-manifest.json'];save(OUT/'evidence-manifest.json',{'createdAtShanghai':now,'files':[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(files)]})
print(json.dumps({'acceptedChecks':total,'changedRuntime':changed,'protectedHistory':len(base['protectedHistory']),'publicAssets':len(base['publicAssets']),'evidenceFiles':len(files),'head':head},ensure_ascii=False))
