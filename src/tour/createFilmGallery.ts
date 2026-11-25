import { createWheelGesture, normalizeCardWheel } from './about-refresh/cardWheelInput';
import { workLabel } from './filmContent';
import type { FilmSliceItem } from './filmContent';

type Side = -1 | 1;
type View = 'full' | 'near' | 'detail';
type Phase = 'waiting' | 'entering' | 'settled' | 'switching' | 'scrubbing' | 'leaving';
const clamp = (value: number, min: number, max: number) => Math.max(min, Math.min(max, value));
const pose = (x: number, y: number, z: number, yaw: number, roll: number) =>
  `translate3d(${x}%, ${y}px, ${z}px) rotateY(${yaw}deg) rotateZ(${roll}deg)`;
const front = pose(0, 0, 0, 0, 0);
const viewNames = new Map<View, string>([['full', '全景'], ['near', '局部'], ['detail', '细节']]);

export function createFilmGallery(
  article: HTMLElement, items: readonly [FilmSliceItem, ...FilmSliceItem[]], openImage: (index: number, trigger: HTMLElement) => void,
  onSettle: () => void,
) {
  const body = article.querySelector<HTMLElement>('.film-body')!;
  body.innerHTML = `
    <div class="film-media film-slice-media" data-slice-phase="waiting" data-slice-multiple="${items.length > 1}">
      <button type="button" class="film-image-button film-slice-button" id="film-slice-current" aria-haspopup="dialog" data-reader-managed disabled>
        <span class="film-slice-viewport" aria-hidden="true"></span>
      </button>
    </div>
    <div class="film-slice-meta" data-film-ink>
      <div><p class="film-slice-title"></p><p class="film-provenance"></p></div>
      <div class="film-slice-buttons film-slice-views" role="group" aria-label="选择图片取景" data-reader-managed>
        ${[...viewNames].map(([id, name]) => `<button type="button" data-film-slice-view="${id}" aria-controls="film-slice-current" aria-pressed="false">${name}</button>`).join('')}
      </div>
    </div>
    <div class="film-slice-navigation" data-film-ink>
      <div class="film-slice-buttons" role="group" aria-label="图集播放" data-reader-managed>
        <button type="button" data-film-slice-control="previous" disabled>上一张</button>
        <button type="button" data-film-slice-control="play" aria-label="自动播放" disabled>播放</button>
        <button type="button" data-film-slice-control="next" disabled>下一张</button>
      </div>
      <p class="film-slice-hint">${items.length > 1 ? '<span class="film-slice-wheel-hint">图上滚轮切图 · </span><span class="film-slice-touch-hint">左右滑动切图 · </span>' : ''}点图放大</p>
    </div>
    ${items.some(({ work }) => work.responsibilities?.length) ? '<p class="film-caption" data-film-ink data-reader-managed></p>' : ''}`;
  const media = body.querySelector<HTMLElement>('.film-slice-media')!;
  const button = media.querySelector<HTMLButtonElement>('.film-slice-button')!;
  const viewport = media.querySelector<HTMLElement>('.film-slice-viewport')!;
  const countLabel = article.querySelector<HTMLElement>('.film-slice-count')!;
  const title = body.querySelector<HTMLElement>('.film-slice-title')!;
  const provenance = body.querySelector<HTMLElement>('.film-provenance')!;
  const responsibilities = body.querySelector<HTMLElement>('.film-caption');
  const views = body.querySelector<HTMLElement>('.film-slice-views')!;
  const viewButtons = [...views.querySelectorAll<HTMLButtonElement>('button')];
  const back = body.querySelector<HTMLButtonElement>('[data-film-slice-control="previous"]')!;
  const play = body.querySelector<HTMLButtonElement>('[data-film-slice-control="play"]')!;
  const next = body.querySelector<HTMLButtonElement>('[data-film-slice-control="next"]')!;
  const main = article.closest('main')!;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const listeners = new AbortController();
  const options = { signal: listeners.signal };
  const gesture = createWheelGesture();
  const cards = items.map(({ work, framedViews }) => {
    const plane = document.createElement('span');
    plane.className = 'film-slice-card';
    plane.dataset.sliceWork = work.id;
    plane.dataset.sliceView = 'full';
    plane.hidden = true;
    plane.innerHTML = '<span class="film-slice-frame"><img decoding="async" draggable="false"></span><span class="film-image-placeholder">载入中</span><span class="film-view-mark">↗</span>';
    const image = plane.querySelector('img')!;
    image.alt = work.image.alt;image.width = work.image.width;image.height = work.image.height;
    viewport.append(plane);
    return { work, framedViews, plane, image };
  });

  const total = cards.length;
  const last = total - 1;
  const multiple = total > 1;
  const wrap = (position: number) => position % total;
  const visible = new Set<number>();
  let current = 0, position = 0;
  let exposed = false, flow = false, covered = false, hovered = false;
  let requestedPlay: boolean | undefined;
  let phase: Phase = 'waiting', entrySide: Side = 1;
  let flight: Animation | undefined, exit: HTMLElement | undefined;
  let timer: number | undefined, frame: number | undefined;
  let tween: { from: number; to: number; started: number; duration: number; automatic: boolean } | undefined;
  let scrub: { aim: number; lastInput: number } | undefined;
  let lastFrame = 0, lastWheel = -Infinity, ownsWheel = false;
  let swipe: { id: number; x: number; y: number; start?: number } | undefined;
  let suppressClickUntil = 0;
  const wantsPlay = () => multiple && (requestedPlay ?? !reduced.matches);
  const canBrowse = () => exposed && !covered;

  function prepare(index: number) {
    const { image, plane, work } = cards[index]!;
    if (image.hasAttribute('src')) return;
    image.src = work.image.src;
    void image.decode().then(() => { plane.dataset.imageState = 'ready'; }, () => {
      plane.dataset.imageState = 'error';
      plane.querySelector<HTMLElement>('.film-image-placeholder')!.textContent = '载入失败';
    }).finally(() => { if (!listeners.signal.aborted && index === current) onSettle(); });
  }

  function controls() {
    const disabled = !exposed && !flow;
    button.disabled = disabled;
    button.setAttribute('aria-disabled', String(!canBrowse() || phase !== 'settled'));
    back.disabled = play.disabled = next.disabled = disabled || !multiple;
    back.setAttribute('aria-disabled', String(!canBrowse() || !multiple || current === 0));
    next.setAttribute('aria-disabled', String(!canBrowse() || !multiple || current === last));
    play.setAttribute('aria-disabled', String(!canBrowse() || !multiple));
    const playLabel = wantsPlay() ? '暂停' : '播放';
    if (play.textContent !== playLabel) play.textContent = playLabel;
    play.setAttribute('aria-pressed', String(wantsPlay()));
    const card = cards[current]!;
    views.setAttribute('aria-hidden', String(!card.framedViews));
    for (const control of viewButtons) {
      control.disabled = disabled || !card.framedViews;
      control.setAttribute('aria-pressed', String(control.dataset.filmSliceView === card.plane.dataset.sliceView));
    }
  }

  function select(index: number) {
    current = wrap(index);
    const { work } = cards[current]!;
    const count = (number: number) => String(number).padStart(2, '0');
    countLabel.textContent = `${count(current + 1)} / ${count(total)}`;
    countLabel.setAttribute('aria-label', `第 ${current + 1} 张，共 ${total} 张`);
    title.textContent = work.title;title.title = work.title;
    provenance.textContent = workLabel(work);
    button.setAttribute('aria-label', `查看《${work.title}》完整画面，${workLabel(work)}`);
    if (responsibilities) {
      const description = work.responsibilities?.join(' / ') ?? '';
      if (responsibilities.textContent !== description) responsibilities.textContent = description;
      responsibilities.hidden = !description;
    }
  }

  function setPhase(nextPhase: Phase) {
    if (phase === nextPhase) return;
    phase = nextPhase;
    media.dataset.slicePhase = phase;
    controls();
  }

  function draw(value: number) {
    position = value;
    const left = Math.floor(value);
    const positions = Math.abs(left - value) < .0001 ? [left] : [left, left + 1];
    const keep = new Set(positions.map(wrap));
    for (const index of visible) if (!keep.has(index)) {
      cards[index]!.plane.hidden = true;
      visible.delete(index);
    }
    for (const slot of positions) {
      const index = wrap(slot), { plane } = cards[index]!;
      const offset = slot - value, distance = Math.abs(offset);
      if (!visible.has(index)) { prepare(index);plane.hidden = false;visible.add(index); }
      plane.style.transform = distance < .0001 ? 'none' : pose(106 * offset, 7 * distance, -84 * distance, -17 * offset, 3 * offset);
    }
  }

  function schedulePlay() {
    clearTimeout(timer);timer = undefined;
    if (!canBrowse() || !wantsPlay() || phase !== 'settled' || hovered || document.hidden) return;
    timer = window.setTimeout(() => {
      timer = undefined;
      moveTo(current + 1, 400, true);
    }, 6000);
  }

  function stopTrack() {
    if (frame !== undefined) cancelAnimationFrame(frame);
    frame = undefined;tween = undefined;scrub = undefined;lastFrame = 0;
  }

  function land(index: number) {
    stopTrack();
    if (current !== wrap(index)) select(index);
    draw(current);
    if (multiple) {
      prepare(wrap(current + 1));
      if (current > 0) prepare(current - 1);
    }
    setPhase('settled');
    schedulePlay();onSettle();
  }

  function track(now: number) {
    frame = undefined;
    const elapsed = lastFrame ? clamp(now - lastFrame, 0, 48) : 16;
    lastFrame = now;
    if (scrub) {
      if (now - scrub.lastInput >= 100) {
        moveTo(Math.round(scrub.aim), 255);
        return;
      }
      if (!reduced.matches) draw(position + (scrub.aim - position) * (1 - Math.exp(-elapsed / 52)));
    } else if (tween) {
      const time = clamp((now - tween.started) / tween.duration, 0, 1);
      if (time === 1) { land(tween.to);return; }
      const eased = 1 - (1 - time) ** 3;
      draw(tween.from + (tween.to - tween.from) * eased);
    }
    queueTrack();
  }

  function queueTrack() {
    if (frame === undefined && (scrub || tween)) frame = requestAnimationFrame(track);
  }

  function moveTo(to: number, duration: number, automatic = false) {
    clearTimeout(timer);timer = undefined;stopTrack();
    if (reduced.matches || Math.abs(to - position) < .001) { land(to);return; }
    tween = { from: position, to, started: performance.now(), duration, automatic };
    setPhase('switching');
    queueTrack();
  }

  function finishEntry() {
    flight?.cancel();flight = undefined;
    land(current);
  }

  function enter(side: Side) {
    exit?.remove();exit = undefined;
    exposed = true;
    draw(current);
    if (reduced.matches) { finishEntry();return; }
    setPhase('entering');
    flight = cards[current]!.plane.animate([
      { transform: pose(109 * side, 25, -152, -38 * side, 7 * side), opacity: .82, offset: 0 },
      { transform: pose(64 * side, 14, -112, -30 * side, 5 * side), opacity: 1, offset: .31 },
      { transform: pose(25 * side, 3, -63, -18 * side, 3 * side), opacity: 1, offset: .59 },
      { transform: pose(5 * side, -2, -19, -6 * side, 1 * side), opacity: 1, offset: .82 },
      { transform: front, opacity: 1, offset: 1 },
    ], { duration: 650, easing: 'linear' });
    flight.onfinish = finishEntry;
  }

  function clearWheel() {
    gesture.clear();lastWheel = -Infinity;ownsWheel = false;
  }

  function clearActivity() {
    clearTimeout(timer);timer = undefined;
    flight?.cancel();flight = undefined;
    stopTrack();clearWheel();swipe = undefined;
    for (const index of visible) cards[index]!.plane.hidden = true;
    visible.clear();position = current;
  }

  function leave(side: Side) {
    exposed = false;
    const card = cards[wrap(Math.round(position))]!.plane;
    const box = viewport.getBoundingClientRect();
    if (!reduced.matches && !covered && !document.hidden && box.width && box.height && !card.hidden) {
      // The fixed copy can finish its flight as the tour hides the departing article.
      const plane = card.cloneNode(true) as HTMLElement;
      const start = getComputedStyle(card);
      const copy = document.createElement('span');
      copy.className = `film-slice-viewport film-slice-exit${flow ? '' : ' film-slice-exit-fixed'}`;
      copy.setAttribute('aria-hidden', 'true');
      if (!flow) Object.assign(copy.style, { left: `${box.left}px`, top: `${box.top}px`, width: `${box.width}px`, height: `${box.height}px` });
      copy.append(plane);
      (flow ? button : main).append(copy);
      exit = copy;
      const motion = plane.animate([
        { transform: start.transform, opacity: Number(start.opacity), offset: 0 },
        { transform: pose(27 * side, -7, -42, -16 * side, 3 * side), opacity: .98, offset: .42 },
        { transform: pose(112 * side, -16, -133, -32 * side, 6 * side), opacity: .65, offset: 1 },
      ], { duration: 320, easing: 'cubic-bezier(.48,.05,.67,.96)' });
      motion.onfinish = () => {
        copy.remove();
        if (exit === copy) { exit = undefined;setPhase('waiting'); }
      };
      setPhase('leaving');
    } else setPhase('waiting');
    clearActivity();
  }

  function syncFlow() {
    if (!flow || covered) return;
    const box = viewport.getBoundingClientRect();
    const visibleHeight = Math.min(box.bottom, innerHeight) - Math.max(box.top, 0);
    if (!exposed && box.height > 0 && visibleHeight / box.height >= .6) enter(box.top < 0 ? -1 : 1);
    else if (exposed && (box.height === 0 || visibleHeight / box.height < .28)) leave(box.top < 0 ? -1 : 1);
  }

  function pauseAutomatic() {
    if (tween?.automatic) land(Math.round(position));
    else schedulePlay();
  }

  function manual() {
    requestedPlay = false;
    if (flight) finishEntry();
    if (position > last) land(Math.round(position)); // Finish a partial wrap before taking bounded input.
    clearTimeout(timer);timer = undefined;
    controls();
  }

  function step(direction: Side) {
    if (!canBrowse() || !multiple || current + direction < 0 || current + direction > last) return false;
    manual();moveTo(clamp(current + direction, 0, last), 400);
    return true;
  }

  button.addEventListener('wheel', event => {
    if (!canBrowse() || !multiple || !event.cancelable || event.ctrlKey || event.metaKey || event.altKey) return;
    const now = performance.now();
    if (now - lastWheel >= 180) ownsWheel = false;
    const width = button.clientWidth;
    const { x, y } = normalizeCardWheel(event, 16, width);
    const delta = gesture.take(x, y, now) === 'horizontal' ? x : y;
    if (!delta) return;
    lastWheel = now;
    const edge = delta < 0 ? position <= .001 : position >= last - .001 && position <= last;
    if (!ownsWheel && edge) return;
    event.preventDefault();event.stopPropagation();
    ownsWheel = true;
    if (edge || Math.abs(delta) < .5) return;
    if (!scrub) {
      manual();stopTrack();
      scrub = { aim: position, lastInput: now };
      setPhase('scrubbing');
    }
    scrub.aim = clamp(scrub.aim + delta / clamp(width * .55, 225, 465), 0, last);
    scrub.lastInput = now;
    queueTrack();
  }, { ...options, passive: false });

  button.addEventListener('pointerenter', event => {
    if (event.pointerType !== 'touch') { hovered = true;pauseAutomatic(); }
  }, options);
  button.addEventListener('pointerleave', event => {
    if (event.pointerType !== 'touch') { hovered = false;clearWheel();schedulePlay(); }
  }, options);
  button.addEventListener('pointerdown', event => {
    if (event.pointerType !== 'touch' || !event.isPrimary) return;
    suppressClickUntil = 0;
    if (canBrowse() && multiple) swipe = { id: event.pointerId, x: event.clientX, y: event.clientY };
  }, options);
  button.addEventListener('pointermove', event => {
    if (!swipe || swipe.id !== event.pointerId) return;
    const x = swipe.x - event.clientX, y = swipe.y - event.clientY;
    if (swipe.start === undefined) {
      if (Math.abs(y) >= 10 && Math.abs(y) >= Math.abs(x)) { swipe = undefined;return; }
      if (Math.abs(x) < 12 || Math.abs(x) < Math.abs(y) * 1.15) return;
      manual();stopTrack();
      swipe.start = position;
      setPhase('scrubbing');
    }
    if (!reduced.matches) draw(clamp(swipe.start + x / button.clientWidth, 0, last));
  }, options);
  function endSwipe(event: PointerEvent) {
    if (!swipe || swipe.id !== event.pointerId) return;
    const started = swipe.start, x = swipe.x - event.clientX;
    swipe = undefined;
    if (started === undefined) return;
    suppressClickUntil = performance.now() + 400;
    const changed = event.type === 'pointerup' && Math.abs(x) >= Math.min(68, button.clientWidth * .24);
    const target = changed ? Math.round(started) + Math.sign(x) : Math.round(position);
    moveTo(clamp(target, 0, last), 255);
  }
  button.addEventListener('pointerup', endSwipe, options);
  button.addEventListener('pointercancel', endSwipe, options);

  button.addEventListener('click', event => {
    if (canBrowse() && phase === 'settled' && (event.detail === 0 || performance.now() >= suppressClickUntil)) openImage(current, button);
  }, options);
  back.addEventListener('click', () => { step(-1); }, options);
  next.addEventListener('click', () => { step(1); }, options);
  play.addEventListener('click', () => {
    if (!canBrowse() || !multiple) return;
    requestedPlay = !wantsPlay();controls();pauseAutomatic();
  }, options);
  for (const control of viewButtons) control.addEventListener('click', () => {
    if (!canBrowse() || phase !== 'settled' || control.disabled) return;
    cards[current]!.plane.dataset.sliceView = control.dataset.filmSliceView;
    manual();
  }, options);
  article.addEventListener('keydown', event => {
    if (event.ctrlKey || event.metaKey || event.altKey || event.shiftKey) return;
    if ((event.key === 'ArrowLeft' && step(-1)) || (event.key === 'ArrowRight' && step(1))) event.preventDefault();
  }, options);
  document.addEventListener('visibilitychange', () => { clearWheel();pauseAutomatic(); }, options);
  reduced.addEventListener('change', () => {
    if (reduced.matches) {
      requestedPlay = false;
      exit?.remove();exit = undefined;
      if (flight) finishEntry();
      else if (exposed && (tween || scrub)) land(Math.round(position));
      else if (!exposed) setPhase('waiting');
    }
    controls();schedulePlay();
  }, options);
  const observer = new IntersectionObserver(syncFlow, { threshold: [0, .28, .6, 1] });
  observer.observe(viewport);
  select(0);controls();

  return {
    prepare() { prepare(current); },
    get ready() { return phase === 'settled'; },
    get image() { return cards[current]!.image; },
    setImmersive(readable: boolean, held: boolean, side: Side) {
      if (flow || covered) return;
      if (!readable) {
        entrySide = side;
        if (exposed) leave(side);
      } else if (!exposed && held) enter(entrySide);
    },
    setFlow(enabled: boolean) {
      if (flow === enabled) return;
      flow = enabled;exposed = false;hovered = false;
      exit?.remove();exit = undefined;clearActivity();setPhase('waiting');controls();
      if (flow) syncFlow();
    },
    setCovered(value: boolean) {
      covered = value;
      if (!value) {
        hovered = matchMedia('(any-hover: hover)').matches && button.matches(':hover');
        syncFlow();
      }
      controls();pauseAutomatic();
    },
    dispose() { listeners.abort();observer.disconnect();exit?.remove();clearActivity(); },
  };
}
