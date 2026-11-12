import cover from '../assets/courtyard-orb-cover.webp';
import motion from '../assets/courtyard-motion.mp4';
import frame00 from '../assets/courtyard-keyframe-00.png';
import frame03 from '../assets/courtyard-keyframe-03.png';

/** This repository's actual scene. No external project credit or publication implied. */
export const courtyardProject = {
  title: '庭院习作', kind: '交互网页场景',
  summary: '一座可以停留、切换和探索的庭院。',
  cover: { src: cover, width: 1440, height: 793, alt: '深色石柱与粉紫小花环绕蓝白水潭，中央浅蓝水球轻悬于石台上方' },
  introduction: '以三根石柱串起介绍、影像与交互。滚动靠近，在柱身之间阅读；也可以暂时停下，观察水面与草花。',
  features: ['随滚动靠近石柱，沿柱身逐段阅读', '在正常画面与像素画面之间切换', '自由播放或暂停庭院环境动效', '观察悬浮水球、石沿反射与落水波纹', '打开作品查看层，再回到原阅读位置'],
  clip: { src: motion, label: '固定视角动效片段', note: '庭院早期固定视角版本 · 12秒 · 无声', width: 680, height: 680 },
  frames: [
    { src: frame00, alt: '早期固定视角庭院，水面与悬浮球的起始画面', label: '固定视角 · 片段起始' },
    { src: frame03, alt: '同一早期庭院片段中的另一帧水面与悬浮球', label: '固定视角 · 片段采样' },
  ],
} as const;
export const experimentContent = {
  C1: { title: '从想法到交互', body: '我也使用 Vibe Coding，把视觉构想做成网页与交互体验。', steps: ['想法', '画面', '交互'] },
  C3: { title: '让想象，动起来。', body: '从一幅画面，到一个可以进入的世界。', cue: '继续向下，回到水潭。' },
} as const;
