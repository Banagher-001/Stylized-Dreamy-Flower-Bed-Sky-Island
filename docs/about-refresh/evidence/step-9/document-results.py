from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json,hashlib,subprocess
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).parent;DOC=OUT.parents[1]
save=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
now=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat();base=json.loads((OUT/'baseline.json').read_text())
changed=[e['path'] for e in base['sources'] if sha(ROOT/e['path'])!=e['sha256']]
expected={'src/tour/about-refresh/createToolCard.ts','src/tour/about-refresh/toolCards.css','src/tour/about-refresh/createCardTrack.ts','src/tour/about-refresh/createToolBrowser.ts','src/tour/about-refresh/host.css'};assert set(changed)==expected,changed
history_bad=[e['path'] for e in base['protectedHistory'] if not (ROOT/e['path']).exists() or sha(ROOT/e['path'])!=e['sha256']];assert not history_bad,history_bad
source_paths=[p for p in (ROOT/'src/tour').rglob('*') if p.is_file()]+list((ROOT/'src/assets/tool-marks').glob('*.svg'));old={e['path'] for e in base['sources']};new=[str(p.relative_to(ROOT)) for p in source_paths if str(p.relative_to(ROOT)) not in old];assert set(new)=={'src/tour/about-refresh/createCardHover.ts','src/tour/about-refresh/cardHover.css'},new
adopted=[]
for name,count in [('verified-components',27),('verified-main',29),('verified-wheel',15),('verified-cycle',2),('verified-regressions',7),('verified-projection',8)]:
 r=OUT/name;d=json.loads((r/'browser.json').read_text());assert d['complete'] and len(d['checks'])==count and all(c['status']=='通过' for c in d['checks']),(name,d)
 assert not d.get('events'),(name,d.get('events'));assert d.get('browserClosed',d.get('cleanup',{}).get('browserClosed'))
 if (r/'build.json').exists():
  b=json.loads((r/'build.json').read_text());records=b['sources'];assert sha(ROOT/b['output']['path'])==b['output']['sha256']
 else:records=json.loads((r/'source-manifest.json').read_text())
 assert all(sha(ROOT/e['path'])==e['sha256'] for e in records),name
 adopted.append({'run':name,'checks':count,'ids':[c['id'] for c in d['checks']],'finalSourcesMatch':True})
