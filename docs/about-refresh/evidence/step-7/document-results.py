from pathlib import Path
from hashlib import sha256
from datetime import datetime
from zoneinfo import ZoneInfo
import json,re,subprocess
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).parent;DOC=OUT.parents[1]
NOW=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
read=lambda p:json.loads(p.read_text())
save=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
git=lambda *a:subprocess.check_output(['git',*a],cwd=ROOT,text=True).strip()
def row(p):
 data=p.read_bytes();return {'path':str(p.relative_to(ROOT)),'bytes':len(data),'sha256':sha256(data).hexdigest()}
def current(item):
 p=ROOT/item['path'];return p.exists() and row(p)==item
baseline=read(OUT/'baseline.json');assert all(current(v) for v in baseline['historicalArtifacts'])
changed=[v['path'] for v in baseline['sourceFilesBefore'] if not current(v)]
assert set(changed)=={'src/tour/createPillarReader.ts','src/tour/about-refresh/createToolBrowser.ts','src/tour/about-refresh/createAboutView.ts','src/tour/about-refresh/types.ts'},changed
assert git('rev-parse','HEAD')==git('rev-parse','origin/main')==baseline['head']
assert set(git('diff','--name-only').splitlines())==set(baseline['trackedChangesBefore']);assert not git('diff','--cached','--name-only')
subprocess.run(['git','diff','--check'],cwd=ROOT,check=True)
suites={}
for name,count in [('delivery-components',49),('delivery-state',5),('verified-hit',2),('verified-regressions',7),('verified-projection',8)]:
 d=read(OUT/name/'browser.json');assert d['complete'] and len(d['checks'])==count and all(c['status']=='通过' for c in d['checks']),name
 assert d.get('browserClosed',d.get('cleanup',{}).get('browserClosed')) is True,name
 suites[name]={'passed':count,'report':name+'/browser.json'}
 if (OUT/name/'source-manifest.json').exists():assert all(current(v) for v in read(OUT/name/'source-manifest.json')),name
 else:
  build=read(OUT/name/'build.json');assert current(build['output']) and all(current(v) for v in build['sources']),name

# Retain the old locator-stability timeout; adopt the single native-pointer rerun.
main=read(OUT/'verified-main/browser.json');pointer=read(OUT/'verified-main-pointer/browser.json')
assert main['cleanup']['browserClosed'] and len(main['checks'])==44 and pointer['complete'] and len(pointer['checks'])==1 and pointer['checks'][0]['id']=='card-detail' and pointer['checks'][0]['status']=='通过'
main_adopted=[v for v in main['checks'] if v['id']!='card-detail'];assert len(main_adopted)==43 and all(v['status']=='通过' for v in main_adopted)
for name in ['verified-main','verified-main-pointer']:assert all(current(v) for v in read(OUT/name/'source-manifest.json'))
save(OUT/'verified-main/adoption.json',{'recordedAtShanghai':NOW,'complete':True,'passed':44,'originalRunAllPassed':main['complete'],'sources':['browser.json','../verified-main-pointer/browser.json'],'reason':'The old locator waits for a moving button to become stable. Only that case was rerun with real mouse coordinates; no runtime code changed between these runs. Original timeout is retained.','checks':[{'id':v['id'],'status':v['status'],'adoptedFrom':'../verified-main-pointer/browser.json' if v['id']=='card-detail' else 'browser.json'} for v in [*main_adopted,pointer['checks'][0]]]})
suites['verified-main']={'passed':44,'report':'verified-main/adoption.json'}

# The frame-aligned timing rerun replaces only the speed check; return is corroborative.
track=read(OUT/'verified-track/browser.json');assert track['complete'] and len(track['checks'])==27
functional=[c for c in track['checks'] if c['id']!='measured-base-speed'];assert len(functional)==26 and all(c['status']=='通过' for c in functional)
assert all(current(v) for v in read(OUT/'verified-track/source-manifest.json'))
timing=read(OUT/'verified-timing/browser.json');assert timing['complete'] and len(timing['checks'])==2 and all(c['status']=='通过' for c in timing['checks'])
assert all(current(v) for v in read(OUT/'verified-timing/source-manifest.json'))
velocity=read(OUT/'verified-timing/measured-base-speed-data.json')['details']['measuredPXPerSecond']
suites['verified-track']={'passed':26,'report':'verified-track/browser.json','adoptedIDs':[c['id'] for c in functional]}
suites['verified-timing']={'passed':1,'report':'verified-timing/browser.json','adoptedIDs':['measured-base-speed'],'corroborativeIDs':['leave-return-resumes'],'measuredPXPerSecond':velocity}

