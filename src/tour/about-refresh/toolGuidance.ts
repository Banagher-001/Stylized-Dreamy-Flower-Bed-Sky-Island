import type { CardTrackActivity } from './createCardTrack';

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
  pinned: boolean; preview: boolean; userPaused: boolean; activity: CardTrackActivity;
  hover: boolean; overflow: boolean; autoAvailable: boolean; autoEnabled: boolean; reduced: boolean;
}): ToolGuidance {
  const { input, overflow } = state;
  const wheel = input === 'mouse' && overflow;
  let key: string, hint: string;
  if (state.help) {
    key = 'help';hint = '操作说明已展开';
  } else if (['preparing', 'playing'].includes(state.entrance)) {
    key = 'entrance';hint = wheel ? '卡片入场中 · 滚轮可接管' : '卡片入场中';
  } else if (state.departure === 'returning') {
    key = state.returnPaused ? 'return-paused' : 'returning';
    hint = state.returnPaused ? '卡片已停住 · 可点击查看' : input === 'mouse' && !state.reduced
      ? '返回中 · 可移入卡面暂停' : '正在返回原浏览位置';
  } else if (['exiting', 'departed'].includes(state.departure)) {
    key = 'departing';hint = '正在离开工具卡片';
  } else if (state.pinned) {
    key = 'pinned';hint = input === 'keyboard' ? '已固定 · Esc 收起详情' : input === 'touch'
      ? '已展开 · 点按收起详情' : wheel ? '已固定 · 滚轮换卡' : '已固定 · 点击收起详情';
  } else if (state.preview && input !== 'touch') {
    key = 'preview';hint = input === 'keyboard' ? 'Enter 固定阅读 · Esc 收起' : '点击固定阅读';
  } else if (!overflow) {
    key = 'fits';hint = '本类已全部展示';
  } else if (input === 'keyboard') {
    key = 'keyboard';hint = 'Tab 选择 · Enter 操作';
  } else if (input === 'touch') {
    key = 'touch';hint = '左右滑卡 · 点按详情';
  } else if (state.activity === 'manual') {
    key = 'manual';hint = '卡牌区内滚轮横移';
  } else if (state.activity === 'automatic') {
    key = 'automatic';hint = '自动展示中 · 滚轮可接管';
  } else if (state.userPaused) {
    key = 'paused';hint = '已暂停 · 滚轮仍可横移';
  } else {
    key = 'native';hint = '卡牌区内滚轮横移';
  }

  const leave = input === 'keyboard' ? '按 Tab 前往「继续浏览 AI 影像」' : input === 'touch'
    ? '上下滑动继续浏览 ↓' : wheel ? '移出卡牌区，再滚动继续 ↓' : '上下滚动继续浏览 ↓';
  let browse = '当前分类一屏可读，可直接打开详情。';
  if (overflow) {
    if (input === 'touch') browse = '左右滑动卡片，也可点按「上一张」或「下一张」。';
    else if (input === 'keyboard') browse = '用 Tab 选择卡片或前后按钮，按 Enter 或空格操作。';
    else if (state.reduced) browse = '卡牌区内滚轮直接横移。触控板也可左右滑动。';
    else {
      const afterWheel = state.autoAvailable && state.autoEnabled ? '停滚后平缓接回自动展示。' : '停滚后缓慢停下。';
      browse = `卡牌区内滚轮横移，滚得越快，横移越快。${afterWheel}`;
    }
  }
  const read = input === 'keyboard' ? '选中详情按钮后按 Enter 或空格，按 Esc 收起详情或说明。'
    : input === 'touch' ? '点按「展开详情」阅读，再点「收起详情」。'
      : state.hover ? '移入卡片预览全文，点击「固定阅读」可停留阅读。' : '点击「展开详情」阅读，再点击「收起详情」。';
  const continueReading = input === 'keyboard' ? '用 Tab 选中「继续浏览 AI 影像」后按 Enter。'
    : input === 'touch' ? '上下滑动页面，或点按「继续浏览 AI 影像」。' : wheel
      ? '移出卡牌区再滚动，或点击「继续浏览 AI 影像」。' : '上下滚动页面，或点击「继续浏览 AI 影像」。';
  const rows: ToolHelpRow[] = [
    { title: '浏览卡片', text: browse },
    { title: '阅读详情', text: read },
    { title: '继续浏览', text: continueReading },
  ];
  if (state.autoAvailable) rows.push({ title: '自动展示', text: '用本区按钮暂停或继续卡片展示，暂停时仍可手动翻卡。' });
  return { state: key, hint, leave, rows, note: state.autoAvailable ? '页面顶部的导览控制整页镜头。' : '' };
}
