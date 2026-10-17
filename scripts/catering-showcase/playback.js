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