cycle=read(OUT/'verified-cycle/browser.json');assert cycle['complete'] and cycle['browserClosed'] and not cycle['errors']
assert len(cycle['seenIDs'])==22 and cycle['recycles']>=22
assert all(current(v) for v in read(OUT/'verified-cycle/source-manifest.json'))
suites['verified-cycle']={'passed':1,'report':'verified-cycle/browser.json','seen':22,'recycles':cycle['recycles'],'seconds':cycle['naturalDurationSeconds']}
motion=read(OUT/'verified-motion/browser.json');assert motion['complete'] and not motion['errors'] and motion['browserClosed']
assert all(current(v) for v in read(OUT/'verified-motion/source-manifest.json'))
assert read(OUT/'services-cleanup.json')=={'servicesStopped':2,'portClosed':True,'otherServicesStopped':False}
assert 'typecheck' in (OUT/'build-12.txt').read_text() and 'built in' in (OUT/'build-12.txt').read_text()
save(OUT/'build-check.json',{'command':'npm run build','includes':'npm run typecheck && vite build','exitCode':0,'output':'build-12.txt','outputSHA256':row(OUT/'build-12.txt')['sha256']})
for v in read(OUT/'verified-main/source-manifest.json'):
 if v['path'].startswith('dist/') and v['path'].endswith(('.js','.css')):
  text=(ROOT/v['path']).read_text()
  assert not any(key in text for key in ['__aboutRefreshPreview','__toolCardReview','__cycleEvidence','__entranceEvidence'])
save(OUT/'protection-final.json',{'checkedAtShanghai':NOW,'historicalArtifactsUnchanged':len(baseline['historicalArtifacts']),'historicalArtifactsChanged':[],'existingSourceChanged':changed,'newRuntimeFiles':['src/tour/about-refresh/createCardTrack.ts','src/tour/about-refresh/cardTrack.css'],'publicCopyMarksAndEmbeddedSitesUnchanged':True,'dependenciesChanged':False,'head':git('rev-parse','HEAD'),'localOriginMain':git('rev-parse','origin/main'),'gitDiffCheck':'通过','stagedChanges':[],'committed':False,'pushed':False,'published':False})

visuals={
 'verified-motion/running.png':'缓慢展示中保留石质材质，中央清晰，两侧浅弧形后退；操作带可见。',
 'verified-motion/paused.png':'暂停按钮和提示切为继续阅读，牌面停在原处。',
 'verified-motion/resumed.png':'原进度继续，弧度保持，基础速度逐渐恢复。',
 'verified-cycle/before-seam.png':'真实速度完整一轮后的首尾相邻画面。',
 'verified-cycle/after-seam.png':'首尾交接之后继续移动，卡距和阅读区域保持。',
 'verified-main/phone-A3.png':'手机保留原生横滑、按钮、分类和完整详情入口。',
}
save(OUT/'visual-review.json',{'reviewedAtShanghai':NOW,'method':'Final screenshots manually inspected with view_image; natural-speed recording, DOM identity checks and native pointer tests supplement visual checks.','files':[{'path':k,'finding':v,'sha256':row(OUT/k)['sha256']} for k,v in visuals.items()],'limits':'Linux Chromium and emulated viewports, not physical-phone or Safari/Firefox coverage.'})

