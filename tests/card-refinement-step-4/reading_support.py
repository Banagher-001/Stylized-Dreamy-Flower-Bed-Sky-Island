"""Main-page interactions and real geometry for the card reading checks."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tests/card-refinement-step-3'))
from observe import DESKTOP, Run, choose, enter_paused, points, snapshot, wait_ready


def ready_automatic(r, page):
    r.go(page, 'A3')
    page.wait_for_function('''() => {
      const t = document.querySelector('.ar-tools-browser').dataset;
      return t.entranceReason === 'completed' && t.trackMode === 'program' && Number(t.trackSpeed) > 20;
    }''')


def tool_state(page):
    return page.locator('.ar-tools-browser').evaluate('''r => ({ ...r.dataset,
      x: r.querySelector('.ar-tool-rail').scrollLeft, y: scrollY,
      camera: document.querySelector('#tour-host').dataset.targetH,
      focus: document.activeElement?.closest('.ar-tool-card')?.dataset.toolId ?? null,
      reading: [...r.querySelectorAll('[data-reading="true"]')].map(e => e.dataset.toolId)
    })''')


def visible_cards(page):
    return page.evaluate('''() => {
      const rail = document.querySelector('.ar-tool-rail');
      const bounds = rail.getBoundingClientRect();
      return [...rail.querySelectorAll('.ar-tool-card')].filter(e=>!e.inert).map(e=>({ id:e.dataset.toolId,
        b:e.querySelector('.ar-card-front').getBoundingClientRect() })).filter(({b})=>b.width>75 && b.left>bounds.left+16 && b.right<bounds.right-16)
        .sort((a,b)=>a.b.left-b.b.left).map(({id,b})=>({id,point:[b.left+b.width*.53,b.top+b.height*.34]}));
    }''')


def hover_card(page, card=None, phase='reading'):
    card = card or visible_cards(page)[1]
    page.mouse.move(*card['point'])
    page.wait_for_function('''([id,phase]) => {
      const t = document.querySelector('.ar-tools-browser').dataset;
      return t.hoverId === id && t.detailMode === 'preview' && (phase === 'either' || t.hoverState === phase);
    }''', arg=[card['id'],phase], timeout=5000)
    return card['id']


def detail_button(page, card_id):
    return page.locator(f'.ar-tool-rail [data-tool-id="{card_id}"] button[data-action="detail"]')


def midpoint(locator):
    box = locator.bounding_box()
    assert box, 'Button has no box'
    return (box['x']+box['width']/2, box['y']+box['height']/2)
