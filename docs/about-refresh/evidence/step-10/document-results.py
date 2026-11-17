from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib, json, subprocess

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).parent
DOC = OUT.parents[1]
now = datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
save = lambda p, d: p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
base = json.loads((OUT / 'baseline.json').read_text())
changed = [e['path'] for e in base['sources'] if sha(ROOT / e['path']) != e['sha256']]
expected = {f'src/tour/about-refresh/{name}.ts' for name in ['createToolCard', 'createCardHover', 'createToolBrowser', 'createCardTrack']}
assert set(changed) == expected, changed
history_bad = [e['path'] for e in base['protectedHistory'] if not (ROOT / e['path']).exists() or sha(ROOT / e['path']) != e['sha256']]
assert not history_bad, history_bad
sources = [p for p in (ROOT / 'src/tour').rglob('*') if p.is_file()] + list((ROOT / 'src/assets/tool-marks').glob('*.svg'))
old = {e['path'] for e in base['sources']}
new = [str(p.relative_to(ROOT)) for p in sources if str(p.relative_to(ROOT)) not in old]
assert set(new) == {'src/tour/about-refresh/cardDetails.css'}, new
adopted = []
for name, count in [('accepted-components', 23), ('accepted-main', 26), ('accepted-shadow', 1), ('accepted-wheel', 15), ('accepted-cycle', 2), ('accepted-regressions', 7), ('accepted-projection', 8)]:
    folder = OUT / name
    report = json.loads((folder / 'browser.json').read_text())
    assert report['complete'] and len(report['checks']) == count and all(c['status'] == '通过' for c in report['checks']), name
    assert not report.get('events'), (name, report.get('events'))
    assert report.get('browserClosed', report.get('cleanup', {}).get('browserClosed')), name
    records = json.loads((folder / 'source-manifest.json').read_text()) if (folder / 'source-manifest.json').exists() else []
    if (folder / 'build.json').exists():
        build = json.loads((folder / 'build.json').read_text())
        assert sha(ROOT / build['output']['path']) == build['output']['sha256'], name
        records += build['sources']
    assert records and all(sha(ROOT / e['path']) == e['sha256'] for e in records), name
    adopted.append({'run': name, 'checks': count, 'ids': [c['id'] for c in report['checks']], 'finalSourcesMatch': True})
