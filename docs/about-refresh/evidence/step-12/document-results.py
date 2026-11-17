from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json,hashlib,subprocess
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).parent;DOC=OUT.parents[1]
now=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat();save=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
base=json.loads((OUT/'baseline.json').read_text());changed=[e['path'] for e in base['sources'] if sha(ROOT/e['path'])!=e['sha256']]
expected={'src/tour/createPillarReader.ts',*[f'src/tour/about-refresh/{n}' for n in ['types.ts','createAboutView.ts','createToolBrowser.ts','createCardDeparture.ts']]};assert set(changed)==expected,changed
history_bad=[e['path'] for e in base['protectedHistory'] if not (ROOT/e['path']).exists() or sha(ROOT/e['path'])!=e['sha256']];assert not history_bad,history_bad
sources=[p for p in (ROOT/'src/tour').rglob('*') if p.is_file()]+list((ROOT/'src/assets/tool-marks').glob('*.svg'));old={e['path'] for e in base['sources']};new=[str(p.relative_to(ROOT)) for p in sources if str(p.relative_to(ROOT)) not in old]
assert set(new)=={f'src/tour/about-refresh/{n}' for n in ['toolGuidance.ts','createToolHelp.ts','toolHelp.css']},new
runs=[('accepted-guidance-components',24),('accepted-guidance-main',32),('accepted-departure-components',23),('accepted-departure-main',28),('accepted-detail-components',23),('accepted-detail-main',26),('accepted-shadow',1),('accepted-wheel',15),('accepted-cycle-final',2),('accepted-existing',7),('accepted-projection',8)];groups=[]
for name,count in runs:
 folder=OUT/name;d=json.loads((folder/'browser.json').read_text());assert d['complete'] and len(d['checks'])==count and all(c['status']=='通过' for c in d['checks']),name;assert not d.get('events'),name;assert d.get('browserClosed',d.get('cleanup',{}).get('browserClosed')),name
 records=json.loads((folder/'source-manifest.json').read_text()) if (folder/'source-manifest.json').exists() else []
 if (folder/'build.json').exists():
  b=json.loads((folder/'build.json').read_text());assert sha(ROOT/b['output']['path'])==b['output']['sha256'],name;records+=b['sources']
  if (folder/'loaded-component.html').exists():assert sha(folder/'loaded-component.html')==b['output']['sha256'],name
 assert records and all(sha(ROOT/e['path'])==e['sha256'] for e in records),name
 groups.append({'run':name,'checks':count,'ids':[c['id'] for c in d['checks']],'finalSourcesMatch':True})
