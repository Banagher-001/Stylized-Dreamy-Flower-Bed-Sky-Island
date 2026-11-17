export type ToolInput = 'mouse' | 'touch' | 'keyboard';
export interface ToolHelpRow { readonly title: string; readonly text: string; }
export interface ToolGuidance {
  readonly state: string; readonly hint: string; readonly leave: string;
  readonly rows: readonly ToolHelpRow[]; readonly note: string;
}
export const toolHelpCopy = {
  open: '操作说明', collapse: '收起说明', title: '如何浏览工具卡片', close: '关闭操作说明',
  catalog: '已列出全部工具，返回后接续原浏览位置。',
} as const;

/** Capability and user intent decide instructions; no animation clock or DOM. */
export function toolGuidance(state: {
  input: ToolInput; help: boolean; entrance: string; departure: string; returnPaused: boolean;
  pinned: boolean; preview: boolean; automatic: boolean; running: boolean; program: boolean;
  hover: boolean; overflow: boolean; autoAvailable: boolean; immersive: boolean;
}): ToolGuidance {
  const {input} = state;
  const program = state.program && input!=='touch';
  let key: string, hint: string;
  if(state.help) { key='help';hint='操作说明已展开'; }
  else if(['preparing','playing'].includes(state.entrance)) { key='entrance';hint='卡片入场中 · 可直接操作'; }
  else if(state.departure==='returning') { key=state.returnPaused?'return-paused':'returning';hint=state.returnPaused?'卡片已停住 · 可点击查看':input==='touch'?'正在返回原浏览位置':'返回中 · 可移入卡面暂停'; }
  else if(['exiting','departed'].includes(state.departure)) { key='departing';hint='正在离开工具卡片'; }
  else if(state.pinned) { key='pinned';hint=input==='keyboard'?'已固定 · Esc 收起详情':input==='touch'?'已固定 · 上下滑动页面':'已固定 · 滚轮浏览页面'; }
  else if(state.preview) { key='preview';hint=input==='keyboard'?'Enter 固定阅读 · Esc 收起':input==='touch'?'点按固定阅读':state.automatic?'临时阅读 · 移开后继续展示':'临时阅读 · 移开后保持暂停'; }
  else if(input==='keyboard') { key='keyboard';hint='Tab 选择 · Enter 操作'; }
  else if(input==='touch') { key='touch';hint=state.overflow?'左右滑动 · 点按查看详情':'点按查看完整介绍'; }
  else if(program && state.automatic) { key='automatic';hint='自动展示已开启 · 滚轮调速'; }
  else if(program && state.running) { key='manual';hint='正在手动浏览 · 悬停查看详情'; }
  else if(program) { key='paused';hint='已暂停 · 滚轮仍可浏览'; }
  else { key='native';hint=state.hover?'悬停查看详情 · 点击固定':'前后浏览 · 点击查看详情'; }
  const rows: ToolHelpRow[] = [
    {title:'浏览卡片',text:program?'卡排内滚轮控制方向与速度，滚得越快，横移越快。':state.overflow?input==='touch'?'左右滑动卡片，或使用上一张、下一张浏览。':'使用上一张、下一张浏览；触控板可左右滑动。':'当前分类已完整展示，可直接查看详情。'},
    {title:'阅读详情',text:state.hover && input==='mouse'?'移入查看全文，点击「固定阅读」后可停留阅读。':input==='touch'?'点按「展开详情」查看全文，再次点按可收起。':'使用「展开详情」查看全文，「收起详情」返回卡片。'},
  ];
  if(state.autoAvailable) rows.push({title:'自动展示',text:'暂停自动后仍可手动浏览；用按钮继续自动展示。'});
  rows.push(
    {title:'继续浏览',text:input==='touch'?'上下滑动页面，或选择「继续浏览 AI 影像」。':'移到卡片外滚动，或继续浏览 AI 影像。固定阅读时，滚轮用于页面。'},
    {title:'返回卡片',text:state.immersive&&input!=='touch'?'滚回第三屏接续原位置；返回时移入卡面可暂时停住。':'返回卡片浏览会接续原分类与位置。'},
    {title:'键盘操作',text:'Tab 选择，Enter 或空格操作，Esc 收起详情或关闭说明。'},
  );
  const leave = input==='keyboard'?'选择「继续浏览 AI 影像」前往下一部分':input==='touch'?'上下滑动继续浏览 ↓':state.pinned?'上下滚动浏览页面，或继续查看 AI 影像 ↓':program?'移到卡片外滚动，继续浏览 ↓':'上下滚动继续浏览 ↓';
  return {state:key,hint,leave,rows,note:state.autoAvailable?'本区自动展示控制卡片；顶部导览控制整页镜头。':''};
}
