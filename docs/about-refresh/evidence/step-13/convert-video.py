from pathlib import Path
import subprocess,json,hashlib
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).parent
d=json.loads((OUT/'accepted5-adaptation-main/browser.json').read_text());assert d['complete'];c=next(v for v in d['checks'] if v['id']=='hybrid-first-tap');assert c['status']=='通过'
source=OUT/'accepted5-adaptation-main'/c['video'];target=OUT/'step-13-adaptation.mp4'
with (OUT/'video-conversion.txt').open('w') as log:subprocess.run(['/usr/bin/ffmpeg','-y','-i',str(source),'-c:v','libx264','-crf','20','-preset','medium','-threads','2','-pix_fmt','yuv420p','-an','-movflags','+faststart',str(target)],check=True,stdout=log,stderr=subprocess.STDOUT)
def meta(p):return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=codec_name,width,height,r_frame_rate:format=duration,size','-of','json',str(p)],text=True))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();a,b=meta(source),meta(target);assert abs(float(a['format']['duration'])-float(b['format']['duration']))<.05
(OUT/'video-metadata.json').write_text(json.dumps({'source':str(source.relative_to(ROOT)),'target':str(target.relative_to(ROOT)),'sourceSHA256':sha(source),'targetSHA256':sha(target),'sourceMetadata':a,'deliveryMetadata':b,'speedChanged':False,'cardClockModified':False,'worldTimeFixture':2,'description':'真实主站入场、鼠标预览、首次触摸固定阅读与原生布局交接'},ensure_ascii=False,indent=2)+'\n')
for label,ratio in [('before',.55),('after',.92)]:subprocess.run(['/usr/bin/ffmpeg','-y','-ss',str(float(b['format']['duration'])*ratio),'-i',str(target),'-frames:v','1','-threads','1',str(OUT/f'video-{label}.png')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
print(json.dumps({'video':str(target.relative_to(ROOT)),'duration':b['format']['duration']}))
