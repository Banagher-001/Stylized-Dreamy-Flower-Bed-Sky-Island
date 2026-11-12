"""Serve only the staged static runtime and a disposable embedding diagnostic."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import argparse

HARNESS = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>罗森独立嵌入核查 · 临时页面</title>
<link rel="icon" href="data:,">
<style>body{margin:0;background:#edf0e4;color:#17332c;font:16px system-ui}header{padding:16px;position:relative;z-index:1}button,a{font:inherit;margin-right:12px;padding:10px}iframe{display:block;width:calc(100% - 32px);height:max(180px,min(700px,calc(100dvh - 106px)));margin:0 16px;border:0}footer{height:1000px;padding:24px}</style>
<header><button id="open">加载场景</button><button id="close">卸载场景</button><span id="state" role="status">等待加载</span></header>
<main id="mount"></main><footer>仅用于检查嵌入、滚轮和资源路径，不是个人网站的新界面。</footer>
<script>const mount=document.querySelector('#mount'),state=document.querySelector('#state');
document.querySelector('#open').onclick=()=>{if(mount.firstChild)return;const frame=document.createElement('iframe');frame.id='lawson';frame.title='罗森场景核查';frame.allow='fullscreen';frame.src='./experiments/lawson/index.html';mount.append(frame);state.textContent='容器已建立，场景加载中';};
document.querySelector('#close').onclick=()=>{mount.replaceChildren();state.textContent='已卸载';};</script></html>'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', default='/tmp/lawson-step1-audit')
    parser.add_argument('--port', type=int, default=4190)
    args = parser.parse_args()
    base = Path(args.directory)
    (base / 'harness.html').write_text(HARNESS)

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(base), **kw)

        def log_message(self, *a):
            pass

    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'Isolated audit server: http://127.0.0.1:{args.port}/root/index.html', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
