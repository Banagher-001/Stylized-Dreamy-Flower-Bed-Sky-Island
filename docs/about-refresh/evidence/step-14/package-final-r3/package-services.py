from pathlib import Path
import json,subprocess,time,os,signal,socket
OUT=Path(__file__).parent
validation=json.loads((OUT/'package-validation.json').read_text());assert validation['complete']
assert not (OUT/'package-services-started.json').exists()
children=[];records=[]
try:
    for kind in ['site','source']:
        directory=Path(validation['archives'][kind]['directory']);site=directory if kind=='site' else directory/'dist'
        for base in ['/','/portfolio-check/']:
            p=subprocess.Popen(['node',str(directory/'scripts/preview-site.mjs'),'--dir',str(site),'--port','0','--base',base,'--json'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,start_new_session=True)
            children.append(p);lines=[]
            while True:
                line=p.stdout.readline();lines.append(line)
                if line.startswith('SAKAN_PREVIEW_READY '):
                    ready=json.loads(line.split(' ',1)[1]);break
                assert p.poll() is None,lines
            records.append({'kind':kind,'base':base,'origin':ready['url'],'directory':str(site),'pid':p.pid,'processGroup':os.getpgid(p.pid)})
    (OUT/'package-services-started.json').write_text(json.dumps({'services':records},ensure_ascii=False,indent=2)+'\n');print(json.dumps({'ready':True,'services':records},ensure_ascii=False),flush=True)
    while not (OUT/'stop-package-services').exists():
        assert all(p.poll() is None for p in children);time.sleep(.3)
finally:
    for p in reversed(children):
        if p.poll() is None:os.killpg(os.getpgid(p.pid),signal.SIGTERM)
        try:p.wait(timeout=6)
        except subprocess.TimeoutExpired:os.killpg(os.getpgid(p.pid),signal.SIGKILL);p.wait(timeout=5)
    ports=[]
    from urllib.parse import urlsplit
    for record in records:
        with socket.socket() as probe:
            probe.settimeout(.3);ports.append({'url':record['origin'],'closed':probe.connect_ex(('127.0.0.1',urlsplit(record['origin']).port))!=0})
    (OUT/'package-services-cleanup.json').write_text(json.dumps({'stoppedOwnedProcesses':len(children),'ports':ports,'otherServicesStopped':False},indent=2)+'\n')
    print(json.dumps({'closed':True,'ports':ports}),flush=True)
