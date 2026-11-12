import { portfolio } from '../content/portfolio';
import type { Project } from '../content/portfolio';

function escape(value: string) {
  return value.replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[character]!);
}

function safeLink(url: string) {
  try {
    const parsed = new URL(url);
    return ['https:', 'http:', 'mailto:'].includes(parsed.protocol) ? escape(parsed.href) : undefined;
  } catch { return undefined; }
}

const arrow = '<span aria-hidden="true">↗</span>';
const mark = '<svg class="mark" viewBox="0 0 32 32" fill="none" aria-hidden="true"><path d="m16 3 12 7v13l-12 7-12-7V10Z M4 10l12 7 12-7 M16 17v13" /></svg>';
const star = '<svg viewBox="0 0 80 80" fill="none" aria-hidden="true"><path d="M40 8v64M8 40h64M17.4 17.4l45.2 45.2M17.4 62.6l45.2-45.2" stroke="currentColor" stroke-width="7" stroke-linecap="round"/></svg>';

function projectCard(project: Project, index: number) {
  return `<article class="work-card" data-kind="${project.kind}">
    <button class="work-open" type="button" data-project="${escape(project.id)}" aria-label="查看${escape(project.title)}的作品详情">
      <span class="work-image"><img src="${escape(project.image)}" alt="${escape(project.imageAlt)}" width="680" height="680" loading="lazy" decoding="async" /><span class="work-kind">${escape(project.badge)}</span><span class="work-image-label">${escape(project.englishTitle)}</span><span class="work-image-arrow" aria-hidden="true">↗</span></span>
      <span class="work-meta"><span class="work-index">${String(index + 1).padStart(2, '0')}</span><span>${escape(project.category)}</span><span class="work-detail-label">查看详情 ${arrow}</span></span>
      <span class="work-title">${escape(project.title)}</span>
      <span class="work-summary">${escape(project.summary)}</span>
    </button>
    <ul class="work-tags" aria-label="作品关键词">${project.tags.map((tag) => `<li>${escape(tag)}</li>`).join('')}</ul>
  </article>`;
}

