from pathlib import Path
import csv, math, re
from datetime import date
ROOT=Path(__file__).resolve().parents[1]
MASTER=ROOT/'data'/'companies.csv'; OUT=ROOT/'data'/'score_history.csv'
def b(v): return str(v).strip().lower() in {'1','true','yes','y'}
def slugify(s): return re.sub(r'-+','-',re.sub(r'[^a-z0-9]+','-',(s or '').lower())).strip('-')
def calc(r):
    rating=float(r.get('rating') or 0); reviews=max(0,int(float(r.get('reviews') or 0))); pm=4.4; pw=40
    adj=(reviews/(reviews+pw))*rating+(pw/(reviews+pw))*pm
    rep=adj/5*85; depth=min(10,10*math.log1p(reviews)/math.log1p(2000)); profile=5*(max(0,min(100,int(float(r.get('profile_strength') or 0))))/100) if b(r.get('claimed')) else 0
    return round(min(100,rep+depth+profile),1)
with MASTER.open(newline='',encoding='utf-8-sig') as f: rows=list(csv.DictReader(f))
existing=[]
if OUT.exists():
    with OUT.open(newline='',encoding='utf-8-sig') as f: existing=list(csv.DictReader(f))
today=str(date.today()); existing=[r for r in existing if r.get('date')!=today]
for r in rows:
    existing.append({'date':today,'slug':r.get('slug') or slugify(f"{r.get('name')} {r.get('city') or r.get('primary_market')}"),'name':r.get('name',''),'score':calc(r),'rating':r.get('rating',''),'reviews':r.get('reviews','')})
with OUT.open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=['date','slug','name','score','rating','reviews']); w.writeheader(); w.writerows(existing)
print(f'Saved {len(rows)} score snapshots for {today}.')
