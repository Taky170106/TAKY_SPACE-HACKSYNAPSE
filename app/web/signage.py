"""Full-screen passenger signage — pixel-neobrutalism. Project on the big screen."""
from __future__ import annotations

_HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>SignGuard — Passenger Signage</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&family=VT323&display=swap" rel="stylesheet"/>
<style>
  :root{--pix:"Press Start 2P",monospace;--term:"VT323","Courier New",monospace;
    --bg:#04080a;--ink:#d6ffe9;--green:#00ff9c;--red:#ff3b3b;--yellow:#ffe600;--pink:#ff3b6b;--muted:#6f9d88}
  *{box-sizing:border-box;margin:0;image-rendering:pixelated}
  html,body{height:100%}
  body{background:var(--bg);color:var(--ink);font-family:var(--term);display:flex;flex-direction:column;overflow:hidden;padding:2vh 2vw;
    background-image:radial-gradient(#c9bd9c 1.5px,transparent 1.5px);background-size:26px 26px}
  .frame{flex:1;display:flex;flex-direction:column;border:5px solid var(--ink);box-shadow:9px 9px 0 var(--ink);background:#fffaf0;overflow:hidden}
  .bar{display:flex;align-items:center;justify-content:space-between;padding:2.4vh 3vw;border-bottom:5px solid var(--ink);background:var(--yellow)}
  .brand{display:flex;align-items:center;gap:1.6vw}
  .mark{width:5.4vh;height:5.4vh;background:var(--pink);border:3px solid var(--ink);box-shadow:4px 4px 0 var(--ink);
    display:flex;align-items:center;justify-content:center;color:#fff;font-family:var(--pix);font-size:2.2vh}
  .brand b{font-family:var(--pix);font-size:2.1vh}
  .brand span{font-size:2vh;color:#4a4460;display:block;margin-top:.9vh}
  .status{font-family:var(--pix);font-size:1.7vh;padding:1.4vh 2vw;border:3px solid var(--ink);box-shadow:5px 5px 0 var(--ink);text-transform:uppercase}
  .status.ok{background:var(--green)} .status.bad{background:var(--red);color:#fff} .status.warn{background:var(--yellow)}
  /* The actual passenger display: dark screen */
  .stage{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;
    padding:4vh 5vw;background:#14121f;color:#f2f7ff;position:relative;transition:.2s;margin:1.4vh;border:4px solid #000}
  .stage.ok{box-shadow:inset 0 0 0 4px var(--green)}
  .stage.attack{box-shadow:inset 0 0 0 4px var(--red);animation:blink .7s steps(2) infinite}
  .stage.block{box-shadow:inset 0 0 0 4px var(--yellow)}
  @keyframes blink{50%{box-shadow:inset 0 0 0 4px rgba(255,68,94,.15)}}
  .banner{font-family:var(--pix);font-size:2.6vh;line-height:1.5;margin-bottom:4vh;text-transform:uppercase}
  .stage.ok .banner{color:var(--green)} .stage.attack .banner{color:var(--red)} .stage.block .banner{color:var(--yellow)}
  .content{font-size:11vh;line-height:1.15;white-space:pre-line;max-width:92vw}
  .stage.attack .content{color:#ff9db0}
  .sub{margin-top:4vh;font-size:2.6vh;color:#9a92ab;max-width:74vw;line-height:1.3}
  .foot{padding:1.8vh 3vw;border-top:5px solid var(--ink);display:flex;justify-content:space-between;font-size:2vh;color:var(--muted);background:#fffaf0}
  .dot{display:inline-block;width:1.5vh;height:1.5vh;background:var(--red);border:2px solid #0a5;margin-right:.8vw}
  .dot.on{background:var(--green)}
  /* ===== Cyberpunk SOC overrides ===== */
  body{background:#04080a;
    background-image:linear-gradient(rgba(0,255,156,.05) 1px,transparent 1px),
      linear-gradient(90deg,rgba(0,255,156,.05) 1px,transparent 1px);background-size:30px 30px}
  .frame{background:#060c10;border-color:#12e39c;box-shadow:0 0 26px rgba(0,255,156,.25)}
  .bar{background:#081014;border-bottom:5px solid #12e39c}
  .brand b{color:var(--green);text-shadow:0 0 10px rgba(0,255,156,.6)}
  .mark{background:var(--green);color:#04140d;border-color:#0a5}
  .foot{background:#081014;border-top:5px solid #12e39c}
  .status{box-shadow:0 0 14px rgba(0,255,156,.25)}
  .status.ok{background:var(--green);color:#04140d} .status.warn{background:var(--yellow);color:#141400} .status.bad{background:var(--red);color:#fff}
  .stage{border-color:#0a5}
</style>
</head>
<body>
 <div class="frame">
  <div class="bar">
    <div class="brand"><div class="mark">S</div>
      <div><b>SignGuard AI</b><span>TNSTC · Public Transport Signage</span></div>
    </div>
    <div id="status" class="status ok">System Secure</div>
  </div>

  <div id="stage" class="stage ok">
    <div id="banner" class="banner">✓ Verified Content</div>
    <div id="content" class="content">TNSTC  •  Route 101
Ranipet → Vellore
Next Bus: 10:30 AM</div>
    <div id="sub" class="sub">Content authorized by the transport authority and verified by SHA-256.</div>
  </div>

  <div class="foot">
    <div>Node SG-RNP-001</div>
    <div><span id="ledB" class="dot"></span><span id="ledT">connecting…</span></div>
  </div>
 </div>

<script>
const $=id=>document.getElementById(id);
let AUTH="TNSTC  •  Route 101\nRanipet → Vellore\nNext Bus: 10:30 AM";

function show(p){
  const st=$("stage"), status=$("status");
  if(p.mode==="unprotected"){
    st.className="stage attack";
    status.className="status bad"; status.textContent="Unverified — No SignGuard";
    $("banner").textContent="⚠ Unverified Content";
    $("content").textContent=p.attacker_text||"";
    $("sub").textContent="SignGuard is OFF — no integrity check ran. Passengers see the attacker's message.";
  }else if(p.mode==="blocked"){
    st.className="stage block";
    status.className="status warn"; status.textContent="⛔ Tampering Blocked";
    $("banner").textContent="⛔ Tampering Detected — Reverted";
    $("content").textContent=p.authentic_text||AUTH;
    $("sub").textContent="Tampered update blocked by SHA-256. Reverted to the last verified content.";
  }else{
    AUTH=p.authentic_text||AUTH;
    st.className="stage ok";
    status.className="status ok"; status.textContent="System Secure";
    $("banner").textContent="✓ Verified Content";
    $("content").textContent=AUTH;
    $("sub").textContent="Content authorized by the transport authority and verified by SHA-256.";
  }
}

function setBroker(on){ $("ledB").className="dot "+(on?"on":""); $("ledT").textContent=on?"live":"offline"; }

function connect(){
  const ws=new WebSocket((location.protocol==="https:"?"wss":"ws")+"://"+location.host+"/ws");
  ws.onmessage=e=>{ const p=JSON.parse(e.data);
    if(p.type==="status") setBroker(p.broker);
    else if(p.type==="authorized"){ AUTH=p.authentic_text; show({mode:"render",authentic_text:AUTH}); }
    else if(p.type==="decision") show(p); };
  ws.onclose=()=>{ setBroker(false); setTimeout(connect,1500); };
}
connect();
</script>
</body>
</html>"""


def render() -> str:
    return _HTML
