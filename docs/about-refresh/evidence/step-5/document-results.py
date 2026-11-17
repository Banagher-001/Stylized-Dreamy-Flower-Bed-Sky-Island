"""Record completed step-5 evidence without modifying earlier steps or test reports."""
from collections import Counter
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from zoneinfo import ZoneInfo
import json
import re
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).parent
DOC = OUT.parents[1]
NOW = datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()


def read(path):
    return json.loads(path.read_text())


def record(path):
    data = path.read_bytes()
    return {'path': str(path.relative_to(ROOT)), 'bytes': len(data), 'sha256': sha256(data).hexdigest()}


def current(item):
    path = ROOT / item['path']
    return path.exists() and record(path) == item


def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


baseline = read(OUT / 'baseline.json')
scope = read(OUT / 'scope-addition.json')
allowed = set(baseline['allowedExistingSourceChanges'] + scope['allowedExistingSourceChanges'])
history = baseline['historicalArtifacts']
assert all(current(item) for item in history), 'Historical artifacts changed'
changed = [item['path'] for item in baseline['sourceFilesBefore'] if not current(item)]
assert set(changed) <= allowed, changed
assert git('rev-parse', 'HEAD') == baseline['head']
assert git('branch', '--show-current') == baseline['branch']
assert git('rev-parse', 'origin/main') == baseline['head']
assert set(git('diff', '--name-only').splitlines()) == set(baseline['trackedChangesBefore'])
assert not git('diff', '--cached', '--name-only'), 'Staged changes'
subprocess.run(['git', 'diff', '--check'], cwd=ROOT, check=True)

suites = {}
for name, expected in [('accepted-cards', 61), ('accepted-components', 49), ('main-final', 44), ('projection-final', 8), ('accepted-regressions', 7)]:
    report = read(OUT / name / 'browser.json')
    assert report['complete'] is True
    assert len(report['checks']) == expected
    assert all(check['status'] == '通过' for check in report['checks'])
    closed = report.get('browserClosed', report.get('cleanup', {}).get('browserClosed'))
    assert closed is True
    suites[name] = {'report': f'{name}/browser.json', 'passed': expected, 'failed': 0, 'browserClosed': True}

for name, suite in [('review-build', 'accepted-cards'), ('component-build', 'accepted-components')]:
    build = read(OUT / (name + '.json'))
    assert current(build['output'])
    assert all(current(item) for item in build['sources'])
    assert read(OUT / suite / 'build.json') == build
    assert read(OUT / suite / 'browser.json')['htmlSHA256'] == build['output']['sha256']
for suite in ['main-final', 'accepted-regressions']:
    assert all(current(item) for item in read(OUT / suite / 'source-manifest.json'))
assert read(OUT / 'main-final/source-manifest.json') == read(OUT / 'accepted-regressions/source-manifest.json')
build_check = read(OUT / 'build-check.json')
assert build_check['exitCode'] == 0
assert 'typecheck' in (OUT / build_check['output']).read_text()
cleanup = read(OUT / 'services-cleanup.json')
assert cleanup == {'servicesStopped': 2, 'portClosed': True, 'otherServicesStopped': False}

sources = read(OUT / 'mark-sources.json')['marks']
mark_paths = sorted((ROOT / 'src/assets/tool-marks').glob('*.svg'))
assert len(mark_paths) == len(sources) == 22
for source in sources:
    path = ROOT / source['path']
    assert record(path)['sha256'] == source['localSHA256']
    assert path.stat().st_size == source['bytes']
    tree = ET.fromstring(path.read_bytes())
    for node in tree.iter():
        assert node.tag.rsplit('}', 1)[-1].lower() not in {'script', 'foreignobject', 'animate', 'animatetransform', 'set'}
        for key, value in node.attrib.items():
            local = key.rsplit('}', 1)[-1].lower()
            assert not local.startswith('on')
            if local in {'href', 'src'}:
                assert value.startswith('#'), (path, key, value)
            assert not re.search(r'url\(\s*[\'"]?(?:https?:|//)', value, re.I)
statuses = Counter(source['status'] for source in sources)
assert statuses == {'downloaded': 17, 'purpose-symbol': 5}
mark_kinds = Counter(re.findall(r"^  '[^']+': \{ src: mark\d+, kind: '(brand|family|purpose)'", (ROOT / 'src/tour/about-refresh/toolMarks.ts').read_text(), re.M))
assert mark_kinds == {'brand': 16, 'family': 1, 'purpose': 5}

