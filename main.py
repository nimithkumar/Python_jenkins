"""
COVID-19 & Indian Voters Dashboard - FastAPI Application
=========================================================
Run with:
    pip install fastapi uvicorn pandas plotly jinja2 python-multipart
    uvicorn main:app --reload --port 8000
Then open: http://localhost:8000
"""
#commit
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import random

app = FastAPI(title="COVID-19 & Indian Voters Dashboard", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
# ─────────────────────────────────────────────
# MOCK DATA
# ─────────────────────────────────────────────

STATES = [
    "Uttar Pradesh", "Maharashtra", "Bihar", "West Bengal", "Madhya Pradesh",
    "Rajasthan", "Tamil Nadu", "Karnataka", "Gujarat", "Andhra Pradesh",
    "Odisha", "Telangana", "Kerala", "Jharkhand", "Assam",
    "Punjab", "Haryana", "Chhattisgarh", "Delhi", "Uttarakhand"
]

random.seed(42)

def generate_covid_data():
    data = []
    for state in STATES:
        total = random.randint(50_000, 3_500_000)
        active = random.randint(100, int(total * 0.02))
        deaths = random.randint(int(total * 0.005), int(total * 0.02))
        recovered = total - active - deaths
        vaccinated = random.randint(int(total * 0.6), int(total * 0.95))
        data.append({
            "state": state,
            "total_cases": total,
            "active_cases": active,
            "recovered": recovered,
            "deaths": deaths,
            "vaccinated": vaccinated,
            "vaccination_pct": round(vaccinated / total * 100, 1)
        })
    return data

def generate_voter_data():
    data = []
    voter_bases = {
        "Uttar Pradesh": 152_000_000, "Maharashtra": 91_000_000,
        "Bihar": 73_000_000, "West Bengal": 73_000_000,
        "Madhya Pradesh": 55_000_000, "Rajasthan": 52_000_000,
        "Tamil Nadu": 61_000_000, "Karnataka": 55_000_000,
        "Gujarat": 48_000_000, "Andhra Pradesh": 40_000_000,
        "Odisha": 34_000_000, "Telangana": 32_000_000,
        "Kerala": 27_000_000, "Jharkhand": 24_000_000,
        "Assam": 23_000_000, "Punjab": 21_000_000,
        "Haryana": 19_000_000, "Chhattisgarh": 19_000_000,
        "Delhi": 14_000_000, "Uttarakhand": 8_000_000,
    }
    for state in STATES:
        total_voters = voter_bases.get(state, 20_000_000)
        male_voters = int(total_voters * random.uniform(0.52, 0.55))
        female_voters = total_voters - male_voters
        turnout = random.uniform(55, 80)
        young_voters = int(total_voters * random.uniform(0.20, 0.30))
        data.append({
            "state": state,
            "total_voters": total_voters,
            "male_voters": male_voters,
            "female_voters": female_voters,
            "turnout_pct": round(turnout, 1),
            "young_voters": young_voters,
            "young_voter_pct": round(young_voters / total_voters * 100, 1),
        })
    return data

COVID_DATA = generate_covid_data()
VOTER_DATA = generate_voter_data()

# ─────────────────────────────────────────────
# API ENDPOINTS
# ─────────────────────────────────────────────

@app.get("/api/covid", response_class=JSONResponse)
async def get_covid_data():
    return COVID_DATA

@app.get("/api/voters", response_class=JSONResponse)
async def get_voter_data():
    return VOTER_DATA

@app.get("/api/summary", response_class=JSONResponse)
async def get_summary():
    total_cases = sum(d["total_cases"] for d in COVID_DATA)
    total_deaths = sum(d["deaths"] for d in COVID_DATA)
    total_recovered = sum(d["recovered"] for d in COVID_DATA)
    total_active = sum(d["active_cases"] for d in COVID_DATA)
    total_vaccinated = sum(d["vaccinated"] for d in COVID_DATA)
    total_voters = sum(d["total_voters"] for d in VOTER_DATA)
    avg_turnout = round(sum(d["turnout_pct"] for d in VOTER_DATA) / len(VOTER_DATA), 1)
    return {
        "covid": {
            "total_cases": total_cases,
            "total_deaths": total_deaths,
            "total_recovered": total_recovered,
            "total_active": total_active,
            "total_vaccinated": total_vaccinated,
            "recovery_rate": round(total_recovered / total_cases * 100, 2),
            "fatality_rate": round(total_deaths / total_cases * 100, 2),
        },
        "voters": {
            "total_voters": total_voters,
            "avg_turnout": avg_turnout,
        }
    }

@app.get("/api/covid/{state}", response_class=JSONResponse)
async def get_state_covid(state: str):
    result = next((d for d in COVID_DATA if d["state"].lower() == state.lower()), None)
    if not result:
        return JSONResponse({"error": "State not found"}, status_code=404)
    return result

@app.get("/api/voters/{state}", response_class=JSONResponse)
async def get_state_voters(state: str):
    result = next((d for d in VOTER_DATA if d["state"].lower() == state.lower()), None)
    if not result:
        return JSONResponse({"error": "State not found"}, status_code=404)
    return result

# ─────────────────────────────────────────────
# HTML DASHBOARD
# ─────────────────────────────────────────────

HTML_DASHBOARD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>COVID-19 & Indian Voters Dashboard</title>
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
<style>
  *, *::before, *::after { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:'Segoe UI',sans-serif; background:#0f1117; color:#e0e0e0; min-height:100vh; }

  /* HEADER */
  header {
    background: linear-gradient(135deg,#1a1f36,#2d3561);
    padding:16px 32px; display:flex; align-items:center; justify-content:space-between;
    border-bottom:2px solid #3d4f8a; box-shadow:0 4px 20px rgba(0,0,0,.5);
    position:sticky; top:0; z-index:100;
  }
  header h1 { font-size:1.45rem; color:#fff; }
  header h1 span { color:#f97316; }
  .badge { background:#f97316; color:#fff; padding:4px 14px; border-radius:20px; font-size:.75rem; font-weight:700; }

  /* TABS */
  .tabs { display:flex; gap:6px; background:#13172a; padding:12px 32px; border-bottom:1px solid #2a2f4e; overflow-x:auto; }
  .tab { padding:9px 22px; border-radius:8px; cursor:pointer; font-size:.88rem; font-weight:600; transition:all .2s; border:none; background:#1e2340; color:#9ca3af; white-space:nowrap; }
  .tab.active  { background:#f97316; color:#fff; }
  .tab:hover:not(.active) { background:#2a2f4e; color:#fff; }

  /* MAIN */
  .main { padding:24px 32px; max-width:1600px; margin:0 auto; }

  /* KPI CARDS */
  .kpi-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(165px,1fr)); gap:14px; margin-bottom:22px; }
  .kpi-card { background:#1e2340; border-radius:12px; padding:16px; border-left:4px solid var(--accent,#f97316); transition:transform .2s,box-shadow .2s; }
  .kpi-card:hover { transform:translateY(-3px); box-shadow:0 8px 24px rgba(0,0,0,.4); }
  .kpi-label { font-size:.7rem; color:#9ca3af; text-transform:uppercase; letter-spacing:1px; }
  .kpi-value { font-size:1.6rem; font-weight:700; color:#fff; margin:6px 0 2px; line-height:1.1; }
  .kpi-sub   { font-size:.76rem; color:#9ca3af; }

  /* GRID LAYOUTS */
  .g2   { display:grid; grid-template-columns:1fr 1fr;     gap:20px; margin-bottom:20px; }
  .g3   { display:grid; grid-template-columns:1fr 1fr 1fr; gap:20px; margin-bottom:20px; }
  .g1   { display:grid; grid-template-columns:1fr;         gap:20px; margin-bottom:20px; }
  .g6040{ display:grid; grid-template-columns:3fr 2fr;     gap:20px; margin-bottom:20px; }

  @media(max-width:1050px){ .g2,.g3,.g6040{ grid-template-columns:1fr; } }

  /* CHART CARD */
  .cc { background:#1e2340; border-radius:12px; padding:18px 16px 10px; box-shadow:0 4px 16px rgba(0,0,0,.3); min-width:0; overflow:hidden; }
  .cc h3 { font-size:.9rem; color:#e0e0e0; margin-bottom:12px; border-left:3px solid #f97316; padding-left:10px; }
  .cc h3.b{ border-color:#3b82f6; }
  .cc h3.p{ border-color:#8b5cf6; }
  .cc h3.k{ border-color:#ec4899; }
  .cc h3.g{ border-color:#22c55e; }

  /* TABLE CARD */
  .tc { background:#1e2340; border-radius:12px; padding:20px; overflow-x:auto; margin-bottom:20px; box-shadow:0 4px 16px rgba(0,0,0,.3); }
  .tc h3 { font-size:.9rem; color:#e0e0e0; margin-bottom:14px; border-left:3px solid #3b82f6; padding-left:10px; }
  table { width:100%; border-collapse:collapse; font-size:.83rem; }
  th { background:#161b2e; color:#9ca3af; padding:10px 12px; text-align:left; font-size:.72rem; text-transform:uppercase; letter-spacing:.5px; }
  td { padding:9px 12px; border-bottom:1px solid #1a1f30; color:#d1d5db; }
  tr:hover td { background:#252b4a; }

  .fb { display:flex; gap:12px; margin-bottom:16px; align-items:center; flex-wrap:wrap; }
  .fb select { background:#161b2e; border:1px solid #3d4f8a; color:#e0e0e0; padding:7px 14px; border-radius:8px; font-size:.83rem; cursor:pointer; }
  .fb label { font-size:.83rem; color:#9ca3af; }

  .section { display:none; }
  .section.active { display:block; }

  footer { text-align:center; padding:18px; color:#4b5563; font-size:.78rem; border-top:1px solid #1e2340; margin-top:8px; }
</style>
</head>
<body>

<header>
  <h1>&#127470;&#127475; India <span>COVID-19</span> &amp; Voters Dashboard</h1>
  <span class="badge">LIVE DATA</span>
</header>

<div class="tabs">
  <button class="tab active" onclick="showTab('overview',this)">&#128202; Overview</button>
  <button class="tab" onclick="showTab('covid',this)">&#129440; COVID-19</button>
  <button class="tab" onclick="showTab('voters',this)">&#128379; Voters</button>
  <button class="tab" onclick="showTab('comparison',this)">&#128200; Comparison</button>
</div>

<div class="main">

  <!-- OVERVIEW -->
  <div id="overview" class="section active">
    <div class="kpi-grid" id="kpi-overview"></div>
    <div class="g2">
      <div class="cc"><h3>Top 10 States &#8212; COVID Cases</h3><div id="c-top-covid" style="height:300px"></div></div>
      <div class="cc"><h3>Voter Turnout by State</h3><div id="c-turnout" style="height:300px"></div></div>
    </div>
    <div class="g6040">
      <div class="cc"><h3>Vaccination Coverage by State</h3><div id="c-vacc-ov" style="height:290px"></div></div>
      <div class="cc"><h3>COVID Case Breakdown</h3><div id="c-pie" style="height:290px"></div></div>
    </div>
  </div>

  <!-- COVID -->
  <div id="covid" class="section">
    <div class="kpi-grid" id="kpi-covid"></div>
    <div class="g1">
      <div class="cc"><h3>Cases vs Recovered vs Deaths &#8212; Top 10 States</h3><div id="c-grouped" style="height:340px"></div></div>
    </div>
    <div class="g1">
      <div class="cc"><h3 class="b">Vaccination % by State (all 20)</h3><div id="c-vacc-h" style="height:430px"></div></div>
    </div>
    <div class="tc">
      <h3>&#129440; State-wise COVID Data</h3>
      <div class="fb">
        <label>Sort by:</label>
        <select onchange="sortCovid(this.value)">
          <option value="total_cases">Total Cases</option>
          <option value="deaths">Deaths</option>
          <option value="vaccination_pct">Vaccination %</option>
          <option value="active_cases">Active Cases</option>
        </select>
      </div>
      <table><thead><tr><th>State</th><th>Total Cases</th><th>Active</th><th>Recovered</th><th>Deaths</th><th>Vaccinated</th><th>Vacc %</th></tr></thead>
      <tbody id="covid-tbody"></tbody></table>
    </div>
  </div>

  <!-- VOTERS -->
  <div id="voters" class="section">
    <div class="kpi-grid" id="kpi-voters"></div>
    <div class="g1">
      <div class="cc"><h3 class="p">Total Registered Voters by State</h3><div id="c-voters-bar" style="height:300px"></div></div>
    </div>
    <div class="g2">
      <div class="cc"><h3 class="b">Male vs Female Voters &#8212; Top 10</h3><div id="c-gender" style="height:320px"></div></div>
      <div class="cc"><h3 class="k">Voter Turnout Distribution</h3><div id="c-turnout-hist" style="height:320px"></div></div>
    </div>
    <div class="g1">
      <div class="cc"><h3>Young Voter % by State</h3><div id="c-young" style="height:280px"></div></div>
    </div>
    <div class="tc">
      <h3>&#128379; State-wise Voter Data</h3>
      <table><thead><tr><th>State</th><th>Total Voters</th><th>Male</th><th>Female</th><th>Turnout %</th><th>Young Voters</th><th>Young %</th></tr></thead>
      <tbody id="voter-tbody"></tbody></table>
    </div>
  </div>

  <!-- COMPARISON -->
  <div id="comparison" class="section">
    <div class="g2">
      <div class="cc"><h3>Vaccination % vs Voter Turnout</h3><div id="c-scatter" style="height:380px"></div></div>
      <div class="cc"><h3 class="b">COVID Deaths vs Total Voters &#8212; Bubble</h3><div id="c-bubble" style="height:380px"></div></div>
    </div>
    <div class="g1">
      <div class="cc"><h3 class="g">COVID Cases &amp; Voter Turnout &#8212; Dual Axis (Top 12)</h3><div id="c-dual" style="height:380px"></div></div>
    </div>
  </div>

</div>

<footer>Dashboard built with FastAPI + Plotly.js &nbsp;|&nbsp; Illustrative mock data &nbsp;|&nbsp; &copy; 2024</footer>

<script>
let CD=[], VD=[], SUM={};

async function boot(){
  [CD,VD,SUM] = await Promise.all([
    fetch('/api/covid').then(r=>r.json()),
    fetch('/api/voters').then(r=>r.json()),
    fetch('/api/summary').then(r=>r.json()),
  ]);
  renderAll();
}

function fmt(n){
  if(n>=1e7) return (n/1e7).toFixed(1)+' Cr';
  if(n>=1e5) return (n/1e5).toFixed(1)+' L';
  return n.toLocaleString('en-IN');
}

function showTab(id,btn){
  document.querySelectorAll('.section').forEach(s=>s.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  btn.classList.add('active');
  setTimeout(()=>document.querySelectorAll('.js-plotly-plot').forEach(el=>Plotly.Plots.resize(el)),60);
}

/* Base layout */
function L(m={t:16,b:100,l:70,r:20},extra={}){
  return {
    paper_bgcolor:'transparent', plot_bgcolor:'transparent',
    font:{color:'#d1d5db',size:11},
    margin:m,
    xaxis:{gridcolor:'#2a2f4e',tickangle:-38,tickfont:{size:10},automargin:true},
    yaxis:{gridcolor:'#2a2f4e',automargin:true},
    legend:{bgcolor:'transparent',font:{size:11}},
    hoverlabel:{bgcolor:'#1e2340',bordercolor:'#3d4f8a',font:{color:'#fff'}},
    ...extra
  };
}
const RC={responsive:true,displayModeBar:false};

function kpiHTML(cards){
  return cards.map(c=>`<div class="kpi-card" style="--accent:${c.a}">
    <div class="kpi-label">${c.l}</div>
    <div class="kpi-value">${c.v}</div>
    ${c.s?`<div class="kpi-sub">${c.s}</div>`:''}
  </div>`).join('');
}

function renderAll(){
  /* KPIs */
  document.getElementById('kpi-overview').innerHTML = kpiHTML([
    {l:'Total Cases',  v:fmt(SUM.covid.total_cases),      s:'All India',              a:'#ef4444'},
    {l:'Active',       v:fmt(SUM.covid.total_active),     s:'Currently Active',       a:'#f97316'},
    {l:'Recovered',    v:fmt(SUM.covid.total_recovered),  s:SUM.covid.recovery_rate+'% rate', a:'#22c55e'},
    {l:'Deaths',       v:fmt(SUM.covid.total_deaths),     s:SUM.covid.fatality_rate+'% CFR', a:'#6b7280'},
    {l:'Vaccinated',   v:fmt(SUM.covid.total_vaccinated), s:'Doses',                  a:'#3b82f6'},
    {l:'Total Voters', v:fmt(SUM.voters.total_voters),    s:'Registered',             a:'#8b5cf6'},
    {l:'Avg Turnout',  v:SUM.voters.avg_turnout+'%',      s:'State Average',          a:'#ec4899'},
  ]);
  document.getElementById('kpi-covid').innerHTML = kpiHTML([
    {l:'Total Cases',   v:fmt(SUM.covid.total_cases),      a:'#ef4444'},
    {l:'Active',        v:fmt(SUM.covid.total_active),     a:'#f97316'},
    {l:'Recovered',     v:fmt(SUM.covid.total_recovered),  a:'#22c55e'},
    {l:'Deaths',        v:fmt(SUM.covid.total_deaths),     a:'#6b7280'},
    {l:'Recovery Rate', v:SUM.covid.recovery_rate+'%',     a:'#3b82f6'},
    {l:'Fatality Rate', v:SUM.covid.fatality_rate+'%',     a:'#9ca3af'},
    {l:'Vaccinated',    v:fmt(SUM.covid.total_vaccinated), a:'#06b6d4'},
  ]);
  const tm=VD.reduce((a,b)=>a+b.male_voters,0), tf=VD.reduce((a,b)=>a+b.female_voters,0);
  document.getElementById('kpi-voters').innerHTML = kpiHTML([
    {l:'Total Voters',  v:fmt(SUM.voters.total_voters), a:'#8b5cf6'},
    {l:'Male Voters',   v:fmt(tm),                      a:'#3b82f6'},
    {l:'Female Voters', v:fmt(tf),                      a:'#ec4899'},
    {l:'Avg Turnout',   v:SUM.voters.avg_turnout+'%',   a:'#f97316'},
  ]);

  /* ── OVERVIEW ── */
  const top10c=[...CD].sort((a,b)=>b.total_cases-a.total_cases).slice(0,10);
  Plotly.newPlot('c-top-covid',[{
    x:top10c.map(d=>d.state), y:top10c.map(d=>d.total_cases), type:'bar',
    marker:{color:top10c.map((_,i)=>`hsl(${5+i*8},80%,${60-i*2}%)`),opacity:.9},
    hovertemplate:'<b>%{x}</b><br>Cases:%{y:,}<extra></extra>',
  }],L({t:12,b:110,l:75,r:16}),RC);

  const vSorted=[...VD].sort((a,b)=>b.turnout_pct-a.turnout_pct);
  Plotly.newPlot('c-turnout',[{
    x:vSorted.map(d=>d.state), y:vSorted.map(d=>d.turnout_pct), type:'bar',
    marker:{color:vSorted.map(d=>d.turnout_pct>72?'#22c55e':d.turnout_pct>63?'#f97316':'#ef4444'),opacity:.9},
    hovertemplate:'<b>%{x}</b><br>Turnout:%{y:.1f}%<extra></extra>',
  }],L({t:12,b:110,l:60,r:16},{yaxis:{title:'Turnout %',gridcolor:'#2a2f4e'}}),RC);

  const cSorted=[...CD].sort((a,b)=>b.vaccination_pct-a.vaccination_pct);
  Plotly.newPlot('c-vacc-ov',[{
    x:cSorted.map(d=>d.state), y:cSorted.map(d=>d.vaccination_pct), type:'bar',
    marker:{color:cSorted.map(d=>d.vaccination_pct>80?'#22c55e':d.vaccination_pct>65?'#f97316':'#ef4444'),opacity:.9},
    hovertemplate:'<b>%{x}</b><br>Vacc:%{y:.1f}%<extra></extra>',
  }],L({t:12,b:110,l:60,r:16},{yaxis:{title:'Vaccination %',gridcolor:'#2a2f4e'}}),RC);

  Plotly.newPlot('c-pie',[{
    labels:['Recovered','Active','Deaths'],
    values:[SUM.covid.total_recovered,SUM.covid.total_active,SUM.covid.total_deaths],
    type:'pie', hole:.44,
    marker:{colors:['#22c55e','#f97316','#ef4444']},
    textinfo:'label+percent', textfont:{size:12},
    hovertemplate:'<b>%{label}</b><br>%{value:,}<br>%{percent}<extra></extra>',
  }],{
    paper_bgcolor:'transparent',plot_bgcolor:'transparent',
    font:{color:'#d1d5db',size:12},
    margin:{t:20,b:20,l:10,r:10},
    legend:{bgcolor:'transparent',orientation:'v',x:1.0,y:0.5,font:{size:12}},
    hoverlabel:{bgcolor:'#1e2340',bordercolor:'#3d4f8a',font:{color:'#fff'}},
  },RC);

  /* ── COVID TAB ── */
  Plotly.newPlot('c-grouped',[
    {name:'Total Cases',x:top10c.map(d=>d.state),y:top10c.map(d=>d.total_cases),type:'bar',marker:{color:'#ef4444',opacity:.85}},
    {name:'Recovered',  x:top10c.map(d=>d.state),y:top10c.map(d=>d.recovered),  type:'bar',marker:{color:'#22c55e',opacity:.85}},
    {name:'Deaths',     x:top10c.map(d=>d.state),y:top10c.map(d=>d.deaths),     type:'bar',marker:{color:'#6b7280',opacity:.85}},
  ],{...L({t:16,b:110,l:85,r:16}),barmode:'group'},RC);

  /* Horizontal vaccination bar — needs special layout (left margin for state names) */
  Plotly.newPlot('c-vacc-h',[{
    x:cSorted.map(d=>d.vaccination_pct),
    y:cSorted.map(d=>d.state),
    type:'bar', orientation:'h',
    marker:{color:cSorted.map(d=>d.vaccination_pct>80?'#22c55e':d.vaccination_pct>65?'#f97316':'#ef4444'),opacity:.9},
    hovertemplate:'<b>%{y}</b><br>Vacc:%{x:.1f}%<extra></extra>',
  }],{
    paper_bgcolor:'transparent',plot_bgcolor:'transparent',
    font:{color:'#d1d5db',size:11},
    margin:{t:12,b:50,l:155,r:50},
    xaxis:{title:'Vaccination %',gridcolor:'#2a2f4e',range:[0,105]},
    yaxis:{gridcolor:'#2a2f4e',automargin:true,tickfont:{size:11}},
    hoverlabel:{bgcolor:'#1e2340',bordercolor:'#3d4f8a',font:{color:'#fff'}},
  },RC);

  renderCovid(CD);

  /* ── VOTERS TAB ── */
  const vsByTotal=[...VD].sort((a,b)=>b.total_voters-a.total_voters);
  Plotly.newPlot('c-voters-bar',[{
    x:vsByTotal.map(d=>d.state),y:vsByTotal.map(d=>d.total_voters),type:'bar',
    marker:{color:vsByTotal.map((_,i)=>`hsl(${260+i*5},70%,${60-i*1.5}%)`),opacity:.9},
    hovertemplate:'<b>%{x}</b><br>Voters:%{y:,}<extra></extra>',
  }],L({t:12,b:110,l:85,r:16}),RC);

  const top10v=vsByTotal.slice(0,10);
  Plotly.newPlot('c-gender',[
    {name:'Male',  x:top10v.map(d=>d.state),y:top10v.map(d=>d.male_voters),  type:'bar',marker:{color:'#3b82f6',opacity:.9}},
    {name:'Female',x:top10v.map(d=>d.state),y:top10v.map(d=>d.female_voters),type:'bar',marker:{color:'#ec4899',opacity:.9}},
  ],{...L({t:12,b:110,l:80,r:16}),barmode:'group'},RC);

  Plotly.newPlot('c-turnout-hist',[{
    x:VD.map(d=>d.turnout_pct),type:'histogram',nbinsx:8,
    marker:{color:'#ec4899',opacity:.85,line:{color:'#f9a8d4',width:1}},
    hovertemplate:'Turnout range<br>States:%{y}<extra></extra>',
  }],L({t:12,b:60,l:60,r:16},{
    xaxis:{title:'Turnout %',gridcolor:'#2a2f4e'},
    yaxis:{title:'No. of States',gridcolor:'#2a2f4e'},
  }),RC);

  const ySorted=[...VD].sort((a,b)=>b.young_voter_pct-a.young_voter_pct);
  Plotly.newPlot('c-young',[{
    x:ySorted.map(d=>d.state),y:ySorted.map(d=>d.young_voter_pct),
    type:'scatter',mode:'lines+markers',
    line:{color:'#f97316',width:2.5},
    marker:{color:'#f97316',size:8,line:{color:'#fff',width:1.5}},
    fill:'tozeroy',fillcolor:'rgba(249,115,22,0.12)',
    hovertemplate:'<b>%{x}</b><br>Young:%{y:.1f}%<extra></extra>',
  }],L({t:12,b:110,l:60,r:16},{yaxis:{title:'Young Voter %',gridcolor:'#2a2f4e'}}),RC);

  renderVoters();

  /* ── COMPARISON ── */
  const merged=CD.map(c=>({...c,...(VD.find(v=>v.state===c.state)||{})}));

  Plotly.newPlot('c-scatter',[{
    x:merged.map(d=>d.vaccination_pct),y:merged.map(d=>d.turnout_pct),
    text:merged.map(d=>d.state),mode:'markers+text',
    textposition:'top center',textfont:{size:9,color:'#9ca3af'},
    marker:{color:merged.map(d=>d.vaccination_pct),colorscale:'Viridis',size:12,opacity:.85,
      showscale:true,colorbar:{title:'Vacc %',tickfont:{color:'#9ca3af',size:10}}},
    hovertemplate:'<b>%{text}</b><br>Vacc:%{x:.1f}%<br>Turnout:%{y:.1f}%<extra></extra>',
    type:'scatter',
  }],L({t:20,b:70,l:75,r:90},{
    xaxis:{title:'Vaccination %',gridcolor:'#2a2f4e'},
    yaxis:{title:'Voter Turnout %',gridcolor:'#2a2f4e'},
  }),RC);

  Plotly.newPlot('c-bubble',[{
    x:merged.map(d=>d.total_voters/1e6),y:merged.map(d=>d.deaths),
    text:merged.map(d=>d.state),mode:'markers+text',
    textposition:'top center',textfont:{size:9,color:'#9ca3af'},
    marker:{size:merged.map(d=>Math.max(10,d.total_cases/80000)),sizemode:'diameter',
      color:merged.map(d=>d.vaccination_pct),colorscale:'RdYlGn',showscale:true,
      colorbar:{title:'Vacc %',tickfont:{color:'#9ca3af',size:10}},opacity:.8},
    hovertemplate:'<b>%{text}</b><br>Voters:%{x:.1f}M<br>Deaths:%{y:,}<extra></extra>',
    type:'scatter',
  }],L({t:20,b:70,l:85,r:90},{
    xaxis:{title:'Total Voters (Millions)',gridcolor:'#2a2f4e'},
    yaxis:{title:'COVID Deaths',gridcolor:'#2a2f4e'},
  }),RC);

  const top12=[...merged].sort((a,b)=>b.total_cases-a.total_cases).slice(0,12);
  Plotly.newPlot('c-dual',[
    {name:'COVID Cases',x:top12.map(d=>d.state),y:top12.map(d=>d.total_cases),
      type:'bar',marker:{color:'#ef4444',opacity:.75},yaxis:'y',
      hovertemplate:'<b>%{x}</b><br>Cases:%{y:,}<extra></extra>'},
    {name:'Voter Turnout %',x:top12.map(d=>d.state),y:top12.map(d=>d.turnout_pct),
      type:'scatter',mode:'lines+markers',
      marker:{color:'#f97316',size:9,line:{color:'#fff',width:1.5}},
      line:{color:'#f97316',width:2.5},yaxis:'y2',
      hovertemplate:'<b>%{x}</b><br>Turnout:%{y:.1f}%<extra></extra>'},
  ],{
    paper_bgcolor:'transparent',plot_bgcolor:'transparent',
    font:{color:'#d1d5db',size:11},
    margin:{t:20,b:110,l:85,r:85},
    xaxis:{gridcolor:'#2a2f4e',tickangle:-38,tickfont:{size:10},automargin:true},
    yaxis:{title:'COVID Cases',gridcolor:'#2a2f4e',automargin:true},
    yaxis2:{title:'Voter Turnout %',overlaying:'y',side:'right',gridcolor:'transparent',range:[40,90]},
    legend:{bgcolor:'transparent',orientation:'h',x:0,y:1.08},
    hoverlabel:{bgcolor:'#1e2340',bordercolor:'#3d4f8a',font:{color:'#fff'}},
    barmode:'overlay',
  },RC);
}

/* ── Table renders ── */
function renderCovid(data){
  document.getElementById('covid-tbody').innerHTML=data.map(d=>`<tr>
    <td><b>${d.state}</b></td>
    <td>${d.total_cases.toLocaleString('en-IN')}</td>
    <td style="color:#f97316">${d.active_cases.toLocaleString('en-IN')}</td>
    <td style="color:#22c55e">${d.recovered.toLocaleString('en-IN')}</td>
    <td style="color:#ef4444">${d.deaths.toLocaleString('en-IN')}</td>
    <td>${d.vaccinated.toLocaleString('en-IN')}</td>
    <td><b style="color:${d.vaccination_pct>80?'#22c55e':d.vaccination_pct>65?'#f97316':'#ef4444'}">${d.vaccination_pct}%</b></td>
  </tr>`).join('');
}
function sortCovid(f){ renderCovid([...CD].sort((a,b)=>b[f]-a[f])); }

function renderVoters(){
  const s=[...VD].sort((a,b)=>b.total_voters-a.total_voters);
  document.getElementById('voter-tbody').innerHTML=s.map(d=>`<tr>
    <td><b>${d.state}</b></td>
    <td>${d.total_voters.toLocaleString('en-IN')}</td>
    <td style="color:#3b82f6">${d.male_voters.toLocaleString('en-IN')}</td>
    <td style="color:#ec4899">${d.female_voters.toLocaleString('en-IN')}</td>
    <td><b style="color:${d.turnout_pct>70?'#22c55e':d.turnout_pct>60?'#f97316':'#ef4444'}">${d.turnout_pct}%</b></td>
    <td>${d.young_voters.toLocaleString('en-IN')}</td>
    <td>${d.young_voter_pct}%</td>
  </tr>`).join('');
}

window.addEventListener('resize',()=>{
  document.querySelectorAll('.js-plotly-plot').forEach(el=>Plotly.Plots.resize(el));
});

boot();
</script>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return HTML_DASHBOARD

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
