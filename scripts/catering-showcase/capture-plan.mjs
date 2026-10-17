// The default captures stills only. A sampler or video needs an explicit flag.
export function captureOptions(args){
 const record=args.includes('--record'),sample=args.includes('--sample');
 if(args.includes('--dry-run')&&(record||sample))throw new Error('--dry-run cannot sample or record.');
 return {record,sample:record||sample,dryRun:!record&&!sample};
}
export function chapterShots(story){
 let start=0;
 return story.map(chapter=>{
  const shot={...chapter,start,end:start+chapter.duration,time:start+chapter.duration*(chapter.still_progress??.45)};
  start=shot.end;return shot;
 });
}