text = (ROOT / 'src/tour/about-refresh/content.ts').read_text()
content = json.loads(text.split('export const aboutRefreshContent = ', 1)[1].split(' as const satisfies AboutContent;', 1)[0])
cards = content['cards']
ordered = sorted(cards, key=lambda card: card['recommendationOrder'])
entry = sorted([card for card in cards if card['initialEntryRank'] is not None], key=lambda card: card['initialEntryRank'])
assert len(cards) == len({card['id'] for card in cards}) == 22
assert Counter(card['kind'] for card in cards) == {'tool': 21, 'practice': 1}
assert [card['id'] for card in entry] == ['midjourney', 'comfyui', 'kling', 'blender']
assert [card['id'] for card in sorted([card for card in cards if card['category'] == 'G1'], key=lambda card: card['categoryOrder'])] == ['midjourney', 'jimeng', 'comfyui']
assert set(card['id'] for card in cards) == set(source['id'] for source in sources)
assert current(next(item for item in baseline['sourceFilesBefore'] if item['path'].endswith('/content.ts')))

factory = (ROOT / 'src/tour/about-refresh/createToolCard.ts').read_text()
assert not re.search(r'\b(?:requestAnimationFrame|setInterval|setTimeout|WebGLRenderer)\b', factory)
bundles = [ROOT / item['path'] for item in read(OUT / 'main-final/source-manifest.json') if item['path'].startswith('dist/') and item['path'].endswith(('.js', '.css'))]
assert bundles
for path in bundles:
    for forbidden in ['__toolCardReview', '__aboutRefreshPreview', 'tool-card-review-stage']:
        assert forbidden not in path.read_text(), (path, forbidden)

save('resource-check.json', {
    'checkedAtShanghai': NOW, 'status': '通过', 'localVectorCount': 22,
    'totalVectorBytes': sum(path.stat().st_size for path in mark_paths),
    'provenance': dict(statuses), 'markKinds': dict(mark_kinds),
    'selfContainedSVG': True, 'sourceSHA256Matches': True,
    'contentUnchangedFromStep4': True, 'cards': len(cards), 'tools': 21, 'capabilities': 1,
    'categories': dict(Counter(card['category'] for card in cards)),
    'recommendationOrder': [card['id'] for card in ordered],
    'initialEntryIds': [card['id'] for card in entry],
    'newCardFactoryHasOwnClock': False, 'newCardFactoryHasWebGLRenderer': False,
    'developmentReviewGlobalsInMainBundle': False,
    'notes': '16 community-sourced brand marks, 1 CapCut family mark for 剪映, 4 original tool-purpose symbols and 1 Vibe Coding capability symbol; purpose symbols are not official logos.',
})

