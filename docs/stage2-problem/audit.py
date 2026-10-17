"""Audit rendering/provenance/links, not the factory's scientific facts."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote,urlsplit
import hashlib,json,re
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
class Page(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.ids=[];self.links=[];self.images=[];self.external_assets=[];self.headings=[];self.hdepth=None;self.heading_text=[];self.tables=0;self.codes=0;self.scripts=0
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if 'id'in a:self.ids.append(a['id'])
  if tag=='a':self.links.append(a.get('href',''))
  if tag=='img':self.images.append(a.get('src',''))
  if tag in ['script','link']and(a.get('src')or a.get('href')):self.external_assets.append(a.get('src',a.get('href')))
  if tag=='h2':self.hdepth=tag;self.heading_text=[]
  if tag=='table':self.tables+=1
  if tag=='pre':self.codes+=1
  if tag=='script':self.scripts+=1
 def handle_data(self,s):
  if self.hdepth:self.heading_text.append(s)
 def handle_endtag(self,tag):
  if tag==self.hdepth:self.headings.append(''.join(self.heading_text).rstrip('#').strip());self.hdepth=None
source=ROOT/'docs/STAGE2_PROBLEM_WALKTHROUGH.md';report=json.loads((HERE/'build-report.json').read_text());page=(HERE/'index.html').read_text();p=Page();p.feed(page)
sha=lambda b:hashlib.sha256(b).hexdigest()
assert report['source_sha256']==sha(source.read_bytes())
assert report['html_sha256']==sha(page.encode())
assert report['style_sha256']==sha((HERE/'style.css').read_bytes())
assert report['builder_sha256']==sha((HERE/'build.mjs').read_bytes())
assert not p.external_assets,p.external_assets
assert len(p.ids)==len(set(p.ids)),'Duplicate HTML ids'
assert len(p.headings)==len(report['chapters'])
assert len(report['chapters'])>=3
assert all(x['id']in p.ids for x in report['chapters'])
assert report['factory_runs']==report['solver_runs']==report['cdn_dependencies']==0
for href in p.links+p.images:
 url=urlsplit(href)
 if url.scheme or url.netloc:continue
 if not url.path:
  if url.fragment:assert unquote(url.fragment)in p.ids,href
 else:
  target=(ROOT/url.path.lstrip('/'))if url.path.startswith('/')else(HERE/unquote(url.path))
  assert target.exists(),(href,str(target))
assert page.count('class="table-scroll"')==p.tables
assert len(re.findall(r'^```',source.read_text(),re.M))%2==0,'Unclosed source fence'
assert 'overflow:auto'in page and '@media print'in page and 'prefers-reduced-motion'in page
result=dict(schema='stage2-walkthrough-render-audit.v1',valid=True,scientific_fact_audit=False,scope='Rendering, source provenance and local link integrity only; no optimization or factory runs',source_sha256=report['source_sha256'],html_sha256=report['html_sha256'],chapters=len(p.headings),tables=p.tables,code_blocks=p.codes,checked_links=len(p.links+p.images),external_runtime_assets=len(p.external_assets),unique_ids=len(p.ids))
(HERE/'audit-report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