(DOC/'step-7-track.md').write_text(f'''# 关于我改版 · 第七步自动轨道

状态：已接入工作区主站。核对时间 {NOW}（Asia/Shanghai）。未提交、推送或发布。

[观看主站演示](evidence/step-7/step-7-display.mp4) · [观看真实循环接缝](evidence/step-7/step-7-seam.mp4) · [验收](step-7-verification.md) · [第八步交接](step-7-handoff.md)

## 观看与操作

四张卡正常飞入并归位后，普通宽幅沉浸模式停留约500ms，再用约300ms平滑起速。卡牌向左以28 CSS px/s持续展示，约9秒推进一个普通卡位；这次独立测得基础速度 {velocity:.3f}px/s。

中央阅读区保持正面，边缘最多下移6px、后退28px、向中央转6°，构成浅弧形。没有额外缩小字号或淡化牌面。原有暖白石面、草木绿、水蓝分类、刻纹、侧边和清晰 HTML 正文保留。

操作带加入“暂停自动展示 / 继续自动展示”。暂停立即停止推进，继续从原位置恢复；弧度与速度分别管理，恢复时不把弧度重置为平面。按钮支持鼠标、Enter和空格，保持至少44px触摸高度。当前卡号只在逻辑卡位变化时更新，aria-live关闭，避免自动移动持续播报。

鼠标进入卡牌区域不暂停、不加速。点击前后按钮会暂停并移动一个逻辑卡位，桌面编排支持首尾相邻；点击详情先交还原生轨道，再使用现有完整阅读处理。键盘进入卡牌会暂停，并在必要时把焦点卡放入可读位置；指针点击局部卡时不会在点击完成前移动按钮。

## 循环与同一节点

始终只有22张真实卡牌和22个唯一工具ID，DOM顺序继续使用已确认的推荐顺序。循环以逻辑偏移、卡片ID、卡位内比例和是否完成首轮记录位置；不复制可聚焦卡牌。只有实际投影及阴影完全离屏后才移动到队尾。首轮不会提前从左侧露出末尾卡，22→1连续衔接。

最终版真实速度运行约 {cycle['naturalDurationSeconds']:.2f} 秒，22张均进入画面，记录 {cycle['recycles']} 次离屏换位，并核对跨循环边界的实际帧坐标。所有实例ID在整轮中保持，原始全程WebM保留；发布用短接缝片段只是原录像截取，没有加速或重画。

## 模式与恢复

普通宽幅沉浸模式正常入场后默认自动；宽屏稳定阅读默认手动，轨道和操作区域完整可见时允许主动开启。当前分类不足一屏则完整静态展示，不强制复制或循环。

分类、详情、全部工具和原生手动接管会暂停；全部工具返回保留分类、逻辑位置、弧度和暂停选择。离开A3暂停更新，未主动暂停时返回后可继续；主动暂停保持。后台返回等待手动继续，不补算离开期间的移动距离。手机、大字号、减少动态效果使用原生手动阅读。手机接管后的新卡位会成为恢复宽屏时的当前位置。

桌面程序编排关闭原生吸附，交还原生模式恢复原有横滑。横向手势首个事件只做一次原生位移交接，后续交给浏览器；纵向滚轮继续控制网页与镜头，没有本步的纵向转横向、速度映射或惯性。

主站导览、卡牌展示和环境播放分别管理。程序推进不算用户操作，不会误停导览；实际操作仍按主站既有规则交还控制。暂停环境不暂停工具展示，继续工具展示不会启动主站导览。

## 实现边界

新增createCardTrack.ts和cardTrack.css，原生轨道、飞入和循环复用当前卡牌节点；分类和全部工具按既有生命周期重建，活动模式中每个ID始终只有一份正文。程序只在运行时请求帧；离屏、暂停、后台和销毁停止更新。速度按经过时间推进，异常长帧限制跨度，避免阻塞后猛跳。可见牌和邻近牌更新空间姿态；循环换位保留原节点。没有新增Canvas、WebGLRenderer、依赖或外部资源。

三维编排父层不接收点击，真实牌面接收点击，避免退后的按钮被透明容器遮挡。原生交接保存并恢复焦点，快照包含逻辑位置、播放选择、首轮标志和当前弧度。容量测量不触发或重置轨道。

第八步的滚轮速度/反向/惯性、第九步的悬停放大和跟随倾斜、第十步的进一步详情呈现、第十一步的飞离均未提前加入。
''')

