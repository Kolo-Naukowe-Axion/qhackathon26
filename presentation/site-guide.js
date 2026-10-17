// Shared orientation for the small example, field manual and factory workspace.
const route=[
 ['/catering/','01','Catering scheduling','Active Stage 2: batches, complete meals and waste.'],
 ['/baseline/','02','Stage 1 schedules','Original two- and three-job scheduling examples.'],
 ['/catering/benchmarks/','03','Benchmarks','Quantum methods, VeloxQ and classical references.'],
 ['/problem-explanation/#schedules','04','Try a different order','Reorder jobs. Compare finishing times.'],
];
const header=document.querySelector('.top-actions')??document.querySelector('.masthead');
if(header){
 const button=document.createElement('button');button.className='site-guide-trigger';button.type='button';button.textContent='Project views';button.setAttribute('aria-haspopup','dialog');header.append(button);
 const dialog=document.createElement('dialog');dialog.className='site-guide-dialog';dialog.setAttribute('aria-labelledby','site-guide-title');
 dialog.innerHTML=`<header><span>AXION / DEMO GUIDE</span><button class="site-guide-close" aria-label="Close site guide">×</button></header><h2 id="site-guide-title">Project views</h2><p>Catering is the main project. The required Stage 1 schedules and formulation are linked separately.</p><nav aria-label="Recommended presentation route">${route.map(([href,n,title,description])=>`<a href="${href}"><span>${n}</span><div><strong>${title}</strong><small>${description}</small></div><b aria-hidden="true">↗</b></a>`).join('')}</nav>`;
 document.body.append(dialog);
 button.addEventListener('click',()=>dialog.showModal());
 dialog.querySelector('.site-guide-close').addEventListener('click',()=>dialog.close());
 dialog.addEventListener('click',event=>{if(event.target===dialog){const r=dialog.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)dialog.close();}});
 dialog.addEventListener('cancel',event=>event.stopPropagation());
 dialog.addEventListener('keydown',event=>{if(event.key==='Escape')event.stopPropagation();});
}
