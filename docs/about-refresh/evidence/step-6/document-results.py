from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from hashlib import sha256
import json,re,subprocess

ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).parent;DOC=OUT.parents[1]
NOW=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
read=lambda p:json.loads(p.read_text())
save=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
git=lambda *args:subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
def row(p):
 data=p.read_bytes();return {'path':str(p.relative_to(ROOT)),'bytes':len(data),'sha256':sha256(data).hexdigest()}
def current(item):
 p=ROOT/item['path'];return p.exists() and row(p)==item

baseline=read(OUT/'baseline.json');assert all(current(v) for v in baseline['historicalArtifacts'])
expected={'src/tour/startTourPrototype.ts','src/tour/createPillarReader.ts','src/tour/about-refresh/toolCards.css','src/tour/about-refresh/types.ts','src/tour/about-refresh/createAboutView.ts','src/tour/about-refresh/createToolBrowser.ts','src/tour/about-refresh/createToolCard.ts'}
changed=[v['path'] for v in baseline['sourceFilesBefore'] if not current(v)];assert set(changed)==expected,changed
assert git('rev-parse','HEAD')==git('rev-parse','origin/main')==baseline['head']
assert set(git('diff','--name-only').splitlines())==set(baseline['trackedChangesBefore'])
assert not git('diff','--cached','--name-only')
subprocess.run(['git','diff','--check'],cwd=ROOT,check=True)
suites={}
for name,count in [('entrance-2',21),('accepted-resource-guide',1),('accepted-main',44),('accepted-projection',8),('accepted-regressions',7)]:
 d=read(OUT/name/'browser.json');assert d['complete'] and len(d['checks'])==count and all(c['status']=='通过' for c in d['checks']),name
 assert d.get('browserClosed',d.get('cleanup',{}).get('browserClosed')) is True,name
 assert all(current(v) for v in read(OUT/name/'source-manifest.json')),name
 suites[name]={'report':name+'/browser.json','passed':count,'failed':0,'sourceMatches':True}
base_sources=read(OUT/'entrance-2/source-manifest.json')
for name in suites:assert read(OUT/name/'source-manifest.json')==base_sources,name
cleanup=read(OUT/'services-cleanup.json');assert cleanup=={'servicesStopped':2,'portClosed':True,'otherServicesStopped':False}
assert 'typecheck' in (OUT/'build-4.txt').read_text() and 'built in' in (OUT/'build-4.txt').read_text()
save(OUT/'build-check.json',{'command':'npm run build','includes':'npm run typecheck && vite build','exitCode':0,'output':'build-4.txt','outputSHA256':row(OUT/'build-4.txt')['sha256']})

motion=read(OUT/'accepted-motion/browser.json');assert motion['complete'] and not motion['errors'] and motion['browserClosed']
b=motion['after']['browser'];assert b['entranceReason']=='completed' and b['entrancePlays']=='1' and b['entranceFramePending']=='false'
elapsed=float(b['entranceFinishedAt'])-float(b['entranceStartedAt']);assert 1450<=elapsed<2000
first=next(f for f in motion['motion']['phases'] if f['phase']=='playing')
ids=['midjourney','comfyui','kling','blender'];assert [c['id'] for c in first['cards']]==ids
rail=motion['after']['rail'];visible={};back_frames={};initial=[];slot_gap=0
for card in first['cards']:
 faces=card['faces'];left=min(r[0] for r in faces);right=max(r[2] for r in faces)
 assert right<-32 or left>1440+32
 initial.append({'id':card['id'],'left':left,'right':right})
 after=next(v for v in motion['after']['cards'] if v['id']==card['id'])
 slot_gap=max(slot_gap,*[abs(a-z) for a,z in zip(card['slot'],[after['slot'][k] for k in ['left','top','right','bottom']])])
for id in ids:
 matches=[]
 for f in motion['motion']['frames']:
  card=next(c for c in f['cards'] if c['id']==id);faces=card['faces']
  if max(r[2] for r in faces)>rail['left'] and min(r[0] for r in faces)<rail['right'] and max(r[3] for r in faces)>rail['top'] and min(r[1] for r in faces)<rail['bottom']:
   matches.append((f['time'],abs(float(card['pose'].split(',')[1]))>90))
 assert matches
 visible[id]=matches[0][0];back_frames[id]=sum(back for _,back in matches)
