"""Real pointer/DOM integration checks for the read-only step-1 contract."""
from pathlib import Path
import sys,json,shutil
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests/about-refresh-final'))
from support import Run
r=Run()
shutil.copyfile(__file__,r.out/'verify.py.txt')

def snapshot(page):
    return page.locator('.ar-card-region-debug').evaluate('e=>JSON.parse(e.dataset.snapshot)')
def debug(page):
    page.goto(r.origin+'?debug=1',wait_until='domcontentloaded')
    page.wait_for_function('document.querySelector("main")?.dataset.layoutReady==="true"&&document.querySelector("#tour-host")?.dataset.renderState==="ready"',timeout=90000)
    page.wait_for_selector('.ar-card-region-debug',state='attached')
def category(page, name):
    if page.locator('.ar-category-select').is_visible():page.locator('.ar-category-select select').select_option(name)
    else:page.locator('button[data-category='+name+']').click()
    page.wait_for_timeout(350)
def enter(page):
    r.go(page,'A3')
    page.wait_for_function('document.querySelector(".ar-tools-browser").dataset.entranceReady==="true"')
def move(page,x,y,owner):
    page.mouse.move(x,y)
    page.evaluate('()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
    page.wait_for_function('o=>JSON.parse(document.querySelector(".ar-card-region-debug").dataset.snapshot).owner===o',arg=owner)
    return snapshot(page)
def center(page,owner='cards'):
    page.wait_for_function('JSON.parse(document.querySelector(".ar-card-region-debug").dataset.snapshot).visibleBounds!==null')
    s=snapshot(page);b=s['visibleBounds'];assert b,s
    return move(page,(b['left']+b['right'])/2,(b['top']+b['bottom'])/2,owner)

def normal(page):
    assert page.locator('.ar-card-region-debug').count()==0
    enter(page);category(page,'G6');page.mouse.move(24,300)
    s=r.state(page);assert len(s['cards'])==5 and s['tools']['trackEnabled']=='false'
    assert page.locator('.ar-card-region-debug').count()==0
    page.locator('.ar-tool-card button').first.click()
    assert r.state(page)['tools']['detailMode']=='pinned'
    assert page.locator('.ar-card-region-debug').count()==0
    return {'debugAbsent':True,'existingFilterPauseAndPinUnchanged':True,'state':r.state(page)}

def desktop(page):
    debug(page);enter(page);category(page,'G6')
    s=center(page);assert s['overflow'] and not s['automatic']
    assert s['bounds']['width']>page.locator('.ar-tool-rail').bounding_box()['width']
    points=[];b=s['visibleBounds'];y=(b['top']+b['bottom'])/2
    for x in [b['left']+6,b['right']-6]:points.append(move(page,x,y,'cards'))
    cards=page.locator('.ar-tool-slot').evaluate_all('es=>es.map(e=>{const r=e.getBoundingClientRect();return{x:r.x,right:r.right,y:r.y,height:r.height}})')
    x=(cards[0]['right']+cards[1]['x'])/2
    points.append(move(page,x,y,'cards'))
    button=page.locator('.ar-tool-card button').first
    box=button.bounding_box();move(page,box['x']+box['width']/2,box['y']+box['height']/2,'cards')
    page.mouse.move(24,300);page.wait_for_timeout(450)
    button.focus();page.keyboard.press('Enter')
    page.wait_for_function('document.querySelector(".ar-tools-browser").dataset.detailMode==="pinned"')
    pinned=center(page);assert pinned['reading']=='pinned' and pinned['action']=='collapse-pinned-and-scroll'
    assert pinned['contentWidth']==s['contentWidth'],(pinned,s)
    page.screenshot(path=str(r.out/'desktop-pinned-region.png'))
    page.keyboard.down('Control')
    page.wait_for_function('JSON.parse(document.querySelector(".ar-card-region-debug").dataset.snapshot).owner==="browser"')
    browser=snapshot(page);page.keyboard.up('Control')
    button.focus();page.keyboard.press('Enter');page.wait_for_timeout(400)
    # A quiet genuine hover must not turn logical width into projected width.
    page.mouse.move(24,300);page.wait_for_timeout(350)
    card=page.locator('.ar-tool-card').first.bounding_box()
    move(page,card['x']+90,card['y']+95,'cards')
    page.wait_for_function('document.querySelector(".ar-tools-browser").dataset.detailMode==="preview"')
    page.wait_for_timeout(400)
    hovered=snapshot(page);assert hovered['contentWidth']==s['contentWidth']
    filter_box=page.locator('button[data-category=G6]').bounding_box()
    outside=move(page,filter_box['x']+10,filter_box['y']+10,'page')
    nav=page.locator('.tour-stops').bounding_box()
    move(page,nav['x']+15,nav['y']+15,'page')
    category(page,'G3');small=center(page,'page');assert not small['overflow'] and small['reason']=='all-cards-visible'
    category(page,'G6');center(page)
    page.locator('[data-action=help]').click();page.wait_for_timeout(150)
    help_box=page.locator('.ar-tool-help-panel').bounding_box()
    help_state=move(page,help_box['x']+40,help_box['y']+45,'overlay')
    page.locator('[data-action=help-close]').click()
    page.locator('[data-action=all]').click()
    page.wait_for_function('document.querySelector(".ar-overview-dialog").open')
    move(page,30,300,'overlay');modal=snapshot(page)
    assert modal['mode']=='all'
    page.keyboard.press('Escape');page.wait_for_function('!document.querySelector(".ar-overview-dialog").open')
    center(page)
    r.go(page,'B1');page.mouse.move(30,300)
    page.wait_for_function('JSON.parse(document.querySelector(".ar-card-region-debug").dataset.snapshot).active===false')
    assert snapshot(page)['owner']=='page'
    return {'region':s,'blankAndGapPoints':points,'pinned':pinned,'hover':hovered,'browserGesture':browser,'filterExcluded':outside,'fittingCategory':small,'help':help_state,'modal':modal,'hidden':snapshot(page)}

def responsive(page):
    debug(page);r.stable(page);enter(page);category(page,'G6');page.locator('.ar-tool-rail').scroll_into_view_if_needed();page.wait_for_timeout(400)
    initial=center(page)
    page.set_viewport_size({'width':1100,'height':850});page.wait_for_timeout(600)
    page.locator('.ar-tool-rail').scroll_into_view_if_needed();page.wait_for_timeout(200)
    resized=center(page);assert resized['layout']=='stable' and resized['overflow']
    page.evaluate('document.documentElement.style.fontSize="200%"');page.wait_for_timeout(800)
    page.locator('.ar-tool-rail').scroll_into_view_if_needed();page.wait_for_timeout(300)
    enlarged=center(page);assert enlarged['contentWidth']>resized['contentWidth']*1.5
    page.screenshot(path=str(r.out/'stable-large-text-region.png'))
    return {'stable':initial,'resized':resized,'font200Simulation':enlarged}

def mobile(page):
    debug(page);enter(page);category(page,'G6');page.locator('.ar-tool-rail').scroll_into_view_if_needed();page.wait_for_timeout(450)
    # Mouse inspection is only a read-only coordinate diagnostic in touch mode.
    s=center(page);assert s['layout']=='stable' and s['overflow']
    rail=page.locator('.ar-tool-rail');box=rail.bounding_box();before=rail.evaluate('e=>e.scrollLeft');y=box['y']+min(130,box['height']/2)
    x=min(box['x']+box['width']-50,330)
    session=page.context.new_cdp_session(page)
    session.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]})
    for i in range(1,9):
        session.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x-i*18,'y':y}]});page.wait_for_timeout(25)
    session.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});page.wait_for_timeout(700)
    after=rail.evaluate('e=>e.scrollLeft');assert after>before+20,(before,after)
    start_y=page.evaluate('scrollY')
    session.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':7,'y':550}]})
    for i in range(1,8):
        session.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':7,'y':550-i*20}]});page.wait_for_timeout(25)
    session.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});page.wait_for_timeout(500)
    end_y=page.evaluate('scrollY');assert end_y>start_y+20,(start_y,end_y)
    return {'region':s,'nativeHorizontalTouch':[before,after],'nativeVerticalTouch':[start_y,end_y],'touchSimulation':True}

