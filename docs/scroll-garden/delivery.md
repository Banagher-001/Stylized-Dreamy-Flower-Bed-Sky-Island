# 交付与独立运行

本版为sakan三柱滚动庭院的第十二步候选交付。真实个人影片仍待替换。工作区保存、ZIP归档、Git提交、远端推送及线上部署是独立状态；本步只完成本地技术交付，不执行后三项。

## 文件与入口

工作区：`/workspace/Stylized-Dreamy-Flower-Bed-Sky-Island`。源码在`src/`及`public/`，生产文件在`dist/`，正式归档在`release/`，本步证据在`docs/evidence/scroll-garden-step-12/`。

| 地址（相对实际托管目录） | 用途 |
| --- | --- |
| `./` | 正式庭院首页 |
| `./?tour=prototype` | 旧收藏链接，进入同一庭院 |
| `./?tour=reference` | 原固定视角参考作品集 |
| `./?debug=1` | 显式调试，普通访客不需要 |

滚轮/触摸沿柱身阅读；小屏、短横屏、大字或减少动态时使用同一正文的稳定阅读。右上角可明确切换阅读方式，底部有五个章节入口与环境/画面按钮。图片完整查看、现场体验、项目档案和早期片段关闭后回到原阅读位置。

| 新交付文件 | 内容 |
| --- | --- |
| `release/scroll-garden-step12-source.zip` | 可安装构建的源码、锁文件、脚本、测试与说明 |
| `release/scroll-garden-step12-site.zip` | 可静态托管的生产文件，解压根目录就是index.html |
| `release/scroll-garden-step12-evidence.zip` | 本步报告、必要基线、代表截图、实际演示与所引用历史证明 |
| `release/scroll-garden-step12-manifest.json` | 实际候选指纹、工具链、文件/包摘要与解压验证状态 |

每个ZIP带`PACKAGE-MANIFEST.json`，摘要覆盖包内所有其他文件，不包含自身。外部manifest记录三个ZIP的SHA-256、字节数和文件数，不引入自包含哈希。最终验收摘要使用`summary.json`和`package-verification.json`；包内说明不在封包后直接修改。

旧`courtyard-*`属于早期固定庭院，`portfolio-*`属于固定庭院作品集扩展；均原样保留，不代表本版三柱滚动网页。第十一步独立对照为`docs/evidence/scroll-garden-step-12/baseline-step11.tar.gz`，证据包附带，可解压后直接托管其中dist。

## 安装、开发与构建

已验证Node **24.22.1**（`.nvmrc`）、npm **11.9.0**。Three **0.187.0**、Vite **8.3.5**、TypeScript **7.0.2**，依赖由lock固定。解压源码包，在其根目录执行：

```bash
npm ci
npm run dev
npm run build
node scripts/serve-dist.mjs dist 4174
```

`build`先严格类型检查再构建。开发地址通常为`http://localhost:5173/`；最后一个命令仅本机预览`http://127.0.0.1:4174/`，不是公网部署服务。修改并重建后重启该静态预览服务。`npm run preview -- --port 4173 --strictPort`也可检查构建。

安装需要包管理器访问或已填充的npm缓存；不承诺新机器无依赖离线构建。应用运行资源全部随站点提供，无API密钥、数据库、后端或CDN需求。正式三维画面需要WebGL2，图形不可用时可稳定阅读。

## 静态托管

成品包不需要Node来运行应用。解压后用任意支持JS模块、正确MIME与正常HTTP的静态服务器托管。例如安装Python的机器：

```bash
python3 -m http.server 8080 --directory /path/to/extracted-site
```

打开`http://localhost:8080/`。不要用file://双击代替HTTP。部署只上传成品包内的静态文件，不上传node_modules、源码、测试或证据包。

Vite使用`base: './'`，favicon、分享图、模块、封面和视频随实际目录解析。同一份产物既可放站点根目录，也可放`/review/courtyard/`这类真实子目录。子目录地址保留末尾`/`；静态主机应为目录地址补斜杠。无需SPA重写，找不到的资源必须404，不能返回index.html伪装成功。HTML建议no-cache，哈希assets可长期缓存。

尚无正式域名，未填写canonical或og:url。分享图提供真实本地庭院封面；选定正式域名后，将og:image配置为该域名下绝对HTTPS地址，并按需补canonical/og:url，再用目标平台抓取器复核。不同分享平台对相对图像地址的支持不同，本地资源检查不代表所有平台已抓取。

## 重建与复验

源码包带独立检查器，不依赖本工作区路径或历史图像：

```bash
python3 -m pip install playwright
python3 -m playwright install chromium
python3 tests/scroll-garden/step12_release_check.py --site dist --out /tmp/garden-release-check
```

它启动并自行关闭本机HTTP服务，实际复制到子目录，检查每项文件SHA/MIME、缺失404、新首页/刷新、兼容链接、参考稿、图形失败退路与减少动态。系统Chromium通过PATH或CHROMIUM_EXECUTABLE选择。加`--engines chromium,firefox,webkit`可检查三引擎，需要安装相应浏览器、Linux依赖和显示服务；GTK WebKit不是iOS真机。

`step12_regression.py`复用一并附带的Step11/Step2测试代码，用新默认首页运行，输出必须指定外部目录，不覆盖旧证据。示例先在4175启动本机生产服务，再运行：

```bash
python3 tests/scroll-garden/step12_regression.py --suite browser --engine chromium --out /tmp/garden-browser-check
```

历史逐步测试保留供追溯；部分需要完整仓库中的历史截图、Vite开发服务或特定原生输入工具，不属于仅解压源码即可全量重跑的承诺。源码包包含当前独立检查所需全部代码；证据包包含本次引用的历史结论与来源摘要，完整历史大图留在工作区。场景对照需从证据包解压基线并在4174托管，候选在4175，然后运行`step12_scene.py --out /tmp/garden-scene-check`；另需Pillow。

## 保存与回退

保存三个新ZIP和外部manifest，核对SHA-256后再转移。临时解压验证目录不作为唯一备份。当前源文件未Git提交/推送，工作区不是已经同步的远端备份。

仅查看旧稿可用`?tour=reference`，无需覆盖当前源码。要完整回退第十一步，在新目录解压baseline-step11.tar.gz，用其中dist独立托管；不要覆盖当前工作区。基线源码可按其锁文件安装构建。新候选的源码和成品分别有摘要，不用旧Git HEAD代替未提交代码身份。

姓名/素材替换见[维护说明](maintenance.md)，技术验收及设备边界见[第十二步验收](step-12-verification.md)。发布、域名、Git提交与远端推送尚未执行。
