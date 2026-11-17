from pathlib import Path
import json,subprocess,urllib.request,urllib.error
ROOT=Path(__file__).resolve().parents[5];OUT=Path(__file__).parent
services=json.loads((OUT/'package-services-started.json').read_text())['services'];build=json.loads((OUT/'build.json').read_text())
checks=[]
for service in services:
    label=service['kind']+('-root' if service['base']=='/' else '-prefix');origin=service['origin']
    http=[]
    for resource,expected in [('index.html','text/html'),(next(x['path'] for x in build['production'] if x['path'].endswith('.js')),'javascript')]:
        with urllib.request.urlopen(origin+resource) as response:
            mime=response.headers['Content-Type'];assert response.status==200 and expected in mime
            http.append({'resource':resource,'status':response.status,'MIME':mime})
    media=next(x['path'] for x in build['production'] if x['path'].endswith('.mp4'))
    with urllib.request.urlopen(urllib.request.Request(origin+media,headers={'Range':'bytes=0-31'})) as response:
        data=response.read();assert response.status==206 and len(data)==32 and response.headers['Content-Range'].startswith('bytes 0-31/')
        http.append({'resource':media,'status':206,'bytes':len(data),'contentRange':response.headers['Content-Range']})
    try: urllib.request.urlopen(origin+'deliberately-missing.js')
    except urllib.error.HTTPError as error: assert error.code==404;http.append({'resource':'deliberately-missing.js','status':404,'expected':True})
    else:raise AssertionError('Missing resource must not become an HTML fallback')
    folder=OUT/('portable-'+label)
    command=['python',str(ROOT/'tests/about-refresh-final/package_smoke.py'),'--origin',origin,'--out',str(folder),'--env-file',str(OUT/'services-started.json'),'--build-record',str(OUT/'build.json')]
    with (OUT/('portable-'+label+'.txt')).open('w') as log:
        completed=subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
    entry={'label':label,'origin':origin,'root':service['directory'],'HTTP':http,'browserRecord':str(folder.relative_to(OUT)/'browser.json'),'exitCode':completed.returncode};checks.append(entry)
    (OUT/'portable-validation.json').write_text(json.dumps({'candidateId':build['candidateId'],'checks':checks,'complete':len(checks)==4 and all(x['exitCode']==0 for x in checks)},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'portable':label,'exitCode':completed.returncode}),flush=True)
    assert completed.returncode==0,label
