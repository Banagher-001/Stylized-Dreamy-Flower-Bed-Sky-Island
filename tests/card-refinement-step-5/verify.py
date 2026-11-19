"""Real wheel routes, projected flights, and native clicks on the built site."""
from pathlib import Path
import json
import shutil

from departure_support import (DESKTOP, Run, choose, detail_button, enter_paused, hover_card, midpoint,
                               paused_overflow, phase, points, progress, ready_automatic, tool_state)

r = Run()
for name in ('verify.py', 'departure_support.py'):
    shutil.copyfile(Path(__file__).with_name(name), r.out / (name + '.txt'))

TRACE = '''() => {
  window.exitTrace?.stop();
  const t=document.querySelector('.ar-tools-browser'), rail=t.querySelector('.ar-tool-rail');
  const scene=document.querySelector('#tour-host'), frames=[], wheel=[], cues=[];
  const box=e=>{const b=e.getBoundingClientRect();return [b.left,b.top,b.right,b.bottom]};
  const atWheel=e=>wheel.push({at:performance.now(),x:e.clientX,y:e.clientY,dy:e.deltaY,dx:e.deltaX,
    trusted:e.isTrusted,claimed:e.defaultPrevented});
  window.addEventListener('wheel',atWheel,{passive:true});
  const observer=new MutationObserver(()=>{if(rail.dataset.edgeContact)cues.push({at:performance.now(),side:rail.dataset.edgeContact});});
  observer.observe(rail,{attributes:true,attributeFilter:['data-edge-contact']});
  let next;
  function draw(){
    const d=t.dataset, state=d.departure, cards=[];
    if(state==='exiting'||state==='returning'||state==='departed'){
      for(const id of (d.departureIds||'').split(',')){
        const card=t.querySelector('[data-tool-id="'+id+'"]');
        if(!card) continue;
        const v=(card.dataset.flightPose||'0,0,0,0,0,0').split(',').map(Number);
        cards.push({id,instance:card.dataset.cardInstance,v,front:box(card.querySelector('.ar-card-front')),
          back:box(card.querySelector('.ar-card-back'))});
      }
    }
    frames.push({at:performance.now(),x:rail.scrollLeft,y:scrollY,target:scene.dataset.targetH,
      speed:Number(d.trackSpeed||0),cycle:Number(d.trackCycles||0),distance:Number(d.trackDistance||0),
      state,reason:d.departureReason,count:Number(d.departurePlays||0),redirects:Number(d.departureRedirects||0),
      track:d.trackFramePending==='true',frame:d.departureFramePending==='true',box:box(rail),cards});
    if(frames.length<260) next=requestAnimationFrame(draw);
  }
  window.exitTrace={stop(){cancelAnimationFrame(next);observer.disconnect();window.removeEventListener('wheel',atWheel);return {frames,wheel,cues}}};
  draw();
}'''


def start(page):
    page.evaluate(TRACE)


def trace(page):
    return page.evaluate('window.exitTrace.stop()')


def move_x(page, target):
    state = tool_state(page)
    page.mouse.move(*points(page)['left'])
    page.mouse.wheel(target-state['x'], 0)
    page.wait_for_timeout(210)
    return tool_state(page)


def wait_x(page, x):
    page.wait_for_function('x=>Math.abs(document.querySelector(".ar-tool-rail").scrollLeft-x)<=1', arg=x, timeout=6000)


