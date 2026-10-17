// Shared orientation for the small example, field manual and factory workspace.
const route=[
 ['/problem-explanation/#brief','01','Start small','Jobs share machines.'],
 ['/problem-explanation/#schedules','02','Try a different order','Reorder jobs. Compare finishing times.'],
 ['/stage2/?view=research&section=problem','03','Meet the full factory','Parts, robots and deadlines.'],
 ['/stage2/?tour=1','04','Follow a real replay','Parts to shipping, in six steps.'],
 ['/stage2/?view=research&section=overview','05','Read the results','Results, checks and limits.'],
];
const header=document.querySelector('.top-actions')??document.querySelector('.masthead');
if(header){
 const button=document.createElement('button');button.className='site-guide-trigger';button.type='button';button.textContent='Start here';button.setAttribute('aria-haspopup','dialog');header.append(button);
 const dialog=document.createElement('dialog');dialog.className='site-guide-dialog';dialog.setAttribute('aria-labelledby','site-guide-title');
 dialog.innerHTML=`<header><span>AXION / DEMO GUIDE</span><button class="site-guide-close" aria-label="Close site guide">×</button></header><h2 id="site-guide-title">Choose a view.</h2><p>Start with the small example, or go straight to the factory.</p><nav aria-label="Recommended presentation route">${route.map(([href,n,title,description])=>`<a href="${href}"><span>${n}</span><div><strong>${title}</strong><small>${description}</small></div><b aria-hidden="true">↗</b></a>`).join('')}</nav>`;
 document.body.append(dialog);
 button.addEventListener('click',()=>dialog.showModal());
 dialog.querySelector('.site-guide-close').addEventListener('click',()=>dialog.close());
 dialog.addEventListener('click',event=>{if(event.target===dialog){const r=dialog.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)dialog.close();}});
 dialog.addEventListener('cancel',event=>event.stopPropagation());
 dialog.addEventListener('keydown',event=>{if(event.key==='Escape')event.stopPropagation();});
}
