from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib,json,subprocess

ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).parent;DOC=OUT.parents[1]
now=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
save=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
base=json.loads((OUT/'baseline.json').read_text())
changed=[e['path'] for e in base['sources'] if sha(ROOT/e['path'])!=e['sha256']]
expected={'src/tour/createPillarReader.ts',*[f'src/tour/about-refresh/{name}' for name in ['types.ts','createCardHover.ts','createAboutView.ts','createToolBrowser.ts','createCardTrack.ts','createToolCard.ts']]}
assert set(changed)==expected,changed
bad=[e['path'] for e in base['protectedHistory'] if not (ROOT/e['path']).exists() or sha(ROOT/e['path'])!=e['sha256']]
assert not bad,bad
sources=[p for p in (ROOT/'src/tour').rglob('*') if p.is_file()]+list((ROOT/'src/assets/tool-marks').glob('*.svg'))
old={e['path'] for e in base['sources']};new=[str(p.relative_to(ROOT)) for p in sources if str(p.relative_to(ROOT)) not in old]
assert set(new)=={'src/tour/about-refresh/createCardDeparture.ts','src/tour/about-refresh/cardDeparture.css'},new
groups=[]
runs=[('components-2',20),('main-1',24),('main-native-selector',1),('interaction-components',3),('interaction-main',3),('regression-detail-components',23),('regression-detail-main',26),('regression-shadow',1),('regression-wheel',15),('regression-cycle',2),('regression-existing',7),('regression-projection',8)]
for name,count in runs:
 folder=OUT/name;report=json.loads((folder/'browser.json').read_text())
 passed=[c for c in report['checks'] if c['status']=='通过']
 if name=='main-1':
  rejected=[c for c in report['checks'] if c['status']!='通过']
  assert len(report['checks'])==25 and len(rejected)==1 and rejected[0]['id']=='stable-wide-keeps-native-reading' and 'strict mode violation' in rejected[0]['error']
 else:assert report['complete'] and len(report['checks'])==count,name
 assert len(passed)==count and not report.get('events'),name
 assert report.get('browserClosed',report.get('cleanup',{}).get('browserClosed')),name
 records=json.loads((folder/'source-manifest.json').read_text()) if (folder/'source-manifest.json').exists() else []
 if (folder/'build.json').exists():
  build=json.loads((folder/'build.json').read_text());assert sha(ROOT/build['output']['path'])==build['output']['sha256'],name;records+=build['sources']
 assert records and all(sha(ROOT/e['path'])==e['sha256'] for e in records),name
 groups.append({'run':name,'checks':count,'ids':[c['id'] for c in passed],'finalSourcesMatch':True,'partialRun':name=='main-1'})
