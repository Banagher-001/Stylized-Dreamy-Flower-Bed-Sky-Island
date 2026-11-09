# 当前庭院的维护说明

本轮最终应用沿用第六步的完整视觉与交互。运行入口是`src/main.ts`到`src/tour/startTourPrototype.ts`，素材由Vite打包；保持锁文件和`.nvmrc`一起保存。首次安装`npm ci`，构建`npm run build`包含严格类型检查。

## 内容与素材

| 修改内容 | 位置 | 一起检查 |
| --- | --- | --- |
| 张辰翰/sakan介绍、枫叶互动/游族网络经历 | `src/tour/aboutContent.ts` | 十段正文容量、导览阅读时间、稳定阅读 |
| 第二柱作品文本和图片 | `src/tour/filmContent.ts`、`src/assets` | 尺寸/替代文本/样片标识、完整图片、失败占位 |
| 第三柱项目与早期影片说明 | `src/tour/experimentContent.ts`、`src/assets` | 现场体验、档案、视频播放/关闭/返回 |
| 水球流纹/形态与水束衔接 | `src/config/orb.ts`、`src/animation/orbMotion.ts`、`src/materials/createOrbMaterial.ts` | 正常/像素、全景/水潭/现场体验、飞滴落点 |
| 云影速度、柔度和响应 | `src/config/cloudShadows.ts` | 草地/石柱/水体、深色细节、循环接点 |
| 飞鸟航线、尺度与拍翼 | `src/config/birds.ts`、`src/animation/birdMotion.ts` | 完整含翼尖间距、阅读安全区、循环与暂停翼姿 |
| 鸟群避让 | `src/tour/birdVisibility.ts` | 实际面板、控件、GPU字样和现场pane边界 |
| 导览停留 | `src/tour/autoGuide.ts` | 到位后计时、自适应长正文、接管及结束重播 |
| 运镜与阅读段 | `src/tour/route.ts`及三类`*Reading.ts` | 原生滚动/相机/正文一致，正反向和窄屏 |
| 介绍羽化与版式 | `src/tour/tour.css`、`readingLayout.css` | 完整边缘、对比度、字体/容量/焦点 |

当前真实信息为张辰翰、sakan（萨坎）、枫叶互动AI动画制作及此前游族网络。第二柱仍是设计样片，档案视频是早期无声习作；替换真实作品时同时更新标题、职责、说明、封面与替代文本，不只换文件。尚未提供的联系方式不预填。

## 保持的行为

只有一个场景、画布和环境时间。导览控制相机与原生滚动，环境控制水体、植被、云影和鸟群；暂停环境后运镜保留世界与翼姿。作品返回不自动重新开启导览。系统减少动态、隐藏/离屏和图形失败沿用现有阅读及节能规则。

原路线16段/12.3H、十个正文站、五个章节入口、水潭稳定区和独立结尾均已验证。正常/像素输出保持，像素设计分辨率384、DPR上限2。长正文会延长导览停留；按实际阅读到位和离站记录复核，不用压缩时间追求旧草案的2～3分钟。

## 修改后如何检查

先执行`npm run build`。在普通页面检查全景、十段正文、水潭、结尾、完整图片与现场体验，再检查环境暂停后滚动、真实滚轮接管导览、作品关闭和窄屏稳定阅读。改鸟群或云影参数还需要复核整个循环及边界，不能只看单帧。

源码包带不依赖历史fixture的独立检查：安装Python Playwright及Chromium后，可运行`python tests/garden-enhancement/step7_release_check.py --site dist --out /tmp/sakan-check`，检查实际HTTP、根/子路径、导览接管、作品返回和失败阅读。它自行启动并关闭临时本地服务。

当前下载包的本地预览入口是`scripts/preview-site.mjs`；修改构建后重启它。它只绑定127.0.0.1，支持正确MIME、缺失404、HEAD和视频字节区间。真实子目录可用`--base /sakan/`验证；正常访问保留末尾斜杠。

本轮自动检查源码保留在`tests/garden-enhancement/step7_*`，依赖说明与实际报告在验收附件。浏览器检查需要Python Playwright/Pillow、相应浏览器及Linux依赖；原生恢复还使用独立虚拟显示和CDP。源码包承诺可独立安装、构建和运行应用；重跑历史封印和逐步套件仍需要相应历史fixture与基线，完整审计不等同于双击启动。

## 保存与回退

保留源码ZIP、成品ZIP及外部版本总清单，搬运后核对SHA256。Git HEAD不代表当前未提交源码，工作区保存、打包、提交、推送和上线分别记录。使用独立目录查看旧版本，避免覆盖当前文件；旧release归档保留原样。

操作入口见[快速上手](quickstart.md)，文件用途与托管说明见[交付说明](delivery.md)。
