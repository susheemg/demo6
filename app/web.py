"""
The BRO Risk Oracle web UI.

Server-rendered, single-file styled interface over the existing API. Carries the
established BRO brand (forest green / navy / gold). It calls the same JSON API
the rest of the app exposes, via fetch, holding the JWT in memory (sessionStorage)
so the security model is identical to API clients — no separate auth path.

Mounted onto the FastAPI app at "/". The SPA-style shell talks to /api/v1/*.
"""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

ui = APIRouter()

_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>BRO · Risk Oracle</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Inter:wght@400;450;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
  :root{
    --paper:#FFFFFF; --soft:#FAFAF8; --softer:#F2F3EE; --ink:#0F1419; --ink-2:#363B44;
    --mute:#727A84; --line:#E7E8E2; --line-2:#F1F2ED;
    --accent:#1A4D3C; --accent-2:#C99B5F; --crit:#B23A2F; --warn:#C97A1A; --ok:#2E7D4F; --info:#335577;
    --r-xs:7px; --r-sm:10px; --r-md:13px; --r-lg:16px; --r-xl:22px;
    --ease:cubic-bezier(.22,.61,.36,1); --ease-spring:cubic-bezier(.34,1.4,.5,1); --dur:.2s; --dur-lg:.42s;
    --sh-1:0 1px 2px rgba(15,20,25,.04),0 1px 3px rgba(15,20,25,.05);
    --sh-2:0 2px 6px rgba(15,20,25,.05),0 6px 16px rgba(15,20,25,.06);
    --sh-3:0 12px 32px rgba(15,20,25,.12),0 4px 10px rgba(15,20,25,.06);
    --ring:0 0 0 3px rgba(26,77,60,.18);
    /* legacy aliases kept so existing view markup keeps resolving */
    --green:#1A4D3C; --green-d:#196046; --navy:#1F3A52; --gold:#C99B5F; --card:#FFFFFF;
    --mut:#727A84; --moss:#2E7D4F; --amber:#C97A1A; --rust:#B23A2F;
    --high:#B23A2F; --elev:#C97A1A; --mod:#C9A227; --low:#2E7D4F;
  }
  *{box-sizing:border-box;margin:0;padding:0}
  ::selection{background:rgba(201,155,95,.28)}
  body{font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--soft);
       color:var(--ink);font-size:14px;line-height:1.55;letter-spacing:-.006em;-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
  h1,h2,h3{font-family:'Fraunces','Georgia',serif;letter-spacing:-.012em;font-optical-sizing:auto}
  .mono,.card-label,.nav-group-label,.brand-sub{font-family:'JetBrains Mono',monospace;letter-spacing:.03em}
  a{color:var(--accent);text-decoration:none}
  .hidden{display:none!important}
  @keyframes fadeUp{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
  @keyframes growW{from{transform:scaleX(0)}to{transform:scaleX(1)}}
  /* ---- simple animations (engaging, not distracting) ---- */
  @keyframes popIn{0%{opacity:0;transform:scale(.96) translateY(8px)}100%{opacity:1;transform:none}}
  @keyframes slideInRight{from{opacity:0;transform:translateX(24px)}to{opacity:1;transform:none}}
  @keyframes rowIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
  @keyframes spin{to{transform:rotate(360deg)}}
  @keyframes pulseCrit{0%{box-shadow:0 0 0 0 rgba(217,83,79,.35)}70%{box-shadow:0 0 0 8px rgba(217,83,79,0)}100%{box-shadow:0 0 0 0 rgba(217,83,79,0)}}
  @keyframes bandPop{0%{transform:scale(.8);opacity:.4}100%{transform:scale(1);opacity:1}}
  table tr{animation:rowIn var(--dur) var(--ease) both}
  table tr:nth-child(2){animation-delay:.02s}table tr:nth-child(3){animation-delay:.04s}
  table tr:nth-child(4){animation-delay:.06s}table tr:nth-child(5){animation-delay:.08s}
  table tr:nth-child(6){animation-delay:.10s}table tr:nth-child(7){animation-delay:.12s}
  table tr:nth-child(n+8){animation-delay:.14s}
  .v360-panel,.rev-panel,.tier-card,.stat,.v360-attr{animation:popIn var(--dur-lg) var(--ease) both}
  .btn:active{transform:translateY(1px) scale(.985)}
  .btn{transition:transform var(--dur) var(--ease),background var(--dur) var(--ease),box-shadow var(--dur) var(--ease)}
  .btn:hover{box-shadow:0 2px 8px rgba(20,48,42,.14)}
  .modal,.modal-card,.sheet{animation:popIn var(--dur-lg) var(--ease) both}
  .flash,.toast{animation:slideInRight var(--dur-lg) var(--ease) both}
  .crit-band.on{animation:bandPop var(--dur-lg) var(--ease) both}
  .crit-band.on .crit-opt.sel{animation:pulseCrit 1.8s ease-out 1}
  .spin{display:inline-block;width:14px;height:14px;border:2px solid var(--line);
        border-top-color:var(--green);border-radius:50%;animation:spin .7s linear infinite;vertical-align:-2px}
  #nav a{transition:background var(--dur) var(--ease),padding-left var(--dur) var(--ease)}
  #nav a:hover{padding-left:14px}
  .band,.posture-pill,.tag.crit{animation:bandPop var(--dur) var(--ease) both}
  @media (prefers-reduced-motion: reduce){
    *,#view>*,table tr,.v360-panel,.rev-panel,.tier-card,.stat,.v360-attr,.modal,.flash,.crit-band.on{
      animation:none!important;transition:none!important}
  }
  #view>*{animation:fadeUp var(--dur-lg) var(--ease) both}
  #view>*:nth-child(2){animation-delay:.04s} #view>*:nth-child(3){animation-delay:.08s}
  #view>*:nth-child(4){animation-delay:.12s} #view>*:nth-child(n+5){animation-delay:.16s}

  /* ---- shell: topbar + grouped sidebar + main ---- */
  #app{display:flex;flex-direction:column;min-height:100vh}
  .topbar{position:sticky;top:0;z-index:30;display:flex;align-items:center;justify-content:space-between;gap:16px;
          background:rgba(11,14,12,.86);-webkit-backdrop-filter:saturate(180%) blur(20px);backdrop-filter:saturate(180%) blur(20px);
          color:#fff;padding:13px 22px;border-bottom:1px solid rgba(201,155,95,.22);box-shadow:0 6px 20px rgba(0,0,0,.16)}
  .topbar .brand{display:flex;align-items:center;gap:13px}
  .topbar .logo{width:42px;height:42px;border-radius:12px;background:linear-gradient(150deg,#E2BD86,#C99B5F 58%,#A87E45);
        color:#0B0E0C;font-family:'Fraunces',serif;font-weight:700;font-size:24px;display:flex;align-items:center;justify-content:center;
        box-shadow:0 2px 10px rgba(201,155,95,.4),inset 0 1px 0 rgba(255,255,255,.4)}
  .topbar .brand-name{font-size:20px;font-weight:600;letter-spacing:-.01em;font-family:'Fraunces',serif}
  .topbar .brand-sub{font-size:9.5px;color:#a8b0a8;margin-top:3px;letter-spacing:.12em}
  .topbar-right{display:flex;align-items:center;gap:10px}
  .role-badge{display:flex;align-items:center;gap:9px;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1);border-radius:11px;padding:6px 12px}
  .role-badge .role-ico{font-size:18px}
  .role-badge .role-name{font-size:13px;font-weight:600} .role-badge .role-kind{font-size:10px;color:#a8b0a8}
  .signout{color:#fff;background:rgba(255,255,255,.1);border-radius:10px;padding:7px 13px;font-size:12px;font-weight:500;cursor:pointer;border:none}
  .signout:hover{background:var(--crit)}
  .shell{display:flex;flex:1;min-height:0}
  aside{width:232px;background:var(--soft);border-right:1px solid var(--line);padding:18px 10px;flex-shrink:0;overflow-y:auto}
  .nav-group{margin-bottom:14px}
  .nav-group-label{font-size:9px;color:var(--mute);text-transform:uppercase;padding:0 10px 6px;letter-spacing:.1em}
  nav a{display:flex;align-items:center;gap:11px;width:100%;text-align:left;padding:9px 11px;border-radius:10px;
        color:var(--ink-2);font-size:14px;font-weight:450;cursor:pointer;position:relative;
        transition:background var(--dur) var(--ease),color var(--dur) var(--ease)}
  nav a:hover{background:var(--softer)}
  nav a.active{background:var(--paper);color:var(--accent);font-weight:600;box-shadow:var(--sh-1)}
  nav a.active::before{content:"";position:absolute;left:-1px;top:50%;transform:translateY(-50%);width:3px;height:18px;border-radius:3px;background:var(--accent)}
  nav .ico{font-size:16px;width:20px;text-align:center;flex:none}

  main{flex:1;padding:28px 32px;overflow-y:auto;min-width:0;max-width:1280px}
  .top{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;margin-bottom:22px}
  .top h1{font-size:33px;font-weight:600;letter-spacing:-.012em;line-height:1.08}
  .top .sub{color:var(--mute);font-size:14.5px;margin-top:8px;max-width:680px}

  .btn{background:var(--accent);color:#fff;border:none;padding:11px 17px;border-radius:var(--r-sm);
       font-family:inherit;font-size:14px;font-weight:600;cursor:pointer;
       transition:transform var(--dur) var(--ease),box-shadow var(--dur) var(--ease),background var(--dur) var(--ease);
       box-shadow:0 1px 2px rgba(26,77,60,.2)}
  .btn:hover{background:#196046;transform:translateY(-1px);box-shadow:0 5px 16px rgba(26,77,60,.28)}
  .btn:active{transform:translateY(0)}
  .btn:disabled{opacity:.45;cursor:not-allowed;box-shadow:none;transform:none}
  .btn.ghost{background:var(--paper);color:var(--accent);border:1px solid var(--line);box-shadow:none}
  .btn.ghost:hover{border-color:var(--accent);background:var(--soft)}
  .btn.amber{background:var(--warn)} .btn.sm{padding:7px 12px;font-size:12px}

  .grid{display:grid;gap:14px}
  .g4{grid-template-columns:repeat(4,1fr)} .g3{grid-template-columns:repeat(3,1fr)}
  .g2{grid-template-columns:repeat(2,1fr)}
  .card{background:var(--paper);border:1px solid var(--line);border-radius:var(--r-lg);padding:24px;
        box-shadow:var(--sh-1);transition:transform var(--dur) var(--ease),box-shadow var(--dur) var(--ease)}
  .card:hover{box-shadow:var(--sh-2)}
  .stat{position:relative;overflow:hidden;text-align:left}
  .stat .v{font-family:'Fraunces',serif;font-size:30px;font-weight:600;color:var(--accent);line-height:1}
  .stat .l{font-size:12px;letter-spacing:.02em;color:var(--mute);font-weight:500;margin-top:7px}

  .sec-h{display:flex;align-items:center;gap:10px;margin:26px 0 14px}
  .sec-h h2{font-size:18px;font-weight:600} .sec-h .rule{flex:1;height:1px;background:linear-gradient(90deg,var(--line),transparent)}

  table{width:100%;border-collapse:collapse;background:var(--paper);border:1px solid var(--line);border-radius:var(--r-lg);overflow:hidden;box-shadow:var(--sh-1)}
  th{background:var(--softer);color:var(--ink-2);text-align:left;padding:11px 16px;font-size:11px;letter-spacing:.04em;text-transform:uppercase;font-weight:600;font-family:'JetBrains Mono',monospace}
  td{padding:12px 16px;border-bottom:1px solid var(--line-2);font-size:13.5px}
  tr:last-child td{border-bottom:none}
  tr.click{cursor:pointer;transition:background var(--dur) var(--ease)} tr.click:hover td{background:var(--soft)}

  .band{display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;color:#fff}
  .band.HIGH{background:var(--crit)} .band.ELEVATED{background:var(--warn)}
  .band.MODERATE{background:var(--mod)} .band.LOW{background:var(--ok)}
  .tag{display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;background:var(--softer);color:var(--ink-2)}
  .crit{background:#f7e6e3;color:var(--crit)}

  /* ---- analysis sections (FDD / Reputation / Monitoring / Contracts) ---- */
  .seg{display:flex;gap:4px;background:#efece2;border-radius:10px;padding:4px;margin-bottom:16px;flex-wrap:wrap}
  .seg button{flex:1;min-width:90px;border:none;background:transparent;padding:8px 10px;border-radius:7px;
        font-family:inherit;font-size:12.5px;font-weight:600;color:var(--mut);cursor:pointer;transition:.15s}
  .seg button.on{background:#fff;color:var(--green);box-shadow:0 1px 3px rgba(20,48,42,.12)}
  /* ---- CR-9 Critical top band ---- */
  .crit-band{display:flex;justify-content:space-between;align-items:center;gap:16px;
        background:#f6f4ec;border:1px solid var(--line);border-left:4px solid #9aa6a0;
        border-radius:12px;padding:14px 18px;margin-bottom:16px;transition:.25s}
  .crit-band.on{background:linear-gradient(90deg,#fbe7e6,#f7f1ea);border-left-color:#d9534f}
  .crit-band-label{font-family:'Fraunces',serif;font-size:16px;font-weight:600;color:var(--ink)}
  .crit-band-sub{display:block;font-size:11.5px;color:var(--mut);margin-top:2px;max-width:620px}
  .crit-toggle{display:flex;gap:4px;background:#fff;border:1px solid var(--line);border-radius:9px;padding:3px}
  .crit-opt{border:none;background:transparent;padding:7px 18px;border-radius:7px;font-family:inherit;
        font-size:13px;font-weight:700;color:var(--mut);cursor:pointer;transition:.18s}
  .crit-opt.sel{background:var(--green);color:#fff}
  .crit-band.on .crit-opt.sel{background:#d9534f}
  /* ---- CR-10 risk attributes panel on 360 ---- */
  .v360-attr-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
  .v360-attr{background:#faf9f4;border:1px solid var(--line);border-radius:10px;padding:11px 13px}
  .v360-attr .al{font-size:10.5px;text-transform:uppercase;letter-spacing:.05em;color:var(--mut)}
  .v360-attr .av{font-family:'Fraunces',serif;font-size:15px;font-weight:600;color:var(--ink);margin-top:3px}
  .v360-attr .as{font-size:11px;color:var(--mut);margin-top:2px}
  /* ---- CR-2 assessment review ---- */
  .rev-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px}
  .rev-panel{background:#fff;border:1px solid var(--line);border-radius:14px;padding:18px}
  .rev-panel h3{font-size:12.5px;text-transform:uppercase;letter-spacing:.05em;color:var(--green);margin:0 0 12px}
  .rev-row{display:flex;justify-content:space-between;gap:12px;padding:7px 0;border-bottom:1px solid #f0ede4;font-size:13px}
  .rev-row:last-child{border-bottom:none}
  .rev-row .rk{color:var(--mut)}.rev-row .rv{font-weight:600;color:var(--ink);text-align:right;max-width:60%}
  .rev-risk{display:flex;align-items:center;gap:9px;padding:8px 0;border-bottom:1px solid #f0ede4;font-size:13px}
  .rev-risk:last-child{border-bottom:none}
  .rev-stage{margin-bottom:12px}
  .rev-stage-h{font-size:12px;font-weight:700;color:var(--green);margin-bottom:5px}
  .rev-turn{font-size:12px;color:#43504a;padding:4px 0 4px 10px;border-left:2px solid #e6e2d6;margin-bottom:3px}
  .rev-verdict{margin-top:10px;padding:10px 12px;background:#f6f4ec;border-radius:9px;font-size:12.5px;color:#3a463f;white-space:pre-wrap}
  .rev-gaps{margin-top:10px;font-size:12px;color:#9a6a1a;background:#fbf2d6;padding:9px 11px;border-radius:8px}
  /* supply-chain concentration legend */
  .conc-legend{display:flex;gap:18px;flex-wrap:wrap;margin-top:10px;font-size:11.5px;color:var(--mut)}
  .conc-legend i.cdot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:5px;vertical-align:-1px}
  .v360-hero{background:linear-gradient(135deg,#14302a 0%,#1d4a40 100%);color:#f4f1e8;border-radius:16px;
        padding:24px 26px;margin-bottom:18px;position:relative;overflow:hidden}
  .v360-hero .vname{font-family:'Fraunces',serif;font-size:24px;font-weight:600;letter-spacing:-.01em}
  .v360-hero .vmeta{font-size:12.5px;opacity:.82;margin-top:3px}
  .v360-verdict{display:flex;align-items:center;gap:16px;margin-top:18px}
  .v360-dot{width:54px;height:54px;border-radius:50%;flex-shrink:0;box-shadow:0 0 0 5px rgba(255,255,255,.12)}
  .v360-dot.l0{background:#4caf7e}.v360-dot.l1{background:#d9b441}.v360-dot.l2{background:#e08a3c}.v360-dot.l3{background:#d9534f}
  .v360-vlabel{font-family:'Fraunces',serif;font-size:21px;font-weight:600}
  .v360-vsub{font-size:12px;opacity:.8}
  .v360-crit{position:absolute;top:18px;right:22px;background:var(--gold);color:#14302a;font-size:11px;
        font-weight:700;padding:5px 11px;border-radius:20px;letter-spacing:.03em}
  .v360-dims{display:grid;grid-template-columns:repeat(6,1fr);gap:10px;margin-bottom:18px}
  .v360-dim{background:#fff;border:1px solid var(--line);border-radius:12px;padding:13px 12px;text-align:center}
  .v360-dim .dv{font-family:'Fraunces',serif;font-size:18px;font-weight:600;color:var(--green)}
  .v360-dim .dl{font-size:10.5px;text-transform:uppercase;letter-spacing:.05em;color:var(--mut);margin-top:4px}
  .v360-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px}
  .v360-panel{background:#fff;border:1px solid var(--line);border-radius:14px;padding:18px}
  .v360-panel h3{font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:var(--mut);margin:0 0 12px}
  .v360-metric{display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid #f0ede4;font-size:13px}
  .v360-metric:last-child{border-bottom:none}
  .v360-metric .mk{color:var(--mut)}.v360-metric .mv{font-weight:600;color:var(--ink)}
  .v360-exc{display:flex;align-items:center;gap:10px;padding:9px 0;border-bottom:1px solid #f0ede4;font-size:13px}
  .v360-exc:last-child{border-bottom:none}
  .v360-sevdot{width:9px;height:9px;border-radius:50%;flex-shrink:0}
  .sev-Critical{background:#d9534f}.sev-High{background:#e08a3c}.sev-Medium{background:#d9b441}.sev-Low{background:#7a8c84}
  .v360-bar{height:8px;border-radius:5px;background:#eee;overflow:hidden;margin-top:6px}
  .v360-bar span{display:block;height:100%}
  .port-row{display:grid;grid-template-columns:1.6fr .7fr .9fr .8fr .6fr;gap:10px;align-items:center;
        padding:11px 14px;border:1px solid var(--line);border-radius:10px;margin-bottom:7px;background:#fff;cursor:pointer;transition:.12s}
  .port-row:hover{border-color:var(--green);box-shadow:0 2px 8px rgba(20,48,42,.08)}
  .posture-pill{font-size:11px;font-weight:700;padding:4px 9px;border-radius:14px;text-align:center}
  .pp-0{background:#e3f3ea;color:#1f7a4d}.pp-1{background:#fbf2d6;color:#94701a}
  .pp-2{background:#fbe7d4;color:#a85a1e}.pp-3{background:#f7dcda;color:#a5322e}
  .ent-box{background:#fff;border:1px solid var(--line);border-radius:12px;padding:16px;margin-bottom:14px}
  .ent-box .row2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
  .score-strip{display:flex;gap:20px;align-items:center;margin-bottom:18px;flex-wrap:wrap}
  .score-big{text-align:center;min-width:120px}
  .score-num{font-family:'Fraunces',serif;font-size:46px;font-weight:900;line-height:1;color:var(--green)}
  .score-cap{font-size:10px;color:var(--mut);text-transform:uppercase;letter-spacing:.1em;margin-top:4px}
  .altman{display:flex;flex-direction:column;gap:4px}
  .altman-z{font-size:15px} .altman-z b{font-size:20px;margin-left:6px}
  .pillar-row{display:grid;grid-template-columns:repeat(5,1fr);gap:14px;margin-bottom:16px}
  .pillar-row.wrap{grid-template-columns:repeat(auto-fit,minmax(150px,1fr))}
  .gauge{display:flex;flex-direction:column;gap:6px;background:#fff;border:1px solid var(--line);border-radius:10px;padding:12px}
  .gauge-bar{height:9px;background:#efece2;border-radius:6px;overflow:hidden}
  .gauge-fill{height:100%;border-radius:6px;transition:width .7s cubic-bezier(.16,.84,.44,1)}
  .gauge-fill.ok{background:var(--moss)} .gauge-fill.info{background:var(--navy)}
  .gauge-fill.warn{background:var(--amber)} .gauge-fill.crit{background:var(--rust)}
  .gauge-meta{display:flex;justify-content:space-between;font-size:11.5px}
  .gauge-meta .gl{color:var(--mut)} .gauge-meta .gv{font-weight:700}
  .tier-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:14px}
  .tier-card{border-radius:11px;padding:14px;border:1px solid var(--line)}
  .tier-card.crit{background:#f9ece9} .tier-card.warn{background:#f8f0e2}
  .tier-card.info{background:#eaf0f4} .tier-card.mute{background:#f1efe8}
  .tier-no{font-size:10px;font-weight:800;letter-spacing:.08em;color:var(--mut)}
  .tier-card p{margin-top:6px;font-size:12px;color:var(--mut)}
  .prov{margin-top:14px;border:1px solid var(--line);border-radius:12px;padding:15px;background:var(--paper)}
  .prov-head{display:flex;justify-content:space-between;align-items:center;gap:12px;font-size:14px}
  .prov-meta{font-size:12.5px;color:var(--mut);margin-top:7px}
  .ai-out{background:#fff;border:1px solid var(--line);border-radius:11px;padding:16px;margin-top:12px;font-size:13.5px;line-height:1.6;white-space:pre-wrap}
  .stress-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:12px}
  .stress-grid input[type=range]{width:100%}
  .pill{display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:700}
  .pill.ok{background:#e3efe6;color:var(--moss)} .pill.info{background:#e7eef3;color:var(--navy)}
  .pill.warn{background:#f6ebda;color:var(--amber)} .pill.crit{background:#f6e2de;color:var(--rust)}
  .pill.mute{background:#eee;color:var(--mut)}
  .empty-box{text-align:center;padding:38px;color:var(--mut)}
  .empty-box .ei{font-size:34px;margin-bottom:8px} .empty-box .et{font-weight:700;color:var(--ink);font-size:15px}

  /* forms */
  .field{margin-bottom:13px}
  label{display:block;font-size:12px;font-weight:600;color:var(--mut);margin-bottom:5px;letter-spacing:.02em}
  input,select,textarea{width:100%;padding:9px 11px;border:1px solid var(--line);border-radius:8px;
        font-family:inherit;font-size:13px;background:#fff;transition:border-color .15s,box-shadow .15s}
  input:focus,select:focus,textarea:focus{outline:none;border-color:var(--green);
        box-shadow:0 0 0 3px rgba(26,77,60,.12)}

  /* modal */
  .ovl{position:fixed;inset:0;background:rgba(20,40,32,.42);display:flex;align-items:center;
       justify-content:center;z-index:50;padding:20px;backdrop-filter:blur(3px);
       animation:ovlIn .18s ease}
  @keyframes ovlIn{from{opacity:0}to{opacity:1}}
  .modal{background:#fff;border-radius:15px;padding:24px;width:480px;max-width:100%;max-height:90vh;
         overflow:auto;box-shadow:0 30px 80px rgba(0,0,0,.28);
         animation:modalIn .24s cubic-bezier(.16,.84,.44,1)}
  @keyframes modalIn{from{opacity:0;transform:translateY(16px) scale(.98)}to{opacity:1;transform:none}}
  .modal h3{font-size:18px;margin-bottom:16px}
  .modal .row{display:flex;gap:10px;justify-content:flex-end;margin-top:18px}

  /* login */
  #login{display:flex;align-items:center;justify-content:center;min-height:100vh;width:100%;
         background:radial-gradient(circle at 30% 20%,#15302a,#0B0E0C 70%)}
  #login .box{background:var(--paper);border-radius:var(--r-xl);padding:40px;width:392px;box-shadow:0 30px 80px rgba(0,0,0,.4)}
  #login .brand{text-align:center;margin-bottom:24px}
  #login .brand .logo{width:54px;height:54px;border-radius:14px;margin:0 auto 14px;
        background:linear-gradient(150deg,#E2BD86,#C99B5F 58%,#A87E45);color:#0B0E0C;
        font-family:'Fraunces',serif;font-weight:700;font-size:30px;display:flex;align-items:center;justify-content:center;
        box-shadow:0 2px 10px rgba(201,155,95,.4),inset 0 1px 0 rgba(255,255,255,.4)}
  #login .brand b{font-family:'Fraunces',serif;font-size:24px;font-weight:600;color:var(--ink);display:block}
  #login .brand span{font-size:9.5px;letter-spacing:.14em;color:var(--mute);font-family:'JetBrains Mono',monospace}
  #login .tag{font-style:italic;color:var(--mute);font-size:12px;margin-top:8px;text-align:center;display:block}
  .err{background:#f7e6e3;color:var(--crit);padding:9px 12px;border-radius:var(--r-sm);font-size:12px;margin-bottom:12px}
  .muted{color:var(--mute);font-size:12.5px}
  .flash{position:fixed;bottom:20px;right:20px;background:var(--accent);color:#fff;padding:12px 18px;
         border-radius:var(--r-sm);font-size:13px;box-shadow:var(--sh-3);z-index:60}

  /* ---- AI Assessment chat surface ---- */
  .chat-wrap{display:grid;grid-template-columns:200px 1fr 230px;gap:14px;height:calc(100vh - 150px)}
  .chat-rail{background:#fff;border:1px solid var(--line);border-radius:11px;padding:14px;overflow:auto}
  .chat-rail h4{font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--mut);margin-bottom:8px}
  .agent-row{display:flex;align-items:center;gap:8px;padding:5px 4px;border-radius:7px;font-size:12px}
  .agent-row.active{background:#f0ede3}
  .adot{width:26px;height:26px;border-radius:50%;color:#fff;display:flex;align-items:center;
        justify-content:center;font-weight:800;font-size:11px;flex-shrink:0}
  .agent-row .an{font-weight:600} .agent-row .at{color:var(--mut);font-size:10px}
  .stagestrip{display:flex;gap:3px;margin-bottom:10px;flex-wrap:wrap}
  .ststep{flex:1;min-width:54px;text-align:center;padding:5px 2px;border-radius:5px;font-size:9px;
          font-weight:700;letter-spacing:.04em;background:#efece2;color:var(--mut)}
  .ststep.cur{background:var(--green);color:#fff} .ststep.done{background:#dCeadF;color:var(--moss)}
  .chat-main{display:flex;flex-direction:column;background:#fff;border:1px solid var(--line);border-radius:11px;overflow:hidden}
  .chat-scroll{flex:1;overflow:auto;padding:16px}
  .cmsg{margin-bottom:14px;display:flex;gap:9px}
  .cmsg.user{justify-content:flex-end}
  .cbub{max-width:78%;padding:9px 13px;border-radius:11px;font-size:13px;line-height:1.5}
  .cbub.agent{background:#f7f5ef;border:1px solid var(--line)}
  .cbub.user{background:var(--green);color:#fff}
  .cbub.sys{background:#f3eee0;color:var(--mut);font-size:11.5px;font-style:italic;max-width:100%;text-align:center;margin:0 auto}
  .cmsg-hdr{font-size:10px;font-weight:700;margin-bottom:3px}
  .chat-input{border-top:1px solid var(--line);padding:11px;display:flex;gap:8px;align-items:flex-end}
  .chat-input textarea{flex:1;border:1px solid var(--line);border-radius:8px;padding:9px;font-family:inherit;font-size:13px;resize:none}
  .insight{border-radius:7px;padding:8px 10px;margin-bottom:7px;font-size:11.5px;border-left:3px solid}
  .insight.high{background:#f6e2de;border-color:var(--rust)}
  .insight.medium{background:#f6ebda;border-color:var(--amber)}
  .insight.low{background:#eef2e8;border-color:var(--moss)}
  .insight .ik{font-weight:700;font-size:10px;text-transform:uppercase;letter-spacing:.06em}
  .learn{background:#f7f5ef;border:1px solid var(--line);border-radius:7px;padding:8px 10px;margin-bottom:7px;font-size:11.5px}
  .dossier-row{display:flex;justify-content:space-between;gap:8px;font-size:11.5px;padding:3px 0;border-bottom:1px solid #eee7d8}
  .dossier-row .dk{color:var(--mut)} .dossier-row .dv{font-weight:600;text-align:right}
  /* ---- supply-chain drill-down drawer ---- */
  .conc-drawer{position:fixed;top:0;right:0;height:100vh;width:420px;max-width:92vw;background:#fff;
    box-shadow:-8px 0 32px rgba(20,48,42,.18);border-left:1px solid var(--line);z-index:9000;
    transform:translateX(105%);transition:transform .26s cubic-bezier(.4,0,.2,1);display:flex;flex-direction:column}
  .conc-drawer.open{transform:translateX(0)}
  .conc-drawer .cd-head{display:flex;align-items:flex-start;justify-content:space-between;gap:10px;
    padding:18px 20px;background:linear-gradient(135deg,#14302A,#1A4D3C);color:#f3efe3}
  .conc-drawer .cd-kicker{font-size:10px;letter-spacing:.16em;text-transform:uppercase;color:#bcae8a;font-weight:700}
  .conc-drawer .cd-head h3{margin:3px 0 0;font-size:18px;color:#fff;line-height:1.2}
  .conc-drawer .cd-x{background:rgba(255,255,255,.14);border:none;color:#fff;width:30px;height:30px;
    border-radius:8px;cursor:pointer;font-size:14px;flex:none}
  .conc-drawer .cd-x:hover{background:rgba(255,255,255,.28)}
  .conc-drawer .cd-body{padding:16px 20px;overflow-y:auto;flex:1}
  .cd-stats{display:flex;flex-wrap:wrap;gap:14px;padding-bottom:14px;margin-bottom:12px;border-bottom:1px solid var(--line)}
  .cd-stats .cv{font-size:22px;font-weight:700;color:var(--forest);font-family:Fraunces,Georgia,serif}
  .cd-stats .cl{font-size:10px;letter-spacing:.06em;text-transform:uppercase;color:var(--mut)}
  .cd-lab{font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--moss);margin:4px 0 8px}
  .cd-card{background:#f7f5ef;border:1px solid var(--line);border-radius:9px;padding:10px 12px;margin-bottom:14px}
  .cd-row{display:flex;justify-content:space-between;gap:8px;font-size:12.5px;padding:3px 0}
  .cd-row span{color:var(--mut)} .cd-row b{text-align:right}
  .cd-list{display:flex;flex-direction:column;gap:6px}
  .cd-item{display:flex;flex-direction:column;gap:2px;padding:9px 11px;border:1px solid var(--line);
    border-radius:8px;cursor:pointer;background:#fff;transition:border-color .15s,background .15s}
  .cd-item:hover{border-color:var(--moss);background:#f3f6f1}
  .cd-item .ci-name{font-size:13px;font-weight:600;color:var(--ink)}
  .cd-item .ci-meta{font-size:11px;color:var(--mut)}
  .band{display:inline-block;padding:1px 6px;border-radius:4px;font-size:10px;font-weight:700}
  .band.HIGH{background:#f8d7d7;color:#a02929}.band.ELEVATED{background:#f6e2c8;color:#9a6418}
  .band.MODERATE{background:#e6eef6;color:#2a5a8a}.band.LOW{background:#e3efe6;color:#1A4D3C}
  .tag.crit{background:#f8d7d7;color:#a02929;padding:1px 6px;border-radius:4px;font-weight:700}
  /* ---- board intelligence ---- */
  .intel-shell{display:grid;grid-template-columns:340px 1fr;gap:16px;margin-top:6px}
  @media(max-width:1024px){.intel-shell{grid-template-columns:1fr}}
  .intel-console{background:#0e1f1a;color:#bfe3c9;border-radius:12px;padding:14px 16px;height:560px;overflow-y:auto;
    font-family:'Spline Sans Mono',ui-monospace,monospace;font-size:12px;line-height:1.55;box-shadow:inset 0 0 0 1px #1c3a30}
  .intel-console .il-line{padding:3px 0;border-bottom:1px solid rgba(255,255,255,.04)}
  .intel-console .il-line b{color:#fff}
  .intel-console .il-line.muted{color:#7f9a86}
  .intel-console .il-line.ok{color:#7fe0a0;font-weight:600}
  .intel-console .il-line.err{color:#ff9b8a}
  .intel-canvas{background:#fff;border:1px solid var(--line);border-radius:12px;padding:20px 22px;min-height:560px;
    max-height:760px;overflow-y:auto;box-shadow:var(--sh,0 1px 2px rgba(0,0,0,.05))}
  .intel-empty{height:480px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;color:#5a6b62}
  .ie-mark{font-size:46px;color:#cdbd92;margin-bottom:10px}
  .ie-mark.spin{animation:spin 1.6s linear infinite}
  @keyframes spin{to{transform:rotate(360deg)}}
  .ib-brief{background:linear-gradient(135deg,#14302A,#1A4D3C);color:#eef2ec;border-radius:12px;padding:18px 20px}
  .ib-kicker{font-size:10px;letter-spacing:.16em;text-transform:uppercase;color:#bcae8a;font-weight:700}
  .ib-brief p{font-size:15px;line-height:1.5;margin:8px 0 14px;color:#f3f6f2}
  .ib-metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
  @media(max-width:560px){.ib-metrics{grid-template-columns:repeat(2,1fr)}}
  .ib-metrics .ibm-v{font-family:Fraunces,Georgia,serif;font-size:21px;font-weight:600;color:#fff}
  .ib-metrics .ibm-k{font-size:10px;letter-spacing:.05em;text-transform:uppercase;color:#a9c1ad}
  .bar-row{display:grid;grid-template-columns:120px 1fr 64px;align-items:center;gap:10px;padding:4px 0;font-size:12px}
  .bar-lab{color:var(--mut);text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .bar-track{background:#eef0ea;border-radius:6px;height:14px;overflow:hidden}
  .bar-fill{height:100%;border-radius:6px;transition:width .5s ease}
  .bar-val{font-weight:600;font-size:12px}
  .ic-card{background:#fbfaf6;border:1px solid var(--line);border-radius:10px;padding:14px 16px}
  .ic-title{font-size:12px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;color:var(--moss);margin-bottom:8px}
  .ic-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
  @media(max-width:720px){.ic-grid{grid-template-columns:1fr}}
  .pestle-row{display:grid;grid-template-columns:120px 1fr 96px;align-items:center;gap:10px;padding:6px 0;border-bottom:1px solid #efece1}
  .pestle-row:last-child{border-bottom:none}
  .pe-fac{font-weight:700;font-size:13px} .pe-sev{font-size:12px;font-weight:700;text-align:right}
  .pe-head{grid-column:1 / -1;font-size:11.5px;margin-top:-2px}
  .obs-list{display:flex;flex-direction:column;gap:12px}
  .obs-card{background:#fff;border:1px solid var(--line);border-left:4px solid #2E6A4F;border-radius:10px;padding:14px 16px}
  .obs-top{display:flex;align-items:center;gap:8px;margin-bottom:6px;flex-wrap:wrap}
  .obs-sev{color:#fff;font-size:10px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;padding:2px 8px;border-radius:5px}
  .obs-fac{font-size:10px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;padding:2px 8px;border:1px solid;border-radius:5px}
  .obs-hz{font-size:11px;margin-left:auto}
  .obs-card h3{font-size:16px;margin:2px 0 8px;color:var(--ink)}
  .obs-ev,.obs-sw{font-size:12.5px;color:var(--ink-soft,#4a554f);margin-bottom:6px;line-height:1.5}
  .obs-ev b,.obs-sw b{color:var(--moss)}
  .obs-act{font-size:13px;background:#f3f6f1;border:1px solid #d8e6dc;border-radius:8px;padding:9px 11px;margin-top:6px;line-height:1.5}
  .oa-tag{display:inline-block;background:var(--forest,#14302A);color:#fff;font-size:9.5px;font-weight:700;letter-spacing:.05em;
    text-transform:uppercase;padding:2px 7px;border-radius:5px;margin-right:7px}
  .pred-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
  @media(max-width:720px){.pred-grid{grid-template-columns:1fr}}
  .pred-card{background:#fbfaf6;border:1px solid var(--line);border-radius:10px;padding:14px 16px}
  .pred-top{display:flex;justify-content:space-between;align-items:center;margin-bottom:4px}
  .pred-metric{font-family:Fraunces,Georgia,serif;font-size:18px;font-weight:600;color:var(--forest)}
  .pred-conf{font-size:10px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;color:var(--gold,#B8862B)}
  .pred-card h4{font-size:14px;margin:2px 0 5px;color:var(--ink)}
  .pred-card p{font-size:12px;line-height:1.5;margin:0}
</style>
</head>
<body>

<!-- LOGIN -->
<div id="login">
  <div class="box">
    <div class="brand"><div class="logo">B</div><b>BRO · Risk Oracle</b><span>ENTERPRISE TPRM</span>
      <span class="tag">Exposure first. Controls second. Verdict last.</span></div>
    <div id="loginErr" class="err hidden"></div>
    <div class="field"><label>Username</label><input id="lu" value="admin"></div>
    <div class="field"><label>Password</label><input id="lp" type="password" value="admin"></div>
    <button class="btn" style="width:100%" onclick="doLogin()">Sign in</button>
    <p class="muted" style="text-align:center;margin-top:14px">Default: admin / admin</p>
  </div>
</div>

<!-- APP -->
<div id="app" class="hidden">
  <header class="topbar">
    <div class="brand">
      <div class="logo">B</div>
      <div><div class="brand-name">BRO · Risk Oracle</div>
        <div class="brand-sub">ENTERPRISE TPRM · POWERED BY CLAUDE</div></div>
    </div>
    <div class="topbar-right">
      <div class="role-badge"><span class="role-ico">🛡️</span>
        <div><div class="role-name" id="whoName">—</div><div class="role-kind" id="whoRole">—</div></div></div>
      <button class="signout" onclick="logout()">Sign out</button>
    </div>
  </header>
  <div class="shell">
    <aside>
      <nav id="nav">
        <div class="nav-group">
          <a data-v="dashboard" class="active"><span class="ico">🏠</span>Home</a>
        </div>
        <div class="nav-group"><div class="nav-group-label">Assessment</div>
          <a data-v="assess"><span class="ico">🗣️</span>BRO Chat</a>
          <a data-v="assessments"><span class="ico">🗂️</span>Open Assessments</a>
          <a data-v="proassess"><span class="ico">⚡</span>ProAssess</a>
        </div>
        <div class="nav-group"><div class="nav-group-label">Vendors</div>
          <a data-v="artefacts"><span class="ico">📜</span>Certifications</a>
          <a data-v="vendors"><span class="ico">🏢</span>Vendor Register</a>
          <a data-v="engagements"><span class="ico">▦</span>Engagements</a>
          <a data-v="vendor360"><span class="ico">◎</span>Vendor 360</a>
          <a data-v="performance"><span class="ico">📈</span>Performance</a>
        </div>
        <div class="nav-group"><div class="nav-group-label">Intelligence</div>
          <a data-v="intel"><span class="ico">✦</span>Intelligence</a>
      <a data-v="fdd"><span class="ico">💰</span>Financial DD</a>
      <a data-v="reputation"><span class="ico">🗞</span>Reputation</a>
      <a data-v="contracts"><span class="ico">⚖</span>Contracts</a>
          <a data-v="management"><span class="ico">📊</span>Management</a>
        </div>
        <div class="nav-group"><div class="nav-group-label">Governance</div>
          <a data-v="findings"><span class="ico">✅</span>Action Plan</a>
          <a data-v="issues"><span class="ico">⚠️</span>Issues Log</a>
          <a data-v="fourthparties"><span class="ico">🔗</span>4th Party Register</a>
          <a data-v="review"><span class="ico">🔎</span>Review Queue</a>
          <a data-v="governance"><span class="ico">§</span>Governance</a>
          <a data-v="audit"><span class="ico">🔒</span>Audit Trail</a>
        </div>
        <div class="nav-group"><div class="nav-group-label">Reference & Admin</div>
          <a data-v="lifecycle"><span class="ico">♻️</span>Lifecycle</a>
          <a data-v="reports"><span class="ico">📁</span>Reports</a>
          <a data-v="notifications"><span class="ico">🔔</span>Notifications</a>
          <a data-v="admin"><span class="ico">⚙️</span>Admin</a>
          <a data-v="settings"><span class="ico">⛭</span>Settings</a>
        </div>
      </nav>
    </aside>
    <main id="view"></main>
  </div>
</div>

<div id="modalRoot"></div>
<div id="flashRoot"></div>

<script>
const API="/api/v1"; let TOKEN=null, ME=null;

function tok(){return sessionStorage.getItem("bro_tok")}
async function api(path, opts={}){
  const h = {"Content-Type":"application/json"};
  if(tok()) h["Authorization"]="Bearer "+tok();
  const r = await fetch(API+path, {...opts, headers:{...h, ...(opts.headers||{})}});
  if(r.status===401){ logout(); throw new Error("session expired"); }
  if(!r.ok){ const e=await r.json().catch(()=>({detail:r.statusText})); throw new Error(e.detail||"error"); }
  return r.status===204?null:r.json();
}
function flash(msg){ const d=document.createElement("div"); d.className="flash"; d.textContent=msg;
  document.getElementById("flashRoot").appendChild(d); setTimeout(()=>d.remove(),2600); }
async function api2(path, opts={}){
  const h = {"Content-Type":"application/json"};
  if(tok()) h["Authorization"]="Bearer "+tok();
  const r = await fetch("/api/v2"+path, {...opts, headers:{...h, ...(opts.headers||{})}});
  if(r.status===401){ logout(); throw new Error("session expired"); }
  if(!r.ok){ const e=await r.json().catch(()=>({detail:r.statusText})); throw new Error(e.detail||"error"); }
  return r.status===204?null:r.json();
}
function esc(s){return (s==null?"":String(s)).replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]))}
// CR-6: key -> human label. Sentence case (capitalise first word only), preserving acronyms.
const _ACRONYMS={tcv:"TCV",acv:"ACV",rto:"RTO",rpo:"RPO",dpa:"DPA",po:"PO",fx:"FX",ict:"ICT",
  raci:"RACI",sla:"SLA",kpi:"KPI",ddq:"DDQ",irq:"IRQ",sic:"SIC",lei:"LEI",euid:"EUID",duns:"D-U-N-S",
  erp:"ERP",grc:"GRC",unspsc:"UNSPSC",nace:"NACE",naics:"NAICS",vat:"VAT",iban:"IBAN",swift:"SWIFT",
  bic:"BIC",esg:"ESG",pep:"PEP",abac:"ABAC",coi:"COI",ubo:"UBO",bcp:"BCP",id:"ID",url:"URL",ref:"ref"};
function lbl(k){
  if(k==null) return "";
  const words=String(k).replace(/_/g," ").trim().split(/\s+/);
  return words.map((w,i)=>{
    const low=w.toLowerCase();
    if(_ACRONYMS[low]) return _ACRONYMS[low];
    if(i===0) return w.charAt(0).toUpperCase()+w.slice(1);
    return w;
  }).join(" ");
}
// CR-8: canonical country list (ISO short names) — reused everywhere a country is needed
const COUNTRIES=["Afghanistan","Albania","Algeria","Andorra","Angola","Argentina","Armenia","Australia","Austria","Azerbaijan","Bahamas","Bahrain","Bangladesh","Barbados","Belarus","Belgium","Belize","Benin","Bhutan","Bolivia","Bosnia and Herzegovina","Botswana","Brazil","Brunei","Bulgaria","Burkina Faso","Burundi","Cambodia","Cameroon","Canada","Cape Verde","Central African Republic","Chad","Chile","China","Colombia","Comoros","Congo","Costa Rica","Croatia","Cuba","Cyprus","Czech Republic","Denmark","Djibouti","Dominica","Dominican Republic","Ecuador","Egypt","El Salvador","Equatorial Guinea","Eritrea","Estonia","Eswatini","Ethiopia","Fiji","Finland","France","Gabon","Gambia","Georgia","Germany","Ghana","Greece","Grenada","Guatemala","Guinea","Guyana","Haiti","Honduras","Hong Kong","Hungary","Iceland","India","Indonesia","Iran","Iraq","Ireland","Israel","Italy","Ivory Coast","Jamaica","Japan","Jordan","Kazakhstan","Kenya","Kiribati","Kuwait","Kyrgyzstan","Laos","Latvia","Lebanon","Lesotho","Liberia","Libya","Liechtenstein","Lithuania","Luxembourg","Madagascar","Malawi","Malaysia","Maldives","Mali","Malta","Mauritania","Mauritius","Mexico","Moldova","Monaco","Mongolia","Montenegro","Morocco","Mozambique","Myanmar","Namibia","Nepal","Netherlands","New Zealand","Nicaragua","Niger","Nigeria","North Korea","North Macedonia","Norway","Oman","Pakistan","Panama","Papua New Guinea","Paraguay","Peru","Philippines","Poland","Portugal","Qatar","Romania","Russia","Rwanda","Saudi Arabia","Senegal","Serbia","Seychelles","Sierra Leone","Singapore","Slovakia","Slovenia","Somalia","South Africa","South Korea","South Sudan","Spain","Sri Lanka","Sudan","Suriname","Sweden","Switzerland","Syria","Taiwan","Tajikistan","Tanzania","Thailand","Togo","Trinidad and Tobago","Tunisia","Turkey","Turkmenistan","Uganda","Ukraine","United Arab Emirates","United Kingdom","United States","Uruguay","Uzbekistan","Vanuatu","Venezuela","Vietnam","Yemen","Zambia","Zimbabwe"];
// CR-7: controlled vocabularies for Vendor Master Classification & segmentation
const VOCAB={
  supplier_category:["Strategic","Operational","Tactical","Commodity","Bottleneck","Leverage"],
  segmentation:["Strategic partner","Preferred","Approved","Transactional","Probationary","Exit"],
  tier:["Tier 1","Tier 2","Tier 3","Tier 4"],
  spend_band:["<£10k","£10k–£50k","£50k–£250k","£250k–£1m","£1m–£5m",">£5m"],
  substitutability:["Easily substitutable","Substitutable with effort","Hard to substitute","Sole source / no alternative"],
};
// field-type detection for typed inputs (CR-8)
function fieldType(k){
  const key=String(k).toLowerCase();
  if(/(^|_)country$|countries$|incorporation_country|tax_residency|^hq_country$|jurisdiction$|delivery_location$|receiving_location$/.test(key)) return "country";
  if(/date$|_date|dob$/.test(key)) return "date";
  if(/email/.test(key)) return "email";
  if(/phone|telephone|mobile|contact_number/.test(key)) return "phone";
  return "text";
}
function typedInput(idAttr,k,v){
  const t=fieldType(k); const val=(v==null?'':esc(String(v)));
  if(t==="country"){
    return `<select id="${idAttr}"><option value="">— select —</option>${COUNTRIES.map(c=>`<option ${String(v)===c?'selected':''}>${c}</option>`).join("")}</select>`;
  }
  if(t==="date") return `<input id="${idAttr}" type="date" value="${val}">`;
  if(t==="email") return `<input id="${idAttr}" type="email" placeholder="name@example.com" value="${val}">`;
  if(t==="phone") return `<input id="${idAttr}" type="tel" inputmode="tel" placeholder="+44…" value="${val}" oninput="this.value=this.value.replace(/(?!^\\+)[^0-9]/g,'').replace(/(?!^)\\+/g,'')">`;
  return `<input id="${idAttr}" value="${val}">`;
}

async function doLogin(){
  const u=document.getElementById("lu").value, p=document.getElementById("lp").value;
  try{
    const r = await fetch(API+"/login",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({username:u,password:p})});
    if(!r.ok) throw new Error("Invalid credentials");
    const d = await r.json();
    sessionStorage.setItem("bro_tok", d.token); ME=d;
    document.getElementById("login").classList.add("hidden");
    document.getElementById("app").classList.remove("hidden");
    document.getElementById("whoName").textContent=d.username;
    document.getElementById("whoRole").textContent=d.role.toUpperCase();
    go("dashboard");
  }catch(e){ const el=document.getElementById("loginErr"); el.textContent=e.message; el.classList.remove("hidden"); }
}
function logout(){ sessionStorage.removeItem("bro_tok"); location.reload(); }

document.getElementById("nav").addEventListener("click",e=>{
  const a=e.target.closest("a"); if(!a)return;
  document.querySelectorAll("#nav a").forEach(x=>x.classList.remove("active"));
  a.classList.add("active"); go(a.dataset.v);
});

const V={};
function go(v){ (V[v]||V.dashboard)(); }
function modal(html){ document.getElementById("modalRoot").innerHTML=
  `<div class="ovl" onclick="if(event.target===this)closeModal()"><div class="modal">${html}</div></div>`; }
function closeModal(){ document.getElementById("modalRoot").innerHTML=""; }
document.addEventListener("keydown",function(ev){ if(ev.key==="Escape"){ const r=document.getElementById("modalRoot"); if(r&&r.innerHTML.trim())closeModal(); } });

/* ---------- Dashboard ---------- */
V.dashboard=async()=>{
  const view=document.getElementById("view");
  view.innerHTML=`<div class="top"><div><h1>Executive Dashboard</h1>
    <div class="sub">Portfolio risk posture at a glance</div></div></div>
    <div id="dashBody" class="muted">Loading…</div>`;
  try{
    const d = await api("/dashboard/executive");
    const ops = await api("/dashboard/operational");
    const rb = d.by_residual||{};
    view.querySelector("#dashBody").innerHTML=`
      <div class="grid g4">
        <div class="card stat"><div class="v">${d.vendors}</div><div class="l">Vendors</div></div>
        <div class="card stat"><div class="v">${d.critical_vendors}</div><div class="l">Critical (Tier 0)</div></div>
        <div class="card stat"><div class="v">${d.engagements}</div><div class="l">Engagements</div></div>
        <div class="card stat"><div class="v">${d.open_findings}</div><div class="l">Open Findings</div></div>
      </div>
      <div class="sec-h"><h2>Residual risk distribution</h2><div class="rule"></div></div>
      <div class="grid g4">
        ${["HIGH","ELEVATED","MODERATE","LOW"].map(b=>`<div class="card stat">
          <div class="v">${rb[b]||0}</div><div class="l"><span class="band ${b}">${b}</span></div></div>`).join("")}
      </div>
      <div class="sec-h"><h2>Operational — by stage</h2><div class="rule"></div></div>
      <div class="card"><div class="muted">${Object.entries(ops.by_stage||{}).map(([k,v])=>
        `<span class="tag" style="margin:3px">${esc(k)}: ${v}</span>`).join("")||"No engagements yet"}</div></div>`;
  }catch(e){ view.querySelector("#dashBody").innerHTML=`<div class="err">${esc(e.message)}</div>`; }
};

/* ---------- Vendors ---------- */
V.vendors=async()=>{
  const view=document.getElementById("view");
  view.innerHTML=`<div class="top"><div><h1>Vendors</h1><div class="sub">Supplier register · auto Vendor ID &amp; Group ID</div></div>
    <button class="btn" onclick="newVendor()">+ New vendor</button></div><div id="vt" class="muted">Loading…</div>`;
  try{
    if(!window._industries){ window._industries = await api2("/industries"); }
    const vs = await api2("/vendors");
    view.querySelector("#vt").innerHTML = vs.length? `<table><tr><th>Vendor ID</th><th>Legal name</th><th>Group</th><th>Tier</th><th>Industries</th><th>Status</th><th></th></tr>
      ${vs.map(v=>`<tr class="click" onclick="openVendorMaster('${v.vendor_id}')"><td><b>${esc(v.vendor_id)}</b></td>
        <td>${esc(v.legal_name)}</td><td class="muted">${esc(v.group_id||"—")}</td><td>${esc(v.tier)}</td>
        <td>${(v.industries||[]).slice(0,2).map(i=>`<span class="tag" style="margin:1px">${esc(i)}</span>`).join("")}${(v.industries||[]).length>2?' +'+((v.industries.length)-2):''}</td>
        <td>${v.is_critical?'<span class="tag crit">CRITICAL</span>':`<span class="muted">${esc(v.status)}</span>`}</td>
        <td style="text-align:right"><button class="btn sm ghost" onclick="event.stopPropagation();openVendor('${v.vendor_id}')">summary</button> →</td></tr>`).join("")}</table>`
      : `<div class="card muted">No vendors yet. Create one — a Vendor ID and Group ID are minted automatically.</div>`;
  }catch(e){ view.querySelector("#vt").innerHTML=`<div class="err">${esc(e.message)}</div>`; }
};
function newVendor(){
  const inds=(window._industries||[]).map(i=>`<option value="${esc(i.industry_id)}">${esc(i.industry_id)}</option>`).join("");
  modal(`<h3>New vendor</h3>
  <p class="muted" style="margin-bottom:10px">Vendor ID and Group ID are auto-generated. The group is proposed automatically and can be changed later.</p>
  <div class="field"><label>Legal name</label><input id="nv_name"></div>
  <div class="field"><label>Trading name</label><input id="nv_trade"></div>
  <div class="field"><label>Parent / group company (optional)</label><input id="nv_parent" placeholder="vendors sharing a parent share a Group ID"></div>
  <div class="grid g2"><div class="field"><label>HQ country</label><input id="nv_country"></div>
    <div class="field"><label>Tier</label><select id="nv_tier"><option>Tier 1</option><option>Tier 2</option><option selected>Tier 3</option></select></div></div>
  <div class="field"><label>Industries (SIC — Ctrl/Cmd-click for multiple)</label><select id="nv_inds" multiple size="5" style="height:auto">${inds}</select></div>
  <div class="row"><button class="btn ghost" onclick="closeModal()">Cancel</button>
    <button class="btn" onclick="saveVendor()">Create</button></div>`); }
async function saveVendor(){
  const inds=[...document.getElementById("nv_inds").selectedOptions].map(o=>o.value);
  try{ const r=await api2("/vendors",{method:"POST",body:JSON.stringify({
    legal_name:val("nv_name"), trading_name:val("nv_trade"), parent_company:val("nv_parent"),
    hq_country:val("nv_country"), tier:val("nv_tier"), industries:inds, created_via:"button"})});
    closeModal(); flash(`Vendor ${r.vendor_id} created (group ${r.group_id})`); V.vendors();
  }catch(e){ flash(e.message); } }
async function openVendor(vid){
  const v=await api2("/vendors/"+vid);
  const contacts=(v.contacts||[]).length?v.contacts.map(c=>`<div class="dossier-row"><span class="dk">${c.is_primary?'<b>Primary</b> · ':''}${esc(c.name)}${c.designation?' ('+esc(c.designation)+')':''}</span><span class="dv">${esc(c.email||'')} ${esc(c.phone||'')}</span></div>`).join(""):'<div class="muted" style="font-size:12px">No contacts yet.</div>';
  const engs=(v.engagements||[]).length?v.engagements.map(e=>`<span class="tag" style="margin:2px">${esc(e.engagement_id)} · ${esc(e.title)} (${esc(e.status)})</span>`).join(""):'<span class="muted" style="font-size:12px">None</span>';
  modal(`<h3>${esc(v.legal_name)} <span class="muted" style="font-size:13px">${esc(v.vendor_id)}</span></h3>
    <div class="dossier-row"><span class="dk">Group ID</span><span class="dv">${esc(v.group_id||'—')} <button class="btn sm ghost" onclick="overrideGroup('${v.vendor_id}')">change</button></span></div>
    <div class="dossier-row"><span class="dk">Tier / Status</span><span class="dv">${esc(v.tier)} · ${esc(v.status)}</span></div>
    <div class="dossier-row"><span class="dk">HQ country</span><span class="dv">${esc(v.hq_country||'—')}</span></div>
    <div class="dossier-row"><span class="dk">Industries</span><span class="dv">${(v.industries||[]).map(i=>esc(i)).join(', ')||'—'}</span></div>
    ${v.fourth_party_id?`<div class="dossier-row"><span class="dk">Also 4th party</span><span class="dv">${esc(v.fourth_party_id)}</span></div>`:''}
    <div class="sec-h" style="margin:14px 0 6px"><h2 style="font-size:13px">Contacts</h2><div class="rule"></div></div>${contacts}
    <button class="btn sm ghost" style="margin-top:6px" onclick="addContact('${v.vendor_id}')">+ Add contact</button>
    <div class="sec-h" style="margin:14px 0 6px"><h2 style="font-size:13px">Engagements</h2><div class="rule"></div></div>${engs}
    <div class="row"><button class="btn ghost" onclick="closeModal()">Close</button>
      <button class="btn ghost" onclick="closeModal();openVendorMaster('${v.vendor_id}')">📇 Master record</button>
      <button class="btn" onclick="closeModal();openVendorAttributes('${v.vendor_id}')">🛡 Risk attributes</button></div>`);
}
function addContact(vid){ modal(`<h3>Add contact</h3>
  <div class="field"><label>Name</label><input id="ct_name"></div>
  <div class="grid g2"><div class="field"><label>Email</label><input id="ct_email"></div>
    <div class="field"><label>Designation</label><input id="ct_desig"></div></div>
  <div class="grid g2"><div class="field"><label>Country code</label><input id="ct_cc" placeholder="+44"></div>
    <div class="field"><label>Phone</label><input id="ct_phone"></div></div>
  <div class="field"><label>Country</label><input id="ct_country"></div>
  <div class="field"><label>Mailing address</label><textarea id="ct_addr" rows="2"></textarea></div>
  <label style="display:flex;align-items:center;gap:6px;font-weight:400"><input type="checkbox" id="ct_primary" style="width:auto"> Primary contact (account manager)</label>
  <div class="row"><button class="btn ghost" onclick="closeModal()">Cancel</button>
    <button class="btn" onclick="saveContact('${vid}')">Add</button></div>`); }
async function saveContact(vid){
  try{ await api2("/contacts",{method:"POST",body:JSON.stringify({
    owner_type:"vendor", owner_id:vid, name:val("ct_name"), email:val("ct_email"),
    designation:val("ct_desig"), phone_country_code:val("ct_cc"), phone_number:val("ct_phone"),
    country:val("ct_country"), mailing_address:val("ct_addr"),
    is_primary:document.getElementById("ct_primary").checked})});
    flash("Contact added"); openVendor(vid);
  }catch(e){ flash(e.message); } }
function overrideGroup(vid){ modal(`<h3>Change Group ID</h3>
  <p class="muted" style="margin-bottom:10px">Override the AI-proposed group assignment.</p>
  <div class="field"><label>Group ID</label><input id="og_gid" placeholder="GRP-00001"></div>
  <div class="row"><button class="btn ghost" onclick="closeModal()">Cancel</button>
    <button class="btn" onclick="saveGroup('${vid}')">Save</button></div>`); }
async function saveGroup(vid){
  try{ await api2(`/vendors/${vid}/group`,{method:"POST",body:JSON.stringify({group_id:val("og_gid")})});
    flash("Group updated"); openVendor(vid);
  }catch(e){ flash(e.message); } }

/* ---------- Engagements ---------- */
V.engagements=async()=>{
  const view=document.getElementById("view");
  view.innerHTML=`<div class="top"><div><h1>Engagements</h1><div class="sub">Exposure first · controls second · verdict last</div></div>
    <button class="btn" onclick="newEngagement()">+ New engagement</button></div>
    <div class="field" style="max-width:220px"><label>Filter by stage</label>
      <select id="eg_stage" onchange="V.engagements()">
        <option value="">All stages</option>${["sourcing","triage","inherent","diligence","decision","contract","onboard","monitor","reassess","terminate"].map(s=>`<option ${(window._egStage===s)?"selected":""}>${s}</option>`).join("")}</select></div>
    <div id="et" class="muted">Loading…</div>`;
  try{
    window._vendors = await api2("/vendors");
    const stage=document.getElementById("eg_stage"); if(stage) window._egStage=stage.value;
    const rows = await api2("/engagements");   // v2 registry — one data layer
    const filtered = window._egStage ? rows.filter(e=>e.stage===window._egStage) : rows;
    const vmap = Object.fromEntries(window._vendors.map(v=>[v.vendor_id, v.legal_name]));
    view.querySelector("#et").innerHTML = filtered.length? `<table><tr><th>ID</th><th>Vendor</th><th>Title</th><th>Stage</th><th>Inherent</th><th>Residual</th><th></th></tr>
      ${filtered.map(e=>`<tr class="click" onclick="openEngagementRegister('${esc(e.engagement_id)}')"><td><b>${esc(e.engagement_id)}</b></td>
        <td>${esc(vmap[e.vendor_id]||e.vendor_id||"—")}</td>
        <td>${esc(e.title||"")}</td>
        <td><span class="tag">${esc(e.stage||e.status||"—")}</span></td>
        <td>${e.inherent_band?`<span class="band ${e.inherent_band}">${e.inherent_band}</span>`:"—"}</td>
        <td>${e.residual_band?`<span class="band ${e.residual_band}">${e.residual_band}</span>`:"—"}</td>
        <td style="text-align:right">open →</td></tr>`).join("")}</table>`
      : `<div class="card muted">No engagements. Create one to walk the lifecycle.</div>`;
  }catch(e){ view.querySelector("#et").innerHTML=`<div class="err">${esc(e.message)}</div>`; }
};
function newEngagement(){
  const opts=(window._vendors||[]).map(v=>`<option value="${v.vendor_id}">${esc(v.legal_name)} (${v.vendor_id})</option>`).join("");
  modal(`<h3>New engagement</h3>
    <div class="field"><label>Vendor</label><select id="ne_v">${opts||'<option value="">(create a vendor first)</option>'}</select></div>
    <div class="field"><label>Title</label><input id="ne_t" placeholder="e.g. Card processing service"></div>
    <div class="grid g2"><div class="field"><label>Annual value</label><input id="ne_val" type="number" placeholder="e.g. 250000"></div>
      <div class="field"><label>Currency</label><input id="ne_ccy" value="GBP"></div></div>
    <div class="row"><button class="btn ghost" onclick="closeModal()">Cancel</button>
      <button class="btn" onclick="saveEngagement()">Create</button></div>`); }
async function saveEngagement(){
  const vid=document.getElementById("ne_v").value;
  if(!vid){ flash("Create a vendor first"); return; }
  try{ const r=await api2("/engagements",{method:"POST",body:JSON.stringify({
      vendor_id:vid,
      title:document.getElementById("ne_t").value,
      annual_value:parseFloat(document.getElementById("ne_val").value)||null,
      currency:document.getElementById("ne_ccy").value||null})});
    closeModal(); flash("Engagement created"); openEngagementRegister(r.engagement_id);
  }catch(e){ flash(e.message); } }

async function openEng(id){
  document.querySelectorAll("#nav a").forEach(x=>x.classList.remove("active"));
  const e = await api("/engagements/"+id);
  const view=document.getElementById("view");
  view.innerHTML=`<div class="top"><div><h1>Engagement #${id}</h1>
    <div class="sub">Stage: <span class="tag">${esc(e.stage)}</span></div></div>
    <button class="btn ghost" onclick="V.engagements()">← Back</button></div>
    <div class="grid g3" style="margin-bottom:8px">
      <div class="card stat"><div class="v">${e.inherent_band||"—"}</div><div class="l">Inherent</div></div>
      <div class="card stat"><div class="v">${e.residual_band||"—"}</div><div class="l">Residual</div></div>
      <div class="card stat"><div class="v" style="font-size:18px">${esc(e.decision||"pending")}</div><div class="l">Decision</div></div>
    </div>
    <div class="sec-h"><h2>Assessment workflow</h2><div class="rule"></div></div>
    <div class="grid g2">
      <div class="card"><h3 style="font-size:14px;margin-bottom:8px">1 · Inherent Risk (IRQ)</h3>
        <p class="muted" style="margin-bottom:10px">Score exposure and route the engagement.</p>
        <button class="btn sm" onclick="runIRQ(${id})">Run IRQ</button></div>
      <div class="card"><h3 style="font-size:14px;margin-bottom:8px">2 · Due Diligence (DDQ)</h3>
        <p class="muted" style="margin-bottom:10px">Assess controls → residual band + decision.</p>
        <button class="btn sm" onclick="runDDQ(${id})">Run DDQ</button></div>
      <div class="card"><h3 style="font-size:14px;margin-bottom:8px">3 · Contract (Matt)</h3>
        <p class="muted" style="margin-bottom:10px">Generate tiered minimum terms.</p>
        <button class="btn sm ghost" onclick="genContract(${id})">Generate terms</button></div>
      <div class="card"><h3 style="font-size:14px;margin-bottom:8px">4 · Terminate</h3>
        <p class="muted" style="margin-bottom:10px">Begin the 8-step offboarding.</p>
        <button class="btn sm ghost" onclick="terminate(${id})">Offboard</button></div>
    </div>
    <div class="sec-h"><h2>Engagement actions</h2><div class="rule"></div></div>
    <div class="card">
      <button class="btn sm ghost" onclick="autopilot(${id})">AI autopilot (propose)</button>
      <button class="btn sm ghost" onclick="editEng(${id},'${esc(e.title||"")}')">Edit details</button>
      <button class="btn sm ghost" onclick="cancelEng(${id})">Cancel engagement</button>
    </div>
    <div id="engMsg"></div>`;
}
async function autopilot(id){
  try{ const r=await api(`/engagements/${id}/autopilot`,{method:"POST",
      body:JSON.stringify({answers:{Q1:"No",Q2:"Important"}})});
    document.getElementById("engMsg").innerHTML=`<div class="sec-h"><h2>Autopilot proposal</h2><div class="rule"></div></div>
      <div class="card"><b>${esc(r.status)}</b><br><span class="muted">Proposed inherent band:
      ${esc(r.proposed_inherent.band)} · routing ${esc(r.proposed_routing.route)}. A human must record the decision.</span></div>`;
    flash("Autopilot proposed (human records decision)");
  }catch(e){ flash(e.message); } }
function editEng(id,title){ modal(`<h3>Edit engagement #${id}</h3>
  <div class="field"><label>Title</label><input id="ee_t" value="${esc(title)}"></div>
  <div class="field"><label>Business contact email</label><input id="ee_bc"></div>
  <div class="row"><button class="btn ghost" onclick="closeModal()">Cancel</button>
    <button class="btn" onclick="saveEditEng(${id})">Save</button></div>`); }
async function saveEditEng(id){
  const b={title:val("ee_t")}; const bc=val("ee_bc"); if(bc) b.business_contact_email=bc;
  try{ await api("/engagements/"+id,{method:"PATCH",body:JSON.stringify(b)});
    closeModal(); flash("Engagement updated"); openEng(id);
  }catch(e){ flash(e.message); } }
async function cancelEng(id){
  try{ await api("/engagements/"+id,{method:"DELETE"}); flash("Engagement cancelled"); V.engagements();
  }catch(e){ flash(e.message); } }
function runIRQ(id){ modal(`<h3>Inherent Risk Questionnaire</h3>
  <div class="field"><label>Regulated data / criticality</label>
    <select id="q2"><option>Standard</option><option>Important</option><option selected>Mission-critical</option></select></div>
  <div class="field"><label>Data types</label>
    <select id="q3"><option>None</option><option selected>Payment Card</option><option>Personal/PII</option></select></div>
  <div class="field"><label>Cross-border data?</label><select id="q5"><option>No</option><option selected>Yes</option></select></div>
  <div class="field"><label>Record volume</label><select id="q4"><option>&lt;10,000</option><option selected>&gt;1,000,000</option></select></div>
  <div class="row"><button class="btn ghost" onclick="closeModal()">Cancel</button>
    <button class="btn" onclick="submitIRQ(${id})">Score</button></div>`); }
async function submitIRQ(id){
  const a={Q1:"No",Q2:val("q2"),Q3:[val("q3")],Q5:val("q5"),Q4:val("q4")};
  try{ const r=await api(`/engagements/${id}/irq`,{method:"POST",body:JSON.stringify({answers:a})});
    closeModal(); flash(`IRQ: ${r.inherent_band} · ${r.routing.route}`); openEng(id);
  }catch(e){ flash(e.message); } }
function runDDQ(id){ modal(`<h3>Due Diligence Questionnaire</h3>
  <p class="muted" style="margin-bottom:10px">Control outcomes drive the residual band. A marginal critical control forces HIGH.</p>
  <div class="field"><label>Encryption control (IS2 — critical)</label>
    <select id="is2"><option>SATISFIED</option><option selected>MARGINAL</option><option>FAILED</option></select></div>
  <div class="field"><label>Access management (IS1)</label>
    <select id="is1"><option selected>SATISFIED</option><option>MARGINAL</option></select></div>
  <div class="row"><button class="btn ghost" onclick="closeModal()">Cancel</button>
    <button class="btn" onclick="submitDDQ(${id})">Score residual</button></div>`); }
async function submitDDQ(id){
  const a={IS2:val("is2"),IS1:val("is1")};
  try{ const r=await api(`/engagements/${id}/ddq`,{method:"POST",body:JSON.stringify({answers:a})});
    closeModal(); flash(`Residual ${r.residual_band}: ${r.decision.text}`); openEng(id);
  }catch(e){ flash(e.message); } }
async function genContract(id){ try{ const r=await api(`/engagements/${id}/contract`,{method:"POST",body:"{}"});
  flash(`Contract: ${r.terms.length} terms for ${r.tier}`); openEng(id);}catch(e){flash(e.message);} }
async function terminate(id){ try{ const r=await api(`/engagements/${id}/terminate`,{method:"POST",body:"{}"});
  flash(`Offboarding started · ${r.offboarding_steps} steps`); openEng(id);}catch(e){flash(e.message);} }
function val(id){return document.getElementById(id).value}

/* ---------- Findings ---------- */
V.findings=async()=>{
  const view=document.getElementById("view");
  view.innerHTML=`<div class="top"><div><h1>Action Plan</h1><div class="sub">Findings to closure</div></div>
    <button class="btn" onclick="newFinding()">+ Raise finding</button></div><div id="ft" class="muted">Loading…</div>`;
  try{ const d=await api("/cap");
    view.querySelector("#ft").innerHTML=`<div class="grid g3" style="margin-bottom:14px">
        <div class="card stat"><div class="v">${d.open_actions}</div><div class="l">Open actions</div></div>
        ${["critical","high","medium"].map(s=>`<div class="card stat"><div class="v">${(d.by_severity||{})[s]||0}</div><div class="l">${s}</div></div>`).join("")}</div>
      ${d.items.length?`<table><tr><th>ID</th><th>Title</th><th>Severity</th><th>Status</th><th></th></tr>
      ${d.items.map(f=>`<tr><td>#${f.finding_id}</td><td>${esc(f.title)}</td><td>${esc(f.severity)}</td>
        <td><span class="tag">${esc(f.status)}</span></td>
        <td style="text-align:right"><button class="btn sm ghost" onclick="advance(${f.finding_id})">Advance</button></td></tr>`).join("")}</table>`
      :`<div class="card muted">No open findings.</div>`}`;
  }catch(e){ view.querySelector("#ft").innerHTML=`<div class="err">${esc(e.message)}</div>`; }
};
function newFinding(){ modal(`<h3>Raise finding</h3>
  <div class="field"><label>Title</label><input id="f_t"></div>
  <div class="field"><label>Severity</label><select id="f_s"><option>critical</option><option>high</option><option selected>medium</option><option>low</option></select></div>
  <div class="row"><button class="btn ghost" onclick="closeModal()">Cancel</button>
    <button class="btn" onclick="saveFinding()">Raise</button></div>`); }
async function saveFinding(){ try{ await api("/findings",{method:"POST",body:JSON.stringify({
    title:val("f_t"),severity:val("f_s")})}); closeModal(); flash("Finding raised"); V.findings();
  }catch(e){flash(e.message);} }
async function advance(id){ try{ const r=await api(`/findings/${id}/advance`,{method:"POST",body:"{}"});
  flash("Status: "+r.status); V.findings(); }catch(e){flash(e.message);} }

/* ---------- Monitoring ---------- */
V.monitoring=async()=>{
  const view=document.getElementById("view");
  view.innerHTML=`<div class="top"><div><h1>Monitoring</h1><div class="sub">Financial & reputation sweeps</div></div></div>
    <div class="card"><p class="muted" style="margin-bottom:10px">Run a financial sweep on a vendor. ALERT/CRITICAL auto-raises a reassessment and notifies.</p>
    <div class="grid g2"><div class="field"><label>Vendor</label><select id="mv">${(await api("/vendors")).map(v=>`<option value="${v.vendor_id}">${esc(v.name)}</option>`).join("")}</select></div>
    <div class="field"><label>Financial health (sim)</label><select id="mh"><option value="weak">Weak / distressed</option><option value="ok">Healthy</option></select></div></div>
    <button class="btn" onclick="sweep()">Run sweep</button></div><div id="ms"></div>`;
};
async function sweep(){
  const v=parseInt(val("mv")); const weak=val("mh")==="weak";
  const payload=weak?{current_ratio:0.3,debt_equity:4,net_margin:-0.2}:{current_ratio:2,debt_equity:0.5,net_margin:0.2};
  try{ const r=await api("/monitoring/sweep",{method:"POST",body:JSON.stringify({vendor_id:v,payload})});
    document.getElementById("ms").innerHTML=`<div class="sec-h"><h2>Result</h2><div class="rule"></div></div>
      <div class="card"><span class="band ${r.status==='OK'?'LOW':r.status==='ALERT'?'ELEVATED':'HIGH'}">${r.status}</span></div>`;
    flash("Sweep: "+r.status);
  }catch(e){flash(e.message);} }

/* ---------- Intelligence ---------- */
V.intel=async()=>{
  const view=document.getElementById("view");
  view.innerHTML=`<div class="top"><div><h1>Board Intelligence</h1>
      <div class="sub">AI horizon scan · external PESTLE × internal estate · predictive oversight for the Board</div></div>
    <div style="display:flex;gap:8px">
      <button class="btn" id="btnStart" onclick="runBoardIntel()">▶ Start analysis</button>
      <button class="btn ghost" id="btnGen" onclick="runBoardIntel()">✦ Generate insights</button>
    </div></div>
    <div class="intel-shell">
      <div class="intel-console" id="intelLog"><div class="il-line muted">Idle. Press <b>Start analysis</b> — the AI will scan the external horizon, ingest the internal estate, correlate, predict, and brief the Board.</div></div>
      <div class="intel-canvas" id="intelCanvas">
        <div class="intel-empty">
          <div class="ie-mark">✦</div>
          <div>Board-grade intelligence will render here.</div>
          <div class="muted" style="font-size:12px;margin-top:6px">Graphical presentation, board observations and predictive analysis — generated by AI from every available data point.</div>
        </div>
      </div>
    </div>`;
};
function _sleep(ms){ return new Promise(r=>setTimeout(r,ms)); }
function _ilog(html, cls){ const l=document.getElementById("intelLog"); if(!l) return;
  const d=document.createElement("div"); d.className="il-line "+(cls||""); d.innerHTML=html; l.appendChild(d); l.scrollTop=l.scrollHeight; }
async function runBoardIntel(){
  const bs=document.getElementById("btnStart"), bg=document.getElementById("btnGen");
  if(bs) bs.disabled=true; if(bg) bg.disabled=true;
  const log=document.getElementById("intelLog"); if(log) log.innerHTML="";
  const canvas=document.getElementById("intelCanvas");
  if(canvas) canvas.innerHTML=`<div class="intel-empty"><div class="ie-mark spin">✦</div><div class="muted">Analysing…</div></div>`;
  const phases=[
    ["Initialising board-intelligence engine…",260],
    ["Scanning external horizon — <b>Political · Regulatory · Environmental · Social · Technological</b>…",520],
    ["Ingesting internal estate — vendors, engagements, spend, expiry &amp; renewal calendar, delivery geography, findings, concentration…",560],
    ["Correlating external signals against internal exposure…",520],
    ["Running predictive models — renewal cliff · assurance-lapse · concentration drift · findings burn-down…",520],
    ["Drafting board observations and specific management actions…",460],
    ["Composing graphical presentation…",360],
  ];
  for(const [t,d] of phases){ _ilog(t); await _sleep(d); }
  try{
    const r=await api2("/intelligence/board",{method:"POST",body:"{}"});
    _ilog(`Analysis complete · <b>${r.observations.length}</b> board matters · <b>${r.predictions.length}</b> predictive calls · engine: ${esc(r.engine)}`,"ok");
    renderBoardIntel(r);
  }catch(e){ _ilog("Error: "+esc(e.message),"err"); if(canvas) canvas.innerHTML=`<div class="intel-empty"><div class="muted">${esc(e.message)}</div></div>`; }
  if(bs){ bs.disabled=false; bs.textContent="▶ Re-run analysis"; } if(bg) bg.disabled=false;
}
const SEVCOL={Critical:"#b3261e",High:"#d9534f",Elevated:"#e0913a",Moderate:"#2E6A4F"};
const FACCOL={Political:"#5C3A6B",Regulatory:"#1E3A5C",Environmental:"#3D6B3D",Social:"#8A2E3B",Technological:"#1A4D3C"};
function _barRow(label,val,max,col,suffix){ const w=Math.max(2,Math.round(100*val/(max||1)));
  return `<div class="bar-row"><div class="bar-lab">${esc(label)}</div><div class="bar-track"><div class="bar-fill" style="width:${w}%;background:${col}"></div></div><div class="bar-val">${esc(String(val))}${suffix||""}</div></div>`; }
function _miniChart(title,series,col,suffix){ const max=Math.max(1,...series.map(p=>p.value));
  return `<div class="ic-card"><div class="ic-title">${esc(title)}</div>${series.map(p=>_barRow(p.label,p.value,max,col,suffix)).join("")}</div>`; }
function renderBoardIntel(r){
  const c=document.getElementById("intelCanvas"); if(!c) return;
  const iv=r.internal;
  // executive briefing
  const brief = r.executive_briefing || r.headline;
  let html=`<div class="ib-brief"><div class="ib-kicker">Executive briefing · ${esc(r.generated)} · ${r.engine==='llm'?'live AI':'AI engine'}</div>
    <p>${esc(brief)}</p>
    <div class="ib-metrics">
      ${[["Vendors",iv.vendors],["Critical",iv.critical_vendors],["Engagements",iv.engagements],
         ["Spend","£"+iv.total_spend_m+"m"],["Top hub",iv.top_hub_share+"%"],["Open findings",iv.open_findings],
         ["Certs expiring (crit)",iv.certs_expiring_90_critical],["Renewals ≤90d",iv.renewals_90d]]
        .map(([k,v])=>`<div><div class="ibm-v">${esc(String(v))}</div><div class="ibm-k">${esc(k)}</div></div>`).join("")}
    </div></div>`;
  // PESTLE horizon
  html+=`<div class="sec-h" style="margin-top:18px"><h2>External horizon — PESTLE exposure</h2><div class="rule"></div></div>
    <div class="ic-card">${r.external.map(e=>{const col=SEVCOL[e.severity]||"#2E6A4F";
      return `<div class="pestle-row"><div class="pe-fac" style="color:${FACCOL[e.factor]}">${esc(e.factor)}</div>
        <div class="bar-track"><div class="bar-fill" style="width:${e.score}%;background:${col}"></div></div>
        <div class="pe-sev" style="color:${col}">${e.score} · ${esc(e.severity)}</div>
        <div class="pe-head muted">${esc(e.headline)}</div></div>`;}).join("")}</div>`;
  // graphical presentation grid
  html+=`<div class="sec-h" style="margin-top:18px"><h2>Graphical presentation</h2><div class="rule"></div></div>
    <div class="ic-grid">
      ${_miniChart("Residual risk distribution",r.charts.residual,"#1A4D3C")}
      ${_miniChart("Delivery geography (engagements)",r.charts.geography,"#1E3A5C")}
      ${_miniChart("Assurance expiry calendar",r.charts.expiry,"#d9534f")}
      ${_miniChart("Spend by residual band (£m)",r.charts.spend_by_band,"#B8862B")}
    </div>`;
  // board observations
  html+=`<div class="sec-h" style="margin-top:18px"><h2>Board observations &amp; management actions</h2><div class="rule"></div></div>
    <div class="obs-list">${r.observations.map(o=>{const col=SEVCOL[o.severity]||"#2E6A4F";
      return `<div class="obs-card" style="border-left-color:${col}">
        <div class="obs-top"><span class="obs-sev" style="background:${col}">${esc(o.severity)}</span>
          <span class="obs-fac" style="color:${FACCOL[o.factor]};border-color:${FACCOL[o.factor]}">${esc(o.factor)}</span>
          <span class="obs-hz muted">Horizon: ${esc(o.horizon)}</span></div>
        <h3>${esc(o.title)}</h3>
        <div class="obs-ev"><b>Evidence.</b> ${esc(o.evidence)}</div>
        <div class="obs-sw"><b>So what.</b> ${esc(o.so_what)}</div>
        <div class="obs-act"><span class="oa-tag">Board → Management</span> ${esc(o.board_action)}</div>
      </div>`;}).join("")}</div>`;
  // predictive analysis
  if((r.predictions||[]).length){
    html+=`<div class="sec-h" style="margin-top:18px"><h2>Predictive analysis</h2><div class="rule"></div></div>
      <div class="pred-grid">${r.predictions.map(p=>`<div class="pred-card">
        <div class="pred-top"><span class="pred-metric">${esc(p.metric)}</span><span class="pred-conf">${esc(p.confidence)} confidence</span></div>
        <h4>${esc(p.title)}</h4><p class="muted">${esc(p.detail)}</p></div>`).join("")}</div>`;
  }
  c.innerHTML=html;
}

/* ---------- Reports ---------- */
V.reports=async()=>{
  const view=document.getElementById("view");
  view.innerHTML=`<div class="top"><div><h1>Reports & Export</h1><div class="sub">Registers and audit export</div></div></div>
    <div class="grid g2">
      <div class="card"><h3 style="font-size:14px;margin-bottom:6px">Vendor risk register</h3>
        <p class="muted" style="margin-bottom:10px">All vendors and engagements with bands and decisions.</p>
        <button class="btn sm" onclick="dl('/reports/register.csv','register.csv')">Download CSV</button></div>
      <div class="card"><h3 style="font-size:14px;margin-bottom:6px">Audit trail export</h3>
        <p class="muted" style="margin-bottom:10px">Full hash-chained audit log.</p>
        <button class="btn sm" onclick="dl('/audit/export.csv','audit.csv')">Download CSV</button></div>
    </div>`;
};
async function dl(path,fname){
  try{ const h={}; if(tok()) h["Authorization"]="Bearer "+tok();
    const r=await fetch(API+path,{headers:h}); const t=await r.text();
    const b=new Blob([t],{type:"text/csv"}); const a=document.createElement("a");
    a.href=URL.createObjectURL(b); a.download=fname; a.click(); flash("Downloaded "+fname);
  }catch(e){ flash(e.message); } }

/* ---------- Notifications ---------- */
V.notifications=async()=>{
  const view=document.getElementById("view");
  view.innerHTML=`<div class="top"><div><h1>Notifications</h1><div class="sub">Stage alerts and issues</div></div>
    <button class="btn ghost" onclick="readAll()">Mark all read</button></div><div id="nt" class="muted">Loading…</div>`;
  try{ const d=await api("/notifications");
    view.querySelector("#nt").innerHTML=`<p class="muted" style="margin-bottom:10px">${d.unread} unread</p>
      ${d.items.length?`<table><tr><th>Event</th><th>Audience</th><th>Read</th></tr>
      ${d.items.map(n=>`<tr><td>${esc(n.event)}</td><td><span class="tag">${esc(n.audience)}</span></td>
        <td>${n.read?'<span class="muted">read</span>':`<button class="btn sm ghost" onclick="readOne(${n.id})">mark read</button>`}</td></tr>`).join("")}</table>`
      :`<div class="card muted">No notifications.</div>`}`;
  }catch(e){ view.querySelector("#nt").innerHTML=`<div class="err">${esc(e.message)}</div>`; }
};
async function readAll(){ try{ await api("/notifications/read-all",{method:"POST",body:"{}"}); flash("All marked read"); V.notifications(); }catch(e){flash(e.message);} }
async function readOne(id){ try{ await api(`/notifications/${id}/read`,{method:"POST",body:"{}"}); V.notifications(); }catch(e){flash(e.message);} }

/* ---------- Admin ---------- */
V.admin=async()=>{
  const view=document.getElementById("view");
  view.innerHTML=`<div class="top"><div><h1>Administration</h1><div class="sub">Users, roles, webhooks & email</div></div>
    <button class="btn" onclick="newUser()">+ New user</button></div>
    <div class="sec-h"><h2>Users</h2><div class="rule"></div></div><div id="ut" class="muted">Loading…</div>
    <div class="sec-h"><h2>Roles &amp; permissions</h2><div class="rule"></div></div><div id="rt" class="muted">Loading…</div>
    <div class="sec-h"><h2>Webhooks</h2><div class="rule"></div></div>
    <div class="card" style="margin-bottom:8px"><div class="grid g2">
      <div class="field"><label>URL</label><input id="wh_url" placeholder="https://hooks.example/bro"></div>
      <div class="field"><label>Event</label><input id="wh_ev" value="*"></div></div>
      <button class="btn sm" onclick="addWebhook()">Add webhook</button></div>
    <div id="wt" class="muted">Loading…</div>
    <div class="sec-h"><h2>AI integration</h2><div class="rule"></div></div>
    <div id="ai_status" class="muted">Loading…</div>
    <div class="sec-h"><h2>Email</h2><div class="rule"></div></div>
    <div class="card" style="margin-bottom:8px"><div class="grid g3">
      <div class="field"><label>To</label><input id="em_to" placeholder="vendor@x.com"></div>
      <div class="field"><label>Subject</label><input id="em_sub"></div>
      <div class="field"><label>Body</label><input id="em_body"></div></div>
      <button class="btn sm" onclick="sendEmail()">Send (SMTP or simulation)</button></div>
    <div id="eo" class="muted">Loading…</div>`;
  try{
    window._roles = await api("/admin/roles");
    const us=await api("/admin/users");
    view.querySelector("#ut").innerHTML=`<table><tr><th>Username</th><th>Name</th><th>Role</th><th>Active</th><th></th></tr>
      ${us.map(x=>`<tr><td><b>${esc(x.username)}</b></td><td>${esc(x.full_name||"")}</td>
        <td><span class="tag">${esc(x.role)}</span></td><td>${x.is_active?"✓":"—"}</td>
        <td style="text-align:right">
          <button class="btn sm ghost" onclick="editUser(${x.id},'${esc(x.role)}')">Edit role</button>
          ${x.username==="admin"?"":`<button class="btn sm ghost" onclick="deactivateUser(${x.id})">Deactivate</button>`}
        </td></tr>`).join("")}</table>`;
    view.querySelector("#rt").innerHTML=`<table><tr><th>Role</th><th>Permissions</th><th></th></tr>
      ${window._roles.map(r=>`<tr><td><b>${esc(r.label)}</b></td><td class="muted">${r.permissions.length} permissions</td>
        <td style="text-align:right"><button class="btn sm ghost" onclick="editRolePerms('${r.key}','${esc(r.label)}')">Edit permissions</button></td></tr>`).join("")}</table>`;
  }catch(e){ view.querySelector("#ut").innerHTML=`<div class="err">${esc(e.message)}</div>`; }
  try{
    const ws=await api("/admin/webhooks");
    view.querySelector("#wt").innerHTML = ws.length?`<table><tr><th>URL</th><th>Event</th><th>Active</th><th></th></tr>
      ${ws.map(w=>`<tr><td>${esc(w.url)}</td><td><span class="tag">${esc(w.event)}</span></td><td>${w.active?"✓":"—"}</td>
        <td style="text-align:right"><button class="btn sm ghost" onclick="delWebhook(${w.id})">Delete</button></td></tr>`).join("")}</table>`
      :`<div class="card muted">No webhooks configured.</div>`;
  }catch(e){ view.querySelector("#wt").innerHTML=`<div class="err">${esc(e.message)}</div>`; }
  try{
    const ob=await api("/email/outbox");
    view.querySelector("#eo").innerHTML = ob.length?`<table><tr><th>To</th><th>Subject</th><th>Mode</th></tr>
      ${ob.map(m=>`<tr><td>${esc(m.to)}</td><td>${esc(m.subject)}</td><td>${m.sent?'<span class="tag">sent</span>':'<span class="tag" style="background:#eee4d4;color:var(--amber)">simulation</span>'}</td></tr>`).join("")}</table>`
      :`<div class="card muted">Outbox empty.</div>`;
  }catch(e){ view.querySelector("#eo").innerHTML=`<div class="err">${esc(e.message)}</div>`; }
  try{
    const ai=await api("/ai/status");
    const badge=ai.enabled?`<span class="tag" style="background:#e3efe6;color:var(--moss)">ENABLED · ${esc(ai.provider)} · ${esc(ai.model||"")}</span>`
      :`<span class="tag" style="background:#f6e2de;color:var(--rust)">DISABLED · deterministic-local</span>`;
    document.getElementById("ai_status").innerHTML=`<div class="card">
      <div style="margin-bottom:8px">${badge}</div>
      <table><tr><th>Provider</th><th>Key present?</th></tr>
        <tr><td>Claude (Anthropic)</td><td>${ai.claude_key_present?'<span class="chk" style="color:var(--moss)">✓ ANTHROPIC_API_KEY set</span>':'<span class="muted">not set</span>'}</td></tr>
        <tr><td>ChatGPT (OpenAI)</td><td>${ai.openai_key_present?'<span class="chk" style="color:var(--moss)">✓ OPENAI_API_KEY set</span>':'<span class="muted">not set</span>'}</td></tr></table>
      <p class="muted" style="margin-top:10px">Keys are read from environment variables, never stored in the app. Set <code>ANTHROPIC_API_KEY</code> or <code>OPENAI_API_KEY</code> (and optionally <code>BRO_LLM_PROVIDER</code>) on the server, then restart. When enabled, AI Assessment agents and intelligence narratives use the live provider; otherwise the tested deterministic-local path runs.</p>
    </div>`;
  }catch(e){ document.getElementById("ai_status").innerHTML=`<div class="muted" style="font-size:12px">AI status unavailable.</div>`; }
};
async function newUser(){
  const roles=window._roles||await api("/admin/roles");
  modal(`<h3>New user</h3>
    <div class="field"><label>Username</label><input id="u_un"></div>
    <div class="field"><label>Full name</label><input id="u_fn"></div>
    <div class="field"><label>Password</label><input id="u_pw" type="password"></div>
    <div class="field"><label>Role</label><select id="u_role">${roles.map(r=>`<option value="${r.key}">${esc(r.label)}</option>`).join("")}</select></div>
    <div class="row"><button class="btn ghost" onclick="closeModal()">Cancel</button>
      <button class="btn" onclick="saveUser()">Create</button></div>`); }
async function saveUser(){
  try{ await api("/admin/users",{method:"POST",body:JSON.stringify({
    username:val("u_un"),full_name:val("u_fn"),password:val("u_pw"),role_key:val("u_role")})});
    closeModal(); flash("User created"); V.admin();
  }catch(e){ flash(e.message); } }
function editUser(id,current){
  const roles=window._roles||[];
  modal(`<h3>Edit user role</h3>
    <div class="field"><label>Role</label><select id="eu_role">
      ${roles.map(r=>`<option value="${r.key}" ${r.key===current?"selected":""}>${esc(r.label)}</option>`).join("")}</select></div>
    <div class="row"><button class="btn ghost" onclick="closeModal()">Cancel</button>
      <button class="btn" onclick="saveUserRole(${id})">Save</button></div>`); }
async function saveUserRole(id){
  try{ await api("/admin/users/"+id,{method:"PATCH",body:JSON.stringify({role_key:val("eu_role")})});
    closeModal(); flash("User role updated"); V.admin();
  }catch(e){ flash(e.message); } }
async function deactivateUser(id){
  try{ await api("/admin/users/"+id,{method:"DELETE"}); flash("User deactivated"); V.admin();
  }catch(e){ flash(e.message); } }
async function editRolePerms(key,label){
  const all=await api("/admin/permissions");
  const role=(window._roles||[]).find(r=>r.key===key);
  const have=new Set(role?role.permissions:[]);
  const byCat={}; all.forEach(p=>{(byCat[p.category]=byCat[p.category]||[]).push(p)});
  const body=Object.entries(byCat).map(([cat,ps])=>`<div style="margin-bottom:8px"><b style="font-size:12px">${esc(cat)}</b><br>
    ${ps.map(p=>`<label style="display:inline-flex;align-items:center;gap:5px;margin:3px 10px 3px 0;font-weight:400">
      <input type="checkbox" style="width:auto" value="${p.key}" ${have.has(p.key)?"checked":""}> ${esc(p.key)}</label>`).join("")}</div>`).join("");
  modal(`<h3>Permissions — ${esc(label)}</h3><div style="max-height:50vh;overflow:auto">${body}</div>
    <div class="row"><button class="btn ghost" onclick="closeModal()">Cancel</button>
      <button class="btn" onclick="saveRolePerms('${key}')">Save permissions</button></div>`); }
async function saveRolePerms(key){
  const keys=[...document.querySelectorAll('.modal input[type=checkbox]:checked')].map(c=>c.value);
  try{ await api(`/admin/roles/${key}/permissions`,{method:"PUT",body:JSON.stringify({permission_keys:keys})});
    closeModal(); flash("Permissions updated"); V.admin();
  }catch(e){ flash(e.message); } }
async function addWebhook(){
  try{ await api("/admin/webhooks",{method:"POST",body:JSON.stringify({url:val("wh_url"),event:val("wh_ev")})});
    flash("Webhook added"); V.admin();
  }catch(e){ flash(e.message); } }
async function delWebhook(id){
  try{ await api("/admin/webhooks/"+id,{method:"DELETE"}); flash("Webhook deleted"); V.admin();
  }catch(e){ flash(e.message); } }
async function sendEmail(){
  try{ const r=await api("/email/send",{method:"POST",body:JSON.stringify({
    to_addr:val("em_to"),subject:val("em_sub"),body:val("em_body")})});
    flash(`Email ${r.mode==='smtp'?'sent':'queued (simulation)'}`); V.admin();
  }catch(e){ flash(e.message); } }

/* ---------- Lifecycle (certs, evidence, reassessment, 4th parties, acceptances) ---------- */
V.lifecycle=async()=>{
  const view=document.getElementById("view");
  window._vendors = await api("/vendors").catch(()=>[]);
  view.innerHTML=`<div class="top"><div><h1>Lifecycle</h1><div class="sub">Evidence, reassessment, 4th parties</div></div></div>
    <div class="sec-h"><h2>Evidence expiring (next 90 days)</h2><div class="rule"></div></div><div id="lc_ev" class="muted">Loading…</div>
    <div class="sec-h"><h2>4th-party concentration</h2><div class="rule"></div></div><div id="lc_4p" class="muted">Loading…</div>
    <div class="sec-h"><h2>Reassessments</h2><div class="rule"></div></div>
    <div class="card"><button class="btn sm" onclick="runDue()">Run due (tier cadence)</button></div>
    <div class="sec-h"><h2>Certifications</h2><div class="rule"></div></div>
    <div class="card"><div class="grid g3">
      <div class="field"><label>Vendor</label><select id="ct_v">${(window._vendors||[]).map(v=>`<option value="${v.vendor_id}">${esc(v.name)}</option>`).join("")||'<option>(no vendors)</option>'}</select></div>
      <div class="field"><label>Certification</label><input id="ct_n" placeholder="ISO 27001"></div>
      <div class="field"><label>Valid until</label><input id="ct_d" type="date"></div></div>
      <button class="btn sm" onclick="addCert()">Add certification</button></div>`;
  try{
    const ev=await api("/evidence/expiring");
    view.querySelector("#lc_ev").innerHTML = ev.length?`<table><tr><th>Document</th><th>Next validation</th><th></th></tr>
      ${ev.map(d=>`<tr><td>${esc(d.name)}</td><td>${esc(d.next_validation||"")}</td>
        <td style="text-align:right"><button class="btn sm ghost" onclick="chase(${d.document_id})">Chase renewal</button></td></tr>`).join("")}</table>`
      :`<div class="card muted">Nothing expiring soon.</div>`;
  }catch(e){ view.querySelector("#lc_ev").innerHTML=`<div class="err">${esc(e.message)}</div>`; }
  try{
    const fp=await api("/fourth-parties/concentration");
    view.querySelector("#lc_4p").innerHTML = fp.length?`<table><tr><th>4th party</th><th>Vendor</th></tr>
      ${fp.map(f=>`<tr><td><b>${esc(f.name)}</b></td><td>#${f.vendor_id}</td></tr>`).join("")}</table>`
      :`<div class="card muted">No concentration flags.</div>`;
  }catch(e){ view.querySelector("#lc_4p").innerHTML=`<div class="err">${esc(e.message)}</div>`; }
};
async function chase(id){ try{ const r=await api(`/evidence/${id}/chase`,{method:"POST",body:"{}"});
  flash(`Renewal chased (${r.mode})`); }catch(e){flash(e.message);} }
async function runDue(){ try{ const r=await api("/reassessments/run-due",{method:"POST",body:"{}"});
  flash(`${r.created} reassessment(s) created`); }catch(e){flash(e.message);} }
async function addCert(){
  const d=val("ct_d");
  const body={vendor_id:parseInt(val("ct_v")),name:val("ct_n")};
  if(d) body.valid_until=d+"T00:00:00";
  try{ await api("/certifications",{method:"POST",body:JSON.stringify(body)});
    flash("Certification added");
  }catch(e){ flash(e.message); } }

/* ---------- Review Queue (Assessor) ---------- */
V.review=async()=>{
  const view=document.getElementById("view");
  view.innerHTML=`<div class="top"><div><h1>Review Queue</h1><div class="sub">HIGH / ELEVATED engagements awaiting Assessor sign-off</div></div></div><div id="rq" class="muted">Loading…</div>`;
  try{ const q=await api("/review-queue");
    view.querySelector("#rq").innerHTML = q.length?`<table><tr><th>ID</th><th>Title</th><th>Residual</th><th>Decision</th><th></th></tr>
      ${q.map(e=>`<tr><td>#${e.engagement_id}</td><td>${esc(e.title)}</td>
        <td><span class="band ${e.residual_band}">${e.residual_band}</span></td><td>${esc(e.decision||"—")}</td>
        <td style="text-align:right">
          <button class="btn sm" onclick="signoff(${e.engagement_id},'approved')">Sign off</button>
          <button class="btn sm ghost" onclick="signoff(${e.engagement_id},'returned')">Return</button>
          <button class="btn sm ghost" onclick="overrideEng(${e.engagement_id})">Override</button>
        </td></tr>`).join("")}</table>`
      :`<div class="card muted">Nothing awaiting review.</div>`;
  }catch(e){ view.querySelector("#rq").innerHTML=`<div class="err">${esc(e.message)}</div>`; }
};
async function signoff(id,decision){ try{ await api(`/engagements/${id}/signoff`,{method:"POST",
    body:JSON.stringify({decision})}); flash(`Engagement ${decision}`); V.review(); }catch(e){flash(e.message);} }
function overrideEng(id){ modal(`<h3>Override decision — #${id}</h3>
  <p class="muted" style="margin-bottom:10px">Requires justification and a second approver (human-only).</p>
  <div class="field"><label>New band</label><select id="ov_b"><option>LOW</option><option>MODERATE</option><option>ELEVATED</option><option>HIGH</option></select></div>
  <div class="field"><label>Justification</label><textarea id="ov_r" rows="2"></textarea></div>
  <div class="field"><label>Second approver</label><input id="ov_a"></div>
  <div class="row"><button class="btn ghost" onclick="closeModal()">Cancel</button>
    <button class="btn amber" onclick="saveOverride(${id})">Apply override</button></div>`); }
async function saveOverride(id){ try{ await api(`/engagements/${id}/override`,{method:"POST",
    body:JSON.stringify({band:val("ov_b"),reason:val("ov_r"),second_approver:val("ov_a")})});
  closeModal(); flash("Override applied"); V.review(); }catch(e){flash(e.message);} }

/* ---------- Governance (BIA, incidents, CAP, methodology, procurement) ---------- */
V.governance=async()=>{
  const view=document.getElementById("view");
  view.innerHTML=`<div class="top"><div><h1>Governance</h1><div class="sub">CAP · methodology · incidents · procurement</div></div></div>
    <div class="sec-h"><h2>Corrective Action Plan</h2><div class="rule"></div></div><div id="gv_cap" class="muted">Loading…</div>
    <div class="sec-h"><h2>Methodology version</h2><div class="rule"></div></div>
    <div class="card"><div class="field" style="max-width:200px"><label>Version label</label><input id="gv_ver" placeholder="v2.1"></div>
      <button class="btn sm" onclick="setMeth()">Record version</button></div>
    <div class="sec-h"><h2>Procurement PO intake</h2><div class="rule"></div></div>
    <div class="card"><div class="grid g2"><div class="field"><label>Vendor name</label><input id="gv_po_v"></div>
      <div class="field"><label>Amount</label><input id="gv_po_a" type="number" value="50000"></div></div>
      <button class="btn sm" onclick="poIntake()">Ingest PO (straight-through)</button></div>`;
  try{ const cap=await api("/cap");
    view.querySelector("#gv_cap").innerHTML=`<div class="card"><b>${cap.open_actions}</b> open action(s).
      ${Object.entries(cap.by_severity||{}).map(([k,v])=>`<span class="tag" style="margin:3px">${esc(k)}: ${v}</span>`).join("")}</div>`;
  }catch(e){ view.querySelector("#gv_cap").innerHTML=`<div class="err">${esc(e.message)}</div>`; }
};
async function setMeth(){ try{ await api("/methodology/version",{method:"POST",body:JSON.stringify({version:val("gv_ver")})});
  flash("Methodology version recorded"); }catch(e){flash(e.message);} }
async function poIntake(){ try{ const r=await api("/procurement/po",{method:"POST",
    body:JSON.stringify({vendor_name:val("gv_po_v"),amount:parseFloat(val("gv_po_a"))})});
  flash(`PO ingested → engagement #${r.engagement_id}`); }catch(e){flash(e.message);} }

/* ---------- Settings (profile + password) ---------- */
V.settings=async()=>{
  const view=document.getElementById("view");
  const me=await api("/me");
  view.innerHTML=`<div class="top"><div><h1>Settings</h1><div class="sub">Your profile and password</div></div></div>
    <div class="grid g2">
      <div class="card"><h3 style="font-size:14px;margin-bottom:10px">Profile</h3>
        <div class="field"><label>Full name</label><input id="st_fn" value="${esc(me.full_name||"")}"></div>
        <div class="field"><label>Email</label><input id="st_em" value="${esc(me.email||"")}"></div>
        <button class="btn sm" onclick="saveProfile()">Save profile</button></div>
      <div class="card"><h3 style="font-size:14px;margin-bottom:10px">Change password</h3>
        <div class="field"><label>Current password</label><input id="st_cp" type="password"></div>
        <div class="field"><label>New password</label><input id="st_np" type="password"></div>
        <button class="btn sm" onclick="changePw()">Update password</button></div>
    </div>`;
};
async function saveProfile(){ try{ await api("/me",{method:"PATCH",body:JSON.stringify({full_name:val("st_fn"),email:val("st_em")})});
  flash("Profile saved"); }catch(e){flash(e.message);} }
async function changePw(){ try{ await api("/me/password",{method:"POST",
    body:JSON.stringify({current_password:val("st_cp"),new_password:val("st_np")})});
  flash("Password updated"); val("st_cp"); }catch(e){flash(e.message);} }

/* ---------- AI Assessment (conversational multi-agent) ---------- */
let _reg=null, _sid=null;
const AGENT_COLORS={bro:"#0F1419",scope:"#335577",infosec:"#1A4D3C",resilience:"#7A4F2E",
  privacy:"#5C3A6B",reputation:"#8A2E3B",compliance:"#2E4A5C",physical:"#4A4A4A",esg:"#3D6B3D",researcher:"#967037"};
V.assess=async()=>{
  const view=document.getElementById("view");
  if(!_reg){ try{ _reg=await api("/agent/registry"); }catch(e){ view.innerHTML=`<div class="err">${esc(e.message)}</div>`; return; } }
  if(!_sid){ const s=await api("/agent/sessions",{method:"POST",body:JSON.stringify({})}); _sid=s.session_id; }
  view.innerHTML=`<div class="top"><div><h1>AI Assessment</h1><div class="sub">Conversational multi-agent · exposure first, controls second, verdict last</div></div>
    <button class="btn ghost" onclick="newAssess()">↺ New engagement</button>
    <button class="btn" onclick="captureAssessment()">⤓ Capture to assessment</button></div>
    <div class="chat-wrap">
      <div class="chat-rail" id="rail-left"></div>
      <div class="chat-main">
        <div class="chat-scroll" id="chat-scroll"></div>
        <div class="chat-input">
          <textarea id="chat-in" rows="2" placeholder="Type your reply… (@privacy to address a specialist)"
            onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();sendChat();}"></textarea>
          <button class="btn" onclick="sendChat()">Send</button>
        </div>
      </div>
      <div class="chat-rail" id="rail-right"></div>
    </div>`;
  await refreshChat();
};
async function newAssess(){ const s=await api("/agent/sessions",{method:"POST",body:JSON.stringify({})}); _sid=s.session_id; await refreshChat(); flash("New engagement opened"); }
async function captureAssessment(){
  // map this conversation to an engagement and file a structured assessment record
  const engs=await api2("/engagements").catch(()=>[]);
  const opts=engs.map(e=>`<option value="${e.engagement_id}" data-v="${e.vendor_id}">${esc(e.engagement_id)} · ${esc(e.title)}</option>`).join("");
  modal(`<h3>Capture conversation to assessment</h3>
    <p class="muted" style="margin-bottom:10px">Files this chat as a structured AssessmentRecord mapped to an engagement. HIGH inherent auto-assigns an assessor.</p>
    <div class="field"><label>Engagement</label><select id="cap_e">${opts||'<option value="">(create a v2 engagement first)</option>'}</select></div>
    <div class="row"><button class="btn ghost" onclick="closeModal()">Cancel</button>
      <button class="btn" onclick="doCapture()">Capture</button></div>`);
}
async function doCapture(){
  const sel=document.getElementById("cap_e"); const eid=sel.value;
  if(!eid){ flash("Pick an engagement (create one under Engagements/v2 first)"); return; }
  const vid=sel.selectedOptions[0]?.getAttribute("data-v")||null;
  try{ const r=await api2("/assessments/from-session",{method:"POST",body:JSON.stringify({session_id:_sid,engagement_id:eid,vendor_id:vid})});
    closeModal(); flash(`Captured → ${r.assessment_id} (${r.status})`);
  }catch(e){ flash(e.message); }
}
async function refreshChat(){
  const d=await api("/agent/sessions/"+_sid);
  // stage strip + agents (left rail)
  const stages=_reg.stages.map(s=>`<div class="ststep ${s.id===d.stage?'cur':s.id<d.stage?'done':''}">${esc(s.short)}</div>`).join("");
  const agents=Object.entries(_reg.agents).map(([id,a])=>`<div class="agent-row ${id===d.active_agent?'active':''}">
    <div class="adot" style="background:${AGENT_COLORS[id]||'#444'}">${esc(a.name[0])}</div>
    <div><div class="an">${esc(a.name)}</div><div class="at">${esc(a.title)}</div></div></div>`).join("");
  const dossier=Object.keys(d.dossier||{}).length?Object.entries(d.dossier).map(([k,v])=>`<div class="dossier-row"><span class="dk">${esc(k)}</span><span class="dv">${esc(String(v))}</span></div>`).join(""):'<div class="muted" style="font-size:11.5px">Facts appear here as the conversation unfolds.</div>';
  document.getElementById("rail-left").innerHTML=`<h4>Stage</h4><div class="stagestrip">${stages}</div>
    <h4>Team on call</h4>${agents}<h4 style="margin-top:12px">Dossier</h4>${dossier}`;
  // messages
  const scroll=document.getElementById("chat-scroll");
  scroll.innerHTML=d.messages.map(m=>{
    if(m.role==="system") return `<div class="cmsg"><div class="cbub sys">${md1(m.body)}</div></div>`;
    if(m.role==="user") return `<div class="cmsg user"><div class="cbub user">${md1(m.body)}</div></div>`;
    const a=_reg.agents[m.agent]||{name:"?",title:""};
    return `<div class="cmsg"><div class="adot" style="background:${AGENT_COLORS[m.agent]||'#444'}">${esc(a.name[0])}</div>
      <div><div class="cmsg-hdr" style="color:${AGENT_COLORS[m.agent]||'#444'}">${esc(a.name)} · ${esc(a.title)}</div>
      <div class="cbub agent">${md1(m.body)}</div></div></div>`;
  }).join("");
  scroll.scrollTop=scroll.scrollHeight;
  // right rail: insights + learnings
  const ins=(d.insights||[]).length?d.insights.map(i=>`<div class="insight ${esc(i.severity)}">
    <div class="ik">${i.kind==='contradiction'?'Contradiction':'Practicality flag'}</div>${esc(i.detail)}</div>`).join(""):'<div class="muted" style="font-size:11.5px">Sara checks every answer for contradictions. Findings appear here.</div>';
  const lrn=(d.learnings||[]).length?d.learnings.map(l=>`<div class="learn">${esc(l.text)}</div>`).join(""):'<div class="muted" style="font-size:11.5px">No calibration yet. Use Feedback to teach the team.</div>';
  document.getElementById("rail-right").innerHTML=`<h4>Background checks</h4>${ins}
    <h4 style="margin-top:14px">Calibrated learnings</h4>${lrn}
    <button class="btn sm ghost" style="margin-top:8px;width:100%" onclick="feedbackModal()">◐ Feedback</button>`;
}
async function sendChat(){
  const t=document.getElementById("chat-in"); const msg=t.value.trim(); if(!msg)return;
  t.value=""; let agent=null;
  const m=msg.match(/^@(\w+)/); let body=msg;
  if(m){ const name=m[1].toLowerCase(); const found=Object.entries(_reg.agents).find(([id,a])=>id===name||a.name.toLowerCase()===name); if(found){agent=found[0];body=msg.replace(/^@\w+\s*/,"");} }
  try{ await api("/agent/send",{method:"POST",body:JSON.stringify({session_id:_sid,message:body,agent})}); await refreshChat(); }
  catch(e){ flash(e.message); }
}
function feedbackModal(){
  const agents=Object.entries(_reg.agents).map(([id,a])=>`<option value="${id}">${esc(a.name)}</option>`).join("");
  const issues=["Asked a question we'd already answered","Missed a contradiction","Wrong agent took the lead","Score floor not applied","Too eager to advance","Too cautious"];
  modal(`<h3>Calibrate this stage</h3>
    <p class="muted" style="margin-bottom:10px">Your feedback becomes a binding learning for every future engagement.</p>
    <div class="field"><label>Rating (1–5)</label><select id="fb_r"><option>1</option><option>2</option><option>3</option><option>4</option><option selected>5</option></select></div>
    <div class="field"><label>Which agent?</label><select id="fb_a">${agents}</select></div>
    <div class="field"><label>What happened?</label><select id="fb_i"><option value="">—</option>${issues.map(i=>`<option>${esc(i)}</option>`).join("")}</select></div>
    <div class="field"><label>Note (optional)</label><textarea id="fb_n" rows="2"></textarea></div>
    <div class="row"><button class="btn ghost" onclick="closeModal()">Cancel</button>
      <button class="btn" onclick="saveFeedback()">Save learning</button></div>`);
}
async function saveFeedback(){
  try{ await api("/agent/learnings",{method:"POST",body:JSON.stringify({
    rating:parseInt(val("fb_r")),agent:val("fb_a"),issue:val("fb_i"),note:val("fb_n"),stage:0})});
    closeModal(); flash("Calibration captured"); await refreshChat();
  }catch(e){ flash(e.message); }
}
// minimal markdown for chat (bold, code, line breaks)
function md1(s){ return esc(s).replace(/\*\*(.+?)\*\*/g,"<strong>$1</strong>").replace(/`([^`]+)`/g,"<code>$1</code>").replace(/\n/g,"<br>"); }

/* ---------- Assessments Data ---------- */
V.assessments=async()=>{
  const view=document.getElementById("view");
  view.innerHTML=`<div class="top"><div><h1>Assessments Data</h1><div class="sub">Structured assessment records · mapped to engagements</div></div></div><div id="at2" class="muted">Loading…</div>`;
  try{ const rows=await api2("/assessments");
    view.querySelector("#at2").innerHTML = rows.length?`<table><tr><th>Assessment ID</th><th>Engagement</th><th>Inherent</th><th>Status</th><th>Assessor</th><th>Locked</th><th></th></tr>
      ${rows.map(a=>`<tr class="click" onclick="openAssessmentReview('${a.assessment_id}')"><td><b>${esc(a.assessment_id)}</b></td><td>${esc(a.engagement_id)}</td>
        <td>${a.inherent_band?`<span class="band ${a.inherent_band}">${a.inherent_band}</span>`:'—'}</td>
        <td><span class="tag">${esc(a.status)}</span></td>
        <td class="muted">${esc(a.assessor_user||'—')}${a.assessor_signed_off?' ✓':''}</td>
        <td>${a.locked?'🔒':'—'}</td>
        <td style="text-align:right">open review →</td></tr>`).join("")}</table>`
      :`<div class="card muted">No assessments yet. They are created from the AI Assessment flow or via the API, mapped to an engagement.</div>`;
  }catch(e){ view.querySelector("#at2").innerHTML=`<div class="err">${esc(e.message)}</div>`; }
};
async function openAssessmentReview(aid){
  const view=document.getElementById("view");
  document.querySelectorAll('.nav a').forEach(a=>a.classList.remove('active'));
  view.innerHTML=`<div class="muted">Loading assessment…</div>`;
  let d; try{ d=await api2("/assessments/"+aid+"/review"); }catch(e){ view.innerHTML=`<div class="err">${esc(e.message)}</div>`; return; }
  const risks=(d.inherent.risks||[]), gaps=(d.gaps||[]), docs=(d.documents||[]), controls=(d.controls_assessed||[]);
  const bandPill=b=>b?`<span class="band ${b}">${b}</span>`:'—';
  view.innerHTML=`
    <div class="top"><div><h1 style="font-size:20px">Assessment review</h1>
      <div class="sub">${esc(d.assessment_id)} · engagement ${esc(d.engagement_id||'—')} · status ${esc(d.status)}${d.locked?' · 🔒 locked':''}</div></div>
      <div><button class="btn ghost" onclick="V.assessments()">← Assessments</button>
        ${d.can_approve?`<button class="btn" onclick="reviewApprove('${d.assessment_id}')">✓ Approve</button>`:(d.locked?'<span class="muted" style="font-size:12px">immutable</span>':'<span class="muted" style="font-size:12px">view only</span>')}</div></div>

    <div class="rev-grid">
      <div class="rev-panel"><h3>① Scope</h3>
        <div class="rev-row"><span class="rk">Service</span><span class="rv">${esc(d.scope.title||'—')}</span></div>
        <div class="rev-row"><span class="rk">Description</span><span class="rv">${esc(d.scope.service_description||'—')}</span></div>
        <div class="rev-row"><span class="rk">Data classification</span><span class="rv">${esc(d.scope.data_classification||'—')}</span></div>
        <div class="rev-row"><span class="rk">Critical</span><span class="rv">${d.scope.is_critical?'<span class="tag crit">CRITICAL</span>':'No'}</span></div>
      </div>
      <div class="rev-panel"><h3>② Inherent risk · ${bandPill(d.inherent.band)}</h3>
        ${risks.length?risks.map(r=>`<div class="rev-risk"><span class="v360-sevdot sev-${esc(r.severity||'Medium')}"></span><span style="flex:1">${esc(r.note||r.detail||'')}</span><span class="muted" style="font-size:11px">${esc(r.domain||'')}</span></div>`).join(""):'<div class="muted">No inherent risks recorded.</div>'}
      </div>
    </div>

    <div class="rev-panel" style="margin-bottom:14px"><h3>③ Controls assessed</h3>
      ${controls.length?controls.map(st=>`<div class="rev-stage"><div class="rev-stage-h">${esc(st.name||('Stage '+st.stage))}</div>
        ${(st.turns||[]).slice(0,6).map(t=>`<div class="rev-turn"><b>${esc(t.agent||t.role||'')}</b> ${esc((t.body||t.excerpt||'').slice(0,240))}</div>`).join("")}</div>`).join(""):'<div class="muted">No control dialogue captured. Controls assessed via DDQ where supplied.</div>'}
    </div>

    <div class="rev-grid">
      <div class="rev-panel"><h3>④ Documents (${docs.length})</h3>
        ${docs.length?docs.map(x=>`<div class="rev-row"><span class="rk">${esc(x.title||x.artefact_id)} <span class="muted" style="font-size:10px">${esc(x.kind||'')}</span></span>
          <span class="rv">${x.doc_link?`<a href="${esc(x.doc_link)}" target="_blank">view</a>`:`<span class="tag">${esc(x.status||'on file')}</span>`}</span></div>`).join(""):'<div class="muted">No documents tagged to this vendor yet.</div>'}
      </div>
      <div class="rev-panel"><h3>⑤ Residual & recommendation · ${bandPill(d.residual.band)}</h3>
        <div class="rev-row"><span class="rk">Recommendation</span><span class="rv"><b>${esc(d.residual.recommendation||d.outcome||'—')}</b></span></div>
        ${d.residual.verdict?`<div class="rev-verdict">${esc(d.residual.verdict)}</div>`:''}
        ${gaps.length?`<div class="rev-gaps"><b>Gaps (resolved risk-averse):</b> ${gaps.map(g=>esc(g.issue||g.domain||'')).join("; ")}</div>`:''}
      </div>
    </div>
    <div class="muted" style="font-size:11px;text-align:center;padding:8px">Reviewer can examine scope, inherent risk, controls, documents and residual recommendation above before approving.</div>`;
}
async function reviewApprove(aid){
  if(!confirm("Approve this assessment? The record will be hard-locked and immutable.")) return;
  try{ await api2(`/assessments/${aid}/approve`,{method:"POST",body:"{}"}); flash("Approved — record hard-locked"); openAssessmentReview(aid); }catch(e){ flash(e.message); }
}
async function asmSignoff(id){ try{ await api2(`/assessments/${id}/signoff`,{method:"POST",body:"{}"}); flash("Signed off"); V.assessments(); }catch(e){flash(e.message);} }
async function asmApprove(id){ try{ const r=await api2(`/assessments/${id}/approve`,{method:"POST",body:"{}"}); flash("Approved — record hard-locked"); V.assessments(); }catch(e){flash(e.message);} }
async function asmRecall(id){ try{ await api2(`/assessments/${id}/recall`,{method:"POST",body:"{}"}); flash("Recalled"); V.assessments(); }catch(e){flash(e.message);} }

/* ---------- Fourth Parties ---------- */
V.fourthparties=async()=>{
  const view=document.getElementById("view");
  view.innerHTML=`<div class="top"><div><h1>Fourth Parties</h1><div class="sub">Sub-processors behind your vendors · concentration risk</div></div>
    <button class="btn" onclick="newFourth()">+ New fourth party</button></div><div id="fp" class="muted">Loading…</div>`;
  try{ const rows=await api2("/fourth-parties");
    view.querySelector("#fp").innerHTML = rows.length?`<table><tr><th>F4P ID</th><th>Name</th><th>Supports vendors</th><th>Concentration</th><th>Also a vendor</th></tr>
      ${rows.map(f=>`<tr><td><b>${esc(f.fourth_party_id)}</b></td><td>${esc(f.legal_name)}</td>
        <td>${(f.supports_vendors||[]).length}</td>
        <td>${f.concentration_flag?'<span class="tag crit">CONCENTRATION ≥3</span>':'<span class="muted">—</span>'}</td>
        <td class="muted">${esc(f.vendor_id||'—')}</td></tr>`).join("")}</table>`
      :`<div class="card muted">No fourth parties yet.</div>`;
  }catch(e){ view.querySelector("#fp").innerHTML=`<div class="err">${esc(e.message)}</div>`; }
};
async function newFourth(){
  const vs=await api2("/vendors"); window._vendors=vs;
  const opts=vs.map(v=>`<option value="${v.vendor_id}">${esc(v.legal_name)} (${v.vendor_id})</option>`).join("");
  modal(`<h3>New fourth party</h3>
    <div class="field"><label>Legal name</label><input id="f4_name"></div>
    <div class="field"><label>Service provided</label><input id="f4_svc"></div>
    <div class="field"><label>HQ country</label><input id="f4_country"></div>
    <div class="field"><label>Supports vendors (Ctrl/Cmd-click)</label><select id="f4_vs" multiple size="5" style="height:auto">${opts}</select></div>
    <div class="row"><button class="btn ghost" onclick="closeModal()">Cancel</button>
      <button class="btn" onclick="saveFourth()">Create</button></div>`); }
async function saveFourth(){
  const vids=[...document.getElementById("f4_vs").selectedOptions].map(o=>o.value);
  try{ const r=await api2("/fourth-parties",{method:"POST",body:JSON.stringify({
    legal_name:val("f4_name"),service_provided:val("f4_svc"),hq_country:val("f4_country"),vendor_ids:vids})});
    closeModal(); flash(`${r.fourth_party_id} created${r.concentration_flag?' — concentration flagged':''}`); V.fourthparties();
  }catch(e){ flash(e.message); } }

/* ---------- Artefacts ---------- */
V.artefacts=async()=>{
  const view=document.getElementById("view");
  view.innerHTML=`<div class="top"><div><h1>Certificates</h1><div class="sub">Document-backed evidence · every record links its source document · revalidation engine</div></div>
    <button class="btn ghost" onclick="revalidate()">↻ Run revalidation</button>
    <button class="btn ghost" onclick="newArtefact()">+ Manual entry</button>
    <button class="btn" onclick="certUpload()">⤒ Upload documents</button></div><div id="ar" class="muted">Loading…</div>`;
  try{ const rows=await api2("/artefacts");
    view.querySelector("#ar").innerHTML = rows.length?`<table><tr><th>Certificate ID</th><th>Vendor</th><th>Name</th><th>Type</th><th>Expiry</th><th>Status</th><th>Via</th><th>Document</th></tr>
      ${rows.map(a=>`<tr style="${a.is_current?'':'opacity:.5'}"><td><b>${esc(a.artefact_id)}</b></td><td class="muted">${esc(a.vendor_id)}</td>
        <td>${esc(a.name)}</td><td>${esc(a.type)}</td><td>${esc(a.expiry_date||'—')}</td>
        <td>${a.status==='Expired'?`<span class="tag crit">Expired</span>`:a.status==='Expiring'?`<span class="tag" style="background:#f6ebda;color:var(--amber)">Expiring</span>`:`<span class="tag" style="background:#e3efe6;color:var(--moss)">Valid</span>`}</td>
        <td class="muted">${esc(a.received_via)}</td>
        <td>${a.doc_link?`<a href="${esc(a.doc_link)}" target="_blank" class="btn sm ghost">view</a>`:'<span class="muted" style="font-size:11px">—</span>'}</td></tr>`).join("")}</table>`
      :`<div class="card muted">No certificates yet. Use <b>Upload documents</b> to add certificates — each document is read automatically and filed with its source attached.</div>`;
  }catch(e){ view.querySelector("#ar").innerHTML=`<div class="err">${esc(e.message)}</div>`; }
};
async function certUpload(){
  const vs=await api2("/vendors");
  const opts=vs.map(v=>`<option value="${v.vendor_id}">${esc(v.legal_name)} (${v.vendor_id})</option>`).join("");
  modal(`<h3>Upload certificate documents</h3>
    <p class="muted" style="margin-bottom:8px">Select one or more documents. Each is read automatically — type, issue and expiry dates are extracted — and filed as a certificate with the document linked for viewing.</p>
    <div class="field"><label>Vendor</label><select id="cu_v">${opts||'<option value="">(create a vendor first)</option>'}</select></div>
    <div class="field"><label>Documents (multiple allowed)</label><input id="cu_files" type="file" multiple></div>
    <div id="cu_status" class="muted" style="font-size:12px"></div>
    <div class="row"><button class="btn ghost" onclick="closeModal()">Cancel</button>
      <button class="btn" onclick="certDoUpload()">Read &amp; file</button></div>`); }
async function certDoUpload(){
  const vid=val("cu_v"); const input=document.getElementById("cu_files");
  if(!vid){ flash("Pick a vendor"); return; }
  if(!input.files.length){ flash("Select at least one document"); return; }
  const st=document.getElementById("cu_status"); st.textContent="Reading documents…";
  const files=[];
  for(const f of input.files){
    const b64=await new Promise((res,rej)=>{const r=new FileReader();r.onload=()=>res(r.result.split(",")[1]);r.onerror=rej;r.readAsDataURL(f);});
    files.push({filename:f.name,content_type:f.type||"application/octet-stream",data_b64:b64});
  }
  try{ const r=await api2("/certificates/ingest",{method:"POST",body:JSON.stringify({vendor_id:vid,files})});
    closeModal();
    const gaps=r.certificates.flatMap(c=>c.gaps||[]);
    flash(`${r.certificates.length} certificate(s) filed${gaps.length?' · '+gaps.length+' gap(s) flagged':''}`);
    V.artefacts();
  }catch(e){ st.textContent=e.message; } }
async function newArtefact(){
  const vs=await api2("/vendors");
  const opts=vs.map(v=>`<option value="${v.vendor_id}">${esc(v.legal_name)} (${v.vendor_id})</option>`).join("");
  modal(`<h3>New artefact / certificate</h3>
    <div class="field"><label>Vendor</label><select id="ar_v">${opts||'<option>(create a vendor first)</option>'}</select></div>
    <div class="field"><label>Name</label><input id="ar_name" placeholder="ISO 27001 / SOC 2 Type II"></div>
    <div class="grid g2"><div class="field"><label>Type</label><select id="ar_type"><option>certificate</option><option>soc2</option><option>iso</option><option>other</option></select></div>
      <div class="field"><label>Expiry date</label><input id="ar_exp" type="date"></div></div>
    <div class="row"><button class="btn ghost" onclick="closeModal()">Cancel</button>
      <button class="btn" onclick="saveArtefact()">Create</button></div>`); }
async function saveArtefact(){
  const exp=val("ar_exp");
  try{ const r=await api2("/artefacts",{method:"POST",body:JSON.stringify({
    vendor_id:val("ar_v"),name:val("ar_name"),artefact_type:val("ar_type"),
    expiry_date:exp?exp+"T00:00:00":null,received_via:"upload"})});
    closeModal(); flash(`${r.artefact_id} filed (${r.status})`); V.artefacts();
  }catch(e){ flash(e.message); } }
async function revalidate(){
  try{ const r=await api2("/artefacts/revalidate",{method:"POST",body:"{}"});
    flash(`Checked ${r.checked} · ${r.notify_7day.length} expiry notice(s) · ${r.new_issues.length} new issue(s)`); V.artefacts();
  }catch(e){ flash(e.message); } }

/* ---------- Issues Log ---------- */
V.issues=async()=>{
  const view=document.getElementById("view");
  view.innerHTML=`<div class="top"><div><h1>Issues Log</h1><div class="sub">Certificates expired &gt;30 days · auto-closed on refresh or engagement close</div></div></div><div id="is" class="muted">Loading…</div>`;
  try{ const rows=await api2("/issues");
    view.querySelector("#is").innerHTML = rows.length?`<table><tr><th>Issue ID</th><th>Vendor</th><th>Artefact</th><th>Detail</th><th>Status</th></tr>
      ${rows.map(i=>`<tr style="${i.status==='Closed'?'opacity:.55':''}"><td><b>${esc(i.issue_id)}</b></td>
        <td>${esc(i.vendor_name)} <span class="muted">${esc(i.vendor_id)}</span></td><td class="muted">${esc(i.artefact_id||'—')}</td>
        <td>${esc(i.detail||'')}</td>
        <td>${i.status==='Open'?'<span class="tag crit">Open</span>':`<span class="muted">Closed · ${esc(i.closed_reason||'')}</span>`}</td></tr>`).join("")}</table>`
      :`<div class="card muted">No issues. Certificates expired over 30 days are logged here automatically by the revalidation engine.</div>`;
  }catch(e){ view.querySelector("#is").innerHTML=`<div class="err">${esc(e.message)}</div>`; }
};

/* ---------- Audit ---------- */
/* ---------- Management (Risk + Ops views + chat) ---------- */
let _mgmtView="risk";
V.management=async()=>{
  const view=document.getElementById("view");
  view.innerHTML=`<div class="top"><div><h1>Management</h1><div class="sub">Portfolio risk &amp; operations · leadership view</div></div>
    <div><button class="btn sm ${_mgmtView==='risk'?'':'ghost'}" onclick="mgmtSwitch('risk')">Risk View</button>
    <button class="btn sm ${_mgmtView==='ops'?'':'ghost'}" onclick="mgmtSwitch('ops')">Operations View</button>
    <button class="btn sm ${_mgmtView==='supply'?'':'ghost'}" onclick="mgmtSwitch('supply')">Supply Chain</button></div></div>
    <div id="mgmt"></div>
    <div class="sec-h" style="margin-top:18px"><h2>Management Chat</h2><div class="rule"></div></div>
    <div id="mgmt_chips" style="margin-bottom:8px"></div>
    <div class="chat-input" style="border:1px solid var(--line);border-radius:10px">
      <textarea id="mq" rows="1" placeholder="Ask about the portfolio…" onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();askMgmt();}"></textarea>
      <button class="btn" onclick="askMgmt()">Ask</button></div>
    <div id="mgmt_ans"></div>`;
  try{
    const sug=await api2("/management/suggested");
    document.getElementById("mgmt_chips").innerHTML=sug.questions.map(q=>`<button class="btn sm ghost" style="margin:3px" onclick="askMgmtQ('${q.replace(/'/g,"")}')">${esc(q)}</button>`).join("");
  }catch(e){}
  mgmtRender();
};
function mgmtSwitch(v){ _mgmtView=v; V.management(); }
async function mgmtRender(){
  const el=document.getElementById("mgmt"); el.innerHTML='<div class="muted">Loading…</div>';
  try{
    if(_mgmtView==="risk"){
      const r=await api2("/management/risk-view");
      el.innerHTML=`<div class="grid g4">
        <div class="card stat"><div class="v">${r.totals.vendors}</div><div class="l">Vendors</div></div>
        <div class="card stat"><div class="v">${r.totals.critical_vendors}</div><div class="l">Critical (Tier 0)</div></div>
        <div class="card stat"><div class="v">${r.totals.engagements}</div><div class="l">Engagements</div></div>
        <div class="card stat"><div class="v">${r.totals.open_findings}</div><div class="l">Open findings</div></div></div>
        <div class="sec-h" style="margin-top:14px"><h2 style="font-size:14px">Residual distribution</h2><div class="rule"></div></div>
        <div class="grid g4">${["HIGH","ELEVATED","MODERATE","LOW"].map(b=>`<div class="card stat"><div class="v">${r.residual_distribution[b]||0}</div><div class="l"><span class="band ${b}">${b}</span></div></div>`).join("")}</div>
        <div class="grid g2" style="margin-top:14px">
          <div class="card"><h3 style="font-size:13px;margin-bottom:6px">HIGH / ELEVATED residual engagements</h3>
            ${r.high_residual_engagements.length?r.high_residual_engagements.map(e=>`<div class="dossier-row"><span class="dk">${esc(e.engagement_id)} · ${esc(e.title)}</span><span class="dv"><span class="band ${e.residual_band}">${e.residual_band}</span></span></div>`).join(""):'<span class="muted" style="font-size:12px">None</span>'}</div>
          <div class="card"><h3 style="font-size:13px;margin-bottom:6px">Fourth-party concentration · Certificate exposure</h3>
            <div class="dossier-row"><span class="dk">Concentration flags</span><span class="dv">${r.fourth_party_concentration.length}</span></div>
            <div class="dossier-row"><span class="dk">Expired certs</span><span class="dv">${r.certificate_status.Expired||0}</span></div>
            <div class="dossier-row"><span class="dk">Expiring ≤7d</span><span class="dv">${r.certificate_status.Expiring||0}</span></div>
            <div class="dossier-row"><span class="dk">Open issues</span><span class="dv">${r.open_issues}</span></div></div></div>`;
    } else if(_mgmtView==="ops"){
      const o=await api2("/management/ops-view");
      el.innerHTML=`<div class="grid g4">
        <div class="card stat"><div class="v">${o.actions.open}</div><div class="l">Open actions</div></div>
        <div class="card stat"><div class="v">${o.actions.closed}</div><div class="l">Closed actions</div></div>
        <div class="card stat"><div class="v">${o.locked_assessments}</div><div class="l">Approved (locked)</div></div>
        <div class="card stat"><div class="v">${o.awaiting_signoff.length}</div><div class="l">Awaiting sign-off</div></div></div>
        <div class="grid g2" style="margin-top:14px">
          <div class="card"><h3 style="font-size:13px;margin-bottom:6px">Assessment pipeline</h3>
            ${Object.keys(o.assessment_pipeline).length?Object.entries(o.assessment_pipeline).map(([k,v])=>`<div class="dossier-row"><span class="dk">${esc(k)}</span><span class="dv">${v}</span></div>`).join(""):'<span class="muted" style="font-size:12px">No assessments yet</span>'}</div>
          <div class="card"><h3 style="font-size:13px;margin-bottom:6px">Assessor workload · Engagement status</h3>
            ${Object.keys(o.assessor_workload).length?Object.entries(o.assessor_workload).map(([k,v])=>`<div class="dossier-row"><span class="dk">${esc(k)}</span><span class="dv">${v} open</span></div>`).join(""):'<span class="muted" style="font-size:12px">No assessors assigned</span>'}
            ${Object.entries(o.engagement_status).map(([k,v])=>`<div class="dossier-row"><span class="dk">Engagements ${esc(k)}</span><span class="dv">${v}</span></div>`).join("")}</div></div>`;
    } else if(_mgmtView==="supply"){
      const g=await api2("/management/concentration");
      el.innerHTML=`
        <div class="grid g4">
          <div class="card stat"><div class="v">${g.summary.vendors}</div><div class="l">Vendors</div></div>
          <div class="card stat"><div class="v">${g.summary.fourth_parties}</div><div class="l">Fourth parties</div></div>
          <div class="card stat"><div class="v">${g.summary.locations}</div><div class="l">Delivery locations</div></div>
          <div class="card stat"><div class="v">${g.summary.edges}</div><div class="l">Dependencies</div></div></div>
        <div class="sec-h" style="margin-top:16px"><h2 style="font-size:14px">Supply-chain concentration network</h2><div class="rule"></div></div>
        <div class="card"><div class="card-label">Hubs (large, red nodes) are shared dependencies many vendors funnel through — your concentration risks.</div>
          <div id="concGraph" style="width:100%;height:520px;overflow:hidden;position:relative"></div>
          <div class="conc-legend">
            <span><i class="cdot" style="background:#1E3A5C"></i> Vendor</span>
            <span><i class="cdot" style="background:#b8862b"></i> Fourth party</span>
            <span><i class="cdot" style="background:#1A4D3C"></i> Delivery location</span>
            <span><i class="cdot" style="background:#d9534f"></i> High concentration</span>
          </div></div>
        ${g.hubs.length?`<div class="card" style="margin-top:12px"><h3 style="font-size:13px;margin-bottom:6px">Top concentration points</h3>
          ${g.hubs.map(h=>`<div class="dossier-row"><span class="dk">${esc(h.label)} <span class="muted" style="font-size:10px">${esc(h.kind.replace('_',' '))}</span></span>
            <span class="dv">${h.degree} vendors · <span class="band ${h.risk>=.66?'HIGH':h.risk>=.4?'ELEVATED':'MODERATE'}">${h.risk>=.66?'HIGH':h.risk>=.4?'ELEVATED':'MODERATE'}</span></span></div>`).join("")}</div>`:''}
        <div class="sec-h" style="margin-top:16px"><h2 style="font-size:14px">Supplier delivery locations</h2><div class="rule"></div></div>
        <div class="card"><div class="card-label">Geographic concentration — bubble size &amp; colour reflect how many engagements deliver from each country.</div>
          <div id="worldMap"></div></div>`;
      setTimeout(()=>{ drawConcGraph(g); drawWorldMap(g.locations); }, 30);
    }
  }catch(e){ el.innerHTML=`<div class="err">${esc(e.message)}</div>`; }
}
function askMgmtQ(q){ document.getElementById("mq").value=q; askMgmt(); }
async function askMgmt(){
  const q=document.getElementById("mq").value.trim(); if(!q)return;
  const out=document.getElementById("mgmt_ans");
  out.innerHTML='<div class="muted" style="margin-top:8px">Thinking…</div>';
  try{ const r=await api2("/management/chat",{method:"POST",body:JSON.stringify({question:q})});
    out.innerHTML=`<div class="card" style="margin-top:8px"><b>Q:</b> ${esc(q)}<br><br>${md1(r.answer)}
      <br><span class="muted" style="font-size:10px">${r.engine==='llm'?'AI':'deterministic'} · grounded in live data</span></div>`;
  }catch(e){ out.innerHTML=`<div class="err">${esc(e.message)}</div>`; }
}

/* ---------- Management (end) ---------- */
// CR: supply-chain concentration force-directed graph (vanilla SVG simulation)
const CONC_COLORS={vendor:"#1E3A5C",fourth_party:"#b8862b",location:"#1A4D3C"};
function drawConcGraph(g){
  const host=document.getElementById("concGraph"); if(!host) return;
  const W=host.clientWidth||900, H=520;
  const nodes=g.nodes.map(n=>({...n, x:W/2+(Math.random()-.5)*W*0.6, y:H/2+(Math.random()-.5)*H*0.6, vx:0, vy:0}));
  const idx=Object.fromEntries(nodes.map((n,i)=>[n.id,i]));
  const links=g.edges.filter(e=>idx[e.source]!=null&&idx[e.target]!=null).map(e=>({s:idx[e.source],t:idx[e.target]}));
  // simple force simulation
  const K_rep=2400, K_spring=0.015, L=70, damp=0.86, center=0.004;
  for(let it=0;it<260;it++){
    for(let i=0;i<nodes.length;i++){
      const a=nodes[i];
      for(let j=i+1;j<nodes.length;j++){
        const b=nodes[j]; let dx=a.x-b.x, dy=a.y-b.y; let d2=dx*dx+dy*dy||0.01; let d=Math.sqrt(d2);
        const f=K_rep/d2; const fx=f*dx/d, fy=f*dy/d;
        a.vx+=fx; a.vy+=fy; b.vx-=fx; b.vy-=fy;
      }
    }
    for(const lk of links){
      const a=nodes[lk.s], b=nodes[lk.t]; let dx=b.x-a.x, dy=b.y-a.y; let d=Math.sqrt(dx*dx+dy*dy)||0.01;
      const f=K_spring*(d-L); const fx=f*dx/d, fy=f*dy/d;
      a.vx+=fx; a.vy+=fy; b.vx-=fx; b.vy-=fy;
    }
    for(const n of nodes){
      n.vx+=(W/2-n.x)*center; n.vy+=(H/2-n.y)*center;
      n.vx*=damp; n.vy*=damp; n.x+=n.vx; n.y+=n.vy;
      n.x=Math.max(16,Math.min(W-16,n.x)); n.y=Math.max(16,Math.min(H-16,n.y));
    }
  }
  const riskColor=r=>r>=0.66?"#d9534f":r>=0.4?"#e0913a":null;
  const svg=[`<svg viewBox="0 0 ${W} ${H}" width="100%" height="${H}" style="display:block">`];
  for(const lk of links){ const a=nodes[lk.s], b=nodes[lk.t];
    svg.push(`<line x1="${a.x.toFixed(1)}" y1="${a.y.toFixed(1)}" x2="${b.x.toFixed(1)}" y2="${b.y.toFixed(1)}" stroke="#c9c3b4" stroke-width="0.6" opacity="0.55"/>`); }
  for(const n of nodes){ const base=CONC_COLORS[n.kind]||"#777"; const col=riskColor(n.risk)||base;
    const r=Math.max(3, Math.min(22, 3+Math.sqrt(n.degree)*2.6));
    const nt=n.kind==="location"?"location":(n.kind==="fourth_party"?"fourth_party":"vendor");
    const nkey=n.kind==="location"?(n.label):n.id;
    svg.push(`<circle class="conc-node" data-nt="${nt}" data-key="${esc(String(nkey))}" data-label="${esc(n.label)}" cx="${n.x.toFixed(1)}" cy="${n.y.toFixed(1)}" r="${r.toFixed(1)}" fill="${col}" fill-opacity="0.85" stroke="#fff" stroke-width="0.8" style="cursor:pointer"><title>${esc(n.label)} · ${esc(n.kind)} · ${n.degree} link(s) — click to explore</title></circle>`);
    if(r>=11) svg.push(`<text x="${n.x.toFixed(1)}" y="${(n.y-r-3).toFixed(1)}" text-anchor="middle" font-size="9" fill="#3a463f" style="pointer-events:none">${esc((n.label||'').slice(0,18))}</text>`);
  }
  svg.push(`</svg>`);
  host.innerHTML=svg.join("");
  host.querySelectorAll(".conc-node").forEach(el=>el.addEventListener("click",()=>
    concDetail(el.getAttribute("data-nt"), el.getAttribute("data-key"), el.getAttribute("data-label"))));
}
// country centroids [lng,lat] for the delivery-location world map
const COUNTRY_LL={"United Kingdom":[-1.5,52.6],"United States":[-98,39.5],"Ireland":[-8,53.4],"France":[2.3,46.6],"Germany":[10.4,51.2],"Spain":[-3.7,40.3],"Italy":[12.5,42.8],"Netherlands":[5.3,52.1],"Switzerland":[8.2,46.8],"Poland":[19.1,52],"Sweden":[15,62],"Norway":[8.5,61],"Belgium":[4.5,50.6],"Portugal":[-8,39.6],"Austria":[14.5,47.6],"Denmark":[9.5,56],"Finland":[26,64],"Greece":[22,39],"Czech Republic":[15.5,49.8],"Romania":[25,46],"India":[79,22],"China":[104,35],"Japan":[138,37],"South Korea":[128,36],"Singapore":[103.8,1.35],"Hong Kong":[114.1,22.3],"Malaysia":[102,4],"Indonesia":[113,-2],"Philippines":[122,12],"Thailand":[101,15],"Vietnam":[106,16],"United Arab Emirates":[54,24],"Saudi Arabia":[45,24],"Israel":[35,31],"Turkey":[35,39],"Pakistan":[69,30],"Bangladesh":[90,24],"Australia":[134,-25],"New Zealand":[172,-41],"Canada":[-106,56],"Mexico":[-102,23],"Brazil":[-52,-10],"Argentina":[-64,-34],"Chile":[-71,-30],"Colombia":[-73,4],"South Africa":[24,-29],"Nigeria":[8,9.5],"Kenya":[38,0],"Egypt":[30,27],"Morocco":[-6,32],"Russia":[90,62],"Ukraine":[32,49]};
function drawWorldMap(locations){
  const host=document.getElementById("worldMap"); if(!host) return;
  const W=960, H=480; // equirectangular
  const proj=(lng,lat)=>[ (lng+180)/360*W, (90-lat)/180*H ];
  const maxc=Math.max(1,...(locations||[]).map(l=>l.count));
  // stylized continent backdrop (simplified equirectangular blobs) + graticule
  const grat=[];
  for(let lo=-180;lo<=180;lo+=30){ const [x]=proj(lo,0); grat.push(`<line x1="${x}" y1="0" x2="${x}" y2="${H}" stroke="#eceadf" stroke-width="0.6"/>`); }
  for(let la=-60;la<=80;la+=30){ const [,y]=proj(0,la); grat.push(`<line x1="0" y1="${y}" x2="${W}" y2="${y}" stroke="#eceadf" stroke-width="0.6"/>`); }
  // approximate land polygons (recognizable, not survey-accurate)
  const LAND=[
    [[-168,65],[-150,71],[-95,70],[-82,62],[-64,60],[-52,47],[-66,44],[-80,25],[-97,18],[-105,23],[-124,40],[-130,54],[-168,65]], // N America
    [[-81,8],[-60,5],[-50,-5],[-43,-23],[-58,-34],[-71,-52],[-75,-45],[-81,-5],[-81,8]], // S America
    [[-10,36],[2,40],[12,38],[18,40],[28,40],[30,46],[24,55],[12,55],[4,52],[-5,48],[-10,43],[-10,36]], // Europe
    [[-17,21],[10,33],[24,32],[33,31],[44,11],[51,12],[40,-5],[40,-18],[32,-28],[18,-34],[12,-17],[8,4],[-8,5],[-17,15],[-17,21]], // Africa
    [[26,40],[40,42],[55,40],[70,38],[90,45],[110,50],[135,48],[142,52],[130,35],[122,30],[120,22],[108,12],[98,8],[80,8],[72,20],[60,25],[45,30],[35,36],[26,40]], // Asia
    [[114,-22],[130,-12],[142,-12],[150,-25],[146,-38],[135,-35],[129,-32],[118,-34],[114,-22]] // Australia
  ];
  const land=LAND.map(poly=>`<polygon points="${poly.map(([lo,la])=>proj(lo,la).map(n=>n.toFixed(1)).join(',')).join(' ')}" fill="#eef1ec" stroke="#dfe3da" stroke-width="0.8"/>`).join("");
  const bubbles=(locations||[]).map(l=>{
    const ll=COUNTRY_LL[l.country]; if(!ll) return "";
    const [x,y]=proj(ll[0],ll[1]); const t=l.count/maxc;
    const r=6+t*22; const col=t>=0.66?"#d9534f":t>=0.33?"#e0913a":"#1A4D3C";
    return `<g class="map-bubble" data-key="${esc(l.country)}" style="cursor:pointer"><circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${r.toFixed(1)}" fill="${col}" fill-opacity="0.55" stroke="${col}" stroke-width="1.2"><title>${esc(l.country)} · ${l.count} engagement(s) — click to explore</title></circle>
      <circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="2.5" fill="${col}"/>
      <text x="${x.toFixed(1)}" y="${(y-r-4).toFixed(1)}" text-anchor="middle" font-size="10" fill="#28332c" style="pointer-events:none">${esc(l.country)} (${l.count})</text></g>`;
  }).join("");
  host.innerHTML=`<svg viewBox="0 0 ${W} ${H}" width="100%" style="display:block;background:#f7f9f6;border-radius:10px">
    ${grat.join("")}${land}${bubbles}
    ${(!locations||!locations.length)?`<text x="${W/2}" y="${H/2}" text-anchor="middle" fill="#9aa39b" font-size="14">No delivery locations recorded yet — add them on engagement records</text>`:''}
  </svg>`;
  host.querySelectorAll(".map-bubble").forEach(el=>el.addEventListener("click",()=>
    concDetail("location", el.getAttribute("data-key"), el.getAttribute("data-key"))));
}
// ---- expandable drill-down drawer behind a concentration node / map bubble ----
async function concDetail(nodeType, key, label){
  let host=document.getElementById("concDrawer");
  if(!host){ host=document.createElement("div"); host.id="concDrawer"; host.className="conc-drawer"; document.body.appendChild(host); }
  host.classList.add("open");
  host.innerHTML=`<div class="cd-head"><div><div class="cd-kicker">${esc((nodeType||'').replace('_',' '))}</div><h3>${esc(label||key)}</h3></div>
    <button class="cd-x" onclick="closeConcDrawer()">✕</button></div><div class="cd-body muted">Loading…</div>`;
  try{
    const d=await api2(`/management/concentration/detail?node_type=${encodeURIComponent(nodeType)}&key=${encodeURIComponent(key)}`);
    concDetailRender(host, d);
  }catch(e){ host.querySelector(".cd-body").innerHTML=`<div class="err">${esc(e.message)}</div>`; }
}
function closeConcDrawer(){ const h=document.getElementById("concDrawer"); if(h) h.classList.remove("open"); }
function _fmtM(n){ if(!n) return "—"; return n>=1e6?`£${(n/1e6).toFixed(1)}m`:n>=1e3?`£${Math.round(n/1e3)}k`:`£${n}`; }
function _band(b){ return b?`<span class="band ${b}">${b}</span>`:'—'; }
function concDetailRender(host, d){
  const s=d.summary||{};
  let stat="";
  const statbits=[];
  if(s.vendors!=null) statbits.push([`${s.vendors}`,"Vendors"]);
  if(s.dependent_vendors!=null) statbits.push([`${s.dependent_vendors}`,"Dependent vendors"]);
  if(s.engagements!=null) statbits.push([`${s.engagements}`,"Engagements"]);
  if(s.critical_vendors!=null) statbits.push([`${s.critical_vendors}`,"Critical"]);
  if(s.critical_dependents!=null) statbits.push([`${s.critical_dependents}`,"Critical"]);
  if(s.fourth_parties!=null) statbits.push([`${s.fourth_parties}`,"4th parties"]);
  if(s.total_value!=null) statbits.push([_fmtM(s.total_value),"Annual value"]);
  stat=`<div class="cd-stats">${statbits.map(([v,l])=>`<div><div class="cv">${v}</div><div class="cl">${esc(l)}</div></div>`).join("")}</div>`;

  let body="";
  if(d.fourth_party){ const f=d.fourth_party;
    body+=`<div class="cd-card"><div class="cd-lab">Fourth party</div>
      <div class="cd-row"><span>Service</span><b>${esc(f.service||'—')}</b></div>
      <div class="cd-row"><span>HQ</span><b>${esc(f.hq_country||'—')}</b></div>
      <div class="cd-row"><span>Concentration flag</span><b>${f.concentration_flag?'<span class=\"tag crit\">Flagged</span>':'No'}</b></div></div>`; }
  if(d.vendor){ const v=d.vendor;
    body+=`<div class="cd-card"><div class="cd-lab">Vendor</div>
      <div class="cd-row"><span>Tier</span><b>${esc(v.tier||'—')}</b></div>
      <div class="cd-row"><span>Critical</span><b>${v.critical?'<span class=\"tag crit\">Critical</span>':'No'}</b></div></div>`; }

  if((d.vendors||[]).length){
    body+=`<div class="cd-lab">Vendors (${d.vendors.length})</div><div class="cd-list">`+
      d.vendors.map(v=>`<div class="cd-item" onclick="closeConcDrawer();openV360('${v.vendor_id}')" title="Open Vendor 360">
        <span class="ci-name">${esc(v.name)} ${v.critical?'<span class=\"tag crit\" style=\"font-size:9px\">CRIT</span>':''}</span>
        <span class="ci-meta">${esc(v.tier||'')} · ${esc(v.vendor_id)} ›</span></div>`).join("")+`</div>`;
  }
  if((d.engagements||[]).length){
    body+=`<div class="cd-lab" style="margin-top:14px">Engagements (${d.engagements.length})</div><div class="cd-list">`+
      d.engagements.slice(0,80).map(e=>`<div class="cd-item" onclick="closeConcDrawer();openEngagementRegister&&openEngagementRegister('${e.engagement_id}')" title="Open engagement register">
        <span class="ci-name">${esc(e.title)}</span>
        <span class="ci-meta">${e.vendor_name?esc(e.vendor_name)+' · ':''}${_band(e.inherent_band)}→${_band(e.residual_band)} · ${_fmtM(e.annual_value)}${e.delivery_location?' · '+esc(e.delivery_location):''}</span></div>`).join("")+`</div>`;
  }
  if((d.fourth_parties||[]).length){
    body+=`<div class="cd-lab" style="margin-top:14px">Fourth-party reliance (${d.fourth_parties.length})</div><div class="cd-list">`+
      d.fourth_parties.map(f=>`<div class="cd-item" onclick="concDetail('fourth_party','${f.id}','${esc(f.name).replace(/'/g,'')}')" title="Explore this dependency">
        <span class="ci-name">${esc(f.name)}</span><span class="ci-meta">${esc(f.id)} ›</span></div>`).join("")+`</div>`;
  }
  if(!body) body=`<div class="muted">No connected records.</div>`;
  host.querySelector(".cd-body").innerHTML=stat+body;
}
/* ============ Analysis sections: shared helpers ============ */
let _secEntities=null;
async function loadEntities(){ if(!_secEntities){ try{ _secEntities=await api2("/vendors"); }catch(e){ _secEntities=[]; } } return _secEntities; }
function entitySelector(idPrefix){
  const opts=(_secEntities||[]).map(v=>`<option value="${v.vendor_id}">${esc(v.legal_name)} (${v.vendor_id})</option>`).join("");
  return `<div class="ent-box"><div class="card-label" style="margin-bottom:10px">Target entity</div>
    <div class="row2">
      <div class="field"><label>Registered vendor</label><select id="${idPrefix}_v"><option value="">— select —</option>${opts}</select></div>
      <div class="field"><label>Other (not in register)</label><input id="${idPrefix}_o" placeholder="type any entity name"></div>
    </div><p class="muted" style="font-size:11.5px;margin-top:6px">Pick a registered vendor to link results to its Vendor ID, or type any entity in “Other”.</p></div>`;
}
function entityPayload(idPrefix){ const v=val(idPrefix+"_v"), o=val(idPrefix+"_o"); return { vendor_id: v||null, other_name: o||null }; }
function toneFor(score){ return score>=80?"ok":score>=60?"info":score>=45?"warn":"crit"; }
function gauge(label,value){
  const v=(value==null||isNaN(value))?null:value; const t=v==null?"info":toneFor(v);
  return `<div class="gauge"><div class="gauge-bar"><div class="gauge-fill ${t}" style="width:${v==null?0:Math.round(v)}%"></div></div>
    <div class="gauge-meta"><span class="gl">${esc(label)}</span><span class="gv">${v==null?"—":Math.round(v)}</span></div></div>`;
}
function entityBadge(ent){ if(!ent)return ""; return ent.registered
  ? `<span class="pill ok">${esc(ent.vendor_name)} · ${esc(ent.vendor_id)}</span>`
  : `<span class="pill mute">${esc(ent.vendor_name)} · not registered</span>`; }
function emptyBox(icon,title,sub){ return `<div class="card empty-box"><div class="ei">${icon}</div><div class="et">${esc(title)}</div><div class="muted">${esc(sub)}</div></div>`; }

/* ============ Financial DD ============ */
const FDD_FIELDS=[["revenue","Revenue"],["cogs","Cost of goods sold"],["grossProfit","Gross profit"],["ebit","EBIT"],["ebitda","EBITDA"],["netProfit","Net profit"],["interest","Interest expense"],["currentAssets","Current assets"],["currentLiabilities","Current liabilities"],["inventory","Inventory"],["cash","Cash & equivalents"],["totalAssets","Total assets"],["totalDebt","Total debt"],["equity","Shareholders equity"],["receivables","Trade receivables"],["payables","Trade payables"],["netDebt","Net debt"],["totalLiabilities","Total liabilities"],["retainedEarnings","Retained earnings"]];
const RATIO_ROWS=[["currentRatio","Current ratio","x","Liquidity"],["quickRatio","Quick ratio","x","Liquidity"],["cashRatio","Cash ratio","x","Liquidity"],["debtToEquity","Debt / equity","x","Solvency"],["debtRatio","Debt ratio","x","Solvency"],["netDebtEbitda","Net debt / EBITDA","x","Solvency"],["interestCover","Interest cover","x","Solvency"],["equityRatio","Equity ratio","x","Solvency"],["grossMargin","Gross margin","%","Profitability"],["ebitMargin","EBIT margin","%","Profitability"],["netMargin","Net margin","%","Profitability"],["ebitdaMargin","EBITDA margin","%","Profitability"],["roa","Return on assets","%","Profitability"],["roe","Return on equity","%","Profitability"],["assetTurnover","Asset turnover","x","Efficiency"],["receivableDays","Receivable days","d","Efficiency"],["payableDays","Payable days","d","Efficiency"]];
let _fddTab="setup", _fddFigs={}, _fddFlags={auditQualified:false,goingConcern:false,negativeEquity:false,filingsOnTime:true}, _fddResult=null, _fddSector="tech", _fddPeers=null, _fddEnt=null;
function fnum(n){ return (n==null||isNaN(n))?"—":(Math.abs(n)>=1000?Math.round(n).toLocaleString():(+n).toFixed(2)); }
function fpct(n){ return (n==null||isNaN(n))?"—":(n*100).toFixed(1)+"%"; }
V.fdd=async()=>{
  await loadEntities();
  let secs; try{ secs=await api2("/sectors"); }catch(e){ secs=[{id:"other",label:"Other"}]; }
  window._fddSecs=secs;
  const view=document.getElementById("view");
  view.innerHTML=`<div class="top"><div><h1>Financial Due Diligence</h1><div class="sub">5-pillar model · 17 ratios · Altman Z′ · Peer benchmarking · Stress testing</div></div></div>
    ${entitySelector("fdd")}
    <div class="seg">${["setup","ratios","peers","stress","report"].map(t=>`<button class="${_fddTab===t?'on':''}" onclick="fddTab('${t}')">${{setup:"⚙️ Setup",ratios:"📊 Ratios",peers:"🏛️ Peers",stress:"💥 Stress",report:"📑 Report"}[t]}</button>`).join("")}</div>
    <div id="fddBody"></div>`;
  fddRender();
};
function fddTab(t){ _fddTab=t; fddRender(); }
function fddRender(){
  const el=document.getElementById("fddBody");
  if(_fddTab==="setup"){
    el.innerHTML=`<div class="card"><div class="card-label">🔍 Research from published financials <span class="muted" style="font-weight:400;text-transform:none">— Vera + Rex search authoritative filings (needs AI key)</span></div>
      <div class="grid g3">
        <div class="field"><label>Jurisdiction</label><select id="fdd_jur">${["UK","US","EU","Ireland","Switzerland","Canada","Australia","India","Singapore","UAE","Other"].map(j=>`<option>${j}</option>`).join("")}</select></div>
        <div class="field"><label>Identifier / ticker (optional)</label><input id="fdd_id" placeholder="NASDAQ:CRM · Co. No. 09876543"></div>
        <div class="field"><label>Reporting year (optional)</label><input id="fdd_yr" placeholder="latest"></div></div>
      <button class="btn" style="margin-top:12px" onclick="fddResearch()">🔍 Research &amp; collect financials</button>
      <div id="fddProv"></div></div>
      <div class="card"><div class="card-label">Financial statement data (millions)</div>
      <div class="grid g3">${FDD_FIELDS.map(([k,l])=>`<div class="field"><label>${esc(l)}</label><input type="number" id="fdd_f_${k}" value="${_fddFigs[k]??""}" placeholder="0"></div>`).join("")}</div></div>
      <div class="card"><div class="card-label">Qualitative flags (viability pillar)</div>
        <div style="display:flex;gap:18px;flex-wrap:wrap">${[["auditQualified","⚠ Audit qualified"],["goingConcern","⚠ Going concern note"],["negativeEquity","⚠ Negative equity"],["filingsOnTime","✓ Filings on time"]].map(([k,l])=>`<label style="display:flex;align-items:center;gap:6px;font-weight:400"><input type="checkbox" id="fdd_fl_${k}" ${_fddFlags[k]?"checked":""} style="width:auto"> ${l}</label>`).join("")}</div></div>
      <div class="field"><label>Industry sector (for peer benchmarking)</label><select id="fdd_sector" style="max-width:320px">${(window._fddSecs||[]).map(s=>`<option value="${s.id}" ${_fddSector===s.id?"selected":""}>${esc(s.label)}</option>`).join("")}</select></div>
      <button class="btn" style="margin-top:14px" onclick="fddCompute()">📊 Compute</button>`;
  } else if(_fddTab==="ratios"){
    if(!_fddResult){ el.innerHTML=emptyBox("📊","No figures computed yet","Enter financials in Setup and press Compute."); return; }
    const r=_fddResult, z=r.altman, zt=z.zone==="safe"?"ok":z.zone==="grey"?"warn":"crit";
    el.innerHTML=`<div class="card"><div class="score-strip">
        <div class="score-big"><div class="score-num">${r.overall==null?"—":Math.round(r.overall)}</div><div class="score-cap">Financial health</div>
          <span class="pill ${r.overall>=75?'ok':r.overall>=60?'info':r.overall>=45?'warn':'crit'}">${esc(r.banding)}</span></div>
        <div class="altman"><div class="altman-z">Altman Z′ <b class="${zt}">${z.z==null?"—":z.z.toFixed(2)}</b></div>
          <span class="pill ${zt}">${z.zone==="safe"?"Safe zone":z.zone==="grey"?"Grey zone":z.zone==="distress"?"Distress zone":"insufficient"}</span>
          <div class="muted" style="font-size:11px">&gt;2.9 safe · 1.23–2.9 grey · &lt;1.23 distress</div></div></div>
      <div class="pillar-row">${["liquidity","solvency","profitability","efficiency","viability"].map(k=>gauge(k[0].toUpperCase()+k.slice(1),r.pillars[k])).join("")}</div></div>
      <table><tr><th>Ratio</th><th>Pillar</th><th>Value</th></tr>
        ${RATIO_ROWS.map(([k,l,u,p])=>{const v=r.ratios[k];const d=v==null?"—":(u==="%"?fpct(v):u==="d"?Math.round(v)+"d":fnum(v)+"×");return `<tr><td>${esc(l)}</td><td class="muted">${esc(p)}</td><td><b>${d}</b></td></tr>`;}).join("")}</table>
      ${r.sara_checks.length?`<div class="card" style="margin-top:12px"><div class="card-label">Sara's consistency checks</div>${r.sara_checks.map(c=>`<div class="note ${c.tone==='crit'?'crit':'warn'}" style="margin-bottom:6px">${esc(c.text)}</div>`).join("")}</div>`:""}`;
  } else if(_fddTab==="peers"){
    if(!_fddPeers){ el.innerHTML=emptyBox("🏛️","Compute first","Peer comparison needs computed ratios."); return; }
    el.innerHTML=`<div class="card"><div class="card-label">Peer benchmarking — sector medians</div>
      <table><tr><th>Metric</th><th>Company</th><th>Sector median</th><th>Δ vs peers</th></tr>
      ${_fddPeers.peers.map(p=>{const d=x=>x==null?"—":(p.unit==="%"?fpct(x):fnum(x)+"×");return `<tr><td>${esc(p.metric)}</td><td><b>${d(p.company)}</b></td><td>${d(p.median)}</td><td><span class="pill ${p.verdict==='favourable'?'ok':p.verdict==='—'?'mute':'warn'}">${esc(p.verdict)}</span></td></tr>`;}).join("")}</table></div>`;
  } else if(_fddTab==="stress"){
    el.innerHTML=`<div class="card"><div class="card-label">Stress test — adjust the dials</div>
      <div class="stress-grid">
        <div class="field"><label>Revenue shock −<span id="sv">0</span>%</label><input type="range" min="0" max="50" value="0" oninput="document.getElementById('sv').textContent=this.value"></div>
        <div class="field"><label>Margin compression −<span id="sm">0</span> pts</label><input type="range" min="0" max="20" value="0" oninput="document.getElementById('sm').textContent=this.value"></div>
        <div class="field"><label>Interest rate +<span id="sr">0</span>%</label><input type="range" min="0" max="10" value="0" oninput="document.getElementById('sr').textContent=this.value"></div></div>
      <p class="muted">Deterministic engine recomputes against shocked figures.</p>
      <button class="btn" onclick="fddStress()">💥 Model this scenario</button><div id="fddStressOut"></div></div>`;
  } else if(_fddTab==="report"){
    if(!_fddResult){ el.innerHTML=emptyBox("📑","No report yet","Compute the figures in Setup first."); return; }
    const r=_fddResult;
    el.innerHTML=`<div class="card"><div class="card-label">📑 Financial due diligence summary</div>
      <div class="ai-out">Entity: ${_fddEnt?(_fddEnt.registered?_fddEnt.vendor_name+" ("+_fddEnt.vendor_id+")":_fddEnt.vendor_name+" — not registered"):"(unspecified)"}
Financial health: ${r.overall==null?"—":Math.round(r.overall)} / 100 — ${r.banding}
Altman Z′: ${r.altman.z==null?"—":r.altman.z.toFixed(2)} (${r.altman.zone} zone)

Pillars — Liquidity ${Math.round(r.pillars.liquidity||0)} · Solvency ${Math.round(r.pillars.solvency||0)} · Profitability ${Math.round(r.pillars.profitability||0)} · Efficiency ${Math.round(r.pillars.efficiency||0)} · Viability ${Math.round(r.pillars.viability||0)}

${r.sara_checks.length?"Consistency flags:\n"+r.sara_checks.map(c=>"• "+c.text).join("\n"):"Inputs internally consistent."}

Informational counterparty-risk analysis — not investment advice. Verify figures against the primary filing.</div></div>`;
  }
}
function fddCollect(){ const f={}; FDD_FIELDS.forEach(([k])=>{const e=document.getElementById("fdd_f_"+k); if(e&&e.value!=="")f[k]=parseFloat(e.value);}); _fddFigs=f;
  ["auditQualified","goingConcern","negativeEquity","filingsOnTime"].forEach(k=>{const e=document.getElementById("fdd_fl_"+k); if(e)_fddFlags[k]=e.checked;});
  const ss=document.getElementById("fdd_sector"); if(ss)_fddSector=ss.value; }
async function fddCompute(){
  fddCollect();
  if(!Object.keys(_fddFigs).length){ flash("Enter at least some figures"); return; }
  try{
    _fddResult=await api2("/financial-dd",{method:"POST",body:JSON.stringify({figures:_fddFigs,flags:_fddFlags})});
    _fddPeers=await api2("/financial-dd/peers",{method:"POST",body:JSON.stringify({figures:_fddFigs,flags:_fddFlags,sector:_fddSector})});
    const ep=entityPayload("fdd"); _fddEnt=(ep.vendor_id||ep.other_name)?(await api2("/reputation",{method:"POST",body:JSON.stringify({...ep,events:[]})})).entity:null;
    _fddTab="ratios"; fddRender(); flash("Computed");
  }catch(e){ flash(e.message); }
}
async function fddResearch(){
  const ep=entityPayload("fdd");
  const company=ep.other_name || (_secEntities.find(v=>v.vendor_id===ep.vendor_id)?.legal_name) || "";
  if(!company){ flash("Pick a vendor or type a company in Other"); return; }
  const prov=document.getElementById("fddProv"); prov.innerHTML='<div class="muted" style="margin-top:10px">Researching authoritative sources…</div>';
  try{
    const r=await api2("/financial-dd/research",{method:"POST",body:JSON.stringify({company,jurisdiction:val("fdd_jur"),identifier:val("fdd_id"),year:val("fdd_yr")})});
    if(r.matched && r.figures){ FDD_FIELDS.forEach(([k])=>{const e=document.getElementById("fdd_f_"+k); if(e&&r.figures[k]!=null)e.value=r.figures[k];});
      prov.innerHTML=`<div class="prov"><div class="prov-head"><span><b>${esc(r.entity?.legalName||company)}</b></span><span class="pill ${r.confidence==='high'?'ok':r.confidence==='medium'?'warn':'crit'}">${esc(r.confidence||'?')} confidence</span></div>
        <div class="prov-meta">Period: <b>${esc(r.period||'—')}</b> · Currency: <b>${esc(r.currency||'—')}</b></div>
        <div class="note warn" style="margin-top:10px"><b>Verify before reliance.</b> AI-extracted from public sources — confirm against the primary filing.</div></div>`;
      flash("Figures auto-filled — review then Compute");
    } else { prov.innerHTML=`<div class="note crit" style="margin-top:10px"><b>No authoritative match.</b> ${esc(r.limitations||"Enter figures manually.")}</div>`; }
  }catch(e){ prov.innerHTML=`<div class="err">${esc(e.message)}</div>`; }
}
async function fddStress(){
  fddCollect();
  const rev=+document.getElementById("sv").textContent, mar=+document.getElementById("sm").textContent, rate=+document.getElementById("sr").textContent;
  const shocked={..._fddFigs};
  if(shocked.revenue){ shocked.revenue=shocked.revenue*(1-rev/100); }
  if(shocked.ebit){ shocked.ebit=shocked.ebit-(_fddFigs.revenue||0)*(mar/100); }
  if(shocked.interest){ shocked.interest=shocked.interest*(1+rate/100); }
  try{ const r=await api2("/financial-dd",{method:"POST",body:JSON.stringify({figures:shocked,flags:_fddFlags})});
    document.getElementById("fddStressOut").innerHTML=`<div class="ai-out">Stressed — revenue −${rev}%, margin −${mar}pts, rates +${rate}%
Financial health: ${r.overall==null?"—":Math.round(r.overall)} / 100 (was ${_fddResult?Math.round(_fddResult.overall):"—"}) — ${r.banding}
Altman Z′: ${r.altman.z==null?"—":r.altman.z.toFixed(2)} (${r.altman.zone} zone)
Interest cover: ${r.ratios.interestCover==null?"—":r.ratios.interestCover.toFixed(2)}×</div>`;
  }catch(e){ flash(e.message); }
}

/* ============ Reputation ============ */
let _repTab="setup", _repResult=null, _repEvents=[];
V.reputation=async()=>{
  await loadEntities();
  const view=document.getElementById("view");
  view.innerHTML=`<div class="top"><div><h1>Reputation &amp; ESG Intelligence</h1><div class="sub">7-pillar model · Regulatory · Litigation · Cyber · ESG-E/S/G · Media</div></div></div>
    ${entitySelector("rep")}
    <div class="seg">${["setup","pillars","findings"].map(t=>`<button class="${_repTab===t?'on':''}" onclick="repTab('${t}')">${{setup:"⚙️ Setup",pillars:"📊 Pillars",findings:"🔎 Findings"}[t]}</button>`).join("")}</div>
    <div id="repBody"></div>`;
  repRender();
};
function repTab(t){ _repTab=t; repRender(); }
function repRender(){
  const el=document.getElementById("repBody");
  if(_repTab==="setup"){
    el.innerHTML=`<div class="card"><div class="card-label">Reputation assessment setup</div>
      <label style="display:flex;align-items:center;gap:6px;font-weight:400;margin-bottom:12px"><input type="checkbox" id="rep_cf" style="width:auto"> Customer-facing engagement (raises brand-transfer risk)</label>
      <div class="card-label">Known adverse events (optional)</div>
      <div id="repEvts">${_repEvents.map((e,i)=>`<div class="dossier-row"><span class="dk">${esc(e.pillar)} · ${esc(e.severity)}</span><span class="dv">${esc(e.title||"")} <button class="btn sm ghost" onclick="repDelEvt(${i})">×</button></span></div>`).join("")}</div>
      <div class="grid g3" style="margin-top:8px">
        <div class="field"><label>Pillar</label><select id="rep_p">${["regulatory","litigation","cyber","esg_environmental","esg_social","esg_governance","media"].map(p=>`<option>${p}</option>`).join("")}</select></div>
        <div class="field"><label>Severity</label><select id="rep_s"><option>critical</option><option>high</option><option selected>medium</option><option>low</option></select></div>
        <div class="field"><label>Title</label><input id="rep_t" placeholder="e.g. FCA settlement 2024"></div></div>
      <button class="btn ghost sm" style="margin-top:8px" onclick="repAddEvt()">+ Add event</button>
      <div style="margin-top:14px"><button class="btn" onclick="repRun()">🔎 Run reputation assessment</button></div>
      <p class="muted" style="margin-top:8px">With an AI key, Mira + Rex sweep authoritative sources across all 7 pillars. Offline, scoring is driven by the events above (clean = 100).</p></div>`;
  } else if(_repTab==="pillars"){
    if(!_repResult){ el.innerHTML=emptyBox("📊","No scores yet","Run the assessment from Setup."); return; }
    el.innerHTML=`<div class="card"><div class="score-strip"><div class="score-big"><div class="score-num">${_repResult.overall}</div><div class="score-cap">Overall reputation</div>
      <span class="pill ${toneFor(_repResult.overall)}">${esc(_repResult.verdict)}</span></div>
      <div>${entityBadge(_repResult.entity)}${_repResult.customer_facing?' <span class="pill warn">customer-facing</span>':''}</div></div>
      <div class="pillar-row wrap">${_repResult.pillars.map(p=>gauge(p.label,p.score)).join("")}</div></div>`;
  } else if(_repTab==="findings"){
    if(!_repResult){ el.innerHTML=emptyBox("🔎","No findings yet","Run the assessment from Setup."); return; }
    const wf=_repResult.pillars.filter(p=>p.findings&&p.findings.length);
    el.innerHTML=`<div class="card"><div class="card-label">Pillar findings</div>
      ${wf.length?wf.map(p=>`<div style="margin-bottom:12px"><b>${esc(p.label)}</b> <span class="pill ${toneFor(p.score)}">${p.score}</span><br>${p.findings.map(f=>`<span class="muted" style="font-size:12.5px">• ${esc(f.title)} (${esc(f.severity)})${f.date?` — ${esc(f.date)}`:""}</span>`).join("<br>")}</div>`).join(""):'<span class="muted">No adverse findings recorded — all pillars clean.</span>'}
      ${_repResult.timeline&&_repResult.timeline.length?`<div class="card-label" style="margin-top:14px">Adverse-event timeline</div>${_repResult.timeline.map(t=>`<div class="dossier-row"><span class="dk">${esc(t.date||"undated")}</span><span class="dv">${esc(t.title||"")} · ${esc(t.pillar||"")} (${esc(t.severity||"")})</span></div>`).join("")}`:""}</div>`;
  }
}
function repAddEvt(){ const p=val("rep_p"),s=val("rep_s"),t=val("rep_t"); if(!t){flash("Add a title");return;} _repEvents.push({pillar:p,severity:s,title:t}); repRender(); }
function repDelEvt(i){ _repEvents.splice(i,1); repRender(); }
async function repRun(){
  const cf=document.getElementById("rep_cf")?.checked||false; const ep=entityPayload("rep");
  try{ _repResult=await api2("/reputation",{method:"POST",body:JSON.stringify({...ep,events:_repEvents,customer_facing:cf})});
    _repTab="pillars"; repRender(); flash("Assessment complete");
  }catch(e){ flash(e.message); }
}

/* ============ Financial Monitoring ============ */
V.finmon=async()=>{
  await loadEntities();
  const view=document.getElementById("view");
  view.innerHTML=`<div class="top"><div><h1>Financial Monitoring Panel</h1><div class="sub">Periodic sweep · financial health, disclosures, profit warnings, rating changes, distress signals</div></div>
    <button class="btn" onclick="finmonSweep()">▶ Run monitoring sweep</button></div>
    <div class="card"><div class="card-label">Empanel an entity for monitoring</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px">
        <div class="field"><label>Registered vendor</label><select id="fm_v"><option value="">— select —</option>${(_secEntities||[]).map(v=>`<option value="${v.vendor_id}">${esc(v.legal_name)} (${v.vendor_id})</option>`).join("")}</select></div>
        <div class="field"><label>Other (not in register)</label><input id="fm_o" placeholder="company name"></div></div>
      <button class="btn ghost sm" style="margin-top:8px" onclick="finmonAdd()">+ Empanel</button></div>
    <div id="fmList" class="muted">Loading…</div>`;
  finmonList();
};
async function finmonList(){
  try{ const rows=await api2("/fin-monitor");
    document.getElementById("fmList").innerHTML = rows.length? rows.map(r=>`<div class="card"><div class="card-label">${esc(r.entity_name)} ${r.vendor_id?`<span class="pill ok" style="margin-left:6px">${esc(r.vendor_id)}</span>`:'<span class="pill mute" style="margin-left:6px">Other</span>'}
      <button class="btn sm ghost" style="float:right" onclick="finmonDel(${r.id})">Remove</button>
      ${r.last_signal?`<span class="pill ${r.last_signal==='distress'?'crit':r.last_signal==='watch'?'warn':'ok'}" style="float:right;margin-right:8px">${esc(r.last_signal)}</span>`:''}</div>
      ${r.last_result?`<div class="ai-out">${md1(r.last_result)}</div><p class="muted" style="font-size:11px;margin-top:6px">Last swept: ${esc(r.last_swept||'—')}</p>`:'<div class="muted">Not yet swept.</div>'}</div>`).join("")
      : emptyBox("📡","No entities empanelled","Add a vendor or Other entity above to monitor its financial health.");
  }catch(e){ document.getElementById("fmList").innerHTML=`<div class="err">${esc(e.message)}</div>`; }
}
async function finmonAdd(){
  const v=val("fm_v"), o=val("fm_o");
  if(!v&&!o){ flash("Pick a vendor or type a name"); return; }
  try{ await api2("/fin-monitor",{method:"POST",body:JSON.stringify({vendor_id:v||null,other_name:o||null})}); flash("Empanelled"); finmonList(); }catch(e){ flash(e.message); }
}
async function finmonDel(id){ try{ await api2("/fin-monitor/"+id,{method:"DELETE"}); finmonList(); }catch(e){ flash(e.message); } }
async function finmonSweep(){
  try{ const r=await api2("/fin-monitor/sweep",{method:"POST",body:"{}"});
    flash(`Swept ${r.swept}${r.ai_enabled?"":" (offline — set AI key for live sources)"}`); finmonList();
  }catch(e){ flash(e.message); }
}

/* ============ Contracts ============ */
let _conTab="min", _conTerms=null, _conGap=null, _conDiff=null;
const CONTRACT_TIERS=[{tier:1,name:"Regulatory mandatory",tone:"crit",desc:"Clauses required by law. Absence = regulatory breach. e.g. GDPR Art.28 DPA, DORA Art.30, FCA outsourcing."},{tier:2,name:"Market standard",tone:"warn",desc:"Present in 90%+ of negotiated contracts. e.g. confidentiality, IP ownership, step-in, data deletion."},{tier:3,name:"Best practice",tone:"info",desc:"Present in well-negotiated contracts. e.g. personnel vetting, SLA granularity, change control, BCP testing."},{tier:4,name:"Commercial preference",tone:"mute",desc:"Useful when leverage permits. e.g. benchmarking, MFN pricing, source-code escrow, enhanced SLA credits."}];
V.contracts=async()=>{
  await loadEntities();
  const engs=await api2("/engagements").catch(()=>[]);
  const view=document.getElementById("view");
  view.innerHTML=`<div class="top"><div><h1>⚖️ Contract Management</h1><div class="sub">Minimum terms scaled to inherent risk · gap report · existing-vs-to-add · document-driven extraction</div></div></div>
    <div class="card"><div class="card-label" style="margin-bottom:10px">Engagement (registered) — inherits inherent band &amp; exposure automatically</div>
      <div class="field" style="max-width:520px"><label>Linked engagement</label>
        <select id="con_eng" onchange="conEngChange()"><option value="">— Other / unregistered (enter band manually) —</option>
        ${engs.map(e=>`<option value="${e.engagement_id}" data-band="${e.inherent_band||''}" data-v="${e.vendor_id}">${esc(e.engagement_id)} · ${esc(e.title)} ${e.inherent_band?'· '+e.inherent_band:''}</option>`).join("")}</select></div>
    </div>
    <div class="card" id="con_manual"><div style="display:grid;grid-template-columns:1fr 1fr;gap:14px">
      <div class="field"><label>Inherent risk band</label><select id="con_band"><option>LOW</option><option selected>MODERATE</option><option>ELEVATED</option><option>HIGH</option></select></div>
      <div class="field"><label>Exposure flags</label><div style="display:flex;gap:12px;flex-wrap:wrap;padding-top:8px">
        ${[["personal_data","Personal data"],["cross_border","Cross-border"],["mission_critical","Mission-critical"],["regulated","Regulated"]].map(([k,l])=>`<label style="display:flex;align-items:center;gap:5px;font-weight:400;font-size:12px"><input type="checkbox" id="con_${k}" style="width:auto"> ${l}</label>`).join("")}</div></div></div>
      <p class="muted" style="font-size:11.5px;margin-top:8px">Manual entry is used for an <b>Other</b> (unregistered) entity. Selecting a registered engagement above inherits these automatically.</p></div>
    <div class="seg">${["min","rev","diff"].map(t=>`<button class="${_conTab===t?'on':''}" onclick="conTab('${t}')">${{min:"📋 Minimum terms",rev:"🔎 Gap review",diff:"📑 Existing vs to-add"}[t]}</button>`).join("")}</div>
    <div id="conBody"></div>`;
  conRender();
};
function conEngChange(){
  const sel=document.getElementById("con_eng"); const manual=document.getElementById("con_manual");
  const opt=sel.selectedOptions[0];
  if(sel.value){
    // registered: inherit, hide manual entry
    const band=opt.getAttribute("data-band");
    if(band){ const bs=document.getElementById("con_band"); if(bs) bs.value=band; }
    manual.style.display="none";
  } else {
    manual.style.display="";
  }
}
function conEngId(){ const s=document.getElementById("con_eng"); return s&&s.value?s.value:null; }
function conTab(t){ _conTab=t; conRender(); }
function conExposure(){ const e={}; ["personal_data","cross_border","mission_critical","regulated"].forEach(k=>{const el=document.getElementById("con_"+k); if(el&&el.checked)e[k]=true;}); return e; }
function conRender(){
  const el=document.getElementById("conBody");
  if(_conTab==="min"){
    el.innerHTML=`<div class="card"><div class="card-label">Tiered minimum terms — scaled to inherent risk &amp; exposure</div>
      <div class="tier-grid">${CONTRACT_TIERS.map(t=>`<div class="tier-card ${t.tone}"><div class="tier-no">TIER ${t.tier}</div><b>${esc(t.name)}</b><p>${esc(t.desc)}</p></div>`).join("")}</div>
      <button class="btn" style="margin-top:14px" onclick="conTerms()">📋 Generate minimum terms</button><div id="conTermsOut"></div></div>`;
    if(_conTerms) renderConTerms();
  } else if(_conTab==="rev"){
    el.innerHTML=`<div class="card"><div class="card-label">Gap review — upload a contract document <span class="muted">(AI extracts terms)</span> or paste text</div>
      <div class="field"><label>Upload contract document</label><input id="con_doc" type="file"></div>
      <button class="btn" onclick="conGapDoc()">📄 Read document &amp; review gaps</button>
      <div style="margin:14px 0;text-align:center;color:var(--mut);font-size:12px">— or —</div>
      <textarea id="con_text" rows="6" placeholder="Paste contract clauses / heads of terms here…"></textarea>
      <button class="btn ghost" style="margin-top:10px" onclick="conGap()">🔎 Review pasted text</button><div id="conGapOut"></div></div>`;
  } else if(_conTab==="diff"){
    el.innerHTML=`<div class="card"><div class="card-label">Existing vs to-add — upload the existing contract <span class="muted">(AI extracts terms)</span> or paste text</div>
      <div class="field"><label>Upload existing contract</label><input id="con_pdoc" type="file"></div>
      <button class="btn" onclick="conDiffDoc()">📄 Read document &amp; compare</button>
      <div style="margin:14px 0;text-align:center;color:var(--mut);font-size:12px">— or —</div>
      <textarea id="con_prior" rows="6" placeholder="Paste prior/existing contract text…"></textarea>
      <button class="btn ghost" style="margin-top:10px" onclick="conDiff()">📑 Compare pasted text</button><div id="conDiffOut"></div></div>`;
  }
}
async function _fileToB64(input){
  const f=input.files[0]; if(!f) return null;
  const b64=await new Promise((res,rej)=>{const r=new FileReader();r.onload=()=>res(r.result.split(",")[1]);r.onerror=rej;r.readAsDataURL(f);});
  return {filename:f.name,content_type:f.type||"application/octet-stream",data_b64:b64};
}
async function conGapDoc(){
  const file=await _fileToB64(document.getElementById("con_doc"));
  if(!file){ flash("Select a contract document"); return; }
  const body={file,engagement_id:conEngId(),inherent_band:val("con_band"),exposure:conExposure()};
  try{ const r=await api2("/contracts/gap-from-document",{method:"POST",body:JSON.stringify(body)});
    const g=r.gap_report;
    document.getElementById("conGapOut").innerHTML=`<div style="margin-top:12px">
      ${r.inherited_from_engagement?`<span class="pill ok">inherited ${esc(r.inherent_band)} from engagement</span> `:`<span class="pill mute">manual band ${esc(r.inherent_band)}</span> `}
      <a href="${esc(r.doc_link)}" target="_blank" class="pill info">view document</a>
      ${r.readable?'':' <span class="pill warn">document not machine-readable — gaps flagged conservatively</span>'}</div>
      <div style="margin-top:10px"><span class="pill ${g.critical_gaps?'crit':g.gaps.length?'warn':'ok'}">${esc(g.verdict)}</span></div>
      <table style="margin-top:10px"><tr><th>Gap</th><th>Tier</th><th>Severity</th><th>Basis</th></tr>
      ${g.gaps.map(x=>`<tr><td>${esc(x.clause)}</td><td>T${x.tier}</td><td><span class="pill ${x.severity==='Critical'?'crit':x.severity==='High'?'warn':'info'}">${esc(x.severity)}</span></td><td class="muted">${esc(x.basis)}</td></tr>`).join("")||'<tr><td colspan=4 class="muted">No gaps — all required terms present.</td></tr>'}</table>`;
  }catch(e){ flash(e.message); }
}
async function conDiffDoc(){
  const file=await _fileToB64(document.getElementById("con_pdoc"));
  if(!file){ flash("Select the existing contract document"); return; }
  // reuse gap-from-document to extract, then show present vs absent as existing/to-add
  const body={file,engagement_id:conEngId(),inherent_band:val("con_band"),exposure:conExposure()};
  try{ const r=await api2("/contracts/gap-from-document",{method:"POST",body:JSON.stringify(body)});
    const present=r.extracted_terms.present||[], gaps=r.gap_report.gaps||[];
    document.getElementById("conDiffOut").innerHTML=`<div style="margin-top:12px"><a href="${esc(r.doc_link)}" target="_blank" class="pill info">view document</a>
      ${r.readable?'':' <span class="pill warn">not machine-readable — conservative</span>'}</div>
      <div class="grid g2" style="margin-top:12px">
      <div class="card"><div class="card-label">✓ Terms detected in document (${present.length})</div>${present.map(t=>`<div class="dossier-row"><span class="dk">${esc(lbl(t))}</span><span class="dv">present</span></div>`).join("")||'<span class="muted">None detected</span>'}</div>
      <div class="card"><div class="card-label">+ Terms to be added (${gaps.length})</div>${gaps.map(t=>`<div class="dossier-row"><span class="dk">${esc(t.clause)}</span><span class="dv"><span class="pill ${t.severity==='Critical'?'crit':'warn'}">${esc(t.severity)}</span></span></div>`).join("")||'<span class="muted">None — fully covered</span>'}</div></div>`;
  }catch(e){ flash(e.message); }
}
async function conTerms(){
  const ep=entityPayload("con");
  try{ _conTerms=await api2("/contracts/terms",{method:"POST",body:JSON.stringify({inherent_band:val("con_band"),exposure:conExposure(),...ep})}); renderConTerms(); }
  catch(e){ flash(e.message); }
}
function renderConTerms(){
  const out=document.getElementById("conTermsOut"); if(!out)return;
  out.innerHTML=`<div style="margin-top:12px">${entityBadge(_conTerms.entity)} <span class="pill info">${_conTerms.count} terms · ${esc(_conTerms.inherent_band)}</span></div>
    <table style="margin-top:10px"><tr><th>Clause</th><th>Tier</th><th>Basis</th></tr>
    ${_conTerms.required_terms.map(t=>`<tr><td>${esc(t.name)}</td><td>T${t.tier}</td><td class="muted">${esc(t.basis)}</td></tr>`).join("")}</table>`;
}
async function conGap(){
  try{ _conGap=await api2("/contracts/gap-report",{method:"POST",body:JSON.stringify({contract_text:val("con_text"),inherent_band:val("con_band"),exposure:conExposure()})});
    document.getElementById("conGapOut").innerHTML=`<div style="margin-top:12px"><span class="pill ${_conGap.critical_gaps?'crit':_conGap.gaps.length?'warn':'ok'}">${esc(_conGap.verdict)}</span></div>
      <table style="margin-top:10px"><tr><th>Gap</th><th>Tier</th><th>Severity</th><th>Basis</th></tr>
      ${_conGap.gaps.map(g=>`<tr><td>${esc(g.clause)}</td><td>T${g.tier}</td><td><span class="pill ${g.severity==='Critical'?'crit':g.severity==='High'?'warn':'info'}">${esc(g.severity)}</span></td><td class="muted">${esc(g.basis)}</td></tr>`).join("")||'<tr><td colspan=4 class="muted">No gaps — all required terms present.</td></tr>'}</table>`;
  }catch(e){ flash(e.message); }
}
async function conDiff(){
  try{ _conDiff=await api2("/contracts/diff",{method:"POST",body:JSON.stringify({inherent_band:val("con_band"),exposure:conExposure(),prior_contract_texts:[val("con_prior")]})});
    document.getElementById("conDiffOut").innerHTML=`<div class="grid g2" style="margin-top:12px">
      <div class="card"><div class="card-label">✓ Terms already existing (${_conDiff.terms_already_existing.length})</div>${_conDiff.terms_already_existing.map(t=>`<div class="dossier-row"><span class="dk">${esc(t.clause)}</span><span class="dv">T${t.tier}</span></div>`).join("")||'<span class="muted">None detected</span>'}</div>
      <div class="card"><div class="card-label">+ Terms to be added (${_conDiff.terms_to_be_added.length})</div>${_conDiff.terms_to_be_added.map(t=>`<div class="dossier-row"><span class="dk">${esc(t.clause)}</span><span class="dv"><span class="pill ${t.severity==='Critical'?'crit':'warn'}">${esc(t.severity)}</span></span></div>`).join("")||'<span class="muted">None — fully covered</span>'}</div></div>`;
  }catch(e){ flash(e.message); }
}

/* ============ REQ 1 — Vendor Master record ============ */
let _vmId=null, _vmData={};
const VM_GROUPS=[
  ["Identifiers & keys",[["vendor_id","Vendor ID",1],["lei","LEI"],["euid","EUID"],["duns","D-U-N-S"],["registration_number","Reg. number"],["erp_id","ERP ID"],["sourcing_id","Sourcing ID"],["grc_id","GRC ID"],["group_id","Group ID",1]]],
  ["Legal identity",[["legal_name","Legal name"],["trading_name","Trading name"],["dba_names","DBA names"],["previous_names","Previous names"],["legal_form","Entity type"],["incorporation_country","Country of incorp."],["incorporation_date","Date of incorp."],["operating_status","Operating status"]]],
  ["Corporate structure & ownership",[["immediate_parent","Immediate parent"],["ultimate_parent","Ultimate parent",1],["subsidiaries","Subsidiaries"],["ownership_type","Ownership type"],["listing_status","Listing status",1],["ticker","Ticker"],["exchange","Exchange"]]],
  ["Classification & segmentation",[["sic_code","SIC code"],["unspsc_code","UNSPSC"],["nace_naics","NACE/NAICS"],["supplier_category","Supplier category"],["segmentation","Segmentation"],["tier","Tier"],["spend_band","Spend band"],["substitutability","Substitutability"]]],
  ["Relationship & internal ownership",[["relationship_owner","Relationship owner"],["sponsoring_bu","Sponsoring BU"],["cost_centre","Cost centre"],["strategic_importance","Strategic importance"],["business_dependency","Business dependency"],["relationship_health","Relationship health"]]],
  ["Addresses & geography",[["hq_address","HQ address",1],["billing_address","Billing address"],["remittance_address","Remittance address"],["operating_address","Operating address"],["service_countries","Service countries"],["data_locations","Data locations"],["geopolitical_risk","Geopolitical risk"],["sanctions_jurisdiction_exposure","Sanctions/jurisdiction exposure"]]],
  ["Financial & commercial",[["currency","Currency"],["payment_terms","Payment terms",1],["payment_method","Payment method"],["credit_limit","Credit limit"],["annual_spend","Annual spend"],["spend_trend","Spend trend"],["discount_terms","Discount terms"],["credit_rating","Credit rating"],["credit_rating_date","Rating date"],["financial_health_band","Fin-health band (rollup)"],["going_concern_flag","Going-concern flag"]]],
  ["Tax & regulatory",[["tax_id","Tax ID"],["vat_number","VAT number"],["w_form_status","W-8/W-9 status"],["tax_residency","Tax residency"],["regulatory_licences","Licences held"],["regulated_entity","Regulated entity"]]],
];
const VM_BANK=[["bank_account_name","Account name"],["iban","IBAN / account"],["swift_bic","SWIFT/BIC"],["routing_number","Routing"],["bank_verified","Verified"],["bank_verified_date","Verified date"],["bank_change_locked","Change-locked (dual-approve)"]];
async function openVendorMaster(vid){ _vmId=vid; try{ _vmData=await api2("/vendor-master/"+vid); }catch(e){ flash(e.message); return; } document.querySelectorAll('.nav a').forEach(a=>a.classList.remove('active')); renderVendorMaster(); }
function vmField(k,label,readonly){
  const v=_vmData[k]; const boolish=(k.endsWith("_flag")||k==="going_concern_flag"||k==="regulated_entity"||k==="sole_source"||k==="bank_verified"||k==="bank_change_locked");
  if(readonly) return `<div class="field"><label>${esc(label)}</label><input value="${v==null?'':esc(String(v))}" disabled style="background:#f1efe8"></div>`;
  if(boolish) return `<div class="field"><label>${esc(label)}</label><select id="vm_${k}"><option value="false" ${!v?'selected':''}>No</option><option value="true" ${v?'selected':''}>Yes</option></select></div>`;
  // CR-7: controlled vocabulary dropdown
  if(VOCAB[k]){
    return `<div class="field"><label>${esc(label)}</label><select id="vm_${k}"><option value="">— select —</option>${VOCAB[k].map(o=>`<option ${String(v)===o?'selected':''}>${esc(o)}</option>`).join("")}</select></div>`;
  }
  // CR-8: typed input (country/date/email/phone) where applicable
  if(fieldType(k)!=="text"){
    return `<div class="field"><label>${esc(label)}</label>${typedInput("vm_"+k,k,v)}</div>`;
  }
  return `<div class="field"><label>${esc(label)}</label><input id="vm_${k}" value="${v==null?'':esc(String(v))}"></div>`;
}
function renderVendorMaster(){
  const view=document.getElementById("view");
  const canBank = _vmData.iban!==undefined || _vmData.banking!=="restricted";
  view.innerHTML=`<div class="top"><div><h1>Vendor Master</h1><div class="sub">${esc(_vmData.legal_name||'')} · ${esc(_vmId)}</div></div>
    <div><button class="btn ghost" onclick="V.vendors()">← Register</button><button class="btn ghost" onclick="openVendorAttributes('${_vmId}')">🛡 Risk attributes</button><button class="btn ghost" onclick="openV360('${_vmId}')">◎ Vendor 360</button><button class="btn" onclick="saveVendorMaster()">Save master</button></div></div>
    <div class="crit-band ${_vmData.is_critical?'on':''}">
      <div><span class="crit-band-label">Critical vendor</span>
        <span class="crit-band-sub">${_vmData.criticality_reason?esc(_vmData.criticality_reason):'Set whether this vendor is business-critical'}</span></div>
      <div class="crit-toggle">
        <button class="crit-opt ${_vmData.is_critical?'sel':''}" onclick="vmSetCritical(true)">Yes</button>
        <button class="crit-opt ${_vmData.is_critical===false||_vmData.is_critical==null?'sel':''}" onclick="vmSetCritical(false)">No</button>
      </div></div>
    ${VM_GROUPS.map(([title,fields])=>`<div class="sec-h"><h2 style="font-size:14px">${esc(title)}</h2><div class="rule"></div></div>
      <div class="card"><div class="grid g3">${fields.map(([k,l,ro])=>vmField(k,l,ro)).join("")}</div></div>`).join("")}
    <div class="sec-h"><h2 style="font-size:14px">Ultimate beneficial owners</h2><div class="rule"></div></div>
    <div class="card"><div id="vm_ubo">${(_vmData.ubo||[]).map((o,i)=>`<div class="dossier-row"><span class="dk">${esc(o.name)}</span><span class="dv">${esc(String(o.pct||''))}% <button class="btn sm ghost" onclick="vmDelUbo(${i})">×</button></span></div>`).join("")||'<span class="muted">None recorded</span>'}</div>
      <div class="grid g3" style="margin-top:8px"><div class="field"><label>UBO name</label><input id="vm_ubo_n"></div><div class="field"><label>Ownership %</label><input id="vm_ubo_p" type="number"></div><div class="field"><label>&nbsp;</label><button class="btn ghost sm" onclick="vmAddUbo()">+ Add UBO</button></div></div></div>
    <div class="sec-h"><h2 style="font-size:14px">Banking & payment ${canBank?'<span class="pill warn" style="margin-left:8px">sensitive</span>':'<span class="pill mute" style="margin-left:8px">restricted — elevated permission required</span>'}</h2><div class="rule"></div></div>
    <div class="card">${canBank?`<div class="grid g3">${VM_BANK.map(([k,l])=>vmField(k,l)).join("")}</div>`:'<span class="muted">Banking fields are hidden for your role.</span>'}</div>`;
}
let _vmUbo=null;
function vmAddUbo(){ _vmUbo=_vmUbo||(_vmData.ubo||[]); const n=val("vm_ubo_n"),p=val("vm_ubo_p"); if(!n)return; _vmData.ubo=[...(_vmData.ubo||[]),{name:n,pct:parseFloat(p)||0}]; renderVendorMaster(); }
function vmDelUbo(i){ _vmData.ubo.splice(i,1); renderVendorMaster(); }
async function vmSetCritical(flag){
  if(_vmData.is_critical===flag) return;
  let reason="";
  if(flag){ reason=prompt("Reason for marking this vendor critical:","Business-critical service")||"Business-critical"; }
  else { reason=prompt("Reason for marking this vendor NOT critical:","Compensating controls in place")||"Not critical"; }
  try{ await api2("/critical-vendors/"+_vmId+"/override",{method:"POST",body:JSON.stringify({is_critical:flag,reason})});
    _vmData=await api2("/vendor-master/"+_vmId); flash("Criticality updated"); renderVendorMaster();
  }catch(e){ flash(e.message); } }

async function saveVendorMaster(){
  const data={}; document.querySelectorAll('[id^="vm_"]').forEach(el=>{ const k=el.id.slice(3); if(["ubo_n","ubo_p"].includes(k))return; let v=el.value; if(v==="true")v=true; else if(v==="false")v=false; data[k]=v; });
  data.ubo=_vmData.ubo||[];
  const incBank = _vmData.banking!=="restricted";
  try{ _vmData=await api2("/vendor-master/"+_vmId,{method:"PUT",body:JSON.stringify({data,include_bank:incBank})}); flash("Master saved"); renderVendorMaster(); }catch(e){ flash(e.message); }
}

/* ============ REQ 2 — Vendor Attributes ============ */
let _vaId=null, _vaData={}, _vaTab="screening";
const SCREEN_LABELS={sanctions:"Sanctions",pep:"PEP",adverse_media:"Adverse media",abac:"ABAC",debarment:"Debarment",modern_slavery:"Modern slavery",coi:"Conflict of interest"};
async function openVendorAttributes(vid){ _vaId=vid; _vaTab="screening"; try{ _vaData=await api2("/vendor-attributes/"+vid); }catch(e){ flash(e.message); return; } renderVendorAttributes(); }
function renderVendorAttributes(){
  const view=document.getElementById("view");
  view.innerHTML=`<div class="top"><div><h1>Vendor Risk Attributes</h1><div class="sub">${esc(_vaId)}</div></div>
    <div><button class="btn ghost" onclick="V.vendors()">← Register</button><button class="btn" onclick="vaRefresh()">↻ Refresh rollups</button></div></div>
    <div class="seg">${["screening","privacy","cyber","resilience","esg","insurance","monitoring","risk","governance"].map(t=>`<button class="${_vaTab===t?'on':''}" onclick="vaTab('${t}')">${({screening:"Screening",privacy:"Privacy",cyber:"Cyber",resilience:"Resilience",esg:"ESG",insurance:"Insurance",monitoring:"Monitoring",risk:"Risk profile",governance:"Governance"})[t]}</button>`).join("")}</div>
    <div id="vaBody"></div>`;
  vaRenderBody();
}
function vaTab(t){ _vaTab=t; vaRenderBody(); document.querySelectorAll('.seg button').forEach(b=>b.classList.toggle('on', b.textContent.toLowerCase().startsWith(t.slice(0,4)))); }
function vaRenderBody(){
  const el=document.getElementById("vaBody"); const d=_vaData;
  if(_vaTab==="screening"){
    el.innerHTML=`<div class="card"><div class="card-label">Integrity screening — result · date · next-due</div>
      <table><tr><th>Type</th><th>Result</th><th>Detail</th><th>Screened</th><th>Next due</th><th></th></tr>
      ${d.screening.map(x=>`<tr><td>${esc(SCREEN_LABELS[x.screen_type]||x.screen_type)}</td>
        <td>${x.result?`<span class="pill ${x.result==='clear'||x.result==='on-file'?'ok':x.result==='hit'?'crit':'warn'}">${esc(x.result)}</span>`:'<span class="muted">—</span>'}</td>
        <td class="muted">${esc(x.detail||'')}</td><td>${esc(x.screened_date||'—')}</td>
        <td>${x.next_due?`${esc(x.next_due)} ${x.overdue?'<span class="pill crit">overdue</span>':''}`:'—'}</td>
        <td><button class="btn sm ghost" onclick="vaScreenEdit('${x.screen_type}')">edit</button></td></tr>`).join("")}</table></div>`;
  } else if(_vaTab==="insurance"){
    el.innerHTML=`<div class="card"><div class="card-label">Insurance policies</div>
      ${(d.insurance||[]).map(p=>`<div class="dossier-row"><span class="dk">${esc(p.policy_type)} · ${esc(p.insurer||'')}</span><span class="dv">${p.coverage_limit?esc(String(p.coverage_limit)):'—'} ${esc(p.currency||'')} · exp ${esc(p.certificate_expiry||'—')}</span></div>`).join("")||'<span class="muted">No policies</span>'}
      <div class="grid g3" style="margin-top:10px"><div class="field"><label>Policy type</label><select id="ins_t"><option>professional_indemnity</option><option>cyber</option><option>public_liability</option></select></div>
      <div class="field"><label>Coverage limit</label><input id="ins_l" type="number"></div><div class="field"><label>Insurer</label><input id="ins_i"></div></div>
      <div class="grid g2"><div class="field"><label>Currency</label><input id="ins_c" value="GBP"></div><div class="field"><label>Expiry</label><input id="ins_e" placeholder="YYYY-MM-DD"></div></div>
      <button class="btn ghost sm" style="margin-top:8px" onclick="vaAddInsurance()">+ Add policy</button></div>`;
  } else if(_vaTab==="monitoring"){
    el.innerHTML=`<div class="card"><div class="card-label">Continuous-monitoring signals — value · source · freshness (time-series)</div>
      <table><tr><th>Signal</th><th>Value</th><th>Source</th><th>Captured</th></tr>
      ${(d.monitor_signals||[]).map(s=>`<tr><td>${esc(s.signal_type)}</td><td><b>${esc(s.value||'')}</b></td><td class="muted">${esc(s.source||'')}</td><td>${esc(s.captured_at||'')}</td></tr>`).join("")||'<tr><td colspan=4 class="muted">No signals captured</td></tr>'}</table>
      <div class="grid g3" style="margin-top:10px"><div class="field"><label>Signal</label><select id="sig_t"><option>cyber_rating</option><option>financial_health</option><option>sanctions_media</option><option>news_sentiment</option><option>breach</option></select></div>
      <div class="field"><label>Value</label><input id="sig_v"></div><div class="field"><label>Source</label><input id="sig_s"></div></div>
      <button class="btn ghost sm" style="margin-top:8px" onclick="vaAddSignal()">+ Capture signal</button></div>`;
  } else if(_vaTab==="risk"){
    const r=d.risk_profile;
    el.innerHTML=`<div class="card"><div class="card-label">Risk profile (rollup, time-versioned)</div>
      ${r?`<div class="grid g4">
        <div class="card stat"><div class="v">${r.inherent_band||'—'}</div><div class="l">Inherent</div></div>
        <div class="card stat"><div class="v">${r.residual_band||'—'}</div><div class="l">Residual</div></div>
        <div class="card stat"><div class="v">${r.open_findings}</div><div class="l">Open findings</div></div>
        <div class="card stat"><div class="v">${r.max_severity||'—'}</div><div class="l">Max severity</div></div></div>
        <p class="muted" style="margin-top:10px">Last assessment: ${esc(r.last_assessment||'—')} · snapshot ${esc((r.snapshot_at||'').slice(0,10))}</p>`
        :'<span class="muted">No rollup yet — press “Refresh rollups”.</span>'}</div>`;
  } else {
    // generic domain editor (privacy/cyber/resilience/esg/governance)
    const domD=d[_vaTab]||{};
    const skip=new Set(["id","vendor_id","updated_at","certifications_json","nth_party_json","record_version","snapshot_at"]);
    const keys=Object.keys(domD).filter(k=>!skip.has(k));
    el.innerHTML=`<div class="card"><div class="card-label">${_vaTab[0].toUpperCase()+_vaTab.slice(1)} attributes</div>
      ${keys.length?`<div class="grid g3">${keys.map(k=>{const v=domD[k];const isBool=typeof v==="boolean";return `<div class="field"><label>${esc(lbl(k))}</label>${isBool?`<select id="dm_${k}"><option value="false" ${!v?'selected':''}>No</option><option value="true" ${v?'selected':''}>Yes</option></select>`:(fieldType(k)!=="text"?typedInput("dm_"+k,k,v):`<input id="dm_${k}" value="${v==null?'':esc(String(v))}">`)}</div>`;}).join("")}</div>`:'<span class="muted">No fields yet — fill and save to create.</span>'}
      ${_vaTab==="cyber"?`<p class="muted" style="margin-top:8px">Certifications roll up from the Artefact register automatically.</p>`:''}
      ${_vaTab==="resilience"?`<p class="muted" style="margin-top:8px">nth-party dependency tree is stored as structured JSON (set via API/import).</p>`:''}
      <button class="btn" style="margin-top:10px" onclick="vaSaveDomain('${_vaTab}')">Save ${_vaTab}</button></div>`;
  }
}
function vaScreenEdit(t){ modal(`<h3>Screening — ${esc(SCREEN_LABELS[t]||t)}</h3>
  <div class="field"><label>Result</label><select id="sc_r"><option value="">—</option><option>clear</option><option>hit</option><option>review</option><option>on-file</option><option>not-checked</option></select></div>
  <div class="field"><label>Detail (lists checked / notes)</label><input id="sc_d"></div>
  <div class="grid g2"><div class="field"><label>Screened date</label><input id="sc_sd" placeholder="YYYY-MM-DD"></div><div class="field"><label>Next due</label><input id="sc_nd" placeholder="YYYY-MM-DD"></div></div>
  <div class="row"><button class="btn ghost" onclick="closeModal()">Cancel</button><button class="btn" onclick="vaSaveScreen('${t}')">Save</button></div>`); }
async function vaSaveScreen(t){ try{ await api2(`/vendor-attributes/${_vaId}/screening`,{method:"POST",body:JSON.stringify({screen_type:t,result:val("sc_r")||null,detail:val("sc_d")||null,screened_date:val("sc_sd")||null,next_due:val("sc_nd")||null})}); closeModal(); _vaData=await api2("/vendor-attributes/"+_vaId); renderVendorAttributes(); flash("Screening saved"); }catch(e){ flash(e.message); } }
async function vaSaveDomain(dom){ const data={}; document.querySelectorAll('[id^="dm_"]').forEach(el=>{ let v=el.value; if(v==="true")v=true;else if(v==="false")v=false; data[el.id.slice(3)]=v; }); try{ _vaData=await api2(`/vendor-attributes/${_vaId}/domain/${dom}`,{method:"POST",body:JSON.stringify({data})}); flash(dom+" saved"); renderVendorAttributes(); }catch(e){ flash(e.message); } }
async function vaAddInsurance(){ try{ await api2(`/vendor-attributes/${_vaId}/insurance`,{method:"POST",body:JSON.stringify({policy_type:val("ins_t"),coverage_limit:parseFloat(val("ins_l"))||null,insurer:val("ins_i"),currency:val("ins_c"),certificate_expiry:val("ins_e")})}); _vaData=await api2("/vendor-attributes/"+_vaId); renderVendorAttributes(); flash("Policy added"); }catch(e){ flash(e.message); } }
async function vaAddSignal(){ try{ await api2(`/vendor-attributes/${_vaId}/monitor-signal`,{method:"POST",body:JSON.stringify({signal_type:val("sig_t"),value:val("sig_v"),source:val("sig_s")})}); _vaData=await api2("/vendor-attributes/"+_vaId); renderVendorAttributes(); flash("Signal captured"); }catch(e){ flash(e.message); } }
async function vaRefresh(){ try{ await api2(`/vendor-attributes/${_vaId}/refresh-rollups`,{method:"POST",body:"{}"}); _vaData=await api2("/vendor-attributes/"+_vaId); flash("Rollups refreshed"); renderVendorAttributes(); }catch(e){ flash(e.message); } }

/* ============ REQ 3 — Engagement Register (full record) ============ */
let _erId=null, _erData={}, _erTab="contract";
const ER_GROUPS={
  origination:["business_justification","requested_by","procurement_category","sourcing_route","competitive_flag","competitive_rationale","requisition_ref","business_case_ref"],
  contract:["contract_reference","agreement_type","signatories","governing_law","governing_language","execution_date","effective_date","initial_term","renewal_type","renewal_window","notice_period","termination_rights","cure_period","change_of_control","assignment_rights","clause_flags","contract_status","contract_doc_link","contract_version"],
  scope:["scope_in","scope_out","objectives","assumptions","dependencies","delivery_location","receiving_location","delivery_locations","change_control_ref"],
  service:["service_type","supported_function","function_criticality","ict_flag","integration_points"],
  financial:["tcv","acv","pricing_model","rate_card","indexation_terms","payment_terms","invoicing_frequency","discounts","fx_terms","budget_allocation","po_numbers","goods_receipt_ref","invoice_refs","committed_spend","actual_spend"],
  governance:["engagement_owner","vendor_account_manager","governance_forum","governance_cadence","escalation_path","raci","relationship_sentiment","performance_reporting_cadence"],
  risk:["data_classification","data_volume","personal_data","data_subject_types","system_access","physical_access","mission_critical","cross_border","regulated_activity","fourth_party_reliance","concentration_contribution"],
  resilience:["rto","rpo","bcp_dependency","exit_plan","exit_plan_tested","transition_in_status","alternative_provider"],
  compliance:["dpa_in_place","audit_rights","audit_last_exercised","required_clauses_present","insurance_evidenced","regulatory_notifications"],
  lifecycle:["engagement_stage","approval_status","approver","approval_date","go_live_date","next_review_date","review_cadence","renewal_decision","renewal_decision_date","end_date","end_reason","transition_status"],
};
async function openEngagementRegister(eid){ _erId=eid; _erTab="contract"; try{ _erData=await api2("/engagement-register/"+eid); }catch(e){ flash(e.message); return; } renderEngReg(); }
function renderEngReg(){
  const view=document.getElementById("view"); const b=_erData.base||{};
  const tabs=["origination","contract","scope","service","financial","governance","risk","resilience","compliance","lifecycle","children"];
  view.innerHTML=`<div class="top"><div><h1>Engagement Register</h1><div class="sub">${esc(b.engagement_id||'')} · ${esc(b.title||'')} · vendor ${esc(b.vendor_id||'')}</div></div>
    <div><button class="btn ghost" onclick="V.engagements()">← Engagements</button>${_erTab!=='children'?`<button class="btn" onclick="saveEngReg()">Save</button>`:''}</div></div>
    <div class="crit-band ${b.is_critical?'on':''}">
      <div><span class="crit-band-label">Critical engagement</span>
        <span class="crit-band-sub">Inherent ${esc(b.inherent_band||'—')} · residual ${esc(b.residual_band||'—')} — set whether this engagement is business-critical</span></div>
      <div class="crit-toggle">
        <button class="crit-opt ${b.is_critical?'sel':''}" onclick="erSetCritical(true)">Yes</button>
        <button class="crit-opt ${!b.is_critical?'sel':''}" onclick="erSetCritical(false)">No</button>
      </div></div>
    <div class="seg">${tabs.map(t=>`<button class="${_erTab===t?'on':''}" onclick="erTab('${t}')">${t[0].toUpperCase()+t.slice(1)}</button>`).join("")}</div>
    <div id="erBody"></div>`;
  erRenderBody();
}
async function erSetCritical(flag){
  const b=_erData.base||{}; if(!!b.is_critical===flag) return;
  const reason=prompt(flag?"Reason for marking this engagement critical:":"Reason for marking NOT critical:", flag?"Business-critical engagement":"Not critical")||"manual";
  try{ await api2("/engagements/"+_erId+"/criticality-override",{method:"POST",body:JSON.stringify({is_critical:flag,reason})});
    _erData=await api2("/engagement-register/"+_erId); flash("Criticality updated"); renderEngReg();
  }catch(e){ flash(e.message); } }
function erTab(t){ _erTab=t; renderEngReg(); }
function erRenderBody(){
  const el=document.getElementById("erBody"); const ext=_erData.ext||{};
  if(_erTab==="children"){
    el.innerHTML=["deliverables","milestones","slas","obligations","personnel"].map(kind=>{
      const rows=_erData[kind]||[];
      return `<div class="sec-h"><h2 style="font-size:13px">${kind[0].toUpperCase()+kind.slice(1)} (${rows.length})</h2><div class="rule"></div></div>
        <div class="card">${rows.map(r=>`<div class="dossier-row"><span class="dk">${esc(r.description||r.name||r.metric||'')}</span><span class="dv">${esc(r.due_date||r.target||r.role||r.status||'')} <button class="btn sm ghost" onclick="erDelChild('${kindSingular(kind)}',${r.id})">×</button></span></div>`).join("")||'<span class="muted">None</span>'}
        <button class="btn ghost sm" style="margin-top:8px" onclick="erAddChild('${kindSingular(kind)}')">+ Add ${kindSingular(kind)}</button></div>`;
    }).join("");
    return;
  }
  const fields=ER_GROUPS[_erTab]||[];
  let contractsPanel="";
  if(_erTab==="contract"){
    contractsPanel=`<div class="sec-h" style="margin-top:14px"><h2 style="font-size:13px">Linked contract records</h2><div class="rule"></div></div>
      <div class="card" id="erContracts"><span class="muted">Loading…</span></div>`;
  }
  el.innerHTML=`<div class="card"><div class="grid g3">${fields.map(k=>{const v=ext[k];const isBool=typeof v==="boolean";return `<div class="field"><label>${esc(lbl(k))}</label>${isBool?`<select id="er_${k}"><option value="false" ${!v?'selected':''}>No</option><option value="true" ${v?'selected':''}>Yes</option></select>`:(fieldType(k)!=="text"?typedInput("er_"+k,k,v):`<input id="er_${k}" value="${v==null?'':esc(String(v))}">`)}</div>`;}).join("")}</div></div>${contractsPanel}`;
  if(_erTab==="contract") erLoadContracts();
}
async function erLoadContracts(){
  const host=document.getElementById("erContracts"); if(!host) return;
  const b=_erData.base||{};
  try{
    const list=await api2("/contracts?engagement_id="+_erId);
    host.innerHTML=`${list.length?`<table><tr><th>Contract ID</th><th>Type</th><th>Primary link</th><th>Parent MSA</th><th>Status</th><th>Critical</th></tr>
      ${list.map(c=>`<tr><td><b>${esc(c.contract_id)}</b></td><td>${esc(c.contract_type)}</td><td>${esc(c.primary_link)}</td>
        <td>${esc(c.parent_msa||'—')}</td><td><span class="tag">${esc(c.status||'draft')}</span></td>
        <td>${c.is_critical?'<span class="tag crit">CRITICAL</span>':'—'}</td></tr>`).join("")}</table>`
      :'<span class="muted">No first-class contract records linked yet.</span>'}
    <div class="row" style="margin-top:10px;gap:8px">
      <button class="btn ghost sm" onclick="erSyncContract()">Sync from fields above</button>
      <button class="btn ghost sm" onclick="erNewContract('${esc(b.vendor_id||'')}')">+ New contract record</button></div>`;
  }catch(e){ host.innerHTML=`<span class="err">${esc(e.message)}</span>`; }
}
async function erSyncContract(){ try{ const r=await api2("/engagement-register/"+_erId+"/sync-contract",{method:"POST",body:"{}"}); flash(r.synced?("Synced "+r.contract_id):("Not synced: "+(r.reason||""))); erLoadContracts(); }catch(e){ flash(e.message); } }
function erNewContract(vid){ modal(`<h3>New contract record</h3>
  <div class="field"><label>Type</label><select id="ct_type"><option>Contract</option><option>MSA</option><option>SOW</option><option>PO</option><option>Order</option><option>NDA</option><option>DPA</option><option>Framework</option><option>Amendment</option></select></div>
  <div class="field"><label>Title</label><input id="ct_title"></div>
  <p class="muted" style="font-size:12px">MSA/Framework link to the vendor; Contract/PO/SOW link to this engagement.</p>
  <div class="row"><button class="btn ghost" onclick="closeModal()">Cancel</button><button class="btn" onclick="erSaveContract('${vid}')">Create</button></div>`); }
async function erSaveContract(vid){ const type=val("ct_type"); const master=["MSA","Framework","Master"].includes(type);
  const body=master?{contract_type:type,vendor_id:vid,data:{title:val("ct_title")}}:{contract_type:type,engagement_id:_erId,data:{title:val("ct_title")}};
  try{ await api2("/contracts",{method:"POST",body:JSON.stringify(body)}); closeModal(); flash("Contract created"); erLoadContracts(); }catch(e){ flash(e.message); } }
function kindSingular(k){ return ({deliverables:"deliverable",milestones:"milestone",slas:"sla",obligations:"obligation",personnel:"personnel"})[k]; }
async function saveEngReg(){ const data={}; document.querySelectorAll('[id^="er_"]').forEach(el=>{ let v=el.value; if(v==="true")v=true;else if(v==="false")v=false; if(["tcv","acv","committed_spend","actual_spend"].includes(el.id.slice(3)))v=parseFloat(v)||null; data[el.id.slice(3)]=v; }); try{ _erData=await api2("/engagement-register/"+_erId,{method:"PUT",body:JSON.stringify({data})}); flash("Engagement saved"); renderEngReg(); }catch(e){ flash(e.message); } }
function erAddChild(kind){
  const f={deliverable:[["description","Description"],["due_date","Due date"],["acceptance_criteria","Acceptance"],["accountable_owner","Owner"]],
    milestone:[["name","Name"],["due_date","Due date"],["payment_trigger","Payment trigger"]],
    sla:[["metric","Metric"],["target","Target"],["measurement_window","Window"],["credit_penalty","Credit/penalty"]],
    obligation:[["description","Description"],["obl_type","Type"],["obligated_party","Party"],["due_date","Due date"],["accountable_owner","Owner"]],
    personnel:[["name","Name"],["role","Role"],["vetting_status","Vetting"],["access_level","Access level"],["location","Location"]]}[kind];
  modal(`<h3>Add ${kind}</h3>${f.map(([k,l])=>`<div class="field"><label>${esc(l)}</label><input id="ec_${k}"></div>`).join("")}
    <div class="row"><button class="btn ghost" onclick="closeModal()">Cancel</button><button class="btn" onclick="erSaveChild('${kind}')">Add</button></div>`);
}
async function erSaveChild(kind){ const data={}; document.querySelectorAll('[id^="ec_"]').forEach(el=>{ if(el.value)data[el.id.slice(3)]=el.value; }); try{ await api2(`/engagement-register/${_erId}/child`,{method:"POST",body:JSON.stringify({kind,data})}); closeModal(); _erData=await api2("/engagement-register/"+_erId); renderEngReg(); flash(kind+" added"); }catch(e){ flash(e.message); } }
async function erDelChild(kind,cid){ try{ await api2(`/engagement-register/${_erId}/child/${kind}/${cid}`,{method:"DELETE"}); _erData=await api2("/engagement-register/"+_erId); renderEngReg(); }catch(e){ flash(e.message); } }

/* ---------- Vendor 360 dashboard ---------- */
V.vendor360=async()=>{
  const view=document.getElementById("view");
  view.innerHTML=`<div class="top"><div><h1>Vendor 360</h1>
    <div class="sub">Single-pane synthesis · correlated internal & external signals</div></div></div>
    <div id="v360Body" class="muted">Loading portfolio…</div>`;
  try{
    const port = await api2("/vendor360/portfolio");
    if(!port.length){ view.querySelector("#v360Body").innerHTML=`<div class="card muted">No vendors yet. Register a vendor to see its 360 view.</div>`; return; }
    view.querySelector("#v360Body").innerHTML=`
      <div class="port-row" style="background:#f6f4ec;cursor:default;font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:#7a8c84;font-weight:700">
        <div>Vendor</div><div>Tier</div><div>Posture</div><div>Residual</div><div style="text-align:right">Findings</div></div>
      ${port.map(p=>`<div class="port-row" onclick="openV360('${p.vendor_id}')">
        <div><b>${esc(p.legal_name)}</b> ${p.is_critical?'<span class="v360-crit" style="position:static;display:inline-block;padding:2px 7px;font-size:9px;margin-left:6px">CRITICAL</span>':''}<div class="muted" style="font-size:11px">${esc(p.vendor_id)}</div></div>
        <div class="muted">${esc(p.tier||'—')}</div>
        <div><span class="posture-pill pp-${p.posture_level}">${esc(p.posture)}</span></div>
        <div>${p.residual?`<span class="band ${p.residual}">${p.residual}</span>`:'<span class="muted">—</span>'}</div>
        <div style="text-align:right;font-weight:600">${p.open_findings}</div></div>`).join("")}`;
  }catch(e){ view.querySelector("#v360Body").innerHTML=`<div class="err">${esc(e.message)}</div>`; }
};

async function openV360(vid){
  const view=document.getElementById("view");
  document.querySelectorAll('.nav a').forEach(a=>a.classList.remove('active'));
  view.innerHTML=`<div class="muted">Compiling 360 view…</div>`;
  let d, attr={}; try{ d = await api2("/vendor360/"+vid); }catch(e){ view.innerHTML=`<div class="err">${esc(e.message)}</div>`; return; }
  try{ attr = await api2("/vendor-attributes/"+vid); }catch(e){ attr={}; }
  const dim=d.dimensions, pl=d.posture.level;
  const fmtMoney=n=>n?("$"+Number(n).toLocaleString()):"—";
  const exc=d.exceptions||[];
  view.innerHTML=`
    <div class="top"><div><h1 style="font-size:20px">Vendor 360</h1></div>
      <div><button class="btn ghost" onclick="V.vendor360()">← Portfolio</button>
        <button class="btn ghost" onclick="openVendorAttributes('${vid}')">Risk attributes</button></div></div>

    <div class="v360-hero">
      ${d.is_critical?`<div class="v360-crit">CRITICAL VENDOR</div>`:''}
      <div class="vname">${esc(d.legal_name)}</div>
      <div class="vmeta">${esc(vid)} · ${esc(d.tier||'Untiered')}${d.ultimate_parent?' · parent '+esc(d.ultimate_parent):''}</div>
      <div class="v360-verdict">
        <div class="v360-dot l${pl}"></div>
        <div><div class="v360-vlabel">${esc(d.posture.label)}</div>
          <div class="v360-vsub">Consolidated posture · residual ${esc(d.posture.band||'—')} · reconciled with risk profile</div></div>
      </div>
    </div>

    <div class="v360-dims">
      <div class="v360-dim"><div class="dv">${dim.risk.residual||dim.risk.inherent||'—'}</div><div class="dl">Risk</div></div>
      <div class="v360-dim"><div class="dv">${dim.financial.band||'—'}</div><div class="dl">Financial</div></div>
      <div class="v360-dim"><div class="dv">${dim.reputation.summary?'●':'—'}</div><div class="dl">Reputation</div></div>
      <div class="v360-dim"><div class="dv">${dim.monitoring.signal||'—'}</div><div class="dl">Monitoring</div></div>
      <div class="v360-dim"><div class="dv">${dim.performance.score!=null?dim.performance.score:'—'}</div><div class="dl">Performance</div></div>
      <div class="v360-dim"><div class="dv">${dim.compliance.open_findings}</div><div class="dl">Findings</div></div>
    </div>

    <div class="v360-grid">
      <div class="v360-panel"><h3>⚠ Ranked exceptions (${d.exception_count})</h3>
        ${exc.length?exc.map(x=>`<div class="v360-exc"><span class="v360-sevdot sev-${x.severity}"></span>
          <span style="flex:1">${esc(x.detail)}</span><span class="muted" style="font-size:11px">${esc(x.type.replace(/_/g,' '))}</span></div>`).join(""):'<div class="muted">No exceptions — clean posture.</div>'}
      </div>
      <div class="v360-panel"><h3>Concentration & dependency</h3>
        <div class="v360-metric"><span class="mk">Engagements</span><span class="mv">${d.concentration.engagement_count}</span></div>
        <div class="v360-metric"><span class="mk">Total annual value</span><span class="mv">${fmtMoney(d.concentration.total_annual_value)}</span></div>
        <div class="v360-metric"><span class="mk">Critical engagements</span><span class="mv">${d.concentration.critical_engagements.length}</span></div>
        <div class="v360-metric"><span class="mk">Contracts</span><span class="mv">${d.concentration.contract_count} (${d.concentration.critical_contracts} critical)</span></div>
      </div>
    </div>

    <div class="v360-grid">
      <div class="v360-panel"><h3>Exposure vs control</h3>
        <div class="v360-metric"><span class="mk">Inherent risk</span><span class="mv">${d.exposure_vs_control.inherent||'—'}</span></div>
        <div class="v360-metric"><span class="mk">Residual risk</span><span class="mv">${d.exposure_vs_control.residual||'—'}</span></div>
        <div class="v360-metric"><span class="mk">Open findings</span><span class="mv">${d.exposure_vs_control.open_findings}</span></div>
        <div class="v360-metric"><span class="mk">Max severity</span><span class="mv">${d.exposure_vs_control.max_severity||'—'}</span></div>
        <div class="v360-bar"><span style="width:${Math.min(100,(d.exposure_vs_control.gap||0)*33)}%;background:${d.exposure_vs_control.gap>1?'#e08a3c':'#4caf7e'}"></span></div>
        <div class="muted" style="font-size:11px;margin-top:5px">Control gap (inherent − residual): ${d.exposure_vs_control.gap}</div>
      </div>
      <div class="v360-panel"><h3>Performance & financial</h3>
        <div class="v360-metric"><span class="mk">Performance score</span><span class="mv">${dim.performance.score!=null?dim.performance.score+' / 5':'—'}</span></div>
        <div class="v360-metric"><span class="mk">Review cadence</span><span class="mv">${dim.performance.cadence||'—'}</span></div>
        <div class="v360-metric"><span class="mk">Last review</span><span class="mv">${dim.performance.last_review||'—'}</span></div>
        <div class="v360-metric"><span class="mk">Financial health</span><span class="mv">${dim.financial.band||'—'}</span></div>
        <div class="v360-metric"><span class="mk">Monitoring signal</span><span class="mv">${dim.monitoring.signal||'—'}</span></div>
      </div>
    </div>

    <div class="v360-panel" style="margin-bottom:14px">
      <h3 style="display:flex;justify-content:space-between;align-items:center">Risk attributes
        <button class="btn sm ghost" onclick="openVendorAttributes('${vid}')">Open editor →</button></h3>
      <div class="v360-attr-grid">
        ${(()=>{const cy=attr.cyber||{},pr=attr.privacy||{},re=attr.resilience||{},es=attr.esg||{},sc=attr.screening||[],ins=attr.insurance||[];
          const certs=(()=>{try{return JSON.parse(cy.certifications_json||"[]").length}catch(e){return 0}})();
          const screenAdverse=(Array.isArray(sc)?sc:[]).filter(x=>x&&(x.result==="hit"||x.result==="adverse")).length;
          return `
          <div class="v360-attr"><div class="al">Cyber assurance</div><div class="av">${esc(cy.assurance_status||'—')}</div><div class="as">${certs} cert(s) · rating ${esc(cy.external_rating||'—')}</div></div>
          <div class="v360-attr"><div class="al">Privacy</div><div class="av">${esc(pr.dpa_status||pr.data_processing_role||'—')}</div><div class="as">${pr.cross_border?'cross-border':'—'}</div></div>
          <div class="v360-attr"><div class="al">Resilience</div><div class="av">${re.bcp_status||re.exit_plan_status||'—'}</div><div class="as">RTO ${esc(re.rto||'—')} · RPO ${esc(re.rpo||'—')}</div></div>
          <div class="v360-attr"><div class="al">ESG</div><div class="av">${esc(es.esg_rating||es.rating||'—')}</div><div class="as">${esc(es.modern_slavery_status||'—')}</div></div>
          <div class="v360-attr"><div class="al">Screening</div><div class="av">${screenAdverse?'<span style="color:#c0392b">'+screenAdverse+' adverse</span>':'Clear'}</div><div class="as">${(Array.isArray(sc)?sc.length:0)} check(s)</div></div>
          <div class="v360-attr"><div class="al">Insurance</div><div class="av">${(Array.isArray(ins)?ins.length:0)} policy(ies)</div><div class="as">${esc((attr.risk_profile||{}).monitoring_signal||'—')}</div></div>`;})()}
      </div>
    </div>

    <div class="v360-panel" style="margin-bottom:14px"><h3>Engagements (${d.engagements.length})</h3>
      ${d.engagements.length?d.engagements.map(e=>`<div class="v360-metric"><span class="mk">${esc(e.title)} <span class="muted">${esc(e.engagement_id)}</span></span>
        <span class="mv">${e.residual_band?'<span class="band '+e.residual_band+'">'+e.residual_band+'</span>':'—'} · ${fmtMoney(e.annual_value)}</span></div>`).join(""):'<div class="muted">No engagements.</div>'}
    </div>

    <div class="muted" style="font-size:11px;text-align:center;padding:8px">
      One version of the truth · reconciled with consolidated risk profile · snapshot ${esc((d.provenance.risk_profile_snapshot||'').slice(0,19).replace('T',' '))} · source: ${esc(d.provenance.source)}
    </div>`;
}

/* ---------- Vendor Performance Management (R4) ---------- */
let _pmVendor=null;
V.performance=async()=>{
  const view=document.getElementById("view");
  view.innerHTML=`<div class="top"><div><h1>Vendor Performance</h1>
    <div class="sub">Scorecards · QBRs · closed-loop improvement · managed vendors</div></div>
    <button class="btn ghost" onclick="pmManage()">⊕ Manage list</button></div>
    <div id="pmBody" class="muted">Loading…</div>`;
  try{
    const enrolled = await api2("/performance/enrolment");
    if(!enrolled.length){
      view.querySelector("#pmBody").innerHTML=`<div class="card muted">No vendors under performance management yet. Use <b>Manage list</b> to add vendors. Critical vendors are added automatically.</div>`;
      return;
    }
    view.querySelector("#pmBody").innerHTML=`
      <div class="field" style="max-width:420px"><label>Managed vendor</label>
        <select id="pm_v" onchange="pmLoad()">${enrolled.map(v=>`<option value="${v.vendor_id}">${esc(v.legal_name||v.vendor_id)} (${v.vendor_id})${v.is_critical?' · CRITICAL':''}</option>`).join("")}</select></div>
      <div id="pmVendor"></div>`;
    _pmVendor = enrolled[0].vendor_id;
    pmLoad();
  }catch(e){ view.querySelector("#pmBody").innerHTML=`<div class="err">${esc(e.message)}</div>`; }
};
async function pmManage(){
  const [enrolled, all] = await Promise.all([api2("/performance/enrolment"), api2("/vendors")]);
  const enrolledIds = new Set(enrolled.map(e=>e.vendor_id));
  const candidates = all.filter(v=>!enrolledIds.has(v.vendor_id));
  modal(`<h3>Manage performance list</h3>
    <p class="muted" style="margin-bottom:8px">Select vendors to add to performance management. Critical vendors are included automatically.</p>
    <div class="field"><label>Add vendors</label>
      <select id="pm_add" multiple size="8" style="min-height:160px">${candidates.map(v=>`<option value="${v.vendor_id}">${esc(v.legal_name)} (${v.vendor_id})${v.is_critical?' · CRITICAL':''}</option>`).join("")||'<option disabled>All vendors already enrolled</option>'}</select></div>
    <div class="sec-h"><h2 style="font-size:13px">Currently managed (${enrolled.length})</h2><div class="rule"></div></div>
    <div style="max-height:140px;overflow:auto">${enrolled.map(e=>`<div class="dossier-row"><span class="dk">${esc(e.legal_name)} ${e.is_critical?'<span class="tag crit">CRITICAL</span>':''}<span class="muted" style="font-size:10px"> · ${esc(e.source)}</span></span>
      <span class="dv">${e.source==='auto-critical'?'<span class="muted" style="font-size:11px">auto</span>':`<button class="btn sm ghost" onclick="pmUnenrol('${e.vendor_id}')">remove</button>`}</span></div>`).join("")}</div>
    <div class="row" style="margin-top:12px"><button class="btn ghost" onclick="closeModal()">Close</button>
      <button class="btn" onclick="pmAddSelected()">+ Add selected</button></div>`);
}
async function pmAddSelected(){
  const sel=document.getElementById("pm_add");
  const ids=Array.from(sel.selectedOptions).map(o=>o.value).filter(Boolean);
  if(!ids.length){ flash("Select at least one vendor"); return; }
  try{ await api2("/performance/enrolment",{method:"POST",body:JSON.stringify({vendor_ids:ids})});
    closeModal(); flash(`${ids.length} vendor(s) added`); V.performance();
  }catch(e){ flash(e.message); } }
async function pmUnenrol(vid){
  try{ await api2("/performance/enrolment/"+vid,{method:"DELETE"}); flash("Removed"); pmManage(); }catch(e){ flash(e.message); } }
async function pmLoad(){
  const sel=document.getElementById("pm_v"); if(sel) _pmVendor=sel.value;
  const host=document.getElementById("pmVendor"); host.innerHTML=`<div class="muted">Loading scorecards…</div>`;
  try{
    const cards = await api2("/performance/vendor/"+_pmVendor);
    host.innerHTML=`<div class="sec-h" style="margin-top:16px"><h2 style="font-size:14px">Scorecards</h2><div class="rule"></div></div>
      <div class="row" style="margin-bottom:10px"><input id="pm_period" placeholder="Period e.g. 2026-Q3" style="max-width:200px">
        <button class="btn" onclick="pmCreate()">+ New scorecard</button></div>
      ${cards.length?`<table><tr><th>ID</th><th>Period</th><th>Status</th><th>Score</th><th>Band</th><th></th></tr>
        ${cards.map(s=>`<tr class="click" onclick="pmOpen('${s.scorecard_id}')"><td><b>${esc(s.scorecard_id)}</b></td>
          <td>${esc(s.period_label)}</td><td><span class="tag">${esc(s.status)}</span></td>
          <td>${s.composite_score!=null?s.composite_score+' / 5':'—'}</td>
          <td>${s.band?`<span class="posture-pill ${({Strong:'pp-0',Adequate:'pp-1',Watch:'pp-2',Underperforming:'pp-3'})[s.band]||'pp-1'}">${s.band}</span>`:'—'}</td>
          <td style="text-align:right">open →</td></tr>`).join("")}</table>`
        :'<div class="card muted">No scorecards yet for this vendor.</div>'}
      <div id="pmCard"></div>`;
  }catch(e){ host.innerHTML=`<div class="err">${esc(e.message)}</div>`; }
}
async function pmCreate(){
  const period=val("pm_period")||("Period-"+new Date().toISOString().slice(0,10));
  try{ const r=await api2("/performance/scorecards",{method:"POST",body:JSON.stringify({vendor_id:_pmVendor,period_label:period})});
    flash("Scorecard created"); pmLoad(); setTimeout(()=>pmOpen(r.scorecard_id),300);
  }catch(e){ flash(e.message); } }
async function pmOpen(sid){
  const host=document.getElementById("pmCard"); host.innerHTML=`<div class="muted">Loading…</div>`;
  try{
    const sc=await api2("/performance/scorecards/"+sid);
    const dimBlocks={};
    sc.kpis.forEach(k=>{ (dimBlocks[k.dimension]=dimBlocks[k.dimension]||[]).push(k); });
    const dimMeta=Object.fromEntries(sc.dimensions.map(d=>[d.name,d]));
    host.innerHTML=`<div class="sec-h" style="margin-top:16px"><h2 style="font-size:14px">${esc(sc.scorecard_id)} · ${esc(sc.period_label)}</h2><div class="rule"></div></div>
      <div class="v360-hero" style="padding:18px 22px"><div class="v360-verdict" style="margin:0">
        <div class="v360-dot l${sc.band==='Strong'?0:sc.band==='Adequate'?1:sc.band==='Watch'?2:3}"></div>
        <div><div class="v360-vlabel">${sc.composite_score!=null?sc.composite_score+' / 5':'Not scored'} · ${esc(sc.band||'—')}</div>
        <div class="v360-vsub">Status: ${esc(sc.status)} · ${sc.agreed_with_vendor?'agreed with vendor':'not yet agreed'} · ${sc.published?'published':'unpublished'}</div></div></div></div>
      ${Object.keys(dimBlocks).map(dim=>`
        <div class="v360-panel" style="margin-bottom:12px"><h3>${esc(lbl(dim))} · weight ${dimMeta[dim]?dimMeta[dim].weight:'?'}% · score ${dimMeta[dim]&&dimMeta[dim].score!=null?dimMeta[dim].score:'—'}</h3>
          ${dimBlocks[dim].map(k=>`<div class="v360-metric"><span class="mk">${esc(k.metric)} ${k.data_source==='auto'?'<span class="tag" style="font-size:9px">auto</span>':''} ${k.auto_value?'<span class="muted">('+esc(k.auto_value)+')</span>':''}</span>
            <span class="mv"><select onchange="pmScore(${k.id},this.value,'${sid}')" style="padding:3px 6px">
              <option value="">—</option>${[1,2,3,4,5].map(n=>`<option value="${n}" ${k.score===n?'selected':''}>${n}</option>`).join("")}</select></span></div>`).join("")}
        </div>`).join("")}
      <div class="row" style="margin:14px 0;gap:8px;flex-wrap:wrap">
        <button class="btn ghost" onclick="pmAgree('${sid}')">Agree with vendor</button>
        <button class="btn" onclick="pmPublish('${sid}')">Publish (roll into risk profile)</button>
        <button class="btn ghost" onclick="pmReview()">+ Record QBR</button>
        <button class="btn ghost" onclick="pmCapa('${sid}')">+ Raise improvement action</button>
      </div>`;
  }catch(e){ host.innerHTML=`<div class="err">${esc(e.message)}</div>`; }
}
async function pmScore(kpiId,v,sid){ if(!v)return; try{ await api2("/performance/kpi/"+kpiId,{method:"PUT",body:JSON.stringify({score:parseInt(v)})}); pmOpen(sid); }catch(e){ flash(e.message); } }
async function pmAgree(sid){ try{ await api2("/performance/scorecards/"+sid+"/agree",{method:"POST",body:JSON.stringify({party:"Vendor representative"})}); flash("Agreed with vendor"); pmOpen(sid); }catch(e){ flash(e.message); } }
async function pmPublish(sid){ try{ const r=await api2("/performance/scorecards/"+sid+"/publish",{method:"POST",body:"{}"}); flash("Published · score "+(r.composite_score!=null?r.composite_score:'—')+" rolled into risk profile"); pmLoad(); }catch(e){ flash(e.message); } }
function pmReview(){ modal(`<h3>Record performance review (QBR)</h3>
  <div class="field"><label>Attendees</label><input id="qbr_att"></div>
  <div class="field"><label>Summary</label><textarea id="qbr_sum" rows="3"></textarea></div>
  <div class="field"><label>Outcomes</label><textarea id="qbr_out" rows="2"></textarea></div>
  <div class="field"><label>Next review date</label><input id="qbr_next" placeholder="YYYY-MM-DD"></div>
  <div class="row"><button class="btn ghost" onclick="closeModal()">Cancel</button><button class="btn" onclick="pmReviewSave()">Save QBR</button></div>`); }
async function pmReviewSave(){ try{ await api2("/performance/vendor/"+_pmVendor+"/reviews",{method:"POST",body:JSON.stringify({data:{attendees:val("qbr_att"),summary:val("qbr_sum"),outcomes:val("qbr_out"),next_review_date:val("qbr_next")}})}); closeModal(); flash("QBR recorded"); }catch(e){ flash(e.message); } }
function pmCapa(sid){ modal(`<h3>Raise improvement action (closed-loop CAPA)</h3>
  <div class="field"><label>Performance gap</label><input id="capa_gap" placeholder="e.g. SLA attainment below target two periods"></div>
  <div class="field"><label>Accountable owner</label><input id="capa_owner"></div>
  <div class="field"><label>Due date</label><input id="capa_due" placeholder="YYYY-MM-DD"></div>
  <p class="muted" style="font-size:12px">This raises a tracked action on the Action Plan. It cannot be closed until verification of sustained effectiveness.</p>
  <div class="row"><button class="btn ghost" onclick="closeModal()">Cancel</button><button class="btn" onclick="pmCapaSave('${sid}')">Raise action</button></div>`); }
async function pmCapaSave(sid){ try{ const r=await api2("/performance/capa",{method:"POST",body:JSON.stringify({scorecard_id:sid,gap:val("capa_gap"),owner:val("capa_owner"),due_date:val("capa_due")||null})}); closeModal(); flash("Improvement action raised: "+r.remediation_id); }catch(e){ flash(e.message); } }

/* ---------- ProAssess (R5) ---------- */
let _paReport=null, _paMode='new';
V.proassess=async()=>{
  const view=document.getElementById("view");
  let vendors=[]; try{ vendors=await api2("/vendors"); }catch(e){}
  view.innerHTML=`<div class="top"><div><h1>ProAssess</h1>
    <div class="sub">Autonomous end-to-end assessment · works for new or existing vendors · no assumptions, gaps resolved risk-averse</div></div></div>
    <div class="card">
      <p class="muted" style="margin-bottom:12px">Describe the vendor and engagement in your own words and attach any documents you have. ProAssess reads internal records, your uploaded documents, public signals and your description together, computes inherent &amp; residual risk across the warranted domains, records every unestablished fact as a risk-averse gap, and — for a new vendor — creates the vendor, engagement, assessment and certificate records automatically. It asks no questions.</p>
      <div class="seg" style="margin-bottom:12px">
        <button class="${_paMode==='new'?'on':''}" onclick="paSetMode('new')">🆕 New vendor</button>
        <button class="${_paMode==='existing'?'on':''}" onclick="paSetMode('existing')">🏢 Existing vendor</button>
      </div>
      <div id="pa_target"></div>
      <div class="field" style="margin-top:10px"><label>Describe the vendor &amp; engagement — everything you know</label>
        <textarea id="pa_text" rows="6" placeholder="e.g. New SaaS payroll provider for EMEA. Processes employee personal and special-category data, ~50,000 records, hosted in AWS Frankfurt, some support offshore in India. We'll integrate via API. SOC 2 attached."></textarea></div>
      <div class="field"><label>Supporting documents (optional, multiple) — read automatically</label><input id="pa_files" type="file" multiple></div>
      <div class="field"><label><input type="checkbox" id="pa_ddq"> Control evidence (DDQ) supplied — without it, no mitigation is credited and residual = inherent</label></div>
      <button class="btn" onclick="paRunAuto()">⚡ Run ProAssess</button>
      <span class="muted" style="font-size:11px;margin-left:8px">Records are created automatically on completion.</span>
    </div>
    <div id="paReport"></div>`;
  paRenderTarget(vendors);
};
let _paVendors=[];
function paSetMode(m){ _paMode=m; paRenderTarget(_paVendors); }
function paRenderTarget(vendors){
  if(vendors&&vendors.length!==undefined) _paVendors=vendors;
  const host=document.getElementById("pa_target"); if(!host) return;
  if(_paMode==='existing'){
    host.innerHTML=`<div class="field"><label>Registered vendor</label>
      <select id="pa_v"><option value="">— select —</option>${(_paVendors||[]).map(v=>`<option value="${v.vendor_id}">${esc(v.legal_name)} (${v.vendor_id})</option>`).join("")}</select></div>
      <div class="field"><label>Engagement title (optional)</label><input id="pa_title" placeholder="e.g. Payment processing"></div>`;
  } else {
    host.innerHTML=`<div class="grid g2">
      <div class="field"><label>New vendor legal name</label><input id="pa_name" placeholder="e.g. Globex Payments Ltd"></div>
      <div class="field"><label>Engagement title</label><input id="pa_title" placeholder="e.g. Payroll processing"></div></div>
      <p class="muted" style="font-size:11px">A duplicate check runs automatically — if this vendor already exists, ProAssess links to it rather than creating a second record.</p>`;
  }
}
async function paRunAuto(){
  const input=document.getElementById("pa_files");
  const files=[];
  if(input&&input.files){
    for(const f of input.files){
      const b64=await new Promise((res,rej)=>{const r=new FileReader();r.onload=()=>res(r.result.split(",")[1]);r.onerror=rej;r.readAsDataURL(f);});
      files.push({filename:f.name,content_type:f.type||"application/octet-stream",data_b64:b64});
    }
  }
  const body={free_text:val("pa_text"),documents:files,engagement_title:val("pa_title")||null,create_records:true};
  if(_paMode==='existing'){ body.vendor_id=val("pa_v")||null; if(!body.vendor_id){ flash("Select a vendor"); return; } }
  else { body.new_vendor_name=val("pa_name")||null; if(!body.new_vendor_name){ flash("Enter the new vendor name"); return; } }
  if(document.getElementById("pa_ddq").checked) body.ddq={};
  const host=document.getElementById("paReport"); host.innerHTML=`<div class="muted" style="margin-top:14px">Reading inputs, assessing, and creating records…</div>`;
  try{
    _paReport=await api2("/proassess/autonomous",{method:"POST",body:JSON.stringify(body)});
    paRenderAuto();
  }catch(e){ host.innerHTML=`<div class="err">${esc(e.message)}</div>`; }
}
function paRenderAuto(){
  const d=_paReport; const host=document.getElementById("paReport");
  const recColor = (d.recommendation||"").startsWith("Approve")&&!(d.recommendation||"").includes("conditions")?"l0":(d.recommendation||"").includes("conditions")?"l1":"l3";
  const writes=d.tables_written||[];
  host.innerHTML=`
    <div class="sec-h" style="margin-top:18px"><h2 style="font-size:15px">Risk Report</h2><div class="rule"></div></div>
    <div class="v360-hero">
      <div class="vname">${esc(d.vendor_id||'unregistered')}${d.created_vendor?' · newly created':''}${d.duplicate_matched?' · matched existing':''}</div>
      <div class="vmeta">${d.engagement_id?esc(d.engagement_id):''} · ${d.documents_considered||0} document(s) · ${d.free_text_considered?'free-text considered':'no narrative'}</div>
      <div class="v360-verdict"><div class="v360-dot ${recColor}"></div>
        <div><div class="v360-vlabel">${esc(d.recommendation||'')}</div>
          <div class="v360-vsub">Inherent ${esc(d.inherent_band)} · Residual ${esc(d.residual_band)} · ${d.gap_count} gap(s) · monitoring ${esc(d.monitoring_cadence)}</div></div></div>
    </div>
    ${writes.length?`<div class="card" style="margin-bottom:12px;background:#f0f6f2;border-color:#cfe3d6">
      <div class="card-label" style="color:var(--green)">✓ Records created automatically</div>
      <div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:8px">${writes.map(w=>`<span class="tag" style="background:#e3efe6;color:var(--moss)">${esc(w)}</span>`).join("")}</div></div>`:''}
    <div class="v360-grid">
      <div class="v360-panel"><h3>Extracted inherent signals (IRQ)</h3>
        ${Object.keys(d.extracted_irq||{}).length?Object.entries(d.extracted_irq).map(([k,v])=>`<div class="v360-metric"><span class="mk">${esc(k)}</span><span class="mv">${esc(Array.isArray(v)?v.join(", "):String(v))}</span></div>`).join(""):'<div class="muted">No strong signals extracted — thin input scored conservatively.</div>'}
      </div>
      <div class="v360-panel"><h3>⚠ Gaps — resolved risk-averse (${d.gap_count})</h3>
        ${(d.gaps||[]).length?d.gaps.map(g=>`<div class="v360-metric"><span class="mk">${esc(g.domain)}: ${esc(g.issue)}</span><span class="mv" style="font-size:11px;color:#a85a1e">${esc(g.resolution)}</span></div>`).join(""):'<div class="muted">No gaps.</div>'}
      </div>
    </div>
    <div class="v360-panel" style="margin-bottom:12px"><h3>Risks (${(d.risks||[]).length})</h3>
      ${(d.risks||[]).length?d.risks.map(r=>`<div class="v360-exc"><span class="v360-sevdot sev-${r.severity}"></span><span style="flex:1">${esc(r.note)}</span><span class="muted" style="font-size:11px">${esc(r.domain)}</span></div>`).join(""):'<div class="muted">No material risks in scope.</div>'}
    </div>
    ${d.assessment_id?`<div class="row" style="margin-bottom:20px"><button class="btn ghost" onclick="openAssessmentReview('${d.assessment_id}')">Open assessment record →</button></div>`:''}`;
}

V.audit=async()=>{
  const view=document.getElementById("view");
  view.innerHTML=`<div class="top"><div><h1>Audit Trail</h1><div class="sub">Tamper-evident, hash-chained</div></div>
    <button class="btn ghost" onclick="verifyAudit()">Verify chain</button></div><div id="at" class="muted">Loading…</div>`;
  try{ const rows=await api("/audit");
    view.querySelector("#at").innerHTML=`<table><tr><th>#</th><th>Action</th><th>Actor</th><th>Hash</th></tr>
      ${rows.map(r=>`<tr><td>${r.seq}</td><td>${esc(r.action)}</td><td>${esc(r.actor)}</td>
        <td class="muted" style="font-family:monospace;font-size:11px">${esc(r.hash.slice(0,16))}…</td></tr>`).join("")}</table>`;
  }catch(e){ view.querySelector("#at").innerHTML=`<div class="err">${esc(e.message)}</div>`; }
};
async function verifyAudit(){ try{ const r=await api("/audit/verify");
  flash(r.intact?`✓ Chain intact (${r.entries} entries)`:`✗ Chain broken at #${r.broke_at}`);
  }catch(e){flash(e.message);} }

// boot: resume session if token present
if(tok()){ (async()=>{ try{
  const d=await api("/dashboard/executive"); // probe
  document.getElementById("login").classList.add("hidden");
  document.getElementById("app").classList.remove("hidden");
  V.dashboard();
}catch(_){ logout(); } })(); }
</script>
</body>
</html>"""


@ui.get("/", response_class=HTMLResponse)
def index() -> str:
    return _PAGE
