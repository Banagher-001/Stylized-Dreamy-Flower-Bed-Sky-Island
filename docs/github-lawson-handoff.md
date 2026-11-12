# 罗森完整网页嵌入：GitHub 保存说明

根据用户于 2026-11-12（Asia/Shanghai）“上传到仓库里面”的明确指示，将当前已验收的个人网站与罗森集成保存到 [Banagher-001/Stylized-Dreamy-Flower-Bed-Sky-Island](https://github.com/Banagher-001/Stylized-Dreamy-Flower-Bed-Sky-Island) 的 main 分支。上传前远端为 `4a6dd7c5c9c126ab3b9319fab5d8ea16a704dae8`，与本地基线一致；保留既有历史，以正常提交和快进推送保存。本记录首次加入的提交对应本次保存，准确提交身份见 [main 提交记录](https://github.com/Banagher-001/Stylized-Dreamy-Flower-Bed-Sky-Island/commits/main/)。

本次保存候选为 `lawson-fullpage-step7-882322e9045fcdba`。Coding 区提供 LAWSON / COURTYARD 选择，罗森使用大尺寸完整网页，包含原控制台、场景操作、车辆、店员、档案、独立打开与返回阅读。

## 保存范围

- 当前主站源码、项目封面、双作品入口、完整网页管理器与查看器布局。
- `public/experiments/lawson/` 中全部 46 个原运行文件，共 20,332,784 字节，包含 HTML、CSS、JS、Three.js 依赖及四个 GLB。
- 罗森初次盘点、重新制定的七步标准、逐项功能对照、交付说明、测试脚本、实际结果和八组独立封存。
- 原有庭院、早期交付归档及其历史记录继续保留。本次不重新打包旧 ZIP。

node_modules、临时 dist、浏览器缓存与 Python 缓存按现有忽略规则处理。新增文件均低于 GitHub 普通 Git 的单文件限制；既有大验收 ZIP 的 LFS 规则保持原样。

上传前重新核对当前 95 项生产输入与已验收候选一致，原运行文件及八组封存完整。最终构建与干净安装复现、41 控件、13 条键位、17 类拾取、三车完整流程和浏览器范围见 [第七步验收](lawson-fullpage/step-7-verification.md)；运行方法见 [交付说明](lawson-fullpage/step-7-handoff.md)。[本次存储清单](lawson-github-storage.json)记录候选、上传前分支与文件依据。

## 下载后使用

使用本次提交后的仓库源码，完整解压并保留 public 目录。在项目根目录执行：

```powershell
npm.cmd ci
npm.cmd run dev
```

macOS/Linux 使用 npm ci、npm run dev。需要预览成品时执行 npm run build 后 npm run preview。请打开终端输出的 HTTP 地址，不能直接双击 HTML 代替。

罗森运行资源已随仓库保存，网页运行不需要访问 luosen-asset 私有仓库。此前 garden-enhancement 等压缩包代表旧庭院版本；当前罗森集成从本次源码构建。

## 历史状态与发布范围

封存的标准、报告、机器结果和 after/ 副本中的“未提交、未推送、未发布”保留验收当时的事实，不为本次仓库保存改写。后续保存状态由此记录与 Git 提交历史说明，封存源码副本仍用于复查原候选。

本次仅保存 GitHub 仓库，没有启用 Pages、部署网站或创建公开 Release。原网页已知问题、真机及硬件 GPU 等未验证边界继续按最终验收报告保留。
