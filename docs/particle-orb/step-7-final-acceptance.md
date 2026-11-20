# 第七步　默认粒子水球与成品验收

成品版本为 `particle-orb-step7-99634b67a4c3f8f7`。普通首页直接显示完整的 708 粒子水球，球面起伏、水纹、两颗水珠与触水涟漪一起运行。窄屏先进入「水潭」一节，再点「进入庭院现场」看近景。 [成品 ZIP](../../release/particle-orb-step7-99634b67a4c3f8f7-site.zip) · [SHA-256](../../release/particle-orb-step7-99634b67a4c3f8f7-SHA256SUMS)

完整解压后，Windows 可以双击 `START-PREVIEW.cmd`。也可以在解压目录运行 `node scripts/preview-site.mjs --port 0`，打开终端显示的地址。使用 Node.js 22.12 或以上版本。 [备用启动说明](../startup-fallback.md)

## 画面与播放

从普通首页实际滚轮往返的录像保留现场播放节奏。桌面固定帧为 1440 × 900，窄屏为 390 × 844 CSS 像素、DPR 2。最终首页的五张同机位对照帧与第六步的实测逐像素一致。窄屏分别核对了两颗水珠的落点与涟漪圆心。 [18.52 秒默认入口实录](evidence/step-7/default-courtyard-tour.mp4)

| 机位与固定时间 | 实拍 |
| --- | --- |
| 桌面全景 · 5.322 秒 | [开场](evidence/step-7/overview.png) |
| 桌面水潭 · 3.5 秒 | [主水纹](evidence/step-7/water-crest.png) |
| 桌面水潭 · 4.425 秒 | [水珠脱落](evidence/step-7/water-release.png) |
| 桌面水潭 · 5.322 秒 | [涟漪展开](evidence/step-7/water-ripple.png) |
| 窄屏水潭 · 5.322 秒 | [现场近景](evidence/step-7/mobile-water.png) |

半空与涟漪展开时均可暂停。切换画面模式、滚出水潭再返回后仍可从原相位续播。自动导览可由滚轮接管后再恢复。窄屏触控验证了返回阅读后的焦点恢复和重新进入时的场景时间。系统减少动态时，首次访问采用稳定阅读并暂停环境。

## 原位作品与生产构建

本地预览分别检查了生产构建和独立解压的成品包。成品包在根路径和 `/Stylized-Dreamy-Flower-Bed-Sky-Island/` 子路径都能直接开启完整水球，实测提交一次 `GL_POINTS` 绘制，共 708 个点。ZIP 的 75 项条目通过 CRC 与 SHA-256 检查，69 个生产文件中有 49 个内嵌作品文件与原资源逐字节一致。 [构建清单](evidence/step-7/build.json)

有窗口的 Chromium 用稳定阅读布局走通了全景、关于我、AI 影像、罗森、瓶中海洋、水潭和返回全景。罗森实测了昼夜、招牌灯、拖动镜头与全屏退出。瓶中海洋实测了波高、镜头、暂停续播和导出 PNG。两次切换在同一个作品窗口完成。 [罗森原位实拍](evidence/step-7/lawson-in-portfolio.png) · [瓶中海洋原位实拍](evidence/step-7/bottle-in-portfolio.png) · [验收数据](evidence/step-7/validation.json)

## 旧版和分步对照

| 地址末尾参数 | 版本 |
| --- | --- |
| `?orb=lively` | 本次改版前的动态水球 |
| `?orb=legacy` | 更早的水球 |
| `?orb=particles` | 第二步静态粒子 |
| `?orb=particles&orbMotion=wave` | 第三步表面起伏 |
| `?orb=particles&orbMotion=wave&orbFlow=on` | 第四步主水纹 |
| `?orb=particles&orbMotion=wave&orbFlow=on&orbDrops=on` | 与普通首页同款的完整效果 |