visuals = {
    'accepted-cards/sample-front.png': '正面平直，标题、用途、标签和按钮清晰；细小石纹不覆盖正文。',
    'accepted-cards/sample-quarter.png': '斜侧面保留真实透视，可见厚度与边缘，非单张平面旋转。',
    'accepted-cards/sample-side.png': '接近侧面时可见窄侧边，前后面之间封闭。',
    'accepted-cards/sample-back.png': '背面独立分类刻纹和 sakan 铭刻，正文没有镜像透出。',
    'accepted-cards/sample-detail.png': '静态展开由真实段落承载，完整内容与收起按钮留在卡内。',
    'main-final/desktop-A3.png': '真实花园工具屏保持原构图与阅读范围，首屏三张完整卡片及第四张预览。',
    'main-final/phone-A3.png': '手机稳定阅读保持清新色彩，单张完整卡片、原生横滑和操作按钮。',
    'projection-final/large-text-detail.png': '200% 大字号采用原宽度向下延展，画面内可见部分文字清晰；整卡边界另由投影数据确认。',
}
save('visual-review.json', {
    'reviewedAtShanghai': NOW, 'method': 'Manually inspected the final screenshots using view_image; projection/DOM assertions supplement visual checks.',
    'screenshots': [{'path': path, 'finding': finding, 'sha256': record(OUT / path)['sha256']} for path, finding in visuals.items()],
    'limits': 'Linux Chromium and emulated viewports; not a claim of physical-device, Safari or Firefox verification.',
})
save('projection-source-context.json', {
    'recordedAtShanghai': NOW, 'report': 'projection-final/browser.json',
    'sourceManifest': 'main-final/source-manifest.json',
    'manifestSHA256': record(OUT / 'main-final/source-manifest.json')['sha256'],
    'context': 'Projection suite used the same step-5 dist service after the final large-text width correction. It did not generate its own source manifest. Current production assets match both main-final and accepted-regressions manifests; final source was not changed between these runs.',
})
save('protection-final.json', {
    'checkedAtShanghai': NOW, 'status': '通过', 'historicalArtifactsChecked': len(history),
    'historicalArtifactsChanged': [], 'existingTourSourceFilesChecked': len(baseline['sourceFilesBefore']),
    'existingSourceFilesChangedFromStep4': changed,
    'allowedExistingSourceChanges': sorted(allowed),
    'additionalLivePreviewChange': 'dev/about-refresh/index.html',
    'head': git('rev-parse', 'HEAD'), 'localOriginMain': git('rev-parse', 'origin/main'),
    'trackedChangesSamePathsAsBefore': True, 'stagedChanges': [], 'gitDiffCheck': '通过',
    'packageDependencyChanges': False, 'existingEmbeddedSiteFilesChanged': False,
    'commitCreated': False, 'pushed': False, 'published': False,
})

appearance = f'''# 关于我改版 · 第五步卡牌外观

状态：第五步完成，{NOW}（Asia/Shanghai）。已接入工作区真实主站，未提交、推送或发布。

[独立卡牌验收页](step-5-card-preview.html) · [主站实际画面](evidence/step-5/main-final/desktop-A3.png) · [验收记录](step-5-verification.md) · [第六步交接](step-5-handoff.md)

## 本步结果

22 张工具与能力卡统一为庭院中的浅色石质卡牌。暖白石面、草木绿文字、水蓝与低饱和分类色沿用主场景；小切角、浅刻纹、稀疏颗粒和柔和阴影提供体积感。正文仍是可选择、可聚焦的真实 HTML。

正面顺序为分类、图案与名称、主要用途、两枚用途标签、展开按钮。展开后显示原定详情正文。背面使用对应分类刻纹与 sakan 铭刻；装饰不重复朗读。独立验收页可切换 22 张卡、正面、斜侧面、近侧面、背面、静态详情、两侧极值及大字号，使用同一套主站卡牌工厂。

## 实体与材质

- 普通阅读面保持 pitch=0、yaw=0，正面 z=0，保证文字清晰；背面 z=-6px。
- 厚度 6px，小切角 6px；正背面和八段周边构成十个实际 CSS 3D 表面，保持 preserve-3d。
- 侧边几何根据真实正面尺寸计算。ResizeObserver 随正文、展开、字体和响应式宽度更新侧边与轮廓，不使用固定高度截断正文。
- 普通桌面卡宽 232—240px，高至少 300px；常规静态展开宽 115%、高至少 345px，内容可继续撑高。窄屏和大字号展开保持原宽度，向下容纳正文。
- 正面为轻微石色渐变与低透明颗粒，刻纹避让正文；侧边受光根据姿态和固定光向变化。阴影位于 3D 实体之外，避免父级 filter 将实体压平。
- 定位、阅读缩放、朝向分别属于 position、reading、orientation 三层；本步不驱动它们连续运动。卡牌是 CSS 3D 实体，光照与阴影是风格化表现，不属于庭院的 Three.js 世界空间投影。

## 22 个本地图案

所有图案随 Vite 本地打包；运行时不请求外部图标服务。22 个 SVG 合计 21,939 字节：16 个社区图标库中的品牌图形、1 个用于剪映的 CapCut 家族图形、4 个工具用途符号及 1 个 Vibe Coding 能力符号。四个用途符号分别表达 3ds Max 的节点多面体、Painter 的绘制、Mixer 的材质叠层及 Marvelous Designer 的布料。它们没有被宣称为官方标识。

已获取图形来自固定版本 LobeHub 1.102.0 / Simple Icons 13.20.0，原路径保持，仅统一庭院墨绿填色。四个无法获取的对应图形使用原创用途符号，完整软件名称仍是身份依据。来源、版本、尝试及本地 SHA256 见 [资源记录](evidence/step-5/mark-sources.json)。

## 主站接入与现有行为

卡牌轨道和“全部工具”均调用 createToolCard；切换分类、模式与销毁时释放各实例的观察器和事件。当前每个 ID 在活动模式只有一张正文与一组控制，不创建隐藏的可访问副本。背面与侧面不进入朗读，转到侧后姿态时正面 inert。

createPillarReader 的导览阅读只计算卡牌正面，排除背面装饰。A1/A2/A3 镜头、阅读容量测量、原生 dialog、全部工具返回状态、键盘、手机横滑、自动导览中断以及已有影像和 Coding 场景均保留并回归验证。

本步只预留同一浏览器内部的 .ar-card-foreground 与姿态变量。没有添加飞入、轨道自动漂移、滚轮加速、惯性、悬停跟随或飞离行为；这些分别继续由第 6—11 步完成。
'''