def edge_damping(page):
    enter_paused(r,page)
    limit = paused_overflow(page)
    seed=move_x(page,80)
    assert abs(seed['x']-80)<=1
    start(page)
    page.mouse.wheel(0,480)
    page.wait_for_timeout(390)
    middle=trace(page)
    assert middle['frames'][-1]['x'] < limit-48
    at_end=move_x(page,limit-30)
    assert abs(at_end['x']-(limit-30))<=1
    start(page)
    for _ in range(4):
        page.mouse.wheel(0,480)
    wait_x(page,limit)
    page.wait_for_timeout(210)
    end=trace(page)
    at_start=move_x(page,30)
    assert abs(at_start['x']-30)<=1
    start(page)
    for _ in range(4):
        page.mouse.wheel(0,-480)
    wait_x(page,0)
    page.wait_for_timeout(210)
    beginning=trace(page)
    speed=[max(abs(f['speed']) for f in t['frames']) for t in (middle,end,beginning)]
    assert 0<max(speed[1:])<speed[0]*.86, speed
    for data,side in ((end,'end'),(beginning,'start')):
        assert all(w['claimed'] and w['trusted'] for w in data['wheel'])
        assert all(f['y']==seed['y'] and f['target']==seed['camera'] and f['state']=='idle' for f in data['frames'])
        gaps=[b['at']-a['at'] for a,b in zip(data['wheel'],data['wheel'][1:])]
        assert len(data['cues'])>=1 and len(data['cues'])<=1+sum(g>180 for g in gaps), data['cues']
        assert all(c['side']==side for c in data['cues'])
    start(page)
    page.mouse.wheel(0,120)
    page.wait_for_timeout(370)
    reverse=trace(page)
    first=next(f for f in reverse['frames'] if f['x']>=8)
    latency=first['at']-reverse['wheel'][0]['at']
    assert 0<=latency<=150,latency
    return {'limit':limit,'middleSpeed':speed[0],'endSpeed':speed[1],'startSpeed':speed[2],
            'reverseMs':latency,'middle':middle,'end':end,'beginning':beginning,'reverse':reverse}


def ring_continues(page):
    ready_automatic(r,page)
    before=tool_state(page)
    page.mouse.move(*points(page)['left'])
    start(page)
    page.mouse.wheel(0,-480)
    page.wait_for_function('n=>Number(document.querySelector(".ar-tools-browser").dataset.trackCycles)<n',arg=int(before['trackCycles']))
    page.wait_for_timeout(350)
    frames=trace(page)
    assert not frames['cues'] and all(f['state']=='idle' and f['y']==before['y'] for f in frames['frames'])
    assert frames['frames'][-1]['distance']<float(before['trackDistance'])-20
    assert frames['wheel'][0]['claimed']
    return {'before':before,'frames':frames}


def paint_is_spatial(frames, data):
    frames=[f for f in frames if f['state']=='exiting'];assert len(frames)>=4, len(frames)
    ids=data['departureIds'].split(',')
    travels=[]; seen_back=False
    for ident in ids:
        centers=[]
        for f in frames:
            c=next((c for c in f['cards'] if c['id']==ident),None)
            if not c:continue
            face=c['back'] if abs(c['v'][4])>90 else c['front']
            area=max(0,min(f['box'][2],face[2])-max(f['box'][0],face[0]))*max(0,min(f['box'][3],face[3])-max(f['box'][1],face[1]))
            if area<650:continue
            centers.append((face[0]+face[2])/2)
            if abs(c['v'][4])>90:seen_back=True
        if centers:travels.append(max(centers)-min(centers))
    assert seen_back and max(travels,default=0)>60, (seen_back,travels)
    return {'horizontalVisibleTravelPx':travels,'visibleBackFace':seen_back,'movingFrames':len(frames)}


def down_end_and_return(page):
    enter_paused(r,page)
    limit=paused_overflow(page)
    move_x(page,limit-25)
    start(page)
    page.mouse.wheel(0,480)
    page.mouse.wheel(0,480)
    wait_x(page,limit)
    before=tool_state(page)
    page.mouse.move(24,300)
    page.wait_for_timeout(190)
    still=tool_state(page)
    assert still['y']==before['y'] and still['departure']=='idle'
    progress(page,.71)
    assert tool_state(page)['departure']=='idle'
    progress(page,.86,wait=False)
    phase(page,'departed')
    parked=tool_state(page)
    assert parked['departureDirection']=='1' and float(parked['departureHandoffError'])<=1
    assert parked['departureFramePending']=='false' and parked['trackFramePending']=='false'
    assert json.loads(parked['departureSnapshot'])['cards']['category']=='G6'
    progress(page,.65,wait=False)
    phase(page,'idle')
    after=tool_state(page)
    assert after['departureReason']=='returned' and after['trackEnabled']=='false' and after['x']==before['x']
    data=trace(page)
    assert data['wheel'][0]['claimed'] and all(not e['claimed'] for e in data['wheel'][-3:])
    assert any(f['state']=='returning' for f in data['frames'])
    at_end=next(f for f in data['frames'] if f['state']=='departed')
    for c in at_end['cards']:
        if c['v'][0] < 0: assert max(c['front'][2],c['back'][2]) <= at_end['box'][0]-25
        else: assert min(c['front'][0],c['back'][0]) >= at_end['box'][2]+25
    return {'before':before,'parked':parked,'returned':after,'flight':paint_is_spatial(data['frames'],parked),'trace':data}


