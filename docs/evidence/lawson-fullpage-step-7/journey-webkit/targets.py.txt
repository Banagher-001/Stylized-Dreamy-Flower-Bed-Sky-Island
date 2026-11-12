"""Observe actual pointer activation and actual effects for every original target class."""
import argparse, json, math
from common import Run

parser = argparse.ArgumentParser()
parser.add_argument('--run', default='run-2')
parser.add_argument('--skip', default='', help='Previously evidenced target IDs, comma separated')
args = parser.parse_args()
r = Run('targets', args.run)
p = r.page

GEOMETRY = r'''async () => {
 const a=__fullpageAudit;a.THREE=await import('three');
 a.effectiveVisible=o=>{while(o){if(!o.visible)return false;o=o.parent;}return true;};
 a.boxFor=entry=>{const box=new a.THREE.Box3();for(const mesh of entry.meshes)if(a.effectiveVisible(mesh))box.union(new a.THREE.Box3().setFromObject(mesh));return box;};
 a.placement=id=>{const e=a.interaction.interactives.find(e=>e.id===id),b=a.boxFor(e);return {id:e.id,label:e.label,action:e.action,meshCount:e.meshes.length,center:b.getCenter(new a.THREE.Vector3()).toArray(),size:b.getSize(new a.THREE.Vector3()).toArray()};};
 a.candidates=id=>{
  const entry=a.interaction.interactives.find(e=>e.id===id),out=[];
  for(const mesh of entry.meshes){
   if(!a.effectiveVisible(mesh))continue;
   const b=new a.THREE.Box3().setFromObject(mesh),c=b.getCenter(new a.THREE.Vector3()),s=b.getSize(new a.THREE.Vector3());
   for(const v of [[0,0,0],[-.28,0,0],[.28,0,0],[0,.28,0],[0,-.28,0],[0,0,-.28],[0,0,.28]]){
    const world=[c.x+v[0]*s.x,c.y+v[1]*s.y,c.z+v[2]*s.z],pt=__LAWSON__.api.project(world);
    if(pt[0]<12||pt[0]>innerWidth-70||pt[1]<64||pt[1]>innerHeight-38)continue;
    if(document.elementFromPoint(...pt)?.id!=='viewport')continue;
    const hit=__LAWSON__.api.pickAt(...pt);if(hit?.action!==entry.action||hit?.label!==entry.label)continue;
    out.push({point:pt,world,mesh:mesh.name,hit});break;
   }
   if(out.length>=5)break;
  }
  return out;
 };
 return a.interaction.interactives.map(e=>({id:e.id,label:e.label,action:e.action,meshCount:e.meshes.length}));
}'''

try:
    r.case('TARGETS.load', '补核独立原网页加载', r.load)
    r.report['functionalSetup'] = r.low()
    p.mouse.move(280, 300)
    p.wait_for_function('!!__fullpageAudit.interaction', timeout=15000)
    entries = p.evaluate(GEOMETRY)
    assert len(entries) == 17
    r.report['originalInteractiveEntries'] = entries
    r.save()
    if not p.locator('#panel').evaluate('e=>e.classList.contains("collapsed")'):
        p.locator('#panel-collapse').click()

    order = ['sign', 'facade', 'door', 'vending', 'basket', 'checkout', 'shelf', 'alcohol', 'oden', 'clerkA', 'clerkB', 'atm', 'freezer', 'cooler', 'microwave', 'dining', 'coffee']
    by_id = {e['id']: e for e in entries}
    for identifier in order:
        if identifier in args.skip.split(','):
            continue
        def interact(identifier=identifier):
            entry = by_id[identifier]
            if identifier not in ['sign', 'facade', 'door', 'vending']:
                if p.evaluate('__LAWSON__.api.getState().roofVisible'):
                    # Original roof button, not an artificial scene visibility mutation.
                    p.locator('#panel-collapse').click()
                    p.locator('#btn-roof').click()
                    p.locator('#panel-collapse').click()
            placement = p.evaluate('(id)=>__fullpageAudit.placement(id)', identifier)
            assert all(math.isfinite(v) for v in placement['center']), placement
            distance = max(4.8, min(26, max(placement['size']) * .85))
            attempts, chosen, activation = [], None, None
            directions = [[0,.35,1],[-.8,.25,1],[.8,.25,1],[-1,.25,0],[1,.25,0],[0,.25,-1],[.08,1,.08]]
            for direction in directions:
                length = sum(v*v for v in direction) ** .5
                position = [c + v / length * distance for c,v in zip(placement['center'],direction)]
                # Existing source camera helper is setup only; the action below is native pointer input.
                before_frame = p.evaluate('__lawsonAudit.mainFrames')
                p.evaluate('(pose)=>__LAWSON__.api.setFreeCamera(pose.pos,pose.target)', {'pos': position, 'target': placement['center']})
                p.wait_for_function('n=>__lawsonAudit.mainFrames>n+1', arg=before_frame, timeout=30000, polling=100)
                candidates = p.evaluate('(id)=>__fullpageAudit.candidates(id)', identifier)
                attempts.append({'position': position, 'target': placement['center'], 'candidates': candidates})
                for candidate in candidates[:3]:
                    n = p.evaluate('__fullpageAudit.activations.length')
                    p.mouse.move(*candidate['point'])
                    p.mouse.click(*candidate['point'])
                    p.wait_for_timeout(100)
                    actual = p.evaluate('(n)=>__fullpageAudit.activations.slice(n)', n)
                    match = next((a for a in actual if a['action'] == entry['action']), None)
                    if match:
                        assert match['handlerPresent'], match
                        chosen, activation = candidate, match
                        break
                if chosen:
                    break
            assert chosen and activation, {'target': entry, 'attempts': attempts}
            kind = entry['action'].split(':')[0]
            if kind == 'focus':
                # Clear only the source free-camera setup so the original focus tween is visible.
                p.evaluate('__LAWSON__.api.clearFreeCamera()')
                r.observed()
                effect_after = p.evaluate('(a)=>__fullpageAudit.signature(a)', entry['action'])
                displacement = sum((a-b)**2 for a,b in zip(activation['before']['camera'],effect_after['camera'])) ** .5
                assert displacement > .05, (activation, effect_after)
                effect = {'cameraMovedWorldUnits': displacement, 'after': effect_after}
            elif kind == 'door':
                p.wait_for_function('t=>Math.abs(__LAWSON__.debugDoor().progress-t)<.01', arg=activation['after']['target'], timeout=45000, polling=100)
                effect_after = p.evaluate('__LAWSON__.debugDoor()')
                assert abs(effect_after['progress'] - activation['after']['target']) < .01
                effect = effect_after
            else:
                assert activation['before'] != activation['after'], activation
                effect = activation['after']
            r.picture('target-' + identifier)
            return {'entry': entry, 'cameraSetup': 'original public setFreeCamera helper; only aids view placement, not action dispatch',
                    'placementAttempts': attempts, 'actualPointer': chosen, 'originalActivation': activation, 'observedEffect': effect,
                    'actionWasNotInvokedThroughClickAtOrActivateAPI': True}
        r.case('TARGET.' + identifier, by_id[identifier]['label'] + '真实点击及反馈', interact)
    p.evaluate('__LAWSON__.api.clearFreeCamera()')
finally:
    r.finish()
