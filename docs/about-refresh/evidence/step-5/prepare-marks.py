"""Download version-pinned public SVG marks; preserve geometry and source records."""
from pathlib import Path
import urllib.request,concurrent.futures,json,hashlib,re
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).parent;DEST=ROOT/'src/assets/tool-marks';DEST.mkdir(parents=True,exist_ok=True)
lobe='https://unpkg.com/@lobehub/icons-static-svg@1.102.0/icons/'
simple='https://raw.githubusercontent.com/simple-icons/simple-icons/13.20.0/icons/'
items={
'midjourney':[lobe+'midjourney.svg'],'comfyui':[lobe+'comfyui.svg'],'kling':[lobe+'kling.svg'],
'blender':[simple+'blender.svg'],'jimeng':[lobe+'jimeng.svg',lobe+'dreamina.svg'],'hailuo':[lobe+'hailuo.svg'],
'chatgpt':[lobe+'openai.svg'],'gemini':[lobe+'gemini.svg'],'maya':[simple+'autodeskmaya.svg'],
'houdini':[simple+'houdini.svg'],'cinema-4d':[simple+'cinema4d.svg'],'3ds-max':[simple+'autodesk3dsmax.svg'],
'unreal-engine':[simple+'unrealengine.svg'],'substance-painter':[simple+'adobesubstance3dpainter.svg'],
'quixel-mixer':[simple+'quixel.svg'],'marvelous-designer':[simple+'marvelousdesigner.svg'],
'photoshop':[simple+'adobephotoshop.svg'],'after-effects':[simple+'adobeaftereffects.svg'],
'premiere-pro':[simple+'adobepremierepro.svg'],'illustrator':[simple+'adobeillustrator.svg'],'jianying':[simple+'capcut.svg'],
}
def fetch(item):
 key,urls=item;attempts=[]
 for url in urls:
  try:
   with urllib.request.urlopen(url,timeout=25) as response:raw=response.read()
   text=raw.decode();assert '<svg' in text and '</svg>' in text
   assert not re.search(r'<(?:script|foreignObject)|(?:href|src)=[\"\'](?:https?:|//)|onload=',text,re.I)
   # Color only: external SVG currentColor otherwise defaults to black.
   local=text.replace('currentColor','#315746')
   if 'fill=' not in local.split('>',1)[0]:local=local.replace('<svg ','<svg fill="#315746" ',1)
   target=DEST/(key+'.svg');target.write_text(local)
   return {'id':key,'status':'downloaded','source':url,'sourceSHA256':hashlib.sha256(raw).hexdigest(),'localSHA256':hashlib.sha256(local.encode()).hexdigest(),'bytes':len(local.encode()),'path':target.relative_to(ROOT).as_posix(),'modification':'currentColor/root fill set to garden ink; paths unchanged','attempts':attempts}
  except Exception as e:attempts.append({'url':url,'error':str(e)[:220]})
 return {'id':key,'status':'needs-purpose-symbol','attempts':attempts}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:records=list(ex.map(fetch,items.items()))
(OUT/'mark-sources.json').write_text(json.dumps({'providers':{'LobeHub':'@lobehub/icons-static-svg 1.102.0, community-maintained brand vectors','SimpleIcons':'13.20.0, community-maintained brand vectors'},'marks':records},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'downloaded':sum(r['status']=='downloaded' for r in records),'missing':[r['id'] for r in records if r['status']!='downloaded'],'bytes':sum(r.get('bytes',0) for r in records)},ensure_ascii=False))
