export function element<K extends keyof HTMLElementTagNameMap>(tag: K, className = '', text?: string): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

export function button(text: string, className = 'ar-button'): HTMLButtonElement {
  const node = element('button', className, text);
  node.type = 'button';
  return node;
}

export const clamp = (value: number, low: number, high: number) => Math.max(low, Math.min(high, value));