assert sum(g['checks'] for g in groups)==189
save(OUT/'adoption.json',{'total':189,'allPassed':True,'groups':groups,'excludedDevelopmentRuns':['inspection-1','help-components-1','help-main-1','regression-departure-components','regression-departure-main','regression-detail-components','regression-detail-main','regression-shadow','regression-wheel','regression-cycle','regression-existing','regression-projection','accepted-cycle'],'notes':['build-5 的 48 项说明检查与 133 项旧功能回归均通过，但未计入最终数量。','混合设备诊断发现触摸输入在程序轨道已绑定时仍沿用鼠标文案，原始结果保存在 hybrid-copy-before.json、hybrid-copy-before-extra.json 和 versions/build-5。','修正仅涉及 toolGuidance 的触摸文案分支；build-6 中新增模拟混合输入、触摸返回、原生横向交接和返回中打开说明检查。','最终 56 项说明专项与 133 项既有功能回归全部在 build-6 重新执行，未混用旧版记录。','原 accepted-cycle 保留一次掉帧采样误判：旧断言要求换边后的首个采样阴影也完全在外。83 ms 延迟中实际走过 43.14 px，下一帧仅进入 7.05 px 阴影，正面仍在画面外。详见 cycle-sampling-diagnosis.json。','最终 accepted-cycle-final 覆盖所有十面和三倍模糊半径，要求换边前完全裁切，采样后的进入量不超过实际行进距离加 1 px，继续核对实体、间距、速度、双向整圈；运动源码未变。','final-capture 为同一构建的视觉留档，不作为额外计数检查。']})
assert subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True).returncode==0;assert subprocess.run(['git','diff','--cached','--quiet'],cwd=ROOT).returncode==0
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();remote=subprocess.check_output(['git','rev-parse','refs/remotes/origin/main'],cwd=ROOT,text=True).strip();assert head==base['head']==remote
cleanup=json.loads((OUT/'services-cleanup.json').read_text());assert cleanup['portClosed'] and cleanup['servicesStopped']==2
services=json.loads((OUT/'services-started.json').read_text());assert all(not Path('/proc',str(s['pid'])).exists() for s in services['services'])
assert '✓ built in' in (OUT/'build-6.txt').read_text()
production=[ROOT/'dist/index.html',*(ROOT/'dist/assets').glob('startTourPrototype*')];save(OUT/'source-freeze.json',{'checkedAtShanghai':now,'buildLog':'build-6.txt','buildPassed':True,'sources':[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sources+production]})
save(OUT/'protection-final.json',{'checkedAtShanghai':now,'changedRuntime':changed,'newRuntime':new,'otherBaselineSourcesUnchanged':len(base['sources'])-len(changed),'historicalFilesUnchanged':len(base['protectedHistory']),'historicalMismatches':history_bad,'contentAndMarksUnchanged':True,'head':head,'localOriginMain':remote,'indexUnchanged':True,'pushed':False,'published':False,'servicesClosed':True})
get=lambda name:json.loads((OUT/'accepted-guidance-main'/f'{name}-data.json').read_text())
auto=get('automatic-help-holds-and-restores');wheel=get('panel-wheel-stays-in-help');pin=get('fixed-reading-escape-priority');quiet=get('hover-no-caption-or-help-dom-churn');phone=get('phone-touch-inline-help');hybrid=get('hybrid-touch-instructions-follow-last-input');ret=get('hybrid-touch-return-caption');native=get('native-horizontal-handoff-updates-instructions')
video=json.loads((OUT/'video-metadata.json').read_text());assert sha(ROOT/video['source'])==video['sourceSHA256'] and sha(ROOT/video['target'])==video['targetSHA256']
capture=json.loads((OUT/'final-capture.json').read_text());assert capture['browserClosed'] and not capture['errors'];assert all(sha(ROOT/e['path'])==e['sha256'] for e in capture['sources'])
metrics={'closedRootHeightPx':auto['before']['root']['height'],'openRootHeightPx':auto['open']['root']['height'],'closedControlsHeightPx':auto['before']['controls']['height'],'openControlsHeightPx':auto['open']['controls']['height'],'closedRailHeightPx':auto['before']['rail']['height'],'openRailHeightPx':auto['open']['rail']['height'],'popupWidthPx':auto['open']['help']['rect']['width'],'popupInnerScrollPx':wheel['afterWheel']['help']['scrollTop'],'pageScrollBeforeAfterHelpWheel':[wheel['beforeWheel']['y'],wheel['afterWheel']['y']],'automaticChoiceAcrossHelp':[auto[x]['d']['trackEnabled'] for x in ['before','open','closed','resumed']],'firstEscapeKeepsFixedReading':pin['firstEscape']['d']['detailMode']=='pinned','secondEscapeClosesFixedReading':pin['secondEscape']['d']['detailMode']=='summary','hoverTextMutations':len(quiet['mutationCheck']['mutations']),'phoneInlineWidthPx':phone['scrolledToHelp']['help']['rect']['width'],'phoneHelpFontPx':phone['scrolledToHelp']['help']['font'],'phoneCloseButtonHeightPx':phone['scrolledToHelp']['help']['close']['height'],'hybridTouchBrowse':hybrid['touchInstructions']['help']['rows'][0],'hybridTouchReturnCaption':ret['returning']['hint']['text'],'nativeHandoffMode':native['native']['d']['trackMode']}
assert metrics['closedRootHeightPx']==metrics['openRootHeightPx'] and metrics['closedControlsHeightPx']==metrics['openControlsHeightPx'];assert metrics['hoverTextMutations']==0
save(OUT/'final-summary.json',{'completedAtShanghai':now,'step':12,'status':'completed','acceptedChecks':189,'metrics':metrics,'clockModified':False,'physicalHardwareTested':False,'video':video['target'],'nextStep':13,'unpublished':True})
save(OUT/'visual-review.json',{'reviewedAtShanghai':now,'reviewed':['final-desktop-default.png','final-desktop-help.png','final-desktop-help-scrolled.png','final-desktop-fixed-help.png','accepted-guidance-main/native-390-open.png','accepted-guidance-main/native-320-open.png','accepted-guidance-main/native-large-open.png','accepted-guidance-main/panel-wheel-stays-in-help.png'],'observations':['默认控制栏保持单行，说明入口与状态提示清楚，庭院和原石牌布局保持。','浅米白说明面板在卡排空间内，长内容有滚动提示，标题与关闭入口在滚动后保持可见。','固定阅读内容保留；手机与大字为内联自然流，关闭入口可达。','触摸说明没有滚轮或移入暂停要求；按实际输入区别说明。','录像使用真实主站与原速输入，waterTime=2 仅用于固定世界画面；既有环境独立性另行回归。'],'accepted':True})
(DOC/'step-12-verification.md').write_text(f'''# 关于我改版 · 第十二步验收

完成：{now}（Asia/Shanghai）。第十二步完成，未提交、推送或发布。

[实现说明](step-12-guidance.md) · [第十三步交接](step-12-handoff.md) · [{float(video['deliveryMetadata']['format']['duration']):.2f} 秒主站录像](evidence/step-12/step-12-guidance.mp4)

## 最终结果

**189 项最终检查通过**，`npm run build`（包含类型检查）与 `git diff --check` 通过。所有采纳结果匹配最终 build-6 的源码、构建与组件载荷 SHA256，未混用早期版本。

| 范围 | 通过数 | 记录 |
| --- | ---: | --- |
| 说明组件：状态、暂停组合、焦点、首次操作、输入与生命周期 | 24 | accepted-guidance-components |
| 真实主站：上述场景、入场/导览/章节、手机、大字与录像 | 32 | accepted-guidance-main |
| 第十一步飞离、折返、固定与返回操作回归 | 51 | accepted-departure-components / main |
| 第十步全文详情、键盘与恢复回归 | 49 | accepted-detail-components / main |
| 滚轮速度、方向、首事件、按钮和时钟 | 15 | accepted-wheel |
| 22 张及五张分类的双向整圈 | 2 | accepted-cycle-final |
| 阴影牌面内区像素检查 | 1 | accepted-shadow |
| 原有影像、罗森、漂流瓶、环境与章节导览 | 7 | accepted-existing |
| 宽屏、手机、首末详情和大字投影 | 8 | accepted-projection |

[逐项采纳清单](evidence/step-12/adoption.json) · [源码冻结](evidence/step-12/source-freeze.json)

## 布局与操作实测

- 1440×900 主站保持沉浸模式。打开说明前后，工具浏览器高度均为 **{metrics['closedRootHeightPx']} px**、控制栏高度均为 **{metrics['closedControlsHeightPx']} px**、轨道高度均为 **{metrics['closedRailHeightPx']} px**；没有挤动卡排。
- 面板宽 **{metrics['popupWidthPx']} px**，内部滚动到 **{metrics['popupInnerScrollPx']} px** 时页面位置保持 **{metrics['pageScrollBeforeAfterHelpWheel'][0]} px**，卡排相位也不变。PageDown 只滚动说明，标题和关闭入口保持可见。
- 自动选择在打开、关闭说明前后均保持 true，临时停帧后恢复；原先暂停则保持暂停。临时预览收起后仍由说明持有暂停，关闭只释放自己的持有。
- 首次外部分类、自动按钮、卡片按钮和返回途中说明入口点击有效。固定阅读打开说明后保留全文，第一次 Escape 只关闭说明，第二次可收起固定内容。
- 悬停四角倾斜时，控制文字和说明列表的文本/子节点变更为 **0 次**，节点身份保持。提示与 aria-describedby 指向同一实际可见文案，自动计数不连续播报。
- 390 px 触摸仿真中内联说明宽 **{metrics['phoneInlineWidthPx']} px**，正文 **{metrics['phoneHelpFontPx']} px**，关闭按钮高 **{metrics['phoneCloseButtonHeightPx']} px**。320 px、200% 大字、稳定宽屏及 1920 宽屏也通过，没有页面横向溢出。
- 触控板横向交接后说明改为原生横向浏览，重新开启程序展示后恢复滚轮说明。模拟混合设备触摸时，浏览条目为“{metrics['hybridTouchBrowse']}”，返回提示为“{metrics['hybridTouchReturnCaption']}”。

## 视觉留档

[默认桌面](evidence/step-12/final-desktop-default.png) · [桌面说明](evidence/step-12/final-desktop-help.png) · [说明内部滚动](evidence/step-12/final-desktop-help-scrolled.png) · [固定阅读与说明](evidence/step-12/final-desktop-fixed-help.png)

[390 px 触摸](evidence/step-12/accepted-guidance-main/native-390-open.png) · [320 px 触摸](evidence/step-12/accepted-guidance-main/native-320-open.png) · [200% 大字](evidence/step-12/accepted-guidance-main/native-large-open.png)

## 开发诊断与验证边界

初版 48 项说明与 133 项回归均通过。补查发现，混合设备在程序横排已绑定时，最近触摸输入仍可能沿用滚轮、移入或移开文案。修正仅在 toolGuidance 的触摸分支，诊断前后记录与 build-5 原文件均保留；最终 build-6 增加相应检查并重新执行全部 189 项。

循环检查保留了一次旧断言的掉帧误判及定位数据：83 ms 的延迟内卡片实际前进 43.14 px，下一次采样已有 7.05 px 阴影自然进入，正面仍在画面外。最终检查改按实际位移限定入画量，并扩大到十面与三倍模糊半径；运动源码未修改。见 [采样定位](evidence/step-12/cycle-sampling-diagnosis.json)。

浏览器 Chromium 155.0.8059.79。点击、滚轮、键盘与触摸仿真通过浏览器输入执行，页面定位使用真实 scrollTo 路径；组件通过实际宿主接口提供上下文。混合设备指针及后台等生命周期模拟明确标记，未作为实体手机或辅助软件实测。未修改动画时钟，未做其他浏览器验收。

截图追加录制仅用于视觉留档，不重复计入检查数量。录像未经加速，固定世界画面方便观察卡片与说明；旧功能中的世界时间、鸟、水球和作品交互另用既有回归核对。

## 保护与交付

本步修改 5 个相关源文件，新增 toolGuidance.ts、createToolHelp.ts、toolHelp.css。content.ts、22 张图标、其余 **{len(base['sources'])-len(changed)} 个基线源文件**与 **{len(base['protectedHistory'])} 个历史档案**保持，见 [保护核对](evidence/step-12/protection-final.json)。没有重写三维运动、场景、相机或嵌入作品。

测试浏览器、专用静态服务与 Xvfb 已关闭，见 [清理记录](evidence/step-12/services-cleanup.json)。HEAD 和本地 origin/main 仍为 `{head}`，暂存区为空。代码保存在工作区，运行 `npm run dev` 查看。

第十三步系统适配与第十四步整体验收仍待后续指示。
''')
files=[p for p in OUT.rglob('*') if p.is_file() and p.name!='evidence-manifest.json'];save(OUT/'evidence-manifest.json',{'createdAtShanghai':now,'files':[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(files)]})
print(json.dumps({'acceptedChecks':189,'changedRuntime':len(changed),'newRuntime':len(new),'protectedHistoricalFiles':len(base['protectedHistory']),'evidenceFiles':len(files),'servicesClosed':True,'head':head},ensure_ascii=False))