def up_preserves_pin(page):
    ready_automatic(r,page)
    card=hover_card(page)
    page.mouse.click(*midpoint(detail_button(page,card)),delay=80)
    page.wait_for_function('document.querySelector(".ar-tools-browser").dataset.detailMode==="pinned"')
    before=tool_state(page)
    progress(page,.26,wait=False)
    phase(page,'departed')
    left=tool_state(page)
    assert left['departureDirection']=='-1' and left['trackEnabled']=='true'
    assert json.loads(left['departureSnapshot'])['cards']['expandedId']==card
    assert all(f['y']>0 for f in json.loads(left['departureEndpoints']))
    progress(page,.52,wait=False)
    phase(page,'idle')
    page.wait_for_timeout(300)
    back=tool_state(page)
    assert back['detailMode']=='pinned' and back['readingId']==card and back['trackEnabled']=='true'
    assert back['trackFramePending']=='false' and back['trackDistance']==before['trackDistance']
    return {'before':before,'parked':left,'returned':back}


def halfway_reverse_and_near_return(page):
    enter_paused(r,page)
    before=move_x(page,110)
    start(page)
    progress(page,.85,wait=False)
    phase(page,'exiting')
    page.wait_for_function('''() => [...document.querySelectorAll('.ar-tool-card')].some(e=>Math.abs(Number(e.dataset.flightPose?.split(',')[0]))>16)''')
    active=tool_state(page)
    progress(page,.72,wait=False)
    phase(page,'returning')
    progress(page,.84,wait=False)
    page.wait_for_function('Number(document.querySelector(".ar-tools-browser").dataset.departureRedirects)>=1')
    redirected=tool_state(page)
    assert redirected['departureIds']==active['departureIds'] and redirected['departurePlays']==active['departurePlays']=='1'
    progress(page,.785)
    phase(page,'idle')
    last=tool_state(page)
    assert last['departureReason']=='returned' and last['x']==before['x'] and last['departurePlays']=='1'
    data=trace(page)
    assert len({tuple(c['instance'] for c in f['cards']) for f in data['frames'] if f['cards']})==1
    return {'active':active,'redirected':redirected,'restoredNearBoundary':last,'trace':data}


def quick_and_shortcut(page):
    enter_paused(r,page)
    progress(page,.93,wait=False)
    page.wait_for_function('document.querySelector(".ar-tools-browser").dataset.departureReason==="rapid-outward"')
    quick=tool_state(page)
    assert 190<=float(quick['departureDuration'])<=280
    phase(page,'departed')
    progress(page,.55)
    phase(page,'idle')
    before=tool_state(page)
    page.locator('[data-action="continue"]').click()
    page.wait_for_function('Math.abs(Number(document.querySelector("#tour-host").dataset.displayH)-4.95)<.006')
    shortcut=tool_state(page)
    assert shortcut['departurePlays']==before['departurePlays'] and shortcut['departure']=='idle'
    assert shortcut['departureFramePending']=='false'
    return {'quick':quick,'shortcut':shortcut}


