import { button,clamp,element } from './dom';
import { toolHelpCopy } from './toolGuidance';
import type { ToolGuidance } from './toolGuidance';
import './toolHelp.css';

/** A single nonmodal explanation, independent of the cards' preserve-3d chain. */
export function createToolHelp(options: {
  prefix: string; root: HTMLElement; rail: HTMLElement; controls: HTMLElement;
  changed(open: boolean, reason: string): void;
}) {
  const {root,rail,controls} = options;
  const events = new AbortController(),abort={signal:events.signal};
  const trigger=button(toolHelpCopy.open,'ar-button ar-tool-help-trigger');trigger.dataset.action='help';
  const panel=element('section','ar-tool-help-panel');panel.id=`${options.prefix}-help`;panel.hidden=true;panel.setAttribute('role','region');
  const heading=element('h3','ar-tool-help-title',toolHelpCopy.title);heading.id=`${panel.id}-title`;heading.tabIndex=-1;
  panel.setAttribute('aria-labelledby',heading.id);trigger.setAttribute('aria-controls',panel.id);trigger.setAttribute('aria-expanded','false');
  const closeButton=button('×','ar-button ar-tool-help-close');closeButton.dataset.action='help-close';closeButton.setAttribute('aria-label',toolHelpCopy.close);
  const scrollHint=element('p','ar-tool-help-scroll-hint','说明可上下滚动');scrollHint.hidden=true;
  const headingGroup=element('div');headingGroup.append(heading,scrollHint);
  const header=element('div','ar-tool-help-header');header.append(headingGroup,closeButton);
  const list=element('dl','ar-tool-help-list'),note=element('p','ar-tool-help-note');panel.append(header,list,note);
  let open=false,disposed=false,signature='',openedLayout='';
  function popup() {return root.closest<HTMLElement>('.about-refresh')?.dataset.layout==='immersive' && innerWidth>=1180 && parseFloat(getComputedStyle(root).fontSize)<=24;}
  function layoutKey() {const h=root.closest<HTMLElement>('.about-refresh');return [innerWidth,innerHeight,getComputedStyle(root).fontSize,h?.dataset.layout,h?.dataset.largeText].join('|');}
  function place() {
    scrollHint.hidden=true;
    panel.dataset.presentation=popup()?'popover':'inline';
    if(!popup()) {panel.removeAttribute('style');return;}
    const box=root.getBoundingClientRect(),r=rail.getBoundingClientRect(),c=controls.getBoundingClientRect(),t=trigger.getBoundingClientRect();
    const headerBottom=document.querySelector('.tour-header')?.getBoundingClientRect().bottom??0;
    const footerTop=document.querySelector('.tour-footer')?.getBoundingClientRect().top??innerHeight;
    const top=Math.max(16,headerBottom+12,r.top+8),bottom=Math.min(innerHeight-16,footerTop-12,c.top-8,r.bottom-8);
    const width=Math.min(360,box.width,innerWidth-32);
    panel.style.width=`${width}px`;panel.style.maxHeight=`${Math.max(120,bottom-top)}px`;
    const left=clamp(t.right-width,Math.max(16,box.left),Math.min(innerWidth-16,box.right)-width);
    const y=clamp(t.top-panel.getBoundingClientRect().height-12,top,Math.max(top,bottom-panel.getBoundingClientRect().height));
    panel.style.left=`${left-box.left}px`;panel.style.top=`${y-box.top}px`;
    scrollHint.hidden=panel.scrollHeight<=panel.clientHeight+1;
  }
  function close(reason='close',restoreFocus=false) {
    if(!open)return;
    open=false;panel.hidden=true;trigger.textContent=toolHelpCopy.open;trigger.setAttribute('aria-expanded','false');root.dataset.helpOpen='false';
    options.changed(false,reason);
    if(restoreFocus && trigger.isConnected && !trigger.closest('[hidden],[inert]'))trigger.focus({preventScroll:true});
  }
  function show(keyboard=false) {
    if(disposed || open)return;
    open=true;panel.dataset.presentation=popup()?'popover':'inline';panel.hidden=false;trigger.textContent=toolHelpCopy.collapse;trigger.setAttribute('aria-expanded','true');root.dataset.helpOpen='true';
    options.changed(true,'open');openedLayout=layoutKey();place();
    if(keyboard){heading.focus({preventScroll:true});if(!popup())heading.scrollIntoView({block:'nearest',behavior:'instant'});}
  }
  trigger.addEventListener('click',e=>{if(open)close('toggle',true);else show(e.detail===0);},abort);
  closeButton.addEventListener('click',()=>close('close',true),abort);
  document.addEventListener('pointerdown',e=>{if(open&&popup()&&!panel.contains(e.target as Node)&&!trigger.contains(e.target as Node))close('outside');},{...abort,capture:true});
  panel.addEventListener('focusout',e=>{if(open&&popup()&&e.relatedTarget&&!panel.contains(e.relatedTarget as Node)&&!trigger.contains(e.relatedTarget as Node))close('focus-left');},abort);
  window.addEventListener('resize',()=>close('resize'),abort);
  document.addEventListener('visibilitychange',()=>{if(document.hidden)close('hidden');},abort);
  const observer=new ResizeObserver(()=>{if(open&&openedLayout!==layoutKey())close('layout');});observer.observe(root);observer.observe(controls);
  root.dataset.helpOpen='false';
  return {
    trigger,panel,get open(){return open;},get popover(){return popup();},
    contains(target: EventTarget|null){return target instanceof Node&&(trigger.contains(target)||panel.contains(target));},
    close,
    update(model: ToolGuidance) {
      if(disposed)return;
      if(open&&openedLayout&&openedLayout!==layoutKey()){close('layout');return;}
      const next=JSON.stringify([model.rows,model.note]);
      if(next!==signature){
        signature=next;list.replaceChildren(...model.rows.map(row=>{const item=element('div','ar-tool-help-item');item.append(element('dt','',`${row.title}：`),element('dd','',row.text));return item;}));
        if(note.textContent!==model.note)note.textContent=model.note;note.hidden=!model.note;
        if(open)place();
      }
    },
    dispose(){if(disposed)return;close('disposed');disposed=true;observer.disconnect();events.abort();panel.remove();trigger.remove();},
  };
}
