"""Verify every built runtime URL, MIME and size under both deployment prefixes."""
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import hashlib,json
from runtime_files import ROOT,OUT,BUILT,manifest,verify,now
assert not (OUT/'http-verification.json').exists(),'Preserve previous HTTP evidence'
m=manifest();verify(BUILT,m)
routes={'root':'/','project':'/Stylized-Dreamy-Flower-Bed-Sky-Island/'}
result={'capturedAtShanghai':now(),'source':'actual dist files','routes':{},'negativeControls':[]}
for name,prefix in routes.items():
    rows=[]
    for f in m['runtimeFiles']:
        url='http://127.0.0.1:4193'+prefix+'experiments/lawson/'+f['path']
        with urlopen(Request(url,method='HEAD'),timeout=15)as response:
            row={'path':f['path'],'url':url,'status':response.status,'length':int(response.headers['Content-Length']),'type':response.headers.get_content_type()}
        assert row['status']==200 and row['length']==f['bytes'],row
        if f['path'].endswith('.js'):assert row['type']in ['text/javascript','application/javascript'],row
        if f['path'].endswith('.css'):assert row['type']=='text/css',row
        if f['path'].endswith('.glb'):assert row['type']!='text/html',row
        if f['path'].endswith('.html'):
            with urlopen(url,timeout=15)as response:assert hashlib.sha256(response.read()).hexdigest()==f['sha256']
        rows.append(row)
    with urlopen('http://127.0.0.1:4193'+prefix+'index.html',timeout=15)as response:
        assert hashlib.sha256(response.read()).hexdigest()==hashlib.sha256((ROOT/'dist/index.html').read_bytes()).hexdigest()
    result['routes'][name]={'prefix':prefix,'files':rows,'all46Correct':True,'hostIndexPresent':True}
    for suffix in ['missing.js','assets/models/missing.glb']:
        url='http://127.0.0.1:4193'+prefix+'experiments/lawson/'+suffix
        try:
            urlopen(Request(url,method='HEAD'),timeout=15)
            raise AssertionError('Missing asset returned success: '+url)
        except HTTPError as error:
            assert error.code==404
            result['negativeControls'].append({'url':url,'expected':404,'actual':error.code})
result['passed']=True
(OUT/'http-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'passed':True,'runtimeURLsVerified':92,'expected404Controls':4,'realHostIndexesVerified':2}))