def return_click(page):
    enter_paused(r,page)
    progress(page,.85,wait=False)
    phase(page,'departed')
    progress(page,.58,wait=False)
    phase(page,'returning')
    usable=page.wait_for_function('''() => {
      if(document.querySelector('.ar-tools-browser').dataset.departure!=='returning')return false;
      const r=document.querySelector('.ar-tool-rail').getBoundingClientRect();
      for(const e of document.querySelectorAll('.ar-tool-card[data-tool-id] .ar-card-front')){
        const b=e.getBoundingClientRect(), x=(Math.max(b.left,r.left)+Math.min(b.right,r.right))/2, y=b.top+b.height*.45;
        if(Math.min(b.right,r.right)-Math.max(b.left,r.left)<64)continue;
        if(document.elementFromPoint(x,y)?.closest('.ar-card-front')===e) return {x,y,id:e.closest('.ar-tool-card').dataset.toolId};
      }
      return false;
    }''',timeout=4500).json_value()
    page.mouse.move(usable['x'],usable['y'])
    page.wait_for_function('document.querySelector(".ar-tools-browser").dataset.departurePointerPaused==="true"',timeout=3500)
    page.evaluate('''() => {
      window.returnClicks=[];
      for(const type of ['pointerdown','pointerup','click'])window.addEventListener(type,e=>{
        const b=e.target.closest?.('button[data-action=detail]');if(!b)return;
        const r=b.getBoundingClientRect(), root=document.querySelector('.ar-tools-browser');
        window.returnClicks.push({type,id:b.dataset.toolId,phase:root.dataset.departure,zone:[r.x,r.y,r.width,r.height],
          held:root.dataset.departurePressed,trusted:e.isTrusted});
      },{capture:true,passive:true});
    }''')
    b=detail_button(page,usable['id']);page.mouse.click(*midpoint(b),delay=90)
    phase(page,'idle')
    final=tool_state(page)
    clicks=page.evaluate('window.returnClicks')
    assert [e['type'] for e in clicks]==['pointerdown','pointerup','click'] and all(e['phase']=='returning' and e['trusted'] for e in clicks),clicks
    error=max(abs(x-y) for e in clicks[1:] for x,y in zip(e['zone'],clicks[0]['zone']))
    assert error<=1 and clicks[-1]['held']=='true',clicks
    assert final['readingId']==usable['id'] and final['detailMode']=='pinned' and final['departureFramePending']=='false',final
    return {'card':usable['id'],'errorCssPx':error,'events':clicks,'final':final}


def resize_interrupt(page):
    enter_paused(r,page)
    progress(page,.85,wait=False)
    phase(page,'exiting')
    page.set_viewport_size({'width':1100,'height':850})
    phase(page,'idle')
    page.wait_for_timeout(350)
    s=tool_state(page)
    assert s['departureFramePending']=='false' and s['departureOwned']=='false'
    assert page.locator('.ar-tool-rail').evaluate('r=>[...r.querySelectorAll(".ar-tool-card")].every(e=>!e.dataset.flightPose||e.dataset.flightPose.split(",").every(v=>Number(v)===0))')
    return s


def reduced_interrupt(page):
    enter_paused(r,page)
    progress(page,.85,wait=False)
    phase(page,'exiting')
    page.emulate_media(reduced_motion='reduce')
    phase(page,'idle')
    page.wait_for_function('document.querySelector("main").dataset.readingMode==="stable"')
    r.go(page,'A3')
    rail=page.locator('.ar-tool-rail')
    rail.scroll_into_view_if_needed()
    before=tool_state(page)
    page.mouse.move(*points(page)['center'])
    page.mouse.wheel(0,120)
    page.wait_for_function('x=>document.querySelector(".ar-tool-rail").scrollLeft>x+8',arg=before['x'])
    after=tool_state(page)
    assert after['departureOwned']=='false' and after['departurePlays']==before['departurePlays']
    assert after['departureFramePending']=='false' and after['trackFramePending']=='false'
    assert rail.evaluate('e=>!e.dataset.edgeContact')
    return {'before':before,'after':after,'mediaEmulation':True}


try:
    r.case('finite-edge-braking-and-first-reverse',edge_damping,size=DESKTOP)
    r.case('program-seam-stays-continuous',ring_continues,size=DESKTOP)
    r.case('native-handoff-down-and-back',down_end_and_return,size=DESKTOP,video=True)
    r.case('upward-flight-with-pin',up_preserves_pin,size=DESKTOP)
    r.case('mid-flight-redirect-and-readable-edge-return',halfway_reverse_and_near_return,size=DESKTOP)
    r.case('accelerated-flight-and-direct-navigation',quick_and_shortcut,size=DESKTOP)
    r.case('first-click-in-return',return_click,size=DESKTOP)
    r.case('resize-clears-departure',resize_interrupt,size=DESKTOP)
    r.case('reduced-motion-clears-flight-and-keeps-cards',reduced_interrupt,size=DESKTOP)
finally:
    ok=r.finish()
raise SystemExit(0 if ok else 1)
