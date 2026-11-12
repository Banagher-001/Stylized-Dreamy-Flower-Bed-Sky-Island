"""Original movement keys, mouse look and the reset-in-walk boundary."""
import argparse
from common import Run

parser = argparse.ArgumentParser()
parser.add_argument('--run', default='run-5')
parser.add_argument('--only', default='')
args = parser.parse_args()
r = Run('keyboard', args.run)
r.only = args.only.split(',') if args.only else None
p = r.page
try:
    r.case('KEYS.load', '移动操作补核加载', r.load)
    r.report['functionalSetup'] = r.low()
    p.evaluate('''async()=>{
      const {CameraSystem}=await import('./js/systems/CameraSystem.js');
      const raw=CameraSystem.prototype._walkUpdate,a=__fullpageAudit;
      a.walkFrames=[];
      CameraSystem.prototype._walkUpdate=function(dt){
        a.cameraInstance=this;
        const row={dt,keys:{...this.keys},before:this.camera.position.toArray(),nativeBaseSpeed:this.walk.speed};
        const value=raw.call(this,dt);row.after=this.camera.position.toArray();
        if(a.walkFrames.length<4000)a.walkFrames.push(row);return value;
      };
    }''')

    def enter():
        p.locator('#btn-walk').click()
        p.wait_for_function('document.pointerLockElement?.id==="viewport" && __LAWSON__.api.getState().walk===true', polling=100)
        p.wait_for_function('!!__fullpageAudit.cameraInstance', polling=100)
        return r.state()

    def leave():
        p.keyboard.press('Escape')
        p.wait_for_function('!document.pointerLockElement && !__LAWSON__.api.getState().walk', polling=100)

    def movement(key, code, shift=None):
        start = enter()
        setup = []
        if code == 'KeyW':
            for setup_key in ['s','a']:
                before_setup=r.state()
                p.keyboard.down(setup_key)
                r.observed(.4)
                p.keyboard.up(setup_key)
                setup.append({'key':setup_key,'before':before_setup,'after':r.state()})
            start=r.state()
        blockers=p.evaluate('__fullpageAudit.cameraInstance.blockers.map(b=>({min:b.min.toArray(),max:b.max.toArray()}))')
        frame = p.evaluate('__fullpageAudit.walkFrames.length')
        if shift:
            p.keyboard.down(shift)
        p.keyboard.down(key)
        r.observed(.12)
        p.keyboard.up(key)
        if shift:
            p.keyboard.up(shift)
        end = r.state()
        rows = p.evaluate('(n)=>__fullpageAudit.walkFrames.slice(n)', frame)
        active = [row for row in rows if row['keys'].get(code)]
        assert active, rows
        distance = sum((a-b)**2 for a,b in zip(start['camera'][::2],end['camera'][::2])) ** .5
        for row in active:
            row['planarDistance'] = sum((row['after'][i]-row['before'][i])**2 for i in [0,2])**.5
            row['observedStepSpeed'] = row['planarDistance']/row['dt'] if row['dt'] else 0
        if shift:
            assert any(row['keys'].get(shift) and row['observedStepSpeed']>row['nativeBaseSpeed']*1.3 for row in active), active
        leave()
        return {'_status':'原页正常' if distance>.02 else '原页已有问题',
                'key':code,'shift':shift,'entered':start,'afterMovement':end,'planarDistance':distance,'originalWalkFrames':rows,'nativePositioningSetup':setup,'originalBlockers':blockers,
                'observation':'original _walkUpdate invoked exactly once with original dt; only read keys/positions before and after',
                'conclusion':'Actual planar movement observed.' if distance>.02 else 'Original movement handler receives the key, but collision handling blocks planar displacement at the observed position; not an iframe regression.',
                'exit':r.state()}

    for key,code in [('w','KeyW'),('s','KeyS'),('a','KeyA'),('d','KeyD')]:
        r.case('KEY.'+code, code+'原漫游移动', lambda key=key,code=code:movement(key,code))
    for shift in ['ShiftLeft','ShiftRight']:
        r.case('KEY.'+shift, shift+'与A组合加速', lambda shift=shift:movement('a','KeyA',shift))

    def mouse_look():
        entered=enter()
        before=p.evaluate('({yaw:__fullpageAudit.cameraInstance.walk.yaw,pitch:__fullpageAudit.cameraInstance.walk.pitch})')
        p.mouse.move(420,270)
        r.observed(.12)
        after=p.evaluate('({yaw:__fullpageAudit.cameraInstance.walk.yaw,pitch:__fullpageAudit.cameraInstance.walk.pitch})')
        assert before!=after
        r.picture('walk-mouse-look-original')
        leave()
        return {'entered':entered,'before':before,'after':after,'exit':r.state()}
    r.case('POINTER.walk-look','漫游鼠标观察与退出',mouse_look)

    def reset_while_walking():
        before=enter()
        p.keyboard.press('r')
        p.wait_for_function('!document.pointerLockElement',polling=100)
        r.observed()
        after_r={'snapshot':r.state(),'actualCameraMode':p.evaluate('__fullpageAudit.cameraInstance.mode'),'walkBarVisible':p.locator('#walk-bar').is_visible()}
        p.locator('[data-preset=night]').click()
        after_sync={'snapshot':r.state(),'actualCameraMode':p.evaluate('__fullpageAudit.cameraInstance.mode'),'walkBarVisible':p.locator('#walk-bar').is_visible(),'walkButtonActive':p.locator('#btn-walk').evaluate('e=>e.classList.contains("active")')}
        r.picture('reset-in-walk-followed-by-ui-sync')
        issue=after_sync['actualCameraMode']=='orbit' and (after_sync['snapshot']['state']['walk'] or after_sync['walkBarVisible'])
        p.locator('#btn-reset-cam').click()
        restored=r.state()
        assert not restored['state']['walk'] and p.locator('#walk-bar').is_hidden()
        return {'_status':'原页已有问题' if issue else '原页正常','entered':before,'afterKeyR':after_r,'afterOriginalNightButton':after_sync,'recoveredUsingOriginalResetButton':restored,
                'reproduction':'Enter walk → R → select night; compare actual camera mode with cached walk/UI state',
                'conclusion':'KeyR exits movement and pointer lock, but does not patch cached walk state; a later original UI sync can redisplay walk UI. Source left unchanged.' if issue else 'No state inconsistency observed.'}
    r.case('BOUNDARY.R-in-walk','漫游中R复位后的原状态一致性',reset_while_walking)
finally:
    r.finish()
