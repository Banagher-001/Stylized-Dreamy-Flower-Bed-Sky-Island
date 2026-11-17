from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json,hashlib,subprocess,os
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).parent;DOC=OUT.parents[1]
save=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
now=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat();base=json.loads((OUT/'baseline.json').read_text())
changed=[e['path'] for e in base['sources'] if not (ROOT/e['path']).exists() or sha(ROOT/e['path'])!=e['sha256']]
expected={'src/tour/about-refresh/types.ts','src/tour/about-refresh/createCardTrack.ts','src/tour/about-refresh/createToolBrowser.ts'}
assert set(changed)==expected,changed
history_bad=[e['path'] for e in base['protectedHistory'] if not (ROOT/e['path']).exists() or sha(ROOT/e['path'])!=e['sha256']];assert not history_bad,history_bad
source_paths=[p for p in (ROOT/'src/tour').rglob('*') if p.is_file()]+list((ROOT/'src/assets/tool-marks').glob('*.svg'))
old={e['path'] for e in base['sources']};new=[str(p.relative_to(ROOT)) for p in source_paths if str(p.relative_to(ROOT)) not in old];assert new==['src/tour/about-refresh/cardWheelInput.ts'],new
adopted=[]
for name,exclude,kind in [
 ('accepted-components',['real-wheel-five-card-directions'],'component'),('accepted-five',[],'component'),
 ('accepted-main',['pointer-outside-page-return','wide-stable-manual-opt-in'],'main'),('accepted-main-followup',[],'main'),
 ('accepted-regressions',[],'main'),('accepted-projection',[],'main')]:
 r=OUT/name;d=json.loads((r/'browser.json').read_text());cases=[c for c in d['checks'] if c['id'] not in exclude]
 assert all(c['status']=='通过' for c in cases),(name,cases)
 assert not d.get('events'),(name,d['events']);assert d.get('browserClosed',d.get('cleanup',{}).get('browserClosed'));assert d.get('complete') or exclude
 if kind=='component':
  manifest=json.loads((r/'build.json').read_text())
  records=manifest['sources'];assert sha(ROOT/manifest['output']['path'])==manifest['output']['sha256']
 else:records=json.loads((r/'source-manifest.json').read_text())
 assert all(sha(ROOT/e['path'])==e['sha256'] for e in records),name
 adopted.append({'run':name,'checks':len(cases),'ids':[c['id'] for c in cases],'excludedEarlierAssertions':exclude,'finalSourcesMatch':True})
assert sum(e['checks'] for e in adopted)==56
save(OUT/'adoption.json',{'adopted':adopted,'total':56,'allPassed':True,'originalFailedAttemptsPreserved':True,'notes':[
 'accepted-components 的五张分类测试沿用了 22 张测试的大于 2000 px 换位阈值，未识别 1280 px 周期；accepted-five 用实际周期的一半识别后通过，产品源码未变。',
 'accepted-main 最初把移出横排等同于关闭自动展示，并假设 1366 px 必然稳定阅读；补验按既定规则区分移出横排/离开 A3，并主动切换稳定模式。其他通过用例不重复计数。',
 '早期组件、快照、缩小动态及离屏预算的修正已纳入最终源码，初期失败日志保留但不计验收。',
 '组件初始测试误将 Playwright 默认 null 参数当作默认 true；取消后阻塞的测试只终止已验证的本次测试后代，见 cancelled-test-cleanup.json。']})
