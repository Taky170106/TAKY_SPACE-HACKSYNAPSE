"""Renders the SignGuard console — modern pixel-neobrutalism UI (self-contained)."""
from __future__ import annotations

_HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>SignGuard AI — Console</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
<link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&family=VT323&display=swap" rel="stylesheet"/>
<style>
  :root{
    --bg:#04080a; --card:#0a1218; --card2:#0b141b; --ink:#d6ffe9; --muted:#6f9d88; --dim:#3f5c50;
    --pink:#ff3b6b; --lime:#00ff9c; --sky:#00e0ff; --yellow:#ffe600; --purple:#b06bff;
    --orange:#ff9f1c; --red:#ff3b3b; --green:#00ff9c;
    --pix:"Press Start 2P",monospace; --term:"VT323","Courier New",monospace;
    --b:2px solid #12e39c; --sh:0 0 12px rgba(0,255,156,.20); --sh-sm:0 0 8px rgba(0,255,156,.16);
  }
  *{box-sizing:border-box;image-rendering:pixelated}
  html,body{margin:0}
  body{background:var(--bg);color:var(--ink);font-family:var(--term);font-size:20px;line-height:1.15;
    min-height:100vh;padding:22px;
    background-image:radial-gradient(var(--dim) 1.5px,transparent 1.5px);background-size:22px 22px}
  .pix,.lbl,.brand b,.badge,.seg button,.opbtn,h2,.balbl,.state,.risk,.mark,.pill,.n,.status{font-family:var(--pix)}
  .shell{max-width:1280px;margin:0 auto;background:var(--card);border:var(--b);box-shadow:var(--sh)}
  /* Nav */
  nav{display:flex;align-items:center;justify-content:space-between;padding:14px 18px;
    border-bottom:var(--b);background:var(--yellow)}
  .brand{display:flex;align-items:center;gap:12px}
  .mark{width:36px;height:36px;background:var(--pink);border:var(--b);box-shadow:var(--sh-sm);
    display:flex;align-items:center;justify-content:center;color:#fff;font-size:14px}
  .brand b{font-size:14px;letter-spacing:1px}
  .tagline{font-size:16px;color:#4a4460;margin-top:5px}
  @media(max-width:640px){.tagline{display:none}}
  .brand .badge{font-size:8px;color:#fff;background:var(--purple);border:2px solid var(--ink);padding:3px 5px;margin-left:6px}
  .navlinks{display:flex;gap:18px;font-size:19px}
  .navlinks a{color:#4a4460;text-decoration:none;cursor:pointer;padding:2px 4px}
  .navlinks a:hover,.navlinks a.act{background:var(--ink);color:var(--yellow)}
  .navright{display:flex;align-items:center;gap:12px}
  .chip{display:flex;align-items:center;gap:8px;font-size:16px;color:var(--ink);background:var(--card);
    border:var(--b);box-shadow:var(--sh-sm);padding:5px 10px}
  .d{width:11px;height:11px;background:var(--dim);border:2px solid var(--ink)}
  .d.on{background:var(--green)} .d.off{background:var(--red)}
  .ghost{font-size:18px;color:var(--ink);cursor:pointer;background:var(--card);border:var(--b);box-shadow:var(--sh-sm);padding:5px 12px}
  @media(max-width:900px){.navlinks{display:none}}
  /* Toolbar */
  .toolbar{display:flex;align-items:center;justify-content:space-between;gap:14px;padding:16px 18px 2px}
  .toolbar h2{margin:0;font-size:16px}
  .toolbar .sub{color:var(--muted);font-size:18px;margin-top:9px}
  /* Toggle */
  .seg{display:flex;border:var(--b);box-shadow:var(--sh);background:var(--card)}
  .seg button{border:0;border-right:var(--b);background:transparent;color:var(--muted);padding:13px 16px;cursor:pointer;font-size:10px}
  .seg button:last-child{border-right:0}
  .seg button.a-off{color:#fff;background:var(--red)}
  .seg button.a-on{color:var(--ink);background:var(--lime)}
  /* Grid */
  main{display:grid;grid-template-columns:300px 1fr 330px;gap:18px;padding:18px;align-items:start}
  @media(max-width:1080px){main{grid-template-columns:1fr}}
  /* Left column scrolls on its own; center + right stay static */
  main>.card:nth-child(1){max-height:calc(100vh - 210px);overflow-y:auto}
  @media(max-width:1080px){main>.card:nth-child(1){max-height:none;overflow:visible}}
  .card{background:var(--card2);border:var(--b);box-shadow:var(--sh);padding:15px}
  .lbl{font-size:9px;letter-spacing:1px;text-transform:uppercase;color:var(--ink);margin:0 0 12px;line-height:1.7}
  /* Attack list */
  .atk{width:100%;text-align:left;background:var(--card);border:var(--b);box-shadow:var(--sh-sm);
    padding:11px 12px;margin-bottom:13px;color:var(--ink);cursor:pointer;display:flex;gap:11px;align-items:flex-start}
  .atk:hover{transform:translate(-2px,-2px);box-shadow:6px 6px 0 var(--ink)}
  .atk .ic{width:34px;height:34px;border:var(--b);display:flex;align-items:center;justify-content:center;font-size:16px;flex:none}
  .atk .t{font-size:18px}
  .atk .v{color:var(--muted);font-size:15px;margin-top:3px;line-height:1.25}
  .atk.base .ic{background:var(--lime)} .atk.threat .ic{background:var(--pink)}
  .steps{font-size:17px;color:var(--muted);line-height:1.5}
  .steps b{color:var(--ink)}
  .steps .n{display:inline-flex;width:22px;height:22px;background:var(--sky);border:2px solid var(--ink);
    align-items:center;justify-content:center;font-size:8px;margin-right:7px;color:var(--ink)}
  /* Signage device (dark screen in a bright room) */
  .device{border:var(--b);box-shadow:var(--sh);padding:9px;background:var(--ink)}
  .screen{min-height:236px;padding:24px;display:flex;flex-direction:column;align-items:center;justify-content:center;
    text-align:center;background:#14121f;position:relative;overflow:hidden;border:2px solid #000}
  .screen .tag{position:absolute;top:10px;left:11px;font-size:14px;color:#9a92ab}
  .screen .state{font-size:11px;line-height:1.5;text-transform:uppercase;margin-bottom:15px}
  .screen .content{font-size:30px;line-height:1.25;white-space:pre-line;color:#f2f7ff}
  .screen .note{margin-top:15px;font-size:16px;color:#9a92ab;max-width:460px;line-height:1.3}
  .screen.ok{box-shadow:inset 0 0 0 3px var(--green)} .screen.ok .state{color:var(--green)}
  .screen.attack{box-shadow:inset 0 0 0 3px var(--red);animation:blink .8s steps(2) infinite}
  .screen.attack .state{color:var(--red)} .screen.attack .content{color:#ff9db0}
  .screen.block{box-shadow:inset 0 0 0 3px var(--yellow)} .screen.block .state{color:var(--yellow)}
  @keyframes blink{50%{box-shadow:inset 0 0 0 3px rgba(255,68,94,.15)}}
  .rej{margin-top:14px;font-size:16px;color:#ff9db0;border:2px dashed var(--red);padding:8px 11px;white-space:pre-line;background:rgba(255,68,94,.12)}
  .rej .x{color:#fff;background:var(--red);font-size:12px;padding:2px 6px;margin-left:8px}
  /* Timeline */
  .tl{list-style:none;margin:6px 0 0;padding:0;font-size:16px}
  .tl li{padding:5px 0 5px 20px;position:relative;color:var(--muted);border-left:3px solid var(--dim);margin-left:6px}
  .tl li:before{content:"";position:absolute;left:-7px;top:9px;width:10px;height:10px;background:var(--dim);border:2px solid var(--ink)}
  .tl li.bad:before{background:var(--red)} .tl li.warn:before{background:var(--yellow)} .tl li.good:before{background:var(--green)}
  .tl li b{color:var(--ink)}
  /* Incident */
  .kv{display:flex;justify-content:space-between;align-items:center;padding:9px 0;border-bottom:2px dashed #d8cdb0;font-size:18px}
  .kv:last-child{border-bottom:0}.kv .k{color:var(--muted)}
  .pill{font-size:9px;padding:5px 8px;border:2px solid var(--ink)}
  .pill.red{color:#fff;background:var(--red)} .pill.green{color:var(--ink);background:var(--green)}
  .pill.amber{color:var(--ink);background:var(--yellow)} .pill.dim{color:var(--muted);background:var(--card)}
  .riskrow{display:flex;align-items:baseline;gap:8px;margin-top:6px}
  .risk{font-size:26px;line-height:1}
  .gauge{height:16px;background:var(--card);border:var(--b);overflow:hidden;margin:12px 0}
  .gauge>i{display:block;height:100%;width:0;transition:.4s steps(10)}
  .g-low{background:var(--green)}.g-medium{background:var(--yellow)}.g-high{background:var(--orange)}.g-critical{background:var(--red)}
  .bar{margin:11px 0}
  .bar .bl{display:flex;justify-content:space-between;font-size:16px;margin-bottom:5px}
  .bar .bl b{color:var(--ink)} .bar .bl span{color:var(--muted)}
  .bar .bt{height:13px;background:var(--card);border:2px solid var(--ink);overflow:hidden}
  .bar .bt>i{display:block;height:100%;background:var(--orange)}
  .xf{font-size:16px;color:var(--muted);margin:6px 0;display:flex;justify-content:space-between}
  .xf b{color:var(--ink)}.xf .pos{color:var(--red)}.xf .neg{color:var(--green)}
  .empty{color:var(--dim);font-size:16px}
  /* Inputs + buttons */
  .op input,.op textarea,#atkContent,#beforeInput{width:100%;background:var(--card);border:var(--b);
    padding:9px 10px;color:var(--ink);font-family:var(--term);font-size:18px;margin-bottom:9px;line-height:1.2}
  .op textarea,#atkContent,#beforeInput{resize:vertical}
  .op input:focus,.op textarea:focus,#atkContent:focus,#beforeInput:focus{outline:0;box-shadow:var(--sh-sm)}
  .opbtn{width:100%;border:var(--b);box-shadow:var(--sh-sm);background:var(--sky);color:var(--ink);
    padding:12px;font-size:9px;cursor:pointer;margin-bottom:10px}
  .opbtn:hover{transform:translate(-2px,-2px);box-shadow:5px 5px 0 var(--ink)}
  .opbtn.pub{background:var(--pink);color:#fff}
  .opstatus{font-size:16px;color:var(--muted);margin:2px 0 10px;line-height:1.25}
  .opstatus.good{color:var(--green)} .opstatus.warn{color:#b58900} .opstatus.bad{color:var(--red)}
  .ophint{font-size:14px;color:var(--dim);line-height:1.3;margin-top:2px}
  /* Before/after */
  .ba{display:grid;grid-template-columns:1fr 1fr;gap:12px}
  @media(max-width:560px){.ba{grid-template-columns:1fr}}
  .balbl{font-size:9px;text-transform:uppercase;color:var(--muted);margin-bottom:8px}
  .balbl .up{color:var(--green)} .balbl .down{color:var(--red)}
  .screen.mini{min-height:280px;padding:22px}
  .screen.mini .content{font-size:28px}
  .screen.mini .state{font-size:9px;margin-bottom:14px}
  .screen.mini .note{font-size:15px;margin-top:12px}
  /* Let the center column fill its height (audit trail stretches) */
  main>.card:nth-child(2){display:flex;flex-direction:column}
  main>.card:nth-child(2) .tl{flex:1 1 auto;min-height:140px;
    border:2px dashed #163d2c;padding:12px;overflow:auto}
  /* ===== Cyberpunk SOC overrides (neon green / yellow / red) ===== */
  body{background:#04080a;
    background-image:linear-gradient(rgba(0,255,156,.05) 1px,transparent 1px),
      linear-gradient(90deg,rgba(0,255,156,.05) 1px,transparent 1px);background-size:26px 26px}
  body::before{content:"";position:fixed;inset:0;pointer-events:none;z-index:9999;
    background:repeating-linear-gradient(0deg,rgba(0,0,0,0) 0 2px,rgba(0,25,15,.35) 2px 3px)}
  .shell{background:#060c10}
  nav{background:#081014}
  .brand b{color:var(--green);text-shadow:0 0 8px rgba(0,255,156,.5)}
  .badge{background:var(--yellow);color:#141400;border-color:#12e39c}
  .mark{background:var(--green);color:#04140d;border-color:#0a5;box-shadow:0 0 10px rgba(0,255,156,.4)}
  .navlinks a:hover,.navlinks a.act{background:transparent;color:var(--green);text-shadow:0 0 8px rgba(0,255,156,.6)}
  .chip{background:#0a1218;color:var(--muted)}
  .ghost{background:#0a1218;color:var(--green)}
  .toolbar h2{color:var(--green);text-shadow:0 0 8px rgba(0,255,156,.4)}
  .lbl{color:var(--yellow)}
  .seg{background:#0a1218}
  .seg button.a-off{background:var(--red);color:#160000;text-shadow:none}
  .seg button.a-on{background:var(--green);color:#04140d}
  .atk{background:#0a141a}
  .atk .ic{background:#0b1a14}
  .atk.base .ic{background:#06231a;color:var(--green)} .atk.threat .ic{background:#2a0a12;color:var(--red)}
  .atk .t{color:var(--ink)}
  .steps .n{background:#0b1a14;color:var(--green)}
  .device{background:#02100a}
  .opbtn{background:#0b1a14;color:var(--green)} .opbtn.pub{background:var(--yellow);color:#141400}
  .op input,.op textarea,#atkContent,#beforeInput{background:#061014}
  .pill.green{background:var(--green);color:#04140d} .pill.amber{background:var(--yellow);color:#141400}
  .pill.red{background:var(--red);color:#fff} .pill.dim{background:#0b1218;color:var(--muted)}
  .risk{color:var(--yellow);text-shadow:0 0 8px rgba(255,230,0,.4)}
  .kv{border-bottom-color:#12281f}
  .gauge,.bar .bt{background:#061014}
  .bar .bt>i{background:var(--yellow)}
  .opstatus.warn{color:var(--yellow)}
  .atk:hover,.opbtn:hover{box-shadow:0 0 14px rgba(0,255,156,.4)}
</style>
</head>
<body>
<div class="shell">
  <nav>
    <div class="brand">
      <div class="mark">S</div>
      <div>
        <div style="display:flex;align-items:center;gap:6px"><b>SignGuard</b><span class="badge">AI</span></div>
        <div class="tagline">Blockchain-based content integrity system for public transport</div>
      </div>
    </div>
    <div class="navlinks">
      <a class="act">Console</a><a>Incidents</a><a>Devices</a><a>Audit</a><a>Docs</a>
    </div>
    <div class="navright">
      <div class="chip"><span id="chainDot" class="d"></span><span id="chainLbl">on-chain…</span></div>
      <div class="chip"><span id="ledBroker" class="d"></span><span id="brokerLbl">connecting…</span></div>
      <span class="ghost">Sign in</span>
    </div>
  </nav>

  <div class="toolbar">
    <div>
      <h2>Attack Console</h2>
      <div class="sub">Node <b style="color:var(--ink)">SG-RNP-001</b> · TNSTC Route 101 signage · content integrity + AI risk</div>
    </div>
    <div class="seg" id="seg">
      <button id="segOff" class="a-off" onclick="setProt(false)">SignGuard OFF</button>
      <button id="segOn" onclick="setProt(true)">SignGuard ON</button>
    </div>
  </div>

  <main>
    <!-- LEFT -->
    <section class="card">
      <div class="lbl">① Authorized content (before)</div>
      <textarea id="beforeInput" rows="2">TNSTC  •  Route 101
Ranipet → Vellore
Next Bus: 10:30 AM</textarea>
      <button class="opbtn" onclick="setAuthorized()">Set as authorized ✓</button>

      <div class="lbl" style="margin-top:14px">② Tampered content (after)</div>
      <textarea id="atkContent" rows="2" placeholder="What the tampered update shows">⚠ THIS DISPLAY HAS BEEN HACKED
DO NOT BOARD</textarea>

      <div class="lbl" style="margin-top:14px">③ Attack scenarios</div>
      <div id="buttons"></div>

      <div class="lbl" style="margin-top:16px">Manual credential attack</div>
      <div class="op">
        <input id="opUser" placeholder="username — try: admin" autocomplete="off"/>
        <input id="opPass" type="password" placeholder="password — try: admin"/>
        <button class="opbtn" onclick="login()">Log in to admin panel</button>
        <div id="opStatus" class="opstatus">Not logged in.</div>
        <textarea id="opContent" rows="3">Route 101
NEXT BUS CANCELLED</textarea>
        <button class="opbtn pub" onclick="publish()">Publish to signage →</button>
        <div class="ophint">Even a valid session can't push content whose hash isn't authorized. With SignGuard ON this upload is <b>blocked</b>; with it OFF it reaches the passengers.</div>
      </div>

      <div class="lbl" style="margin-top:16px">Demo script</div>
      <div class="steps">
        <div><span class="n">1</span><b>OFF</b> → run an attack → attacker wins.</div>
        <div style="margin-top:7px"><span class="n">2</span><b>ON</b> → run the <b>same</b> attack → blocked.</div>
        <div style="margin-top:7px"><span class="n">3</span>Read the incident &amp; audit on the right.</div>
      </div>
    </section>

    <!-- CENTER -->
    <section class="card">
      <div class="lbl">Passenger signage — <span class="balbl" style="display:inline"><span class="up">before</span> vs <span class="down">after</span></span></div>
      <div class="ba">
        <div>
          <div class="balbl"><span class="up">● BEFORE</span> · authorized</div>
          <div class="device">
            <div id="beforeScreen" class="screen ok mini">
              <div class="state">✓ Authorized</div>
              <div class="content" id="beforeContent">TNSTC  •  Route 101
Ranipet → Vellore
Next Bus: 10:30 AM</div>
            </div>
          </div>
        </div>
        <div>
          <div class="balbl"><span class="down">● AFTER</span> · result</div>
          <div class="device">
            <div id="screen" class="screen mini">
              <div class="tag" id="tag">SG-RNP-001</div>
              <div class="state" id="state">Standby</div>
              <div class="content" id="content">—</div>
              <div class="note" id="note">Pick a scenario to run the attack.</div>
            </div>
          </div>
        </div>
      </div>
      <div class="lbl" style="margin-top:16px">Audit trail</div>
      <ul class="tl" id="timeline"><li class="empty">No events yet.</li></ul>
    </section>

    <!-- RIGHT -->
    <section class="card">
      <div class="lbl">Decision</div>
      <div class="kv"><span class="k">Scenario</span><span id="mScenario">—</span></div>
      <div class="kv"><span class="k">Integrity</span><span id="mIntegrity" class="pill dim">—</span></div>
      <div class="kv"><span class="k">Authorization</span><span id="mAuth" class="pill dim">—</span></div>
      <div class="kv"><span class="k">Action</span><span id="mAction" class="pill dim">—</span></div>
      <div class="kv"><span class="k">Safe fallback</span><span id="mFallback" class="pill dim">—</span></div>

      <div class="lbl" style="margin-top:18px">Risk score</div>
      <div class="riskrow"><span class="risk" id="mRisk">0</span>
        <span style="color:var(--muted);font-size:16px">/ 100 · <span id="mLevel">low</span></span></div>
      <div class="gauge"><i id="gauge" class="g-low"></i></div>

      <div class="lbl" style="margin-top:16px">Why — risk contributions</div>
      <div id="breakdown"><div class="empty">—</div></div>

      <div class="lbl" style="margin-top:16px">AI anomaly evidence</div>
      <div id="xai"><div class="empty">—</div></div>
    </section>
  </main>
</div>

<script>
const $=id=>document.getElementById(id);
let PROT=false;
const FALLBACK="OFFICIAL SERVICE INFORMATION\nContent update unavailable.\nContact station staff.";

function setProt(on){
  PROT=on;
  $("segOff").className=on?"":"a-off";
  $("segOn").className=on?"a-on":"";
}

async function loadButtons(){
  const list=await (await fetch("/demo/scenarios")).json();
  const box=$("buttons");
  list.forEach(s=>{
    const b=document.createElement("button");
    b.className="atk "+(s.id==="baseline"?"base":"threat");
    b.innerHTML=`<span class="ic">${s.icon||"⚠"}</span><span><span class="t">${s.title}</span><span class="v">${s.vector}</span></span>`;
    b.onclick=()=>run(s);
    box.appendChild(b);
  });
}

async function setAuthorized(){
  const text=$("beforeInput").value||"";
  const r=await fetch("/demo/authorize-content",{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({content:text})});
  const d=await r.json();
  $("beforeContent").textContent=d.authentic_text;
}

async function run(s){
  try{
    const body=JSON.stringify({protected:PROT,content:$("atkContent").value||""});
    const r=await fetch(`/demo/attack/${s.id}`,{method:"POST",headers:{"content-type":"application/json"},body});
    if(!r.ok){ const e=await r.json(); $("note").textContent="Error: "+(e.detail||r.status); }
  }catch(err){ $("note").textContent="Error: "+err; }
}

let GRANTED=false;
async function login(){
  const body=JSON.stringify({user:$("opUser").value||"",password:$("opPass").value||""});
  const r=await fetch("/demo/login",{method:"POST",headers:{"content-type":"application/json"},body});
  const d=await r.json(); GRANTED=d.granted;
  const s=$("opStatus"); s.textContent=d.note;
  s.className="opstatus "+(d.flag==="valid"?"good":d.flag==="default"?"warn":"bad");
}
async function publish(){
  if(!GRANTED){ const s=$("opStatus"); s.textContent="Log in first (access not granted)."; s.className="opstatus bad"; return; }
  const body=JSON.stringify({content:$("opContent").value||"",protected:PROT});
  const r=await fetch("/demo/publish",{method:"POST",headers:{"content-type":"application/json"},body});
  if(!r.ok){ const e=await r.json(); const s=$("opStatus"); s.textContent="Error: "+(e.detail||r.status); s.className="opstatus bad"; }
}

function renderScreen(p){
  const scr=$("screen"); $("tag").textContent=p.device_id;
  if(p.mode==="unprotected"){
    scr.className="screen mini attack";
    $("state").textContent="⚠ Unverified — LIVE";
    $("content").textContent=p.attacker_text||"";
    $("note").textContent="SignGuard is OFF. No integrity check ran — every passenger sees the attacker's message.";
  }else if(p.mode==="render"){
    scr.className="screen mini ok";
    $("state").textContent="✓ Authorized";
    $("content").textContent=p.authentic_text;
    $("note").textContent="SHA-256 matched the authorized fingerprint. Genuine signage shown.";
  }else{
    scr.className="screen mini block";
    $("state").textContent="⛔ Tamper detected — reverted to verified content";
    $("content").textContent=p.authentic_text;
    let n="Tampered update <b>blocked</b>. The sign safely reverted to the last verified content.";
    if(p.attacker_text) n+=`<div class="rej">Rejected: ${p.attacker_text}<span class="x">BLOCKED</span></div>`;
    $("note").innerHTML=n;
  }
}

function setPill(el,txt,cls){ el.textContent=txt; el.className="pill "+cls; }

function renderIncident(p){
  const blocked=p.mode==="blocked", unprot=p.mode==="unprotected";
  $("mScenario").textContent=(p.icon?p.icon+" ":"")+p.title;
  if(unprot){
    setPill($("mIntegrity"),"NOT CHECKED","amber"); setPill($("mAuth"),"NOT CHECKED","amber");
    setPill($("mAction"),"DISPLAYED","red"); setPill($("mFallback"),"—","dim");
  }else if(blocked){
    setPill($("mIntegrity"),"FAILED","red"); setPill($("mAuth"),"FAILED","red");
    setPill($("mAction"),"BLOCKED","red"); setPill($("mFallback"),"ACTIVE","green");
  }else{
    setPill($("mIntegrity"),"PASS","green"); setPill($("mAuth"),"OK","green");
    setPill($("mAction"),"RENDERED","green"); setPill($("mFallback"),"—","dim");
  }
  $("mRisk").textContent=p.risk; $("mLevel").textContent=p.level;
  const g=$("gauge"); g.style.width=Math.min(p.risk,100)+"%"; g.className="g-"+p.level;

  const bd=$("breakdown");
  if(p.breakdown&&p.breakdown.length){
    bd.innerHTML="";
    p.breakdown.forEach(b=>{ const d=document.createElement("div"); d.className="bar";
      d.innerHTML=`<div class="bl"><b>${b.label}</b><span>+${b.points}</span></div>`+
        `<div class="bt"><i style="width:${Math.min(b.points*2.2,100)}%"></i></div>`; bd.appendChild(d); });
  }else bd.innerHTML="<div class='empty'>No risk contributions.</div>";

  const xf=$("xai");
  if(p.xai&&p.xai.length){
    xf.innerHTML="";
    p.xai.forEach(x=>{ const d=document.createElement("div"); d.className="xf";
      const cls=x.impact>=0?"pos":"neg", s=x.impact>=0?"+":"";
      d.innerHTML=`<b>${x.name}</b><span class="${cls}">${s}${x.impact}</span>`; xf.appendChild(d); });
  }else xf.innerHTML="<div class='empty'>Not computed for this scenario.</div>";
}

function renderTimeline(p){
  const tl=$("timeline"); tl.innerHTML="";
  (p.timeline||[]).forEach(step=>{ const li=document.createElement("li"); const s=step.toUpperCase();
    if(/BLOCK|FAIL|MISMATCH|UNVERIFIED/.test(s)) li.className="bad";
    else if(/FALLBACK|INCIDENT/.test(s)) li.className="warn";
    else if(/MATCH|RENDER|AUTHORIZED/.test(s)) li.className="good";
    li.innerHTML=`<b>${new Date().toLocaleTimeString()}</b>  ${step}`; tl.appendChild(li); });
}

function onDecision(p){ renderScreen(p); renderIncident(p); renderTimeline(p); }

function setBroker(on){
  $("ledBroker").className="d "+(on?"on":"off");
  $("brokerLbl").textContent=on?"broker live · ESP32 armed":"broker offline";
}

function connect(){
  const ws=new WebSocket((location.protocol==="https:"?"wss":"ws")+"://"+location.host+"/ws");
  ws.onmessage=e=>{ const p=JSON.parse(e.data);
    if(p.type==="status") setBroker(p.broker);
    else if(p.type==="authorized") $("beforeContent").textContent=p.authentic_text;
    else if(p.type==="decision") onDecision(p); };
  ws.onclose=()=>{ setBroker(false); setTimeout(connect,1500); };
}
async function chainStatus(){
  try{ const d=await (await fetch("/chain/verify")).json();
    document.getElementById("chainDot").className="d "+(d.valid?"on":"off");
    document.getElementById("chainLbl").textContent="⛓ "+d.blocks+" blocks "+(d.valid?"✓ signed":"✗ tampered");
  }catch(e){}
}
loadButtons(); connect(); chainStatus(); setInterval(chainStatus, 4000);
</script>
</body>
</html>"""


def render() -> str:
    return _HTML
