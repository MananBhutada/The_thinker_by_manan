const FounderGraph = (() => {
  const $ = id => document.getElementById(id);
  let graph = { root:{title:"Your startup",summary:""}, nodes:[], edges:[], insights:[], questions:[] };
  let activeNode = null;

  const labels = {
    goal:"Goal", idea:"Idea", initiative:"Initiative", problem:"Problem", customer:"Customer",
    product:"Product", market:"Market", decision:"Decision", option:"Option", risk:"Risk",
    dependency:"Dependency", constraint:"Constraint", fact:"Fact", assumption:"Assumption",
    metric:"Metric", experiment:"Experiment", unknown:"Unknown", investment:"Investment",
    cost:"Cost", revenue:"Revenue", runway:"Runway"
  };

  async function load() {
    try { graph = await API.getGraph(); render(); }
    catch (e) { render(); }
  }

  function svg(tag, attrs={}, text="") {
    const el = document.createElementNS("http://www.w3.org/2000/svg", tag);
    Object.entries(attrs).forEach(([k,v]) => el.setAttribute(k,v));
    if (text) el.textContent = text;
    return el;
  }

  function layout(nodes, edges) {
    const ids = new Set(nodes.map(n => n.id));
    const parent = {};
    // Use dependency / support semantics to create the visible tree.
    edges.forEach(e => {
      if (!ids.has(e.source) || !ids.has(e.target) || parent[e.source] || parent[e.target]) return;
      if (e.relationship === "depends_on") parent[e.source] = e.target;
      else if (["supports","unlocks","causes","measures","tests"].includes(e.relationship)) parent[e.target] = e.source;
      else if (["alternative_to","conflicts_with"].includes(e.relationship)) parent[e.target] = e.source;
    });

    // Remove cycles.
    nodes.forEach(n => {
      const seen = new Set([n.id]);
      let p = parent[n.id];
      while (p) {
        if (seen.has(p)) { delete parent[n.id]; break; }
        seen.add(p); p = parent[p];
      }
    });

    const children = {};
    nodes.forEach(n => children[n.id] = []);
    nodes.forEach(n => { if (parent[n.id] && children[parent[n.id]]) children[parent[n.id]].push(n.id); });

    const level = {};
    const queue = nodes.filter(n => !parent[n.id]).map(n => [n.id,1]);
    while (queue.length) {
      const [id,l] = queue.shift();
      if (level[id]) continue;
      level[id] = Math.min(l,4);
      (children[id] || []).forEach(child => queue.push([child,l+1]));
    }
    nodes.forEach(n => { if (!level[n.id]) level[n.id]=1; });

    const buckets = {1:[],2:[],3:[],4:[]};
    nodes.forEach(n => buckets[level[n.id]].push(n));

    const pos = {};
    const width = 980;
    const y = {1:165,2:300,3:435,4:570};
    [1,2,3,4].forEach(l => {
      const arr = buckets[l];
      const step = width / Math.max(arr.length,1);
      arr.forEach((n,i) => {
        pos[n.id] = { x: 40 + step*(i+.5), y:y[l] };
      });
    });
    return { parent, children, level, pos };
  }

  function edgePath(a,b,vertical=true) {
    if (vertical) {
      const mid = (a.y+b.y)/2;
      return "M "+a.x+" "+a.y+" C "+a.x+" "+mid+" "+b.x+" "+mid+" "+b.x+" "+b.y;
    }
    return "M "+a.x+" "+a.y+" C "+((a.x+b.x)/2)+" "+a.y+" "+((a.x+b.x)/2)+" "+b.y+" "+b.x+" "+b.y;
  }

  function render() {
    const canvas = $("founderGraphSvg");
    if (!canvas) return;
    const nodes = Array.isArray(graph.nodes) ? graph.nodes : [];
    const edges = Array.isArray(graph.edges) ? graph.edges : [];
    const empty = $("graphEmpty");
    if (empty) empty.hidden = nodes.length > 0;
    canvas.innerHTML = "";

    const tree = layout(nodes,edges);
    const {parent,pos} = tree;

    // Root = the founder's startup context.
    const root = { x:540, y:55 };
    const rootG = svg("g",{class:"mind-root"});
    rootG.appendChild(svg("rect",{x:root.x-110,y:root.y-24,width:220,height:48,rx:15,class:"root-card"}));
    rootG.appendChild(svg("text",{x:root.x,y:root.y-2,class:"root-title"},String(graph.root?.title || "Your startup").slice(0,30)));
    rootG.appendChild(svg("text",{x:root.x,y:root.y+14,class:"root-label"},"STARTUP CONTEXT"));
    canvas.appendChild(rootG);

    // Solid tree branches: what belongs under what.
    nodes.filter(n => !parent[n.id]).forEach(n => {
      const p=pos[n.id];
      if (!p) return;
      canvas.appendChild(svg("path",{d:edgePath({x:root.x,y:root.y+24},{x:p.x,y:p.y-23}),class:"mind-edge tree-edge"}));
    });
    nodes.forEach(n => {
      const pid=parent[n.id];
      if (!pid || !pos[pid] || !pos[n.id]) return;
      canvas.appendChild(svg("path",{d:edgePath({x:pos[pid].x,y:pos[pid].y+22},{x:pos[n.id].x,y:pos[n.id].y-22}),class:"mind-edge tree-edge"}));
    });

    // Dashed links: related, but not part of the hierarchy.
    edges.forEach(e => {
      const a=pos[e.source], b=pos[e.target];
      if (!a || !b) return;
      const isTree = parent[e.source]===e.target || parent[e.target]===e.source;
      if (isTree) return;
      canvas.appendChild(svg("path",{
        d:edgePath({x:a.x,y:a.y},{x:b.x,y:b.y},false),
        class:"mind-edge semantic-edge "+(e.relationship||"")
      }));
    });

    nodes.forEach(n => {
      const p=pos[n.id];
      if (!p) return;
      const g=svg("g",{
        class:"mind-node type-"+(n.type||"idea")+(activeNode?.id===n.id?" is-active":""),
        transform:"translate("+p.x+" "+p.y+")",
        tabindex:"0",role:"button","aria-label":"Open "+n.title
      });
      g.appendChild(svg("rect",{x:-76,y:-22,width:152,height:44,rx:11,class:"node-card"}));
      g.appendChild(svg("circle",{cx:-63,cy:-8,r:4,class:"node-dot"}));
      g.appendChild(svg("text",{x:-53,y:-5,class:"node-title"},String(n.title||"Untitled").slice(0,25)));
      g.appendChild(svg("text",{x:-53,y:12,class:"node-meta"},(labels[n.type]||n.type||"Idea")+" · "+(n.state||"unknown")));
      g.addEventListener("click",()=>inspect(n));
      g.addEventListener("keydown",e=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();inspect(n);}});
      canvas.appendChild(g);
    });

    // Small context label for the root summary.
    if (graph.root?.summary) {
      canvas.appendChild(svg("text",{x:540,y:92,class:"root-summary"},String(graph.root.summary).slice(0,110)));
    }
  }

  function escapeHtml(v) {
    return String(v ?? "").replace(/[&<>"']/g,ch=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[ch]));
  }

  function inspect(n) {
    activeNode=n;
    render();
    const box=$("nodeInspector");
    if (!box) return;
    const capital=n.capital && n.capital.amount!=null
      ? (n.capital.currency||"INR")+" "+Number(n.capital.amount).toLocaleString("en-IN")+" · "+(n.capital.status||"estimated")
      : "Not recorded";

    box.innerHTML =
      '<button class="inspector-close" aria-label="Close">×</button>'+
      '<span class="inspector-type">'+escapeHtml(labels[n.type]||n.type||"Idea")+'</span>'+
      '<h3>'+escapeHtml(n.title)+'</h3>'+
      '<p class="inspector-context">'+escapeHtml(n.details||"No context recorded yet.")+'</p>'+
      '<div class="inspector-meta"><span>STATE</span><b>'+escapeHtml(n.state||"unknown")+'</b></div>'+
      '<div class="inspector-meta"><span>CONFIDENCE</span><b>'+escapeHtml(n.confidence||0)+'%</b></div>'+
      '<div class="inspector-meta"><span>CAPITAL</span><b>'+escapeHtml(capital)+'</b></div>'+
      '<div class="node-chat">'+
        '<div class="node-chat-label">CHAT WITH THIS NODE</div>'+
        '<textarea id="nodeChatInput" rows="2" placeholder="Ask about '+escapeHtml(n.title)+'…"></textarea>'+
        '<button type="button" id="nodeChatSend">Ask ↗</button>'+
        '<div id="nodeChatReply" class="node-chat-reply" hidden></div>'+
      '</div>';

    box.hidden=false;
    box.querySelector(".inspector-close").onclick=()=>{activeNode=null;box.hidden=true;render();};
    box.querySelector("#nodeChatSend").onclick=()=>chatWithNode(n);
    box.querySelector("#nodeChatInput").addEventListener("keydown",e=>{
      if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();chatWithNode(n);}
    });
  }

  async function chatWithNode(n) {
    const input=$("nodeChatInput"), reply=$("nodeChatReply"), btn=$("nodeChatSend");
    if (!input || !input.value.trim()) return;
    const question=input.value.trim();
    const provider=await FounderProvider.open();
    if (!provider) return;
    btn.disabled=true; btn.textContent="Thinking…"; reply.hidden=false; reply.textContent="";
    const context =
      "NODE CONTEXT\\n"+
      "Title: "+n.title+"\\n"+
      "Type: "+(n.type||"idea")+"\\n"+
      "State: "+(n.state||"unknown")+"\\n"+
      "Details: "+(n.details||"none")+"\\n"+
      "Confidence: "+(n.confidence||0)+"%\\n\\n"+
      "FOUNDER QUESTION\\n"+question;
    const extra={provider:provider.provider};
    if(provider.provider==="byok"){
      extra.apiKey=provider.apiKey;
      extra.llmModel=provider.llmModel;
      extra.llmBaseUrl=provider.llmBaseUrl;
    }
    try {
      const response=await API.chat(context,"founder",extra);
      reply.textContent=response.reply||"No response returned.";
    } catch(e) {
      reply.textContent=e.message||"Node chat failed.";
    } finally {
      btn.disabled=false; btn.textContent="Ask ↗";
    }
  }

  async function extract() {
    const input=$("graphInput");
    if(!input || !input.value.trim()) return;
    const provider=await FounderProvider.open();
    if(!provider) return;
    const btn=$("graphExtractBtn");
    btn.disabled=true; btn.textContent="Mapping…";
    try {
      graph=await API.extractGraph(input.value.trim(),provider);
      activeNode=null;
      render();
      input.value="";
      App.toast("Your thinking is mapped.");
    } catch(e) { App.toast(e.message||"Graph extraction failed"); }
    finally { btn.disabled=false; btn.textContent="Map my thinking ↗"; }
  }

  function init() {
    const btn=$("graphExtractBtn");
    if(btn) btn.onclick=extract;
    const refresh=$("graphRefreshBtn");
    if(refresh) refresh.onclick=load;
    render();
    load();
  }

  return {init,load,render};
})();