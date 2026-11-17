import { aboutRefreshContent, getCard, getTrackCards } from './content';
import { button, clamp, element } from './dom';
import { createToolCard } from './createToolCard';
import { createCardEntrance } from './createCardEntrance';
import { createCardTrack } from './createCardTrack';
import { createCardHover } from './createCardHover';
import { createCardDeparture } from './createCardDeparture';
import { createToolHelp } from './createToolHelp';
import { toolGuidance, toolHelpCopy } from './toolGuidance';
import type { ToolInput } from './toolGuidance';
import { createWheelGesture, normalizeCardWheel } from './cardWheelInput';
import type { ToolCardView } from './createToolCard';
import type { AboutViewOptions, CardDepartureContext, CardEntranceContext, CardTrackContext, CardsSnapshot, CategoryFilter, ToolBrowserSnapshot, ToolCard, TrackPosition } from './types';

let instanceCount = 0;
const labels: Readonly<Record<string, string>> = aboutRefreshContent.controls;

/** One card per ID, shared by native browsing, entrance and the automatic track. */
export function createToolBrowser(options: AboutViewOptions = {}) {
  const prefix = `ar-tools-${++instanceCount}`;
  const listeners = new AbortController();
  const cardViews = new Map<string, ToolCardView>();
  const events = { signal: listeners.signal };
  const root = element('section', 'ar-tools-browser');
  root.setAttribute('aria-label', '工具卡片浏览');
  const filters = element('div', 'ar-filter-bar');
  const desktopFilters = element('div', 'ar-category-buttons');
  desktopFilters.setAttribute('role', 'group');
  desktopFilters.setAttribute('aria-label', '按分类浏览');
  const mobileLabel = element('label', 'ar-category-select', '按分类浏览');
  const select = element('select');
  const categories = [{ id: 'all', name: '全部' }, ...aboutRefreshContent.categories];
  for (const category of categories) {
    const choice = button(category.name);
    choice.dataset.category = category.id;
    desktopFilters.append(choice);
    const option = element('option', '', category.name);
    option.value = category.id;
    select.append(option);
  }
  mobileLabel.append(select);
  const showAll = button(labels['show-all']!);
  showAll.dataset.action = 'all';
  filters.append(desktopFilters, mobileLabel, showAll);

  const rail = element('div', 'ar-tool-rail');
  rail.tabIndex = 0;
  rail.setAttribute('role', 'region');
  rail.setAttribute('aria-label', '工具卡片横向浏览区');
  const foreground = element('div', 'ar-card-foreground');
  foreground.setAttribute('role', 'presentation');
  const allPanel = element('section', 'ar-all-tools');
  allPanel.hidden = true;
  const allHeading = element('h3', '', '全部工具');
  allHeading.id = `${prefix}-all-title`;
  allHeading.tabIndex = -1;
  allPanel.setAttribute('aria-labelledby', allHeading.id);
  const allHeader = element('div', 'ar-all-header');
  const returnTop = button(labels['return-to-cards']!);
  returnTop.dataset.action = 'return';
  allHeader.append(allHeading, element('p', 'ar-muted', '21 款工具 · 1 张能力卡'), returnTop, element('p','ar-catalog-instruction',toolHelpCopy.catalog));
  const catalog = element('div', 'ar-catalog');
  const returnBottom = button(labels['return-to-cards']!, 'ar-button ar-return-bottom');
  returnBottom.dataset.action = 'return';
  allPanel.append(allHeader, catalog, returnBottom);

  const controls = element('div', 'ar-tool-controls');
  const actions = element('div', 'ar-tool-actions');
  const previous = button(labels['previous-card']!);
  previous.dataset.action = 'previous';
  previous.setAttribute('aria-label', '查看上一张工具卡');
  const next = button(labels['next-card']!);
  next.dataset.action = 'next';
  next.setAttribute('aria-label', '查看下一张工具卡');
  const count = element('span', 'ar-card-count');
  count.setAttribute('role', 'status');
  count.setAttribute('aria-live', 'off');
  const autoplay = button(labels['pause-auto']!, 'ar-button ar-auto-toggle');
  autoplay.dataset.action = 'auto';autoplay.hidden = true;
  actions.append(previous, next, count, autoplay);
  const primaryHint = element('p', 'ar-hint ar-current-hint');primaryHint.id = `${prefix}-wheel-hint`;
  rail.setAttribute('aria-describedby',primaryHint.id);
  const guidanceBar = element('div','ar-guidance-bar');guidanceBar.append(primaryHint);
  const announcement = element('span','ar-announcement');announcement.setAttribute('role','status');announcement.setAttribute('aria-live','polite');
  controls.append(actions,guidanceBar);
  root.append(filters, rail, foreground, allPanel, controls,announcement);
  const entrance = createCardEntrance({ root, rail, foreground, views: cardViews, changed: () => { syncTrack();options.onEntranceChange?.(); } });

  let disposed = false;
  let departure: ReturnType<typeof createCardDeparture> | undefined;
  let help: ReturnType<typeof createToolHelp> | undefined;
  let uiReady=false,updatingControls=false,controlsDirty=false,readingHold=false,helpHold=false,lastLeaveHint='';
  const fine=matchMedia('(hover:hover) and (pointer:fine)'),reduced=matchMedia('(prefers-reduced-motion:reduce)');
  let input: ToolInput=fine.matches?'mouse':'touch';
  let touchButton: { pointerId: number; x: number; y: number } | undefined;
  let touchRelease: number | undefined;
  let restoreFrame: number | undefined;
  let mode: 'cards' | 'all' = 'cards';
  let railWidth = 0;
  let cardsState: CardsSnapshot = {
    category: 'all', activeId: 'midjourney', expandedId: null,
    position: { anchorId: 'midjourney', offsetRatio: 0, scrollLeft: 0, viewportWidth: 0 },
  };
  const changed = () => { if (!disposed) options.onLayoutChange?.(); };
  const wheelGesture = createWheelGesture();
  const interact = () => { if (!disposed) { help?.close('interaction');departure?.cancel('interaction');wheelGesture.clear();hover.cancel('interaction');track.pause('interaction');entrance.cancel('interaction');options.onInteraction?.(); } };
  const visibleCards = () => getTrackCards(cardsState.category);
  const slots = () => [...rail.querySelectorAll<HTMLElement>('.ar-tool-slot')];
  const leadingPadding = () => parseFloat(getComputedStyle(rail).paddingLeft) || 0;
  let trackContext: CardTrackContext = { active: false, allowed: false, automatic: false, top: 0, bottom: 0 };
  const track = createCardTrack({ root, rail, controls, views: cardViews,
    nativePosition: captureNativePosition,
    restoreNative(position) { if (mode === 'cards') applyNativePosition(position); },
    cursor(id, position) { cardsState = { ...cardsState, activeId: id, position };updateControls(); },
    changed: updateControls,
  });
  const hover = createCardHover({ root, rail, views: cardViews,
    hold: held => {readingHold=held;track.holdReading(readingHold||helpHold);}, interaction: () => options.onInteraction?.(), changed: updateControls,
    pinnedChanged(id) { if (!disposed) { cardsState = { ...cardsState, expandedId: id, activeId: id ?? cardsState.activeId };updateControls(); } },
    nativePinned() {
      track.native('detail-reading');
      const id = cardsState.expandedId;
      if (mode === 'cards' && id) {
        applyNativePosition({ anchorId: id, offsetRatio: 0, scrollLeft: 0, viewportWidth: rail.clientWidth });
        cardsState = { ...cardsState, position: captureNativePosition() };
      }
    }, layoutChanged: changed,
  });
  departure = createCardDeparture({root,rail,views:cardViews,ready:() => entrance.ready,capture:captureState,
    changed:updateControls,
    freeze() { wheelGesture.clear();track.suspendForDeparture(true);hover.suspendForDeparture(true); },
    release(returned) {
      track.suspendForDeparture(false);
      hover.present({...trackContext,active:trackContext.active && mode === 'cards',allowed:trackContext.allowed && mode === 'cards'},entrance.ready);
      hover.suspendForDeparture(false,returned);syncTrack();
    },
  });
  help=createToolHelp({prefix,root,rail,controls,changed(open) {
    helpHold=open;track.holdReading(readingHold||helpHold);
    if(open){departure?.cancel('help');entrance.cancel('help');wheelGesture.clear();options.onInteraction?.();}
    updateControls();if(!help?.popover)changed();
  }});
  guidanceBar.append(help.trigger);root.append(help.panel);uiReady=true;
  function syncTrack() {
    if (departure?.owns) return;
    const context = { ...trackContext, active: trackContext.active && mode === 'cards',
      allowed: trackContext.allowed && mode === 'cards' };
    if (!context.active || !context.allowed) wheelGesture.clear();
    track.present(context, entrance.ready, root.dataset.entranceReason ?? '');
    hover.present(context, entrance.ready);
  }

  function capturePosition(): TrackPosition {
    return track.active ? track.position() : captureNativePosition();
  }
  function captureNativePosition(): TrackPosition {
    if (mode !== 'cards' || !rail.clientWidth) return cardsState.position;
    const padding = leadingPadding();
    const anchor = slots().find(node => node.offsetLeft + node.offsetWidth > rail.scrollLeft + padding + 1);
    if (!anchor) return cardsState.position;
    return {
      anchorId: anchor.dataset.cardId!,
      offsetRatio: (rail.scrollLeft - (anchor.offsetLeft - padding)) / Math.max(1, anchor.offsetWidth),
      scrollLeft: rail.scrollLeft, viewportWidth: rail.clientWidth,
    };
  }

  function captureState(): ToolBrowserSnapshot {
    if (mode === 'cards') cardsState = { ...cardsState, position: capturePosition() };
    return structuredClone({ mode, cards: cardsState, track: track.capture() });
  }

  function updateControls() {
    if(!uiReady||disposed)return;
    if(updatingControls){controlsDirty=true;return;}
    updatingControls=true;
    try{do{controlsDirty=false;renderControls();}while(controlsDirty);}finally{updatingControls=false;}
  }
  function text(node:HTMLElement,value:string){if(node.textContent!==value)node.textContent=value;}
  function attr(node:HTMLElement,name:string,value:string){if(node.getAttribute(name)!==value)node.setAttribute(name,value);}
  function renderControls() {
    const cards = visibleCards();
    const readingId = cardsState.expandedId ?? root.dataset.readingId;
    const index = Math.max(0, cards.findIndex(card => card.id === (readingId || cardsState.activeId)));
    previous.disabled = !track.active && index === 0;
    next.disabled = !track.active && index === cards.length - 1;
    text(count,`${index + 1} / ${cards.length}`);attr(count,'aria-label',`第 ${index+1} 张，共 ${cards.length} 张工具卡`);
    root.dataset.activeId = cardsState.activeId;
    root.dataset.mode = mode;
    root.dataset.category = cardsState.category;
    root.dataset.cardCount = String(mode === 'all' ? aboutRefreshContent.cards.length : cards.length);
    for (const slot of slots()) {const active=String(slot.dataset.cardId===cardsState.activeId);if(slot.dataset.active!==active)slot.dataset.active=active;}
    autoplay.hidden = mode !== 'cards' || !track.available;
    text(autoplay,labels[track.enabled ? 'pause-auto' : 'resume-auto']!);attr(autoplay,'aria-pressed',String(track.enabled));
    const host=root.closest<HTMLElement>('.about-refresh');
    const model=toolGuidance({input,help:help?.open??false,entrance:root.dataset.entrance??'',departure:root.dataset.departure??'',returnPaused:root.dataset.departurePointerPaused==='true',
      pinned:cardsState.expandedId!==null,preview:['entering','reading','pressed'].includes(root.dataset.hoverState??''),automatic:track.enabled,running:root.dataset.trackState==='running',program:track.active,
      hover:hover.available,
      overflow:track.active||rail.scrollWidth>rail.clientWidth+1,autoAvailable:track.available,immersive:host?.dataset.layout==='immersive'});
    text(primaryHint,model.hint);if(root.dataset.guidanceState!==model.state)root.dataset.guidanceState=model.state;
    if(root.dataset.toolInput!==input)root.dataset.toolInput=input;
    if(model.leave!==lastLeaveHint){lastLeaveHint=model.leave;options.onToolLeaveHint?.(model.leave);}
    help?.update(model);
  }
  function setInput(next:ToolInput,deferTouch=false){
    if(!deferTouch)hover.setTouchInput(next==='touch');
    if(input!==next){input=next;updateControls();}
  }
  function releaseTouchButton() {
    if(touchRelease!==undefined)clearTimeout(touchRelease);touchRelease=undefined;
    if(!touchButton)return;
    touchButton=undefined;
    if(input!=='touch')return;
    hover.setTouchInput(true);track.native('touch');updateControls();
  }

  function restorePosition(position: TrackPosition, focus?: HTMLElement) {
    if (restoreFrame !== undefined) cancelAnimationFrame(restoreFrame);
    restoreFrame = requestAnimationFrame(() => {
      restoreFrame = undefined;
      if (disposed || departure?.owns || mode !== 'cards' || !rail.clientWidth) return;
      if (track.active) { focus?.focus({ preventScroll: true });return; }
      const pinned = cardsState.expandedId;
      applyNativePosition(pinned && cardViews.get(pinned)?.element.dataset.detailWide === 'false'
        ? { anchorId: pinned, offsetRatio: 0, scrollLeft: 0, viewportWidth: rail.clientWidth } : position);
      cardsState = { ...cardsState, position: capturePosition() };
      focus?.focus({ preventScroll: true });
    });
  }
  function applyNativePosition(position: TrackPosition) {
    const anchor = slots().find(slot => slot.dataset.cardId === position.anchorId);
    const destination = anchor ? anchor.offsetLeft - leadingPadding() + position.offsetRatio * anchor.offsetWidth : position.scrollLeft;
    rail.scrollTo({ left: clamp(destination, 0, rail.scrollWidth - rail.clientWidth), behavior: 'instant' });
  }

  function clearCardViews(rememberTrack = false) {
    releaseTouchButton();
    departure?.cancel('content-changed');
    hover.cancel('content-changed');
    entrance.cancel('content-changed');
    track.clear(rememberTrack);
    for (const view of cardViews.values()) view.dispose();
    cardViews.clear();
  }

  function createCard(card: ToolCard, full: boolean) {
    const view = createToolCard(card, { prefix, full, expanded: full || cardsState.expandedId === card.id });
    cardViews.set(card.id, view);
    return view.element;
  }

  function renderRail(restoreTrack = false) {
    clearCardViews(restoreTrack);
    rail.replaceChildren();
    for (const card of visibleCards()) {
      const slot = element('div', 'ar-tool-slot');
      slot.dataset.cardId = card.id;
      slot.append(createCard(card, false));
      rail.append(slot);
    }
    select.value = cardsState.category;
    for (const choice of desktopFilters.querySelectorAll<HTMLButtonElement>('button')) {
      choice.setAttribute('aria-pressed', String(choice.dataset.category === cardsState.category));
    }
    updateControls();
    hover.restorePinned(cardsState.expandedId);
  }

  function selectCategory(value: string) {
    if (!categories.some(category => category.id === value)) return;
    hover.clearPin(false);interact();
    const category = value as CategoryFilter;
    const first = getTrackCards(category)[0]!;
    cardsState = {
      category, activeId: first.id, expandedId: null,
      position: { anchorId: first.id, offsetRatio: 0, scrollLeft: 0, viewportWidth: rail.clientWidth },
    };
    renderRail();
    restorePosition(cardsState.position);
    syncTrack();
    text(announcement,`${categories.find(item=>item.id===category)!.name}，${getTrackCards(category).length} 张工具卡。`);
    changed();
  }

  function move(direction: -1 | 1) {
    const source = cardsState.expandedId ?? (root.dataset.readingId || cardsState.activeId);
    const keepPinned = cardsState.expandedId !== null;
    if (keepPinned) hover.clearPin(false);
    interact();
    if (track.active) {
      const id = track.step(direction, source);
      if (keepPinned && id) hover.pin(id);
      updateControls();return;
    }
    track.native('native-step');
    const cards = visibleCards();
    const index = Math.max(0, cards.findIndex(card => card.id === source));
    const target = cards[clamp(index + direction, 0, cards.length - 1)]!;
    cardsState = { ...cardsState, activeId: target.id };
    const slot = slots().find(node => node.dataset.cardId === target.id)!;
    rail.scrollTo({ left: clamp(slot.offsetLeft - leadingPadding(), 0, rail.scrollWidth - rail.clientWidth), behavior: 'instant' });
    cardsState = { ...cardsState, position: capturePosition() };
    if (keepPinned) hover.pin(target.id);
    updateControls();
  }

  function toggleDetail(id: string) {
    if (!getCard(id) || !visibleCards().some(item => item.id === id)) return;
    wheelGesture.clear();track.pause('detail');entrance.cancel('detail');options.onInteraction?.();
    cardsState = { ...cardsState, position: capturePosition() };
    if (cardsState.expandedId === id) hover.clearPin(true);else hover.pin(id);
    updateControls();syncTrack();
    // Native/mobile layouts may grow vertically; the full paragraph remains in flow.
    if (cardViews.get(id)?.element.dataset.detailWide !== 'true') {
      const slot = slots().find(node => node.dataset.cardId === id)!;
      const box = slot.getBoundingClientRect(), bounds = rail.getBoundingClientRect();
      if (box.left < bounds.left + 12 || box.right > bounds.right - 12) rail.scrollTo({ left: clamp(slot.offsetLeft - leadingPadding(), 0, rail.scrollWidth - rail.clientWidth), behavior: 'instant' });
      changed();
    }
  }

  function showAllTools(interaction = true) {
    help?.close('all-tools');
    if (interaction) interact();
    cardsState = { ...cardsState, position: capturePosition() };
    mode = 'all';
    clearCardViews(true);
    filters.hidden = true;rail.hidden = true;controls.hidden = true;allPanel.hidden = false;
    rail.replaceChildren();
    catalog.replaceChildren();
    for (const category of aboutRefreshContent.categories) {
      const section = element('section', 'ar-catalog-group');
      const title = element('h4', '', category.name);
      title.id = `${prefix}-group-${category.id}`;
      section.setAttribute('aria-labelledby', title.id);
      const grid = element('div', 'ar-catalog-grid');
      for (const id of category.cardIds) grid.append(createCard(getCard(id)!, true));
      section.append(title, grid);catalog.append(section);
    }
    updateControls();
    changed();
    if (interaction) options.onToolModeChange?.('all');
    allHeading.focus({ preventScroll: true });
    syncTrack();
  }

  function returnToCards(focus = true, interaction = true) {
    if (interaction) interact();
    mode = 'cards';
    filters.hidden = false;rail.hidden = false;controls.hidden = false;allPanel.hidden = true;
    catalog.replaceChildren();
    renderRail(true);
    restorePosition(cardsState.position, focus ? showAll : undefined);
    changed();
    if (interaction) options.onToolModeChange?.('cards');
    syncTrack();
  }

  root.addEventListener('click', event => {
    const target = (event.target as Element).closest<HTMLButtonElement>('button');
    if (!target || !root.contains(target) || target.disabled) return;
    if(help?.contains(target))return;
    help?.close('button');
    departure?.cancel('button');
    if (target.dataset.category) { selectCategory(target.dataset.category);return; }
    switch (target.dataset.action) {
      case 'previous': move(-1);break;
      case 'next': move(1);break;
      case 'detail': toggleDetail(target.dataset.toolId!);releaseTouchButton();break;
      case 'all': showAllTools();break;
      case 'return': returnToCards();break;
      case 'auto': {
        const play = !track.enabled;
        wheelGesture.clear();entrance.cancel('interaction');options.onInteraction?.();
        if (play) {
          if (cardsState.expandedId) hover.clearPin(true);else hover.cancel('automatic');
          track.play();
        } else { hover.cancel('user-pause');track.pause('user-pause'); }
        updateControls();break;
      }
    }
  }, events);
  root.addEventListener('keydown', event => {
    if(!event.ctrlKey&&!event.metaKey&&!event.altKey&&['Tab','Enter',' ','Escape'].includes(event.key))setInput('keyboard');
    if(event.key==='Escape'&&help?.open){help.close('escape',true);event.preventDefault();event.stopPropagation();return;}
    if(help?.contains(event.target)){
      if(event.key==='Escape'){departure?.cancel('keyboard');if(hover.escape())event.preventDefault();}
      return;
    }
    departure?.cancel('keyboard');
    if ((event.target as Element).closest('[data-action="auto"]')) return;
    if (event.key === 'Escape' && hover.escape()) event.preventDefault();
    wheelGesture.clear();track.pause('keyboard');entrance.cancel('keyboard');
  }, { ...events, capture: true });
  root.addEventListener('focusin', event => {
    if((event.target as Element).matches(':focus-visible'))setInput('keyboard');
    if(help?.contains(event.target))return;
    if (!departure?.pointerHeld) departure?.cancel('focus');
    if ((event.target as Element).closest('[data-action="auto"]')) return;
    wheelGesture.clear();track.pause('focus');entrance.cancel('focus');
    const card = (event.target as Element).closest<HTMLElement>('.ar-tool-card');
    if (card) {
      if (track.active) { if (!cardsState.expandedId && (event.target as Element).matches(':focus-visible')) track.focus(card.dataset.toolId!); }
      else track.native('native-focus');
      if ((event.target as Element).matches(':focus-visible')) hover.focus(card.dataset.toolId!);
    }
  }, events);
  root.addEventListener('pointerdown',event=>{
    releaseTouchButton();
    const touch=event.pointerType!=='mouse';
    // Keep the actual button under the finger until its native click. Detaching
    // the perspective track on pointerdown moves a hovered button before touchup.
    if(touch && rail.contains(event.target as Node) && (event.target as Element).closest('button'))touchButton={pointerId:event.pointerId,x:event.clientX,y:event.clientY};
    setInput(touch?'touch':'mouse',!!touchButton);
  },{...events,capture:true});
  root.addEventListener('pointermove',event=>{
    if(touchButton?.pointerId===event.pointerId && Math.hypot(event.clientX-touchButton.x,event.clientY-touchButton.y)>8)releaseTouchButton();
  },{...events,capture:true});
  root.addEventListener('pointercancel',releaseTouchButton,events);
  window.addEventListener('pointerup',event=>{
    if(touchButton?.pointerId===event.pointerId)touchRelease=window.setTimeout(releaseTouchButton,350);
  },events);
  // Recognize the returning mouse before the rail evaluates this same move.
  root.addEventListener('pointermove',event=>{if(event.pointerType==='mouse'&&!event.buttons&&(event.movementX||event.movementY))setInput('mouse');},{...events,capture:true});
  fine.addEventListener('change',()=>{if(input!=='keyboard')setInput(fine.matches?'mouse':'touch');updateControls();},events);
  reduced.addEventListener('change',()=>updateControls(),events);
  root.addEventListener('focusout', event => {
    const card = (event.target as Element).closest('.ar-tool-card');
    if (card && (!event.relatedTarget || !card.contains(event.relatedTarget as Node))) hover.blur();
  }, events);
  select.addEventListener('change', () => selectCategory(select.value), events);
  rail.addEventListener('pointerdown', event => {
    wheelGesture.clear();
    if (event.pointerType !== 'mouse' && !touchButton) track.native('touch');
    track.pause('pointer');
    if (!(event.target as Element).closest('button')) { entrance.cancel('pointer');options.onInteraction?.(); }
  }, events);
  rail.addEventListener('wheel', event => {
    // Modified wheel belongs to browser zoom; unavailable layouts/reading panels
    // retain native page scrolling. Only this row can own program wheel input.
    if (disposed || mode !== 'cards' || event.ctrlKey || event.metaKey || event.altKey || !event.cancelable || event.defaultPrevented) return;
    setInput('mouse');help?.close('wheel');
    departure?.cancel('wheel');
    const bounds = rail.getBoundingClientRect();
    if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) return;
    if (cardsState.expandedId) return;
    hover.wheel();
    const delta = normalizeCardWheel(event, parseFloat(getComputedStyle(rail).lineHeight) || 20, rail.clientWidth);
    if (!delta.x && !delta.y) return;
    const axis = wheelGesture.take(delta.x, delta.y, performance.now());
    if (axis === 'horizontal') {
      const handingOff = track.active;
      track.native('horizontal-gesture');entrance.cancel('interaction');options.onInteraction?.();
      // Chromium chooses the scroll chain before dispatch. Transfer this first
      // event exactly once; subsequent events keep native browser momentum.
      if (handingOff) {
        event.preventDefault();
        rail.scrollBy({ left: delta.x, behavior: 'instant' });
      }
    } else if (track.wheelAvailable && track.wheel(delta.y)) {
      event.preventDefault();
      // A wheel gesture interrupts the main guide without changing the card
      // autoplay choice. Explicit buttons/pointer focus still pause immediately.
      options.onInteraction?.();
    }
  }, { ...events, passive: false });
  rail.addEventListener('pointerleave', () => { wheelGesture.clear();track.releaseWheel(); }, events);
  window.addEventListener('resize', () => {releaseTouchButton();wheelGesture.clear();}, events);
  document.addEventListener('visibilitychange', () => {releaseTouchButton();wheelGesture.clear();}, events);
  rail.addEventListener('scroll', () => {
    if (disposed || mode !== 'cards' || !rail.clientWidth) return;
    if (track.active) { if (rail.scrollLeft) rail.scrollLeft = 0;return; }
    cardsState = { ...cardsState, position: capturePosition() };
    const current = slots().find(node => node.dataset.cardId === cardsState.activeId);
    const frame = rail.getBoundingClientRect();
    const box = current?.getBoundingClientRect();
    if (box && (box.right <= frame.left || box.left >= frame.right)) {
      cardsState = { ...cardsState, activeId: cardsState.position.anchorId };
    }
    updateControls();
  }, { ...events, passive: true });
  const observer = new ResizeObserver(() => {
    if (disposed || mode !== 'cards' || !rail.clientWidth || railWidth === rail.clientWidth) return;
    railWidth = rail.clientWidth;
    restorePosition(cardsState.position);
    changed();
  });
  observer.observe(rail);
  renderRail();

  return {
    root, captureState,
    get entranceReady() { return entrance.ready; },
    cancelEntrance(reason?: string) { entrance.cancel(reason); },
    closeHelp(reason?:string){help?.close(reason);},
    presentDeparture(context: CardDepartureContext) {if(help?.open&&help.popover&&(!context.active||context.progress<.3||context.progress>.8))help.close('left-section');departure?.present({...context,enabled:context.enabled && mode === 'cards'});},
    cancelDeparture(reason?: string) { departure?.cancel(reason); },
    presentEntrance(context: CardEntranceContext) {
      entrance.present({ ...context, enabled: context.enabled && mode === 'cards' && cardsState.category === 'all' && cardsState.activeId === 'midjourney' && cardsState.expandedId === null });
    },
    presentTrack(context: CardTrackContext) { const different=JSON.stringify(context)!==JSON.stringify(trackContext);if(!context.active||!context.allowed)releaseTouchButton();trackContext = context;if(help?.open&&!help.popover&&!context.active)help.close('left-section');syncTrack();if(different)updateControls(); },
    closeOverview() { if (!disposed && mode === 'all') returnToCards(); },
    restoreState(snapshot: ToolBrowserSnapshot) {
      if (disposed) return;
      releaseTouchButton();
      help?.close('state-restored');
      departure?.cancel('state-restored');
      wheelGesture.clear();hover.cancel('state-restored');entrance.cancel('state-restored');
      const category = categories.some(item => item.id === snapshot.cards.category) ? snapshot.cards.category : 'all';
      const cards = getTrackCards(category);
      cardsState = structuredClone({ ...snapshot.cards, category,
        activeId: cards.some(card => card.id === snapshot.cards.activeId) ? snapshot.cards.activeId : cards[0]!.id,
        expandedId: cards.some(card => card.id === snapshot.cards.expandedId) ? snapshot.cards.expandedId : null });
      if (snapshot.mode === 'all') { mode = 'all';showAllTools(false); } else returnToCards(false, false);
      if (snapshot.track) track.restore({ ...snapshot.track, enabled: snapshot.cards.expandedId ? false : snapshot.track.enabled }, visibleCards().map(card => card.id));else track.pause('state-restored');
      hover.restorePinned(cardsState.expandedId);
      syncTrack();
    },
    refresh() { if (!disposed && !departure?.owns && mode === 'cards') restorePosition(cardsState.position); },
    dispose() {
      if (disposed) return;
      releaseTouchButton();
      help?.dispose();
      departure?.dispose();
      disposed = true;hover.dispose();track.dispose();entrance.dispose();listeners.abort();observer.disconnect();clearCardViews();
      if (restoreFrame !== undefined) cancelAnimationFrame(restoreFrame);
      root.remove();
    },
  };
}
