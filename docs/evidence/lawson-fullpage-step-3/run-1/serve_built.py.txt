"""Serve one real dist tree at root and project subpath, with no SPA fallback."""
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit
import argparse
ROOT=Path(__file__).resolve().parents[2]
PREFIX='/Stylized-Dreamy-Flower-Bed-Sky-Island'
class Handler(SimpleHTTPRequestHandler):
    def translate_path(self,path):
        parts=urlsplit(path);route=parts.path
        if route==PREFIX:route='/'
        elif route.startswith(PREFIX+'/'):route=route[len(PREFIX):]
        return super().translate_path(urlunsplit(('', '',route,parts.query,'')))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=4193);args=parser.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',args.port),partial(Handler,directory=str(ROOT/'dist')))
    print(f'Serving actual dist at http://127.0.0.1:{args.port}/ and {PREFIX}/; no HTML fallback',flush=True)
    server.serve_forever()
