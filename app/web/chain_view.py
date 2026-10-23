"""Visual on-chain ledger explorer (/chain/view).

Fetches /chain and /chain/verify and renders the signed, hash-linked blocks as
a chain of cards — so the "blockchain" claim is visually verifiable during the
demo. Matches the cyberpunk-SOC theme of the dashboard.
"""

_HTML = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>SignGuard — On-Chain Ledger</title>
<style>
  :root{--bg:#07140e;--panel:#0f2a1f;--panel2:#123529;--green:#1ee69c;--yel:#ffe03f;
        --red:#ff5a5a;--txt:#eafbf3;--mute:#8fb7a6;--line:#1e5c43;}
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--txt);
       font-family:"Segoe UI",Consolas,monospace;padding:22px}
  h1{margin:0 0 2px;font-size:22px;color:var(--green);letter-spacing:.5px}
  .sub{color:var(--mute);font-size:13px;margin-bottom:16px}
  .bar{display:flex;gap:14px;align-items:center;flex-wrap:wrap;margin-bottom:18px}
  .badge{padding:8px 16px;border-radius:8px;font-weight:700;font-size:15px;
         border:2px solid var(--green);color:var(--green);background:#0b2018}
  .badge.bad{border-color:var(--red);color:var(--red)}
  .pill{padding:6px 12px;border-radius:20px;background:var(--panel);color:var(--mute);
        font-size:12px;border:1px solid var(--line)}
  .chain{display:flex;flex-direction:column;gap:0}
  .block{background:var(--panel);border:1.5px solid var(--line);border-radius:12px;
         padding:14px 18px;position:relative}
  .block:hover{border-color:var(--green)}
  .idx{font-size:15px;font-weight:700;color:var(--yel)}
  .ts{float:right;color:var(--mute);font-size:12px}
  .row{display:flex;gap:8px;margin-top:6px;font-size:12.5px;flex-wrap:wrap}
  .k{color:var(--green);min-width:96px;font-weight:600}
  .v{color:var(--txt);word-break:break-all;font-family:Consolas,monospace}
  .v.hash{color:#9fe7c8}
  .genesis{color:var(--mute)}
  .link{height:26px;width:2px;background:var(--green);margin:0 auto;opacity:.7}
  .link::after{content:"prev_hash \\2193";position:relative;left:12px;top:2px;
        color:var(--mute);font-size:10px;white-space:nowrap}
  .empty{color:var(--mute);padding:30px;text-align:center}
</style></head>
<body>
  <h1>SignGuard — On-Chain Authorization Ledger</h1>
  <div class="sub">Signed (Ed25519), hash-linked, tamper-evident. Each block chains to the previous via prev_hash.</div>
  <div class="bar">
    <span id="verdict" class="badge">checking…</span>
    <span class="pill" id="count">— blocks</span>
    <span class="pill">SHA-256 · Ed25519 · prev_hash link</span>
    <span class="pill">auto-refresh 5s</span>
  </div>
  <div id="chain" class="chain"><div class="empty">Loading…</div></div>

<script>
const short = (h,n=20)=> h ? (h.length>n? h.slice(0,n)+"…"+h.slice(-6) : h) : "";
async function load(){
  try{
    const [blocks, ver] = await Promise.all([
      fetch("/chain").then(r=>r.json()),
      fetch("/chain/verify").then(r=>r.json())
    ]);
    const vd = document.getElementById("verdict");
    if(ver.valid){ vd.textContent = "✔ CHAIN VALID"; vd.className="badge"; }
    else { vd.textContent = "✘ TAMPERED: "+ver.message; vd.className="badge bad"; }
    document.getElementById("count").textContent = blocks.length + " block(s)";
    const c = document.getElementById("chain");
    if(!blocks.length){ c.innerHTML='<div class="empty">No authorizations yet. Authorize content to mint the first block.</div>'; return; }
    c.innerHTML = "";
    blocks.slice().reverse().forEach((b,i)=>{
      const el = document.createElement("div");
      el.className="block";
      el.innerHTML =
        '<span class="idx">Block #'+b.index+'</span>'+
        '<span class="ts">'+ (b.timestamp||"") +'</span>'+
        '<div class="row"><span class="k">content_id</span><span class="v">'+ (b.content_id||"") +'</span></div>'+
        '<div class="row"><span class="k">content_hash</span><span class="v hash">'+ short(b.content_hash,40) +'</span></div>'+
        '<div class="row"><span class="k">signature</span><span class="v hash">'+ short(b.signature,40) +'</span></div>'+
        '<div class="row"><span class="k">authorized_by</span><span class="v">'+ (b.authorized_by||"") +'</span></div>'+
        '<div class="row"><span class="k">prev_hash</span><span class="v hash '+(b.prev_hash&&b.prev_hash.replace(/0/g,"")===""?"genesis":"")+'">'+ short(b.prev_hash,40) +'</span></div>'+
        '<div class="row"><span class="k">block_hash</span><span class="v hash">'+ short(b.block_hash,40) +'</span></div>';
      c.appendChild(el);
      if(i < blocks.length-1){ const l=document.createElement("div"); l.className="link"; c.appendChild(l); }
    });
  }catch(e){
    document.getElementById("chain").innerHTML='<div class="empty">Backend not reachable.</div>';
  }
}
load(); setInterval(load, 5000);
</script>
</body></html>"""


def render() -> str:
    return _HTML
