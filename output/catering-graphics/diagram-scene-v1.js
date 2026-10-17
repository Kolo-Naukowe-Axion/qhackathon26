// Native vector art keeps the floor, equipment, workers and plan highlights independent.
const project = (u, v, z = 0) => [430 + (u - v) * .87, 117 + (u + v) * .32 - z];
const pts = a => a.map(p => p.join(',')).join(' ');
const poly = (p, fill, extra = '') => `<polygon points="${pts(p)}" fill="${fill}" ${extra}/>`;
function box(u, v, w, d, h, top = '#e8e5ce', front = '#a3aea0', side = '#788e81') {
  const a = project(u,v,h), b = project(u+w,v,h), c = project(u+w,v+d,h), e = project(u,v+d,h);
  return poly([e,c,project(u+w,v+d),project(u,v+d)],front)+poly([b,c,project(u+w,v+d),project(u+w,v)],side)+poly([a,b,c,e],top);
}
function ellipse(u,v,z,rx,ry,fill,extra='') { const [x,y]=project(u,v,z);return `<ellipse cx="${x}" cy="${y}" rx="${rx}" ry="${ry}" fill="${fill}" ${extra}/>`; }
function pot(u,v) {
  const [x,y]=project(u,v,79);
  return `<g><ellipse cx="${x}" cy="${y+12}" rx="32" ry="16" fill="#586962"/><path d="M${x-30},${y-8}v20a30 13 0 0 0 60 0v-20" fill="#bdc7b9"/><ellipse cx="${x}" cy="${y-8}" rx="30" ry="14" fill="#e0e5d5"/><ellipse cx="${x}" cy="${y-9}" rx="24" ry="10" fill="#dba85f"/><path d="M${x-35},${y}h-8m78,0h8" stroke="#475e55" stroke-width="6" stroke-linecap="round"/><ellipse cx="${x-5}" cy="${y-10}" rx="5" ry="2.5" fill="#678268"/><ellipse cx="${x+10}" cy="${y-8}" rx="4" ry="2" fill="#b16845"/></g>`;
}
function chef(id, color) {
  const start = { W1: [280,260], W2: [315,215], W3: [345,260] }[id];
  const [cx, cy] = project(...start);
  return `<g id="chef-${id}" class="chef" transform="translate(${cx} ${cy})"><ellipse cy="7" rx="19" ry="9" fill="#254d3b" opacity=".14"/><g class="chef-body"><path d="M-9,-9l-2,14m18,-14l5,13" stroke="#3f554d" stroke-width="8" stroke-linecap="round"/><path d="M-17,-42q17-12 34 0l-1,28q-16,11-32,0z" fill="${color}"/><path d="M-9,-39h18v22h-18z" fill="#fff7e7"/><path d="M-17,-35l-8,17m42,-17l8,17" stroke="${color}" stroke-width="8" stroke-linecap="round"/><circle cy="-53" r="13" fill="#d9a97e"/><path d="M-14,-59q-10-17 3-18q2-12 13-6q14-3 13 12q9 9-1 15z" fill="#fffdf0"/><path d="M-12,-59h25v7h-25z" fill="#ecebdc"/><path d="M-5,-51h1m9,0h1" stroke="#493e32" stroke-width="2" stroke-linecap="round"/></g><text class="chef-label" y="26" text-anchor="middle">${id}</text></g>`;
}
export const STATIONS = {P1:[70,265],C1:[100,35],C2:[320,35],K1:[390,265]};
export const WORKER_SPOTS = {P1:[185,335],C1:[170,155],C2:[390,155],K1:[505,335]};
export const REST_SPOTS = {W1:[280,260],W2:[315,215],W3:[345,260]};
function station(id,u,v,type) {
  const w=type==='cook'?150:175, d=90;
  const [cx,cy]=project(u+w/2,v+d/2);
  let detail='';
  if(type==='cook') detail=pot(u+75,v+45);
  if(type==='prep') {
    detail=box(u+20,v+12,110,60,72,'#b89565','#8c704c','#8c704c');
    for(let i=0;i<5;i++)detail+=ellipse(u+45+i*13,v+35,74,5,3,i%2?'#d87b43':'#6c8c55');
    const [x,y]=project(u+103,v+49,75);detail+=`<path d="M${x},${y}l23,10" stroke="#d9e1db" stroke-width="6"/><path d="M${x+20},${y+9}l12,6" stroke="#425a4e" stroke-width="5"/>`;
  }
  if(type==='pack') {
    for(let i=0;i<3;i++)detail+=box(u+25+i*40,v+22,29,45,74,'#f3ead5','#c1b6a0','#d7cbb3')+ellipse(u+39+i*40,v+40,75,9,5,'#8c9b69');
  }
  const [tx,ty]=project(u+w/2,v+d+10);
  return `<g id="station-${id}" class="station"><ellipse class="station-halo" cx="${cx}" cy="${cy}" rx="115" ry="50" fill="none" stroke="#e98651" stroke-width="3" stroke-dasharray="8 6"/>${box(u+8,v+8,w,d,8,'#50665a','#50665a','#50665a')}${box(u,v,w,d,65)}${detail}<g class="steam" transform="translate(${project(u+w/2,v+45,112).join(' ')})"><path d="M-15,0q-12-12 0-24t0-22m18,38q12-12 0-24t0-20m18,45q-10-10 0-20t0-22" stroke="#fffdf2" stroke-width="5" stroke-linecap="round" fill="none"/></g><g class="offline-mark" transform="translate(${cx} ${cy-80})"><circle r="17" fill="#a44432"/><path d="M-6-6l12 12m0-12l-12 12" stroke="#fff5e4" stroke-width="3"/></g><g transform="translate(${tx} ${ty+24})"><rect x="-60" y="-12" width="120" height="25" rx="5" fill="#fcf8e9"/><text text-anchor="middle" y="5" class="station-title">${id} / ${type==='prep'?'PREP':type==='pack'?'PACK':'COOKER'}</text><text id="status-${id}" class="station-status" text-anchor="middle" y="32">Ready</text></g></g>`;
}
export function kitchenSVG() {
  let tiles='';
  for(let u=0;u<600;u+=60)for(let v=0;v<420;v+=60)tiles+=poly([project(u,v),project(u+60,v),project(u+60,v+60),project(u,v+60)],(u+v)%120===0?'#d9dbc2':'#e3e3cc','stroke="#c3ccb4" stroke-width=".6"');
  const shelf=box(12,130,55,100,130,'#d3d8c5','#a1b7a1','#789580');
  const [sx,sy]=project(15,160,140);
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 530" role="img" aria-labelledby="kitchen-title kitchen-desc"><title id="kitchen-title">The Axion catering kitchen</title><desc id="kitchen-desc">An isometric kitchen with one prep station, two cookers, one packing line and three qualified workers. Station activity follows the saved schedule.</desc><style>.steam,.offline-mark,.station-halo{opacity:0}.chef-label{font:10px monospace;fill:#516b50}.station-title{font:9px monospace;fill:#3a5847}.station-status{font:10px monospace;fill:#78906c}</style><defs><filter id="floor-shadow" x="-30%" y="-30%" width="160%" height="170%"><feGaussianBlur stdDeviation="14"/></filter></defs><ellipse cx="505" cy="410" rx="410" ry="115" fill="#5b7561" opacity=".12" filter="url(#floor-shadow)"/>${poly([project(0,0,-16),project(600,0,-16),project(600,420,-16),project(0,420,-16)],'#a7b69a')}${poly([project(0,420),project(600,420),project(600,420,-16),project(0,420,-16)],'#9da98b')}${poly([project(600,0),project(600,420),project(600,420,-16),project(600,0,-16)],'#b6bfa6')}${tiles}${poly([project(0,0),project(600,0),project(600,0,110),project(0,0,110)],'#cbd5bb')}${poly([project(0,0),project(0,420),project(0,420,110),project(0,0,110)],'#b5c6ad')}${poly([project(0,0,110),project(600,0,110),project(600,10,110),project(0,10,110)],'#e4e8d5')}${poly([project(0,0,110),project(0,420,110),project(10,420,110),project(10,0,110)],'#dce3cb')}${shelf}<path d="M${sx+10},${sy+10}v65" stroke="#e7eadc" stroke-width="3"/>${station('C1',100,35,'cook')}${station('C2',320,35,'cook')}<g class="floor-route" fill="none" stroke="#faf7df" stroke-width="3" stroke-dasharray="7 11" opacity=".65"><path d="M${project(210,310)}L${project(210,185)}L${project(490,185)}L${project(490,310)}"/></g>${station('P1',70,265,'prep')}${station('K1',390,265,'pack')}<g id="workers">${chef('W2','#849775')}${chef('W3','#c38b62')}${chef('W1','#315f50')}</g><g transform="translate(798 470)"><path d="M-20,8h83v-48h-83z" fill="#e6c9a0"/><path d="M-25,-40l43-22 51 22-43 23z" fill="#f5e1b9"/><path d="M18,-62v45" stroke="#bda075" stroke-width="2"/><text x="22" y="30" text-anchor="middle" fill="#687868" font-size="11" font-family="monospace">DISPATCH</text></g></svg>`;
}
export function moveWorker(el, u, v) { const [x,y]=project(u,v);el.setAttribute('transform',`translate(${x} ${y})`); }
