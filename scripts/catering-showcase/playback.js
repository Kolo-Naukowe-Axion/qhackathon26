// Advance the recording continuously; hold each live chapter for the speaker.
export function advancePlayback({time, delta, chapters, mode}) {
  const total = chapters.at(-1).end;
  const nextTime = Math.min(total, time + Math.max(0, delta));
  const current = chapters.find(chapter => time < chapter.end) ?? chapters.at(-1);
  if (mode === 'live' && nextTime >= current.end) {
    return {
      time: current.end === total ? total : current.end - 0.001,
      pause: true,
    };
  }
  return {time: nextTime, pause: nextTime === total};
}

export function rehearsalStatus(seconds) {
  const elapsed=Math.max(0,Math.floor(seconds));
  return {
    elapsed,
    label:`${Math.floor(elapsed/60)}:${String(elapsed%60).padStart(2,'0')}`,
    level:elapsed>=180?'over':elapsed>=165?'wrap':'normal',
  };
}

// Resume normally; restart a completed video or a live chapter at its hold.
export function playbackStartTime({time,chapters,mode}) {
  const current=chapters.find(chapter=>time<chapter.end)??chapters.at(-1);
  if(mode==='video'&&time>=chapters.at(-1).end)return 0;
  if(mode==='live'&&current.end-time<=0.01)return current.start;
  return time;
}

// Keep playback keys available after using presenter controls, while leaving
// text entry, selects and visible action buttons to their native keyboard UI.
export function handlesPresentationKey({code,tagName='',inputType='',editable=false,
  insideControls=false,inMainDocument=true,onButton=false,audience=false,composing=false}) {
  if(composing||!['Space','ArrowRight','ArrowLeft','KeyF','KeyP','KeyR'].includes(code))return false;
  if(editable)return false;
  if(tagName==='INPUT'&&inputType==='range'&&insideControls){
    return audience||!['ArrowRight','ArrowLeft'].includes(code);
  }
  if(['INPUT','SELECT','TEXTAREA'].includes(tagName))return false;
  if(code==='Space'&&inMainDocument&&onButton&&!insideControls&&!audience)return false;
  return true;
}
