from pathlib import Path
import argparse, csv, re, subprocess, sys

ROOT=Path(__file__).resolve().parents[1]
MASTER=ROOT/'data'/'companies.csv'

BOOL_FIELDS={'claimed','verified','independent'}
INT_FIELDS={'reviews','profile_strength'}
FLOAT_FIELDS={'rating'}
PRESERVE_IF_BLANK={'claimed','verified','profile_strength','website','independent','services','description'}


def norm(s): return re.sub(r'[^a-z0-9]+',' ',(s or '').lower()).strip()
def slugify(s): return re.sub(r'-+','-',re.sub(r'[^a-z0-9]+','-',(s or '').lower())).strip('-')
def load(path):
    with Path(path).open(newline='',encoding='utf-8-sig') as f: return list(csv.DictReader(f))
def key(row):
    if row.get('external_id','').strip(): return ('external',row['external_id'].strip().lower())
    if row.get('phone','').strip(): return ('phone',re.sub(r'\D','',row['phone']))
    return ('namecity',norm(row.get('name')),norm(row.get('city') or row.get('primary_market')))

p=argparse.ArgumentParser(description='Merge new or refreshed companies into Texas Rated master data.')
p.add_argument('file',help='CSV to import')
p.add_argument('--build',action='store_true',help='Rebuild all static pages after import')
args=p.parse_args()

master=load(MASTER); incoming=load(args.file)
if not incoming: sys.exit('No rows found in import file.')
headers=list(master[0].keys()) if master else list(incoming[0].keys())
for extra in ['external_id','slug']:
    if extra not in headers: headers.append(extra)
# Ensure every incoming header can be retained.
for row in incoming:
    for h in row:
        if h not in headers: headers.append(h)

index={key(r):i for i,r in enumerate(master)}
added=updated=0
for row in incoming:
    row={k:(v or '').strip() for k,v in row.items()}
    if not row.get('name'): print('Skipping row without name'); continue
    if not row.get('categories'): print(f"Skipping {row['name']}: categories required"); continue
    if not row.get('primary_market') and not row.get('markets'): print(f"Skipping {row['name']}: primary_market or markets required"); continue
    k=key(row)
    if k in index:
        old=master[index[k]]
        for h in headers:
            new=row.get(h,'')
            if new!='' or h not in PRESERVE_IF_BLANK:
                if new!='': old[h]=new
        if not old.get('slug'): old['slug']=slugify(f"{old.get('name')} {old.get('city') or old.get('primary_market')}")
        updated+=1
    else:
        new={h:row.get(h,'') for h in headers}
        if not new.get('slug'): new['slug']=slugify(f"{new.get('name')} {new.get('city') or new.get('primary_market')}")
        for f in ['claimed','verified','independent']: new[f]=new.get(f) or 'false'
        new['profile_strength']=new.get('profile_strength') or '0'
        master.append(new); index[k]=len(master)-1; added+=1

with MASTER.open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=headers); w.writeheader(); w.writerows(master)
print(f'Import complete: {added} added, {updated} updated. Master now has {len(master)} rows.')
if args.build:
    subprocess.run([sys.executable,str(ROOT/'scripts'/'build_site.py')],check=True)
