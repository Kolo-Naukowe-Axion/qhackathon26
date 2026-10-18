// Notes are attached to visible slide views, never to elapsed-second ranges.
const views = {
 hook: [
  {view:'opening',label:'Opening · Axion Kitchen',speech:'Axion Kitchen. Quantum optimization for catering production.'},
  {view:'baseline',label:'Stage 1 · factory baselines',speech:'Factory baselines: four and eight hours, both checked optimal.'},
  {view:'problem',label:'The catering production problem',speech:'Cookers are machines; cleaning is setup. Each order needs ten mains and ten sides. Waiting is allowed before cooking and packing; cooker cleaning is immediate. The freshness cutoff runs from cooking finish to departure: thirty minutes for A, forty for B and C.'},
 ],
 encoding: [
  {view:'main',label:'Encoding · one bit selects a batch program',speech:'A bit selects one batch and its schedule. Each anchor block chooses one program or idle. Conflicts forbid clashes. This cell uses thirty-five bits.'},
  {view:'code',label:'Encoding · compiler excerpt',speech:'The compiler expands coverage products into pair terms and sets the hard penalty above the full objective range.'},
 ],
 loss: [
  {view:'main',label:'Objective · complete meals and waste',speech:'Main and side coverage multiply into quadratic service and waste terms. Priority weights put missed meals first, then waste and new batches.'},
  {view:'proof',label:'Correctness · the penalty guarantee',speech:'The objective varies by at most S over all bitstrings. Set P to S plus one: every invalid state costs more than every feasible state. This ground-state guarantee does not guarantee solver convergence.'},
 ],
 hamiltonian: [
  {view:'main',label:'Quantum formulation · operators and circuits',speech:'Replacing each bit by I minus Z over two preserves the basis-state cost. QAOA alternates cost and mixing gates. VQE uses coupled Givens rotations and now switches from CVaR to Gibbs loss.'},
  {view:'structure',label:'Quantum formulation · preserved structure and conditional QUBOs',speech:'The mixer preserves one selected choice per block, but cross-block conflicts remain. Removing idle bits preserves feasible schedules. Fixing outside variables turns boundary interactions into linear coefficients for the free variables.'},
 ],
};

export function noteSlidesForChapter(chapter,mode='live') {
 const candidates=views[chapter.id];
 if(candidates)return candidates.map(note=>({...note,chapter:chapter.id}));
 return [{view:'main',chapter:chapter.id,label:chapter.title,
  speech:mode==='live'?(chapter.live_narration||chapter.narration):chapter.narration}];
}

export function notesForSlide(chapter,view='main',mode='live') {
 const candidates=noteSlidesForChapter(chapter,mode);
 return candidates.find(note=>note.view===view)||candidates[0];
}