assert sum(e['checks'] for e in adopted)==88
save(OUT/'adoption.json',{'total':88,'allPassed':True,'groups':adopted,'developmentRunsRetained':True,'excludedDevelopmentRuns':['components-1','depth-probe','depth-corners','depth-fixed','accepted-components'],'notes':['早期 24 项基础悬停检查和初始深度探针保留作开发记录，不计最终验收。','depth-corners 揭示边缘牌反向倾斜时被邻卡遮挡；修正共同轨道深度补偿后，最终版本四角命中全部通过。','accepted-components 为修复指针阅读转键盘阅读前版本的 26 项通过记录；最终 verified-components 重新验证 27 项，不重复计数。']})
assert subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True).returncode==0
assert subprocess.run(['git','diff','--cached','--quiet'],cwd=ROOT).returncode==0
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();remote=subprocess.check_output(['git','rev-parse','refs/remotes/origin/main'],cwd=ROOT,text=True).strip();assert head==base['head']==remote
cleanup=json.loads((OUT/'services-cleanup.json').read_text());assert cleanup['portClosed'] and cleanup['servicesStopped']==2
services=json.loads((OUT/'services-started.json').read_text());assert all(not Path('/proc',str(p['pid'])).exists() for p in services['services'])
production=[ROOT/'dist/index.html',*(ROOT/'dist/assets').glob('startTourPrototype*')]
save(OUT/'source-freeze.json',{'checkedAtShanghai':now,'buildLog':'build-6.txt','buildPassed':'✓ built in' in (OUT/'build-6.txt').read_text(),'sources':[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in source_paths+production]})
assert json.loads((OUT/'source-freeze.json').read_text())['buildPassed']
protection={'checkedAtShanghai':now,'historicalFilesUnchanged':len(base['protectedHistory']),'historicalMismatches':history_bad,'changedRuntime':changed,'newRuntime':new,'otherBaselineSourcesUnchanged':len(base['sources'])-len(changed),'contentAndMarksUnchanged':True,'head':head,'localOriginMain':remote,'indexUnchanged':True,'pushed':False,'published':False,'servicesClosed':True};save(OUT/'protection-final.json',protection)
hold=json.loads((OUT/'verified-main/hover-holds-and-resumes-choice-data.json').read_text());shadow=json.loads((OUT/'verified-components/shadow-behind-front-pixel-check-data.json').read_text());cycle=json.loads((OUT/'verified-cycle/real-wheel-two-full-directions-data.json').read_text());five=json.loads((OUT/'verified-cycle/real-wheel-five-card-directions-data.json').read_text());video=json.loads((OUT/'video-metadata.json').read_text());tilt=json.loads((OUT/'verified-main/four-corners-and-edges-data.json').read_text())
metrics={'actualMainMagnification':hold['ratio'],'shadowInteriorDifferentPixels':[s['differentPixels'] for s in shadow],'allCardsSeen':len(cycle['seen']),'allCardsRecycles':len(cycle['wraps']),'fiveCardsSeen':len(five['seen']),'fiveCardsRecycles':len(five['wraps']),'mainReadingDepth':hold['hover']['d']['hoverWorldDepth'],'mainTiltSamples':tilt['angles']}
save(OUT/'final-summary.json',{'completedAtShanghai':now,'step':9,'status':'completed','acceptedChecks':88,'metrics':metrics,'clockModified':False,'physicalHardwareTested':False,'video':video['target'],'nextStep':10,'unpublished':True})
save(OUT/'visual-review.json',{'reviewedAtShanghai':now,'reviewed':['main-hover-second.png','video-5.png','video-6.png','verified-main/edge-card-front-occlusion.png','verified-main/phone-stable-reading.png','verified-projection/large-front.png'],'observations':['保持清新花园与暖白石牌，普通宽屏继续沉浸模式；放大牌有厚度与轻微倾斜。','阴影矩形交叠已修复；阴影开关前后牌面内区像素相同。','边缘牌在正反倾角下处于邻卡前方，真实命中保持活动卡。','手机采用稳定阅读，按钮和正文完整。','录像使用真实时间与原生鼠标操作；仅 waterTime=2 固定世界便于观察。'],'accepted':True})
(DOC/'step-9-verification.md').write_text(f'''# 关于我改版 · 第九步验收

完成：{now}（Asia/Shanghai）。第九步完成，未提交、推送或发布。

[实现说明](step-9-reading.md) · [第十步交接](step-9-handoff.md) · [{float(video['deliveryMetadata']['format']['duration']):.2f} 秒实际主站录像](evidence/step-9/step-9-hover.mp4)

## 最终结果

**88 项检查通过**，`npm run build`（含类型检查）与 `git diff --check` 通过。所有最终结果匹配当前源码及构建 SHA256。浏览器 Chromium 155.0.8059.79；鼠标、滚轮、键盘使用原生浏览器输入；后台测试明确标记为模拟。未修改动画时钟，未使用实体设备或其他浏览器验收。

| 范围 | 通过数 | 记录 |
| --- | ---: | --- |
| 组件悬停、空间、深度、按钮、输入、焦点和生命周期 | 27 | verified-components |
| 真实花园主站、导览中断、继续章节、降级与录像 | 29 | verified-main |
| 第八步滚轮速度、方向、页面所有权、移动按钮与场景时钟 | 15 | verified-wheel |
| 22 张和 5 张分类的真实滚轮正反整圈 | 2 | verified-cycle |
| 原有弹窗、影像、罗森、漂流瓶、环境与 A1→A2→A3 导览 | 7 | verified-regressions |
| 宽屏、手机、首末详情与大字的牌面投影 | 8 | verified-projection |

[最终采纳清单](evidence/step-9/adoption.json) 不计早期开发运行。原始 depth-corners 失败探针保留，它查出了边缘牌反向倾斜时被邻卡覆盖的问题；最终四角真实命中网格和安全边界均通过。所有最终运行完整通过，无需混合旧版本结果。

## 关键实测

- 1440×900 主站继续沉浸布局，悬停阅读实际宽度约为原来的 **{hold['ratio']:.3f} 倍**；目标共同轨道深度 **{hold['hover']['d']['hoverWorldDepth']} px**，自动开关保持开启而轨道停帧。
- 鼠标移开后恢复原选择；手动关闭后悬停不会开启它。静止鼠标下自动经过的卡牌不拦截展示，快速掠过只激活最终目标。
- 四角与四边通过真实牌面/厚度/阴影测量；边缘局部卡可完整阅读，活动牌不被邻卡挡住。参考平面固定，没有姿态自我追逐。
- 基础曲轨与左右倾斜的三组静帧中，阴影可见/隐藏后牌面内区变化均为 **0 像素**；旧灰色矩形不再覆盖正文。
- pointerdown 固定姿态；首牌、末牌、局部牌、放大途中按钮均能首次原生点击。鼠标阅读切到同一卡的键盘阅读会收正；Enter、Escape 和焦点正常。
- 第一个滚轮事件即可接管，横向首事件移交一次，原生页面与缩放修饰键规则保留。轮动和惯性期间不抢回悬停。
- 双向整圈见到全部 **{len(cycle['seen'])} 张**，记录 **{len(cycle['wraps'])} 次**离屏换位；五张分类记录 **{len(five['wraps'])} 次**。同一节点实例与 DOM 顺序保持，首尾没有可见跳牌。
- 组件快照、重挂、尺寸、后台、减少动态与销毁清理悬停及候选；静止阅读后姿态 RAF 取消。真正阅读停止主导览，移开不自动开启主导览；世界播放选择独立。

## 保护与交付

仅修改 5 个相关源文件并新增 2 个悬停文件；资料、正文、22 张图标、其他基线源文件和 **{len(base['protectedHistory'])} 个历史档案**保持。详见 [保护核对](evidence/step-9/protection-final.json)。第十步的更多内容正式呈现尚待细化和授权，现有详情入口有效。

录像未经加速；`waterTime=2` 只固定世界时间，卡牌、导览与输入均使用真实时间。所有测试 Chromium、录制进程、本地静态服务与 Xvfb 已关闭，见 [清理记录](evidence/step-9/services-cleanup.json)。

HEAD 和本地 origin/main 仍为 `{head}`，暂存区为空。代码保存在工作区，运行 `npm run dev` 查看。
''')
files=[p for p in OUT.rglob('*') if p.is_file() and p.name!='evidence-manifest.json'];save(OUT/'evidence-manifest.json',{'createdAtShanghai':now,'files':[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(files)]})
print(json.dumps({'acceptedChecks':88,'historicalFilesUnchanged':len(base['protectedHistory']),'changedRuntime':len(changed),'newRuntime':len(new),'evidenceFiles':len(files),'servicesClosed':True,'head':head},ensure_ascii=False))