(DOC/'step-7-verification.md').write_text(f'''# 关于我改版 · 第七步验收

最终版本核对：{NOW}（Asia/Shanghai）。采用143项通过检查；npm run build（含TypeScript）、git diff --check通过。所有采用报告的源文件和资源SHA与当前交付一致。

| 范围 | 通过 | 采用报告 |
| --- | ---: | --- |
| 轨道功能、暂停姿态、分类、输入、适配与导览 | 26 | [verified-track](evidence/step-7/verified-track/browser.json)，除速度项 |
| 同一动画帧对齐的基础速度复测 | 1 | [verified-timing](evidence/step-7/verified-timing/browser.json)，返回项为补充复核不重复计数 |
| 原有静态组件功能 | 49 | [delivery-components](evidence/step-7/delivery-components/browser.json) |
| 播放/暂停/全部工具快照、重建和销毁 | 5 | [delivery-state](evidence/step-7/delivery-state/browser.json) |
| 首末牌面实际命中、原生点击与焦点 | 2 | [verified-hit](evidence/step-7/verified-hit/browser.json) |
| 真实主站多视口及原有阅读功能 | 44 | [verified-main采用汇总](evidence/step-7/verified-main/adoption.json) |
| 浅弧形和详情表面、阴影边界 | 8 | [verified-projection](evidence/step-7/verified-projection/browser.json) |
| 影像、罗森、瓶中海洋、环境与连续导览 | 7 | [verified-regressions](evidence/step-7/verified-regressions/browser.json) |
| 真实速度完整22张循环 | 1 | [verified-cycle](evidence/step-7/verified-cycle/browser.json) |

并发的delivery-track运行曾出现基础速度偏低与返回时序检查失败，原记录保留。最终版将返回激活收紧为镜头停稳、牌面可读，轨道交互26项通过。原速度检查跨帧读取距离与时间，仍有采样偏差；改为在同一requestAnimationFrame时间戳读取后，速度与返回两项复测通过，速度实测 {velocity:.3f}px/s，只把速度项另计一次。异常长帧限制用于避免阻塞后猛跳，旧失败没有覆盖或改写。

## 关键结果

完整自然运行 {cycle['naturalDurationSeconds']:.2f} 秒，22个ID全部出现，实例未替换；{cycle['recycles']}次换位均在实际牌面离屏后发生，循环边界前后帧坐标连续，未修改时钟。原始全程录像与逐帧接缝数据保留。普通演示录像包含运行、暂停及原生Enter继续。

返回全部工具保持实际逻辑偏移和牌面弧度；尺寸变化保持卡牌ID与卡位比例；手机操作后恢复宽屏沿用新位置。运行和暂停快照可跨组件重建，旧实例销毁后不再更新。局部露出的第四张卡首次点击可打开完整详情，键盘焦点保持。

主站多视口覆盖1920/1440/1366/1280/1024/820/390/320及横屏、小屏、大字号、减少动态和图形不可用降级。两个嵌入网页通过真实原生操作验证：罗森时间滑杆Home，瓶中海洋暂停及实际渲染诊断；关闭后iframe清理。图形不可用案例保留两条预期错误，常规主站案例无新增运行错误。

[自动展示演示](evidence/step-7/step-7-display.mp4) · [循环接缝](evidence/step-7/step-7-seam.mp4) · [运行画面](evidence/step-7/verified-motion/running.png) · [暂停画面](evidence/step-7/verified-motion/paused.png)

[构建记录](evidence/step-7/build-check.json) · [历史保护](evidence/step-7/protection-final.json) · [视觉核对](evidence/step-7/visual-review.json) · [最终汇总](evidence/step-7/final-summary.json)

## 过程记录与限制

早期过程发现并修复：原生横向首个事件被丢弃、退后牌面被透明父层拦截、归还节点丢失焦点、稳定阅读误用已移位底栏的边界、恢复播放时弧度回零、指针点击局部卡前提前对齐按钮，以及原生接管后保留旧轨道锚点。相关失败、定位日志和被替代的运行目录保留，最终采用只以上表为准。

部分旧主站测试使用scrollLeft判断全部工具返回位置，已按程序模式改查逻辑位置；文字范围与真实牌面投影比较。主站详情测试原本等待移动按钮稳定，改为真实鼠标事件后单项通过；采用汇总明确链接原43项与该1项复测，原超时不覆盖。旧记录器访问已被移除的子节点导致的空引用也保留并修正。较早的自然运行属于调试版本，不替代最终整轮验收。两个被中止的录屏任务在关闭阶段挂起，已核对其命令及父子关系，只清理这些自有进程树；部分录像不纳入采用，见evidence/step-7/cancelled-recorders-cleanup.json。

录像固定环境时间便于核对卡牌，飞入、轨道及导览时钟未加速。浏览器为Linux Chromium，手机为视口模拟；页面隐藏分支明确使用模拟visibility事件，没有宣称物理手机、Safari或Firefox验证。

2,353个第六步及更早文件的SHA原样保留，正文、图案、依赖和嵌入网页未修改。已关闭本次两个专用验收服务，其他服务未停止；未提交、推送或发布。
''')

