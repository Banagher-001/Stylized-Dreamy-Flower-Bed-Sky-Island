"""Read the real tour and replay native page and card input."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tests/card-refinement-step-4'))
from reading_support import (DESKTOP, Run, choose, detail_button, enter_paused, hover_card,
                             midpoint, points, ready_automatic, snapshot, tool_state)


def phase(page, value, timeout=6000):
    page.wait_for_function('v=>document.querySelector(".ar-tools-browser").dataset.departure===v', arg=value, timeout=timeout)


def progress(page, position, wait=True):
    h = 2.9 + .8*position
    delta = page.evaluate('h=>h/12.3*(document.documentElement.scrollHeight-innerHeight)-scrollY', h)
    page.mouse.move(24, 300)
    page.mouse.wheel(0, delta)
    if wait:
        page.wait_for_function('h=>Math.abs(Number(document.querySelector("#tour-host").dataset.displayH)-h)<.005', arg=h, timeout=6500)
    return delta


def paused_overflow(page):
    return page.locator('.ar-tool-rail').evaluate('e=>e.scrollWidth-e.clientWidth')
