from pathlib import Path
import csv, html, json, math, re, shutil
from collections import defaultdict
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / 'data' / 'companies.csv'
HISTORY_FILE = ROOT / 'data' / 'score_history.csv'
BASE_URL = 'https://texasrated.com'
DATA_REFRESH = '2026-08-28'

CATEGORIES = [
    'HVAC','Plumbing','Roofing','Electrical','Tree Service','Landscaping','Hardscaping','House Cleaning',
    'Handyman','Dumpster Rental','Junk Removal','Pest Control','Garage Door','Painting','Pool Service','Moving'
]
MARKETS = ['Austin','North Austin','South Austin','San Antonio']
CATEGORY_DESCRIPTIONS = {
    'HVAC':'Heating, cooling, repair and replacement companies.',
    'Plumbing':'Local plumbers for repair, installation and emergencies.',
    'Roofing':'Roof repair, replacement and storm-related contractors.',
    'Electrical':'Residential electrical repair, upgrades and installations.',
    'Tree Service':'Tree trimming, removal, storm cleanup and arborist services.',
    'Landscaping':'Landscape design, installation and ongoing property care.',
    'Hardscaping':'Patios, pavers, retaining walls and outdoor living projects.',
    'House Cleaning':'Recurring, deep and move-in / move-out cleaning services.',
    'Handyman':'General repair, installation and home maintenance professionals.',
    'Dumpster Rental':'Local roll-off dumpster delivery and pickup providers.',
    'Junk Removal':'Furniture, debris and property cleanout services.',
    'Pest Control':'Pest, termite, rodent and mosquito control companies.',
    'Garage Door':'Garage door repair, installation, springs and openers.',
    'Painting':'Interior, exterior and specialty painting contractors.',
    'Pool Service':'Pool cleaning, repair, equipment and maintenance companies.',
    'Moving':'Local movers, packing services and residential relocations.'
}
MARKET_DESCRIPTIONS = {
    'Austin':'Austin-area service companies across all currently tracked categories.',
    'North Austin':'Companies serving North Austin neighborhoods and ZIP codes.',
    'South Austin':'Companies serving South Austin neighborhoods and ZIP codes.',
    'San Antonio':'Service companies across the San Antonio market.'
}

for d in ['company','rankings','widget']:
    p=ROOT/d
    if p.exists(): shutil.rmtree(p)
    p.mkdir(parents=True, exist_ok=True)
(ROOT/'assets'/'icons').mkdir(parents=True, exist_ok=True)


def esc(s): return html.escape(str(s or ''), quote=True)
def slugify(s):
    s=re.sub(r'[^a-zA-Z0-9]+','-',str(s).strip().lower()).strip('-')
    return re.sub(r'-+','-',s) or 'company'
def boolish(v): return str(v).strip().lower() in {'1','true','yes','y'}
def split_pipe(v): return [x.strip() for x in str(v or '').split('|') if x.strip()]
def fmt_date(d):
    try: return datetime.strptime(d,'%Y-%m-%d').strftime('%B %-d, %Y')
    except Exception: return d

def score_company(c):
    rating=max(0.0,min(5.0,float(c.get('rating') or 0)))
    reviews=max(0,int(float(c.get('reviews') or 0)))
    prior_mean=4.4; prior_weight=40
    adjusted=(reviews/(reviews+prior_weight))*rating + (prior_weight/(reviews+prior_weight))*prior_mean
    reputation=(adjusted/5.0)*85.0
    review_depth=min(10.0, 10.0*math.log1p(reviews)/math.log1p(2000))
    profile_strength=max(0,min(100,int(float(c.get('profile_strength') or 0)))) if c.get('claimed') else 0
    profile_component=5.0*(profile_strength/100.0)
    total=min(100.0,reputation+review_depth+profile_component)
    return round(total,1), {
        'Adjusted reputation':round(reputation,1),
        'Review depth':round(review_depth,1),
        'Verified profile data':round(profile_component,1)
    }