def selection(page):
    debug(page);enter(page);category(page,'G6');page.mouse.move(24,300)
    button=page.locator('.ar-tool-card button').first;button.focus();page.keyboard.press('Enter')
    page.wait_for_function('document.querySelector(".ar-tools-browser").dataset.detailMode==="pinned"&&document.querySelector(".ar-tools-browser").dataset.hoverState==="reading"')
    box=page.locator('.ar-tool-card .ar-card-detail').first.bounding_box();assert box
    page.mouse.move(box['x']+6,box['y']+10);page.mouse.down()
    page.mouse.move(box['x']+min(160,box['width']-10),box['y']+10,steps=12);page.mouse.up()
    text=page.evaluate('getSelection()?.toString()??""');assert len(text.strip())>=2,text
    page.keyboard.press('Tab');state=r.state(page)
    assert not state['focus']['hidden']
    assert not page.evaluate('document.querySelector(".ar-card-region-debug").contains(document.activeElement)')
    return {'nativeSelectedText':text,'focusAfterNativeTab':state['focus'],'debugInert':page.locator('.ar-card-region-debug').evaluate('e=>e.inert&&getComputedStyle(e).pointerEvents==="none"')}

try:
    r.case('native-selection-and-keyboard',selection,size=(1652,949))
    r.case('normal-page-unchanged',normal,size=(1652,949))
    r.case('desktop-region-and-ownership',desktop,size=(1652,949))
    r.case('stable-resize-and-large-text',responsive)
    r.case('native-mobile-gestures',mobile,size=(390,844),touch=True)
finally:good=r.finish()
raise SystemExit(0 if good else 1)
