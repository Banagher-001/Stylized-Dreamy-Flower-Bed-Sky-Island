"""Complete the original B/C cycles; prior A cycle and clerk evidence are reused."""
import argparse,json,time
from common import Run

parser=argparse.ArgumentParser()
parser.add_argument('--run',default='run-6')
parser.add_argument('--cars',default='B,C')
args=parser.parse_args()
r=Run('traffic',args.run)
p=r.page
try:
    r.case('CYCLES.load','车辆B/C完整流程补核加载',r.load)
    r.report['functionalSetup']=r.low()
    p.locator('[data-speed="1.8"]').click()
    p.locator('[data-cam=vehicle]').click()
    for tag in args.cars.split(','):
        def cycle(tag=tag):
            p.locator(f'[data-car={tag}]').click()
            p.wait_for_function('(tag)=>__LAWSON__.api.getVehicleState(tag).active',arg=tag,polling=100)
            timeline=[];phases=set();started=time.monotonic();complete=False
            while time.monotonic()-started<420:
                state=p.evaluate('(tag)=>({vehicle:__LAWSON__.api.getVehicleState(tag),traffic:__LAWSON__.api.getState().traffic,clerks:__LAWSON__.api.getClerkStates(),stats:__LAWSON__.api.getStats()})',tag)
                timeline.append({'wallSeconds':time.monotonic()-started,**state});phases.add(state['vehicle']['phase'])
                if len(timeline)%5==0:
                    (r.folder/f'car-{tag}-progress.json').write_text(json.dumps({'complete':False,'tag':tag,'timeline':timeline},ensure_ascii=False,indent=2)+'\n')
                if {'PARKED','REVERSING_OUT','DRIVING_OUT'}.issubset(phases) and not state['vehicle']['active'] and not state['vehicle']['visible']:
                    complete=True;break
                p.wait_for_timeout(700)
            assert complete,{'tag':tag,'phases':sorted(phases),'last':timeline[-1]}
            assert any(abs(row['vehicle']['wheelSpinTotal'])>.1 for row in timeline)
            assert any(row['vehicle']['reverseLamp'] for row in timeline)
            r.picture('car-'+tag+'-cycle-complete')
            return {'tag':tag,'complete':complete,'nativeClock':True,'speedSelectedThroughOriginalUI':1.8,'viewport':[960,540],'quality':'low',
                    'phases':sorted(phases),'wallSeconds':timeline[-1]['wallSeconds'],'timeline':timeline,
                    'clerkTasksObserved':{t:sorted({row['clerks']['clerks'][t]['task']for row in timeline if row['clerks']['clerks'][t]['task']})for t in ['A','B']}}
        r.case('CYCLE.'+tag,'车辆'+tag+'进场、停车、倒车、离场及交接',cycle)
finally:
    r.finish()
