"""Step2 browser helpers: actual DOM/canvas screenshots and background RGBA.

The alpha isolation hides the scene/text only. It never changes the target
pseudo-element's mask, geometry, opacity or color. Full unaltered page images
are captured separately. No historical output directory is written.
"""
from pathlib import Path
from io import BytesIO
from functools import lru_cache
import json
import math
import sys
from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tests/scroll-garden'))
from step11_common import launch, ready, go, frames, data, PROBE, STOPS, VIEWS

def save(out, name, value):
    (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def visit(page, h):
    page.bring_to_front()
    go(page, h)
    frames(page)

def load(page, url):
    page.bring_to_front()
    ready(page, url)
    page.wait_for_function('document.querySelector("main").dataset.layoutReady==="true"')
    frames(page)

def about(page):
    return page.locator('.pillar-reading').evaluate('''e=>{
      const s=getComputedStyle(e,'::before'),r=e.getBoundingClientRect();
      const left=r.left+parseFloat(s.left),top=r.top+parseFloat(s.top);
      return{panel:r.toJSON(),background:{left,top,width:parseFloat(s.width),height:parseFloat(s.height),right:left+parseFloat(s.width),bottom:top+parseFloat(s.height)},
        mask:s.maskImage,composite:s.maskComposite,opacity:s.opacity,color:s.backgroundColor,
        radius:s.borderRadius,shadow:s.boxShadow,filter:s.filter,pointer:s.pointerEvents,
        feather:parseFloat(getComputedStyle(e).getPropertyValue('--veil-feather'))||null,
        state:{...e.dataset},text:e.textContent,visibleArticle:e.querySelector('article[aria-hidden=false]')?.dataset.readingStation};}''')

def glyphs(page):
    return page.locator('.pillar-reading article[aria-hidden=false]').evaluate('''e=>{
      const w=document.createTreeWalker(e,NodeFilter.SHOW_TEXT),result=[];let n;
      while(n=w.nextNode()){
        const p=n.parentElement,s=getComputedStyle(p);if(s.visibility!=='visible')continue;
        let i=0;for(const char of n.textContent){const size=char.length;if(/\\s/.test(char)){i+=size;continue;}
          const range=document.createRange();range.setStart(n,i);range.setEnd(n,i+size);i+=size;
          for(const r of range.getClientRects())if(r.width>0&&r.height>0)result.push({char,rect:r.toJSON(),color:s.color});}
      }return result;}''')

def luminance(rgb):
    values = [x / 255 for x in rgb]
    linear = [x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4 for x in values]
    return sum(v * k for v, k in zip(linear, [.2126, .7152, .0722]))

@lru_cache(maxsize=8192)
def white_composite_luminance(pixel):
    r, g, b, a = pixel
    return luminance([c * a / 255 + 255 * (1 - a / 255) for c in [r, g, b]])

@lru_cache(maxsize=8192)
def rgb_luminance(pixel):
    return luminance(pixel)

def background_measurement(page, out, filename, check=False):
    before = about(page)
    letters = glyphs(page)
    rect = before['background']
    vw, vh = page.viewport_size['width'], page.viewport_size['height']
    assert rect['left'] >= 0 and rect['top'] >= 0 and rect['right'] <= vw and rect['bottom'] <= vh, rect
    clip = {'x': max(0, math.floor(rect['left']) - 4), 'y': max(0, math.floor(rect['top']) - 4)}
    clip['width'] = min(vw, math.ceil(rect['right']) + 4) - clip['x']
    clip['height'] = min(vh, math.ceil(rect['bottom']) + 4) - clip['y']
    style = page.add_style_tag(content='''
      html,body,#app,main{background:transparent!important}
      #app *:not(.pillar-reading){visibility:hidden!important}
    ''')
    frames(page)
    isolated = about(page)
    assert isolated == before, 'Isolation changed target background properties.'
    white_image = None
    matte_files = []
    if page.context.browser.browser_type.name == 'firefox':
        # This Firefox screenshot backend returns "Not implemented" for
        # omit_background. Recover alpha from two actual opaque composites:
        # white - black = 255 * (1-alpha), with at most 1-level rounding.
        matte = page.add_style_tag(content='html{background:#000!important}')
        frames(page)
        black_raw = page.screenshot(clip=clip)
        black_file = filename.removesuffix('.png') + '-black.png'
        (out / black_file).write_bytes(black_raw)
        matte.evaluate('e=>e.textContent="html{background:#fff!important}"')
        frames(page)
        white_raw = page.screenshot(clip=clip)
        white_file = filename.removesuffix('.png') + '-white.png'
        (out / white_file).write_bytes(white_raw)
        matte.evaluate('e=>e.remove()')
        image = Image.open(BytesIO(black_raw)).convert('RGB')
        white_image = Image.open(BytesIO(white_raw)).convert('RGB')
        channels = ImageChops.subtract(white_image, image).split()
        low, high = ImageChops.darker(channels[0], channels[1]), ImageChops.lighter(channels[0], channels[1])
        median = ImageChops.lighter(low, ImageChops.darker(high, channels[2]))
        alpha = ImageChops.invert(median)
        matte_files = [black_file, white_file]
        capture_method = 'two actual black/white backdrop renders; alpha=255-median(white-black); original target styles preserved; raw renders saved; derived numeric alpha only'
    else:
        raw = page.screenshot(omit_background=True, clip=clip)
        (out / filename).write_bytes(raw)
        image = Image.open(BytesIO(raw)).convert('RGBA')
        alpha = image.getchannel('A')
        capture_method = 'actual transparent PNG from browser'
    style.evaluate('e=>e.remove()')
    frames(page)
    assert about(page) == before, 'Isolation was not fully removed.'
    dpr = page.evaluate('devicePixelRatio')
    x0 = math.ceil((rect['left'] - clip['x']) * dpr)
    y0 = math.ceil((rect['top'] - clip['y']) * dpr)
    x1 = math.floor((rect['right'] - clip['x']) * dpr)
    y1 = math.floor((rect['bottom'] - clip['y']) * dpr)
    band = max(1, int(dpr))
    edges = {'left': alpha.crop((x0, y0, x0 + band, y1)).getextrema()[1],
        'right': alpha.crop((x1 - band, y0, x1, y1)).getextrema()[1],
        'top': alpha.crop((x0, y0, x1, y0 + band)).getextrema()[1],
        'bottom': alpha.crop((x0, y1 - band, x1, y1)).getextrema()[1]}
    count = math.ceil((before['feather'] or 36) * dpr) + 2
    mx, my = (x0 + x1) // 2, (y0 + y1) // 2
    profiles = {'left': [alpha.getpixel((x0 + i, my)) for i in range(count)],
        'right': [alpha.getpixel((x1 - 1 - i, my)) for i in range(count)],
        'top': [alpha.getpixel((mx, y0 + i)) for i in range(count)],
        'bottom': [alpha.getpixel((mx, y1 - 1 - i)) for i in range(count)]}
    monotonic = all(all(a <= b + 1 for a, b in zip(v, v[1:])) for v in profiles.values())
    ratios = []
    for letter in letters:
        box = letter['rect']
        region = (max(0, math.floor((box['left'] - clip['x']) * dpr)),
            max(0, math.floor((box['top'] - clip['y']) * dpr)),
            min(image.width, math.ceil((box['right'] - clip['x']) * dpr)),
            min(image.height, math.ceil((box['bottom'] - clip['y']) * dpr)))
        assert region[2] > region[0] and region[3] > region[1], (letter, region)
        if white_image is None:
            worst_bg = max(white_composite_luminance(p) for p in image.crop(region).getdata())
        else:
            worst_bg = max(rgb_luminance(p) for p in white_image.crop(region).getdata())
        color = [float(x) for x in letter['color'].replace('rgba(', '').replace('rgb(', '').rstrip(')').replace(',', ' ').split()[:3]]
        ratio = (luminance(color) + .05) / (worst_bg + .05)
        ratios.append({'ratio': ratio, 'character': letter['char'], 'color': letter['color'], 'rect': box})
    assert ratios
    worst = min(ratios, key=lambda x: x['ratio'])
    result = {'actualPseudo': before, 'DPR': dpr, 'CSSClip': clip, 'physicalImageSize': list(image.size),
        'outerOneCssPixelAlpha': edges, 'profilesAlpha': profiles, 'profilesMonotonicWithinOneLevel': monotonic,
        'peakAlpha': alpha.getextrema()[1], 'glyphsMeasured': len(ratios), 'minimumContrastOverWhite': worst,
        'contrastMethod': 'Actual rendered RGBA below every visible character range, composited over worst-case white; foreground computed CSS color; conservative lower bound for actual lighter/darker scene; text shadows ignored.',
        'captureMethod': capture_method, 'rawAlphaScreenshot': filename if not matte_files else None,
        'rawMatteScreenshots': matte_files, 'isolationPreservesActualMaskColorOpacityGeometry': True}
    if check:
        assert max(edges.values()) <= 1, edges
        assert monotonic, profiles
        assert worst['ratio'] >= 4.5, worst
        assert alpha.getextrema()[1] <= 231 and all(v[-1] >= 227 for v in profiles.values())
        assert before['pointer'] == 'none' and before['shadow'] == 'none' and before['filter'] == 'none'
    return result

PURE_CSS = '.tour-header,.tour-heading,.tour-stops,.tour-footer,.pillar-reading,.film-reading,.experiment-reading,.pillar-reading-link,.film-reading-link,.experiment-reading-link,.tour-flow-intro,.tour-flow-label,.tour-flow-water,.tour-flow-ending,.tour-skip{visibility:hidden!important}'

def pure_canvas(page):
    page.bring_to_front()
    style = page.add_style_tag(content=PURE_CSS)
    frames(page)
    raw = page.locator('canvas').screenshot()
    style.evaluate('e=>e.remove()')
    frames(page)
    return raw

def pixels_equal(a, b):
    return ImageChops.difference(Image.open(BytesIO(a)).convert('RGB'), Image.open(BytesIO(b)).convert('RGB')).getbbox() is None
