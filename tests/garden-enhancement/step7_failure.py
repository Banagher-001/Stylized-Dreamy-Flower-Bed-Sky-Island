"""Fresh final-version run of an accepted read-only harness; never copy reports."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
_qa_origin=ROOT/'tests/garden-enhancement/step6_failure.py'
_qa_bytes=_qa_origin.read_bytes();_qa_code=_qa_bytes.decode()
_qa_code=_qa_code.replace('from step6_common import *','from step7_common import *')
_qa_code=_qa_code.replace('127.0.0.1:4181','127.0.0.1:4183')
exec(compile(_qa_code,str(_qa_origin),"exec"),globals())
_qa_report=OUT/'failure-and-font.json'
if _qa_report.is_file():
 _qa_result=json.loads(_qa_report.read_text());_qa_result["freshHarness"]={"source":str(_qa_origin.relative_to(ROOT)),"sha256":hashlib.sha256(_qa_bytes).hexdigest(),"adaptations":{'from step6_common import *': 'from step7_common import *', '127.0.0.1:4181': '127.0.0.1:4183'}};_qa_report.write_text(json.dumps(_qa_result,ensure_ascii=False,indent=2)+"\n")