(DOC/'step-7-handoff.md').write_text(f'''# 关于我改版 · 第七步交接

状态：第七步完成，{NOW}（Asia/Shanghai）。继续第八步前先细化滚轮速度、方向与惯性标准，待用户指令执行。未提交、推送或发布。

[实现说明](step-7-track.md) · [验收](step-7-verification.md) · [主站录像](evidence/step-7/step-7-display.mp4)

## 第八步可直接使用

createCardTrack统一管理基础速度28、逻辑phase、period、单一帧循环、空间bend和原节点循环。对外有present、pause、play、step、position、capture、restore、native、refresh、clear和dispose；createToolBrowser持有唯一控制器，createAboutView.presentToolsTrack由真实宿主驱动。没有现成的滚轮速度API；第八步在同一个tick模型中加入输入速度贡献，不再创建第二套横移循环。

CardTrackSnapshot记录position（anchorId/offsetRatio）、program、cycled、enabled、decided、bend。恢复不使用离开时长，不追赶后台时间。弧度和起速eased分开，不能再次用速度进度覆盖已建立的bend。前景飞入完成后节点归位，轨道才初始化；cancelled/ready不等于自动播放授权。

当前横向手势桥位于createToolBrowser的rail wheel监听：只有程序模式且abs(deltaX)>abs(deltaY)时，把首个事件移交原生位移一次；后续原生事件不重复消费。纵向滚轮没有被截获。第八步应在这里统一输入所有权和边界条件，避免新增重复监听、同一事件消费两次或把详情/全部工具中的滚轮变成轨道输入。

## 必须保留

1. 主导览、环境播放、工具展示分别管理，程序推进不调用onInteraction；用户操作仍停止主导览。
2. 暂停停止帧，继续保留phase和bend；减少动态、后台、手机、大字和模式切换按既定规则处理。
3. 每个工具只有一个真实节点。循环换位必须连同阴影离屏，保持首轮不提前露出末尾牌；不能用复制ID拼无限列表。
4. 只有真实牌面接收指针，编排stage、slot和实体容器不接收指针。键盘焦点可对齐，指针焦点不得在click前搬走局部卡的按钮。
5. 原生手动接管清除过期程序锚点；全部工具返回与快照恢复则保留程序位置、弧度与暂停选择。二者不能混用。
6. 同一position/reading/orientation层持续复用，后续悬停姿态要与轨道基姿态合成，不能直接争写transform。
7. 稳定模式底部边界来自视口，沉浸模式才扣除固定底栏。容量测量不重置或触发轨道，尺寸重测按真实卡牌ID和比例恢复。
8. 查看全部仍为七类22张，默认及分类两套顺序不变；正文不增加项目、奖项、业绩和作品入口。

当前工作区相对本步基线只修改createPillarReader、createAboutView、createToolBrowser和types，新增createCardTrack/cardTrack.css。主站入口与Three场景资源未另改。后续新建基线和证据，不覆盖本步档案。HEAD仍为 {baseline['head']}；开发运行npm run dev，进入A3观察首批飞入与自动轨道，返回不会重播飞入。
''')

total=sum(v['passed'] for v in suites.values());assert total==143,total
save(OUT/'final-summary.json',{'completedAtShanghai':NOW,'status':'第七步完成','suites':suites,'totalPassedChecks':total,'measuredPXPerSecond':velocity,'naturalCycleSeconds':cycle['naturalDurationSeconds'],'seenTools':22,'offscreenRecycles':cycle['recycles'],'allAdoptedSourcesMatch':True,'historicalArtifactsUnchanged':len(baseline['historicalArtifacts']),'video':row(OUT/'step-7-display.mp4'),'seamVideo':row(OUT/'step-7-seam.mp4'),'servicesCleanup':read(OUT/'services-cleanup.json'),'committed':False,'pushed':False,'published':False,'notImplemented':['wheel-velocity-inertia','pointer-follow-hover','flight-out']})
for name in ['step-7-track.md','step-7-verification.md','step-7-handoff.md']:
 path=DOC/name
 for link in re.findall(r'\]\(([^)]+)\)',path.read_text()):assert (path.parent/link).exists(),(path,link)
assert all(current(v) for v in baseline['historicalArtifacts'])
files=sorted([p for p in OUT.rglob('*') if p.is_file() and p.name!='evidence-manifest.json']+[DOC/name for name in ['step-7-track.md','step-7-verification.md','step-7-handoff.md']])
save(OUT/'evidence-manifest.json',{'recordedAtShanghai':NOW,'files':[row(p) for p in files],'excludesSelf':True})
print(json.dumps({'status':'通过','checks':total,'speed':velocity,'cycleSeconds':cycle['naturalDurationSeconds'],'historicalProtected':2353,'published':False},ensure_ascii=False))
