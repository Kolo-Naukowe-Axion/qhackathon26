import { variants, findVariant, applyVariant } from './variants.js';
const params = new URLSearchParams(location.search);
const storage = { get(key) { try { return localStorage.getItem(`axion-art-${key}`); } catch { return null; } }, set(key,value) { try { localStorage.setItem(`axion-art-${key}`,value); } catch { /* Private browsing still supports this session. */ } } };
let current = findVariant(params.get('variant') || storage.get('variant') || 'lunar');
let favorite = storage.get('favorite');
if (!variants.some(v => v.id === favorite)) {
  favorite = null;
  if (params.get('preview') !== '1') storage.set('favorite', '');
}
if (storage.get('variant') && !variants.some(v => v.id === storage.get('variant')) && params.get('preview') !== '1') storage.set('variant', 'lunar');
if (params.has('variant') && params.get('variant') !== current.id) {
  const url = new URL(location.href); url.searchParams.set('variant', current.id); history.replaceState(null, '', url);
}
applyVariant(current.id);
if (params.get('preview') === '1') {
  document.body.classList.add('variant-preview');
} else {
  const panel = document.createElement('aside');
  panel.className = 'art-switcher';
  panel.setAttribute('aria-label','Visual variant switcher');
  panel.innerHTML = `<div class="art-handle" title="Drag to move · arrow keys to reposition" tabindex="0" role="group" aria-label="Move variant switcher with arrow keys"><span class="art-grip" aria-hidden="true">⠿</span><span>ART DIRECTION</span><span class="art-count"></span><button class="art-collapse" aria-label="Collapse variant switcher" aria-expanded="true">−</button></div><div class="art-body"><div class="art-heading"><span class="art-name"></span><button class="art-favorite" title="Choose as favorite" aria-label="Choose as favorite" aria-pressed="false">☆</button></div><p class="art-genre"></p><div class="art-navigation"><button class="art-prev" aria-label="Previous visual variant">←</button><label><span class="sr-only">Visual variant</span><select class="art-select">${variants.map((v,i)=>`<option value="${v.id}">${String(i+1).padStart(2,'0')} / ${v.name}</option>`).join('')}</select></label><button class="art-next" aria-label="Next visual variant">→</button></div><div class="art-swatches" aria-hidden="true"></div><p class="art-note"></p><button class="art-gallery">▦ &nbsp; Compare all 3</button><div class="art-foot"><span>← → browse · drag to move</span><button class="art-reset" title="Return switcher to its starting position" aria-label="Reset switcher position">⌖</button></div><p class="art-saved" role="status"></p></div>`;
  document.body.append(panel);
  const dialog = document.createElement('dialog');
  dialog.className = 'art-dialog';
  dialog.setAttribute('aria-label','Compare visual variants');
  dialog.innerHTML = `<div class="art-dialog-head"><div><span class="art-kicker">AXION / ART DIRECTION SELECT</span><h2>Three directions. One factory.</h2><p>Try each direction in the live factory. Star your favorite to keep your choice.</p></div><button class="art-dialog-close" aria-label="Close variant gallery">×</button></div><div class="art-dialog-tools"><span class="art-favorite-label"></span><div><button class="art-density">Large previews</button><button class="art-compare">Compare favorite + current</button><button class="art-show-all" hidden>Show all 3</button></div></div><div class="art-grid"></div>`;
  document.body.append(dialog);
  const $ = selector => panel.querySelector(selector);
  const all = variants;
  function render() {
    $('.art-name').textContent = current.name;
    $('.art-genre').textContent = current.genre;
    $('.art-count').textContent = `${variants.indexOf(current)+1} / ${variants.length}`;
    $('.art-select').value = current.id;
    $('.art-note').textContent = current.note;
    $('.art-favorite').textContent = favorite===current.id?'★':'☆';
    $('.art-favorite').setAttribute('aria-pressed',String(favorite===current.id));
    $('.art-saved').textContent = favorite ? `★ Favorite: ${findVariant(favorite).name}` : 'No favorite chosen yet';
    $('.art-swatches').innerHTML = [current.land[0],current.ui[4],current.ui[0],current.accent,...current.metal.slice(1,3)].map(c=>`<i style="background:${c}"></i>`).join('');
    dialog.querySelector('.art-favorite-label').textContent = favorite ? `★ ${findVariant(favorite).name}` : '☆ Choose a favorite';
    dialog.querySelector('.art-compare').disabled = !favorite || favorite===current.id;
    for (const card of dialog.querySelectorAll('.art-card')) {
      card.classList.toggle('is-current', card.dataset.id===current.id);
      const star = card.querySelector('.art-card-star');
      star.textContent = favorite===card.dataset.id?'★ Favorite':'☆ Favorite';
      star.setAttribute('aria-pressed',String(favorite===card.dataset.id));
    }
  }
  function choose(id) {
    current = applyVariant(id);
    storage.set('variant',current.id);
    const url = new URL(location.href); url.searchParams.set('variant',current.id); url.searchParams.delete('gallery');
    history.replaceState(null,'',url);
    render();
    document.body.classList.remove('art-changing');
    requestAnimationFrame(()=>document.body.classList.add('art-changing'));
  }
  function star(id) { favorite = favorite===id ? null : id; storage.set('favorite',favorite||''); render(); }
  function step(direction) { choose(all[(all.indexOf(current)+direction+all.length)%all.length].id); }
  function gallery(ids=variants.map(v=>v.id)) {
    const grid = dialog.querySelector('.art-grid');
    grid.classList.toggle('art-pair',ids.length===2);
    grid.classList.toggle('art-overview',ids.length===variants.length);
    dialog.querySelector('.art-density').hidden = ids.length===2;
    dialog.querySelector('.art-density').textContent = 'Large previews';
    dialog.querySelector('.art-show-all').hidden = ids.length!==2;
    grid.innerHTML = ids.map(id=>{const v=findVariant(id);return `<article class="art-card" data-id="${v.id}"><button class="art-preview-button" aria-label="Try ${v.name}"><div class="art-thumbnail"><iframe src="/?variant=${v.id}&preview=1" tabindex="-1" title="${v.name} preview" loading="lazy" aria-hidden="true"></iframe><span class="art-preview-cta">Enter world ↗</span></div></button><div class="art-card-info"><div><span>${String(variants.indexOf(v)+1).padStart(2,'0')} / ${v.genre}</span><h3>${v.name}</h3></div><button class="art-card-star" aria-pressed="false">☆ Favorite</button></div><p>${v.note}</p></article>`;}).join('');
    for (const card of grid.querySelectorAll('.art-card')) {
      card.querySelector('.art-preview-button').addEventListener('click',()=>{choose(card.dataset.id);dialog.close();});
      card.querySelector('.art-card-star').addEventListener('click',()=>star(card.dataset.id));
    }
    render();
    dialog.scrollTop = 0;
    if (!dialog.open) dialog.showModal();
  }
  $('.art-select').addEventListener('change',e=>choose(e.target.value));
  $('.art-prev').addEventListener('click',()=>step(-1));
  $('.art-next').addEventListener('click',()=>step(1));
  $('.art-favorite').addEventListener('click',()=>star(current.id));
  $('.art-gallery').addEventListener('click',()=>gallery());
  $('.art-collapse').addEventListener('click',()=>{
    const collapsed = panel.classList.toggle('is-collapsed');
    $('.art-collapse').textContent=collapsed?'+':'−';
    $('.art-collapse').setAttribute('aria-expanded',String(!collapsed));
    $('.art-collapse').setAttribute('aria-label',`${collapsed?'Expand':'Collapse'} variant switcher`);
    clamp();
  });
  dialog.querySelector('.art-dialog-close').addEventListener('click',()=>dialog.close());
  dialog.addEventListener('click',e=>{if(e.target===dialog) dialog.close();});
  dialog.addEventListener('close',()=>{dialog.querySelector('.art-grid').replaceChildren();$('.art-gallery').focus();});
  dialog.querySelector('.art-compare').addEventListener('click',()=>{if(favorite&&favorite!==current.id)gallery([favorite,current.id]);});
  dialog.querySelector('.art-density').addEventListener('click',()=>{
    const overview = dialog.querySelector('.art-grid').classList.toggle('art-overview');
    dialog.querySelector('.art-density').textContent = overview ? 'Large previews' : 'Overview';
    dialog.scrollTop = 0;
  });
  dialog.querySelector('.art-show-all').addEventListener('click',()=>gallery());
  document.addEventListener('keydown',e=>{
    if (dialog.open || e.altKey || e.metaKey || e.ctrlKey || e.shiftKey || e.defaultPrevented || e.target.closest('input,select,textarea,[role="tab"],.art-handle')) return;
    if (e.key==='ArrowLeft'||e.key==='ArrowRight') {e.preventDefault();step(e.key==='ArrowLeft'?-1:1);}
  });
  let drag;
  const handle=$('.art-handle');
  function move(x,y) {
    panel.style.left=`${Math.max(8,Math.min(x,innerWidth-panel.offsetWidth-8))}px`;
    panel.style.top=`${Math.max(8,Math.min(y,innerHeight-panel.offsetHeight-8))}px`;
    panel.style.right='auto';panel.style.bottom='auto';
  }
  const positionKey = () => `${matchMedia('(max-width: 700px)').matches ? 'mobile-' : ''}${document.body.dataset.view === 'desk' ? 'desk-position' : 'position'}`;
  function savePosition() {const r=panel.getBoundingClientRect();storage.set(positionKey(),JSON.stringify({x:r.x,y:r.y}));}
  function restorePosition() {
    panel.removeAttribute('style');
    try {const p=JSON.parse(storage.get(positionKey()));if(p)move(p.x,p.y);}catch{/* Use default placement. */}
  }
  function clamp() { if(panel.style.left) {const r=panel.getBoundingClientRect();move(r.x,r.y);} }
  handle.addEventListener('pointerdown',e=>{
    if(e.target.closest('button')||e.button!==0)return;
    const r=panel.getBoundingClientRect(); drag={x:e.clientX-r.x,y:e.clientY-r.y};
    handle.setPointerCapture(e.pointerId);panel.classList.add('is-dragging');
  });
  handle.addEventListener('pointermove',e=>{if(drag)move(e.clientX-drag.x,e.clientY-drag.y);});
  const finish=()=>{if(drag){drag=null;panel.classList.remove('is-dragging');savePosition();}};
  handle.addEventListener('pointerup',finish);handle.addEventListener('pointercancel',finish);
  handle.addEventListener('keydown',e=>{
    if(!e.key.startsWith('Arrow'))return;e.preventDefault();e.stopPropagation();
    const r=panel.getBoundingClientRect(), d=e.shiftKey?40:12;
    move(r.x+(e.key==='ArrowRight'?d:e.key==='ArrowLeft'?-d:0),r.y+(e.key==='ArrowDown'?d:e.key==='ArrowUp'?-d:0));savePosition();
  });
  $('.art-reset').addEventListener('click',()=>{panel.removeAttribute('style');storage.set(positionKey(),'');});
  window.addEventListener('resize',clamp);
  restorePosition();
  document.addEventListener('axion:view', restorePosition);
  if (matchMedia('(max-width: 700px)').matches) {
    panel.classList.add('is-collapsed');
    $('.art-collapse').textContent = '+';
    $('.art-collapse').setAttribute('aria-expanded', 'false');
    $('.art-collapse').setAttribute('aria-label', 'Expand variant switcher');
  }
  render();
  if (params.get('gallery') === '1') gallery();
}