assert list(visible.values())==sorted(visible.values())
assert back_frames['comfyui']>0 and slot_gap<.2
assert all(c['inSlot'] and not c['inert'] and not c['frontInert'] for c in motion['after']['cards'])
save(OUT/'motion-validation.json',{'checkedAtShanghai':NOW,'status':'通过','actualDurationMS':elapsed,'orderedIDs':ids,'firstVisibleAt':visible,'visibleReversePoseFrameCounts':back_frames,'initialProjectedBounds':initial,'maximumSlotMovementPX':slot_gap,'framesObserved':len(motion['motion']['frames']),'clockModified':False,'sceneTimeFixedForRecording':True,'notes':'Visible-frame counts combine projected intersection with orientation; the actual reverse engraving was also visually inspected in early.png. The source manifest was not emitted during recording; its same final build context is recorded separately.'})
save(OUT/'accepted-motion-source-context.json',{'recordedAtShanghai':NOW,'context':'Recording used the same dedicated dist server after build-4 and after entrance-2 passed. No runtime source or production rebuild occurred between these runs. Current source/assets match all five adopted browser manifests. This is retrospective adoption metadata, not an original per-recording manifest.','sourceManifest':'entrance-2/source-manifest.json','manifestSHA256':row(OUT/'entrance-2/source-manifest.json')['sha256']})

# Preserve the failed recording attempt explicitly; cached ffmpeg was then selected.
save(OUT/'inspection-2/recording-failure-note.json',{'recordedAtShanghai':NOW,'status':'未完成','reason':'Playwright looked for ffmpeg under its default cache and could not create the recording page. Later runs selected the already installed workspace cache; no dependency was downloaded.','adoptedInstead':'accepted-motion'})
visuals={
 'accepted-motion/early.png':'画内可见卡牌厚度与独立背面刻纹，标题、分类和导航仍可辨认。',
 'accepted-motion/middle.png':'卡牌在不同深度和朝向上交叠，呈立体弧线运动。',
 'accepted-motion/late.png':'卡牌逐渐转正并接近各自卡位，保持石质配色。',
 'accepted-main/desktop-A3.png':'落位后恢复原有三张完整加第四张局部构图，文字与控件清晰。',
 'accepted-main/phone-A3.png':'手机静态完整阅读、分类入口和原生横滑保留。',
}
save(OUT/'visual-review.json',{'reviewedAtShanghai':NOW,'method':'Final screenshots inspected with view_image; frame-level geometry and native interaction checks provide motion/cleanup evidence.','screenshots':[{'path':k,'finding':v,'sha256':row(OUT/k)['sha256']} for k,v in visuals.items()],'limits':'Linux Chromium with emulated viewports. Simulated page-hidden lifecycle is labelled in its test; not a claim of physical phones, Safari or Firefox testing.'})
save(OUT/'protection-final.json',{'checkedAtShanghai':NOW,'status':'通过','historicalArtifactsChecked':len(baseline['historicalArtifacts']),'historicalArtifactsChanged':[],'existingSourceChanged':changed,'newRuntimeFiles':['src/tour/about-refresh/createCardEntrance.ts','src/tour/about-refresh/cardEntrance.css'],'publicCopyAndMarksUnchanged':True,'head':git('rev-parse','HEAD'),'localOriginMain':git('rev-parse','origin/main'),'gitDiffCheck':'通过','stagedChanges':[],'dependenciesChanged':False,'existingEmbeddedSiteFilesChanged':False,'committed':False,'pushed':False,'published':False})
for item in base_sources:
 if item['path'].startswith('dist/') and item['path'].endswith(('.js','.css')):
  data=(ROOT/item['path']).read_text();assert '__entranceEvidence' not in data and '__toolCardReview' not in data and '__aboutRefreshPreview' not in data