verification = f'''# 关于我改版 · 第五步验收

采用版本核对时间：{NOW}（Asia/Shanghai）。生产构建含 TypeScript 检查通过，当前工作区卡牌源文件与最终浏览器证据的构建清单一致。

## 最终检查

| 验收项 | 结果 | 依据 |
| --- | --- | --- |
| S5-01 庭院配色与石质层级 | 通过 | 正面、背面和主站最终截图人工核对 |
| S5-02 正文、数量、两套顺序 | 通过 | 21 款工具+1 张能力卡、7 类、首批四张与 G1 分类顺序保持原数据 |
| S5-03 本地图案与来源 | 通过 | 22 个自包含 SVG、SHA 对照、品牌/家族/用途符号区分 |
| S5-04 真实厚度与侧边 | 通过 | 十表面、6px 厚度、八段切角侧边、DOMMatrix 接缝测量 |
| S5-05 背面与侧后阅读控制 | 通过 | 背面无遮挡穿透，装饰隐藏于辅助阅读，侧后正面 inert |
| S5-06 材质与阅读清晰度 | 通过 | 正面平直、颗粒低透明、CSS 3D 链保持、真实 HTML 字号 |
| S5-07 22 张正面/详情及极值 | 通过 | 实体 61 项，包括长名称、斜侧面、背面、窄屏和大字号 |
| S5-08 主站实体及阴影边界 | 通过 | 投影专项 8 项，首末展开及大字号余量通过 |
| S5-09 响应式与全部工具 | 通过 | 组件 49 项，主站 44 项，320—1920px 多视口与 200% 字号 |
| S5-10 原生操作与导览 | 通过 | 原生按键、触摸横滑、返回恢复、真实 A1→A2→A3 导览及 7 项回归 |
| S5-11 空闲与资源 | 通过 | 实体静止像素对照、无自有时钟/Canvas、无新增 WebGLRenderer、开发入口不进入主包 |
| S5-12 构建、历史与收尾 | 通过 | npm run build、git diff --check、1,163 个历史文件 SHA、专属服务关闭 |

## 采用的浏览器证据

| 范围 | 通过 | 最终报告 |
| --- | ---: | --- |
| 同源实体/材质/姿态 | 61/61 | [accepted-cards](evidence/step-5/accepted-cards/browser.json) |
| About 组件与已有控制 | 49/49 | [accepted-components](evidence/step-5/accepted-components/browser.json) |
| 真实主站接入 | 44/44 | [main-final](evidence/step-5/main-final/browser.json) |
| 实际表面及阴影余量 | 8/8 | [projection-final](evidence/step-5/projection-final/browser.json) |
| 站点完整功能回归 | 7/7 | [accepted-regressions](evidence/step-5/accepted-regressions/browser.json) |

7 项回归包括阅读层缩到手机、原生滚轮导航、影像打开返回、罗森 iframe 时间滑杆操作与关闭、瓶中海洋暂停与实际渲染、环境播放暂停恢复，以及未修改时钟的连续自动导览。主站主动模拟 WebGL 不可用时的两条预期报错记录在报告中，降级阅读通过；正常案例没有新增错误。浏览器为 Linux Chromium 155.0.8059.79；手机/平板为浏览器模拟，不代表实机或其他内核验证。

## 可直接检查的交付

- [独立卡牌验收页](step-5-card-preview.html)：同代码、单文件，可切换姿态和全部 22 张卡；不需要额外 WebGL。
- [斜侧面](evidence/step-5/accepted-cards/sample-quarter.png)、[背面](evidence/step-5/accepted-cards/sample-back.png)、[静态详情](evidence/step-5/accepted-cards/sample-detail.png)。
- [主站桌面](evidence/step-5/main-final/desktop-A3.png)、[手机](evidence/step-5/main-final/phone-A3.png)、[大字号修复后](evidence/step-5/projection-final/large-text-detail.png)。
- [资源检查](evidence/step-5/resource-check.json)、[人工视觉核对](evidence/step-5/visual-review.json)、[构建记录](evidence/step-5/build-check.json)、[历史保护](evidence/step-5/protection-final.json)。

独立验收页 SHA256：77828531e9271ce6fb0a7a0d906b916cd00af978b95ec685322108a0148d28a9；组件验收页 SHA256：f1fa9177c4b03fb418bb563454f6d7874f85e89c717e667c5d4a19980240231b。主站仍需 npm run dev 或 HTTP 服务，不把主站声明为双击 HTML 运行。

## 保留的过程记录与修正

早期样本采用轻微默认倾斜，人工核对发现正文重采样与阴影过方，之后改为阅读正面零倾角、正面 z=0，并收柔阴影。首次投影专项 projection-1 为 7/8；200% 字号展开仍沿用 115% 宽度，真实阴影左界超出轨道约 9.2px。已改为大字号保持 100% 宽度、按正文自然长高，projection-final 8/8；最终五组采用检查均在该修复后完成。

specimen-1、smoke-1、cards-final、component-final、accepted-main 和 projection-1 保留为过程记录，不替代最终采用报告。projection-final 没有单独输出源清单，其同一最终构建的对应关系另记于 [投影来源上下文](evidence/step-5/projection-source-context.json)，没有补改原报告。

卡牌没有自有动画循环；测试未进行跨浏览器与物理设备验收，也没有实现下一步飞入与后续自动轨道。已有正文、前三步预览、第四步主站记录和证据未覆盖。仅关闭第五步自有的两个验收服务，未停止其他服务；未上传或发布。
'''

