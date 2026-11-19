"""Observe every original vehicle's route at the native fast speed."""
from time import monotonic

from pair_support import BrowserRun, LAWSON, position, save


r = BrowserRun()


def traffic(page, scene, side):
    for _ in range(3):
        if scene.evaluate('__LAWSON__.state.quality')=='low':
            break
        scene.locator('#btn-settings').click()
    assert scene.evaluate('__LAWSON__.state.quality')=='low'
    scene.locator('[data-speed="1.8"]').click()
    assert scene.evaluate('__LAWSON__.state.traffic.speed')==1.8
    scene.locator('[data-cam=vehicle]').click()
    initial=position(page)
    cycles={}
    for car in 'ABC':
        scene.locator(f'[data-car={car}]').click()
        scene.wait_for_function('tag=>__LAWSON__.api.getVehicleState(tag).active',arg=car,polling=100)
        timeline=[]
        phases=set()
        started=monotonic()
        moving=False
        reverse=False
        print(side,'car',car,'native cycle started',flush=True)
        while monotonic()-started<480:
            sample=scene.evaluate('''tag=>({
              vehicle:__LAWSON__.api.getVehicleState(tag),
              tasks:Object.fromEntries(Object.entries(__LAWSON__.api.getClerkStates().clerks).map(([key,value])=>[key,value.task]))
            })''',car)
            v=sample['vehicle']
            phases.add(v['phase'])
            moving=moving or abs(v['wheelSpinTotal'])>.1
            reverse=reverse or v['reverseLamp']
            timeline.append({'seconds':round(monotonic()-started,3),**sample})
            if len(timeline)%15==1:
                save(r.out/f'{side}-car-{car}-progress.json',{'phases':sorted(phases),'timeline':timeline})
            if {'PARKED','REVERSING_OUT','DRIVING_OUT'}.issubset(phases) and not v['active'] and not v['visible']:
                break
            page.wait_for_timeout(600)
        else:
            raise AssertionError((side,car,sorted(phases),timeline[-1]))
        assert moving and reverse and len({tuple(x['vehicle']['position']) for x in timeline})>5,car
        cycles[car]={'phases':sorted(phases),'wallSeconds':timeline[-1]['seconds'],'timeline':timeline,
                     'wheelRotation':moving,'reverseLamp':reverse,'completed':True}
        save(r.out/f'{side}-car-{car}.json',cycles[car])
        print(side,'car',car,'completed',cycles[car]['wallSeconds'],'seconds',flush=True)
    assert side=='reference' or position(page)==initial
    return {'comparison':{car:cycles[car]['completed'] for car in 'ABC'},'cars':cycles,'speed':1.8}


try:
    r.pairs('lawson-vehicle-cycles',LAWSON,traffic)
finally:
    ok=r.finish()
raise SystemExit(0 if ok else 1)
