import { createBottleOceanExperience } from './createBottleOceanExperience';
import { createLawsonExperience } from './createLawsonExperience';
import { projects, resolveProjectEntry } from './projectContent';
import type { EmbeddedProjectId, EmbeddedProjectState } from './projectContent';

/** The cover and the original page share one window. Only its current project can own a frame. */
export function createExperimentScene(stage: HTMLElement, initialProject: EmbeddedProjectId, interact: () => void) {
  const mount = stage.querySelector<HTMLElement>('.experiment-scene-mount')!;
  const feedback = stage.querySelector<HTMLElement>('.experiment-scene-status')!;
  const retry = stage.querySelector<HTMLButtonElement>('.experiment-scene-retry')!;
  const listeners = new AbortController();
  let cover = stage.querySelector<HTMLImageElement>('.experiment-scene-cover')!;
  let projectId = initialProject, active = false;

  function present(state: EmbeddedProjectState, message?: string) {
    const { title } = projects[projectId];
    stage.dataset.sceneState = state;
    mount.setAttribute('aria-busy', String(state === 'loading' || state === 'slow'));
    feedback.textContent = {
      prepared: '进入作品窗口后载入场景。',
      loading: `正在载入${title}…`,
      slow: `${title}载入较慢，可以继续等待或重新载入。`,
      error: `${message ?? `${title}暂时无法载入`}，可在此重新载入。`,
      ready: message ?? `${title}已就绪。`,
    }[state];
  }

  function options(id: EmbeddedProjectId) {
    const wanted = () => active && projectId === id;
    return {
      container: mount, entry: resolveProjectEntry(id)!, wanted, interact,
      status(state: EmbeddedProjectState, message?: string) { if (wanted()) present(state, message); },
    };
  }
  const experiences = {
    lawson: createLawsonExperience(options('lawson')),
    'bottle-ocean': createBottleOceanExperience(options('bottle-ocean')),
  };
  function prime() {
    if (!cover.hasAttribute('src')) cover.src = projects[projectId].cover.src;
  }
  function setActive(next: boolean) {
    if (next) {
      active = true;
      prime();
      experiences[projectId].mount();
    } else if (active) {
      active = false;
      experiences[projectId].unmount();
      present('prepared');
    }
  }

  retry.addEventListener('click', () => {
    if (!active) return;
    stage.focus({ preventScroll: true });
    experiences[projectId].retry();
  }, { signal: listeners.signal });
  present('prepared');
  return {
    prime,
    setActive,
    get projectId() { return projectId; },
    select(id: EmbeddedProjectId) {
      if (id === projectId) return;
      setActive(false);projectId = id;
      const { width, height, alt } = projects[id].cover;
      const next = new Image(width, height);
      next.alt = alt;next.decoding = 'async';next.className = cover.className;
      cover.replaceWith(next);cover = next;
      stage.setAttribute('aria-label', `${projects[id].title}场景窗口`);
      present('prepared');prime();
    },
    dispose() {
      active = false;listeners.abort();
      for (const experience of Object.values(experiences)) experience.dispose();
    },
  };
}
