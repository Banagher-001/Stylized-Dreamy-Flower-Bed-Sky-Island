from pathlib import Path
import hashlib, json, subprocess

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).parent
report = json.loads((OUT / 'accepted-main/browser.json').read_text())
assert report['complete']
case = next(c for c in report['checks'] if c['id'] == 'actual-detail-demonstration')
assert case['status'] == '通过'
source = OUT / 'accepted-main' / case['video']
target = OUT / 'step-10-details.mp4'
ffmpeg = Path('/usr/bin/ffmpeg')
with (OUT / 'step-10-details.mp4.conversion.txt').open('w') as log:
    subprocess.run([str(ffmpeg), '-y', '-i', str(source), '-c:v', 'libx264', '-crf', '20', '-preset', 'medium', '-threads', '2', '-pix_fmt', 'yuv420p', '-an', '-movflags', '+faststart', str(target)], check=True, stdout=log, stderr=subprocess.STDOUT)
def metadata(path):
    return json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_name,width,height,r_frame_rate:format=duration,size', '-of', 'json', str(path)], text=True))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
data = {'source': str(source.relative_to(ROOT)), 'target': str(target.relative_to(ROOT)), 'sourceSHA256': sha(source), 'targetSHA256': sha(target), 'sourceMetadata': metadata(source), 'deliveryMetadata': metadata(target), 'speedChanged': False, 'clockModified': False}
assert abs(float(data['sourceMetadata']['format']['duration']) - float(data['deliveryMetadata']['format']['duration'])) < .05
(OUT / 'video-metadata.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
for second in [4, 6, 8]:
    subprocess.run([str(ffmpeg), '-y', '-ss', str(second), '-i', str(target), '-frames:v', '1', '-threads', '1', str(OUT / f'video-{second}.png')], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print(json.dumps({'video': str(target.relative_to(ROOT)), 'duration': data['deliveryMetadata']['format']['duration'], 'sha256': data['targetSHA256']}))
