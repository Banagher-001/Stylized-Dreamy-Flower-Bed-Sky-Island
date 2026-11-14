"""Strict local production server: mount one actual build at / and /portfolio-check/."""
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit,unquote
import argparse,hashlib,json,mimetypes,time
parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--port',type=int,required=True);parser.add_argument('--log',required=True);args=parser.parse_args();root=Path(args.root).absolute();log=Path(args.log)
class Handler(BaseHTTPRequestHandler):
 def do_HEAD(self):self.serve(False)
 def do_GET(self):self.serve(True)
 def serve(self,body):
  path=unquote(urlsplit(self.path).path);prefix='/portfolio-check'
  if path==prefix or path.startswith(prefix+'/'):path=path[len(prefix):]or'/'
  live_root=root.resolve();target=(live_root/path.lstrip('/')).resolve()
  if not target.is_relative_to(live_root):status=403;data=b'Forbidden';content='text/plain; charset=utf-8'
  else:
   if target.is_dir():target=target/'index.html'
   if target.is_file():status=200;data=target.read_bytes();content=mimetypes.guess_type(str(target))[0]or'application/octet-stream'
   elif path=='/favicon.ico':status=204;data=b'';content='image/x-icon'
   else:status=404;data=b'Not found';content='text/plain; charset=utf-8'
  self.send_response(status);self.send_header('Content-Type',content);self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.end_headers()
  if body:self.wfile.write(data)
  with log.open('a')as f:f.write(json.dumps({'time':time.time(),'method':self.command,'url':self.path,'status':status,'type':content,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})+'\n')
 def log_message(self,*args):pass
ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