export function createPortfolio(root: HTMLElement, onDialogChange: (open: boolean) => void) {
  const listeners = new AbortController();
  const options = { signal: listeners.signal };
  const content = portfolio;
  document.title = `${content.alias.split(' / ')[0]} · ${content.name} | AIGC 与 AI 动画`;

  root.innerHTML = `
    <a class="skip-link" href="#about">跳到自我介绍</a>
    <header class="site-header">
      <div class="site-shell header-inner">
        <a class="identity" href="#home" aria-label="${escape(content.brand)}，返回首页">${mark}<span>${escape(content.brand)}<small>PERSONAL PORTFOLIO</small></span></a>
        <nav class="site-nav" aria-label="主导航"><a href="#home" aria-current="location"><span>01</span> 首页</a><a href="#about"><span>02</span> 关于我</a><a href="#works"><span>03</span> 作品集</a></nav>
      </div>
    </header>
    <main id="main-content">
      <section class="cover site-shell" id="home" aria-labelledby="cover-title">
        <div class="cover-grid">
          <div class="cover-copy">
            <p class="eyebrow"><span class="tiny-star" aria-hidden="true">${star}</span> AIGC CREATOR / AI ANIMATION</p>
            <h1 id="cover-title" tabindex="-1">${escape(content.cover.title[0])}<span>${escape(content.cover.title[1])}</span></h1>
            <p class="cover-intro">${escape(content.cover.introduction)}</p>
            <div class="cover-actions"><a class="primary-link" href="#about">认识我 <span aria-hidden="true">↓</span></a><a class="text-link" href="#works">浏览作品 ${arrow}</a></div>
            <p class="cover-signature"><span aria-hidden="true">—</span> 影像、想象与交互的交汇处</p>
          </div>
          <div class="cover-visual">
            <figure class="composition" aria-label="庭院习作，个人作品集动态封面">
              <div class="scene-frame"><div class="scene-host" id="scene-host" data-render-state="loading"><p id="scene-notice" class="scene-notice" hidden></p></div></div>
              <figcaption class="scene-caption"><span><span class="caption-dot" aria-hidden="true"></span> 庭院习作</span><span>${escape(content.cover.note)}</span></figcaption>
            </figure>
            <div class="tools" role="group" aria-label="封面画面设置">
              <span class="tools-label">停一会儿，看风经过。</span>
              <div class="tool-actions"><div class="mode-controls" role="group" aria-label="渲染模式"><button type="button" data-mode="native" aria-pressed="false">正常画面</button><button type="button" data-mode="pixel" aria-pressed="true">像素预览</button></div><button type="button" id="motion-control" class="motion-control">暂停动效</button></div>
            </div>
          </div>
        </div>
        <div class="cover-bottom"><a href="#about" class="scroll-link">往下走走 <span aria-hidden="true">↓</span></a><span>AI MOVES. IDEAS GROW.</span><span class="cover-coordinate" aria-hidden="true">01 — 03</span></div>
      </section>

      <section class="about-section" id="about" aria-labelledby="about-title" tabindex="-1">
        <div class="site-shell section-inner">
          <div class="section-kicker"><span>02 / ABOUT ME</span><span>从这里，认识我</span></div>
          <div class="about-grid">
            <div class="about-heading"><h2 id="about-title">${escape(content.about.heading[0])}<br>${escape(content.about.heading[1])}</h2><div class="about-garden" aria-hidden="true"><span class="garden-flower">${star}</span><span class="garden-note">STILL GROWING,<br>ALWAYS CURIOUS.</span><span class="garden-pixel"></span></div></div>
            <div class="about-copy"><p class="about-greeting">${escape(content.name)}<span>${escape(content.alias)}</span></p>${content.profilePending ? '<p class="pending-label">个人介绍 · 待补充</p>' : ''}${content.about.paragraphs.map((text) => `<p class="about-paragraph">${escape(text)}</p>`).join('')}<dl class="about-facts">${content.about.facts.map((fact) => `<div><dt>${escape(fact.label)}</dt><dd>${escape(fact.value)}</dd></div>`).join('')}</dl><ul class="capabilities" aria-label="创作能力">${content.about.capabilities.map((item) => `<li>${escape(item)}</li>`).join('')}</ul><p class="alias-note">${escape(content.about.aliasNote)}</p></div>
          </div>
        </div>
      </section>

      <section class="works-section site-shell" id="works" aria-labelledby="works-title" tabindex="-1">
        <div class="section-kicker"><span>03 / SELECTED WORK</span><span>把想法，变成看得见的东西</span></div>
        <div class="works-heading"><h2 id="works-title">想象的切片。<br>创作的现场。</h2><p>从一帧画面，到一个可以进入的世界。<br>影像、视觉与交互实验，在这里相遇。</p></div>
        <div class="work-filters" role="group" aria-label="作品分类"><button type="button" data-filter="all" aria-pressed="true">全部 / ALL</button><button type="button" data-filter="visual" aria-pressed="false">影像与视觉</button><button type="button" data-filter="interactive" aria-pressed="false">交互实验</button></div>
        <div class="works-grid">${content.projects.map(projectCard).join('')}</div>
        <p class="concept-note">标记为「概念样片」的画面用于本次网页视觉设计，后续可替换为实际项目。</p>
        <p id="work-status" class="sr-only" role="status" aria-live="polite"></p>
      </section>
    </main>
    <footer class="site-footer site-shell"><div class="footer-top"><p>保持好奇，<br><span>继续生长。</span></p><a class="back-to-top" href="#home">回到顶部 <span aria-hidden="true">↑</span></a></div><div class="footer-bottom"><span>${escape(content.brand)} <span aria-hidden="true">✳</span> ${escape(content.profilePending ? 'PERSONAL PORTFOLIO' : content.name)}</span><div class="contact-links">${content.contactLinks.map((link) => { const url = safeLink(link.url); return url ? `<a href="${url}" target="_blank" rel="noopener noreferrer">${escape(link.label)} ${arrow}</a>` : ''; }).join('')}</div><span>一点一滴，慢慢成形。</span></div></footer>
    <dialog class="project-dialog" id="project-dialog" aria-labelledby="project-title" aria-describedby="project-description"><div class="project-detail"><button class="dialog-close" type="button" aria-label="关闭作品详情" autofocus>关闭 <span aria-hidden="true">×</span></button><div id="project-detail-content"></div></div></dialog>
    <p id="render-status" class="sr-only" role="status" aria-live="polite"></p>
  `;

  const dialog = root.querySelector<HTMLDialogElement>('#project-dialog')!;
  const detail = root.querySelector<HTMLDivElement>('#project-detail-content')!;
  root.querySelectorAll<HTMLButtonElement>('[data-project]').forEach((button) => {
    button.addEventListener('click', () => {
      const project = content.projects.find((item) => item.id === button.dataset.project);
      if (!project) return;
      const link = project.link && safeLink(project.link.url);
      detail.innerHTML = `<p class="eyebrow">${escape(project.englishTitle)}${project.concept ? ' / 概念样片' : ''}</p><h2 id="project-title">${escape(project.title)}</h2><p id="project-description" class="project-summary">${escape(project.summary)}</p><img class="project-image" src="${escape(project.image)}" alt="${escape(project.imageAlt)}" width="680" height="680" /><div class="project-story"><p>${escape(project.description)}</p><dl>${project.facts.map((fact) => `<div><dt>${escape(fact.label)}</dt><dd>${escape(fact.value)}</dd></div>`).join('')}</dl></div>${project.video ? `<figure class="project-film"><p class="project-section-label">MOTION STUDY / 动效放映</p><video controls playsinline muted preload="none" poster="${escape(project.image)}" aria-label="${escape(project.title)}，无声动效演示"><source src="${escape(project.video.src)}" type="video/mp4" />你的浏览器暂不支持此视频。</video><figcaption><span>${escape(project.video.caption)}</span><a href="${escape(project.video.src)}" download>下载片段 ↓</a></figcaption></figure>` : ''}${project.frames?.length ? `<p class="project-section-label">FRAME NOTES / 画面切片</p><div class="project-frames">${project.frames.map((frame) => `<figure><img src="${escape(frame.src)}" alt="${escape(frame.caption)}" loading="lazy" width="680" height="680" /><figcaption>${escape(frame.caption)}</figcaption></figure>`).join('')}</div>` : ''}<div class="project-actions"><a class="primary-link" href="${project.kind === 'interactive' ? '#home' : '#works'}" data-return-cover>${project.kind === 'interactive' ? '回到封面体验' : '返回作品集'} <span aria-hidden="true">${project.kind === 'interactive' ? '↑' : '↗'}</span></a>${link ? `<a class="text-link" href="${link}" target="_blank" rel="noopener noreferrer">${escape(project.link!.label)} ${arrow}</a>` : ''}</div>`;
      dialog.showModal();
      document.documentElement.classList.add('dialog-open');
      onDialogChange(true);
    }, options);
  });
  dialog.querySelector<HTMLButtonElement>('.dialog-close')!.addEventListener('click', () => dialog.close(), options);
  dialog.addEventListener('click', (event) => {
    if (event.target === dialog) dialog.close();
    if (event.target instanceof Element && event.target.closest('[data-return-cover]')) dialog.close();
  }, options);
  dialog.addEventListener('close', () => {
    dialog.querySelectorAll('video').forEach((video) => video.pause());
    document.documentElement.classList.remove('dialog-open');
    onDialogChange(false);
  }, options);

  const filters = [...root.querySelectorAll<HTMLButtonElement>('[data-filter]')];
  const worksGrid = root.querySelector<HTMLElement>('.works-grid')!;
  const cards = [...worksGrid.querySelectorAll<HTMLElement>('.work-card')];
  const reveal = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      (entry.target as HTMLElement).dataset.reveal = 'visible';
      reveal.unobserve(entry.target);
    });
  }, { rootMargin: '0px 0px -30px 0px', threshold: 0 });
  cards.forEach((card) => { card.dataset.reveal = 'pending'; reveal.observe(card); });
  filters.forEach((button) => button.addEventListener('click', () => {
    filters.forEach((filter) => filter.setAttribute('aria-pressed', String(filter === button)));
    let count = 0;
    cards.forEach((card) => {
      card.hidden = button.dataset.filter !== 'all' && card.dataset.kind !== button.dataset.filter;
      if (!card.hidden) count++;
    });
    worksGrid.dataset.filtered = String(button.dataset.filter !== 'all');
    worksGrid.dataset.count = String(count);
    root.querySelector('#work-status')!.textContent = `显示 ${count} 个项目。`;
  }, options));

  const sections = [...root.querySelectorAll<HTMLElement>('main > section[id]')];
  const navigation = [...root.querySelectorAll<HTMLAnchorElement>('.site-nav a')];
  const observer = new IntersectionObserver(() => {
    const current = sections.filter((section) => section.getBoundingClientRect().top <= window.innerHeight * 0.4).at(-1) ?? sections[0];
    navigation.forEach((link) => {
      if (link.hash === `#${current.id}`) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    });
  }, { rootMargin: '-15% 0px -55% 0px', threshold: 0 });
  sections.forEach((section) => observer.observe(section));

  // Replaced markup and fonts can move a deep link after the browser's first hash jump.
  const hash = window.location.hash;
  const anchorFrame = ['#home', '#about', '#works'].includes(hash) ? requestAnimationFrame(() => root.querySelector(hash)?.scrollIntoView({ behavior: 'instant' })) : undefined;

  return {
    dispose() {
      dialog.querySelectorAll('video').forEach((video) => video.pause());
      listeners.abort();
      observer.disconnect();
      reveal.disconnect();
      if (anchorFrame !== undefined) cancelAnimationFrame(anchorFrame);
      if (dialog.open) dialog.close();
      document.documentElement.classList.remove('dialog-open');
    },
  };
}
