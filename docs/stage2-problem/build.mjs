/** Render the canonical Markdown walkthrough; no solver or factory imports.
 * Build-only dependency: marked17.0.5. Reader needs only index.html.
 * MARKED_MODULE may point to another installation's lib/marked.esm.js.
 */
import {readFile,writeFile,stat} from 'node:fs/promises';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {resolve,dirname,relative,sep} from 'node:path';
import {createHash} from 'node:crypto';
import {createRequire} from 'node:module';
const HERE=dirname(fileURLToPath(import.meta.url)),ROOT=resolve(HERE,'../..'),SOURCE=resolve(HERE,'../STAGE2_PROBLEM_WALKTHROUGH.md');
const hash=b=>createHash('sha256').update(b).digest('hex');
const escape=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
let modulePath=process.env.MARKED_MODULE;
if(!modulePath){try{modulePath=createRequire(import.meta.url).resolve('marked');}catch{modulePath='/Users/iwosmura/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/marked/lib/marked.esm.js';}}
const {Marked}=await import(pathToFileURL(resolve(modulePath)).href);
const packageInfo=JSON.parse(await readFile(resolve(dirname(modulePath),'../package.json'),'utf8'));
if(packageInfo.version!=='17.0.5')throw Error(`Expected marked17.0.5, found ${packageInfo.version}`);
const source=await readFile(SOURCE,'utf8'),style=await readFile(resolve(HERE,'style.css'),'utf8');
const headings=[],ids=new Set(),localLinks=[];
const slug=text=>text.replace(/<[^>]*>/g,'').replace(/`/g,'').toLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g,'').replace(/[^\p{L}\p{N}\s_-]/gu,'').trim().replace(/[\s_]+/g,'-');
function anchor(text){const base=slug(text)||'section';let id=base,i=1;while(ids.has(id))id=`${base}-${i++}`;ids.add(id);return id;}
function rebase(href){
 if(!href)return href;
 if(/^(?:https?:|mailto:|tel:)/i.test(href)||href.startsWith('#'))return href;
 if(/^[a-z][\w+.-]*:/i.test(href))throw Error(`Unsupported URL scheme: ${href}`);
 const m=href.match(/^([^?#]*)(.*)$/),p=decodeURIComponent(m[1]),suffix=m[2];
 if(p.startsWith('/')){localLinks.push({target:resolve(ROOT,'.'+p),href});return href;}
 const target=resolve(dirname(SOURCE),p),rebased=relative(HERE,target).split(sep).join('/');
 if(target===SOURCE)return suffix||'#book';
 localLinks.push({target,href:rebased+suffix});return rebased+suffix;
}
const md=new Marked({gfm:true,breaks:false,renderer:{
 heading({tokens,depth,text}){const html=this.parser.parseInline(tokens),id=anchor(text);headings.push({id,depth,title:html.replace(/<[^>]*>/g,'')});return `<h${depth} id="${id}">${html}${depth>1?`<a class="heading-anchor" href="#${id}" aria-label="Link to this section">#</a>`:''}</h${depth}>\n`;},
 link({href,title,tokens}){return `<a href="${escape(rebase(href))}"${title?` title="${escape(title)}"`:''}>${this.parser.parseInline(tokens)}</a>`;},
 image({href,title,text}){return `<img src="${escape(rebase(href))}" alt="${escape(text)}"${title?` title="${escape(title)}"`:''}>`;}
}});
let content=md.parse(source);
if(/<script\b|\son\w+\s*=|javascript:/i.test(content))throw Error('Executable HTML is not supported in the canonical prose source');
content=content.replace(/(<table>[\s\S]*?<\/table>)/g,'<div class="table-scroll" tabindex="0" aria-label="Scrollable reference table">$1</div>');
content=content.replace(/<pre>/g,'<pre tabindex="0" aria-label="Code or formula block">');
// GitHub callouts render as readable notes without requiring a browser plugin.
content=content.replace(/<blockquote>\s*<p>\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*/g,(_,kind)=>`<blockquote class="${['WARNING','CAUTION'].includes(kind)?'callout-warning':'callout'}"><p><strong>${kind[0]+kind.slice(1).toLowerCase()}.</strong> `);
const chapters=headings.filter(h=>h.depth===2);
if(headings.filter(h=>h.depth===1).length!==1||chapters.length<3)throw Error('Expected one document title and at least three step sections');
const pieces=content.split(/(?=<h2 id=")/),opening=pieces.shift();
if(pieces.length!==chapters.length)throw Error('Chapter splitting mismatch');
content=`<header class="book-opening"><p class="kicker">AXION / STAGE2 PROBLEM WALKTHROUGH</p>${opening}</header>`+pieces.map((part,i)=>`<section class="chapter" aria-labelledby="${chapters[i].id}"><span class="chapter-number">SECTION ${String(i+1).padStart(2,'0')}</span>${part}</section>`).join('');
const nav=chapters.map((h,i)=>`<a href="#${h.id}"><small>${String(i+1).padStart(2,'0')}</small><span>${h.title}</span></a>`).join('');
const sourceSHA=hash(source),sourceLink='../STAGE2_PROBLEM_WALKTHROUGH.md';
for(const l of localLinks){if(!l.target.startsWith(ROOT+sep))throw Error(`Local link escapes repository: ${l.href}`);try{await stat(l.target);}catch{throw Error(`Missing rebased local link: ${l.href}`);}}
const title=headings[0].title;
const script=`const menu=document.querySelector('#menu-toggle'),contents=document.querySelector('#contents');menu.onclick=()=>{const open=contents.classList.toggle('open');menu.setAttribute('aria-expanded',String(open));};document.querySelector('#print').onclick=()=>window.print();const nav=[...contents.querySelectorAll('nav a')],sections=[...document.querySelectorAll('.chapter')];contents.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>{contents.classList.remove('open');menu.setAttribute('aria-expanded','false');}));let queued=false;function update(){queued=false;const y=window.scrollY,range=document.documentElement.scrollHeight-innerHeight;document.querySelector('#progress').style.width=(range>0?Math.min(100,100*y/range):100)+'%';let active=sections[0]?.getAttribute('aria-labelledby');for(const s of sections){if(s.getBoundingClientRect().top<innerHeight*.35)active=s.getAttribute('aria-labelledby');}nav.forEach(a=>{const current=a.hash==='#'+active;a.classList.toggle('active',current);current?a.setAttribute('aria-current','location'):a.removeAttribute('aria-current');});}addEventListener('scroll',()=>{if(!queued){queued=true;requestAnimationFrame(update);}},{passive:true});addEventListener('resize',update);addEventListener('keydown',e=>{if(e.key==='Escape'){contents.classList.remove('open');menu.setAttribute('aria-expanded','false');}});update();`;
const page=`<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="A step-by-step written explanation of the Stage2 factory, its numerical rules, solver scopes and QUBO encodings."><title>${escape(title)}</title><style>${style}</style></head><body><a class="skip" href="#book">Skip to the walkthrough</a><div class="reading-progress" aria-hidden="true"><i id="progress"></i></div><header class="topbar"><a class="wordmark" href="#book">AXION / FACTORY FIELD GUIDE</a><div class="tools"><span>Written walkthrough · retained evidence</span><a href="../../presentation/stage2/start.html">Visual overview ↗</a><button type="button" id="print">Print / save PDF</button><button type="button" id="menu-toggle" aria-expanded="false" aria-controls="contents">Contents</button></div></header><aside class="contents" id="contents" aria-label="Table of contents"><p class="nav-title">THE FACTORY, STEP BY STEP</p><nav>${nav}</nav><div class="nav-footer"><a href="../learning-methods/index.html">General scheduling & quantum course ↗</a><a href="${sourceLink}">Canonical Markdown source ↗</a><p>Same source, readable document.<br>No solver, experiment or training is run.</p></div></aside><main id="book">${content}<footer class="book-footer"><strong>End of the walkthrough.</strong><p>Always name the model, the decisions searched, the units and the certificate. A valid replay, complete order set, restricted-pool optimum and full-model optimum establish different things.</p><a href="#book">Return to the beginning ↑</a><p class="source-caption">Built from ${escape(relative(ROOT,SOURCE))}.<br>Source SHA256:<code>${sourceSHA}</code><br>Renderer:marked${packageInfo.version}. CSS and navigation are embedded; reading requires no server, network, account or installed package.</p></footer></main><script>${script}</script></body></html>\n`;
const report={schema:'stage2-written-walkthrough-build.v1',source:relative(ROOT,SOURCE),source_sha256:sourceSHA,renderer:{name:'marked',version:packageInfo.version},style_sha256:hash(style),builder_sha256:hash(await readFile(fileURLToPath(import.meta.url))),html_sha256:hash(page),chapters:chapters.map(h=>({id:h.id,title:h.title})),local_links:localLinks.map(l=>({href:l.href,target:relative(ROOT,l.target)})),words:source.split(/\s+/).filter(Boolean).length,html_bytes:Buffer.byteLength(page),factory_runs:0,solver_runs:0,cdn_dependencies:0};
await writeFile(resolve(HERE,'index.html'),page);await writeFile(resolve(HERE,'build-report.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({chapters:chapters.length,words:report.words,local_links:localLinks.length,bytes:report.html_bytes,source_sha256:sourceSHA}));
