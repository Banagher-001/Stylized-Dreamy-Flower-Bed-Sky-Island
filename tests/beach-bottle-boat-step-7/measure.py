"""Measure actual child viewports before configuring the independent counterpart."""
from harness import *
args=arguments();r=Run(args);conditions={}
try:
 for key,host,dpr,touch in[('desktop',[1440,900],1,False),('phone',[390,844],3,True),('landscape',[844,390],3,True),('narrow',[320,740],2,True)]:
  r.case_id='MEASURE.'+key;s=Session(r,'embedded',{'host':host,'dpr':dpr,'touch':touch})
  try:
   s.open();info=s.conditions;conditions[key]={'host':host,'child':info['viewport'],'dpr':dpr,'touch':touch};r.report['checks'].append({'id':r.case_id,'status':'配对通过','evidence':info});s.picture('measured-'+key)
  finally:s.close()
 write(OUT/'pair-conditions.json',conditions);print(json.dumps(conditions),flush=True)
finally:r.finish()
