"""One-way conversion of approved public copy into standalone runtime data."""
from pathlib import Path
import json,re,hashlib
ROOT=Path(__file__).resolve().parents[4]
DOC=ROOT/'docs/about-refresh';OUT=Path(__file__).parent
blocks=lambda s:dict(re.findall(r'<!-- public:([\w:-]+) -->\n(.*?)\n<!-- /public:\1 -->',s,re.S))
rows=lambda s:{a.strip():b.strip() for a,b in re.findall(r'^\| ([^|\n]+) \| ([^|\n]+) \|$',s,re.M)}
copy=blocks((DOC/'step-1-copy.md').read_text());source=(DOC/'step-1-tool-cards.md').read_text();public=blocks(source)
category_rows=re.findall(r'^\| (G[1-7]) \| ([^|]+) \| ([^|]+) \| (\d+) \|$',source,re.M)
raw=[]
marks=['MJ','CF','可','BL','梦','海','GPT','GE','MA','HO','C4D','3D','UE','SP','QM','MD','PS','AE','PR','AI','剪','VI']
for number,key,body in re.findall(r'^### (\d{2}) / ([\w-]+)\n(.*?)(?=^### \d{2} / |^## 字符预算)',source,re.M|re.S):
 meta=rows(body.split('<!-- public:')[0]);p=rows(public['card:'+key]);order=int(meta['推荐顺序'])
 raw.append({'id':key,'name':p['名称'],'use':p['用途'],'detail':p['展开介绍'],'tags':p['标签'].split(' · '),'category':meta['分类'].split(' · ')[0],'kind':'practice' if meta['类型']=='能力' else 'tool','recommendationOrder':order,'categoryOrder':0,'initialEntryRank':order if order<=4 else None,'mark':marks[order-1]})
by_name={c['name']:c for c in raw};categories=[]
for cid,name,ordered,count in category_rows:
 names=[s.strip() for s in ordered.split('→')];assert len(names)==int(count)
 ids=[]
 for index,name_in_order in enumerate(names):
  card=by_name[name_in_order];assert card['category']==cid
  card['categoryOrder']=index+1;ids.append(card['id'])
 categories.append({'id':cid,'name':name.strip(),'cardIds':ids})
a=rows(copy['A1-main']);e=rows(copy['A2-main']);t=rows(copy['A3-main'])
entries=[]
for key in ['现在','此前','工作室实践']:
 parts=e[key].split(' · ',1);entries.append({'label':key,'company':parts[0],**({'role':parts[1]} if len(parts)>1 else {})})
controls={key:text.strip() for key,_,text in re.findall(r'^\| ([\w-]+) \| ([^|]+) \| ([^|]+) \|$',copy['A3-controls'],re.M) if key!='编号'}
data={'identity':{'eyebrow':a['章节提示'],'title':a['主标题'],'role':a['职业定位'],'paragraphs':[a['介绍第一句'],a['介绍第二句']],'keywords':a['关键词'].split(' · '),'alias':copy['A1-details'].strip()},'experience':{'eyebrow':e['小标题'],'title':e['主标题'],'entries':entries,'process':[{'name':key,'detail':text} for key,text in rows(copy['A2-process']).items() if key not in ['环节','---']],'education':copy['A2-education'].replace('**教育背景**','').strip()},'tools':{'eyebrow':t['小标题'],'title':t['主标题'],'introduction':t['介绍']},'categories':categories,'cards':raw,'controls':controls}
assert len(raw)==22 and len(categories)==7 and all(c['categoryOrder'] for c in raw)
assert len(controls)==13 and sum(c['kind']=='practice' for c in raw)==1
payload=json.dumps(data,ensure_ascii=False,indent=2)
target=ROOT/'src/tour/about-refresh/content.ts'
target.write_text("import type { AboutContent, CategoryFilter, ToolCard } from './types';\n\n/** Approved step-1 public copy. Runtime data has no dependency on docs/evidence. */\nexport const aboutRefreshContent = "+payload+" as const satisfies AboutContent;\n\nexport const initialEntryIds: readonly string[] = aboutRefreshContent.cards\n  .filter(card => card.initialEntryRank !== null)\n  .sort((a, b) => a.initialEntryRank! - b.initialEntryRank!)\n  .map(card => card.id);\n\nexport function getTrackCards(category: CategoryFilter): readonly ToolCard[] {\n  if (category === 'all') return [...aboutRefreshContent.cards].sort((a, b) => a.recommendationOrder - b.recommendationOrder);\n  return aboutRefreshContent.cards.filter(card => card.category === category).sort((a, b) => a.categoryOrder - b.categoryOrder);\n}\n\nexport function getCard(id: string): ToolCard | undefined {\n  return aboutRefreshContent.cards.find(card => card.id === id);\n}\n")
(OUT/'content.json').write_text(payload+'\n')
(OUT/'content-source.json').write_text(json.dumps({'sources':['docs/about-refresh/step-1-copy.md','docs/about-refresh/step-1-tool-cards.md'],'runtimeFile':target.relative_to(ROOT).as_posix(),'runtimeSHA256':hashlib.sha256(target.read_bytes()).hexdigest(),'cards':22,'tools':21,'capabilities':1,'categories':7,'categoryCounts':[len(c['cardIds']) for c in categories],'initialEntryIds':[c['id'] for c in raw[:4]]},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'contentCreated':True,'cards':len(raw),'categories':len(categories),'controls':len(controls)},ensure_ascii=False))