assert sum(g['checks'] for g in groups)==133
main_ids=[c for g in groups if g['run'] in ['main-1','main-native-selector'] for c in g['ids']];assert len(main_ids)==len(set(main_ids))==25
save(OUT/'adoption.json',{'total':133,'allPassed':True,'groups':groups,'excludedDevelopmentRuns':['inspection-1','components-1','click-probe','click-fixed'],'excludedChecks':[{'run':'main-1','id':'stable-wide-keeps-native-reading','reason':'测试选择器同时匹配 main 的当前锚点和实际 A3 章节；未计入最终通过数。','replacementRun':'main-native-selector'}],'notes':['components-1 和 click-probe 记录返回按钮继续移动、实际点击落到相邻牌面的情况。增加有意移入暂停后，测试按先移入、再对准停稳按钮的真实操作验证唯一一次原生点击。','components-2 的 20 项通过与 main-1 中 24 项通过均为最终 build-4；主站唯一未通过项为选择器冲突，限定真实阅读流后单独复验通过。没有重复计数或混用旧版运行。','interaction-components/main 各补充 3 项鼠标暂停继续、指针取消和键盘检查。','先前 82 项详情、滚轮、循环、阴影、作品与投影回归全部在 build-4 重新执行通过。']})
assert subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True).returncode==0
assert subprocess.run(['git','diff','--cached','--quiet'],cwd=ROOT).returncode==0
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();remote=subprocess.check_output(['git','rev-parse','refs/remotes/origin/main'],cwd=ROOT,text=True).strip();assert head==remote==base['head']
cleanup=json.loads((OUT/'services-cleanup.json').read_text());assert cleanup['portClosed'] and cleanup['servicesStopped']==2
services=json.loads((OUT/'services-started.json').read_text());assert all(not Path('/proc',str(p['pid'])).exists() for p in services['services'])
production=[ROOT/'dist/index.html',*(ROOT/'dist/assets').glob('startTourPrototype*')]
build_passed='✓ built in' in (OUT/'build-4.txt').read_text();assert build_passed
save(OUT/'source-freeze.json',{'checkedAtShanghai':now,'buildLog':'build-4.txt','buildPassed':True,'sources':[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sources+production]})
save(OUT/'protection-final.json',{'checkedAtShanghai':now,'changedRuntime':changed,'newRuntime':new,'otherBaselineSourcesUnchanged':len(base['sources'])-len(changed),'historicalFilesUnchanged':len(base['protectedHistory']),'historicalMismatches':bad,'contentAndMarksUnchanged':True,'head':head,'localOriginMain':remote,'indexUnchanged':True,'pushed':False,'published':False,'servicesClosed':True})
forward=json.loads((OUT/'main-1/forward-visible-entities-data.json').read_text());reverse=json.loads((OUT/'main-1/reverse-visible-entities-data.json').read_text());pin=json.loads((OUT/'main-1/pinned-wide-preserves-full-text-data.json').read_text());shadow=json.loads((OUT/'regression-shadow/shadow-behind-front-pixel-check-data.json').read_text());guide=json.loads((OUT/'main-1/guide-remains-active-on-departure-data.json').read_text());video=json.loads((OUT/'video-metadata.json').read_text());paused=json.loads((OUT/'main-1/paused-world-independent-flight-data.json').read_text())
assert sha(ROOT/video['source'])==video['sourceSHA256'] and sha(ROOT/video['target'])==video['targetSHA256']
done=next(f for f in forward['frames'] if f['phase']=='departed');widths=[c['width'] for f in pin['frames'] for c in f['cards'] if c['id']=='comfyui'];assert widths and min(widths)>=339
metrics={'visibleCards':forward['during']['d']['departureIds'].split(','),'fourCardTargetDurationMs':int(forward['during']['d']['departureDuration']),'observedFirstDepartedFrameMs':done['t']-float(forward['during']['d']['departureStartedAt']),'forwardHandoffErrorPx':float(forward['during']['d']['departureHandoffError']),'reverseHandoffErrorPx':float(reverse['during']['d']['departureHandoffError']),'minimumFixedCardWidthAcrossExitAndReturnPx':min(widths),'fixedReadingId':pin['settled']['d']['readingId'],'guidePhaseDuringDeparture':guide['world']['guide'],'worldTimeWhilePaused':[paused['paused']['world']['time'],paused['departed']['world']['time']],'shadowInteriorDifferentPixels':[x['differentPixels'] for x in shadow]}
assert metrics['worldTimeWhilePaused'][0]==metrics['worldTimeWhilePaused'][1]
save(OUT/'final-summary.json',{'completedAtShanghai':now,'step':11,'status':'completed','acceptedChecks':133,'metrics':metrics,'clockModified':False,'physicalHardwareTested':False,'video':video['target'],'nextStep':12,'unpublished':True})
save(OUT/'visual-review.json',{'reviewedAtShanghai':now,'reviewed':['main-1/demonstration-flight.png','video-3.8.png','video-5.3.png','video-5.5.png','video-6.2.png','main-1/resize-interrupts-fixed-flight.png'],'observations':['暖白石牌与清新庭院保持，错峰转身有清楚的厚度、侧边和背面刻纹。','卡片通过实体空间运动离开展示窗口，正文透明度没有提前盖掉飞行。','回收后固定介绍完整，手机尺寸切换后同一固定卡仍完整可读。','源码保持原透视链和原节点，不存在前景副本或残留影子。','录像为实际主站原速录制；waterTime=2 仅固定世界画面，环境暂停独立性另用正常世界时间验证。'],'accepted':True})
(DOC/'step-11-verification.md').write_text(f'''# 关于我改版 · 第十一步验收

完成：{now}（Asia/Shanghai）。本步完成，未提交、推送或发布。

[实现说明](step-11-departure.md) · [第十二步交接](step-11-handoff.md) · [{float(video['deliveryMetadata']['format']['duration']):.2f} 秒实际主站录像](evidence/step-11/step-11-departure.mp4)

## 最终结果

**133 项最终采纳检查通过**。`npm run build`（包含类型检查）与 `git diff --check` 通过，全部采纳记录匹配当前 build-4 源码 SHA256。Chromium 155.0.8059.79；滚轮、指针和键盘使用浏览器原生输入，页面定位经过真实 scrollTo 路径。组件另以宿主接口提供阅读上下文。未修改动画时钟，未使用实体设备或其他浏览器验收。

| 范围 | 通过数 | 记录 |
| --- | ---: | --- |
| 离场组件：方向、当前实体、折返、分类、展开、首次点击和生命周期 | 20 | components-2 |
| 真实主站：上述场景、导览、世界暂停、快捷导航、稳定阅读与录像 | 25 | main-1 采用 24 项，main-native-selector 采用 1 项 |
| 返回操作：移入暂停/移开继续、指针取消、键盘焦点与 Enter/Escape | 6 | interaction-components / interaction-main |
| 第十步组件与主站全文详情回归 | 49 | regression-detail-components / regression-detail-main |
| 原生滚轮速度、方向、首事件、按钮和场景时钟 | 15 | regression-wheel |
| 22 张及五张分类的双向整圈循环 | 2 | regression-cycle |
| 阴影牌面内区像素检查 | 1 | regression-shadow |
| 原有影像、罗森、漂流瓶、环境和章节导览 | 7 | regression-existing |
| 宽屏、手机、首末详情及大字实际投影 | 8 | regression-projection |

[逐项采纳清单](evidence/step-11/adoption.json) · [源码冻结](evidence/step-11/source-freeze.json)

## 关键实测

- 四张正常离场目标 **{metrics['fourCardTargetDurationMs']} ms**，首个 departed 观测帧约 **{metrics['observedFirstDepartedFrameMs']:.1f} ms**。正向、反向接管的实际十面边界误差均为 **0 px**。
- 当前默认可见卡为 {', '.join(metrics['visibleCards'])}；分类、两张原生轨道、边缘卡和末张 Vibe Coding 也分别验证。节点实例与槽位不变，没有复制卡牌或增加画布。
- 转身时在窗口内测得超过 100° 的姿态，录像 3.8 秒处可见背面刻纹。牌面在飞行中保持完整有效透明度，十面和阴影终点位于窗口外至少约 36 px。
- 离场中反向返回从当前姿态回收，离场后返回恢复同一轨道位置。原先自动开启则在回收后继续，原先暂停则保持暂停，首批入场不重播。
- 固定阅读全过程记录的 ComfyUI 自然宽度最小 **{metrics['minimumFixedCardWidthAcrossExitAndReturnPx']} px**，正文没有关闭重开；返回后固定 ID 仍为 `{metrics['fixedReadingId']}`。
- 鼠标有意移入回收卡面后停止运动，移开继续；首次 down/up/click 可操作同一原生按钮。键盘焦点进入会结束回收，Tab、Enter、Escape 和焦点可见性通过。
- 正常自动导览离场时仍处于 **{metrics['guidePhaseDuringDeparture']}**。环境播放暂停前后，飞离期间世界时间保持 `{metrics['worldTimeWhilePaused'][0]}`，卡片仍能完成运动；该项未使用固定世界时间参数。
- 停在离场状态时，退场、横排、悬停均无待执行帧。窗口、后台、减少动态、字号、指针取消和销毁检查恢复单位飞行姿态与交互。
- 三种阴影姿态的牌面内区像素变化均为 **0**，原有作品、滚轮与布局回归通过。

## 开发检查与修正

最初返回测试发现，读取按钮位置到 pointerdown 之间卡片继续移动，真实事件落在相邻卡面。补充“鼠标主动移入先暂停”的行为后，测试先移入、对准停稳后的同一按钮，再只发一次原生点击；20 项组件和主站对应路径通过。原始 components-1、click-probe 及事件目标记录保留，不计最终通过数。

main-1 的宽屏稳定阅读检查曾因选择器同时匹配 main 当前锚点和 A3 章节而失败。限定到真实阅读流后，main-native-selector 单项复验通过；main-1 中其余 24 项通过与该复验均为同一 build-4，合计 25 项，不重复计算。早期构建与探针不混入最终版本。

后台与指针取消采用明确标记的模拟生命周期事件；其余点击、滚轮、键盘和媒体偏好通过浏览器执行。录像未经加速，固定世界画面只用于方便观察卡片，卡片及导览使用真实时间。

## 保护与交付

本步修改 7 个相关源文件，新增 createCardDeparture.ts 与 cardDeparture.css。资料、22 张图标、其余 **{len(base['sources'])-len(changed)} 个基线源文件**及 **{len(base['protectedHistory'])} 个历史档案**保持，见 [保护核对](evidence/step-11/protection-final.json)。

测试浏览器、专用静态服务与 Xvfb 均已关闭，见 [清理记录](evidence/step-11/services-cleanup.json)。HEAD 与本地 origin/main 仍为 `{head}`，暂存区为空。代码保存在工作区，使用 `npm run dev` 查看。

下一步是第十二步操作说明，尚未开始。
''')
files=[p for p in OUT.rglob('*') if p.is_file() and p.name!='evidence-manifest.json']
save(OUT/'evidence-manifest.json',{'createdAtShanghai':now,'files':[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(files)]})
print(json.dumps({'acceptedChecks':133,'changedRuntime':len(changed),'newRuntime':len(new),'protectedHistoricalFiles':len(base['protectedHistory']),'evidenceFiles':len(files),'servicesClosed':True,'head':head},ensure_ascii=False))
