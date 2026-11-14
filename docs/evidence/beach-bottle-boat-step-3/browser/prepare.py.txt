"""Pin the existing work before copying the fixed original bytes."""
from pathlib import Path
import shutil,struct,tempfile
from common import *
assert not OUT.exists(),'Preserve previous runs'
assert not RUNTIME.exists()and not COVER.exists(),'Do not overwrite existing runtime or cover'
history=verify_history();assert sha(SOURCE/'index.html')==ENTRY_SHA
assert git(SOURCE,'rev-parse','HEAD')=='d94c1f911a39143fd8f5efe152b99a87fdc53184'
OUT.mkdir(parents=True)
standard=DOC/'step-3-standard.md';shutil.copyfile(standard,OUT/'standard-before.md')
scratch=Path(tempfile.mkdtemp(prefix='bottle-ocean-step-3-',dir='/tmp'))
before={'capturedAtShanghai':now(),'hostCommit':git(ROOT,'rev-parse','HEAD'),'sourceCommit':git(SOURCE,'rev-parse','HEAD'),'hostStatusBefore':git(ROOT,'status','--short'),'historyBefore':history,'existingDistFiles':tree(ROOT/'dist'),'otherExistingDocuments':[row(p)for p in sorted(DOC.glob('*'))if p.is_file()and p!=standard],'standardBefore':row(standard),'scratch':str(scratch),'runtimePreviouslyPresent':False,'coverPreviouslyPresent':False,'step2Status':'standard only; not executed','versions':{name:subprocess.check_output(argv,text=True).strip()for name,argv in [('node',['node','--version']),('npm',['npm','--version']),('chromium',['chromium','--version'])]}}
write(OUT/'baseline.json',before)
RUNTIME.mkdir(parents=True)
for name in['index.html','THIRD_PARTY_NOTICES.md']:shutil.copyfile(SOURCE/name,RUNTIME/name);assert sha(SOURCE/name)==sha(RUNTIME/name)
shutil.copyfile(COVER_SOURCE,COVER);assert sha(COVER)==sha(COVER_SOURCE)=='7fc210e644776fda61efbe4d05a15e75392d5f563a024474dfcd0bfcf23da4fa'
b=COVER.read_bytes();assert b[:8]==b'\x89PNG\r\n\x1a\n';assert struct.unpack('>II',b[16:24])==(1920,1080)
write(OUT/'copied-files.json',{'capturedAtShanghai':now(),'runtime':[row(RUNTIME/n)for n in['index.html','THIRD_PARTY_NOTICES.md']],'cover':{**row(COVER),'width':1920,'height':1080,'source':COVER_SOURCE.relative_to(ROOT).as_posix(),'alt':'黄昏海岸的玻璃瓶中，三桅帆船随微型海浪起伏','condition':'Step-1 native screenshot download; Chromium 155; 1920x1080 CSS; DPR1; original fine; PNG contains WebGL scene without DOM panel'}})
print(json.dumps({'prepared':True,'originalBytesCopied':True,'coverCopied':True,'existingDistFilesProtected':len(before['existingDistFiles']),'scratch':str(scratch)},ensure_ascii=False))
