"""Read each final HTTP-served file and compare its actual bytes, on both bases."""
from pathlib import Path
import hashlib,json,urllib.request,urllib.error
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/evidence/lawson-fullpage-step-7'
target=OUT/'http-integrity.json';assert not target.exists()
read=lambda p:json.loads(p.read_text());sha=lambda b:hashlib.sha256(b).hexdigest()
rows=[]
for prefix in ['/','/Stylized-Dreamy-Flower-Bed-Sky-Island/']:
    for f in read(OUT/'build-result.json')['builtFiles']:
        relative=Path(f['path']).relative_to('dist').as_posix();url='http://127.0.0.1:4197'+prefix+relative
        with urllib.request.urlopen(url,timeout=15)as response:
            content=response.read();assert response.status==200 and sha(content)==f['sha256'],url
            rows.append({'url':url,'bytes':len(content),'sha256':sha(content),'contentType':response.headers.get('Content-Type')})
original=[]
for f in read(ROOT/'docs/evidence/lawson-fullpage-step-1/runtime-manifest.json')['runtimeFiles']:
    url='http://127.0.0.1:4197/original/'+f['path']
    with urllib.request.urlopen(url,timeout=15)as response:
        content=response.read();assert len(content)==f['bytes']and sha(content)==f['sha256'],url
        original.append({'path':f['path'],'bytes':len(content),'sha256':sha(content)})
missing=[]
for prefix in ['/','/Stylized-Dreamy-Flower-Bed-Sky-Island/']:
    for name in ['assets/step7-does-not-exist.js','experiments/lawson/assets/models/step7-missing.glb']:
        url='http://127.0.0.1:4197'+prefix+name
        try:urllib.request.urlopen(url,timeout=15);raise AssertionError('Missing resource served as success: '+url)
        except urllib.error.HTTPError as e:assert e.code==404;missing.append({'url':url,'status':e.code})
data={'passed':True,'finalBuildHTTPFiles':rows,'independentOriginalHTTPFiles':original,'missingResourceStatus':missing,'localOnly':True,'publicDeploymentVerified':False}
target.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'passed':True,'finalHTTPByteChecks':len(rows),'independentOriginalChecks':len(original),'missingResource404Checks':len(missing)}))
