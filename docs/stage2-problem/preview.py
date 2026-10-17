"""Read-only loopback preview: document, declared source links, public presentation."""
from http.server import BaseHTTPRequestHandler,HTTPServer
from pathlib import Path
from urllib.parse import unquote,urlsplit
import json,mimetypes
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
report=json.loads((HERE/'build-report.json').read_text())
allowed={(ROOT/row['target']).resolve()for row in report['local_links']}
allowed.update([ROOT/'docs/STAGE2_PROBLEM_WALKTHROUGH.md',ROOT/'docs/learning-methods/index.html'])
class Preview(BaseHTTPRequestHandler):
 def do_GET(self):
  path=(ROOT/unquote(urlsplit(self.path).path).lstrip('/')).resolve()
  if path.is_dir():path=path/'index.html'
  permitted=path in allowed or path.is_relative_to(HERE)or path.is_relative_to(ROOT/'presentation')
  if not path.is_relative_to(ROOT)or not permitted or not path.is_file():self.send_error(404);return
  kind=mimetypes.guess_type(path)[0]or'text/plain'
  if path.suffix in ['.py','.md','.mjs']:kind='text/plain'
  self.send_response(200);self.send_header('Content-Type',kind+'; charset=utf-8');self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(path.read_bytes())
 def log_message(self,*_):pass
print('Written walkthrough: http://127.0.0.1:4191/docs/stage2-problem/',flush=True)
HTTPServer(('127.0.0.1',4191),Preview).serve_forever()