(DOC/'step-6-entrance.md').write_text(f'''# 关于我改版 · 第六步首批卡牌飞入

状态：已完成并接入工作区主站。核对时间 {NOW}（Asia/Shanghai）。本次未提交、推送或发布。

[观看主站实录](evidence/step-6/step-6-entrance.mp4) · [验收](step-6-verification.md) · [第七步交接](step-6-handoff.md)

## 实际观看行为

首次正常进入宽幅沉浸模式的 A3“工具与方法”后，标题先完成显现，随后 Midjourney→ComfyUI→可灵→Blender 四张石质卡牌错峰飞入。初始真实表面投影在视口外约 42px，经过不同深度、弧线位移和朝向变化，再减速转正归位。ComfyUI 的背面刻纹在画内可见。落定仍为三张完整加第四张局部预览，没有缩小文字或强塞四张完整卡。

首批延迟 0/110/220/330ms，单卡时长 980/1040/1080/1120ms；总目标 1450ms，采用录像中实际测得 {elapsed:.1f}ms。初始深度分别 -280/-420/-240/-360px，结合俯仰、左右转向及小幅绕正面旋转。后段只有一次小幅姿态修正，最终 pitch/yaw/roll 和位移归零。牌面透明度没有参与飞入。

实体继续使用第五步的真实 HTML 正文、正背面和八段侧边。飞入期间将同一节点移到浏览器内部前景层，原 slot 保留实际高度；统一 1100px 透视，临时禁用单卡透视以免重复投影。裁切位于三维链之外，活动窗口与卡牌轨道重合，保护标题、分类、导航和下方按钮。阴影随定位层运动，不在目标位置留下静止影子。卡牌使用 CSS 3D 及风格化受光，不增加 WebGLRenderer，也不参与庭院的世界空间阴影。

## 触发与就绪

真实 A3 可阅读、标题和正文完成显现、镜头停稳、主站布局已就绪且空间足够时才开始。系统容量测量不调用入场接口，不触发动画、不消耗首次机会。首次等待资源和尺寸时隐藏首批牌面但保留布局；本地图案与字体准备最多等待约 1200ms，失败则静态归位，名称和正文仍可阅读。飞行若异常拖长到 2500ms以上，也转入静态完成。

状态为 waiting→preparing→playing→ready；中断归为 cancelled，销毁归为 disposed。只在准备阶段离开且尚未开播，会恢复 waiting；开始后离开不重播。首次完成后返回保留原分类、详情、位置与状态。

主站 A3 自动导览要求入口 ready 后才能开始阅读计时。就绪变化只唤醒导览，不发起容量重测，也不算用户交互。A3 本地装饰图案已由有限准备过程处理，不再让装饰资源失败导致阅读无限等待。其他站点原有图片解码检查保留。

## 中断与适配

分类、前后按钮、全部工具、键盘焦点和继续浏览会先清理飞入，再执行原操作；第一次操作即生效。离开 A3、切换阅读模式、改变窗口或字体布局、页面隐藏、减少动态偏好变化均能归位。卡牌在运动中 inert，不接收点击或焦点；归位恢复同一正文与控制。完成、取消和销毁都取消待执行帧并移除临时前景节点。

手机、空间不足的稳定阅读、大字号和减少动态效果采用静态落位。稳定阅读用 IntersectionObserver 识别真实 A3 可见性，环境暂停时也有效，不依赖 WebGL 持续刷新。22 张内容、原生横滑、分类、详情和全部工具保持可用。

录像是实际主站录屏，使用固定环境时间参数便于对照；飞入和导览时钟没有修改。MP4 全长约 4.32 秒，含进入界面前后的画面，卡牌飞入本身约 1.47 秒。

本步没有实现自动横向轨道、滚轮速度/惯性、悬停跟随或专门飞离动画，继续分别归属第 7—11 步。
''')

