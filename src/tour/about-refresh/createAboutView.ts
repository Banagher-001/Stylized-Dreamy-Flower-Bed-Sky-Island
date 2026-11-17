import { aboutRefreshContent } from './content';
import { createToolBrowser } from './createToolBrowser';
import { button, element } from './dom';
import type { AboutLayout, AboutSnapshot, AboutStationId, AboutViewOptions, CardDepartureContext, CardEntranceContext, CardTrackContext } from './types';
import './aboutRefresh.css';

let instanceCount = 0;

/** Reusable DOM content. Camera coordinates and main-site scroll stay with the host. */
export function createAboutView(host: HTMLElement, options: AboutViewOptions = {}) {
  const prefix = `about-refresh-${++instanceCount}`;
  const listeners = new AbortController();
  const root = element('section', 'about-refresh');
  root.dataset.layout = 'stable';
  root.setAttribute('aria-label', '关于我');
  let disposed = false;
  let station: AboutStationId = 'A1';
  let continuous = false;
  const changed = () => { if (!disposed) options.onLayoutChange?.(); };
  let continueHint:HTMLElement|undefined;let leaveHint:string=aboutRefreshContent.controls['hint-leave']!;
  const tools = createToolBrowser({...options,onToolLeaveHint(text){leaveHint=text;if(continueHint&&continueHint.textContent!==text)continueHint.textContent=text;options.onToolLeaveHint?.(text);}});
  const screens = new Map<AboutStationId, HTMLElement>();

  function screen(id: AboutStationId, className: string, eyebrow: string, title: string) {
    const section = element('section', 'ar-screen');
    section.dataset.aboutStation = id;
    const content = element('div', `ar-content ${className}`);
    const heading = element('h2', 'ar-title', title);
    heading.id = `${prefix}-${id}-title`;
    section.setAttribute('aria-labelledby', heading.id);
    content.append(element('p', 'ar-eyebrow', eyebrow), heading);
    section.append(content);screens.set(id, section);root.append(section);
    return content;
  }

  const identity = aboutRefreshContent.identity;
  const identityBody = screen('A1', 'ar-reading-card ar-identity', identity.eyebrow, identity.title);
  identityBody.append(element('p', 'ar-role', identity.role));
  for (const paragraph of identity.paragraphs) identityBody.append(element('p', 'ar-introduction', paragraph));
  const keywords = element('ul', 'ar-keywords');
  for (const keyword of identity.keywords) keywords.append(element('li', '', keyword));
  identityBody.append(keywords);
  const identityDetails = element('details', 'ar-native-details');
  identityDetails.dataset.aboutDetails = 'identity';
  identityDetails.append(element('summary', '', '关于这个名字'), element('p', '', identity.alias));
  identityBody.append(identityDetails);

  const experience = aboutRefreshContent.experience;
  const experienceBody = screen('A2', 'ar-reading-card ar-experience', experience.eyebrow, experience.title);
  const entries = element('ol', 'ar-experiences');
  for (const entry of experience.entries) {
    const item = element('li');
    item.append(element('span', 'ar-experience-label', entry.label));
    const description = element('div');
    description.append(element('p', 'ar-company', entry.company));
    if ('role' in entry) description.append(element('p', 'ar-duty', entry.role));
    item.append(description);entries.append(item);
  }
  const process = element('ol', 'ar-process');
  process.setAttribute('aria-label', '制作环节');
  for (const stage of experience.process) process.append(element('li', '', stage.name));
  const experienceDetails = element('details', 'ar-native-details');
  experienceDetails.dataset.aboutDetails = 'experience';
  experienceDetails.append(element('summary', '', '制作环节与教育背景'));
  const processDetails = element('dl', 'ar-process-details');
  for (const stage of experience.process) processDetails.append(element('dt', '', stage.name), element('dd', '', stage.detail));
  const education = element('div', 'ar-education');
  education.append(element('p', 'ar-education-label', '教育背景'), element('p', '', experience.education));
  experienceDetails.append(processDetails, education);
  experienceBody.append(entries, process, experienceDetails);

  const toolsCopy = aboutRefreshContent.tools;
  const toolsBody = screen('A3', 'ar-tools-content', toolsCopy.eyebrow, toolsCopy.title);
  const toolsHeader = element('header', 'ar-tools-header');
  toolsHeader.append(...toolsBody.children);
  toolsHeader.append(element('p', 'ar-tools-introduction', toolsCopy.introduction));
  const continueSlot = element('div', 'ar-continue-slot');
  if (options.onContinue) {
    const hint = element('p', 'ar-hint', leaveHint);continueHint=hint;
    const continueButton = button(aboutRefreshContent.controls['continue-reading'], 'ar-button ar-button-primary');
    continueButton.dataset.action = 'continue';
    continueButton.addEventListener('click', () => { tools.closeHelp('continue');tools.cancelEntrance('continue');options.onInteraction?.();options.onContinue?.(); }, { signal: listeners.signal });
    continueSlot.append(hint, continueButton);
  } else continueSlot.setAttribute('aria-hidden', 'true');
  toolsBody.append(toolsHeader, tools.root, continueSlot);

  for (const details of [identityDetails, experienceDetails]) {
    details.addEventListener('toggle', changed, { signal: listeners.signal });
    details.addEventListener('click', event => {
      if ((event.target as Element).closest('summary')) options.onInteraction?.();
    }, { signal: listeners.signal });
  }
  host.append(root);

  function setStation(next: AboutStationId, silent = false) {
    if (disposed || !screens.has(next)) return;
    if(next!=='A3'&&!silent)tools.closeHelp('station');
    const focused = document.activeElement;
    const wasInHiddenScreen = focused instanceof HTMLElement && [...screens].some(([id, node]) => id !== next && node.contains(focused));
    station = next;root.dataset.station = next;
    for (const [id, section] of screens) {
      const hidden = !continuous && id !== next;
      section.hidden = hidden;section.inert = hidden;
      section.setAttribute('aria-hidden', String(hidden));
    }
    if (wasInHiddenScreen && !continuous && !silent) {
      const heading = screens.get(next)!.querySelector<HTMLElement>('h2')!;
      heading.tabIndex = -1;heading.focus({ preventScroll: true });
    }
    if (next === 'A3' && !silent) tools.refresh();
    if (!silent) changed();
  }
  setStation('A1');

  return {
    root,
    get station() { return station; },
    setStation,
    setContinuous(enabled: boolean, silent = false) {
      if (disposed || continuous === enabled) return;
      continuous = enabled;root.dataset.continuous = String(enabled);
      setStation(station, silent);
    },
    get stations() { return [...screens.values()]; },
    get toolsElement() { return tools.root; },
    get toolsEntranceReady() { return tools.entranceReady; },
    presentToolsEntrance(context: CardEntranceContext) { tools.presentEntrance(context); },
    presentToolsTrack(context: CardTrackContext) { tools.presentTrack(context); },
    presentToolsDeparture(context: CardDepartureContext) { tools.presentDeparture(context); },
    cancelToolsDeparture(reason?: string) { tools.cancelDeparture(reason); },
    cancelToolsHelp(reason?:string){tools.closeHelp(reason);},
    cancelToolsEntrance(reason?: string) { tools.cancelEntrance(reason); },
    mountToolsInto(target?: HTMLElement) {
      if (disposed) return;
      if (target) target.append(tools.root);else toolsBody.insertBefore(tools.root, continueSlot);
    },
    closeToolOverview() { tools.closeOverview(); },
    setLayout(layout: AboutLayout, availableHeight?: number) {
      if (disposed) return;
      root.dataset.layout = layout;
      if (availableHeight !== undefined) root.style.setProperty('--ar-available-height', `${Math.max(0, availableHeight)}px`);
    },
    measure() {
      const content = screens.get(station)!.querySelector<HTMLElement>('.ar-content')!;
      const box = content.getBoundingClientRect();
      return { station, width: root.clientWidth, contentHeight: box.height, requiredHeight: box.height + 48 };
    },
    captureState(): AboutSnapshot {
      return { station, identityOpen: identityDetails.open, experienceOpen: experienceDetails.open, tools: tools.captureState() };
    },
    restoreState(snapshot: AboutSnapshot) {
      if (disposed) return;
      identityDetails.open = snapshot.identityOpen;
      experienceDetails.open = snapshot.experienceOpen;
      setStation(snapshot.station);
      tools.restoreState(snapshot.tools);
      changed();
    },
    dispose() {
      if (disposed) return;
      disposed = true;listeners.abort();tools.dispose();root.remove();
    },
  };
}
