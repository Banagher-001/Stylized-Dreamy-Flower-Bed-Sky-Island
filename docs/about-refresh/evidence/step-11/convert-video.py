from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).parent
report=json.loads((OUT/'main-1/browser.json').read_text())
case=next(c for c in report['checks'] if c['id']=='actual-departure-demonstration');assert case['status']=='通过'
source=OUT/'main-1'/case['video'];target=OUT/'step-11-departure.mp4'
with (OUT/'video-conversion.txt').open('w') as log:
 subprocess.run(['/usr/bin/ffmpeg','-y','-i',str(source),'-c:v','libx264','-crf','20','-preset','medium','-threads','2','-pix_fmt','yuv420p','-an','-movflags','+faststart',str(target)],check=True,stdout=log,stderr=subprocess.STDOUT)
def meta(p):return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=codec_name,width,height,r_frame_rate:format=duration,size','-of','json',str(p)],text=True))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
d={'source':str(source.relative_to(ROOT)),'target':str(target.relative_to(ROOT)),'sourceSHA256':sha(source),'targetSHA256':sha(target),'sourceMetadata':meta(source),'deliveryMetadata':meta(target),'speedChanged':False,'clockModified':False,'sourceCase':{'run':'main-1','id':case['id'],'status':case['status']}}
assert abs(float(d['sourceMetadata']['format']['duration'])-float(d['deliveryMetadata']['format']['duration']))<.05
(OUT/'video-metadata.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
for second in [3.8,4.0,5.3,5.5,6.2,8.0]:
 subprocess.run(['/usr/bin/ffmpeg','-y','-ss',str(second),'-i',str(target),'-frames:v','1','-threads','1',str(OUT/f'video-{second}.png')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
print(json.dumps({'video':d['target'],'duration':d['deliveryMetadata']['format']['duration'],'sha256':d['targetSHA256']}))