(DOC/'step-6-verification.md').write_text(f'''# 关于我改版 · 第六步验收

采用版本核对时间：{NOW}（Asia/Shanghai）。81 项浏览器检查通过，npm run build（含 TypeScript）通过，git diff --check 通过。

| 范围 | 结果 | 最终证据 |
| --- | ---: | --- |
| 飞入实体、触发、中断、适配和导览门槛 | 21/21 | [entrance-2](evidence/step-6/entrance-2/browser.json) |
| 装饰资源超时后的真实导览阅读 | 1/1 | [accepted-resource-guide](evidence/step-6/accepted-resource-guide/browser.json) |
| 主站多视口与完整阅读功能 | 44/44 | [accepted-main](evidence/step-6/accepted-main/browser.json) |
| 表面投影、阴影、首末展开、大字号 | 8/8 | [accepted-projection](evidence/step-6/accepted-projection/browser.json) |
| 影像、罗森、瓶中海洋、环境及连续导览 | 7/7 | [accepted-regressions](evidence/step-6/accepted-regressions/browser.json) |

五组检查均有源文件与生产资源清单，当前内容逐项 SHA 一致。主站检查的 A3 静态截图会等待真实入口 ready；飞行中的检查由专项逐帧完成，不以最终截图替代动画证据。

## 主要验收结果

- 初始四张实体表面完整位于视口外，实际画内出场顺序正确；飞行中有深度位移、旋转与可见背纹，不采用牌面淡入。
- 录像实际入场 {elapsed:.1f}ms；原 slot 在飞行到归位之间最大移动 {slot_gap:.4f}px，节点未复制，重复 ID 为零。
- 分类首击、原生 Enter 下一张、全部工具首击和 Escape、继续浏览首击、滚动离开、窗口缩到手机和阅读模式切换均正常；返回不重播。
- 原生窗口探测和阅读容量测量不触发；准备中离开再回来仍能首次播放。
- 390/320px、1366×768 稳定模式、200% 字号及减少动态效果直接阅读；运动中切换减少动态设置也能收尾。
- 自动导览在飞入时尚无阅读截止时间，落位后 readyAt 不早于 entranceFinishedAt；点击分类仍停止导览。资源准备超时后也能开始真实阅读。
- 实际罗森 iframe 的时间滑杆 Home、瓶中海洋暂停按钮与渲染诊断、关闭后 iframe 清理、影像返回及环境播放暂停恢复均通过。
- 等待或完成时不保留入场帧循环；卡牌节点归还原位，前景容器清空，临时尺寸移除。组件销毁路径另做源码检查：取消帧、代际令牌失效、AbortController 与观察器清理；未另称已进行浏览器内组件反复销毁压力测试。

[真实主站录像](evidence/step-6/step-6-entrance.mp4) · [飞入前段/背纹](evidence/step-6/accepted-motion/early.png) · [飞入中段](evidence/step-6/accepted-motion/middle.png) · [落位后](evidence/step-6/accepted-main/desktop-A3.png) · [手机](evidence/step-6/accepted-main/phone-A3.png)

[逐帧核对](evidence/step-6/motion-validation.json) · [录像版本上下文](evidence/step-6/accepted-motion-source-context.json) · [人工视觉核对](evidence/step-6/visual-review.json) · [构建](evidence/step-6/build-check.json) · [历史保护](evidence/step-6/protection-final.json)

## 过程记录和实际限制

inspection-1 显示初版起点过远，后发卡牌可能先进入画内；改为按实际投影边缘求解画外起点，并延后背面转正，使背纹在画内可见。inspection-2 未成功建立录屏页，原因是录屏工具默认缓存路径，之后使用工作区已有 ffmpeg 完成，不下载新依赖。

entrance-1 为 11/21。实际发现稳定阅读在环境暂停时没有刷新入场就绪状态，已加入独立的交叉观察触发。其余失败来自检查工具取到轨道尾部卡牌、全部网格没有 slot 时的记录器空引用、原生 focus 先于 click 中断以及导览 moving/arriving 的阶段断言；均修正记录器或断言后保留原始失败文件。当前源文件随后通过 entrance-2 21/21 和全部最终回归。

浏览器为 Linux Chromium 155.0.8059.79，视口模拟不代表物理手机或 Safari/Firefox。页面隐藏分支使用明确标记的模拟 visibilitychange；资源延迟通过测试页面临时覆盖图像 complete 属性，不修改生产代码。主动禁用 WebGL 的主站降级案例有两条预期报错，普通案例没有新增运行错误。

2,003 个第五步及更早的历史文件 SHA 未变化。正文、22 个本地图案、依赖和两个嵌入网页未更改。已关闭本次两个专用验收服务，端口关闭，其他服务未停止；未提交、推送或发布。
''')

