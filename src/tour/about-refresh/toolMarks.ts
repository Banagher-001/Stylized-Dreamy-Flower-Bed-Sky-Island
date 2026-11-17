import mark0 from '../../assets/tool-marks/midjourney.svg';
import mark1 from '../../assets/tool-marks/comfyui.svg';
import mark2 from '../../assets/tool-marks/kling.svg';
import mark3 from '../../assets/tool-marks/blender.svg';
import mark4 from '../../assets/tool-marks/jimeng.svg';
import mark5 from '../../assets/tool-marks/hailuo.svg';
import mark6 from '../../assets/tool-marks/chatgpt.svg';
import mark7 from '../../assets/tool-marks/gemini.svg';
import mark8 from '../../assets/tool-marks/maya.svg';
import mark9 from '../../assets/tool-marks/houdini.svg';
import mark10 from '../../assets/tool-marks/cinema-4d.svg';
import mark11 from '../../assets/tool-marks/3ds-max.svg';
import mark12 from '../../assets/tool-marks/unreal-engine.svg';
import mark13 from '../../assets/tool-marks/substance-painter.svg';
import mark14 from '../../assets/tool-marks/quixel-mixer.svg';
import mark15 from '../../assets/tool-marks/marvelous-designer.svg';
import mark16 from '../../assets/tool-marks/photoshop.svg';
import mark17 from '../../assets/tool-marks/after-effects.svg';
import mark18 from '../../assets/tool-marks/premiere-pro.svg';
import mark19 from '../../assets/tool-marks/illustrator.svg';
import mark20 from '../../assets/tool-marks/jianying.svg';
import mark21 from '../../assets/tool-marks/vibe-coding.svg';

/** Local vector marks; original purpose symbols are not represented as official logos. */
export const toolMarks: Readonly<Record<string, { src: string; kind: 'brand' | 'family' | 'purpose' }>> = {
  'midjourney': { src: mark0, kind: 'brand' },
  'comfyui': { src: mark1, kind: 'brand' },
  'kling': { src: mark2, kind: 'brand' },
  'blender': { src: mark3, kind: 'brand' },
  'jimeng': { src: mark4, kind: 'brand' },
  'hailuo': { src: mark5, kind: 'brand' },
  'chatgpt': { src: mark6, kind: 'brand' },
  'gemini': { src: mark7, kind: 'brand' },
  'maya': { src: mark8, kind: 'brand' },
  'houdini': { src: mark9, kind: 'brand' },
  'cinema-4d': { src: mark10, kind: 'brand' },
  '3ds-max': { src: mark11, kind: 'purpose' },
  'unreal-engine': { src: mark12, kind: 'brand' },
  'substance-painter': { src: mark13, kind: 'purpose' },
  'quixel-mixer': { src: mark14, kind: 'purpose' },
  'marvelous-designer': { src: mark15, kind: 'purpose' },
  'photoshop': { src: mark16, kind: 'brand' },
  'after-effects': { src: mark17, kind: 'brand' },
  'premiere-pro': { src: mark18, kind: 'brand' },
  'illustrator': { src: mark19, kind: 'brand' },
  'jianying': { src: mark20, kind: 'family' },
  'vibe-coding': { src: mark21, kind: 'purpose' },
};
