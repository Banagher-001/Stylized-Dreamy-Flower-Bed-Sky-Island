import { aboutRefreshContent, getCard, getTrackCards } from './content';
import { button, clamp, element } from './dom';
import { createToolCard } from './createToolCard';
import { createCardEntrance } from './createCardEntrance';
import { createCardTrack } from './createCardTrack';
import { createCardInteractionRegion } from './cardInteractionRegion';
import type { CardRegionBounds } from './cardInteractionRegion';
import { createCardRegionDebug } from './createCardRegionDebug';
import { createCardHover } from './createCardHover';
import { createCardDeparture } from './createCardDeparture';
import { createToolHelp } from './createToolHelp';
import { toolGuidance, toolHelpCopy } from './toolGuidance';
import type { ToolInput } from './toolGuidance';
import { createWheelGesture, normalizeCardWheel } from './cardWheelInput';
import type { WheelAxis } from './cardWheelInput';
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
  const entrance = createCardEntrance({ root, rail, foreground, views: cardViews,
    changed: () => { syncTrack();applyLandingWheel();options.onEntranceChange?.(); } });

  let disposed = false;
  let departure: ReturnType<typeof createCardDeparture> | undefined;
  let help: ReturnType<typeof createToolHelp> | undefined;
  let uiReady=false,updatingControls=false,controlsDirty=false,readingHold=false,helpHold=false,lastLeaveHint='';
  const fine=matchMedia('(hover:hover) and (pointer:fine)'),reduced=matchMedia('(prefers-reduced-motion:reduce)');
  let lastInput: ToolInput | undefined;
  const currentInput = (): ToolInput => lastInput ?? (fine.matches ? 'mouse' : 'touch');
  let cardPress: { pointerId: number; button: HTMLButtonElement | null; touch: boolean; x: number; y: number } | undefined;
  let pressRelease: number | undefined;
  let keyboardFocus: HTMLElement | undefined;
  let changingCards = false;
  let restoreFrame: number | undefined;
  let mode: 'cards' | 'all' = 'cards';
  let railWidth = 0;
  let cardOverflow = false, measuredSlot: HTMLElement | undefined;
  let cardsState: CardsSnapshot = {
    category: 'all', activeId: 'midjourney', expandedId: null,
    position: { anchorId: 'midjourney', offsetRatio: 0, scrollLeft: 0, viewportWidth: 0 },
  };
  const changed = () => { if (!disposed) options.onLayoutChange?.(); };
  const wheelGesture = createWheelGesture();
  let wheelBounds: CardRegionBounds | null = null;
  let landingWheel: { axis: WheelAxis; amount: number; slot: HTMLElement } | undefined;

  function clearWheelInput() {
    landingWheel = undefined;
    wheelBounds = null;
    wheelGesture.clear();
    track.cancelWheel();
  }
  function releaseWheelInput() {
    landingWheel = undefined;
    wheelBounds = null;
    wheelGesture.clear();
    track.releaseWheel();
  }
  function syncReadingHold() {
    if (!disposed) track.holdReading(readingHold || helpHold || !!cardPress || !!keyboardFocus || changingCards || mode === 'all');
  }
  function withCardsHeld(action: () => void) {
    const previous = changingCards;
    changingCards = true;
    syncReadingHold();
    try { action(); }
    finally { changingCards = previous;syncReadingHold(); }
  }
  function interact(reason: 'interaction' | 'category' = 'interaction') {
    if (disposed) return;
    clearWheelInput();
    help?.close(reason);
    departure?.cancel(reason);
    hover.cancel(reason);
    entrance.cancel(reason);
    options.onInteraction?.();
  }
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
  const interactionRegion = createCardInteractionRegion({ root, rail, filters, controls,
    state: () => ({ mode, category: cardsState.category, automatic: track.enabled,
      reading: root.dataset.detailMode === 'pinned' ? 'pinned' : root.dataset.detailMode === 'preview' ? 'preview' : 'summary',
      entrance: root.dataset.entrance ?? 'waiting', departure: root.dataset.departure ?? 'idle' }),
  });
  const hover = createCardHover({ root, rail, views: cardViews,
    hold: held => {readingHold=held;syncReadingHold();}, interaction: () => options.onInteraction?.(), changed: updateControls,
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
    freeze() {
      track.suspendForDeparture(true);
      releaseCardPress();clearKeyboardFocus();clearWheelInput();hover.suspendForDeparture(true);
    },
    release(returned) {
      track.suspendForDeparture(false);
      hover.present({...trackContext,active:trackContext.active && mode === 'cards',allowed:trackContext.allowed && mode === 'cards'},entrance.ready);
      hover.suspendForDeparture(false,returned);syncTrack();
    },
  });
  help=createToolHelp({prefix,root,rail,controls,changed(open) {
    helpHold=open;syncReadingHold();
    if(open){clearWheelInput();departure?.cancel('help');entrance.cancel('help');options.onInteraction?.();}
    updateControls();if(!help?.popover)changed();
  }});
  guidanceBar.append(help.trigger);root.append(help.panel);uiReady=true;
  function syncTrack() {
    if (departure?.owns) return;
    const context = { ...trackContext, active: trackContext.active && mode === 'cards',
      allowed: trackContext.allowed && mode === 'cards' };
    if (!context.active && root.closest('.about-refresh')?.getAttribute('data-layout') === 'immersive') releaseWheelInput();
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
    const autoAvailable = mode === 'cards' && track.available;
    autoplay.hidden = !autoAvailable;
    text(autoplay,labels[track.enabled ? 'pause-auto' : 'resume-auto']!);attr(autoplay,'aria-pressed',String(track.enabled));
    const input = currentInput();
    const model = toolGuidance({ input, help: help?.open ?? false, entrance: root.dataset.entrance ?? '',
      departure: root.dataset.departure ?? '', returnPaused: root.dataset.departurePointerPaused === 'true',
      pinned: cardsState.expandedId !== null, preview: root.dataset.detailMode === 'preview',
      userPaused: track.userPaused, activity: track.activity, hover: hover.available,
      overflow: mode === 'cards' && cardOverflow, autoAvailable, autoEnabled: track.enabled, reduced: reduced.matches });
    text(primaryHint,model.hint);if(root.dataset.guidanceState!==model.state)root.dataset.guidanceState=model.state;
    if(root.dataset.toolInput!==input)root.dataset.toolInput=input;
    if(model.leave!==lastLeaveHint){lastLeaveHint=model.leave;options.onToolLeaveHint?.(model.leave);}
    help?.update(model);
  }
  function setInput(next: ToolInput, deferDetail = false) {
    const previous = currentInput();
    lastInput = next;
    if (next !== 'keyboard' && keyboardFocus) clearKeyboardFocus();
    if (next !== 'touch') track.setTouchInput(false);
    if (!deferDetail) hover.setTouchInput(next === 'touch');
    if (previous !== next) updateControls();
  }
  function clearKeyboardFocus() {
    if (!keyboardFocus) return;
    keyboardFocus = undefined;
    if (!cardPress) hover.blur();
    syncReadingHold();
  }
  function releaseCardPress() {
    if (pressRelease !== undefined) clearTimeout(pressRelease);
    pressRelease = undefined;
    if (!cardPress) return;
    const pressed = cardPress;
    if (pressed.touch && pressed.button && currentInput() === 'touch') {
      // A tap can move a previously mouse-driven rail only after its click.
      track.setTouchInput(true);
      hover.setTouchInput(true);
      updateControls();
    } else if (currentInput() === 'mouse') hover.setTouchInput(false);
    hover.releasePress();
    cardPress = undefined;
    delete root.dataset.detailPressed;
    departure?.holdPress(false);
    syncReadingHold();
  }

  function restorePosition(position: TrackPosition, focus?: HTMLElement) {
    cancelPositionRestore();
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
  function cancelPositionRestore() {
    if (restoreFrame !== undefined) cancelAnimationFrame(restoreFrame);
    restoreFrame = undefined;
  }
  function applyNativePosition(position: TrackPosition) {
    const anchor = slots().find(slot => slot.dataset.cardId === position.anchorId);
    const destination = anchor ? anchor.offsetLeft - leadingPadding() + position.offsetRatio * anchor.offsetWidth : position.scrollLeft;
    rail.scrollTo({ left: clamp(destination, 0, rail.scrollWidth - rail.clientWidth), behavior: 'instant' });
  }

  function clearCardViews(rememberTrack = false) {
    if (measuredSlot) observer.unobserve(measuredSlot);
    measuredSlot = undefined;
    cardOverflow = false;
    clearWheelInput();
    cancelPositionRestore();
    releaseCardPress();
    clearKeyboardFocus();
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
    measuredSlot = rail.querySelector<HTMLElement>('.ar-tool-slot') ?? undefined;
    if (measuredSlot) observer.observe(measuredSlot);
    cardOverflow = interactionRegion.measureHorizontal().overflow;
    select.value = cardsState.category;
    for (const choice of desktopFilters.querySelectorAll<HTMLButtonElement>('button')) {
      choice.setAttribute('aria-pressed', String(choice.dataset.category === cardsState.category));
    }
    updateControls();
    hover.restorePinned(cardsState.expandedId);
  }

  function selectCategory(value: string) {
    if (!categories.some(category => category.id === value)) return;
    withCardsHeld(() => {
      hover.clearPin(false);interact('category');
      const category = value as CategoryFilter;
      const first = getTrackCards(category)[0]!;
      cardsState = {
        category, activeId: first.id, expandedId: null,
        position: { anchorId: first.id, offsetRatio: 0, scrollLeft: 0, viewportWidth: rail.clientWidth },
      };
      renderRail();
      applyNativePosition(cardsState.position);
      syncTrack();
      text(announcement,`${categories.find(item=>item.id===category)!.name}，${getTrackCards(category).length} 张工具卡。`);
      changed();
    });
  }

  function move(direction: -1 | 1) {
    const source = cardsState.expandedId ?? (root.dataset.readingId || cardsState.activeId);
    const keepPinned = cardsState.expandedId !== null;
    withCardsHeld(() => {
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
    });
  }

  function toggleDetail(id: string) {
    if (!getCard(id) || !visibleCards().some(item => item.id === id)) return;
    clearWheelInput();entrance.cancel('detail');options.onInteraction?.();
    cardsState = { ...cardsState, position: capturePosition() };
    if (cardsState.expandedId === id) hover.clearPin(true);else hover.pin(id);
    updateControls();syncTrack();
    // Native/mobile layouts may grow vertically; the full paragraph remains in flow.
    if (cardsState.expandedId === id && !track.active && cardViews.get(id)?.element.dataset.detailWide !== 'true') {
      const slot = slots().find(node => node.dataset.cardId === id)!;
      const box = slot.getBoundingClientRect(), bounds = rail.getBoundingClientRect();
      if (box.left < bounds.left + 12 || box.right > bounds.right - 12) rail.scrollTo({ left: clamp(slot.offsetLeft - leadingPadding(), 0, rail.scrollWidth - rail.clientWidth), behavior: 'instant' });
      changed();
    }
  }

  function showAllTools(interaction = true) {
    withCardsHeld(() => {
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
    });
  }

  function returnToCards(focus = true, interaction = true) {
    withCardsHeld(() => {
      if (interaction) interact();
      mode = 'cards';
      filters.hidden = false;rail.hidden = false;controls.hidden = false;allPanel.hidden = true;
      catalog.replaceChildren();
      renderRail(true);
      restorePosition(cardsState.position, focus ? showAll : undefined);
      changed();
      if (interaction) options.onToolModeChange?.('cards');
      syncTrack();
    });
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
      case 'detail':
        withCardsHeld(() => {
          toggleDetail(target.dataset.toolId!);
          releaseCardPress();
        });
        break;
      case 'all': showAllTools();break;
      case 'return': returnToCards();break;
      case 'auto': {
        const play = !track.enabled;
        clearWheelInput();entrance.cancel('interaction');options.onInteraction?.();
        if (play) {
          if (cardsState.expandedId) hover.clearPin(true);else hover.cancel('automatic');
          track.play();
        } else track.pause();
        updateControls();break;
      }
    }
  }, events);
  root.addEventListener('keydown', event => {
    if (event.ctrlKey || event.metaKey || event.altKey) return;
    if (['Tab','Enter',' ','Escape'].includes(event.key)) {
      setInput('keyboard');
      if (!cardPress && event.target instanceof HTMLElement && rail.contains(event.target)) {
        keyboardFocus = event.target;
        syncReadingHold();
        clearWheelInput();
      }
    }
    if(event.key==='Escape'&&help?.open){help.close('escape',true);event.preventDefault();event.stopPropagation();return;}
    if(help?.contains(event.target)){
      if(event.key==='Escape'){departure?.cancel('keyboard');if(hover.escape())event.preventDefault();}
      return;
    }
    departure?.cancel('keyboard');
    if (event.key === 'Escape' && hover.escape()) {
      clearWheelInput();
      event.preventDefault();
    }
  }, { ...events, capture: true });
  root.addEventListener('focusin', event => {
    const node = event.target;
    if (!(node instanceof HTMLElement) || cardPress || changingCards || help?.contains(node)) return;
    if (!node.matches(':focus-visible')) return;
    setInput('keyboard');
    if (!departure?.pointerHeld) departure?.cancel('focus');
    if (!rail.contains(node)) return;
    keyboardFocus = node;
    syncReadingHold();
    clearWheelInput();entrance.cancel('focus');
    const card = node.closest<HTMLElement>('.ar-tool-card');
    if (!card || cardsState.expandedId) return;
    const id = card.dataset.toolId!;
    if (track.active) track.focus(id);
    hover.focus(id);
  }, events);
  root.addEventListener('pointerdown', event => {
    if (!event.isPrimary || event.button !== 0 || !(event.target instanceof Element)) return;
    releaseCardPress();
    const touch = event.pointerType !== 'mouse';
    const nextInput = touch ? 'touch' : 'mouse';
    if (!rail.contains(event.target)) {
      if (root.dataset.departure === 'returning') departure?.cancel('pointer');
      // A control tap changes the guidance without moving any pressed button.
      setInput(nextInput, touch);
      return;
    }

    const button = event.target.closest<HTMLButtonElement>('button[data-action="detail"]');
    cardPress = { pointerId: event.pointerId, button, touch, x: event.clientX, y: event.clientY };
    root.dataset.detailPressed = button?.dataset.toolId ?? 'rail';
    if (root.dataset.departure === 'returning') {
      if (event.target.closest('.ar-tool-card')) departure?.holdPress(true);
      else departure?.cancel('pointer');
    }
    syncReadingHold();
    hover.press();
    // Keep a real detail button in place through pointerup and native click.
    if (touch && !button) track.setTouchInput(true);
    setInput(nextInput, !!button);
    cancelPositionRestore();
    clearWheelInput();
    if (!button) {
      entrance.cancel('pointer');
      options.onInteraction?.();
    }
  }, { ...events, capture: true });
  window.addEventListener('pointermove', event => {
    if (cardPress?.pointerId !== event.pointerId || !cardPress.button) return;
    const moved = Math.hypot(event.clientX - cardPress.x, event.clientY - cardPress.y) > 8;
    if (moved && (cardPress.touch || !(event.target instanceof Node && cardPress.button.contains(event.target)))) releaseCardPress();
  }, { ...events, passive: true });
  window.addEventListener('pointercancel', event => {
    if (cardPress?.pointerId === event.pointerId) releaseCardPress();
  }, events);
  window.addEventListener('pointerup', event => {
    if (cardPress?.pointerId !== event.pointerId) return;
    if (!cardPress.button || !(event.target instanceof Node && cardPress.button.contains(event.target))) releaseCardPress();
    else pressRelease = window.setTimeout(releaseCardPress, cardPress.touch ? 350 : 150);
  }, events);
  window.addEventListener('blur', () => { releaseCardPress();clearKeyboardFocus(); }, events);
  // Recognize the returning mouse before the rail evaluates this same move.
  root.addEventListener('pointermove',event=>{if(event.pointerType==='mouse'&&!event.buttons&&(event.movementX||event.movementY))setInput('mouse');},{...events,capture:true});
  fine.addEventListener('change', updateControls, events);
  reduced.addEventListener('change', () => {
    clearWheelInput();
    updateControls();
  }, events);
  root.addEventListener('focusout', event => {
    if (event.target === keyboardFocus) clearKeyboardFocus();
  }, events);
  select.addEventListener('change', () => selectCategory(select.value), events);
  window.addEventListener('resize', () => { releaseCardPress();clearKeyboardFocus();clearWheelInput(); }, events);
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) { releaseCardPress();clearKeyboardFocus();clearWheelInput(); }
  }, events);
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
    if (disposed || mode !== 'cards' || !rail.clientWidth) return;
    const previousOverflow = cardOverflow;
    const size = interactionRegion.measureHorizontal();
    cardOverflow = size.overflow;
    if (railWidth === size.viewportWidth) {
      if (previousOverflow !== cardOverflow) updateControls();
      return;
    }
    railWidth = size.viewportWidth;
    clearWheelInput();
    restorePosition(cardsState.position);
    updateControls();
    changed();
  });
  observer.observe(rail);
  renderRail();

  function applyLandingWheel() {
    if (!landingWheel || !entrance.ready) return;
    const input = landingWheel;
    landingWheel = undefined;
    if (root.dataset.entranceReason !== 'wheel' || !rail.contains(input.slot)) return;
    const region = interactionRegion.inspect();
    if (!region.active || !region.overflow || region.owner === 'overlay') return;
    track.wheel(input.amount, input.axis, region.contentWidth - region.viewportWidth);
  }

  root.addEventListener('wheel', event => {
    if (disposed || !event.cancelable || event.defaultPrevented) return;
    const region = interactionRegion.inspect(event);
    const leaving = departure?.owns && region.departure !== 'returning';
    if (region.owner !== 'cards' || (track.active && !trackContext.active) || leaving) {
      releaseWheelInput();
      return;
    }
    const limit = region.contentWidth - region.viewportWidth;
    const delta = normalizeCardWheel(event, parseFloat(getComputedStyle(rail).lineHeight) || 20, region.viewportWidth);
    if (Math.max(Math.abs(delta.x), Math.abs(delta.y)) < .1) return;
    const now = performance.now();
    const axis = wheelGesture.take(delta.x, delta.y, now);
    if (!axis) return;
    const amount = axis === 'horizontal' ? delta.x : delta.y;
    // A finite row keeps valid input even when clamped at its first or last card.
    // A gesture with a locked axis also owns the samples on its ignored axis.
    event.preventDefault();
    if (Math.abs(amount) < .1 || cardPress) return;

    wheelBounds = region.visibleBounds;
    cancelPositionRestore();
    departure?.cancel('wheel');
    setInput('mouse');
    help?.close('wheel');
    if (region.action === 'collapse-pinned-and-scroll') hover.clearPin();
    hover.wheel({ x: event.clientX, y: event.clientY });
    options.onInteraction?.();

    if (region.entrance === 'playing' || region.entrance === 'preparing') {
      const slot = slots()[0];
      if (!slot) return;
      const previous = landingWheel?.axis === axis && Math.sign(landingWheel.amount) === Math.sign(amount) ? landingWheel.amount : 0;
      landingWheel = { axis, slot, amount: clamp(previous + amount, -region.viewportWidth, region.viewportWidth) };
      if (region.entrance === 'playing') entrance.shorten('wheel');
      else entrance.cancel('wheel');
      return;
    }
    track.wheel(amount, axis, limit, now);
  }, { ...events, passive: false });
  root.addEventListener('pointermove', event => {
    if (event.pointerType !== 'mouse' || !wheelBounds) return;
    const { left, right, top, bottom } = wheelBounds;
    if (event.clientX < left || event.clientX >= right || event.clientY < top || event.clientY >= bottom) releaseWheelInput();
  }, { ...events, passive: true });
  root.addEventListener('pointerleave', releaseWheelInput, events);

  // Optional read-only overlay uses the same live geometry as wheel ownership.
  const regionDebug = new URLSearchParams(location.search).get('debug') === '1'
    ? createCardRegionDebug(root, interactionRegion) : undefined;

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
    presentTrack(context: CardTrackContext) {
      const different = JSON.stringify(context) !== JSON.stringify(trackContext);
      if (trackContext.active && !context.active) { releaseCardPress();clearKeyboardFocus(); }
      trackContext = context;
      if (help?.open && !help.popover && !context.active) help.close('left-section');
      syncTrack();if (different) updateControls();
    },
    closeOverview() { if (!disposed && mode === 'all') returnToCards(); },
    restoreState(snapshot: ToolBrowserSnapshot) {
      if (disposed) return;
      withCardsHeld(() => {
        releaseCardPress();clearKeyboardFocus();
        help?.close('state-restored');
        departure?.cancel('state-restored');
        clearWheelInput();hover.cancel('state-restored');entrance.cancel('state-restored');
        const category = categories.some(item => item.id === snapshot.cards.category) ? snapshot.cards.category : 'all';
        const cards = getTrackCards(category);
        cardsState = structuredClone({ ...snapshot.cards, category,
          activeId: cards.some(card => card.id === snapshot.cards.activeId) ? snapshot.cards.activeId : cards[0]!.id,
          expandedId: cards.some(card => card.id === snapshot.cards.expandedId) ? snapshot.cards.expandedId : null });
        if (snapshot.mode === 'all') { mode = 'all';showAllTools(false); } else returnToCards(false, false);
        if (snapshot.track) track.restore(snapshot.track, visibleCards().map(card => card.id));
        hover.restorePinned(cardsState.expandedId);
        syncTrack();
      });
    },
    refresh() { if (!disposed && !departure?.owns && mode === 'cards') restorePosition(cardsState.position); },
    dispose() {
      if (disposed) return;
      regionDebug?.dispose();
      releaseCardPress();clearKeyboardFocus();
      help?.dispose();
      departure?.dispose();
      disposed = true;hover.dispose();track.dispose();entrance.dispose();listeners.abort();observer.disconnect();clearCardViews();
      cancelPositionRestore();
      root.remove();
    },
  };
}