assert sum(e['checks'] for e in adopted) == 82
save(OUT / 'adoption.json', {
    'total': 82, 'allPassed': True, 'groups': adopted, 'developmentRunsRetained': True,
    'excludedDevelopmentRuns': ['components-1', 'verified-components', 'verified-main', 'final-components', 'final-main', 'final-shadow', 'final-wheel', 'final-cycle', 'final-regressions', 'final-projection', 'visual-regression-before'],
    'notes': [
        '先行 340/360 px 测量只用于确定布局，不计正式验收。',
        'components-1 的销毁状态已正确清理，但测试读取脱离样式后的 filter:none 发生解析错误；修正测试读取后重新运行。',
        '开发版缩到手机后固定卡未对齐；按固定 ID 对齐并增加实际可见范围断言后修复。',
        'build-4 的 82 项通过记录仍保留，但视觉复核查出原生宽屏的邻卡遮挡；visual-regression-before 用真实命中网格复现失败。',
        '原生宽阅读卡保留堆叠层级后，build-5 的 accepted 系列全部重新验收；全文断言同时检查实际可视区域命中，未混用早期通过记录。'
    ]
})
assert subprocess.run(['git', 'diff', '--check'], cwd=ROOT, capture_output=True).returncode == 0
assert subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=ROOT).returncode == 0
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
remote = subprocess.check_output(['git', 'rev-parse', 'refs/remotes/origin/main'], cwd=ROOT, text=True).strip()
assert head == base['head'] == remote
cleanup = json.loads((OUT / 'services-cleanup.json').read_text())
assert cleanup['portClosed'] and cleanup['servicesStopped'] == 2
services = json.loads((OUT / 'services-started.json').read_text())
assert all(not Path('/proc', str(p['pid'])).exists() for p in services['services'])
production = [ROOT / 'dist/index.html', *(ROOT / 'dist/assets').glob('startTourPrototype*')]
build_passed = '✓ built in' in (OUT / 'build-5.txt').read_text()
assert build_passed
save(OUT / 'source-freeze.json', {'checkedAtShanghai': now, 'buildLog': 'build-5.txt', 'buildPassed': build_passed, 'sources': [{'path': str(p.relative_to(ROOT)), 'bytes': p.stat().st_size, 'sha256': sha(p)} for p in sources + production]})
save(OUT / 'protection-final.json', {
    'checkedAtShanghai': now, 'historicalFilesUnchanged': len(base['protectedHistory']), 'historicalMismatches': history_bad,
    'changedRuntime': changed, 'newRuntime': new, 'otherBaselineSourcesUnchanged': len(base['sources']) - len(changed),
    'contentAndMarksUnchanged': True, 'head': head, 'localOriginMain': remote, 'indexUnchanged': True,
    'pushed': False, 'published': False, 'servicesClosed': True
})
all_cards = json.loads((OUT / 'accepted-main/all-22-full-paragraphs-data.json').read_text())['readings']
cards = [next(c for c in reading['cards'] if c['id'] == reading['d']['readingId']) for reading in all_cards]
assert len(cards) == 22 and all(c['hitGrid'] and set(c['hitGrid']) == {c['id']} for c in cards)
resize = json.loads((OUT / 'accepted-main/resize-keeps-fixed-content-data.json').read_text())
fixed = next(c for c in resize['wide']['cards'] if c['id'] == 'comfyui')
assert set(fixed['hitGrid']) == {'comfyui'}
shadow = json.loads((OUT / 'accepted-shadow/shadow-behind-front-pixel-check-data.json').read_text())
cycle = json.loads((OUT / 'accepted-cycle/real-wheel-two-full-directions-data.json').read_text())
five = json.loads((OUT / 'accepted-cycle/real-wheel-five-card-directions-data.json').read_text())
video = json.loads((OUT / 'video-metadata.json').read_text())
assert sha(ROOT / video['source']) == video['sourceSHA256'] and sha(ROOT / video['target']) == video['targetSHA256']
metrics = {
    'fullParagraphCards': len(cards), 'minimumParagraphFontPx': min(c['detail']['font'] for c in cards),
    'maxNaturalOffsetHeightPx': max(c['height'] for c in cards), 'allFullTextHitGridsPass': True,
    'phonePinnedFullyVisible': resize['phone']['selectedFullyVisible'], 'restoredWidePinnedHitGrid': fixed['hitGrid'],
    'shadowInteriorDifferentPixels': [s['differentPixels'] for s in shadow],
    'allCardsSeen': len(cycle['seen']), 'allCardsRecycles': len(cycle['wraps']),
    'fiveCardsSeen': len(five['seen']), 'fiveCardsRecycles': len(five['wraps'])
}
save(OUT / 'final-summary.json', {'completedAtShanghai': now, 'step': 10, 'status': 'completed', 'acceptedChecks': 82, 'metrics': metrics, 'clockModified': False, 'physicalHardwareTested': False, 'video': video['target'], 'nextStep': 11, 'unpublished': True})
save(OUT / 'visual-review.json', {
    'reviewedAtShanghai': now,
    'reviewed': ['video-6.png', 'video-8.png', 'accepted-main/partial-edge-full-text-and-hit-grid.png', 'accepted-main/phone-one-tap-full-detail.png', 'accepted-main/resize-keeps-fixed-content.png', 'accepted-projection/large-text-detail.png'],
    'developmentImagesAlsoReviewed': ['final-main/resize-keeps-fixed-content.png', 'visual-regression-before/resize-keeps-fixed-content-failure.png'],
    'observations': ['保持清新花园、暖白石牌、草绿文字与实体厚度。', '全文、按钮、标签有序排布，预览固定不重复开合。', '手机点按后全文可读，回到宽屏后固定卡高于邻卡，右侧正文完整。', '大字采用原生自然流，长页面通过上下滚动阅读。', '实际主站录像未经加速；仅 waterTime=2 固定世界画面，卡片与输入使用真实时间。'],
    'accepted': True
})
(DOC / 'step-10-verification.md').write_text(f'''# 关于我改版 · 第十步验收

完成：{now}（Asia/Shanghai）。第十步完成，未提交、推送或发布。

[实现说明](step-10-details.md) · [第十一步交接](step-10-handoff.md) · [{float(video['deliveryMetadata']['format']['duration']):.2f} 秒实际主站录像](evidence/step-10/step-10-details.mp4)

## 最终结果

**82 项最终检查通过**，`npm run build`（包含类型检查）与 `git diff --check` 通过。最终采纳结果全部匹配 build-5 的源码 SHA256；没有混用早期版本结果。Chromium 155.0.8059.79，鼠标、滚轮、键盘使用原生浏览器输入；后台测试明确标记为模拟。未修改动画时钟，未用实体设备或其他浏览器验收。

| 范围 | 通过数 | 记录 |
| --- | ---: | --- |
| 22 张全文、预览/固定/收起、真实命中、快照与销毁 | 23 | accepted-components |
| 真实花园主站、章节、导览中断、手机、大字及录像 | 26 | accepted-main |
| 阴影开关的牌面内区像素检查 | 1 | accepted-shadow |
| 滚轮速度、方向、页面所有权、按钮和场景时钟 | 15 | accepted-wheel |
| 22 张与 5 张分类的真实双向整圈循环 | 2 | accepted-cycle |
| 原有弹窗、影像、罗森、漂流瓶、环境和章节导览 | 7 | accepted-regressions |
| 宽屏、手机、首末详情和大字的实际实体投影 | 8 | accepted-projection |

[最终采纳清单](evidence/step-10/adoption.json) · [源码冻结](evidence/step-10/source-freeze.json)

## 关键实测

- 全部 22 张卡显示现有完整介绍，正文最小 **{metrics['minimumParagraphFontPx']:.0f} px**，没有横向文字溢出；最终正文自然高度最大约 **{metrics['maxNaturalOffsetHeightPx']} px**（offsetHeight 整数测量）。预览时卡排占位与主站模式保持。
- 预览临时暂停自动展示，移开恢复原选择；手动关闭后不会被预览打开。点击固定不先收回再展开；宽度变化途中按下鼠标会冻结到真实 click，首次点击有效。
- 固定后移开仍保留；收起和 Escape 关闭并抑制原位置立刻重开。键盘焦点离开再返回可重新预览，手机点一次直接打开全文。
- 预览滚轮的第一事件直接接管横排，固定阅读的滚轮用于页面。继续自动展示先收牌再移动，上一张/下一张与序号以阅读 ID 为准。
- 全部工具展示 22 份全文；返回、章节往返与重挂保留分类、固定 ID、位置和暂停选择，临时预览不进入快照。
- 手机尺寸下固定卡完整对齐到可视范围；恢复宽屏后 3×3 原生可视区域命中全部为固定卡。大字与减少动态保持自然流全文阅读。
- 三种阴影姿态的牌面内区变化均为 **0 像素**。22 张双向滚轮循环见到全部卡，记录 **{metrics['allCardsRecycles']} 次**离屏换位；五张分类记录 **{metrics['fiveCardsRecycles']} 次**。节点与 DOM 顺序保持。

## 视觉复核发现与修复

build-4 的初版检查通过后，人工复核发现从手机恢复宽屏的静态阅读中，ComfyUI 右侧被可灵卡片遮住。它们拥有独立局部透视，单卡内部的 translateZ 不能决定兄弟卡绘制顺序。

新增真实命中网格后，[修复前复现](evidence/step-10/visual-regression-before/browser.json) 明确查到右侧三点命中 `kling`。在原生轨道中为宽阅读卡保留堆叠层级后，[最终尺寸切换记录](evidence/step-10/accepted-main/resize-keeps-fixed-content-data.json) 九点全部命中 `comfyui`，全文可见；程序轨道继续使用共同三维深度。最终 82 项均在修复后的构建重新运行。

早期开发记录完整保留，不计最终验收；详见采纳清单。视频仅固定世界时间以方便观察，卡片、导览、缓动和输入使用真实时间。

## 保护与交付

本步修改 4 个卡片相关 TypeScript 文件并新增 `cardDetails.css`；资料、正文、22 张图标、其余 **{len(base['sources']) - len(changed)} 个基线源文件**与 **{len(base['protectedHistory'])} 个历史档案**保持，见 [保护核对](evidence/step-10/protection-final.json)。原有影像、罗森、漂流瓶及环境回归通过。

测试浏览器、本地静态服务与 Xvfb 均已关闭，见 [清理记录](evidence/step-10/services-cleanup.json)。HEAD 与本地 origin/main 仍为 `{head}`，暂存区为空。代码保存在工作区，运行 `npm run dev` 查看。

下一步仍是第十一步飞离动画，等待细化与执行指示。
''')
files = [p for p in OUT.rglob('*') if p.is_file() and p.name != 'evidence-manifest.json']
save(OUT / 'evidence-manifest.json', {'createdAtShanghai': now, 'files': [{'path': str(p.relative_to(ROOT)), 'bytes': p.stat().st_size, 'sha256': sha(p)} for p in sorted(files)]})
print(json.dumps({'acceptedChecks': 82, 'historicalFilesUnchanged': len(base['protectedHistory']), 'changedRuntime': len(changed), 'newRuntime': len(new), 'evidenceFiles': len(files), 'servicesClosed': True, 'head': head}, ensure_ascii=False))
