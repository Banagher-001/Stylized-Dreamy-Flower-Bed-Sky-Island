import { tourTotalH, waterHold } from './route';
import type { TourSample } from './route';

export const chapterLabels = { overview: '庭院', about: '关于我', films: 'AI影像', experiments: '交互实验', water: '水潭' } as const;
const chapterMarks = { overview: 'GARDEN', about: 'ABOUT', films: 'FILM', experiments: 'LAB', water: 'WATER' } as const;
const chapterKickers = { overview: 'CREATIVE COURTYARD', about: '01 / ABOUT', films: '02 / FILMS', experiments: '03 / EXPERIMENTS', water: 'WATER / STILLNESS' } as const;
const smooth = (value: number) => { const t = Math.max(0, Math.min(1, value));return t * t * t * (t * (t * 6 - 15) + 10); };
const windowOpacity = (h: number, start: number, end: number, fade = .06) => smooth((h - start) / fade) * smooth((end - h) / fade);
const setText = (node: Node, value: string) => { if (node.textContent !== value) node.textContent = value; };

/** All narrative UI derives from the same displayed H as the camera. */
export function sampleTourPresentation(frame: TourSample) {
  const { h, chapter, stage } = frame;
  let kind: 'opening' | 'reading' | 'travel' | 'water' | 'closing' = 'travel';
  let opacity = 1, kicker: string = chapterKickers[chapter], title = frame.title, note = frame.note;
  if (stage === 'S00') {
    kind = 'opening';kicker = 'SAKAN / 张辰翰';opacity = 1 - smooth((h - .35) / .15);
  } else if (stage === 'S99') {
    kind = 'closing';opacity = smooth((h - 11.8) / .15);
  } else if (frame.reading || frame.filmReading || frame.experimentReading) {
    kind = 'reading';title = chapterLabels[chapter];note = '';
    const [start, end] = chapter === 'about' ? [1.3, 3.7] : chapter === 'films' ? [4.4, 8] : [8.7, 11.1];
    opacity = windowOpacity(h, start!, end!);
  } else if (chapter === 'water') {
    kind = 'water';
    if (h < waterHold.start) opacity = windowOpacity(h, 11.1, waterHold.start);
    else if (h <= waterHold.end) opacity = windowOpacity(h, waterHold.start, waterHold.end, .02);
    else opacity = windowOpacity(h, waterHold.end, 11.8);
  } else {
    const [start, end] = stage === 'T01' ? [.5, 1.3] : stage === 'T12' ? [3.7, 4.4] : [8, 8.7];
    opacity = windowOpacity(h, start!, end!);
    if (stage === 'T12') kicker = '01 ↔ 02';
    if (stage === 'T23') kicker = '02 ↔ 03';
  }
  return { kind, opacity, kicker, title, note, mark: chapterMarks[chapter], chapterLabel: chapterLabels[chapter], progress: h / tourTotalH };
}

/** DOM-only presentation. No timers, observers, RAF, or independent scene state. */
export function createTourPresentation(app: HTMLElement, debug: boolean) {
  const heading = app.querySelector<HTMLElement>('.tour-heading')!;
  const title = app.querySelector<HTMLElement>('#tour-title')!, note = app.querySelector<HTMLElement>('#tour-note')!;
  const kicker = app.querySelector<HTMLElement>('.tour-kicker')!, cue = app.querySelector<HTMLElement>('.tour-scroll-cue')!;
  const actions = app.querySelector<HTMLElement>('.tour-ending-actions')!;
  const replayButtons = [...actions.querySelectorAll<HTMLButtonElement>('button')];
  const reference = app.querySelector<HTMLAnchorElement>('#tour-reference')!;
  const brandNote = app.querySelector<HTMLElement>('.tour-brand p')!;
  const phase = app.querySelector<HTMLElement>('#tour-phase')!, percent = app.querySelector<HTMLElement>('#tour-percent')!;
  const progress = app.querySelector<HTMLProgressElement>('#tour-progress')!;
  const nav = [...app.querySelectorAll<HTMLButtonElement>('.tour-stops [data-stop]')];
  const instruction = app.querySelector<HTMLElement>('.tour-instruction')!;
  let signature = '', progressLabel = '', unavailable = false, covered = false, disposed = false;
  let previous: { frame: TourSample; reduced: boolean; settled: boolean; atBottom: boolean } | undefined;

  function update(frame: TourSample, reduced: boolean, settled: boolean, atBottom: boolean) {
    if (disposed) return;
    if (app.querySelector<HTMLElement>('main')?.dataset.readingMode === 'stable') return;
    previous = { frame, reduced, settled, atBottom };
    const state = sampleTourPresentation(frame);
    const end = settled && atBottom && frame.h > 12.29;
    const value = end ? 100 : Math.min(99, Math.max(0, Math.floor(state.progress * 100)));
    if (progress.value !== state.progress) progress.value = state.progress;
    const label = `${state.chapterLabel}，${value}%`;
    if (progressLabel !== label) {
      progressLabel = label;progress.setAttribute('aria-valuetext', label);percent.textContent = `${value}%`;
    }
    // Do not replace stable text nodes while scrolling a held reading window.
    // Apart from selection/accessibility, that can invalidate adjacent SVG veils.
    const key = JSON.stringify([state.kind, state.opacity, state.kicker, state.title, state.note, state.mark, frame.chapter, debug ? frame.stage : '', reduced, covered, unavailable]);
    if (signature === key) return;
    signature = key;
    const opacity = covered ? 0 : state.opacity;
    heading.dataset.kind = state.kind;heading.dataset.opacity = opacity.toFixed(7);
    heading.style.opacity = String(opacity);heading.style.visibility = opacity > .000001 ? 'visible' : 'hidden';
    heading.setAttribute('aria-hidden', String(opacity <= .000001));
    heading.style.transform = reduced ? 'none' : `translateY(${(state.kind === 'closing' ? 6 : -6) * (1 - opacity)}px)`;
    setText(kicker, state.kicker);setText(title, state.title);setText(note, state.note);
    note.hidden = !state.note;cue.hidden = state.kind !== 'opening';
    actions.hidden = state.kind !== 'closing' || covered;
    const actionable = state.kind === 'closing' && state.opacity >= .999999 && !covered && !unavailable;
    actions.inert = !actionable;actions.setAttribute('aria-hidden', String(!actionable));
    for (const button of replayButtons) button.disabled = !actionable;
    reference.hidden = !debug && !unavailable;
    setText(reference, debug ? '返回参考稿 ↗' : '返回参考版本 ↗');
    setText(brandNote, state.kind === 'reading' ? chapterKickers[frame.chapter] : 'CREATIVE COURTYARD');
    setText(phase, debug ? frame.stage : state.mark);
    for (const button of nav) {
      if (button.dataset.stop === frame.chapter) button.setAttribute('aria-current', 'location');
      else button.removeAttribute('aria-current');
    }
    setText(instruction.firstChild!, state.kind === 'closing' ? '向上滚动，回看创作 ' : state.kind === 'opening' ? '滚动进入庭院 ' : '沿庭院继续探索 ');
  }
  const refresh = () => { if (previous) update(previous.frame, previous.reduced, previous.settled, previous.atBottom); };
  return {
    update, replayButtons,
    setCovered(value: boolean) { covered = value;refresh(); },
    setUnavailable(value: boolean) { unavailable = value;reference.hidden = !debug && !value;refresh(); },
    dispose() { disposed = true;previous = undefined; },
  };
}
