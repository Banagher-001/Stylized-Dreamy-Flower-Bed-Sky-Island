# 第三步交接：第四步入口与第五步现场

第三步已完成资源保存、构建复制、根/真实子路径独立访问及代表操作。代码仍在工作区，未提交 GitHub、未发布；测试服务和临时产物已清理。第二步仍仅有标准，其正式架构审查/生命周期交付没有冒充完成。

| 内容 | 已保存值 |
|---|---|
| 作品身份 | bottle-ocean |
| 展示名 | 瓶中海洋 |
| 体验类型 | embedded-page，原完整网页 |
| 相对 entryPath | experiments/bottle-ocean/index.html |
| 工作区网页 | public/experiments/bottle-ocean/index.html |
| 成品 SHA256 | 941feb2ea6ddd3cc93aad5b0b92dbca52ee66a3e1098fee0dbf16f01ca63d1ef |
| 声明/来源 | 同目录 THIRD_PARTY_NOTICES.md、SOURCE.md |
| 封面候选 | src/assets/bottle-ocean-cover.png |
| 封面尺寸/格式 | 1920×1080 PNG；原生截图，未编辑，不含 DOM 面板 |
| 替代文字 | 黄昏海岸的玻璃瓶中，三桅帆船随微型海浪起伏 |

第四步可以从作品配置导入上述封面，增加第三个作品入口和档案，并把现有二选一键盘逻辑扩展为三作品顺序。iframe 与独立链接须通过同一份入口配置和现有 BASE_URL 解析，不能把运行入口固定成站点根路径。封面目前未导入、未打进主站 assets，待第四步引用后再验证输出和加载。

第四步暂未接通现场时应保持 prepared/独立打开的准确状态，不得误落入庭院或假报 ready。当前主站仍只有罗森和庭院两个作品入口，这是分步范围。

第五步再接通大尺寸 iframe、作品专用状态观察、重试/卸载、焦点和阅读恢复。原瓶中海洋使用 __bottleOcean、bottle-ocean-ready、#gl、__bottleError、#loader/#loader-error；初始就绪须组合当前文档/画布证据。原图形丢失后可能保留 ready=true、没有错误标志且错误遮罩不可见，需观察真实 canvas 故障；原暂停仍持续绘制，退出必须卸载。其余原功能与已知问题见第一步矩阵和第二步标准。

本步 root 与前缀路径均有真实原生输入、自然模拟和 PNG 下载证据；这不替代后续 iframe 中的输入隔离、资源回收、主站/罗森/庭院回归以及真机验证。

以后在项目目录启动 npm run dev 后，使用实际服务地址加 /experiments/bottle-ocean/index.html 可独立访问。生产站点需通过静态服务器提供构建目录；本步记录的临时端口不是长期或公网链接。

本步 runtime-manifest.json 记录原文件/public/构建文件与封面摘要。第一步和历史封存未重写；本步自建 evidence-manifest.json，不把已有封存里旧的阶段进度当成本轮最新状态。