(DOC/'step-6-handoff.md').write_text(f'''# 关于我改版 · 第六步交接

状态：第六步完成，{NOW}（Asia/Shanghai）。应从此工作区继续第七步，先细化、待用户指令执行；本次未提交、推送或发布。

[实现说明](step-6-entrance.md) · [验收](step-6-verification.md) · [实际录像](evidence/step-6/step-6-entrance.mp4)

## 可复用接口

| 位置 | 当前职责 |
| --- | --- |
| createCardEntrance.ts | 一次性四张飞入、资源准备、投影起点、有限帧循环、归还和取消 |
| cardEntrance.css | 独立裁切窗口与共享透视舞台；运动期间禁用轨道 snap |
| createToolBrowser.ts | 入场控制器与已有分类/详情/全部工具/状态恢复衔接 |
| createAboutView.ts | presentToolsEntrance、cancelToolsEntrance、toolsEntranceReady 转发 |
| createPillarReader.ts | 实际 A3 触发、静态 IntersectionObserver、排除 measuring 的调度 |
| startTourPrototype.ts | 就绪唤醒与 A3 导览阅读门槛，其他站点图片检查保留 |
| createToolCard.ts / toolCards.css | 原实体增加 roll 姿态，阴影跟随定位层，静态阅读外观保留 |

presentEntrance 接收 active、enabled、revealed；cancelEntrance(reason) 结束待播/飞行并静态归位；entranceReady 表示可以阅读。AboutViewOptions.onEntranceChange 负责就绪状态通知，宿主只唤醒导览或单次渲染，不发起容量重测。数据属性 entrance、entranceReady、entranceReason、entrancePlays、entranceFramePending 可用于检查。

## 第七步自动轨道的接入约束

1. 入口 preparing/playing 时不能启动轨道。ready/completed 后才允许按第七步的播放规则开始。cancelled 也表示可阅读，但不代表可以自动恢复用户已中断的展示。
2. 下一步必须独立区分主站自动导览、工具自动展示和环境播放；不要把它们绑定同一个暂停状态。
3. 全 22 张默认顺序与七类顺序继续来自原 content.ts。入场只处理首批四张，其他卡仍在原轨道正常占位。
4. 飞行结束已把同一节点放回 slot，清空 foreground 并移除临时宽高；轨道应以归位后的真实尺寸初始化。
5. 卡牌 position、reading、orientation 分层保持。当前 roll 扩展会更新侧边受光；未来轨道倾角与悬停不能争写同一 transform。
6. 原生 scroll-snap 在手机正常启用，仅 playing 时临时关闭。第七步须明确程序轨道与原生滚动的拥有关系；滚轮速度和惯性仍由第八步实现。
7. 分类、下一张、全部工具和焦点可以中断入场，且首个操作生效。未来轨道启停同样要保留这些行为、焦点恢复和原分类/位置/详情状态。
8. 静态降级 ready/static-reading 不播放完整飞入；减少动态和窄屏的自动展示策略需由第七步明确，不能仅因 ready 就强制自动运动。
9. measuring=true 的容量探测不消费首次入场，也不能在未来启动或重置自动轨道。真实主站 A3 阅读容量与阴影余量仍需保持。
10. 入场使用有限独立时钟，环境暂停不影响落位；当前没有自动横移、滚轮加速、鼠标跟随或飞离。第七步不得提前吞并第八至十一步的交互。

后续新增基线与证据，不覆盖本步或旧记录。当前 HEAD 仍为 {baseline['head']}，修改保存在工作区；生产构建和 81 项检查通过。开发运行 npm run dev，从主站第三屏首次进入可观察完整飞入；刷新可重新验收，返回 A3 本身不重播。
''')

save(OUT/'final-summary.json',{'completedAtShanghai':NOW,'status':'第六步完成','suites':suites,'totalPassedChecks':sum(v['passed'] for v in suites.values()),'motionDurationMS':elapsed,'video':row(OUT/'step-6-entrance.mp4'),'sourceMatchesFinalEvidence':True,'build':read(OUT/'build-check.json'),'historicalArtifactsUnchanged':len(baseline['historicalArtifacts']),'servicesCleanup':cleanup,'notImplemented':['automatic-track','wheel-velocity-inertia','pointer-follow-hover','flight-out'],'committed':False,'pushed':False,'published':False})
for name in ['step-6-entrance.md','step-6-verification.md','step-6-handoff.md']:
 path=DOC/name
 for link in re.findall(r'\]\(([^)]+)\)',path.read_text()):assert (path.parent/link).exists(),(path,link)
assert all(current(v) for v in baseline['historicalArtifacts'])
files=sorted([p for p in OUT.rglob('*') if p.is_file() and p.name!='evidence-manifest.json']+[DOC/name for name in ['step-6-entrance.md','step-6-verification.md','step-6-handoff.md']])
save(OUT/'evidence-manifest.json',{'recordedAtShanghai':NOW,'files':[row(p) for p in files],'excludesSelf':True})
print(json.dumps({'status':'通过','browserChecks':81,'actualMotionMS':elapsed,'historicalFilesUnchanged':2003,'servicesClosed':True,'published':False},ensure_ascii=False))
