"""SignGuard — realistic web hardware lab: Raspberry Pi + USB stick + ESP-12E LCD."""
from __future__ import annotations

_HTML = r"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>SignGuard — Hardware Lab</title>
<link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&family=VT323&display=swap" rel="stylesheet"/>
<style>
  :root{--pix:"Press Start 2P",monospace;--term:"VT323",monospace;
    --green:#00ff9c;--red:#ff3b3b;--yellow:#ffe600;--cyan:#39e0ff;--muted:#8fb7a8;}
  *{box-sizing:border-box;margin:0}
  body{background:#070b10;color:#dfeee7;font-family:var(--term);font-size:18px;min-height:100vh;
    background:radial-gradient(1200px 600px at 50% -10%,#0e1a16,#070b10 70%)}
  .bar{display:flex;align-items:center;justify-content:space-between;border-bottom:2px solid #123;padding:10px 18px}
  .brand{font-family:var(--pix);font-size:15px;color:var(--green);text-shadow:0 0 10px rgba(0,255,156,.5)}
  .right{display:flex;gap:12px;align-items:center}
  a.dash{color:var(--cyan);font-family:var(--pix);font-size:9px;text-decoration:none;border:2px solid #245;padding:8px 11px}
  .seg{display:flex;border:2px solid #000;box-shadow:0 0 12px rgba(0,255,156,.15)}
  .seg button{font-family:var(--pix);font-size:9px;border:0;padding:11px 14px;cursor:pointer;background:#0a1218;color:var(--muted)}
  .seg button.aoff{background:var(--red);color:#160000}.seg button.aon{background:var(--green);color:#04140d}
  /* workbench */
  .bench{position:relative;height:640px;background:
     repeating-linear-gradient(90deg,#0b120f 0 38px,#0d1512 38px 40px),
     repeating-linear-gradient(0deg,#0b120f 0 38px,#0d1512 38px 40px);
     background-color:#0a100d;border-bottom:2px solid #123;overflow:hidden}
  .label{position:absolute;font-family:var(--pix);font-size:10px;color:var(--cyan)}
  /* ---- Raspberry Pi board ---- */
  .pi{position:absolute;left:60px;top:150px;width:360px;height:240px;border-radius:12px;
     background:linear-gradient(160deg,#0a7d3f,#0b5f31);box-shadow:0 12px 30px rgba(0,0,0,.6),inset 0 0 0 2px #063d20;}
  .pi .silk{position:absolute;color:#bfe;opacity:.5;font-family:var(--term);font-size:14px}
  .pi .gpio{position:absolute;top:12px;left:20px;width:320px;height:22px;border-radius:3px;background:#1a1a1a;
     display:flex;gap:3px;padding:3px 4px}
  .pi .gpio i{flex:1;background:linear-gradient(#ffd76a,#caa03a);border-radius:1px}
  .pi .soc{position:absolute;left:130px;top:96px;width:96px;height:96px;background:#111;border:2px solid #333;border-radius:6px;
     display:flex;align-items:center;justify-content:center;font-family:var(--pix);font-size:10px;color:#8fd;box-shadow:0 0 0 6px #0b5f31}
  .pi .usb{position:absolute;background:#c9cfd6;border:2px solid #8a929b;border-radius:2px;width:52px;height:34px}
  .pi .usb.u1{right:-14px;top:56px}.pi .usb.u2{right:-14px;top:150px}
  .pi .eth{position:absolute;right:-14px;top:100px;width:52px;height:40px;background:#5a6b7a;border-radius:2px}
  .pi .act{position:absolute;left:26px;top:210px;width:12px;height:12px;border-radius:50%;background:#3a0f12;box-shadow:0 0 0 2px #063d20}
  .pi.reading .act{background:var(--red);box-shadow:0 0 12px var(--red),0 0 0 2px #063d20;animation:actblink .18s steps(2) infinite}
  @keyframes actblink{50%{opacity:.25}}
  /* USB flash drive that plugs in */
  .stick{position:absolute;left:-150px;top:56px;width:120px;height:34px;transition:left .7s cubic-bezier(.5,0,.3,1);z-index:5}
  .stick .body{position:absolute;left:24px;top:0;width:96px;height:34px;border-radius:4px;background:linear-gradient(#2b3550,#1a2138);border:1px solid #445;
     color:#9fb;font-family:var(--pix);font-size:7px;display:flex;align-items:center;justify-content:center;text-align:center}
  .stick .plug{position:absolute;left:0;top:8px;width:26px;height:18px;background:#c9cfd6;border:1px solid #8a929b;border-radius:2px}
  .stick.in{left:36px}
  /* data wire Pi -> ESP */
  .wire{position:absolute;left:420px;top:206px;width:210px;height:6px;background:#123;border-radius:3px;z-index:1}
  .wire .pulse{position:absolute;top:-3px;left:0;width:14px;height:12px;border-radius:50%;background:var(--green);box-shadow:0 0 12px var(--green);opacity:0}
  .wire.flow .pulse{animation:flow 1s linear}
  @keyframes flow{0%{left:0;opacity:1}100%{left:196px;opacity:1}}
  /* ---- Breadboard + ESP-12E + LCD ---- */
  .board{position:absolute;left:640px;top:120px;width:430px;height:300px;border-radius:10px;
     background:repeating-linear-gradient(0deg,#e9e6d8 0 14px,#e2dfd0 14px 16px);box-shadow:0 12px 30px rgba(0,0,0,.6);}
  .esp{position:absolute;left:20px;top:150px;width:120px;height:120px;background:#0b3c22;border:2px solid #052;border-radius:4px;
     color:#7fd;font-family:var(--pix);font-size:9px;display:flex;align-items:center;justify-content:center;text-align:center;box-shadow:0 0 0 3px #cfc8b0}
  .esp .ant{position:absolute;left:-2px;top:-14px;width:118px;height:12px;border:2px solid #052;border-bottom:0;border-radius:6px 6px 0 0}
  /* LCD module */
  .lcdmod{position:absolute;left:150px;top:26px;width:260px;height:120px;background:#0a2f6b;border:6px solid #0a1a3a;border-radius:6px;padding:8px;box-shadow:0 0 0 3px #cfc8b0}
  .lcd{height:100%;background:#12d17a;color:#03210f;font-family:var(--term);font-size:30px;line-height:1.1;letter-spacing:2px;
     padding:10px 12px;white-space:pre-line;border:2px solid #0a5;box-shadow:inset 0 0 14px rgba(0,0,0,.35)}
  .lcd.tamper{background:#ffd23f;color:#3a1400}.lcd.off{background:#2a2a2a;color:#39ff6a}
  /* LEDs + buzzer on board */
  .parts{position:absolute;left:150px;top:158px;display:flex;gap:26px;align-items:center;font-family:var(--pix);font-size:8px;color:#333}
  .led{width:18px;height:18px;border-radius:50%;border:2px solid #222;display:inline-block;margin-right:6px;vertical-align:middle;background:#1a2a1a}
  .led.g.on{background:var(--green);box-shadow:0 0 12px var(--green)}
  .led.r.on{background:var(--red);box-shadow:0 0 14px var(--red)}
  .buzz{width:26px;height:26px;border-radius:50%;background:#111;border:2px solid #000;display:inline-block;vertical-align:middle;margin-right:6px;position:relative}
  .buzz:after{content:"";position:absolute;left:9px;top:9px;width:6px;height:6px;border-radius:50%;background:#333}
  .buzz.on{box-shadow:0 0 16px var(--red);animation:bz .25s steps(2) infinite}
  @keyframes bz{50%{box-shadow:0 0 4px var(--red)}}
  /* controls */
  .ctrl{display:flex;gap:16px;padding:14px 18px;flex-wrap:wrap;align-items:flex-start;border-bottom:2px solid #123;background:#0a120e}
  .ctrl .col{display:flex;flex-direction:column;gap:6px}
  .ctrl textarea{width:340px;height:56px;background:#061014;border:2px solid #245;color:#dfeee7;font-family:var(--term);font-size:17px;padding:7px;resize:none}
  .ctrl input[type=file]{font-size:13px;color:var(--muted);width:340px}
  .btn{font-family:var(--pix);font-size:9px;border:2px solid #000;padding:11px;cursor:pointer}
  .btn.ins{background:var(--red);color:#160000}.btn.auth{background:var(--cyan);color:#03222b}
  .strip{display:flex;gap:12px;justify-content:center;flex-wrap:wrap;font-family:var(--pix);font-size:10px;padding:12px}
  .pill{border:2px solid #234;padding:8px 12px;color:var(--muted)}
  .pill.red{color:#160000;background:var(--red)}.pill.green{color:#04140d;background:var(--green)}.pill.amber{color:#141400;background:var(--yellow)}
  .hint{color:var(--muted);font-size:15px;text-align:center;padding:0 12px 14px}
  .authb{color:#dfeee7}
</style></head>
<body>
  <div class="bar">
    <div class="brand">🛡 SignGuard — HARDWARE LAB</div>
    <div class="right">
      <a class="dash" href="/" target="_blank">dashboard ↗</a>
      <div class="seg"><button id="off" class="aoff" onclick="setProt(false)">SignGuard OFF</button><button id="on" onclick="setProt(true)">SignGuard ON</button></div>
    </div>
  </div>

  <div class="ctrl">
    <div class="col">
      <input type="file" id="file" accept=".txt"/>
      <textarea id="content">ALL SERVICES CANCELLED|LEAVE THE AREA</textarea>
    </div>
    <div class="col">
      <button class="btn ins" onclick="insertUsb()">⬇ INSERT USB INTO PI</button>
      <button class="btn auth" onclick="authorize()">✓ SET AS AUTHORIZED</button>
    </div>
    <div class="col">
      <div class="hint" style="text-align:left;max-width:260px">Original authorized:<br/><b class="authb" id="authTxt">TNSTC Route 101 | Next 10:30</b></div>
    </div>
  </div>

  <div class="bench">
    <div class="label" style="left:60px;top:118px">RASPBERRY&nbsp;PI · USB DETECTOR</div>
    <div class="label" style="left:640px;top:92px">BREADBOARD · ESP-12E + 16×2 LCD</div>

    <!-- USB stick -->
    <div class="stick" id="stick"><div class="plug"></div><div class="body" id="stickTxt">USB</div></div>
    <!-- Raspberry Pi -->
    <div class="pi" id="pi">
      <div class="gpio">""" + "".join("<i></i>" for _ in range(20)) + r"""</div>
      <div class="soc">Pi</div>
      <div class="usb u1"></div><div class="usb u2"></div><div class="eth"></div>
      <div class="silk" style="left:16px;top:44px">GPIO</div>
      <div class="act" id="act"></div>
      <div class="silk" style="left:44px;top:206px">ACT</div>
    </div>
    <!-- wire: Pi -> MQTT -> physical ESP -->
    <div class="wire" id="wire"><div class="pulse"></div></div>
    <!-- MQTT + physical ESP-12E output -->
    <div class="board" style="background:#0a141a;border:2px solid #245;border-radius:10px;box-shadow:0 0 22px rgba(57,224,255,.12)">
      <div class="label" style="left:16px;top:10px;position:absolute;color:#ffb347">ESP-12E · REAL HARDWARE (LCD + BUZZER) · via MQTT signguard/commands</div>
      <div class="esp" style="left:20px;top:120px;background:#07131a;border:2px solid #245;color:#7df;box-shadow:0 0 0 3px #0a141a">
        <div class="ant" style="border-color:#245"></div>ESP-12E<br/>(hardware)</div>
      <!-- command sent to the real device -->
      <div style="position:absolute;left:150px;top:36px;width:260px">
        <div style="font-family:var(--pix);font-size:9px;color:var(--muted)">COMMAND SENT TO DEVICE</div>
        <div id="cmd" style="font-family:var(--pix);font-size:15px;color:var(--green);margin-top:10px">render</div>
        <div style="font-family:var(--pix);font-size:8px;color:var(--muted);margin-top:14px">REAL LCD WILL SHOW</div>
        <div class="lcd" id="lcd" style="margin-top:6px;height:70px;font-size:22px;border:2px solid #0a5">SYSTEM SECURE
Route 101 OK</div>
        <div style="margin-top:10px;font-family:var(--pix);font-size:8px;color:var(--muted)">
          <span id="hw" style="color:#a95">● hardware: waiting</span> &nbsp; buzzer: <span id="buzTxt">off</span></div>
      </div>
    </div>
  </div>

  <div class="strip">
    <span class="pill" id="pIntegrity">INTEGRITY —</span>
    <span class="pill" id="pAction">ACTION —</span>
    <span class="pill" id="pRisk">RISK 0</span>
    <span class="pill" id="pFb">FALLBACK —</span>
  </div>

<script>
const $=id=>document.getElementById(id);
let PROT=true, AUTH="TNSTC Route 101|Next 10:30";
setProt(true);
function setProt(on){PROT=on; $("off").className=on?"":"aoff"; $("on").className=on?"aon":"";}

$("file").addEventListener("change",e=>{const f=e.target.files[0]; if(!f)return;
  const r=new FileReader(); r.onload=()=>{$("content").value=r.result.trim();}; r.readAsText(f);});

async function authorize(){
  const t=$("content").value||""; AUTH=t;
  await fetch("/demo/authorize-content",{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({content:t})});
  $("authTxt").textContent=t.replace(/\|/g," | ");
}

function plugAnimation(){
  const st=$("stick"); $("stickTxt").textContent=PROT?"USB":"USB";
  st.classList.remove("in"); void st.offsetWidth; st.classList.add("in");   // slide into port
  setTimeout(()=>{ $("pi").classList.add("reading"); },650);
  setTimeout(()=>{ $("wire").classList.add("flow"); },1100);
  setTimeout(()=>{ $("pi").classList.remove("reading"); $("wire").classList.remove("flow"); st.classList.remove("in"); },2000);
}

async function insertUsb(){
  const content=$("content").value||"";
  plugAnimation();
  setTimeout(async()=>{
    await fetch("/ingest/usb",{method:"POST",headers:{"content-type":"application/json"},
      body:JSON.stringify({content:content, protected:PROT, serial:"SIM-USB-"+(PROT?"001":"666")})});
  },1200);
}

function lcdShow(t,cls){ $("lcd").className="lcd"+(cls?" "+cls:""); $("lcd").textContent=t.replace(/\|/g,"\n"); }
function pill(el,txt,cls){ el.textContent=txt; el.className="pill"+(cls?" "+cls:""); }
function firstLine(t){return (t||"").split("|")[0];}
function setCmd(c,color){ $("cmd").textContent=c; $("cmd").style.color=color; }
function setHw(p){ const on=p.hardware_notified;
  $("hw").textContent="● hardware: "+(on?"command delivered":"broker/ESP not connected");
  $("hw").style.color=on?"#00ff9c":"#a95"; }

function onDecision(p){
  const auth=p.authentic_text||AUTH;
  setHw(p);
  if(p.mode==="unprotected"){
    setCmd("(none — SignGuard OFF)","#ff3b3b");
    lcdShow(p.attacker_text||"","off"); $("buzTxt").textContent="off";
    pill($("pIntegrity"),"NOT CHECKED","amber"); pill($("pAction"),"DISPLAYED","red");
    pill($("pFb"),"FALLBACK —"); pill($("pRisk"),"RISK "+(p.risk||0));
  } else if(p.mode==="blocked"){
    setCmd("safe_fallback","#ffe600");
    lcdShow("TAMPER DETECTED\n"+firstLine(auth),"tamper"); $("buzTxt").textContent="BEEP BEEP";
    setTimeout(()=>{ lcdShow(auth); $("buzTxt").textContent="off"; },2800); // revert to original
    pill($("pIntegrity"),"FAILED","red"); pill($("pAction"),"BLOCKED","red");
    pill($("pFb"),"FALLBACK ACTIVE","green"); pill($("pRisk"),"RISK "+(p.risk||0),"amber");
  } else {
    setCmd("render","#00ff9c");
    lcdShow(auth); $("buzTxt").textContent="off";
    pill($("pIntegrity"),"PASS","green"); pill($("pAction"),"RENDER","green");
    pill($("pFb"),"FALLBACK —"); pill($("pRisk"),"RISK "+(p.risk||0));
  }
}

function connect(){
  const ws=new WebSocket((location.protocol==="https:"?"wss":"ws")+"://"+location.host+"/ws");
  ws.onmessage=e=>{const p=JSON.parse(e.data);
    if(p.type==="authorized"){AUTH=p.authentic_text; $("authTxt").textContent=(p.authentic_text||"").replace(/\|/g," | ");}
    else if(p.type==="decision") onDecision(p);};
  ws.onclose=()=>setTimeout(connect,1500);
}
connect();
</script>
</body></html>"""


def render() -> str:
    return _HTML
