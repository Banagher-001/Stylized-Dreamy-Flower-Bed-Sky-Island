/** Reuse the original inscription nodes in normal document flow. */
export function createReaderFlow(panel: HTMLElement) {
  const attributes = ['style', 'aria-hidden', 'hidden', 'inert', 'disabled', 'title'] as const;
  let saved: Map<HTMLElement, (string | null)[]> | undefined;
  return {
    get active() { return !!saved; },
    set(enabled: boolean) {
      if (enabled && !saved) {
        const nodes = [panel, ...panel.querySelectorAll<HTMLElement>('*')];
        saved = new Map(nodes.map(node => [node, attributes.map(name => node.getAttribute(name))]));
        panel.dataset.readingLayout = 'flow';
        panel.setAttribute('aria-hidden', 'false');
        for (const article of panel.querySelectorAll<HTMLElement>('[data-reading-station],[data-film-station],[data-experiment-station]')) {
          article.hidden = false;article.inert = false;article.setAttribute('aria-hidden', 'false');
        }
        for (const node of panel.querySelectorAll<HTMLElement>('h2,[class$="-eyebrow"],[class$="-body"],[data-reading-ink],[data-film-ink],[data-experiment-ink],.film-media')) node.removeAttribute('aria-hidden');
        for (const button of panel.querySelectorAll<HTMLButtonElement>('button')) button.disabled = false;
      } else if (!enabled && saved) {
        for (const [node, values] of saved) attributes.forEach((name, i) => {
          const value = values[i]!;if (value === null) node.removeAttribute(name);else node.setAttribute(name, value);
        });
        saved = undefined;delete panel.dataset.readingLayout;
      }
    },
  };
}
