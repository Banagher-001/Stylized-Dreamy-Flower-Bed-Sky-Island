import type { AboutContent, CategoryFilter, ToolCard } from './types';

/** Approved step-1 public copy. Runtime data has no dependency on docs/evidence. */
export const aboutRefreshContent = {
  "identity": {
    "eyebrow": "01 / 关于我",
    "title": "sakan / 张辰翰",
    "role": "AIGC 影像创作者",
    "paragraphs": [
      "现于枫叶互动制作 AI 动画，曾在游族网络。",
      "结合 AI 生成、三维制作与后期处理，探索画面风格与镜头表达，让创意从概念走向画面。"
    ],
    "keywords": [
      "AI 动画",
      "三维视觉",
      "交互创作"
    ],
    "alias": "sakan，也叫萨坎。化名取自《战锤 40K》的角色。"
  },
  "experience": {
    "eyebrow": "经历与制作",
    "title": "让创意进入制作。",
    "entries": [
      {
        "label": "现在",
        "company": "枫叶互动",
        "role": "AI 动画制作"
      },
      {
        "label": "此前",
        "company": "游族网络"
      },
      {
        "label": "工作室实践",
        "company": "869 三维美学工作室",
        "role": "3D / AIGC 方向助理设计师"
      }
    ],
    "process": [
      {
        "name": "概念与分镜",
        "detail": "梳理视觉方向、场景氛围与镜头表达。"
      },
      {
        "name": "AI 视觉生成",
        "detail": "运用生成工具探索画面，并进行迭代调整。"
      },
      {
        "name": "三维与材质",
        "detail": "完成模型、场景、材质与灯光制作。"
      },
      {
        "name": "剪辑合成",
        "detail": "衔接画面修整、合成与最终输出。"
      }
    ],
    "education": "辽宁师范大学 · 动画本科 · 2023—2027"
  },
  "tools": {
    "eyebrow": "工具与方法",
    "title": "工具，让想法继续向前。",
    "introduction": "使用主流 AI 创作工具，并结合三维、材质与后期完成制作。"
  },
  "categories": [
    {
      "id": "G1",
      "name": "AI 图像与工作流",
      "cardIds": [
        "midjourney",
        "jimeng",
        "comfyui"
      ]
    },
    {
      "id": "G2",
      "name": "AI 视频",
      "cardIds": [
        "kling",
        "hailuo"
      ]
    },
    {
      "id": "G3",
      "name": "创作辅助",
      "cardIds": [
        "chatgpt",
        "gemini"
      ]
    },
    {
      "id": "G4",
      "name": "三维制作",
      "cardIds": [
        "blender",
        "maya",
        "houdini",
        "cinema-4d",
        "3ds-max",
        "unreal-engine"
      ]
    },
    {
      "id": "G5",
      "name": "材质与资产",
      "cardIds": [
        "substance-painter",
        "quixel-mixer",
        "marvelous-designer"
      ]
    },
    {
      "id": "G6",
      "name": "后期与视觉制作",
      "cardIds": [
        "photoshop",
        "after-effects",
        "premiere-pro",
        "illustrator",
        "jianying"
      ]
    },
    {
      "id": "G7",
      "name": "交互实践",
      "cardIds": [
        "vibe-coding"
      ]
    }
  ],
  "cards": [
    {
      "id": "midjourney",
      "name": "Midjourney",
      "use": "概念探索、风格推演与氛围图生成",
      "detail": "通过提示词、构图与风格调整探索视觉方向，生成概念和氛围参考，再对画面进行筛选、细化与后期处理。",
      "tags": [
        "概念探索",
        "氛围图像"
      ],
      "category": "G1",
      "kind": "tool",
      "recommendationOrder": 1,
      "categoryOrder": 1,
      "initialEntryRank": 1,
      "mark": "MJ"
    },
    {
      "id": "comfyui",
      "name": "ComfyUI",
      "use": "节点生成流程与画面控制的组织",
      "detail": "搭建并调整节点工作流，结合模型与 LoRA 组织生成过程，探索画面控制与细化方式，并衔接后期处理。",
      "tags": [
        "节点流程",
        "画面控制"
      ],
      "category": "G1",
      "kind": "tool",
      "recommendationOrder": 2,
      "categoryOrder": 3,
      "initialEntryRank": 2,
      "mark": "CF"
    },
    {
      "id": "kling",
      "name": "可灵",
      "use": "视频镜头生成与画面运动探索",
      "detail": "围绕场景描述与参考画面探索视频镜头，调整运动方向和画面节奏，筛选适合后续剪辑、整理的生成结果。",
      "tags": [
        "视频生成",
        "镜头运动"
      ],
      "category": "G2",
      "kind": "tool",
      "recommendationOrder": 3,
      "categoryOrder": 1,
      "initialEntryRank": 3,
      "mark": "可"
    },
    {
      "id": "blender",
      "name": "Blender",
      "use": "模型制作、场景搭建与灯光渲染",
      "detail": "结合建模、材质与灯光完成场景搭建和渲染，调整资产结构、空间关系与画面氛围，将视觉构想推进为三维画面。",
      "tags": [
        "场景搭建",
        "灯光渲染"
      ],
      "category": "G4",
      "kind": "tool",
      "recommendationOrder": 4,
      "categoryOrder": 1,
      "initialEntryRank": 4,
      "mark": "BL"
    },
    {
      "id": "jimeng",
      "name": "即梦",
      "use": "图像生成、风格探索与画面调整",
      "detail": "围绕创作需求探索图像和视觉风格，通过描述与参考画面反复调整生成方向，筛选适合继续细化的结果。",
      "tags": [
        "图像生成",
        "风格探索"
      ],
      "category": "G1",
      "kind": "tool",
      "recommendationOrder": 5,
      "categoryOrder": 2,
      "initialEntryRank": null,
      "mark": "梦"
    },
    {
      "id": "hailuo",
      "name": "海螺",
      "use": "短镜头生成、动作与氛围探索",
      "detail": "用于短镜头、动作表现和画面氛围的生成探索，通过调整描述与参考素材比较不同结果，再衔接剪辑处理。",
      "tags": [
        "短片探索",
        "动作表现"
      ],
      "category": "G2",
      "kind": "tool",
      "recommendationOrder": 6,
      "categoryOrder": 2,
      "initialEntryRank": null,
      "mark": "海"
    },
    {
      "id": "chatgpt",
      "name": "ChatGPT",
      "use": "创意梳理、文案推敲与编程辅助",
      "detail": "辅助梳理创意、文字结构和制作思路，在编程时协助理解需求、拆分步骤与排查问题，再结合实际结果修订。",
      "tags": [
        "创意梳理",
        "编程辅助"
      ],
      "category": "G3",
      "kind": "tool",
      "recommendationOrder": 7,
      "categoryOrder": 1,
      "initialEntryRank": null,
      "mark": "GPT"
    },
    {
      "id": "gemini",
      "name": "Gemini",
      "use": "创作资料梳理与多模态思路辅助",
      "detail": "结合文字与图像梳理创作资料，辅助理解参考内容、比较视觉方向和整理思路，为后续生成与制作提供参考。",
      "tags": [
        "资料梳理",
        "多模态"
      ],
      "category": "G3",
      "kind": "tool",
      "recommendationOrder": 8,
      "categoryOrder": 2,
      "initialEntryRank": null,
      "mark": "GE"
    },
    {
      "id": "maya",
      "name": "Maya",
      "use": "模型编辑、角色动画与镜头调整",
      "detail": "用于模型编辑、角色动画与镜头调整，围绕动作、时间节奏和画面关系反复预览，衔接三维制作中的不同环节。",
      "tags": [
        "模型编辑",
        "角色动画"
      ],
      "category": "G4",
      "kind": "tool",
      "recommendationOrder": 9,
      "categoryOrder": 2,
      "initialEntryRank": null,
      "mark": "MA"
    },
    {
      "id": "houdini",
      "name": "Houdini",
      "use": "程序化建模、场景变化与效果探索",
      "detail": "通过节点组织程序化建模和场景变化，探索可调整的几何与效果流程，便于在不同参数之间比较和修改结果。",
      "tags": [
        "程序建模",
        "节点流程"
      ],
      "category": "G4",
      "kind": "tool",
      "recommendationOrder": 10,
      "categoryOrder": 3,
      "initialEntryRank": null,
      "mark": "HO"
    },
    {
      "id": "cinema-4d",
      "name": "Cinema 4D",
      "use": "三维构成、动态设计与视觉表达",
      "detail": "围绕三维构成与动态设计组织模型、材质和灯光，调整画面层次与运动节奏，完成视觉表达与渲染输出。",
      "tags": [
        "动态设计",
        "三维构成"
      ],
      "category": "G4",
      "kind": "tool",
      "recommendationOrder": 11,
      "categoryOrder": 4,
      "initialEntryRank": null,
      "mark": "C4D"
    },
    {
      "id": "3ds-max",
      "name": "3ds Max",
      "use": "三维资产建模与空间场景的组织",
      "detail": "用于三维资产建模和空间组织，处理模型形体、材质与灯光关系，配合场景搭建完成画面预览和渲染调整。",
      "tags": [
        "资产建模",
        "空间组织"
      ],
      "category": "G4",
      "kind": "tool",
      "recommendationOrder": 12,
      "categoryOrder": 5,
      "initialEntryRank": null,
      "mark": "3D"
    },
    {
      "id": "unreal-engine",
      "name": "Unreal Engine",
      "use": "实时场景整合、灯光与效果预览",
      "detail": "将模型、材质与灯光整合到实时场景中，调整空间层次、气氛和镜头取景，通过即时预览迭代场景表现。",
      "tags": [
        "实时场景",
        "灯光预览"
      ],
      "category": "G4",
      "kind": "tool",
      "recommendationOrder": 13,
      "categoryOrder": 6,
      "initialEntryRank": null,
      "mark": "UE"
    },
    {
      "id": "substance-painter",
      "name": "Substance 3D Painter",
      "use": "材质绘制、表面细节与质感调整",
      "detail": "围绕 PBR 材质绘制贴图，调整金属、粗糙度、磨损与污渍等表面特征，让三维资产的质感和细节更完整。",
      "tags": [
        "材质绘制",
        "表面细节"
      ],
      "category": "G5",
      "kind": "tool",
      "recommendationOrder": 14,
      "categoryOrder": 1,
      "initialEntryRank": null,
      "mark": "SP"
    },
    {
      "id": "quixel-mixer",
      "name": "Quixel Mixer",
      "use": "材质混合、表面分层与质感探索",
      "detail": "组合不同材质与表面层次，调整颜色、粗糙度和细节分布，探索适合资产与场景氛围的材质变化。",
      "tags": [
        "材质混合",
        "表面分层"
      ],
      "category": "G5",
      "kind": "tool",
      "recommendationOrder": 15,
      "categoryOrder": 2,
      "initialEntryRank": null,
      "mark": "QM"
    },
    {
      "id": "marvelous-designer",
      "name": "Marvelous Designer",
      "use": "服装形态、布料模拟与细节调整",
      "detail": "通过版片与布料模拟探索服装形态，调整轮廓、褶皱和垂坠关系，为三维制作提供服装与布料资产。",
      "tags": [
        "服装制作",
        "布料模拟"
      ],
      "category": "G5",
      "kind": "tool",
      "recommendationOrder": 16,
      "categoryOrder": 3,
      "initialEntryRank": null,
      "mark": "MD"
    },
    {
      "id": "photoshop",
      "name": "Photoshop",
      "use": "图像修整、画面合成与视觉优化",
      "detail": "处理图像修整、合成与颜色调整，整理 AI 生成画面的局部细节和视觉关系，为后续制作准备更清晰的素材。",
      "tags": [
        "图像合成",
        "画面修整"
      ],
      "category": "G6",
      "kind": "tool",
      "recommendationOrder": 17,
      "categoryOrder": 1,
      "initialEntryRank": null,
      "mark": "PS"
    },
    {
      "id": "after-effects",
      "name": "After Effects",
      "use": "画面合成、动态设计与效果处理",
      "detail": "组织画面合成、动态元素与视觉效果，调整图层关系、时间节奏和画面衔接，完善影像的整体呈现。",
      "tags": [
        "画面合成",
        "动态设计"
      ],
      "category": "G6",
      "kind": "tool",
      "recommendationOrder": 18,
      "categoryOrder": 2,
      "initialEntryRank": null,
      "mark": "AE"
    },
    {
      "id": "premiere-pro",
      "name": "Premiere Pro",
      "use": "镜头剪辑、节奏调整与影像输出",
      "detail": "整理素材并完成镜头剪辑，调整叙事节奏、画面衔接和声音关系，再按需要完成基础颜色处理与输出。",
      "tags": [
        "镜头剪辑",
        "影像输出"
      ],
      "category": "G6",
      "kind": "tool",
      "recommendationOrder": 19,
      "categoryOrder": 3,
      "initialEntryRank": null,
      "mark": "PR"
    },
    {
      "id": "illustrator",
      "name": "Adobe Illustrator",
      "use": "矢量图形、版式与视觉元素设计",
      "detail": "制作矢量图形、标识与版式元素，调整形状、文字和视觉秩序，为平面表达及后续动态制作准备素材。",
      "tags": [
        "矢量图形",
        "版式设计"
      ],
      "category": "G6",
      "kind": "tool",
      "recommendationOrder": 20,
      "categoryOrder": 4,
      "initialEntryRank": null,
      "mark": "AI"
    },
    {
      "id": "jianying",
      "name": "剪映",
      "use": "素材剪辑、字幕整理与节奏调整",
      "detail": "用于素材剪辑、字幕整理和基础画面调整，快速比较镜头顺序与节奏，完成短片整理及常用格式输出。",
      "tags": [
        "素材剪辑",
        "字幕整理"
      ],
      "category": "G6",
      "kind": "tool",
      "recommendationOrder": 21,
      "categoryOrder": 5,
      "initialEntryRank": null,
      "mark": "剪"
    },
    {
      "id": "vibe-coding",
      "name": "Vibe Coding",
      "use": "把视觉构想做成可操作的网页",
      "detail": "借助 AI 辅助编程推进网页制作，围绕视觉、操作和反馈反复调整，把画面构想转化为可使用的交互体验。",
      "tags": [
        "网页制作",
        "交互探索"
      ],
      "category": "G7",
      "kind": "practice",
      "recommendationOrder": 22,
      "categoryOrder": 1,
      "initialEntryRank": null,
      "mark": "VI"
    }
  ],
  "controls": {
    "hint-desktop": "滚轮加速浏览 · 悬停放大查看",
    "hint-leave": "移到卡片外继续向下浏览 ↓",
    "continue-reading": "继续浏览 AI 影像",
    "pause-auto": "暂停自动展示",
    "resume-auto": "继续自动展示",
    "previous-card": "上一张",
    "next-card": "下一张",
    "show-all": "查看全部工具",
    "return-to-cards": "返回卡片浏览",
    "hint-touch": "左右滑动浏览 · 点按查看详情",
    "expand-detail": "展开详情",
    "collapse-detail": "收起详情",
    "hint-keyboard": "使用前后按钮浏览，按 Enter 展开详情。"
  }
} as const satisfies AboutContent;

export const initialEntryIds: readonly string[] = aboutRefreshContent.cards
  .filter(card => card.initialEntryRank !== null)
  .sort((a, b) => a.initialEntryRank! - b.initialEntryRank!)
  .map(card => card.id);

export function getTrackCards(category: CategoryFilter): readonly ToolCard[] {
  if (category === 'all') return [...aboutRefreshContent.cards].sort((a, b) => a.recommendationOrder - b.recommendationOrder);
  return aboutRefreshContent.cards.filter(card => card.category === category).sort((a, b) => a.categoryOrder - b.categoryOrder);
}

export function getCard(id: string): ToolCard | undefined {
  return aboutRefreshContent.cards.find(card => card.id === id);
}
