"""Local-only final-build and untouched independent-original HTTP server."""
from pathlib import Path
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import unquote,urlsplit

ROOT=Path(__file__).resolve().parents[2]
class Handler(SimpleHTTPRequestHandler):
    def translate_path(self,path):
        path=unquote(urlsplit(path).path)
        if path.startswith('/original/'):
            directory=ROOT.parent/'luosen-asset/lawson-blender/out/web_final';relative=path[len('/original/'):]
        else:
            directory=ROOT/'dist';prefix='/Stylized-Dreamy-Flower-Bed-Sky-Island/'
            relative=path[len(prefix):]if path.startswith(prefix)else path.lstrip('/')
        resolved=(directory/relative).resolve()
        return str(resolved if resolved.is_relative_to(directory.resolve())else directory/'__invalid__')
    def log_message(self,*args):pass
    def end_headers(self):
        self.send_header('Cache-Control','no-cache');super().end_headers()
ThreadingHTTPServer(('127.0.0.1',4197),Handler).serve_forever()