handoff = f'''# 关于我改版 · 第五步交接

状态：第五步完成，{NOW}（Asia/Shanghai）。后续应从本工作区版本继续，先细化第六步，再按用户指令执行；本次未提交、推送或发布。

[外观说明](step-5-appearance.md) · [验收](step-5-verification.md) · [独立姿态检查](step-5-card-preview.html)

## 第六步可直接使用

| 位置 | 已完成的职责 |
| --- | --- |
| src/tour/about-refresh/createToolCard.ts | 同一正文的正背面、侧边几何、尺寸观察、姿态、可读性、销毁与投影范围 |
| src/tour/about-refresh/toolCards.css | 石质材质、6px 厚度/切角、独立 3D 层、阴影、前景容器与大字号规则 |
| src/tour/about-refresh/toolMarks.ts | 22 张本地图案，brand/family/purpose 类型明确 |
| src/tour/about-refresh/createToolBrowser.ts | 卡实例生命周期、分类/位置/详情恢复、原有键盘/触摸/查看全部控制 |
| src/tour/createPillarReader.ts | 主站阅读与容量协调；导览仅读可见卡正面 |
| dev/about-cards/index.html | 开发姿态检查；开发全局与审阅样式没有进入主包 |

createToolCard 返回 element、setPose、setExpanded、measure、dispose。setPose 接收 pitch/yaw 角度与可选 scale/lift，当前约束 pitch±80°、yaw±180°、scale 0.7—1.3。转到侧后角度时正面 inert，正面朝向恢复后可读、可操作。每张卡通过 ResizeObserver 更新八段侧边，销毁时 disconnect 与 abort。

position 层使用 --ar-card-x/y/z；reading 层使用 --ar-card-read-scale 与 --ar-card-lift；orientation 层使用 --ar-card-pitch/yaw。不要让多个阶段同时写入同一个 transform；统一协调姿态与侧面光照，避免只改 CSS 角度后没有更新辅助阅读状态。

## 第六步飞入设计的承接约束

1. 首批只有 Midjourney→ComfyUI→可灵→Blender 四张；全轨道 22 张与分类顺序来自原 content.ts。不能把 22 张同时飞入。
2. 本步 .ar-card-foreground 为空，位于同一 .ar-tools-browser 内，pointer-events:none，子卡可操作。它只是下一步的挂载位置，没有完成移动或动画。
3. 飞入应移动同一张真实卡，不复制可聚焦正文。移动前保留原 slot 占位并锁住实际宽高，在浏览器内部前景层确定定位参考系；原位置不能因移出卡而塌陷。
4. 飞入完成后归还节点及交互状态，取消飞入、反向离开、分类/查看全部/返回/销毁时也应先归还或清理。既有点击委托属于工具浏览器，移动到其外部会丢失委托。
5. 需要统一的时间驱动与可取消状态，不给每张卡各建永久循环。姿态不能把文字和点击保留在不可见背面；减少动态效果与窄屏仍能完整阅读。
6. 当前普通阅读保持零倾角，动态期间的透视/包围范围需按真实表面复测。measure 已包含十个面的投影并为阴影预留左右各10、上4、下18px；它不是所有未来飞行动作的安全证明。
7. 原有主站导览仅读卡片正面；以后必须等待首批卡实际到达且可读后再计阅读时间，离开或中断及时取消。不能只在动画开始时设置“完成”。
8. A3 目前 1440×900 沉浸布局为 1080×652.265625px，依赖原有阅读容量测量。额外运动空间需协调并复测，不能硬挤压 300px 基础卡高。

## 保留的限制与行为

本步是 CSS 3D 石质实体与静态光照，没有第二个 WebGLRenderer，也没有真正世界空间阴影。原生横滑/对齐、前后按钮、点击详情、全部工具、返回焦点、稳定阅读、原生 dialog 与手动操作打断主导览继续有效。未来自动轨道要明确与原生 scroll-snap 的启停关系；滚轮速度与惯性仍属第八步，悬停跟随属第九步，飞离属第十一步。

22 个正文和分类、身份/经历均保持前四步内容，不增加项目、奖项、业绩或相关作品入口。现有 AI 影像、罗森与瓶中海洋照常保留。图案来源见资源记录，不将五个用途符号描述为官方 Logo。

第六步需新建基线及证据，不覆盖本步和以前归档。最终采用检查为实体61、组件49、主站44、投影8、回归7项全部通过。开发可运行 npm run dev，主站 /，实体检查 /dev/about-cards/index.html，独立组件 /dev/about-refresh/index.html。
'''

