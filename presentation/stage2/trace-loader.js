/** Lazy same-origin JSON/gzip loading. A gzip replay requires a matching evidence sidecar. */
export async function fetchLinkedTrace(requested,base,fetcher=fetch){
 const url=new URL(requested,base),origin=new URL(base).origin;
 if(url.origin!==origin||!(/\.json(?:\.gz)?$/).test(url.pathname))throw new Error('Linked traces must be JSON or evidenced JSON.gz files on this viewer’s origin.');
 const response=await fetcher(url);
 if(!response.ok)throw new Error(`Trace request failed (${response.status}).`);
 if(!url.pathname.endsWith('.json.gz'))return response.json();
 const evidenceURL=new URL(url);evidenceURL.pathname=evidenceURL.pathname.replace(/\.json\.gz$/,'.evidence.json');
 const evidenceResponse=await fetcher(evidenceURL);
 if(!evidenceResponse.ok)throw new Error('Compressed replay evidence sidecar is missing.');
 const evidence=await evidenceResponse.json(),bytes=await response.arrayBuffer();
 const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),n=>n.toString(16).padStart(2,'0')).join('');
 if(evidence.schema!=='stage2-optional-replay-evidence.v1'||digest!==evidence.trace_sha256)throw new Error('Compressed replay does not match its retained evidence digest.');
 if(!evidence.fresh_independent_check?.valid||!evidence.fresh_independent_check?.terminal_requirements_met)throw new Error('Optional replay requires passed physical and terminal checks.');
 if(typeof DecompressionStream!=='function')throw new Error('This browser does not support gzip replay decoding.');
 const text=await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).text();
 const raw=JSON.parse(text);
 return {...raw,validation:{...evidence.fresh_independent_check,status:'passed'},provenance:{...raw.provenance,instance_sha256:evidence.instance_sha256,
  viewer_replay:{posthoc_audit_only:evidence.posthoc_audit_only===true,label:evidence.label,seed_role:evidence.seed_role,horizon_scope:evidence.horizon_scope,evidence_url:evidenceURL.pathname,
   predeclared_first_tape:evidence.predeclared_first_tape===true,selection:evidence.selection,
   original_gzip_sha256:digest,certificate_path:evidence.certificate_path,certificate_sha256:evidence.certificate_sha256,
   checker_sha256:evidence.checker_sha256,activity_data_changed:false,secondary_optimality_gap:evidence.secondary_optimality_gap}}};
}
