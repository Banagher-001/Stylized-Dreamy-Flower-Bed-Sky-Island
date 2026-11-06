"""Isolated real decoder tests of the same viewer component; not portfolio media."""
from pathlib import Path
from io import BytesIO
import argparse,json,os
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/evidence/scroll-garden-step-6'
parser=argparse.ArgumentParser();parser.add_argument('--engine',choices=['chromium','firefox','webkit'],default='chromium');args=parser.parse_args()
checks=[];errors=[];diagnostics=[]
def record(name,evidence):checks.append({'check':name,'passed':True,'evidence':evidence});print(args.engine+': '+name,flush=True)
with sync_playwright() as p:
 options={'headless':args.engine=='chromium'}
 if args.engine=='chromium':options.update(executable_path='/usr/bin/chromium',args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 if args.engine=='firefox':options['firefox_user_prefs']={'webgl.force-enabled':True}
 if args.engine=='webkit'and os.environ.get('COURTYARD_WEBKIT_EXECUTABLE'):options['executable_path']=os.environ['COURTYARD_WEBKIT_EXECUTABLE']
 b=getattr(p,args.engine).launch(**options);page=b.new_page(viewport={'width':1280,'height':800});page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:diagnostics.append({'type':m.type,'text':m.text})if m.type in ['warning','error']else None)
 page.goto('http://127.0.0.1:5173/tests/scroll-garden/media-fixture.html',wait_until='networkidle');page.wait_for_selector('body[data-fixture-ready=true]');baseline=page.locator('*').count()
 page.locator('#fixture-open').click();page.wait_for_selector('.film-dialog[open][data-state=ready]');page.wait_for_function('()=>{const v=document.querySelector("video");return v&&!v.paused&&v.currentTime>.15&&v.videoWidth===680}')
 quality=page.locator('video').evaluate('v=>({time:v.currentTime,width:v.videoWidth,height:v.videoHeight,duration:v.duration,frames:v.getVideoPlaybackQuality?.().totalVideoFrames??v.webkitDecodedFrameCount,loop:v.loop,inline:v.playsInline})');assert quality['duration']==12 and quality['frames']>0 and not quality['loop']and quality['inline']
 a=Image.open(BytesIO(page.locator('video').screenshot())).convert('RGB');page.wait_for_timeout(700);c=Image.open(BytesIO(page.locator('video').screenshot())).convert('RGB');assert ImageChops.difference(a,c).getbbox()is not None
 page.screenshot(path=str(OUT/f'fixture-{args.engine}-playing.png'));record('actual native playback decodes changing frames from the labelled local test clip',quality)
 page.evaluate('window.lastFixtureVideo=document.querySelector("video")');page.keyboard.press('Escape');page.wait_for_function('!document.querySelector("dialog").open&&document.querySelectorAll("video").length===0');assert page.evaluate('window.lastFixtureVideo.paused&&window.lastFixtureVideo.getAttribute("src")===null&&!window.lastFixtureVideo.isConnected');assert page.locator('#fixture-open').evaluate('e=>document.activeElement===e')
 record('close releases the decoder source, removes video and restores focus',{'paused':True,'sourceRemoved':True,'videoRemoved':True,'focusRestored':True})
 page.locator('#fixture-rapid').click();page.wait_for_selector('.film-dialog[open][data-state=ready]');page.wait_for_function('document.querySelector("video").currentTime>.05');assert page.locator('video').count()==1 and page.evaluate('window.mediaFixture.counts.open-window.mediaFixture.counts.close')==1
 page.evaluate('window.lastFixtureVideo=document.querySelector("video");window.mediaFixture.viewer.open(window.mediaFixture.picture)');page.wait_for_selector('.film-dialog[open][data-state=ready]');assert page.locator('video').count()==0 and page.locator('.film-dialog img').count()==1 and page.evaluate('window.lastFixtureVideo.paused&&window.lastFixtureVideo.getAttribute("src")===null')
 page.keyboard.press('Escape');page.wait_for_function('!document.querySelector("dialog").open');record('queued close and rapid reopen keep a single decoder and switching releases old media',{'balancedCallbacks':True,'singleVideo':True,'imageSwitchPass':True})
 page.locator('#fixture-error').click();page.wait_for_selector('.film-dialog[open][data-state=error]');assert page.get_by_role('button',name='重新载入',exact=True).is_visible();page.screenshot(path=str(OUT/f'fixture-{args.engine}-error.png'))
 page.evaluate('window.mediaFixture.bad.src=window.mediaFixture.clip.src');page.get_by_role('button',name='重新载入',exact=True).click();page.wait_for_selector('.film-dialog[open][data-state=ready]');assert page.locator('video').evaluate('v=>v.paused');page.get_by_role('button',name='关闭放映',exact=True).click();page.wait_for_function('!document.querySelector("dialog").open&&document.querySelectorAll("video").length===0')
 record('failed video exposes retry and close, and retry loads without unexpected playback',{'errorReadable':True,'retryLoaded':True,'retryPaused':True})
 for _ in range(10):
  page.locator('#fixture-open').click();page.wait_for_selector('.film-dialog[open][data-state=ready]');page.keyboard.press('Escape');page.wait_for_function('!document.querySelector("dialog").open&&document.querySelectorAll("video").length===0')
 assert page.locator('*').count()==baseline and page.evaluate('window.mediaFixture.counts.open===window.mediaFixture.counts.close')and not errors
 record('ten playback cycles retain closed DOM size with balanced lifecycle callbacks',{'cycles':10,'closedNodes':baseline,'activeVideos':0,'unhandledExceptions':errors})
 (OUT/f'player-{args.engine}.json').write_text(json.dumps({'engine':args.engine,'version':b.version,'mechanismOnly':True,'realFilmIntegrated':False,'fixture':'12-second silent courtyard scene, not an AI animation project','checks':checks,'unhandledExceptions':errors,'expectedMissingMediaDiagnostics':diagnostics,'passed':True},ensure_ascii=False,indent=2)+'\n');b.close()
