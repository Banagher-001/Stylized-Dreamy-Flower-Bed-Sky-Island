"""Run only against independently extracted delivery archives."""
from support import Run, save
import hashlib,struct
r=Run()

def journey(page):
    first=r.state(page)
    assert first['host']['renderState']=='ready'
    r.stable(page);r.go(page,'A1')
    assert '枫叶互动' in page.locator('.ar-screen[data-about-station=A1]').inner_text()
    r.go(page,'A3')
    assert len(r.state(page)['cards'])==22
    page.locator('.ar-tool-card[data-tool-id=midjourney] button').click()
    assert r.state(page)['tools']['readingId']=='midjourney'
    r.checkpoint(page,'cards')
    r.go(page,'B1')
    page.locator('[data-film-station=B1] .film-image-button').first.click()
    page.wait_for_function('document.querySelector(".film-dialog").dataset.state==="ready"')
    assert '非个人实际项目' in page.locator('.film-dialog').inner_text()
    page.locator('.film-dialog-close').click()
    page.wait_for_function('!document.querySelector(".film-dialog").open&&!document.querySelector(".film-dialog-viewport img")')
    rows=[]
    for identifier in ['lawson','bottle-ocean']:
        frame=r.open_scene(page,identifier)
        assert frame.url==r.origin+'experiments/'+identifier+'/index.html'
        if identifier=='lawson':
            frame.locator('#btn-help').click()
            assert frame.locator('#help').is_visible()
            frame.locator('#help-close').click()
            native={'controls':frame.locator('button,input,.toggle').count(),'ready':frame.evaluate('__LAWSON__.ready')}
            assert native['controls']==41
        else:
            frame.locator('[data-quality=retro]').click()
            frame.locator('[data-action=pause]').click()
            assert frame.evaluate('__bottleOcean.state.paused')
            with page.expect_download(timeout=30000) as event:
                frame.locator('[data-action=screenshot]').click()
            d=event.value;path=r.out/'portable-native-export.png';d.save_as(str(path));raw=path.read_bytes()
            assert raw[:8]==b'\x89PNG\r\n\x1a\n' and not d.failure() and len(raw)>10000
            native={'controls':frame.locator('button,input').count(),'ready':frame.evaluate('__bottleOcean.ready'),'download':{'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'PNG':list(struct.unpack('>II',raw[16:24]))}}
            assert native['controls']==34
        r.checkpoint(page,identifier)
        r.go(page,'water')
        page.wait_for_function('!document.querySelector(".experiment-window-stage iframe")')
        assert not page.locator('iframe').count()
        rows.append({'id':identifier,'native':native})
    r.go(page,'ending')
    return {'normalEntry':first['url'],'projects':rows,'returned':r.state(page),'originalWorkspaceFallback':False}
try:
    r.case('independent-package-root-or-prefix',journey)
finally:
    good=r.finish()
raise SystemExit(0 if good else 1)
