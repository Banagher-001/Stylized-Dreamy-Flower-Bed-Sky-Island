import courtyardImage from '../assets/courtyard.png';
import courtyardFilm from '../assets/courtyard-motion.mp4';
import courtyardFrameA from '../assets/courtyard-keyframe-00.png';
import courtyardFrameB from '../assets/courtyard-keyframe-03.png';
import signalImage from '../assets/signal-garden.webp';
import formImage from '../assets/liquid-form.webp';

export interface Project {
  id: string;
  title: string;
  englishTitle: string;
  category: string;
  kind: 'visual' | 'interactive';
  badge: string;
  summary: string;
  description: string;
  image: string;
  imageAlt: string;
  tags: string[];
  facts: { label: string; value: string }[];
  link?: { label: string; url: string };
  video?: { src: string; caption: string };
  frames?: { src: string; caption: string }[];
  concept?: boolean;
}

export interface PortfolioContent {
  brand: string;
  name: string;
  alias: string;
  profilePending: boolean;
  cover: { title: [string, string]; introduction: string; note: string };
  about: { heading: [string, string]; paragraphs: string[]; facts: { label: string; value: string }[]; capabilities: string[]; aliasNote: string };
  projects: Project[];
  contactLinks: { label: string; url: string }[];
}

/** Biography supplied by the owner. Generated concept studies are labeled separately. */
export const portfolio: PortfolioContent = {
  brand: 'sakan.',
  name: '张辰翰',
  alias: 'sakan / 萨坎',
  profilePending: false,
  cover: {
    title: ['sakan.', '让想象，动起来。'],
    introduction: '张辰翰 / 萨坎\nAIGC 创作者，专注 AI 动画。\n用新的工具，构建画面、故事与可以进入的世界。',
    note: '一方水池，几段旧时光。',
  },
  about: {
    heading: ['好奇心驱动，', '想象力成形。'],
    paragraphs: [
      '我是一名专注 AIGC 的创作者，目前在枫叶互动制作 AI 动画，此前曾在游族网络工作。',
      '我的创作横跨 AI 图像、AI 视频与 Vibe Coding。熟悉市面上的主流 AI 图像与视频工具，也用代码把想法变成可以交互的体验。',
    ],
    facts: [
      { label: 'NOW / 现在', value: '枫叶互动 · AI 动画制作' },
      { label: 'BEFORE / 此前', value: '游族网络' },
      { label: 'PRACTICE / 创作', value: 'AI 图像 / AI 视频 / Vibe Coding' },
    ],
    capabilities: ['AI ANIMATION', 'GENERATIVE IMAGE', 'VIBE CODING'],
    aliasNote: 'sakan（萨坎）这个化名，取自《战锤 40K》的角色。',
  },
  projects: [{
    id: 'signal-garden',
    title: '异星来信',
    englishTitle: 'SIGNAL GARDEN / 001',
    category: '世界构建 · 视觉方向',
    kind: 'visual',
    badge: 'AI VISUAL / 概念样片',
    summary: '一扇通向未知的门，一颗悬在风里的星。',
    description: '围绕“遗迹、信号与生命”展开的一张概念主视觉：石质圆环与漂浮的镜面球体构成叙事中心，用冷暖光线与微小人物建立空间尺度。这张图为本次网页设计生成的视觉方向示意，尚未替换为个人实际项目。',
    image: signalImage,
    imageAlt: '粉色天空与浅水花园中，巨型石环包围悬浮的镜面球体，远处站着一个微小人物',
    tags: ['概念视觉', '世界构建', '叙事氛围'],
    facts: [
      { label: '呈现形式', value: '概念主视觉 / 世界观氛围研究' },
      { label: '画面关键词', value: '遗迹 / 镜面信号 / 粉色天光' },
      { label: '当前状态', value: '网页设计用 AI 概念样片，非个人实际项目' },
    ],
    concept: true,
  }, {
    id: 'courtyard',
    title: '庭院习作',
    englishTitle: 'THE LITTLE COURTYARD',
    category: '交互场景',
    kind: 'interactive',
    badge: 'INTERACTIVE / 可交互作品',
    summary: '把光影、水面与微风，放进一座可以停留的小庭院。',
    description: '以固定的俯视镜头，把八边形水池、石柱、草花和树影放进同一座小院。水面、草花与树影轻微流动，也可以停下来，观察一个瞬间。首页封面就是这件作品的实时版本。',
    image: courtyardImage,
    imageAlt: '草绿庭院中的八边形喷泉、三根石柱、粉紫色小花与深绿树影',
    tags: ['风格化场景', '实时交互', '像素美学'],
    facts: [
      { label: '项目类型', value: '风格化网页场景' },
      { label: '视觉语言', value: '固定视角 / 柔和色彩 / 像素质感' },
      { label: '体验方式', value: '画面模式切换 / 整场景播放与暂停' },
    ],
    video: { src: courtyardFilm, caption: '00:12 / 无声场景动效' },
    frames: [{ src: courtyardFrameA, caption: 'FRAME 01 / 一瞬的水光' }, { src: courtyardFrameB, caption: 'FRAME 02 / 风经过草花' }],
  }, {
    id: 'liquid-form',
    title: '流动标本',
    englishTitle: 'LIQUID FORM / 003',
    category: '材质实验 · 视觉方向',
    kind: 'visual',
    badge: 'AI VISUAL / 概念样片',
    summary: '在金属与玻璃之间，捕捉一种尚未命名的形态。',
    description: '用液态铬与半透明玻璃组成一个悬浮的环结，在淡紫色和鼠尾草绿之间探索材质、反射与形态。这张图为本次网页设计生成的视觉方向示意，用来呈现不同幅面和材质题材的作品展示方式。',
    image: formImage,
    imageAlt: '淡紫背景上，半透明玻璃与拉丝金属交织成悬浮的环结，下方是浅绿基座',
    tags: ['材质研究', '形态实验', '概念视觉'],
    facts: [
      { label: '呈现形式', value: '材质与形态研究' },
      { label: '画面关键词', value: '液态金属 / 半透明玻璃 / 柔和反射' },
      { label: '当前状态', value: '网页设计用 AI 概念样片，非个人实际项目' },
    ],
    concept: true,
  }],
  contactLinks: [],
};
