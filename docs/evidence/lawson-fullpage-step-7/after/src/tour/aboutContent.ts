/** Owner-supplied facts from this conversation, arranged for the first pillar.
 * No dates, previous job responsibilities, project credits or contacts supplied.
 * Content stays separate from camera/scroll coordinates and the reference page.
 */
export const aboutContent = {
  A1: {
    kind: 'identity', label: '身份', title: 'sakan',
    name: '张辰翰 / 萨坎', role: '专注 AIGC 的创作者。',
    note: '化名取自《战锤 40K》的角色。',
  },
  A2: {
    kind: 'experience', label: '经历', title: '现在与此前',
    entries: [
      { label: '现在', english: 'NOW', company: '枫叶互动', role: 'AI 动画制作' },
      { label: '此前', english: 'BEFORE', company: '游族网络' },
    ],
  },
  A3: {
    kind: 'practice', label: '创作', title: '让想法成形',
    directions: [
      { name: '图像构建', detail: 'AI 图像' },
      { name: '影像制作', detail: 'AI 视频与动画' },
      { name: '交互表达', detail: 'Vibe Coding' },
    ],
    cue: '继续向下，进入 AI 影像。',
  },
} as const;
