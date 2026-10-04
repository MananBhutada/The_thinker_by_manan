const FounderGraph = (() => {
  const $ = id => document.getElementById(id);
  let graph = {root:{title:"Your Startup"},nodes:[],edges:[],insights:[]};

  const labels = {goal:"Goal",idea:"Idea",initiative:"Initiative",problem:"Problem",customer:"Customer",product:"Product",market:"Market",decision:"Decision",option:"Option",risk:"Risk",dependency:"Dependency",constraint:"Constraint",fact:"Fact",assumption:"Assumption",metric:"Metric",experiment:"Experiment",unknown:"Unknown",investment:"Investment",cost:"Cost",revenue:"Revenue",runway:"Runway"};

  async function load(){ try { graph=await API.getGraph(); render(); } catch(e){} }

  function render(){
    const svg=$("founderGraphSvg"), list=$("graphNodeList"), insights=$("graphInsights");
    if(!svg||!list)return;
    svg.innerHTML="";
    const nodes=graph.nodes||[], cx=450, cy=280, pos={};
    nodes.forEach((n,i)=>{
      const ring=i<6?1:2, count=ring===1?Math.min(nodes.length,6):Math.max(1,nodes.length-6);
      const idx=ring===1?i:i-6, radius=ring===1?155:245;
      const angle=-Math.PI/2+idx*Math.PI*2/count;
      pos[n.id]={x:cx+Math.cos(angle)*radius,y:cy+Math.sin(angle)*radius};
    });
    (graph.edges||[]).forEach(e=>{
      const a=pos[e.source],b=pos[e.target]; if(!a||!b)return;
      const line=document.createElementNS("http://www.w3.org/2000/svg","line");
      line.setAttribute("x1",a.x);line.setAttribute("y1",a.y);line.setAttribute("x2",b.x);line.setAttribute("y2",b.y);
      line.setAttribute("class","graph-edge");line.setAttribute("data-relationship",e.relationship);svg.appendChild(line);
    });
    const rg=document.createElementNS("http://www.w3.org/2000/svg","g");
    rg.setAttribute("class","graph-root");
    const circle=document.createElementNS("http://www.w3.org/2000/svg","circle");circle.setAttribute("cx",cx);circle.setAttribute("cy",cy);circle.setAttribute("r",62);rg.appendChild(circle);
    const rt=document.createElementNS("http://www.w3.org/2000/svg","text");rt.setAttribute("x",cx);rt.setAttribute("y",cy-5);rt.textContent=(graph.root&&graph.root.title)||"Your Startup";rg.appendChild(rt);
    const rs=document.createElementNS("http://www.w3.org/2000/svg","text");rs.setAttribute("x",cx);rs.setAttribute("y",cy+15);rs.setAttribute("class","root-sub");rs.textContent="STARTUP";rg.appendChild(rs);svg.appendChild(rg);
    nodes.forEach(n=>{
      const p=pos[n.id],g=document.createElementNS("http://www.w3.org/2000/svg","g");g.setAttribute("class","graph-node");g.setAttribute("transform","translate("+p.x+" "+p.y+")");
      const c=document.createElementNS("http://www.w3.org/2000/svg","circle");c.setAttribute("r",39);g.appendChild(c);
      const t=document.createElementNS("http://www.w3.org/2000/svg","text");t.setAttribute("class","node-title");t.textContent=n.title.slice(0,18);g.appendChild(t);
      const s=document.createElementNS("http://www.w3.org/2000/svg","text");s.setAttribute("class","node-type");s.textContent=labels[n.type]||n.type;g.appendChild(s);
      g.onclick=()=>detail(n);svg.appendChild(g);
    });
    list.innerHTML="";
    nodes.forEach(n=>{
      const b=document.createElement("button");b.className="graph-list-item";
      const strong=document.createElement("strong"),span=document.createElement("span"),small=document.createElement("small");
      strong.textContent=n.title;span.textContent=labels[n.type]||n.type;small.textContent=(n.state||"unknown").toUpperCase();
      b.appendChild(strong);b.appendChild(span);b.appendChild(small);b.onclick=()=>detail(n);list.appendChild(b);
    });
    if(insights){insights.innerHTML="";(graph.insights||[]).forEach(x=>{const li=document.createElement("li");li.textContent=x;insights.appendChild(li);});}
  }

  function detail(n){
    const body=document.createElement("div");
    body.innerHTML='<div class="graph-detail"><div class="graph-detail-type"></div><h3></h3><p class="graph-detail-copy"></p><div class="graph-detail-grid"><div><b>State</b><span></span></div><div><b>Confidence</b><span></span></div><div><b>Capital</b><span></span></div></div></div>';
    body.querySelector(".graph-detail-type").textContent=labels[n.type]||n.type;
    body.querySelector("h3").textContent=n.title;
    body.querySelector(".graph-detail-copy").textContent=n.details||"No supporting context recorded yet.";
    body.querySelector(".graph-detail-grid div:nth-child(1) span").textContent=n.state||"unknown";
    body.querySelector(".graph-detail-grid div:nth-child(2) span").textContent=(n.confidence||0)+"%";
    const cap=n.capital&&n.capital.amount!=null?n.capital.currency+" "+Number(n.capital.amount).toLocaleString("en-IN")+" · "+n.capital.status:"None recorded";
    body.querySelector(".graph-detail-grid div:nth-child(3) span").textContent=cap;
    App.openModal(body,{title:"Founder Graph"});
  }

  async function extract(){
    const input=$("graphInput");if(!input||!input.value.trim())return;
    const provider=await FounderProvider.open();if(!provider)return;
    const btn=$("graphExtractBtn");btn.disabled=true;btn.textContent="Mapping…";
    try{graph=await API.extractGraph(input.value.trim(),provider);render();input.value="";}catch(e){App.toast(e.message||"Graph extraction failed");}
    finally{btn.disabled=false;btn.textContent="Map my thinking";}
  }

  function init(){if($("graphExtractBtn"))$("graphExtractBtn").onclick=extract;if($("graphRefreshBtn"))$("graphRefreshBtn").onclick=load;load();}
  return {init,load,render};
})();