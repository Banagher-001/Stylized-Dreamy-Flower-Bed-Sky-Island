"""Build an isolated, self-contained layout board from the unchanged step-1 text."""
from pathlib import Path
import base64, hashlib, json, re

ROOT = Path(__file__).resolve().parents[4]
DOC = ROOT / 'docs/about-refresh'
OUT = Path(__file__).parent

def blocks(text):
    return dict(re.findall(r'<!-- public:([\w:-]+) -->\n(.*?)\n<!-- /public:\1 -->', text, re.S))

def rows(text):
    return {a.strip(): b.strip() for a, b in re.findall(r'^\| ([^|\n]+) \| ([^|\n]+) \|$', text, re.M)}

copy = blocks((DOC / 'step-1-copy.md').read_text())
source = (DOC / 'step-1-tool-cards.md').read_text()
public = blocks(source)
cards = []
groups = {}
for _, key, body in re.findall(r'^### (\d{2}) / ([\w-]+)\n(.*?)(?=^### \d{2} / |^## 字符预算)', source, re.M | re.S):
    meta = rows(body.split('<!-- public:')[0])
    text = rows(public['card:' + key])
    group, group_name = meta['分类'].split(' · ')
    groups[group] = group_name
    cards.append({'id': key, 'name': text['名称'], 'shortName': meta['紧凑显示名'],
                  'use': text['用途'], 'detail': text['展开介绍'], 'tags': text['标签'].split(' · '),
                  'group': group, 'kind': meta['类型'], 'order': int(meta['推荐顺序'])})
assert len(cards) == 22 and [c['id'] for c in cards[:4]] == ['midjourney', 'comfyui', 'kling', 'blender']
identity = rows(copy['A1-main'])
experience = rows(copy['A2-main'])
data = {'identity': identity, 'alias': copy['A1-details'].strip(),
        'experienceTitle': experience['主标题'],
        'experiences': [{'label': key, 'text': experience[key]} for key in ['现在', '此前', '工作室实践']],
        'process': [{'name': key, 'text': text} for key, text in rows(copy['A2-process']).items() if key not in ['环节', '---']],
        'education': copy['A2-education'].replace('**教育背景**', '').strip(),
        'tools': rows(copy['A3-main']), 'groups': [{'id': key, 'name': groups[key]} for key in sorted(groups)],
        'cards': cards}
image = ROOT / 'src/assets/courtyard-orb-cover.webp'
background = 'data:image/webp;base64,' + base64.b64encode(image.read_bytes()).decode()
template = (OUT / 'preview-template.html').read_text()
html = template.replace('__CONTENT_JSON__', json.dumps(data, ensure_ascii=False).replace('<', '\\u003c')).replace('__BACKGROUND__', background)
assert '__CONTENT_JSON__' not in html and '__BACKGROUND__' not in html
(DOC / 'step-2-layout-preview.html').write_text(html)
(OUT / 'content.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
(OUT / 'build.json').write_text(json.dumps({'input': 'step-1-copy.md + step-1-tool-cards.md',
    'cards': len(cards), 'initialCards': [c['id'] for c in cards[:4]],
    'background': {'path': 'src/assets/courtyard-orb-cover.webp', 'sha256': hashlib.sha256(image.read_bytes()).hexdigest()},
    'output': {'path': 'docs/about-refresh/step-2-layout-preview.html', 'bytes': len(html.encode()), 'sha256': hashlib.sha256(html.encode()).hexdigest()},
    'productionImports': False, 'externalRuntimeRequestsRequired': False}, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'built': True, 'cards': len(cards), 'bytes': len(html.encode())}, ensure_ascii=False))
