"""Loopback-only recording/live-demo studio; excluded from the deployed site."""
import argparse
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import tempfile
import threading
from urllib.parse import unquote,urlsplit

from catering_live import ROOT,run_demo

studio=ROOT/'scripts/catering-showcase'
lock=threading.Lock()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        name=unquote(urlsplit(self.path).path)
        base=studio if name=='/' or name.startswith('/studio/') else ROOT/'presentation'
        relative='index.html' if name=='/' or name.rstrip('/')=='/baseline' else name.removeprefix('/studio/') if name.startswith('/studio/') else name.lstrip('/')
        path=(base/relative).resolve()
        if not path.is_relative_to(base.resolve()):self.send_error(403);return
        if path.is_dir():path=path/'index.html'
        if not path.is_file():self.send_error(404);return
        data=path.read_bytes()
        if name.rstrip('/')=='/baseline':data=data.replace(b'<head>',b'<head>\n<base href="/" />',1)
        self.send_response(200)
        self.send_header('Content-Type',mimetypes.guess_type(str(path))[0] or 'application/octet-stream')
        self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)

    def do_POST(self):
        host=f'http://127.0.0.1:{self.server.server_port}'
        if self.path!='/api/sample' or self.headers.get('Origin')!=host:
            self.send_error(403);return
        if not lock.acquire(blocking=False):self.send_error(409);return
        try:
            directory=Path(tempfile.mkdtemp(prefix='axion-live-'))/'run'
            result=run_demo(directory)
            data=json.dumps(result).encode();self.send_response(200)
        except Exception as exc:
            data=json.dumps(dict(status='failed',error=str(exc),fallback='Use the retained result and state that the fresh launch failed.')).encode()
            self.send_response(500)
        finally:lock.release()
        self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)

    def log_message(self,format,*args):
        if self.path=='/api/sample':super().log_message(format,*args)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--port',type=int,default=4193)
    args=parser.parse_args();server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    print(f'Axion recording/live studio: http://127.0.0.1:{args.port}/',flush=True)
    server.serve_forever()