for name, value in [('step-5-appearance.md', appearance), ('step-5-verification.md', verification), ('step-5-handoff.md', handoff)]:
    (DOC / name).write_text(value)

save('final-summary.json', {
    'completedAtShanghai': NOW, 'status': '第五步完成', 'scope': baseline['scope'],
    'suites': suites, 'totalPassedChecks': sum(item['passed'] for item in suites.values()),
    'build': build_check, 'sourceMatchesFinalEvidence': True,
    'review': read(OUT / 'review-build.json')['output'],
    'component': read(OUT / 'component-build.json')['output'],
    'historicalArtifactsUnchanged': len(history), 'servicesCleanup': cleanup,
    'notImplemented': ['flight-in', 'automatic-track', 'wheel-velocity-inertia', 'pointer-follow-hover', 'flight-out'],
    'committed': False, 'pushed': False, 'published': False,
})

# Check documentation links before sealing the evidence inventory.
for path in [DOC / name for name in ['step-5-appearance.md', 'step-5-verification.md', 'step-5-handoff.md']]:
    for link in re.findall(r'\]\(([^)]+)\)', path.read_text()):
        assert (path.parent / link).exists(), (path, link)
assert all(current(item) for item in history)
files = sorted([path for path in OUT.rglob('*') if path.is_file() and path.name != 'evidence-manifest.json'] + list(DOC.glob('step-5-*')))
save('evidence-manifest.json', {'recordedAtShanghai': NOW, 'files': [record(path) for path in files], 'excludesSelf': True})
print(json.dumps({'status': '通过', 'historicalFilesProtected': len(history), 'sourceChanges': changed, 'finalChecksPassed': 169, 'servicesClosed': True, 'published': False}, ensure_ascii=False))
