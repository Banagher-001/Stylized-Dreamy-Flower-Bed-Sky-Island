# 内容与维护

本版是可审阅的交互作品集候选交付。张辰翰 / sakan（萨坎），现于枫叶互动制作AI动画，此前在游族网络；这几项来自本人提供的信息。真实个人AI影片、职责/制作分镜与联系方式尚未提供。第二柱两件视觉是明确标记的网页设计样片，第三柱是本仓库实际庭院。不要直接把样片标签改成个人作品。

## 内容修改位置

| 内容 | 当前庭院 | 旧参考作品集 |
| --- | --- | --- |
| 姓名、化名、公司、介绍、创作方向 | `src/tour/aboutContent.ts` | `src/content/portfolio.ts`的cover/about |
| 第二柱作品、封面、替代文字、来源与职责 | `src/tour/filmContent.ts`的filmWorks | `src/content/portfolio.ts`的projects |
| 庭院案例、当前封面、早期片段及版本文字 | `src/tour/experimentContent.ts`的courtyardProject | `src/content/portfolio.ts`中的courtyard |
| 第三柱介绍与结语 | `src/tour/experimentContent.ts`的experimentContent | `src/content/portfolio.ts`中的介绍与结语 |
| 真实联系方式 | 当前庭院尚无联系方式模块；获得真实内容后再设计接入 | `src/content/portfolio.ts`的contactLinks，目前为空 |
| 浏览器标题/描述/分享信息 | `index.html`，运行标题另见`src/tour/startTourPrototype.ts` | 共用HTML，运行标题由旧稿入口管理 |
| 分享图 | `public/share-cover.webp` | 共用HTML |

当前庭院和参考稿各有内容配置，修改个人事实时同步两处。没有确认的日期、职位、客户和项目经历不补写。不要把生产代码中的诊断参数当作作品内容。查看器现有行为分别在`createFilmReader.ts`、`createProjectViewer.ts`内，替换静态数据通常不需要动运镜或渲染代码。

## 素材台账与替换

完整文件尺寸、时长及摘要见`docs/evidence/scroll-garden-step-12/content-audit.json`（证据包附带）。

| 文件 | 规格与身份 | 替换要求 |
| --- | --- | --- |
| `src/assets/signal-garden.webp` | 1672×941，异星来信，网页设计样片 | 提供真实项目名称、图像、准确alt及本人职责后，才把provenance改为real；同步旧稿concept、来源说明与facts |
| `src/assets/liquid-form.webp` | 1122×1402，流动标本，网页设计样片 | 保留竖图完整查看，改尺寸时同步width/height；不要靠裁切隐藏内容 |
| `src/assets/courtyard-orb-cover.webp` | 1440×793，本庭院的真实封面 | 保留原图来源；分享副本`public/share-cover.webp`本版与其逐字节相同 |
| `src/assets/courtyard.png` | 早期固定视角庭院，旧参考稿使用 | 与当前封面版本不同，不互相冒充 |
| `src/assets/courtyard-motion.mp4` | H.264，680×680，12秒，无声，早期固定视角片段 | 保留早期版本说明；换成新庭院录像时同时改clip的说明、尺寸和旧稿caption |
| `src/assets/courtyard-keyframe-00.png`、`-03.png` | 上述早期片段采样 | 与视频版本一致，修改alt、label和旧稿frames |

新增影片时先放本地媒体到`src/assets/`，用ES模块import取得Vite资源URL，再填入`filmWorks[].video`的`kind: 'file'`、src与真实MIME。建议H.264 MP4，封面WebP/JPEG/PNG；避免4K原片直接进入首屏。当前接口也支持external，但本交付没有外链或远程服务，接外部播放器需另测隐私、可用性与返回交互。真实作品未提供，当前没有虚假的播放按钮。

媒体的封面比例可以不同；配置中填写实际像素尺寸，保留完整图查看与文字来源。不要为压缩包缩小正文、替换成低清主体画面或改动水体。新声音/字幕内容需提供相应字幕、可访问名称与明确的用户播放操作，不增加自动播放。

替换媒体后至少检查：封面与完整图、来源/职责文字、手机竖横屏、大字、失败重试、播放/暂停、关闭释放、原位置和焦点返回，随后重新build、封包并解压复验。只改介绍时检查十站容量、长文自然阅读和旧稿同步；改路线/布局/着色器时还需对应几何、完整场景及独立性能复测。

## 维护边界

路线在`src/tour/route.ts`，桌面16段/12.3H、十站、五入口与水潭11.45～11.55H稳定区保持。阅读容量与模式在`createReadingLayout.ts`、`readerFlow.ts`和`readingLayout.css`；场景组装在`src/scene/createScene.ts`，唯一绘制系统在`src/rendering/`，环境播放使用`src/animation/`的统一时钟。仅为换文字/媒体不应新增画布、RAF或场景。

`debug=1`为工程查看；普通首页隐藏调试信息和参考稿链接。图形创建失败时稳定阅读保留十站，参考稿链接作为退路。减少动态会选择稳定阅读并暂停环境，解除偏好后需要明确操作才恢复。

真机复核顺序：iOS Safari和Android Chrome各从默认首页完成十站→两种查看器→横竖屏→返回→200%系统文字/双指缩放；检查浏览器栏、刘海与安全区；VoiceOver/TalkBack读序、焦点和关闭；物理触控板快速/反向滚动与Firefox APZ；最后在实际GPU测帧率。本云环境不替代这些结果。
