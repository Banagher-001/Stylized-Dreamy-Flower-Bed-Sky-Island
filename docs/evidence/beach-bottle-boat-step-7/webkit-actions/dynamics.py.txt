"""17 paired natural trajectories; original timing/RAF/randomness are untouched."""
from harness import *
args=arguments();r=Run(args)
conditions=[]
for value in[0,50,100]:conditions.append(('waveHeight-'+str(value),{'waveHeight':value}))
for value in[0,90,180,270]:conditions.append(('direction-'+str(value),{'waveHeight':50,'waveDirection':value}))
for name in['boatResponse','boatDamping','wind']:
 for value in[0,100]:conditions.append((name+'-'+str(value),{'waveHeight':50,name:value}))
for value in[0,100]:conditions.append(('waterLevel-'+str(value),{'waveHeight':50,'waterLevel':value}))
for value in[0,100]:conditions.append(('strong-water-'+str(value),{'waveHeight':100,'wind':100,'waterLevel':value}))
assert len(conditions)==17
try:
 for label,configuration in conditions:
  def sample(s,label=label,configuration=configuration):
   s.reset()
   for name,value in configuration.items():s.slider(name,value)
   settling=4 if configuration.get('waveHeight')==0 else 2;start=s.evaluate('__bottleOcean.getDiagnostics().simTime');deadline=time.monotonic()+240
   while s.evaluate('__bottleOcean.getDiagnostics().simTime')-start<settling:
    assert time.monotonic()<deadline,'Natural settling exceeded wall limit';s.page.wait_for_timeout(500)
   before=s.snapshot();s.evaluate('''()=>{const a=__parityProbe.observation={rows:[],done:false,lastDraw:-1};function read(){const b=__bottleOcean,d=b.getDiagnostics(),draws=__parityProbe.draws;if(draws!==a.lastDraw){a.lastDraw=draws;a.rows.push({observedFrame:a.rows.length,drawCounter:draws,wall:performance.now(),simTime:d.simTime,boat:d.boat,water:d.water,gpuWaveTime:b.waterField.uniforms.uTime.value,sails:b.boat.masts.map(m=>m.sails.map(s=>({x:s.pivot.rotation.x,z:s.pivot.rotation.z,pz:s.pivot.position.z})))})}if(a.rows.length>=40&&a.rows.at(-1).simTime-a.rows[0].simTime>=8)a.done=true;else requestAnimationFrame(read)}requestAnimationFrame(read)}''');deadline=time.monotonic()+300;wall=time.monotonic();lastPrinted=-1
   while not s.evaluate('__parityProbe.observation.done'):
    assert time.monotonic()<deadline,'Natural 8-sim-second window exceeded wall limit';s.page.wait_for_timeout(1500);data=s.evaluate('__parityProbe.observation');write(r.folder/(label+'-'+s.side+'-partial.json'),data)
    if data['rows']:
     elapsed=int(data['rows'][-1]['simTime']-data['rows'][0]['simTime'])
     if elapsed!=lastPrinted:print(label+' '+s.side+' '+str(elapsed)+' natural sim seconds',flush=True);lastPrinted=elapsed
   rows=s.evaluate('__parityProbe.observation.rows');window=rows[-1]['simTime']-rows[0]['simTime'];assert window>=8 and len({x['drawCounter']for x in rows})>=40
   for x in rows:
    assert abs(x['gpuWaveTime']-x['simTime'])<1e-8
    for value in x['boat']['position']+[x['boat']['pitch'],x['boat']['roll'],x['water']['heightAtBoat']]:assert math.isfinite(value)
   ranges={name:max(x['boat'][name]for x in rows)-min(x['boat'][name]for x in rows)for name in['rootY','pitch','roll']};ranges['surface']=max(x['water']['heightAtBoat']for x in rows)-min(x['water']['heightAtBoat']for x in rows)
   if configuration.get('waveHeight')==0:assert before['actual']['amplitude']==0 and ranges['surface']<1e-8
   if configuration.get('waveHeight',50)>0:assert ranges['surface']>.005
   if configuration.get('waveHeight',50)>0 and configuration.get('boatResponse',72)>0:assert ranges['rootY']>.002 and max(ranges['pitch'],ranges['roll'])>.003
   after=s.snapshot();s.picture('trajectory-'+label);actualConfig={name:after['diagnostics']['state'][name]for name in configuration};assert actualConfig==configuration;return {'configuration':configuration,'before':before,'after':after,'simSeconds':window,'distinctRenderedFrames':len({x['drawCounter']for x in rows}),'wallSeconds':time.monotonic()-wall,'range':ranges,'allReportedInsideBottle':all(x['boat']['safety']['withinBottle']for x in rows),'rows':rows,'comparison':{'configuration':actualConfig,'sampledAtLeast8SimSeconds':True,'atLeast40DifferentRenderedFrames':True,'GPUTimeMatchesOriginalSimulation':True},'phaseMatchedTrajectoryClaimed':False}
  r.pair('DYN.'+label,[],sample)
finally:r.finish()
