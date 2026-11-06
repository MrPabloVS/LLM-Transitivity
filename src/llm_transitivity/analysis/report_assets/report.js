"use strict";
const byId = id => document.getElementById(id);
const state = {summary: null, cases: [], page: 0, request: 0};
const metrics = ["samples","matched","disagreed","strict","answered","content_filter","empty","ambiguous","invalid_format","error"];
function element(tag, text) { const el=document.createElement(tag); if(text!==undefined) el.textContent=String(text); return el; }
function fraction(n,d) { return `${n.toLocaleString()}/${d.toLocaleString()} (${d ? (100*n/d).toFixed(2)+"%" : "undefined"})`; }
async function jsonFile(path) { const response=await fetch(path); if(!response.ok) throw new Error(`Cannot load ${path} (${response.status})`); return response.json(); }
function addSelect(container,id,label,values) { const wrapper=element("label",label); const select=element("select");select.id=id;select.append(new Option("All","all")); values.forEach(v=>select.append(new Option(v,v)));wrapper.append(select);container.append(wrapper);select.addEventListener("change",aggregate); }
function aggregate() {
 const s=state.summary; const definitions=new Map(s.stratum_definitions.map(d=>[d.stratum,d])); const fields=["family","frequency","tense","canonical","validity","formulation","dataset"];
 const totals=new Map(s.models.map(m=>[m,Object.fromEntries(metrics.map(k=>[k,0]))]));
 for(const row of s.breakdowns.stratum){const d=definitions.get(row.condition); if(fields.some(k=>byId(`agg-${k}`).value!=="all"&&byId(`agg-${k}`).value!==d[k])) continue; const sum=totals.get(row.model);metrics.forEach(k=>sum[k]+=row[k]);}
 const body=byId("aggregate-rows");body.replaceChildren();let count=0;
 for(const [model,r] of totals){if(byId("agg-model").value!=="all"&&byId("agg-model").value!==model)continue;const tr=element("tr");[model,fraction(r.matched,r.answered),fraction(r.answered,r.samples),fraction(r.strict,r.samples),fraction(r.matched,r.samples),r.content_filter,r.samples-r.answered-r.content_filter].forEach(v=>tr.append(element("td",v)));body.append(tr);count+=r.samples;}
 byId("aggregate-status").textContent=`${count.toLocaleString()} model/case results in this selection. Each row has its own explicit denominator.`;
}
function filteredCases(){const outcome=byId("case-outcome").value;const validity=byId("case-validity").value;const canonical=byId("case-canonical").value;const uid=byId("case-uid").value.trim();return state.cases.filter(c=>{
 if(validity!=="all"&&c.validity!==validity)return false;if(canonical!=="all"&&c.canonical!==canonical)return false;if(uid&&!c.uid.includes(uid))return false;
 if(outcome==="different")return new Set(c.responses.filter(r=>r.status==="answered").map(r=>r.answer)).size>1;
 if(outcome==="content_filter")return c.responses.some(r=>r.status==="content_filter");
 if(outcome==="non-strict")return c.responses.some(r=>r.status==="answered"&&!r.strict);
 if(outcome==="uninterpretable")return c.responses.some(r=>r.status!=="answered");
 if(outcome==="all-match")return c.responses.every(r=>r.matched===1);return true;
});}
function caseBody(c){const div=element("div");div.className="case-body";div.append(element("p",`Source label: ${c.validity}; target: ${c.target}. ${c.family} / ${c.frequency} / ${c.tense} / ${c.canonical}. ${c.formulation}`),element("pre",c.prompt),element("p",`Original: ${c.original_path}, row ${c.row_number}. Source identifiers: ${JSON.stringify(c.source_id)}`));
 const table=element("table"),head=element("tr");["Model","Interpreted answer","Outcome","Strict format"].forEach(v=>head.append(element("th",v)));table.append(head);
 for(const r of c.responses){const tr=element("tr");[r.model,r.answer===null?"not interpreted":r.answer,r.status==="answered"?(r.matched?"match":"disagreement"):r.status,Boolean(r.strict)].forEach(v=>tr.append(element("td",v)));table.append(tr);}div.append(table);
 for(const r of c.responses){const details=element("details");details.append(element("summary",`${r.model} — original response`),element("pre",r.raw),element("p",`Native log: ${r.log}; SHA-256: ${r.log_hash}`));div.append(details);}div.append(element("p",`Sentence SHA-256: ${c.sentence_hash}. Original record SHA-256: ${c.original_hash}.`));return div;
}
function showCases(){const rows=filteredCases(),pages=Math.max(1,Math.ceil(rows.length/50));state.page=Math.min(state.page,pages-1);byId("case-list").replaceChildren();
 for(const c of rows.slice(state.page*50,(state.page+1)*50)){const details=element("details");details.className="case";details.append(element("summary",`${c.uid} · ${c.validity} · ${c.canonical}`));details.addEventListener("toggle",()=>{if(details.open&&!details.dataset.loaded){details.append(caseBody(c));details.dataset.loaded="yes";}});byId("case-list").append(details);}
 byId("case-status").textContent=`${rows.length.toLocaleString()} matching cases in ${byId("case-dataset").value}. Each case has six saved responses.`;byId("page-number").textContent=`Page ${state.page+1} of ${pages}`;byId("previous").disabled=state.page===0;byId("next").disabled=state.page>=pages-1;
}
async function loadCases(){const token=++state.request;byId("case-status").textContent="Loading local case data…";try{const rows=await jsonFile(`data/${encodeURIComponent(byId("case-dataset").value)}.json`);if(token!==state.request)return;state.cases=rows;state.page=0;showCases();}catch(e){byId("case-status").textContent=e.message;byId("case-status").className="error";}}
async function init(){try{state.summary=await jsonFile("summary.json");const s=state.summary;const filters=byId("aggregate-filters");addSelect(filters,"agg-model","Model",s.models);
 for(const key of ["family","frequency","tense","canonical","validity","formulation","dataset"]){addSelect(filters,`agg-${key}`,key,[...new Set(s.stratum_definitions.map(d=>d[key]))].sort());}aggregate();
 s.cases.forEach(d=>byId("case-dataset").append(new Option(d.dataset,d.dataset)));byId("case-dataset").addEventListener("change",loadCases);
 for(const id of ["case-outcome","case-validity","case-canonical"]){byId(id).addEventListener("change",()=>{state.page=0;showCases();});}
 byId("case-uid").addEventListener("input",()=>{const dataset=byId("case-uid").value.trim().split(":")[0];if(s.cases.some(d=>d.dataset===dataset)&&byId("case-dataset").value!==dataset){byId("case-dataset").value=dataset;loadCases();}else{state.page=0;showCases();}});
 byId("previous").addEventListener("click",()=>{state.page--;showCases();});byId("next").addEventListener("click",()=>{state.page++;showCases();});await loadCases();
 }catch(e){byId("aggregate-status").textContent=`${e.message}. Serve this folder through a local HTTP server; no external service is needed.`;byId("aggregate-status").className="error";}}
init();