# Read source-of-truth CSV
rows=[]
with DATA_FILE.open(newline='',encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        if not r.get('name'): continue
        r={k:(v or '').strip() for k,v in r.items()}
        r['claimed']=boolish(r.get('claimed'))
        r['verified']=boolish(r.get('verified'))
        r['independent']=boolish(r.get('independent')) if r.get('independent') else False
        r['categories']=split_pipe(r.get('categories'))
        r['markets']=split_pipe(r.get('markets')) or ([r.get('primary_market')] if r.get('primary_market') else [])
        r['services']=split_pipe(r.get('services'))
        r['rating']=float(r.get('rating') or 0)
        r['reviews']=int(float(r.get('reviews') or 0))
        r['profile_strength']=int(float(r.get('profile_strength') or 0))
        base_slug=r.get('slug') or slugify(f"{r['name']}-{r.get('city') or r.get('primary_market')}")
        r['slug']=base_slug
        r['score'],r['score_breakdown']=score_company(r)
        rows.append(r)

# Ensure unique slugs deterministically.
seen={}
for r in rows:
    s=r['slug']
    n=seen.get(s,0)+1; seen[s]=n
    if n>1: r['slug']=f'{s}-{n}'

# Rankings by market/category.
groups=defaultdict(list)
for c in rows:
    for market in c['markets']:
        for cat in c['categories']:
            groups[(market,cat)].append(c)
for key,arr in groups.items():
    arr.sort(key=lambda c:(-c['score'],-c['reviews'],-c['rating'],c['name'].lower()))

rank_positions=defaultdict(dict)
for (market,cat),arr in groups.items():
    for i,c in enumerate(arr,1): rank_positions[c['slug']][(market,cat)]=i

# history / momentum
history=[]
if HISTORY_FILE.exists():
    with HISTORY_FILE.open(newline='',encoding='utf-8-sig') as f:
        history=list(csv.DictReader(f))
hist_by_slug=defaultdict(list)
for h in history:
    try: hist_by_slug[h['slug']].append((h['date'],float(h['score'])))
    except Exception: pass
for s in hist_by_slug: hist_by_slug[s].sort()
all_dates=sorted({h.get('date') for h in history if h.get('date')})
have_momentum=len(all_dates)>=2
momentum=[]
if have_momentum:
    first_date,last_date=all_dates[0],all_dates[-1]
    first={h['slug']:float(h['score']) for h in history if h.get('date')==first_date}
    last={h['slug']:float(h['score']) for h in history if h.get('date')==last_date}
    for c in rows:
        if c['slug'] in first and c['slug'] in last:
            momentum.append((round(last[c['slug']]-first[c['slug']],1),c))
    momentum.sort(key=lambda x:(-x[0],-x[1]['score']))

# Visual icons: custom SVG medallions, not emoji.
ICON_PATHS={
'HVAC':'<path d="M32 15v34M15 32h34M20 20l24 24M44 20 20 44"/><circle cx="32" cy="32" r="7"/>',
'Plumbing':'<path d="M32 13s-13 16-13 27a13 13 0 0 0 26 0c0-11-13-27-13-27Z"/><path d="M25 42c2 4 6 6 10 5"/>',
'Roofing':'<path d="m13 34 19-16 19 16"/><path d="M18 32v18h28V32"/><path d="M26 50V38h12v12"/>',
'Electrical':'<path d="M36 12 20 35h11l-3 17 16-24H33l3-16Z"/>',
'Tree Service':'<path d="M32 13c-8 0-12 7-10 13-7 2-8 13 0 16h20c8-4 7-14 0-16 2-6-2-13-10-13Z"/><path d="M32 35v17M25 52h14"/>',
'Landscaping':'<path d="M13 43c13 0 19-6 22-19 8 1 14 6 16 13-5 10-15 15-27 13"/><path d="M17 50c7-9 16-15 27-19"/>',
'Hardscaping':'<rect x="14" y="18" width="16" height="12" rx="2"/><rect x="34" y="18" width="16" height="12" rx="2"/><rect x="14" y="34" width="16" height="12" rx="2"/><rect x="34" y="34" width="16" height="12" rx="2"/>',
'House Cleaning':'<path d="m13 32 19-16 19 16"/><path d="M18 30v20h28V30"/><path d="m41 15 2 5 5 2-5 2-2 5-2-5-5-2 5-2 2-5Z"/>',
'Handyman':'<path d="m18 46 21-21"/><path d="M38 15a10 10 0 0 0-9 14L15 43l6 6 14-14a10 10 0 0 0 14-9l-8 5-7-7 4-9Z"/>',
'Dumpster Rental':'<path d="M14 24h36l-4 25H18l-4-25Z"/><path d="M19 24l4-8h18l4 8M25 30v13M32 30v13M39 30v13"/>',
'Junk Removal':'<path d="M16 24h32v24H16z"/><path d="m16 24 8-8h24v8M24 34h16M29 40h6"/>',
'Pest Control':'<ellipse cx="32" cy="35" rx="10" ry="13"/><path d="M27 22c0-6 10-6 10 0M22 30l-8-5M22 38l-9 3M42 30l8-5M42 38l9 3M32 22v26"/>',
'Garage Door':'<path d="M14 50V19h36v31"/><path d="M20 50V27h24v23M20 34h24M20 41h24"/>',
'Painting':'<path d="M14 18h28v10H14zM42 23h7v10h-7M46 33v7H31v12"/><path d="M27 52h8v-8h-8z"/>',
'Pool Service':'<path d="M12 35c5 5 9 5 14 0s9-5 14 0 9 5 14 0M12 44c5 5 9 5 14 0s9-5 14 0 9 5 14 0"/><path d="M22 31V18h12M34 31V18h9"/>',
'Moving':'<path d="M13 24h25v22H13zM38 31h8l6 8v7H38z"/><circle cx="22" cy="49" r="4"/><circle cx="45" cy="49" r="4"/><path d="M18 31h14M18 37h14"/>'
}

def icon_svg(cat):
    path=ICON_PATHS.get(cat,ICON_PATHS['Handyman'])
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#061b3a"/><stop offset=".68" stop-color="#0d4da8"/><stop offset="1" stop-color="#ee2c35"/></linearGradient></defs><circle cx="32" cy="32" r="30" fill="url(#bg)"/><circle cx="32" cy="32" r="25" fill="none" stroke="rgba(255,255,255,.28)" stroke-width="1.5"/><g fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">{path}</g></svg>'''
for cat in CATEGORIES:
    (ROOT/'assets'/'icons'/f'{slugify(cat)}.svg').write_text(icon_svg(cat),encoding='utf-8')

# app.js
(ROOT/'assets'/'app.js').write_text(r'''document.addEventListener('click',function(e){
  const s=e.target.closest('[data-share]');
  if(s){e.preventDefault(); const data={title:s.dataset.title||document.title,text:s.dataset.text||'',url:s.dataset.url||location.href}; if(navigator.share){navigator.share(data).catch(()=>{});}else{navigator.clipboard&&navigator.clipboard.writeText(data.url); s.textContent='Link copied'; setTimeout(()=>s.textContent='Share',1500);}}
  const t=e.target.closest('[data-toggle]'); if(t){const id=t.dataset.toggle; document.getElementById(id)?.classList.toggle('open');}
});
const filters=document.querySelectorAll('[data-filter-group] select'); filters.forEach(el=>el.addEventListener('change',()=>{ const group=el.closest('[data-filter-group]'); const market=group.querySelector('[name=market]')?.value||''; const category=group.querySelector('[name=category]')?.value||''; group.querySelectorAll('[data-score-row]').forEach(row=>{ const okM=!market||row.dataset.markets.split('|').includes(market); const okC=!category||row.dataset.categories.split('|').includes(category); row.hidden=!(okM&&okC); }); }));
const q=document.querySelector('[data-company-search]'); if(q){q.addEventListener('input',()=>{const v=q.value.toLowerCase().trim(); document.querySelectorAll('[data-company-result]').forEach(r=>r.hidden=v&&!r.dataset.companyResult.includes(v));});}
''',encoding='utf-8')

# CSS
(ROOT/'assets'/'styles.css').write_text(r''':root{--navy:#071d3d;--navy2:#0b2c5f;--blue:#0c63db;--red:#ef3139;--ink:#0a2142;--muted:#61728a;--line:#dce5f1;--soft:#f4f8fd;--green:#159447;--gold:#e5a91b;--shadow:0 12px 34px rgba(7,29,61,.09)}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:var(--ink);background:#fff}a{color:inherit;text-decoration:none}img{max-width:100%}.container{width:min(1180px,calc(100% - 38px));margin:auto}.site-header{position:sticky;top:0;z-index:30;background:rgba(255,255,255,.96);backdrop-filter:blur(14px);border-bottom:1px solid #e7edf5}.header-inner{height:74px;display:flex;align-items:center;gap:30px}.brand{display:flex;align-items:center;gap:10px;font-weight:900;letter-spacing:-.6px;font-size:20px;white-space:nowrap}.brand img{width:48px;height:48px;object-fit:contain}.brand span small{display:block;color:var(--red);font-size:10px;letter-spacing:1.8px;margin-top:-2px}.main-nav{display:flex;align-items:center;gap:22px;margin-left:auto;font-size:14px;font-weight:750}.main-nav a:hover{color:var(--blue)}.header-actions{display:flex;gap:9px}.btn{display:inline-flex;align-items:center;justify-content:center;gap:7px;padding:11px 17px;border-radius:8px;border:1px solid #b8cae2;font-size:14px;font-weight:800;background:#fff;color:var(--ink);cursor:pointer}.btn.primary,.btn.navy{background:var(--blue);color:white;border-color:var(--blue)}.btn.navy{background:var(--navy);border-color:var(--navy)}.btn.red{background:var(--red);border-color:var(--red);color:white}.hero{background:linear-gradient(115deg,#061a39 0%,#0b2e61 63%,#0a4eaa 100%);color:white;overflow:hidden}.hero .container{display:grid;grid-template-columns:1.05fr .95fr;min-height:445px;align-items:center;gap:48px;padding:54px 0}.hero h1{font-size:52px;line-height:1.02;letter-spacing:-2.2px;margin:10px 0 17px}.hero p{font-size:18px;line-height:1.65;color:#d7e4f5;max-width:650px}.eyebrow{text-transform:uppercase;font-size:12px;letter-spacing:1.25px;font-weight:900;color:#4c8ff1}.hero .eyebrow{color:#92c1ff}.hero-search{background:#fff;border-radius:13px;padding:10px;display:grid;grid-template-columns:1fr 1fr auto;gap:9px;margin-top:25px;box-shadow:0 12px 40px rgba(0,0,0,.18)}.select,.input{width:100%;padding:13px 14px;border:1px solid #d5dfec;border-radius:8px;background:white;color:var(--ink);font-size:14px}.hero-panel{position:relative;border:1px solid rgba(255,255,255,.15);border-radius:18px;padding:23px;background:linear-gradient(145deg,rgba(255,255,255,.12),rgba(255,255,255,.04));box-shadow:0 24px 60px rgba(0,0,0,.2)}.hero-panel:before{content:"";position:absolute;inset:auto -70px -110px auto;width:310px;height:310px;background:url('logo.png') center/contain no-repeat;opacity:.08}.hero-panel-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px}.hero-panel h3{margin:0;font-size:18px}.hero-row{position:relative;display:grid;grid-template-columns:42px 1fr auto;gap:12px;align-items:center;padding:13px 4px;border-top:1px solid rgba(255,255,255,.12)}.hero-row strong{display:block}.hero-row small{display:block;color:#a9bdd6;margin-top:3px}.hero-score{font-weight:900;font-size:20px;color:#fff}.hero-score small{font-size:9px;color:#94bfff}.section{padding:54px 0}.section.soft{background:var(--soft)}.section-title{display:flex;align-items:end;justify-content:space-between;gap:24px;margin-bottom:22px}.section-title h2{font-size:28px;margin:0 0 5px;letter-spacing:-.8px}.section-title p{margin:0;color:var(--muted)}.text-link{color:var(--blue);font-weight:800;font-size:14px}.popular-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:13px}.ranking-tile{min-height:126px;border:1px solid var(--line);border-radius:14px;padding:17px;background:#fff;display:flex;gap:14px;align-items:flex-start;transition:.2s;box-shadow:0 3px 10px rgba(7,29,61,.02)}.ranking-tile:hover{transform:translateY(-3px);box-shadow:var(--shadow);border-color:#b6cff0}.service-medallion{width:56px;height:56px;flex:0 0 56px;filter:drop-shadow(0 7px 10px rgba(7,29,61,.13))}.ranking-tile h3{font-size:15px;margin:2px 0 6px}.ranking-tile p{font-size:12px;color:var(--muted);margin:0 0 8px;line-height:1.35}.tile-top{font-size:12px;color:var(--blue);font-weight:800}.market-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:15px}.market-card{position:relative;min-height:205px;overflow:hidden;border-radius:16px;background:linear-gradient(145deg,#071d3d,#0d4da8);color:#fff;padding:22px;box-shadow:var(--shadow)}.market-card:nth-child(2){background:linear-gradient(145deg,#102651,#165fc3)}.market-card:nth-child(3){background:linear-gradient(145deg,#0c355f,#0a7394)}.market-card:nth-child(4){background:linear-gradient(145deg,#38162a,#b42f3a)}.market-card:after{content:"";position:absolute;width:150px;height:150px;right:-28px;bottom:-23px;background:url('logo.png') center/contain no-repeat;opacity:.15}.market-card .market-pin{width:44px;height:44px;border:1px solid rgba(255,255,255,.35);border-radius:50%;display:grid;place-items:center;margin-bottom:30px;background:rgba(255,255,255,.08)}.market-pin svg{width:25px}.market-card h3{font-size:22px;margin:0 0 5px}.market-card p{color:#d1e1f6;font-size:13px;max-width:75%;line-height:1.4}.market-meta{margin-top:12px;font-size:12px;font-weight:800;color:#fff}.score-strip{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.score-card{border:1px solid var(--line);border-radius:13px;padding:18px;background:#fff}.score-card .big{font-size:31px;font-weight:950;letter-spacing:-1px;color:var(--green)}.score-card h3{font-size:14px;margin:8px 0 4px}.score-card p{font-size:12px;color:var(--muted);margin:0}.how-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:18px}.how-card{padding:20px}.how-num{width:38px;height:38px;border-radius:50%;display:grid;place-items:center;background:#eaf3ff;color:var(--blue);font-weight:900;margin-bottom:14px}.how-card h3{margin:0 0 7px;font-size:16px}.how-card p{margin:0;color:var(--muted);font-size:13px;line-height:1.55}.owner-cta{background:linear-gradient(135deg,#071d3d,#0c418d);border-radius:18px;padding:34px;color:white;display:grid;grid-template-columns:1fr auto;align-items:center;gap:28px}.owner-cta h2{margin:0 0 8px;font-size:30px}.owner-cta p{margin:0;color:#cfe0f7}.page-hero{padding:55px 0 38px;background:linear-gradient(180deg,#f5f9ff,#fff)}.page-hero h1{font-size:42px;letter-spacing:-1.4px;margin:8px 0 10px}.page-hero p{color:var(--muted);font-size:17px;max-width:760px;line-height:1.55}.category-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:17px}.category-card{border:1px solid var(--line);border-radius:16px;padding:20px;background:white;box-shadow:0 4px 18px rgba(7,29,61,.035)}.category-head{display:flex;align-items:center;gap:14px;margin-bottom:14px}.category-head .service-medallion{width:58px;height:58px}.category-head h2{font-size:20px;margin:0 0 4px}.category-head p{font-size:12px;color:var(--muted);margin:0}.top-five{border-top:1px solid #e8eef6}.top-five-row{display:grid;grid-template-columns:28px 1fr auto;align-items:center;gap:9px;padding:9px 2px;border-bottom:1px solid #edf2f7;font-size:13px}.top-five-row .rank{font-weight:900;color:#718198}.top-five-row strong{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.top-five-row .score{font-weight:900;color:var(--green)}.category-actions{display:flex;justify-content:space-between;align-items:center;margin-top:13px}.category-actions small{color:var(--muted)}.ranking-layout{display:grid;grid-template-columns:260px 1fr;gap:24px}.filter-card{border:1px solid var(--line);border-radius:14px;padding:17px;position:sticky;top:95px;align-self:start}.filter-card h3{margin:0 0 12px}.filter-card label{font-size:11px;font-weight:900;text-transform:uppercase;letter-spacing:.6px}.filter-card .select{margin:6px 0 14px}.ranking-table{border:1px solid var(--line);border-radius:14px;overflow:hidden;background:white}.table-head,.table-row{display:grid;grid-template-columns:58px minmax(220px,1.7fr) 100px 100px 110px;align-items:center;gap:8px;padding:12px 16px}.table-head{font-size:11px;text-transform:uppercase;letter-spacing:.5px;background:#f6f9fd;color:#75869d;font-weight:900}.table-row{border-top:1px solid #eaf0f7;font-size:14px}.table-row:hover{background:#fbfdff}.table-row .rank{font-size:17px;font-weight:950}.company-cell strong{display:block}.company-cell small{display:block;color:var(--muted);margin-top:3px}.tr-score{font-weight:950;color:var(--green);font-size:17px}.rating-stars{color:#e5a91b;font-weight:850}.badge{display:inline-flex;align-items:center;padding:4px 7px;border-radius:999px;font-size:10px;font-weight:850;background:#e9f7ef;color:#117a3e}.badge.unclaimed{background:#f3f5f8;color:#718198}.company-hero{padding:42px 0;background:linear-gradient(180deg,#f3f8ff,#fff)}.company-shell{display:grid;grid-template-columns:1fr 330px;gap:24px}.company-main,.company-side{border:1px solid var(--line);border-radius:16px;background:#fff;padding:23px}.company-title{display:flex;justify-content:space-between;gap:20px}.company-title h1{font-size:32px;margin:0 0 7px}.company-title p{margin:0;color:var(--muted)}.score-orb{min-width:120px;text-align:center;border-left:1px solid var(--line);padding-left:20px}.score-orb strong{display:block;font-size:38px;color:var(--green);letter-spacing:-1.5px}.score-orb span{font-size:11px;color:var(--muted);font-weight:800}.facts{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:20px 0}.fact{border:1px solid #e8eef6;background:#f9fbfe;border-radius:10px;padding:13px}.fact small{display:block;color:var(--muted);margin-bottom:4px}.fact strong{font-size:14px}.rank-list{display:grid;gap:8px}.rank-item{display:flex;justify-content:space-between;padding:12px 0;border-bottom:1px solid #ebf0f6}.rank-item b{font-size:19px}.claim-box{background:#071d3d;color:white;border-radius:14px;padding:19px;margin-top:18px}.claim-box h3{margin:0 0 7px}.claim-box p{font-size:13px;color:#c7daef;line-height:1.5}.company-side h3{margin:0 0 14px}.score-break{display:grid;gap:12px}.meter{height:7px;background:#edf2f7;border-radius:20px;overflow:hidden;margin-top:6px}.meter span{display:block;height:100%;background:linear-gradient(90deg,#0c63db,#159447);border-radius:20px}.source-note{font-size:11px;color:#798aa1;line-height:1.45;margin-top:18px}.share-row{display:flex;gap:8px;flex-wrap:wrap}.message-card,.card{border:1px solid var(--line);border-radius:14px;background:#fff;padding:18px}.form-card label{display:block;font-size:12px;font-weight:850;margin:13px 0 6px}.notice{padding:14px 16px;border-radius:10px;background:#fff8df;color:#725800;border:1px solid #f0df9d;font-size:13px;line-height:1.5}.empty-state{border:1px dashed #b7cae3;border-radius:15px;padding:38px;text-align:center;background:#f8fbff}.empty-state img{width:78px;opacity:.95}.empty-state h2{margin:12px 0 8px}.empty-state p{color:var(--muted);max-width:650px;margin:0 auto 18px;line-height:1.55}.footer{background:#06182f;color:#fff;padding:44px 0 20px;margin-top:55px}.footer-grid{display:grid;grid-template-columns:1.5fr repeat(4,1fr);gap:30px}.footer .brand{margin-bottom:12px}.footer h4{margin:0 0 10px;font-size:13px}.footer a:not(.brand){display:block;color:#aebfd3;font-size:12px;margin:8px 0}.footer-note{border-top:1px solid rgba(255,255,255,.1);margin-top:30px;padding-top:18px;color:#8298b1;font-size:11px}.mobile-menu{display:none}.dashboard-hero{background:#071d3d;color:white;padding:26px 0}.dashboard-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.dash-card{border:1px solid var(--line);border-radius:14px;padding:18px;background:#fff;min-height:165px}.dash-card .big{font-size:34px;font-weight:950}.dash-card h3{font-size:11px;text-transform:uppercase;letter-spacing:.65px;margin:0 0 14px;color:#63758e}.dashboard-grid .wide{grid-column:span 2}.profile-progress{display:flex;align-items:center;gap:15px}.progress-ring{width:54px;height:54px;border-radius:50%;background:conic-gradient(#20a35b 0 78%,#d6e0ec 78%);display:grid;place-items:center}.progress-ring:after{content:"";width:39px;height:39px;border-radius:50%;background:#071d3d}.widget-body{margin:0;background:transparent}.widget-link{display:block}.widget{width:260px;height:290px;padding:24px;text-align:center;color:#fff;background:linear-gradient(145deg,#061a39,#0b4ca3);border:5px solid #d8e0e9;outline:2px solid #081c3b;clip-path:polygon(10% 0,90% 0,100% 15%,100% 77%,50% 100%,0 77%,0 15%);box-shadow:inset 0 0 0 3px #e4af36}.w-brand{font-size:14px;font-weight:950;letter-spacing:1.5px;color:#fff}.w-top{font-size:27px;font-weight:1000;margin-top:31px;color:#fff}.w-cat{font-size:15px;font-weight:900;margin-top:5px}.w-rank{font-size:46px;font-weight:1000;color:#fff;margin:9px}.w-year{font-size:10px;letter-spacing:.9px;color:#cfe2ff}.muted{color:var(--muted)}.small{font-size:12px}@media(max-width:980px){.main-nav{display:none}.header-inner{gap:12px}.header-actions{margin-left:auto}.hero .container{grid-template-columns:1fr;min-height:auto}.hero h1{font-size:44px}.popular-grid,.market-grid,.score-strip,.how-grid{grid-template-columns:repeat(2,1fr)}.category-grid{grid-template-columns:1fr}.ranking-layout{grid-template-columns:1fr}.filter-card{position:static}.company-shell{grid-template-columns:1fr}.dashboard-grid{grid-template-columns:repeat(2,1fr)}.footer-grid{grid-template-columns:repeat(2,1fr)}}@media(max-width:640px){.container{width:min(100% - 24px,1180px)}.header-actions .btn:first-child{display:none}.brand span{display:none}.hero .container{padding:38px 0}.hero h1{font-size:38px}.hero-search{grid-template-columns:1fr}.popular-grid,.market-grid,.score-strip,.how-grid,.dashboard-grid{grid-template-columns:1fr}.table-head{display:none}.table-row{grid-template-columns:40px 1fr auto;padding:13px 10px}.table-row>div:nth-child(4),.table-row>div:nth-child(5){display:none}.company-title{display:block}.score-orb{text-align:left;border:0;padding:15px 0 0}.facts{grid-template-columns:1fr 1fr}.owner-cta{grid-template-columns:1fr}.footer-grid{grid-template-columns:1fr 1fr}.dashboard-grid .wide{grid-column:span 1}}''',encoding='utf-8')

# page components
def relprefix(depth): return '../'*depth

def brand(depth=0):
    p=relprefix(depth)
    return f'<a class="brand" href="{p}index.html"><img src="{p}assets/logo.png" alt="Texas Rated emblem"><span>TEXAS<small>RATED</small></span></a>'

def header(depth=0):
    p=relprefix(depth)
    return f'''<header class="site-header"><div class="container header-inner">{brand(depth)}<nav class="main-nav"><a href="{p}rankings.html">Rankings</a><a href="{p}categories.html">Categories</a><a href="{p}scores.html">Scores</a><a href="{p}fastest-rising.html">Fastest Rising</a><a href="{p}methodology.html">Methodology</a><a href="{p}businesses.html">For Businesses</a></nav><div class="header-actions"><a class="btn" href="{p}claim.html">Claim Your Profile</a><a class="btn navy" href="{p}login.html">Owner Login</a></div></div></header>'''

def footer(depth=0):
    p=relprefix(depth)
    return f'''<footer class="footer"><div class="container"><div class="footer-grid"><div>{brand(depth)}<p style="color:#9db0c6;font-size:13px;line-height:1.6">Public reputation data, Texas Rated Scores and company profiles for local Texas service businesses.</p></div><div><h4>Explore</h4><a href="{p}rankings.html">Rankings</a><a href="{p}categories.html">Categories</a><a href="{p}scores.html">Scores</a><a href="{p}fastest-rising.html">Fastest Rising</a></div><div><h4>For Businesses</h4><a href="{p}claim.html">Claim Profile</a><a href="{p}login.html">Owner Login</a><a href="{p}businesses.html">Business Benefits</a></div><div><h4>Popular</h4><a href="{p}rankings/austin/hvac.html">Austin HVAC</a><a href="{p}rankings/austin/plumbing.html">Austin Plumbing</a><a href="{p}rankings/san-antonio/roofing.html">San Antonio Roofing</a></div><div><h4>About</h4><a href="{p}methodology.html">Methodology</a><a href="{p}sitemap.xml">Sitemap</a></div></div><div class="footer-note">© 2026 Texas Rated. Rankings are informational and based on a dated public-data snapshot. Texas Rated does not guarantee service quality or outcomes.</div></div></footer>'''

def page(title,desc,body,depth=0,canonical=None,og_image=None,noindex=False,extra_head=''):
    p=relprefix(depth)
    canon=canonical or (BASE_URL+'/' if depth==0 else '')
    meta_robots='<meta name="robots" content="noindex,nofollow">' if noindex else '<meta name="robots" content="index,follow,max-image-preview:large">'
    canonical_tag=f'<link rel="canonical" href="{esc(canon)}">' if canon else ''
    og=f'''<meta property="og:type" content="website"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{esc(canon)}">'''
    if og_image: og+=f'<meta property="og:image" content="{esc(og_image)}">'
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><meta name="description" content="{esc(desc)}">{meta_robots}{canonical_tag}{og}<link rel="icon" type="image/png" href="{p}assets/favicon.png"><link rel="stylesheet" href="{p}assets/styles.css">{extra_head}</head><body>{header(depth)}{body}{footer(depth)}<script src="{p}assets/app.js"></script></body></html>'''

def category_icon(cat,depth=0):
    p=relprefix(depth); return f'<img class="service-medallion" src="{p}assets/icons/{slugify(cat)}.svg" alt="">'

def market_icon():
    return '<div class="market-pin"><svg viewBox="0 0 64 64" fill="none" stroke="white" stroke-width="3"><path d="M32 54s16-15 16-29a16 16 0 1 0-32 0c0 14 16 29 16 29Z"/><circle cx="32" cy="25" r="6"/></svg></div>'

def company_href(c,depth=0): return f'{relprefix(depth)}company/{c["slug"]}.html'

def group_top(market,cat,n=5): return groups.get((market,cat),[])[:n]

# HOME
featured=group_top('Austin','HVAC',5)
hero_rows=''.join(f'''<a class="hero-row" href="company/{c['slug']}.html"><div>#{i}</div><div><strong>{esc(c['name'])}</strong><small>{c['rating']:.1f} rating · {c['reviews']:,} reviews</small></div><div class="hero-score">{c['score']:.1f}<small>TR SCORE</small></div></a>''' for i,c in enumerate(featured,1))
opts_m=''.join(f'<option>{esc(m)}</option>' for m in MARKETS)
opts_c=''.join(f'<option>{esc(c)}</option>' for c in CATEGORIES)
# Popular combos: ensure nonempty
popular=[('Austin','HVAC'),('Austin','Plumbing'),('North Austin','Landscaping'),('South Austin','Tree Service'),('Austin','House Cleaning'),('San Antonio','Roofing'),('Austin','Dumpster Rental'),('Austin','Handyman')]
popular_html=''
for market,cat in popular:
    arr=groups.get((market,cat),[])
    top=arr[0] if arr else None
    popular_html+=f'''<a class="ranking-tile" href="rankings/{slugify(market)}/{slugify(cat)}.html">{category_icon(cat)}<div><h3>{esc(market)} {esc(cat)}</h3><p>{len(arr)} companies tracked</p><div class="tile-top">{('Top score: '+esc(top['name'])) if top else 'View coverage'} →</div></div></a>'''
market_html=''
for market in MARKETS:
    market_companies={c['slug']:c for (m,cat),arr in groups.items() if m==market for c in arr}
    cats=sorted({cat for (m,cat) in groups if m==market and groups[(m,cat)]})
    market_html+=f'''<a class="market-card" href="rankings/{slugify(market)}.html">{market_icon()}<h3>{esc(market)}</h3><p>{esc(MARKET_DESCRIPTIONS[market])}</p><div class="market-meta">{len(market_companies)} companies · {len(cats)} categories →</div></a>'''
top_global=sorted(rows,key=lambda c:(-c['score'],-c['reviews']))[:4]
score_cards=''.join(f'''<a class="score-card" href="company/{c['slug']}.html"><div class="big">{c['score']:.1f}</div><h3>{esc(c['name'])}</h3><p>{esc(c['primary_market'])} · {esc(c['categories'][0])}</p></a>''' for c in top_global)
home_body=f'''<section class="hero"><div class="container"><div><div class="eyebrow">Independent local service-company ratings</div><h1>Find Texas's highest-rated local service companies.</h1><p>Compare public reputation signals, Texas Rated Scores and detailed company profiles across Austin and San Antonio markets.</p><form class="hero-search" action="rankings.html"><select class="select" name="market">{opts_m}</select><select class="select" name="category">{opts_c}</select><button class="btn red" type="submit">View Rankings →</button></form></div><div class="hero-panel"><div class="hero-panel-head"><h3>Austin HVAC — Top 5</h3><a href="rankings/austin/hvac.html" style="color:#9cc4ff;font-size:12px;font-weight:800">Full rankings →</a></div>{hero_rows}</div></div></section>
<section class="section"><div class="container"><div class="section-title"><div><h2>Popular Rankings</h2><p>High-demand service rankings with real company profiles.</p></div><a class="text-link" href="rankings.html">Browse all →</a></div><div class="popular-grid">{popular_html}</div></div></section>
<section class="section soft"><div class="container"><div class="section-title"><div><h2>Texas Markets</h2><p>Browse coverage by local market.</p></div><a class="text-link" href="categories.html#markets">Explore markets →</a></div><div class="market-grid">{market_html}</div></div></section>
<section class="section"><div class="container"><div class="section-title"><div><h2>Highest Texas Rated Scores</h2><p>Current public-data score leaders across tracked categories.</p></div><a class="text-link" href="scores.html">See Scores →</a></div><div class="score-strip">{score_cards}</div></div></section>
<section class="section soft"><div class="container"><div class="section-title"><div><h2>How Texas Rated works</h2><p>Simple enough for consumers, useful enough for business owners.</p></div></div><div class="how-grid"><div class="how-card"><div class="how-num">1</div><h3>Public data snapshot</h3><p>We collect public ratings, review counts and company information and date every refresh.</p></div><div class="how-card"><div class="how-num">2</div><h3>Texas Rated Score</h3><p>Public reputation is adjusted for review depth so a perfect score on a handful of reviews does not automatically lead the market.</p></div><div class="how-card"><div class="how-num">3</div><h3>Company profiles</h3><p>Every tracked company gets a profile page. Owners can claim and verify theirs to add richer, confirmed information.</p></div><div class="how-card"><div class="how-num">4</div><h3>Owner tools</h3><p>Claimed businesses can manage their profile, receive leads and messages, track rank, and install a live Texas Rated emblem.</p></div></div></div></section>
<section class="section"><div class="container"><div class="owner-cta"><div><h2>Own a Texas service company?</h2><p>Your Texas Rated profile may already be live. Claim it to verify information, activate your website link, receive leads and unlock owner tools.</p></div><a class="btn red" href="claim.html">Claim Your Profile →</a></div></div></section>'''
(ROOT/'index.html').write_text(page('Texas Rated | Texas Service Company Rankings','Texas Rated publishes local service-company rankings, Texas Rated Scores and company profiles across Texas markets.',home_body,canonical=f'{BASE_URL}/',og_image=f'{BASE_URL}/assets/logo.png'),encoding='utf-8')

# CATEGORIES PAGE distinct: category cards + top 5
cat_cards=''
for cat in CATEGORIES:
    arr=sorted([c for c in rows if cat in c['categories']],key=lambda c:(-c['score'],-c['reviews']))[:5]
    top_rows=''.join(f'''<a class="top-five-row" href="company/{c['slug']}.html"><span class="rank">#{i}</span><strong>{esc(c['name'])}<small style="display:block;color:#7b8ca2;font-weight:500">{esc(c['primary_market'])}</small></strong><span class="score">{c['score']:.1f}</span></a>''' for i,c in enumerate(arr,1))
    cat_cards+=f'''<article class="category-card" id="{slugify(cat)}"><div class="category-head">{category_icon(cat)}<div><h2>{esc(cat)}</h2><p>{esc(CATEGORY_DESCRIPTIONS[cat])}</p></div></div><div class="top-five">{top_rows}</div><div class="category-actions"><small>{sum(1 for c in rows if cat in c['categories'])} companies tracked</small><a class="text-link" href="rankings/{slugify(cat)}.html">View {esc(cat)} rankings →</a></div></article>'''
cat_body=f'''<section class="page-hero"><div class="container"><div class="eyebrow">Service categories</div><h1>Browse Texas service categories.</h1><p>Each category shows the current top five Texas Rated Scores across tracked markets, with links to every company's profile and local-market rankings.</p></div></section><section class="section"><div class="container"><div class="category-grid">{cat_cards}</div></div></section><section class="section soft" id="markets"><div class="container"><div class="section-title"><div><h2>Texas Markets</h2><p>Current launch coverage.</p></div></div><div class="market-grid">{market_html}</div></div></section>'''
(ROOT/'categories.html').write_text(page('Service Categories | Texas Rated','Browse Texas Rated service categories and top local service companies.',cat_body,canonical=f'{BASE_URL}/categories.html'),encoding='utf-8')

# SCORES PAGE
score_rows=sorted(rows,key=lambda c:(-c['score'],-c['reviews']))
score_table=''.join(f'''<a class="table-row" data-score-row data-markets="{esc('|'.join(c['markets']))}" data-categories="{esc('|'.join(c['categories']))}" href="company/{c['slug']}.html"><div class="rank">#{i}</div><div class="company-cell"><strong>{esc(c['name'])}</strong><small>{esc(c['primary_market'])} · {esc(', '.join(c['categories']))}</small></div><div class="tr-score">{c['score']:.1f}</div><div><span class="rating-stars">★</span> {c['rating']:.1f}</div><div>{c['reviews']:,} reviews</div></a>''' for i,c in enumerate(score_rows,1))
score_body=f'''<section class="page-hero"><div class="container"><div class="eyebrow">Texas Rated Score</div><h1>Compare Texas Rated Scores.</h1><p>The Texas Rated Score is a 100-point public-reputation score that adjusts ratings for review depth and can include a small verified-profile-data component after a business claims its page.</p></div></section><section class="section"><div class="container ranking-layout" data-filter-group><aside class="filter-card"><h3>Filter Scores</h3><label>Market</label><select class="select" name="market"><option value="">All markets</option>{''.join(f'<option>{esc(m)}</option>' for m in MARKETS)}</select><label>Category</label><select class="select" name="category"><option value="">All categories</option>{''.join(f'<option>{esc(c)}</option>' for c in CATEGORIES)}</select><div class="notice">Scores use the public-data snapshot dated {fmt_date(DATA_REFRESH)}. Rankings can change when public data is refreshed or verified profile data is added.</div></aside><div><div class="ranking-table"><div class="table-head"><div>Rank</div><div>Company</div><div>TR Score</div><div>Rating</div><div>Reviews</div></div>{score_table}</div></div></div></section>'''
(ROOT/'scores.html').write_text(page('Texas Rated Scores | Compare Service Companies','Compare Texas Rated Scores across tracked Texas service companies and markets.',score_body,canonical=f'{BASE_URL}/scores.html'),encoding='utf-8')

# RANKINGS INDEX
ranking_cards=''
for market in MARKETS:
    for cat in CATEGORIES:
        arr=groups.get((market,cat),[])
        if not arr: continue
        top=arr[0]
        ranking_cards+=f'''<a class="ranking-tile" href="rankings/{slugify(market)}/{slugify(cat)}.html">{category_icon(cat)}<div><h3>{esc(market)} {esc(cat)}</h3><p>{len(arr)} companies · refreshed {fmt_date(DATA_REFRESH)}</p><div class="tile-top">#1 {esc(top['name'])} · {top['score']:.1f} →</div></div></a>'''
rank_body=f'''<section class="page-hero"><div class="container"><div class="eyebrow">Local rankings</div><h1>Texas service-company rankings.</h1><p>Choose a market and service category to compare current Texas Rated Scores and open detailed company profiles.</p></div></section><section class="section"><div class="container"><div class="popular-grid">{ranking_cards}</div></div></section>'''
(ROOT/'rankings.html').write_text(page('Service Company Rankings | Texas Rated','Browse Texas Rated local service-company rankings by market and category.',rank_body,canonical=f'{BASE_URL}/rankings.html'),encoding='utf-8')

# CATEGORY OVERVIEW PAGES
for cat in CATEGORIES:
    arr=sorted([c for c in rows if cat in c['categories']],key=lambda c:(-c['score'],-c['reviews']))
    if not arr: continue
    top_rows=''.join(f'''<a class="table-row" href="../company/{c['slug']}.html"><div class="rank">#{i}</div><div class="company-cell"><strong>{esc(c['name'])}</strong><small>{esc(c['primary_market'])}</small></div><div class="tr-score">{c['score']:.1f}</div><div><span class="rating-stars">★</span> {c['rating']:.1f}</div><div>{c['reviews']:,} reviews</div></a>''' for i,c in enumerate(arr,1))
    market_links=''.join(f'''<a class="ranking-tile" href="{slugify(m)}/{slugify(cat)}.html">{category_icon(cat,1)}<div><h3>{esc(m)} {esc(cat)}</h3><p>{len(groups.get((m,cat),[]))} companies tracked</p><div class="tile-top">View local ranking →</div></div></a>''' for m in MARKETS if groups.get((m,cat)))
    body=f'''<section class="page-hero"><div class="container"><div class="eyebrow">{esc(cat)} ratings</div><h1>Top Rated {esc(cat)} Companies in Texas</h1><p>{esc(CATEGORY_DESCRIPTIONS[cat])} Compare Texas Rated Scores across currently tracked Austin and San Antonio markets.</p></div></section><section class="section"><div class="container"><div class="section-title"><div><h2>Browse by market</h2><p>Local rankings determine awards and market position.</p></div></div><div class="popular-grid">{market_links}</div></div></section><section class="section soft"><div class="container"><div class="section-title"><div><h2>Current {esc(cat)} score leaders</h2><p>Cross-market score comparison from the {fmt_date(DATA_REFRESH)} data snapshot.</p></div></div><div class="ranking-table"><div class="table-head"><div>Rank</div><div>Company</div><div>TR Score</div><div>Rating</div><div>Reviews</div></div>{top_rows}</div></div></section>'''
    (ROOT/'rankings'/f'{slugify(cat)}.html').write_text(page(f'Top Rated {cat} Companies in Texas | Texas Rated',f'Compare Texas Rated Scores and local {cat} rankings across tracked Texas markets.',body,depth=1,canonical=f'{BASE_URL}/rankings/{slugify(cat)}.html'),encoding='utf-8')

# MARKET OVERVIEW PAGES
for market in MARKETS:
    cards=''
    for cat in CATEGORIES:
        arr=groups.get((market,cat),[])
        if not arr: continue
        top=arr[0]
        cards+=f'''<a class="ranking-tile" href="{slugify(market)}/{slugify(cat)}.html">{category_icon(cat,1)}<div><h3>{esc(cat)}</h3><p>{len(arr)} companies tracked</p><div class="tile-top">#1 {esc(top['name'])} · {top['score']:.1f} →</div></div></a>'''
    market_companies={c['slug']:c for (m,cat),arr in groups.items() if m==market for c in arr}
    body=f'''<section class="page-hero"><div class="container"><div class="eyebrow">Texas Rated market</div><h1>{esc(market)} Service Company Rankings</h1><p>{esc(MARKET_DESCRIPTIONS[market])} Browse {len(market_companies)} tracked companies across available service categories.</p></div></section><section class="section"><div class="container"><div class="popular-grid">{cards}</div></div></section>'''
    (ROOT/'rankings'/f'{slugify(market)}.html').write_text(page(f'{market} Service Company Rankings | Texas Rated',f'Browse Texas Rated service-company rankings across {market}.',body,depth=1,canonical=f'{BASE_URL}/rankings/{slugify(market)}.html'),encoding='utf-8')

# LOCAL RANKING PAGES
for (market,cat),arr in sorted(groups.items()):
    if market not in MARKETS or cat not in CATEGORIES or not arr: continue
    outdir=ROOT/'rankings'/slugify(market); outdir.mkdir(parents=True,exist_ok=True)
    rows_html=''
    for i,c in enumerate(arr,1):
        claimed_badge='<span class="badge">Owner verified</span>' if c['verified'] else '<span class="badge unclaimed">Profile unclaimed</span>'
        rows_html+=f'''<a class="table-row" href="../../company/{c['slug']}.html"><div class="rank">#{i}</div><div class="company-cell"><strong>{esc(c['name'])} {claimed_badge}</strong><small>{esc(c.get('city'))}, TX</small></div><div class="tr-score">{c['score']:.1f}</div><div><span class="rating-stars">★</span> {c['rating']:.1f}</div><div>{c['reviews']:,} reviews</div></a>'''
    desc=f'Compare {len(arr)} {market} {cat} companies using Texas Rated Scores, public ratings and review counts. Data snapshot {fmt_date(DATA_REFRESH)}.'
    body=f'''<section class="page-hero"><div class="container"><div class="eyebrow">Texas Rated Rankings</div><h1>Top Rated {esc(cat)} Companies in {esc(market)}</h1><p>{esc(desc)}</p><div class="share-row"><button class="btn" data-share data-title="Top Rated {esc(cat)} Companies in {esc(market)}" data-text="See the latest Texas Rated ranking.">Share Ranking</button><a class="btn" href="../../methodology.html">How Scores Work</a></div></div></section><section class="section"><div class="container"><div class="ranking-table"><div class="table-head"><div>Rank</div><div>Company</div><div>TR Score</div><div>Rating</div><div>Reviews</div></div>{rows_html}</div><p class="source-note">Source: public business listing snapshot collected {fmt_date(DATA_REFRESH)}. Ratings and review counts can change. Texas Rated is not affiliated with the listed companies unless a profile is explicitly marked owner verified.</p></div></section>'''
    title=f'Top Rated {cat} Companies in {market} | Texas Rated'
    (outdir/f'{slugify(cat)}.html').write_text(page(title,desc,body,depth=2,canonical=f'{BASE_URL}/rankings/{slugify(market)}/{slugify(cat)}.html'),encoding='utf-8')

# COMPANY PAGES
for c in rows:
    ranks=sorted([(m,cat,r) for (m,cat),r in rank_positions[c['slug']].items()],key=lambda x:(x[0]!=c['primary_market'],x[2],x[0],x[1]))
    rank_html=''.join(f'''<a class="rank-item" href="../rankings/{slugify(m)}/{slugify(cat)}.html"><span>{esc(m)} {esc(cat)}</span><b>#{r}</b></a>''' for m,cat,r in ranks)
    primary_rank=next((r for m,cat,r in ranks if m==c['primary_market'] and cat==c['categories'][0]),ranks[0][2] if ranks else '-')
    verified=c['verified'] and c['claimed']
    status='<span class="badge">Owner verified</span>' if verified else '<span class="badge unclaimed">Profile unclaimed</span>'
    website=''
    if c.get('website') and verified:
        rel='' if int(primary_rank)<=10 else ' rel="ugc nofollow"'
        website=f'<a class="btn primary" href="{esc(c["website"])}" target="_blank"{rel}>Visit Website ↗</a>'
    actions=website + f'<a class="btn" href="../claim.html?company={esc(c["slug"])}">{("Manage Profile" if verified else "Claim This Profile")}</a><button class="btn" data-share data-title="{esc(c["name"])} | Texas Rated">Share</button>'
    facts=f'''<div class="facts"><div class="fact"><small>Public rating</small><strong>{c['rating']:.1f} ★</strong></div><div class="fact"><small>Review count</small><strong>{c['reviews']:,}</strong></div><div class="fact"><small>Data refreshed</small><strong>{fmt_date(c.get('source_updated') or DATA_REFRESH)}</strong></div></div>'''
    break_html=''.join(f'''<div><div style="display:flex;justify-content:space-between;font-size:12px"><span>{esc(k)}</span><strong>{v:.1f} / {85 if k=='Adjusted reputation' else 10 if k=='Review depth' else 5}</strong></div><div class="meter"><span style="width:{min(100,(v/(85 if k=='Adjusted reputation' else 10 if k=='Review depth' else 5))*100):.0f}%"></span></div></div>''' for k,v in c['score_breakdown'].items())
    addr=', '.join(x for x in [c.get('address')] if x)
    services=', '.join(c['services']) if c['services'] else ', '.join(c['categories'])
    claim_box='' if verified else f'''<div class="claim-box"><h3>Own {esc(c['name'])}?</h3><p>Claim this page to verify information, activate your website link, edit services and service areas, receive customer leads and messages, and unlock your live Texas Rated emblem.</p><a class="btn red" href="../claim.html?company={esc(c['slug'])}">Claim This Profile →</a></div>'''
    body=f'''<section class="company-hero"><div class="container company-shell"><main class="company-main"><div class="company-title"><div><div class="eyebrow">{esc(c['primary_market'])} · {esc(', '.join(c['categories']))}</div><h1>{esc(c['name'])}</h1><p>{status} · Primary local rank #{primary_rank}</p></div><div class="score-orb"><strong>{c['score']:.1f}</strong><span>TEXAS RATED SCORE</span></div></div>{facts}<p style="line-height:1.65;color:#52667f">{esc(c.get('description'))}</p><div class="facts"><div class="fact"><small>Phone</small><strong>{esc(c.get('phone') or 'Not listed')}</strong></div><div class="fact"><small>Address / area</small><strong>{esc(c.get('address') or c.get('city')+', TX')}</strong></div><div class="fact"><small>Services</small><strong>{esc(services)}</strong></div></div><div class="share-row">{actions}</div>{claim_box}<p class="source-note">Public profile data source: {esc(c.get('source'))}. Snapshot date: {fmt_date(c.get('source_updated') or DATA_REFRESH)}. This page is an independent Texas Rated profile and is not controlled by the company unless marked owner verified.</p></main><aside class="company-side"><h3>Current Rankings</h3><div class="rank-list">{rank_html or '<p class="muted">No current local ranking.</p>'}</div><h3 style="margin-top:24px">Texas Rated Score</h3><div class="score-break">{break_html}</div><p class="source-note">Verified profile data can contribute up to 5 points after a company claims and confirms its information. Paid participation, lead acceptance and emblem installation do not increase rank.</p></aside></div></section>'''
    addr_json={"@type":"PostalAddress","streetAddress":c.get('address',''),"addressLocality":c.get('city',''),"addressRegion":"TX","postalCode":c.get('zip',''),"addressCountry":"US"}
    schema={"@context":"https://schema.org","@type":"LocalBusiness","name":c['name'],"url":f'{BASE_URL}/company/{c["slug"]}.html',"telephone":c.get('phone') or None,"address":addr_json,"aggregateRating":{"@type":"AggregateRating","ratingValue":c['rating'],"reviewCount":c['reviews']}}
    schema={k:v for k,v in schema.items() if v not in (None,'')}
    extra=f'<script type="application/ld+json">{json.dumps(schema,ensure_ascii=False)}</script>'
    desc=f"{c['name']} in {c['city']}, TX has a Texas Rated Score of {c['score']:.1f} based on a public-data snapshot including a {c['rating']:.1f} rating and {c['reviews']:,} reviews."
    title=f"{c['name']} {c['city']} {c['categories'][0]} | Texas Rated Score & Profile"
    (ROOT/'company'/f'{c["slug"]}.html').write_text(page(title,desc,body,depth=1,canonical=f'{BASE_URL}/company/{c["slug"]}.html',extra_head=extra),encoding='utf-8')

# CLAIM
company_options=''.join(f'<option value="{esc(c["slug"])}">{esc(c["name"])} — {esc(c["city"])} ({esc(c["categories"][0])})</option>' for c in sorted(rows,key=lambda c:c['name']))
claim_body=f'''<section class="page-hero"><div class="container"><div class="eyebrow">For business owners</div><h1>Claim your Texas Rated profile.</h1><p>Your company page may already be live. Verification unlocks owner-controlled information, your website link, lead delivery, messages, ranking tools and the live Texas Rated emblem.</p></div></section><section class="section"><div class="container" style="display:grid;grid-template-columns:1.1fr .9fr;gap:22px"><div class="card form-card"><h2 style="margin-top:0">1. Find your company</h2><label>Company</label><select class="select">{company_options}</select><label>Work email</label><input class="input" placeholder="you@company.com"><label>Business phone</label><input class="input" placeholder="(512) 555-0123"><label>Your role</label><select class="select"><option>Owner</option><option>Manager</option><option>Authorized marketing / admin</option></select><div style="margin-top:18px"><a class="btn primary" href="dashboard.html">Verify & Continue →</a></div><p class="source-note">Production verification will require a work-email, business-phone or other ownership-control check before owner-only features are activated.</p></div><div><div class="card"><div class="eyebrow">Unlocked after verification</div><h2>Turn your profile into an owner asset.</h2><div class="how-grid" style="grid-template-columns:1fr 1fr"><div class="how-card"><b>Website link</b><p>Activate a direct business website link on your profile.</p></div><div class="how-card"><b>Leads + messages</b><p>Choose where and what jobs you want automatically emailed.</p></div><div class="how-card"><b>Live emblem</b><p>Install once; your displayed recognition updates as rankings change.</p></div><div class="how-card"><b>Rank tracking</b><p>Monitor your score, profile strength and local competition.</p></div></div></div><div class="card" style="margin-top:16px;background:#f5f9ff"><div class="eyebrow">Private owner resource</div><h2>What is your business worth?</h2><p class="muted">Keep valuation separate from Texas Rated. Use TexasBusinessWorth.com for a private business-value estimate and transaction benchmarks.</p><a class="btn navy" href="https://texasbusinessworth.com/" target="_blank">Check My Business Value ↗</a></div></div></div></section>'''
(ROOT/'claim.html').write_text(page('Claim Your Business Profile | Texas Rated','Claim and verify your Texas Rated business profile.',claim_body,canonical=f'{BASE_URL}/claim.html',noindex=True),encoding='utf-8')

# FOR BUSINESSES
business_body='''<section class="page-hero"><div class="container"><div class="eyebrow">For Texas service businesses</div><h1>Your public reputation, made useful.</h1><p>Claim your existing Texas Rated profile to control verified business information, track your score and rankings, receive customer opportunities and display live recognition on your own website.</p></div></section><section class="section"><div class="container"><div class="how-grid"><div class="how-card"><div class="how-num">1</div><h3>Claim what already exists</h3><p>No blank profile setup. Find the public page already associated with your company and verify ownership.</p></div><div class="how-card"><div class="how-num">2</div><h3>Improve verified data</h3><p>Add services, service areas and company information. Verified profile data can contribute a bounded part of your score.</p></div><div class="how-card"><div class="how-num">3</div><h3>Receive opportunities</h3><p>Turn lead delivery on or off and select the services and markets you actually want.</p></div><div class="how-card"><div class="how-num">4</div><h3>Display your emblem</h3><p>Install the Texas Rated widget once. It updates automatically if your ranking or recognition changes.</p></div></div><div class="owner-cta" style="margin-top:30px"><div><h2>Find your company and claim it free.</h2><p>Verification, profile management and owner dashboard access begin with your existing company page.</p></div><a class="btn red" href="claim.html">Claim Your Profile →</a></div></div></section>'''
(ROOT/'businesses.html').write_text(page('For Texas Service Businesses | Texas Rated','Claim your Texas Rated profile, manage verified information, receive leads and track your rankings.',business_body,canonical=f'{BASE_URL}/businesses.html'),encoding='utf-8')

# LOGIN + Dashboard demo, noindex
login_body='''<section class="page-hero"><div class="container"><div class="eyebrow">Verified owners</div><h1>Owner Login</h1><p>Access profile controls, leads, messages, ranking tools and your live emblem.</p></div></section><section class="section"><div class="container" style="max-width:560px"><div class="card form-card"><label>Email</label><input class="input" value="owner@example.com"><label>Password</label><input class="input" type="password" value="password"><div style="margin-top:17px"><a class="btn primary" href="dashboard.html">Login to Dashboard →</a></div><p class="source-note">Demo authentication only in this static build.</p></div></div></section>'''
(ROOT/'login.html').write_text(page('Owner Login | Texas Rated','Texas Rated verified-owner login.',login_body,canonical=f'{BASE_URL}/login.html',noindex=True),encoding='utf-8')
# Dashboard sample based on current top Austin HVAC, intentionally demo / not claimed factual.
sample=featured[0] if featured else rows[0]
dashboard_body=f'''<section class="dashboard-hero"><div class="container" style="display:flex;justify-content:space-between;gap:25px;align-items:center"><div><div class="eyebrow" style="color:#91bdff">OWNER DASHBOARD DEMO</div><h1 style="margin:5px 0">Your Company</h1><div style="color:#bed2e9">Austin HVAC · Verified owner view</div></div><div class="profile-progress"><div class="progress-ring"></div><div><b>Profile strength 78%</b><div style="color:#b9cee7;font-size:12px">Complete verified data to improve profile quality</div></div></div></div></section><section class="section"><div class="container"><div class="dashboard-grid"><div class="dash-card"><h3>Your rank</h3><div class="big">#4</div><p class="muted">Austin HVAC</p><a class="text-link" href="rankings/austin/hvac.html">View ranking →</a></div><div class="dash-card"><h3>Texas Rated Score</h3><div class="big" style="color:var(--green)">93.1</div><p class="muted">+0.8 after last verified profile update</p></div><div class="dash-card"><h3>Leads</h3><div class="big">3</div><p>New opportunities</p><p><span class="badge">Accepting leads: ON</span></p></div><div class="dash-card"><h3>Messages</h3><div class="big">2</div><p class="muted">Unread conversations</p></div><div class="dash-card wide"><h3>Competition</h3><div class="rank-item"><span>#3 Nearby competitor</span><b>93.8</b></div><div class="rank-item"><span>#4 YOU</span><b>93.1</b></div><div class="rank-item"><span>#5 Nearby competitor</span><b>92.7</b></div></div><div class="dash-card"><h3>Profile traffic</h3><div class="big">382</div><p class="muted">Profile views · 71 website clicks</p></div><div class="dash-card"><h3>Live emblem</h3><div class="big">LIVE</div><p class="muted">Installed · 6,821 impressions</p></div><div class="dash-card wide"><h3>Lead delivery</h3><p><b>Email new matching leads automatically</b></p><p class="muted">HVAC repair · replacements · Austin / North Austin</p><button class="btn primary">Edit Lead Settings</button></div><div class="dash-card wide"><h3>Private business value</h3><p class="muted">Curious what your business may be worth? Keep the valuation process private on TexasBusinessWorth.com.</p><a class="btn navy" href="https://texasbusinessworth.com/" target="_blank">Check Business Value ↗</a></div></div></div></section>'''
(ROOT/'dashboard.html').write_text(page('Owner Dashboard Demo | Texas Rated','Texas Rated owner dashboard demo.',dashboard_body,canonical=f'{BASE_URL}/dashboard.html',noindex=True),encoding='utf-8')

# METHODOLOGY
method_body=f'''<section class="page-hero"><div class="container"><div class="eyebrow">Transparent scoring</div><h1>How the Texas Rated Score works.</h1><p>The launch score is intentionally simple and auditable: public rating strength is adjusted for review depth, and a small verified-profile-data component becomes available after ownership verification.</p></div></section><section class="section"><div class="container"><div class="how-grid"><div class="how-card"><div class="how-num">85</div><h3>Adjusted reputation</h3><p>Up to 85 points. Ratings are Bayesian-adjusted toward a market prior so a 5.0 score with very few reviews does not automatically outrank established companies.</p></div><div class="how-card"><div class="how-num">10</div><h3>Review depth</h3><p>Up to 10 points. More public reviews increase confidence, with diminishing returns so enormous review counts do not overwhelm the score.</p></div><div class="how-card"><div class="how-num">5</div><h3>Verified profile data</h3><p>Up to 5 points after a company claims and verifies accurate business information. Unclaimed companies receive zero profile-data points.</p></div><div class="how-card"><div class="how-num">0</div><h3>Pay-to-rank points</h3><p>Advertising, accepting leads, installing the emblem or linking to Texas Rated do not increase the score.</p></div></div><div class="notice" style="margin-top:24px">Current ratings and review counts are a dated public-listing snapshot from {fmt_date(DATA_REFRESH)}. They are not presented as live values. Texas Rated should refresh the dataset on a recurring schedule.</div></div></section>'''
(ROOT/'methodology.html').write_text(page('Texas Rated Score Methodology','See how Texas Rated Scores are calculated from public reputation data and verified profile information.',method_body,canonical=f'{BASE_URL}/methodology.html'),encoding='utf-8')

# FASTEST RISING (historical only)
if have_momentum and momentum:
    mom_cards=''.join(f'''<a class="score-card" href="company/{c['slug']}.html"><div class="big">+{delta:.1f}</div><h3>{esc(c['name'])}</h3><p>{esc(c['primary_market'])} · {esc(c['categories'][0])} · current {c['score']:.1f}</p></a>''' for delta,c in momentum[:24])
    fast_body=f'''<section class="page-hero"><div class="container"><div class="eyebrow">Score movement</div><h1>Fastest-Rising Texas Service Companies</h1><p>Companies with the largest Texas Rated Score gains between {fmt_date(all_dates[0])} and {fmt_date(all_dates[-1])}.</p></div></section><section class="section"><div class="container"><div class="score-strip">{mom_cards}</div></div></section>'''
else:
    fast_body=f'''<section class="page-hero"><div class="container"><div class="eyebrow">Score movement</div><h1>Fastest-Rising Texas Service Companies</h1><p>Momentum rankings require actual historical score snapshots. Texas Rated does not invent movement from a single dataset.</p></div></section><section class="section"><div class="container"><div class="empty-state"><img src="assets/logo.png" alt=""><h2>Baseline tracking has started.</h2><p>The first public-data baseline is dated {fmt_date(DATA_REFRESH)}. After the next data refresh, this page can rank companies by real Texas Rated Score movement and show owners who is gaining or slipping.</p><a class="btn primary" href="scores.html">See Current Scores →</a></div></div></section>'''
(ROOT/'fastest-rising.html').write_text(page('Fastest-Rising Texas Service Companies | Texas Rated','Track real Texas Rated Score movement after multiple data snapshots are available.',fast_body,canonical=f'{BASE_URL}/fastest-rising.html'),encoding='utf-8')

# WIDGETS: only meaningful once claimed, but generated for every company; unclaimed gets claim state.
for c in rows:
    ranks=rank_positions[c['slug']]
    primary_rank=ranks.get((c['primary_market'],c['categories'][0]), min(ranks.values()) if ranks else '-')
    if c['claimed'] and c['verified']:
        status='TOP 10' if isinstance(primary_rank,int) and primary_rank<=10 else 'VERIFIED COMPANY'
        rank_display=f'#{primary_rank}' if isinstance(primary_rank,int) and primary_rank<=10 else '✓'
        sub=f'{c["primary_market"]} {c["categories"][0]}'
    else:
        status='PROFILE'; rank_display='—'; sub='UNCLAIMED'
    widget=f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="../assets/styles.css"></head><body class="widget-body"><a class="widget-link" target="_blank" href="../company/{c['slug']}.html"><div class="widget"><div class="w-brand">TEXAS RATED</div><div class="w-top">{esc(status)}</div><div class="w-cat">{esc(sub)}</div><div class="w-rank">{rank_display}</div><div class="w-year">CURRENT STATUS · 2026</div></div></a></body></html>'''
    (ROOT/'widget'/f'{c["slug"]}.html').write_text(widget,encoding='utf-8')

# JSON export for optional client/server use
export=[]
for c in rows:
    x=dict(c); x['rankings']=[{'market':m,'category':cat,'rank':r} for (m,cat),r in rank_positions[c['slug']].items()]
    export.append(x)
(ROOT/'data'/'companies.json').write_text(json.dumps(export,ensure_ascii=False,indent=2),encoding='utf-8')

# sitemap/robots
urls=['','categories.html','scores.html','rankings.html','fastest-rising.html','methodology.html','businesses.html']
urls += [f'company/{c["slug"]}.html' for c in rows]
urls += [f'rankings/{slugify(cat)}.html' for cat in CATEGORIES if any(cat in c['categories'] for c in rows)]
urls += [f'rankings/{slugify(m)}.html' for m in MARKETS]
urls += [f'rankings/{slugify(m)}/{slugify(cat)}.html' for (m,cat),arr in groups.items() if arr and m in MARKETS and cat in CATEGORIES]
sitemap='<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+''.join(f'<url><loc>{BASE_URL}/{u}</loc><lastmod>{DATA_REFRESH}</lastmod></url>\n' for u in urls)+'</urlset>\n'
(ROOT/'sitemap.xml').write_text(sitemap,encoding='utf-8')
(ROOT/'robots.txt').write_text(f'User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n',encoding='utf-8')

print(f'Built {len(rows)} company pages, {sum(1 for k,a in groups.items() if a and k[0] in MARKETS and k[1] in CATEGORIES)} ranking pages, {len(CATEGORIES)} category cards.')