assert subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True).returncode==0
assert subprocess.run(['git','diff','--cached','--quiet'],cwd=ROOT).returncode==0
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();remote=subprocess.check_output(['git','rev-parse','refs/remotes/origin/main'],cwd=ROOT,text=True).strip();assert head==base['head']==remote
cleanup=json.loads((OUT/'services-cleanup.json').read_text());assert cleanup['portClosed'] and cleanup['servicesStopped']==2
started=json.loads((OUT/'services-started.json').read_text());assert all(not Path('/proc',str(p['pid'])).exists() for p in started['services'])
protection={'checkedAtShanghai':now,'historicalFilesUnchanged':len(base['protectedHistory']),'historicalMismatches':history_bad,'changedRuntime':changed,'newRuntime':new,'otherBaselineSourcesUnchanged':len(base['sources'])-len(changed),'contentAndMarksUnchanged':True,'head':head,'localOriginMain':remote,'indexUnchanged':True,'pushed':False,'published':False,'servicesClosed':True}
save(OUT/'protection-final.json',protection)
production=[ROOT/'dist/index.html',*(ROOT/'dist/assets').glob('startTourPrototype*')]
save(OUT/'source-freeze.json',{'checkedAtShanghai':now,'buildLog':'build-3.txt','buildPassed':'✓ built in' in (OUT/'build-3.txt').read_text(),'sources':[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in source_paths+production]})
assert json.loads((OUT/'source-freeze.json').read_text())['buildPassed']
gentle=json.loads((OUT/'accepted-components/gentle-notch-manual-tail-data.json').read_text());intensity=json.loads((OUT/'accepted-components/slow-fast-intensity-data.json').read_text());main=json.loads((OUT/'accepted-main/real-wheel-speed-direction-tail-data.json').read_text());cycle=json.loads((OUT/'accepted-components/real-wheel-two-full-directions-data.json').read_text());five=json.loads((OUT/'accepted-five/real-wheel-five-card-directions-data.json').read_text());video=json.loads((OUT/'video-metadata.json').read_text())
metrics={'gentleNotchTravelCSSPixels':gentle['travel'],'gentlePeak':gentle['peak'],'slowPeak':intensity['slowPeak'],'fastPeak':intensity['fastPeak'],'baseForwardMeasuredFromDOM':main['measuredBaseForward']['speed'],'baseReverseMeasuredFromDOM':main['measuredBaseReverse']['speed'],'allCardsSeen':len(cycle['seen']),'allCardsOffscreenRecycles':len(cycle['wraps']),'fiveCardsSeen':len(five['seen']),'fiveCardsOffscreenRecycles':len(five['wraps'])}
save(OUT/'final-summary.json',{'completedAtShanghai':now,'step':8,'status':'completed','acceptedChecks':56,'groups':{'component':20,'main':21,'regressions':7,'projection':8},'metrics':metrics,'clockModified':False,'physicalHardwareTested':False,'video':video['target'],'nextStep':9,'unpublished':True})
save(OUT/'visual-review.json',{'reviewedAtShanghai':now,'reviewed':['accepted-main/real-wheel-speed-direction-tail.png','video-5.png','video-8.png','accepted-main/phone-native-page.png','accepted-projection/large-front.png'],'observations':['自然花园、浅色石牌与清晰 HTML 文案保持；新增提示在宽屏一行显示。','手机使用原生横向浏览和触摸提示，页面滚动不中断。','录像体现不同位置、方向及自动开关状态；未加速录像或修改卡牌时钟。','边缘小角度下仍可见既有阴影层与前牌面的局部交叠；本步未改材质 CSS，后续悬停姿态合成时应复查并修正该分层。'],'step8InputAndLayoutAccepted':True})
(DOC/'step-8-verification.md').write_text(f'''# 关于我改版 · 第八步验收

完成时间：{now}（Asia/Shanghai）。本步已在工作区完成，未提交、推送或发布。

[实现说明](step-8-wheel.md) · [第九步交接](step-8-handoff.md) · [14.24 秒实际主站录像](evidence/step-8/step-8-wheel.mp4)

## 结果

按最终源码采纳 **56 项通过检查**，构建、类型检查及 `git diff --check` 通过。浏览器为 Chromium 155.0.8059.79，包含真实鼠标滚轮与键盘事件；line/page 单位用可取消的合成 WheelEvent 验证，后台切换有明确标记的模拟测试。未修改卡牌时钟，未使用实体鼠标或实体触控板验收。录像仅用 `waterTime=2` 固定世界以便观察，卡牌和导览继续使用真实时间。

| 范围 | 采纳数 | 证据 |
| --- | ---: | --- |
| 组件输入、速度、方向、缓冲、生命周期与循环 | 20 | accepted-components 采纳 19 项；accepted-five 补验 1 项 |
| 实际主站、滚轮区域、布局、详情点击、导览与场景时钟 | 21 | accepted-main 采纳 19 项；accepted-main-followup 补验 2 项 |
| 原生运镜、弹窗缩放、影像、罗森、漂流瓶、环境、A1→A2→A3 导览 | 7 | accepted-regressions |
| 1440/1920 宽屏、390/320 手机、首末详情及大字投影边界 | 8 | accepted-projection |

[采纳清单](evidence/step-8/adoption.json) 保留原始失败尝试及排除原因，不把所有运行次数写成全部通过。组件补验修正的是五张分类的测试周期阈值；主站补验修正的是移出横排与离开 A3 的不同规则，以及主动进入稳定阅读的前提，均未再次修改产品代码。最终所有采纳结果与当前源码、构建产物的 SHA256 一致。

## 实测

- 普通 120 像素单次滚轮在暂停状态下前进约 **{gentle['travel']:.2f} CSS px**，约四分之一张卡；随后减速并取消轨道帧。
- 轻缓输入峰值约 **{intensity['slowPeak']:.2f} px/s**，快速输入峰值约 **{intensity['fastPeak']:.2f} px/s**；极端输入也未超过 560 上限。
- 使用同一 animation frame 中的实际 DOM 位移与时间差，测得基础展示正向 **{main['measuredBaseForward']['speed']:.2f} px/s**、反向 **{main['measuredBaseReverse']['speed']:.2f} px/s**。
- 真实滚轮加速完成正反两圈，见到全部 22 张卡，记录 **{len(cycle['wraps'])} 次**完整离屏换位；五张分类另记录 **{len(five['wraps'])} 次**。原节点实例和 DOM 顺序始终相同，首次反向未在可见区弹出尾牌。
- 暂停立即清空速度；自动关闭时滚轮仍能手动推动，尾段归零；自动开启时按最近方向回到基础速度。离开 A3、后台、重挂、尺寸和减少动态设置均不恢复旧惯性。
- 标题、分类、按钮与继续区滚动页面；卡牌横排捕获合格纵向输入；横向首事件转移一次后由浏览器接手；缩放修饰键保留原生。首次点击首牌、末牌和局部卡的按钮均成功，键盘焦点保持。

## 保留与收尾

本步仅修改 3 个轨道相关文件并新增 1 个无时钟输入模块。内容、22 张卡的本地图标、其他基线源文件及 **{len(base['protectedHistory'])} 个历史档案**未改，详见 [保护核对](evidence/step-8/protection-final.json)。场景、相机路线与两项 Coding 网页资源未另改。

保留既有石材样式与浅弧，未提前实现悬停放大、指针倾斜或飞离。视觉检查观察到边缘角度下既有阴影层与牌面的局部交叠，已在第九步交接中标注需结合悬停分层修正；它不影响本步的滚轮所有权、文字内容与原生操作。

本步的 Chromium、录制进程、静态服务和 Xvfb 已关闭；[服务清理](evidence/step-8/services-cleanup.json)。开发入口仍为 `npm run dev`。HEAD 与本地 origin/main 保持 `{head}`，Git 暂存区为空。
''')
# Inventory is deliberately last; it does not include itself.
files=[p for p in OUT.rglob('*') if p.is_file() and p.name!='evidence-manifest.json']
save(OUT/'evidence-manifest.json',{'createdAtShanghai':now,'files':[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(files)]})
print(json.dumps({'acceptedChecks':56,'historicalFilesUnchanged':len(base['protectedHistory']),'changedRuntime':len(changed),'newRuntime':len(new),'evidenceFiles':len(files),'servicesClosed':True,'head':head},ensure_ascii=False))
