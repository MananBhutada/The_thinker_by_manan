/* FounderOS workspace: the graph IS the first screen. */
const FounderWorkspace = (() => {
  const $ = id => document.getElementById(id);
  let graph = { root: { title: "Your startup", summary: "", objective: "" }, nodes: [], edges: [] };
  let mode = "founder", busy = false, panelOpen = false, lastFocus = null, saveTimer = 0;
  const chats = new Map();
  let showIgnored = false;
  const reduced = () => window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  const mobile = () => window.matchMedia && matchMedia("(max-width: 760px)").matches;
  const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;" }[c]));
  const say = t => { const l = $("fwLive"); if (l) { l.textContent = ""; setTimeout(() => l.textContent = t, 30); } };
  const toast = m => (window.App && App.toast) ? App.toast(m) : null;
  const QUICK = {
    root:["What is missing from my startup context?","Where are my biggest blind spots?","What should I validate first?"],
    money:["Where am I financially exposed?","How should I think about this runway?","What assumptions am I making here?"],
    default:["What assumptions am I making here?","What depends on this?","What needs to become true before this?"],
    proposal:["Why might this matter?","How would I answer this?","What would change if the answer is bad?"],
    future_plan:["What needs to become true before this?","What could make this wrong?","What should I validate first?"],
    decision:["Do I actually need this?","What assumptions am I making here?","What is the cheapest way to test this?"]
  };
  function visibleGraph() {
    if (showIgnored) return graph;
    const hide = new Set(graph.nodes.filter(n => n.status === "ignored").map(n => n.id));
    if (!hide.size) return graph;
    return Object.assign({}, graph, { nodes:graph.nodes.filter(n => !hide.has(n.id)), edges:graph.edges.filter(e => !hide.has(e.source) && !hide.has(e.target)) });
  }
  function apply(g, opts={}) { graph = g || graph; const fresh = FounderGraph.setGraph(visibleGraph(), opts); updateChrome(); return fresh; }
  async function load() { try { apply(await API.getGraph(), {initial:true}); } catch(e) { toast("Could not load your map."); apply(graph,{initial:true}); } }
  function updateChrome() {
    const c = FounderGraph.count(); $("fwCount").textContent = graph.nodes.length ? graph.nodes.length+" nodes · "+c.links+" cross-links" : "";
    $("fwRootName").textContent = graph.root.title || "Your startup";
    const ig = graph.nodes.filter(n => n.status === "ignored").length, btn=$("fwIgnoredBtn");
    btn.hidden=!ig; btn.textContent=(showIgnored?"Hide":"Show")+" "+ig+" ignored";
    $("fwEngine").textContent=FounderProvider.label(FounderProvider.current());
  }
  function schedulePositionSave() { clearTimeout(saveTimer); saveTimer=setTimeout(()=>API.saveGraphPositions(FounderGraph.positions()).catch(()=>{}),900); }
  async function map() {
    if(busy)return; const ta=$("fwInput"), text=ta.value.trim(); if(!text){ta.focus();return;}
    const provider=await FounderProvider.get(); if(!provider)return; setBusy(true,"Mapping your thinking…");
    const before=new Set(graph.nodes.map(n=>n.id));
    try { const g=await API.extractGraph(text,provider); ta.value=""; autosize(); const fresh=apply(g,{}); const added=g.nodes.filter(n=>!before.has(n.id)).length;
      say("Added "+added+" new nodes to your map."); toast(added?"Added "+added+" to your map":"Nothing new to add"); markNew(fresh); setTimeout(()=>FounderGraph.fit(true),reduced()?0:900); schedulePositionSave();
    } catch(e) { const m=e&&e.message||"Mapping failed."; if(e&&(e.status===401||e.status===402))FounderProvider.reset(); toast(m); say(m); showDockError(m); } finally { setBusy(false); }
  }
  function markNew(ids){ if(reduced())return; ids.forEach(id=>{const g=document.querySelector('.gn[data-id="'+CSS.escape(id)+'"]');if(g){g.classList.add("is-born");setTimeout(()=>g.classList.remove("is-born"),2600);}}); }
  function setBusy(b,msg){ busy=b; $("fwMapBtn").disabled=b; $("fwMapBtn").setAttribute("aria-busy",String(b)); $("fwMapBtn").querySelector("span").textContent=b?"Mapping…":"Map"; $("fwDock").classList.toggle("is-busy",b); const st=$("fwDockStatus");st.textContent=b?msg:"";st.hidden=!b;if(b)$("fwDockError").hidden=true; }
  function showDockError(m){const e=$("fwDockError");e.textContent=m;e.hidden=false;}
  function autosize(){const ta=$("fwInput");ta.style.height="auto";ta.style.height=Math.min(ta.scrollHeight,mobile()?120:168)+"px";}
  function nodeData(id){return id==="root"?Object.assign({id:"root",type:"root",state:"known",title:graph.root.title},graph.root):graph.nodes.find(n=>n.id===id);}
  function titleOf(id){const n=nodeData(id);return n?n.title:id;}
  function listBlock(label,items){if(!items||!items.length)return "";return '<section class="fp-block"><h3>'+label+'</h3><ul>'+items.map(i=>"<li>"+esc(i)+"</li>").join("")+"</ul></section>";}
  function relatedBlock(id){const nb=FounderGraph.neighbors(id).filter(n=>nodeData(n.id)&&n.id!=="root"),parent=FounderGraph.neighbors(id).find(n=>n.kind==="structural"&&n.dir==="in"),chips=[];
    if(parent)chips.push('<button type="button" class="fp-chip is-parent" data-go="'+esc(parent.id)+'"><i>in</i>'+esc(titleOf(parent.id))+"</button>");
    nb.filter(n=>!(parent&&n.id===parent.id)).forEach(n=>{const rel=n.kind==="structural"?(n.dir==="out"?"contains":"in"):n.kind==="proposal"?"question":(n.dir==="in"&&n.rel==="depends_on"?"needed by":FounderGraph.relText(n.rel));chips.push('<button type="button" class="fp-chip k-'+n.kind+'" data-go="'+esc(n.id)+'"><i>'+esc(rel)+"</i>"+esc(titleOf(n.id))+"</button>");});
    return chips.length?'<section class="fp-block"><h3>Related</h3><div class="fp-chips">'+chips.join("")+"</div></section>":"";
  }
  function capitalText(n){const c=n.capital||{};if(c.amount==null)return "";return(c.currency||"INR")+" "+Number(c.amount).toLocaleString()+(c.status&&c.status!=="none"?" · "+c.status:"");}
  function lensHtml(){const L=[["founder","Founder"],["product","Product"],["people","People"],["money","Money"],["growth","Growth"],["conflict","Conflict"]];return '<div class="fp-lens" role="radiogroup" aria-label="Coaching lens">'+L.map(([k,n])=>'<button type="button" role="radio" aria-checked="'+(k===mode)+'" class="'+(k===mode?"on":"")+'" data-lens="'+k+'">'+n+"</button>").join("")+"</div>";}
  const trunc=(t,n)=>(t.length>n?t.slice(0,n-1)+"…":t);
  function renderPanel(id){
    const n=nodeData(id);
    if(!n) return closePanel();
    const isRoot=id==="root";
    const fam=isRoot?"root":FounderGraph.family(n.type);
    const typeTxt=isRoot?"Startup":FounderGraph.typeLabel(n.type);
    const stateTxt=isRoot?"":(n.proposal?"proposed":n.state);
    const cap=isRoot?"":capitalText(n);

    let h=`<header class="fp-head t-${fam}">
      <div class="fp-meta">
        <span class="fp-type"><b class="fp-dot"></b>${esc(typeTxt)}</span>
        ${stateTxt ? `<span class="fp-state s-${esc(n.state)}">${esc(stateTxt)}</span>` : ""}
      </div>
      <h2 id="fpTitle" tabindex="-1">${esc(n.title)}</h2>
    </header>
    <div class="fp-scroll" id="fpScroll">`;

    if(n.proposal){
      h+=`<section class="fp-proposal">
        <p><strong>AI-proposed blind spot.</strong> This is a question, not a fact. You decide whether it belongs on your map.</p>
        <div class="fp-actions">
          <button type="button" class="fp-btn is-primary" data-prop="accept">Accept</button>
          <button type="button" class="fp-btn" data-prop="ignore">Ignore</button>
          <button type="button" class="fp-btn is-danger" data-prop="reject">Reject</button>
        </div>
      </section>`;
    }

    const ctx=isRoot?(n.summary||""):(n.details||n.summary||"");
    h+=`<section class="fp-block">
      <h3>Context</h3>
      <p class="fp-ctx">${ctx?esc(ctx):'<span class="fp-faint">Nothing recorded yet. Tell FounderOS more, or ask below.</span>'}</p>
      ${isRoot&&n.objective?`<p class="fp-objective"><span>Objective</span>${esc(n.objective)}</p>`:""}
    </section>`;

    if(!isRoot){
      h+=`<div class="fp-stats">
        <div>
          <span>Confidence</span>
          <div class="fp-bar" role="img" aria-label="Confidence ${n.confidence||0} percent"><i style="width:${n.confidence||0}%"></i></div>
          <b>${n.confidence||0}%</b>
        </div>
        ${cap?`<div><span>Capital</span><b>${esc(cap)}</b></div>`:""}
      </div>`;
      h+=listBlock("Evidence",n.evidence)+listBlock("Assumptions",n.assumptions)+listBlock("Dependencies",n.dependencies);
    }

    h+=relatedBlock(id);
    if(n.createdFrom) h+=`<p class="fp-origin">From: ${esc(n.createdFrom)}</p>`;
    h+=`<section class="fp-chat" aria-label="Chat about ${esc(n.title)}">
      <div class="fp-chat-head"><h3>Chat about this</h3>${lensHtml()}</div>
      <div class="fp-thread" id="fpThread" aria-live="polite"></div>
    </section></div>`;

    const q=isRoot?QUICK.root:(n.proposal?QUICK.proposal:(QUICK[n.type]||(fam==="money"?QUICK.money:QUICK.default)));
    h+=`<footer class="fp-foot">
      <div class="fp-quick">${q.map(t=>`<button type="button" class="fp-q">${esc(t)}</button>`).join("")}</div>
      <div class="fp-ask">
        <label class="sr-only" for="fpInput">Ask about ${esc(n.title)}</label>
        <textarea id="fpInput" rows="1" maxlength="1500" placeholder="Ask about ${esc(trunc(n.title,28))}…"></textarea>
        <button type="button" id="fpSend" class="fp-send" aria-label="Send question">↑</button>
      </div>
      <div class="fp-row">
        <button type="button" class="fp-link" id="fpEngine">${esc(FounderProvider.label(FounderProvider.current()))}</button>
        ${isRoot?"":'<button type="button" class="fp-link is-danger" id="fpDelete">Remove node</button>'}
      </div>
    </footer>`;

    const p=$("fwPanel");
    p.innerHTML=h;
    p.dataset.node=id;
    bindPanel(id);
    renderThread(id);
  }
  function bindPanel(id){const p=$("fwPanel");p.querySelectorAll("[data-go]").forEach(b=>b.onclick=()=>FounderGraph.select(b.dataset.go));p.querySelectorAll("[data-lens]").forEach(b=>b.onclick=()=>{mode=b.dataset.lens;p.querySelectorAll("[data-lens]").forEach(x=>{const on=x.dataset.lens===mode;x.classList.toggle("on",on);x.setAttribute("aria-checked",String(on));});});p.querySelectorAll("[data-prop]").forEach(b=>b.onclick=()=>resolveProposal(id,b.dataset.prop));p.querySelectorAll(".fp-q").forEach(b=>b.onclick=()=>ask(id,b.textContent));const input=$("fpInput");input.addEventListener("input",()=>{input.style.height="auto";input.style.height=Math.min(input.scrollHeight,110)+"px";});input.addEventListener("keydown",e=>{if(e.key==="Enter"&&!e.shiftKey&&!e.isComposing){e.preventDefault();ask(id,input.value);}});$("fpSend").onclick=()=>ask(id,input.value);$("fpEngine").onclick=async()=>{const pv=await FounderProvider.get({force:true});updateChrome();if(pv)$("fpEngine").textContent=FounderProvider.label(pv);};const del=$("fpDelete");if(del)del.onclick=async()=>{const ok=window.App&&App.confirm?await App.confirm("Remove “"+titleOf(id)+"” from your map? Its children stay and move up a level."):confirm("Remove this node?");if(!ok)return;try{const g=await API.deleteGraphNode(id);closePanel();apply(g,{});say("Node removed");}catch(e){toast(e.message||"Could not remove");}};}
  function openPanel(id,opts={}){lastFocus=opts.source==="keyboard"?document.querySelector('.gn[data-id="'+CSS.escape(id)+'"]'):lastFocus;const wasOpen=panelOpen;panelOpen=true;const p=$("fwPanel");renderPanel(id);p.classList.add("is-open");p.setAttribute("aria-hidden","false");$("fwWorkspace").classList.add("has-panel");p.classList.remove("is-peek");syncInsets();if(opts.source==="keyboard"||opts.focusPanel)setTimeout(()=>$("fpTitle")&&$("fpTitle").focus({preventScroll:true}),40);if(!wasOpen)FounderGraph.focusOn(id);say("Selected "+titleOf(id));}
  function closePanel(){if(!panelOpen)return;panelOpen=false;const p=$("fwPanel");p.classList.remove("is-open");p.setAttribute("aria-hidden","true");$("fwWorkspace").classList.remove("has-panel");syncInsets();if(FounderGraph.selected())FounderGraph.select(null,{silent:true,focus:false});if(lastFocus&&document.contains(lastFocus))lastFocus.focus({preventScroll:true});lastFocus=null;setTimeout(()=>FounderGraph.fit(true),reduced()?0:60);}
  function syncInsets(){const r=$("fwStage").getBoundingClientRect();if(panelOpen&&!mobile())FounderGraph.setInsets({right:Math.min(430,r.width*.46)+12});else if(panelOpen&&mobile())FounderGraph.setInsets({bottom:Math.round(r.height*.58)+90,top:56});else FounderGraph.setInsets({});}
  async function resolveProposal(id,action){try{const g=await API.resolveProposal(id,action);apply(g,{});toast(({accept:"Accepted",reject:"Rejected",ignore:"Ignored"})[action]+" blind spot");if(action==="reject"||(action==="ignore"&&!showIgnored))closePanel();else FounderGraph.select(id,{focus:false});schedulePositionSave();}catch(e){toast(e.message||"Could not update");}}
  function renderThread(id){const t=$("fpThread");if(!t)return;const msgs=chats.get(id)||[];if(!msgs.length){t.innerHTML='<p class="fp-hint">Ask anything about this '+(id==="root"?"startup":"node")+". The coach reads its parents, links, assumptions and risks, not just its title.</p>";return;}t.innerHTML=msgs.map(m=>m.role==="user"?'<div class="fm fm-user"><p>'+esc(m.text)+"</p></div>":m.pending?'<div class="fm fm-coach is-pending"><span class="fp-dots" aria-label="Thinking"><i></i><i></i><i></i></span></div>':'<div class="fm fm-coach'+(m.error?" is-error":"")+'">'+coachHtml(m)+"</div>").join("");const sc=$("fpScroll");if(sc)requestAnimationFrame(()=>{const last=t.lastElementChild;if(last)sc.scrollTop=Math.max(0,last.offsetTop-120);});}
  function tagged(line){const m=/^\s*([A-Z][A-Z \/&-]{2,28}):\s*(.+)$/s.exec(line);return m?'<li><b class="fm-tag">'+esc(m[1].toLowerCase())+"</b> "+esc(m[2])+"</li>":"<li>"+esc(line)+"</li>";}
  function coachHtml(m){if(m.error)return"<p>"+esc(m.text)+"</p>";const b=m.brief||{};let h="<p>"+esc(m.text||b.summary||"")+"</p>";const sec=(title,arr)=>arr&&arr.length?'<div class="fm-sec"><h4>'+title+"</h4><ul>"+arr.map(x=>tagged(typeof x==="string"?x:(x.text||x.title||JSON.stringify(x)))).join("")+"</ul></div>":"";return h+sec("Reasoning",(b.perspectives||[]).slice(0,5))+sec("Watch out",(b.risks||[]).slice(0,4))+sec("Next questions",(b.nextSteps||b.next_steps||[]).slice(0,4));}
  async function ask(id,text){text=(text||"").trim();if(!text||busy)return;const provider=await FounderProvider.get();if(!provider)return;const list=chats.get(id)||[];chats.set(id,list);const history=list.filter(m=>!m.pending&&!m.error).slice(-6).map(m=>({role:m.role,text:(m.text||"").slice(0,600)}));list.push({role:"user",text});const pending={role:"coach",pending:true};list.push(pending);const input=$("fpInput");if(input&&$("fwPanel").dataset.node===id){input.value="";input.style.height="auto";}renderThread(id);busy=true;$("fpSend")&&($("fpSend").disabled=true);try{const res=await API.graphChat({nodeId:id,question:text,mode,history},provider);list.splice(list.indexOf(pending),1,{role:"coach",text:res.reply||(res.brief&&res.brief.summary)||"",brief:res.brief||res.result});say("Coach replied");}catch(e){if(e&&(e.status===401||e.status===402))FounderProvider.reset();list.splice(list.indexOf(pending),1,{role:"coach",error:true,text:e&&e.message||"The coach could not answer. Try again."});}finally{busy=false;if($("fwPanel").dataset.node===id){renderThread(id);$("fpSend")&&($("fpSend").disabled=false);}updateChrome();}}
  function bindSidebar(){
    document.querySelectorAll(".nav-item").forEach(btn=>{
      btn.onclick=async()=>{
        const tab=btn.dataset.tab;
        document.getElementById("sidebar")?.classList.remove("open");
        if(tab==="settings"){
          await FounderProvider.get({force:true});
          updateChrome();
          return;
        }
        if(tab==="archive"){
          const body=document.createElement("div");
          body.innerHTML='<h2 style="margin:0 0 8px">Archive</h2><p style="color:var(--ink2);line-height:1.6">FounderOS is currently keeping your living Founder Graph as the source of truth. Your workspace is isolated from other browsers.</p><p style="color:var(--ink3);font-size:12px">A full decision and graph history view can be added without changing the graph architecture.</p>';
          App.openModal(body);
        }
      };
    });
  }
  function init(){bindSidebar();FounderGraph.init({svg:$("fwSvg"),stage:$("fwStage"),tip:$("fwTip"),graph});FounderGraph.on("select",(id,opts)=>{if(id)openPanel(id,opts||{});else if(!(opts&&opts.silent))closePanel();});FounderGraph.on("open-chat",id=>{openPanel(id,{focusPanel:true});setTimeout(()=>$("fpInput")&&$("fpInput").focus(),120);});FounderGraph.on("moved",schedulePositionSave);$("fwDock").addEventListener("submit",e=>{e.preventDefault();map();});$("fwInput").addEventListener("input",autosize);$("fwInput").addEventListener("keydown",e=>{if((e.key==="Enter"&&(e.metaKey||e.ctrlKey))||(e.key==="Enter"&&!e.shiftKey&&!e.isComposing&&!mobile())){e.preventDefault();map();}});$("fwFit").onclick=()=>FounderGraph.fit(true);$("fwZoomIn").onclick=()=>FounderGraph.zoomBy(1.3);$("fwZoomOut").onclick=()=>FounderGraph.zoomBy(1/1.3);$("fwRefresh").onclick=async()=>{await load();say("Map refreshed")};$("fwRootBtn").onclick=()=>FounderGraph.select("root",{source:"pointer"});$("fwEngine").onclick=async()=>{await FounderProvider.get({force:true});updateChrome();};$("fwIgnoredBtn").onclick=()=>{showIgnored=!showIgnored;apply(graph,{})};$("fwPanelClose").onclick=()=>closePanel();$("fwPanelGrip").onclick=()=>$("fwPanel").classList.toggle("is-peek");document.querySelectorAll("[data-example]").forEach(b=>b.onclick=()=>{$("fwInput").value=b.dataset.example;autosize();$("fwInput").focus();});document.addEventListener("keydown",e=>{if(e.key!=="Escape")return;if(document.querySelector(".modal-overlay.show"))return;if(panelOpen){e.preventDefault();closePanel();}});window.addEventListener("resize",()=>syncInsets());load();const q=new URLSearchParams(location.search);const seed=q.get("text");if(location.pathname==="/map"&&seed){const ta=$("fwInput");if(ta){ta.value=seed;autosize();setTimeout(()=>map(),120);}}}
  return {init,load};
})();
document.addEventListener("DOMContentLoaded",()=>FounderWorkspace.init());
