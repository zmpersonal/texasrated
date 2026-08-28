from pathlib import Path
import json, math, html, shutil
from urllib.parse import quote

ROOT=Path(__file__).resolve().parents[1]
DEMO_MODE=True  # Set False only after replacing placeholder companies with validated production data.
for generated in ('company','rankings','widget'):
  d=ROOT/generated
  if d.exists(): shutil.rmtree(d)
  d.mkdir(parents=True,exist_ok=True)

locations=['Austin','North Austin','South Austin','San Antonio']
categories=['HVAC','Plumbing','Roofing','Electrical','Tree Service','Landscaping','Hardscaping','House Cleaning','Handyman','Dumpster Rental','Junk Removal','Pest Control','Garage Door','Painting','Pool Service','Moving']
services={
'HVAC':['AC Repair','AC Replacement','Maintenance','Heat Pumps','Ductwork'],
'Plumbing':['Emergency Plumbing','Water Heaters','Drain & Sewer','Leak Repair','Fixtures'],
'Roofing':['Roof Replacement','Roof Repair','Storm & Hail','Metal Roofing','Inspections'],
'Electrical':['Panel Upgrades','Electrical Repair','Generators','EV Chargers','Rewiring'],
'Tree Service':['Tree Trimming','Tree Removal','Stump Grinding','Storm Cleanup','Arborist Services'],
'Landscaping':['Landscape Design','Planting','Beds','Irrigation','Maintenance'],
'Hardscaping':['Patios','Pavers','Retaining Walls','Outdoor Kitchens','Masonry'],
'House Cleaning':['Recurring Cleaning','Deep Cleaning','Move Out','One-Time Cleaning','Eco-Friendly'],
'Handyman':['Repairs','Carpentry','Drywall','Fixture Install','Punch Lists'],
'Dumpster Rental':['10 Yard','20 Yard','30 Yard','40 Yard','Construction Debris'],
'Junk Removal':['Furniture','Appliances','Construction Debris','Estate Cleanout','Same-Day Pickup'],
'Pest Control':['General Pest','Termites','Rodents','Mosquito','Wildlife'],
'Garage Door':['Garage Door Repair','Openers','Spring Repair','New Doors','Emergency Service'],
'Painting':['Interior','Exterior','Cabinets','Commercial','Prep & Repair'],
'Pool Service':['Weekly Service','Repairs','Equipment','Renovation','Cleaning'],
'Moving':['Local Moving','Packing','Apartment Moves','Office Moves','Storage']}

suffix={
'HVAC':'Air & Heat','Plumbing':'Plumbing','Roofing':'Roofing','Electrical':'Electric','Tree Service':'Tree Co.','Landscaping':'Landscapes','Hardscaping':'Outdoor Works','House Cleaning':'Home Cleaning','Handyman':'Handyman Co.','Dumpster Rental':'Dumpster Co.','Junk Removal':'Junk Removal','Pest Control':'Pest Control','Garage Door':'Garage Door Co.','Painting':'Painting Co.','Pool Service':'Pool Care','Moving':'Moving Co.'}
locprefix={
'Austin':['Capital','Lone Star','Hill Country','Barton','Republic','Travis','Bluebonnet','Live Oak','Pecan','Congress','Zilker','Central Texas'],
'North Austin':['North Star','Brushy Creek','Lakeline','Cedar Ridge','Parmer','Tech Ridge','Walnut Creek','Jollyville','North Loop','Anderson','Domain','Cypress'],
'South Austin':['Southside','Bouldin','Sunset Valley','Onion Creek','Slaughter','South Congress','Barton Hills','Manchaca','Circle C','Oak Hill','Southpark','William Cannon'],
'San Antonio':['Alamo','Mission','River City','Stone Oak','Hill Country','Lone Star','Pearl','Bexar','Fiesta','Cibolo','Olmos','San Pedro']}

claimed_seeds={1,2,3,4,8,12}
companies=[]
for loc in locations:
  for cat in categories:
    group=[]
    for i in range(12):
      seed=i+1
      prefix=locprefix[loc][i]
      # Keep the familiar demo company at #4-ish so the owner dashboard shows competitive pressure.
      if loc=='Austin' and cat=='HVAC' and seed==4:
        name='ABC Heating & Air'
      else:
        name=f'{prefix} {suffix[cat]}'
      slug='-'.join(''.join(ch.lower() if ch.isalnum() else '-' for ch in f'{name}-{loc}-{cat}').split())
      while '--' in slug: slug=slug.replace('--','-')
      slug=slug.strip('-')
      claimed=seed in claimed_seeds
      verified=claimed
      profile_strength=(95-seed if claimed else 45+seed)
      reputation=max(72,98-(seed-1)*1.55)
      momentum=max(62,95-(seed-1)*1.35)
      verification=profile_strength
      response=max(55,91-seed) if claimed else 52
      # A deliberately weaker claimed company demonstrates the nofollow case outside the Top 10.
      if seed==12 and claimed:
        reputation-=8; momentum-=5; response=66
      score=round(0.55*reputation+0.20*momentum+0.15*verification+0.10*response,1)
      rating=round(max(4.1,4.95-seed*0.035),1)
      reviews=int(max(85,1950-seed*118+(len(cat)*7)))
      independent=(seed not in {9,12})
      group.append({
        'name':name,'slug':slug,'seed':seed,'score':score,'rating':rating,'reviews':reviews,
        'claimed':claimed,'verified':verified,'profileStrength':profile_strength,'location':loc,'category':cat,
        'independent':independent,'services':services[cat],
        'serviceAreas':[loc]+([x for x in locations if x!=loc][:1]),
        'website':'https://example.com/' if claimed else '',
        'description':f'{name} is listed in the {loc} {cat} Rankings. This profile summarizes publicly available reputation signals, service information and Texas Rated ranking data.',
        'scoreBreakdown':{'Reputation':round(reputation),'Momentum':round(momentum),'Verified Profile Data':round(verification),'Response Performance':round(response)}
      })
    group.sort(key=lambda c:(-c['score'],-c['reviews'],c['name']))
    for rank,c in enumerate(group,1):
      c['rank']=rank
      c['momentumRank']=sorted(group,key=lambda x:(-x['scoreBreakdown']['Momentum'],-x['score'])) .index(c)+1
      c.pop('seed',None)
      companies.append(c)

(ROOT/'data'/'companies.json').write_text(json.dumps(companies,indent=2),encoding='utf-8')


def esc(s): return html.escape(str(s), quote=True)
def slugify(s):
  out=''.join(ch.lower() if ch.isalnum() else '-' for ch in s)
  while '--' in out: out=out.replace('--','-')
  return out.strip('-')
def relprefix(depth): return '../'*depth

def logo(depth=0):
  p=relprefix(depth)
  return f'<a class="brand" href="{p}index.html"><img src="{p}assets/favicon.svg" alt=""><span>TEXAS<small>RATED</small></span></a>'

def header(depth=0):
  p=relprefix(depth)
  return f'''<header class="site-header"><div class="container header-inner">{logo(depth)}<nav class="main-nav"><a href="{p}rankings.html">Rankings</a><a href="{p}index.html#categories">Categories</a><a href="{p}index.html#markets">Markets</a><a href="{p}independent.html">Independent Companies</a><a href="{p}fastest-rising.html">Fastest Rising</a><a href="{p}methodology.html">Methodology</a></nav><div class="header-actions"><a class="btn" href="{p}claim.html">Claim Your Profile</a><a class="btn navy" href="{p}login.html">Owner Login</a></div></div></header>'''

def footer(depth=0):
  p=relprefix(depth)
  return f'''<footer class="footer"><div class="container"><div class="footer-grid"><div>{logo(depth)}<p style="color:#9db0c6;font-size:13px;line-height:1.6">Independent ratings, Texas Rated Scores and company profiles for Texas service businesses.</p></div><div><h4>Rankings</h4><a href="{p}rankings.html">Browse Rankings</a><a href="{p}fastest-rising.html">Fastest Rising</a><a href="{p}independent.html">Independent Companies</a></div><div><h4>Businesses</h4><a href="{p}claim.html">Claim Profile</a><a href="{p}login.html">Owner Login</a><a href="{p}dashboard.html">Owner Dashboard</a></div><div><h4>Categories</h4><a href="{p}rankings/austin/hvac.html">HVAC</a><a href="{p}rankings/austin/plumbing.html">Plumbing</a><a href="{p}rankings/austin/tree-service.html">Tree Service</a><a href="{p}rankings/austin/dumpster-rental.html">Dumpster Rental</a></div><div><h4>About</h4><a href="{p}methodology.html">Methodology</a><a href="#">Contact</a><a href="#">Terms</a></div></div><div class="footer-note">© 2026 Texas Rated. Texas Rated rankings are informational and do not guarantee service quality or outcomes.</div></div></footer>'''

def page(title,desc,body,depth=0,extra_head='',extra_script=''):
  p=relprefix(depth)
  robots_meta='<meta name="robots" content="noindex,nofollow">' if DEMO_MODE else ''
  return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><meta name="description" content="{esc(desc)}">{robots_meta}<link rel="icon" href="{p}assets/favicon.svg"><link rel="stylesheet" href="{p}assets/styles.css">{extra_head}</head><body>{header(depth)}{body}{footer(depth)}<script src="{p}assets/app.js"></script>{extra_script}</body></html>'''

# homepage helpers
featured=[c for c in companies if c['location']=='Austin' and c['category']=='HVAC'][:5]
hero_rows=''.join(f'''<div class="hero-rank-row"><div>#{c['rank']}</div><div><strong>{esc(c['name'])}</strong><small>{'Owner verified' if c['claimed'] else 'Profile unclaimed'}</small></div><div class="score">{c['score']:.1f}<small>TR</small></div></div>''' for c in featured)
popular=[('Austin','HVAC'),('Austin','Plumbing'),('North Austin','Tree Service'),('South Austin','Landscaping'),('Austin','House Cleaning'),('San Antonio','Roofing'),('Austin','Dumpster Rental'),('Austin','Handyman')]
icons={'HVAC':'❄','Plumbing':'💧','Tree Service':'🌳','Landscaping':'🌿','House Cleaning':'⌂','Roofing':'⌃','Dumpster Rental':'▣','Handyman':'🔧'}
popular_html=''.join(f'''<a class="rank-card" href="rankings/{slugify(loc)}/{slugify(cat)}.html"><span class="rank-card-icon">{icons.get(cat,'★')}</span><div><strong>{esc(loc)} {esc(cat)}</strong><span>View Rankings</span></div></a>''' for loc,cat in popular)
flagship=next(c for c in companies if c['name']=='ABC Heating & Air')
featured_companies=[flagship, next(c for c in companies if c['location']=='Austin' and c['category']=='Tree Service' and c['rank']==1), next(c for c in companies if c['location']=='South Austin' and c['category']=='Landscaping' and c['rank']==1), next(c for c in companies if c['location']=='San Antonio' and c['category']=='Plumbing' and c['rank']==1), next(c for c in companies if c['location']=='Austin' and c['category']=='Dumpster Rental' and c['rank']==1), next(c for c in companies if c['location']=='North Austin' and c['category']=='House Cleaning' and c['rank']==1)]
company_cards=''.join(f'''<a class="index-card" href="company/{c['slug']}.html"><div class="kicker">#{c['rank']} {esc(c['location'])} {esc(c['category'])}</div><div class="metric">{c['score']:.1f}</div><strong>{esc(c['name'])}</strong><p>{c['rating']:.1f} ★ · {c['reviews']:,} reviews · {'Verified profile' if c['claimed'] else 'Unclaimed profile'}</p></a>''' for c in featured_companies)

home_body=f'''
<section class="hero"><div class="container hero-inner"><div><div class="eyebrow" style="color:#9fc7ff">Independent ratings for Texas service companies</div><h1>Find Texas's highest-rated local service companies.</h1><p>Compare Texas Rated Scores, local rankings, verified company profiles and service areas—all in one place. Every company in Texas Rated has a public profile; verified owners can keep their information current and receive customer opportunities.</p><form class="hero-form" id="rankingFilter"><div class="field"><label>Location</label><select name="location">{''.join(f'<option>{x}</option>' for x in locations)}</select></div><div class="field"><label>Service</label><select name="category">{''.join(f'<option>{x}</option>' for x in categories)}</select></div><button class="btn red">View Rankings →</button></form><div class="company-search-wrap"><input id="companySearch" data-profile-prefix="company/" class="company-search" placeholder="Search a company by name…"><div id="companySearchResults" class="search-results" hidden></div></div></div><div class="hero-panel"><div class="hero-panel-head"><h3>Austin HVAC Rankings</h3><span class="live-pill">Updated monthly</span></div>{hero_rows}<div style="margin-top:14px"><a class="btn primary" href="rankings/austin/hvac.html">View Austin HVAC Rankings →</a></div></div></div></section>
<section class="section" id="categories"><div class="container"><div class="section-head"><div><h2>Popular Rankings</h2><p>Browse high-demand service categories by Texas market.</p></div><a class="text-link" href="rankings.html">Browse all →</a></div><div class="popular-grid">{popular_html}</div></div></section>
<section class="section soft"><div class="container"><div class="section-head"><div><h2>Companies on Texas Rated</h2><p>Every listed company has its own profile page—even before the owner claims it.</p></div></div><div class="index-grid">{company_cards}</div></div></section>
<section class="section"><div class="container"><div class="section-head"><div><h2>How the Texas Rated Score works</h2><p>A 100-point score that combines public reputation, current momentum and verified company information.</p></div><a class="text-link" href="methodology.html">See methodology →</a></div><div class="index-grid"><div class="index-card"><div class="kicker">55%</div><div class="metric">Reputation</div><p>Ratings, review volume, review quality and established public reputation signals.</p></div><div class="index-card"><div class="kicker">20%</div><div class="metric">Momentum</div><p>Recent review growth and changes relative to comparable companies in the same market.</p></div><div class="index-card"><div class="kicker">15% + 10%</div><div class="metric">Verified Data</div><p>Profile verification/completeness plus first-party response performance as Texas Rated usage grows.</p></div></div></div></section>
<section class="section soft" id="markets"><div class="container"><div class="section-head"><div><h2>Texas Markets</h2><p>Start with Austin-area local rankings and San Antonio.</p></div></div><div class="popular-grid">{''.join(f'<a class="rank-card" href="rankings/{slugify(loc)}/hvac.html"><span class="rank-card-icon">★</span><div><strong>{esc(loc)}</strong><span>Browse local rankings</span></div></a>' for loc in locations)}</div></div></section>
<section class="section"><div class="container"><div class="owner-cta"><div><h3>Own a Texas service company?</h3><p>Your company may already be rated. Claim it to verify your company, activate your website link, improve the verified-data portion of your Texas Rated Score, receive customer leads and messages, track competitors, and install your live Texas Rated emblem.</p></div><a class="btn primary" href="claim.html">Claim Your Profile →</a></div></div></section>'''
(ROOT/'index.html').write_text(page('Texas Rated | Texas Service Companies, Measured','Browse Texas Rated rankings, Texas Rated Scores and public company profiles by market and service category.',home_body),encoding='utf-8')

# Rankings directory index
rank_cards=''.join(f'''<a class="rank-card" href="rankings/{slugify(loc)}/{slugify(cat)}.html"><span class="rank-card-icon">★</span><div><strong>{esc(loc)} {esc(cat)}</strong><span>View Texas Rated rankings</span></div></a>''' for loc in locations for cat in categories[:8])
body=f'''<section class="page-hero"><div class="container"><div class="eyebrow">Browse Rankings</div><h1>Top Rated Texas Service Companies</h1><p>Choose a market and service category to compare companies by Texas Rated Score, public reputation and verified business information.</p></div></section><section class="section"><div class="container"><div class="popular-grid">{rank_cards}</div></div></section>'''
(ROOT/'rankings.html').write_text(page('Browse Texas Rated Rankings','Browse Texas Rated rankings by location and service category.',body),encoding='utf-8')

# Ranking pages
for loc in locations:
  locdir=ROOT/'rankings'/slugify(loc);locdir.mkdir(parents=True,exist_ok=True)
  for cat in categories:
    rows=[c for c in companies if c['location']==loc and c['category']==cat]
    ranking_rows=''.join(f'''<div class="ranking-row"><div class="rank-medal {'top-'+str(c['rank']) if c['rank']<=3 else ''}">{c['rank']}</div><div class="company-cell"><span class="company-logo">{''.join(x[0] for x in c['name'].split()[:2]).upper()}</span><div><a class="company-name" href="../../company/{c['slug']}.html">{esc(c['name'])}</a><div class="tiny-meta">{'<span class="verified-pill">✓ Owner Verified</span>' if c['claimed'] else '<span class="unclaimed-pill">Profile unclaimed</span>'}</div></div></div><div class="score-cell"><strong>{c['score']:.1f}</strong><span>TR Score</span></div><div class="review-cell"><span class="stars">★★★★★</span><span>{c['rating']:.1f} · {c['reviews']:,} reviews</span></div><div class="row-action"><a class="text-link" href="../../company/{c['slug']}.html">View Profile →</a></div></div>''' for c in rows)
    body=f'''<section class="page-hero"><div class="container"><div class="eyebrow">Texas Rated</div><h1>Top Rated {esc(cat)} Companies in {esc(loc)}</h1><p>Compare {esc(cat.lower())} companies serving {esc(loc)} using Texas Rated Scores, reputation signals and verified business information. Every company below has a public profile page.</p><div class="badges"><span class="pill">12 companies shown</span><span class="pill green">Monthly updates</span><span class="pill gold">Top 10 recognition</span><button class="btn" type="button" data-share data-share-title="Top Rated {esc(cat)} Companies in {esc(loc)} | Texas Rated">Share Rankings</button></div></div></section><section class="section"><div class="container"><div class="tabs"><a class="tab active" href="#">Overall Rankings</a><a class="tab" href="../../fastest-rising.html">Fastest Rising</a><a class="tab" href="../../independent.html">Independent Companies</a></div><div class="rankings-shell"><div class="ranking-header"><span>Rank</span><span>Company</span><span>TR Score</span><span>Reputation</span><span>Profile</span></div>{ranking_rows}</div><div class="trust-strip"><div class="trust-item"><span class="trust-icon">✓</span><div><strong>Every company has a page</strong><span>Profiles exist before owners claim them, making rankings easy to verify and discover.</span></div></div><div class="trust-item"><span class="trust-icon">↗</span><div><strong>Links require a claim</strong><span>Unclaimed companies do not receive an outbound website link.</span></div></div><div class="trust-item"><span class="trust-icon">★</span><div><strong>Top 10 recognition</strong><span>Eligible verified companies can display a live Texas Rated emblem on their site.</span></div></div><div class="trust-item"><span class="trust-icon">◉</span><div><strong>Transparent score</strong><span>Texas Rated Score components are disclosed in our methodology.</span></div></div></div></div></section>'''
    rank_title=f'Top Rated {cat} Companies in {loc} | Texas Rated'
    rank_desc=f'Compare top rated {cat.lower()} companies in {loc} by Texas Rated Score, reputation and verified profile data.'
    rank_url=f'https://texasrated.com/rankings/{slugify(loc)}/{slugify(cat)}.html'
    rank_head=f'<link rel="canonical" href="{rank_url}"><meta property="og:title" content="{esc(rank_title)}"><meta property="og:description" content="{esc(rank_desc)}"><meta property="og:url" content="{rank_url}"><meta property="og:type" content="website">'
    (locdir/f'{slugify(cat)}.html').write_text(page(rank_title,rank_desc,body,depth=2,extra_head=rank_head),encoding='utf-8')

# Company pages
for c in companies:
  initials=''.join(x[0] for x in c['name'].split()[:2]).upper()
  badges=f'''<span class="pill gold">#{c['rank']} {esc(c['location'])} {esc(c['category'])}</span>'''
  if c['claimed']: badges+='<span class="pill green">✓ Owner Verified</span>'
  else: badges+='<span class="pill gray">Profile Unclaimed</span>'
  if c['independent']: badges+='<span class="pill">Independently Owned</span>'
  if c['rank']<=10: badges+='<span class="pill gold">Texas Rated Top 10</span>'
  breakdown=''.join(f'''<div class="score-line"><span>{esc(k)}</span><div class="bar"><span style="width:{v}%"></span></div><strong>{v}</strong></div>''' for k,v in c['scoreBreakdown'].items())
  service_tags=''.join(f'<span class="service-tag">{esc(s)}</span>' for s in c['services'])
  area_tags=''.join(f'<span class="service-tag">{esc(s)}</span>' for s in c['serviceAreas'])
  if c['claimed']:
    rel='' if c['rank']<=10 else ' rel="ugc nofollow"'
    website=f'<a class="btn primary" href="{c["website"]}" target="_blank"{rel}>Visit Website ↗</a>'
    request='<a class="btn red" href="../login.html">Request Service</a><a class="btn" href="../login.html">Send Message</a>'
  else:
    website='<span class="btn" style="opacity:.55;cursor:not-allowed">Website link activates when claimed</span>'
    request=f'<a class="btn red" href="../claim.html?company={quote(c["slug"])}">Claim This Profile</a>'
  claimbox='' if c['claimed'] else f'''<div class="claim-banner"><h3>Own {esc(c['name'])}?</h3><p>Claim this profile to verify company information, activate your website link, receive customer leads and messages, complete verified data used by the Texas Rated Score, and access your live emblem.</p><a class="btn primary" href="../claim.html?company={quote(c['slug'])}">Claim Your Profile →</a></div>'''
  link_note='Top 10 verified profile: direct editorial website link.' if c['claimed'] and c['rank']<=10 else ('Verified profile: owner-supplied outbound link.' if c['claimed'] else 'No outbound company website link until this profile is claimed and verified.')
  body=f'''<section class="page-hero"><div class="container"><div class="eyebrow">Company Profile · Texas Rated</div><div class="company-top"><div class="big-logo">{initials}</div><div><h1>{esc(c['name'])}</h1><p style="margin:0">{esc(c['location'])} · {esc(c['category'])}</p><div class="badges">{badges}</div></div></div></div></section><section class="section"><div class="container company-page-grid"><main><div class="card"><div class="score-band"><div class="score-box"><strong>{c['score']:.1f}</strong><span>Texas Rated Score</span></div><div class="score-box"><strong>#{c['rank']}</strong><span>{esc(c['location'])} rank</span></div><div class="score-box"><strong>{c['rating']:.1f} ★</strong><span>{c['reviews']:,} public reviews</span></div><div class="score-box"><strong>{c['profileStrength']}%</strong><span>Profile data strength</span></div></div><p class="small muted">{esc(c['description'])}</p><h3>Texas Rated Score components</h3><div class="score-breakdown">{breakdown}</div><p class="tiny muted">Verified profile information contributes to the verified-data component of the Texas Rated Score. Reputation remains the largest component.</p><h3>Services</h3><div class="service-tags">{service_tags}</div><h3>Areas served</h3><div class="service-tags">{area_tags}</div><div class="action-row">{request}{website}<button class="btn" type="button" data-share data-share-title="{esc(c['name'])} on Texas Rated">Share Profile</button></div><p class="tiny muted">{esc(link_note)}</p></div></main><aside><div class="card"><h3>Current Ranking Position</h3><div class="rank-list-mini"><div class="mini-row"><span>{esc(c['location'])} {esc(c['category'])}</span><strong>#{c['rank']}</strong></div><div class="mini-row"><span>Texas Rated Score</span><strong>{c['score']:.1f}</strong></div><div class="mini-row"><span>Momentum</span><strong>#{c['momentumRank']}</strong></div><div class="mini-row"><span>Profile</span><strong>{'Verified' if c['claimed'] else 'Unclaimed'}</strong></div></div><a class="text-link" href="../rankings/{slugify(c['location'])}/{slugify(c['category'])}.html">View full rankings →</a></div>{claimbox}</aside></div></section>'''
  canonical=f"https://texasrated.com/company/{c['slug']}.html"
  schema={
    '@context':'https://schema.org','@type':'LocalBusiness','name':c['name'],'url':canonical,
    'description':c['description'],'areaServed':c['serviceAreas'],
    'aggregateRating':{'@type':'AggregateRating','ratingValue':c['rating'],'reviewCount':c['reviews']}
  }
  extra_head=f'<link rel="canonical" href="{canonical}"><meta property="og:title" content="{esc(c['name'])} | Texas Rated"><meta property="og:description" content="Texas Rated Score {c['score']:.1f} · #{c['rank']} {esc(c['location'])} {esc(c['category'])}"><meta property="og:url" content="{canonical}"><meta property="og:type" content="website"><script type="application/ld+json">{json.dumps(schema,separators=(",",":"))}</script>'
  (ROOT/'company'/f"{c['slug']}.html").write_text(page(f"{c['name']} | {c['location']} {c['category']} Texas Rated Score",f"View the Texas Rated profile, Texas Rated Score and {c['location']} {c['category']} ranking for {c['name']}.",body,depth=1,extra_head=extra_head),encoding='utf-8')

# Claim page
flag=flagship
benefits=['Activate your public website link','Edit services, areas, logo and business details','Complete verified data used in your Texas Rated Score','Turn automatic customer lead delivery on or off','Receive customer and Pro Network messages','Track rank, momentum and nearby competitors','Install a live emblem that updates with your rank','View profile, website and emblem traffic']
body=f'''<section class="page-hero"><div class="container"><div class="eyebrow">For Texas service businesses</div><h1>Claim your company profile.</h1><p>Your Texas Rated profile already exists. Verification unlocks control, visibility, competitive intelligence, lead delivery, messages and your live Texas Rated emblem.</p></div></section><section class="section"><div class="container claim-layout"><div><div class="card form-card"><h2>Verify your business</h2><p class="muted small">Demo claim flow shown for <strong data-claim-company>{esc(flag['name'])}</strong>. Production verification can use a work email, business phone or domain check.</p><form id="claimForm"><label>Business name</label><input class="input" id="claimBusiness" value="{esc(flag['name'])}"><label>Your name</label><input class="input" placeholder="Owner or authorized manager"><label>Work email</label><input class="input" type="email" placeholder="you@company.com"><label>Business phone</label><input class="input" placeholder="(512) 555-0123"><div style="margin-top:16px"><button class="btn primary" type="submit">Verify & Claim Profile →</button></div></form><div id="claimDone" hidden><div class="notice"><strong>Profile claimed in this demo.</strong> Your verified owner dashboard is now unlocked.</div><div style="margin-top:14px"><a class="btn primary" href="dashboard.html">Open Owner Dashboard →</a></div></div></div><h3>Claimed profiles unlock</h3><div class="benefit-grid">{''.join(f'<div class="benefit">✓ {esc(b)}</div>' for b in benefits)}</div></div><aside><div class="card"><div class="eyebrow">Your profile is already waiting</div><h2 data-claim-company>{esc(flag['name'])}</h2><div class="score-band" style="grid-template-columns:1fr 1fr"><div class="score-box"><strong data-claim-rank>#{flag['rank']}</strong><span>Austin HVAC</span></div><div class="score-box"><strong data-claim-score>{flag['score']:.1f}</strong><span>Texas Rated Score</span></div></div><p class="small muted">Claiming activates owner controls and verified benefits. Rankings cannot be purchased.</p></div><div class="card worth-card" style="margin-top:14px"><div class="eyebrow" style="color:#9fc7ff">Separate private tool</div><h2>What is your business worth?</h2><p>Texas Rated stays focused on rankings, reputation and customer opportunities. For a private business-value estimate, use TexasBusinessWorth.com.</p><a class="btn" href="https://texasbusinessworth.com/" target="_blank" rel="noopener">Check My Business Value ↗</a></div></aside></div></section>'''
(ROOT/'claim.html').write_text(page('Claim Your Profile | Texas Rated','Claim and verify your Texas Rated company profile.',body),encoding='utf-8')

# Dashboard
widget_src=f'widget/{flag["slug"]}.html'
hvac_group=sorted([c for c in companies if c['location']=='Austin' and c['category']=='HVAC'], key=lambda c:c['rank'])
above=hvac_group[max(0,flag['rank']-2)]
below=hvac_group[min(len(hvac_group)-1,flag['rank'])]
embed_code=f'<iframe src="https://texasrated.com/widget/{flag["slug"]}.html" width="185" height="220" style="border:0" title="Texas Rated emblem"></iframe>'
body=f'''<div class="dashboard-body"><div class="dashboard-header"><div class="container dash-title"><div><div class="eyebrow" style="color:#8fc0ff;margin:0 0 5px">Verified owner dashboard</div><h1>{esc(flag['name'])}</h1><span>Austin HVAC · Texas Rated Top 10 · <b style="color:#72e3a1">● Accepting Leads</b></span></div><div class="profile-meter"><div class="meter"></div><div><strong>78%</strong><span style="display:block">Profile Strength</span></div></div></div></div><div class="container dashboard-layout"><aside class="sidebar"><a class="active" href="#overview">Overview</a><a href="#profile">Profile</a><a href="#leads">Leads</a><a href="#messages">Messages</a><a href="#rankings">Rankings</a><a href="#emblem">Emblem</a></aside><main><div class="dash-grid" id="overview"><div class="dash-card"><div class="kicker">Your Rank</div><div class="big">#{flag['rank']}</div><div class="trend-up">↑ 1 this month</div><p class="small muted">0.9 points from the company above.</p><a class="text-link" href="rankings/austin/hvac.html">View Rankings →</a><div style="margin-top:10px"><button class="btn" type="button" data-share data-share-title="ABC Heating & Air is #4 Austin HVAC on Texas Rated">Share Rank</button></div></div><div class="dash-card"><div class="kicker">Texas Rated Score</div><div class="big">{flag['score']:.1f}</div><div class="trend-up">↑ 0.8</div><p class="small muted">Verified profile data is now 78% complete.</p><a class="text-link" href="#profile">Improve Profile →</a></div><div class="dash-card"><div class="kicker">Momentum</div><div class="big">#2</div><div class="trend-up">Fastest Rising</div><p class="small muted">+31 reviews · Top 10 average +18.</p><a class="text-link" href="fastest-rising.html">View Momentum →</a></div><div class="dash-card" id="leads"><div class="kicker">Leads</div><div class="big">3</div><div class="lead-list"><div class="lead-item"><span><i class="dot"></i>HVAC Repair</span><strong>2</strong></div><div class="lead-item"><span><i class="dot"></i>AC Replacement</span><strong>1</strong></div></div><p class="small"><b>Accepting Leads:</b> <span id="leadStatus">ON</span> <input id="leadToggle" class="toggle" type="checkbox" checked></p><p class="tiny muted">Automatic email delivery: <b>ON</b> · owner@company.com</p></div><div class="dash-card"><div class="kicker">Competition</div><div class="competitor-table" style="margin-top:12px"><div><b>#{above['rank']}</b><span>{esc(above['name'])}</span><b>{above['score']:.1f}</b></div><div class="you"><b>#{flag['rank']}</b><span>YOU</span><b>{flag['score']:.1f}</b></div><div><b>#{below['rank']}</b><span>{esc(below['name'])}</span><b>{below['score']:.1f}</b></div></div><p class="small muted"><b>{esc(below['name'])}</b> is gaining quickly this month.</p></div><div class="dash-card"><div class="kicker">Profile Performance</div><div class="big">382</div><p class="small">Profile views</p><p class="small muted">71 website clicks · 9 service requests</p><div class="trend-up">↑ 18% vs prior 30 days</div></div><div class="dash-card"><div class="kicker">Response Performance</div><div class="big">92%</div><p class="small">Response rate</p><p class="small muted"><b>14 min</b> median response · Top 10 median 22 min</p></div><div class="dash-card"><div class="kicker">Messages</div><div class="big">2</div><p class="small">Unread conversations</p><a class="text-link" href="#messages">Open Messages →</a></div></div><div class="dash-lower" id="profile"><div class="card"><h3>Public Profile Preview</h3><div class="profile-preview"><div class="big-logo">AB</div><div><h2 style="margin:0">{esc(flag['name'])}</h2><div class="badges"><span class="pill gold">#{flag['rank']} Austin HVAC</span><span class="pill green">✓ Owner Verified</span><span class="pill">Independently Owned</span></div><p class="small muted">Services: AC Repair · AC Replacement · Maintenance · Heat Pumps · Ductwork</p><div class="action-row"><a class="btn red" href="company/{flag['slug']}.html">View Public Profile</a><button class="btn">Edit Profile</button></div></div></div></div><div class="card worth-card"><div class="eyebrow" style="color:#9fc7ff">Owner resource</div><h3 style="font-size:22px">Curious what the business may be worth?</h3><p>Run a private valuation separately at TexasBusinessWorth.com.</p><a class="btn" href="https://texasbusinessworth.com/" target="_blank" rel="noopener">Estimate Business Value ↗</a></div></div><div class="dash-lower" id="emblem"><div class="card"><h3>Your Live Texas Rated Emblem</h3><div class="emblem-box"><iframe class="emblem-frame" src="{widget_src}" title="Live Texas Rated emblem"></iframe><div><p class="small"><strong>Installed:</strong> demo-company.com</p><p class="small muted">The emblem is served by Texas Rated. When the official ranking changes, the emblem changes without the owner replacing embed code.</p><div class="code-box" id="embedCode">{esc(embed_code)}</div><div style="margin-top:10px"><button class="btn" data-copy="#embedCode">Copy Embed Code</button></div></div></div></div><div class="card"><h3>Emblem Performance</h3><div class="score-band" style="grid-template-columns:repeat(3,1fr)"><div class="score-box"><strong>6,821</strong><span>Impressions</span></div><div class="score-box"><strong>43</strong><span>Clicks</span></div><div class="score-box"><strong>18</strong><span>Website referrals</span></div></div><p class="small muted">Clicking the emblem verifies the company's current Texas Rated recognition and leads visitors to its profile.</p></div></div><div id="messages" class="message-layout"><div class="message-list"><div class="message-row active" data-message data-name="Sarah M." data-type="AC Replacement" data-zip="78759" data-body="Looking to replace a 12-year-old downstairs system. Can someone contact me this week?"><strong>Sarah M.</strong><span>AC Replacement · 78759</span><small>2 minutes ago · unread</small></div><div class="message-row" data-message data-name="Michael R." data-type="AC Repair" data-zip="78731" data-body="Upstairs system is running but not cooling. Looking for service today if possible."><strong>Michael R.</strong><span>AC Repair · 78731</span><small>31 minutes ago · unread</small></div><div class="message-row" data-message data-name="Greenway Plumbing" data-type="Pro Network Referral" data-zip="78728" data-body="Customer needs an HVAC company for a no-cool call in North Austin. Can your team take it?"><strong>Greenway Plumbing</strong><span>Pro Network referral · 78728</span><small>Yesterday</small></div></div><div class="message-detail" id="messageDetail"><div class="message-detail-head"><strong>Sarah M.</strong><span>AC Replacement • 78759</span></div><div class="message-bubble">Looking to replace a 12-year-old downstairs system. Can someone contact me this week?</div><div class="reply-box"><textarea placeholder="Reply to this customer…"></textarea><button class="btn primary">Send Reply</button></div></div></div></main></div></div>'''
# dashboard has its own body/header; use no standard header/footer
(ROOT/'dashboard.html').write_text(f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Owner Dashboard | Texas Rated</title>{'<meta name="robots" content="noindex,nofollow">' if DEMO_MODE else ''}<link rel="icon" href="assets/favicon.svg"><link rel="stylesheet" href="assets/styles.css"></head><body>{header(0)}{body}<script src="assets/app.js"></script></body></html>''',encoding='utf-8')

# Login
body='''<section class="page-hero"><div class="container"><div class="eyebrow">Verified business owners</div><h1>Owner Login</h1><p>Access your Texas Rated ranking dashboard, company profile, customer leads, messages and live emblem.</p></div></section><section class="section"><div class="container" style="max-width:560px"><div class="card form-card"><label>Email</label><input class="input" value="owner@example.com"><label>Password</label><input class="input" type="password" value="password"><div style="margin-top:16px"><a class="btn primary" href="dashboard.html">Login to Dashboard →</a></div><p class="small muted">Demo login only. Production authentication is not connected in this static build.</p></div></div></section>'''
(ROOT/'login.html').write_text(page('Owner Login | Texas Rated','Owner login for verified Texas Rated business profiles.',body),encoding='utf-8')

# Methodology
body='''<section class="page-hero"><div class="container"><div class="eyebrow">Transparent methodology</div><h1>How the Texas Rated Score works</h1><p>The Texas Rated Score is designed to combine public reputation, recent momentum and verified company information into a comparable 100-point score within each local service market.</p></div></section><section class="section"><div class="container"><div class="index-grid"><div class="index-card"><div class="kicker">55% weight</div><div class="metric">Reputation</div><p>Public rating strength, review volume, review quality, longevity and other defensible reputation signals.</p></div><div class="index-card"><div class="kicker">20% weight</div><div class="metric">Momentum</div><p>Recent review growth and changes relative to comparable companies in the same location and category.</p></div><div class="index-card"><div class="kicker">15% weight</div><div class="metric">Verified Profile Data</div><p>Owner verification, service coverage, business details and other information that can be verified rather than inferred.</p></div><div class="index-card"><div class="kicker">10% weight</div><div class="metric">Response Performance</div><p>As Texas Rated generates first-party inquiries, response rate and response speed can provide a measured service signal.</p></div><div class="index-card"><div class="kicker">Non-negotiable</div><div class="metric">Rankings aren't sold</div><p>Advertising, lead participation, badge installation and outbound links do not purchase a higher Texas Rated rank.</p></div><div class="index-card"><div class="kicker">Owner participation</div><div class="metric">Better data</div><p>Completing a verified profile can improve the verified-data component because Texas Rated has more reliable business information to score.</p></div></div><div class="notice" style="margin-top:24px">This build contains illustrative placeholder company data for UI/development purposes. Replace the seed dataset with validated company data and finalized scoring logic before public production launch.</div></div></section>'''
(ROOT/'methodology.html').write_text(page('Texas Rated Score Methodology | Texas Rated','Learn how the Texas Rated Score is structured.',body),encoding='utf-8')

# Independent and fastest rising
for filename,title,desc,sortkey,filterfn in [
 ('independent.html','Independent Texas Service Companies','Browse independently owned service companies across Texas Rated markets.','score',lambda c:c['independent']),
 ('fastest-rising.html','Fastest-Rising Texas Service Companies','See service companies with the strongest recent momentum across Texas Rated markets.','momentumRank',lambda c:True)]:
  arr=[c for c in companies if filterfn(c)]
  if sortkey=='score': arr=sorted(arr,key=lambda c:-c['score'])[:24]
  else: arr=sorted(arr,key=lambda c:c['momentumRank'])[:24]
  cards=''.join(f'''<a class="index-card" href="company/{c['slug']}.html"><div class="kicker">{esc(c['location'])} · {esc(c['category'])}</div><div class="metric">{'#'+str(c['momentumRank']) if sortkey=='momentumRank' else f'{c["score"]:.1f}'}</div><strong>{esc(c['name'])}</strong><p>#{c['rank']} local rank · TR {c['score']:.1f} · {'Verified' if c['claimed'] else 'Unclaimed'}</p></a>''' for c in arr)
  b=f'''<section class="page-hero"><div class="container"><div class="eyebrow">Texas Rated</div><h1>{esc(title)}</h1><p>{esc(desc)}</p></div></section><section class="section"><div class="container"><div class="index-grid">{cards}</div></div></section>'''
  (ROOT/filename).write_text(page(f'{title} | Texas Rated',desc,b),encoding='utf-8')

# Widgets
for c in companies:
  status='TOP 10' if c['rank']<=10 else 'VERIFIED COMPANY'
  if c['claimed']:
    widget=f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="../assets/styles.css"></head><body class="widget-body"><a class="widget-link" target="_blank" href="../company/{c['slug']}.html"><div class="widget"><div class="w-brand">TEXAS RATED</div><div class="w-top">{status}</div><div class="w-cat">{esc(c['location'])} {esc(c['category'])}</div><div class="w-rank">#{c['rank']}</div><div class="w-year">CURRENT RANK · 2026</div></div></a></body></html>'''
  else:
    widget=f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="../assets/styles.css"></head><body class="widget-body"><a class="widget-link" target="_blank" href="../company/{c['slug']}.html"><div class="widget"><div class="w-brand">TEXAS RATED</div><div class="w-top">PROFILE</div><div class="w-cat">UNCLAIMED</div><div class="w-rank">#{c['rank']}</div><div class="w-year">CLAIM TO UNLOCK EMBLEM</div></div></a></body></html>'''
  (ROOT/'widget'/f"{c['slug']}.html").write_text(widget,encoding='utf-8')

# robots / sitemap
urls=['index.html','rankings.html','claim.html','login.html','methodology.html','independent.html','fastest-rising.html']
urls += [f'company/{c["slug"]}.html' for c in companies]
urls += [f'rankings/{slugify(loc)}/{slugify(cat)}.html' for loc in locations for cat in categories]
sitemap='''<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'''+''.join(f'<url><loc>https://texasrated.com/{u}</loc></url>\n' for u in urls)+"</urlset>\n"
(ROOT/'sitemap.xml').write_text(sitemap,encoding='utf-8')
(ROOT/'robots.txt').write_text(('User-agent: *\nDisallow: /\n' if DEMO_MODE else 'User-agent: *\nAllow: /\nSitemap: https://texasrated.com/sitemap.xml\n'),encoding='utf-8')

readme=f'''# Texas Rated — GitHub / Cloudflare-ready build\n\nFresh static rebuild for TexasRated.com, designed for GitHub Pages or Cloudflare Pages.\n\n## Included\n- Consumer-first homepage and category/location rankings\n- Texas Rated Score terminology throughout\n- {len(companies)} static, independently indexable company profile pages\n- Unclaimed profiles have no outbound company website link\n- Claimed Top-10 demo profiles use a normal outbound link; claimed profiles outside Top 10 use `rel="ugc nofollow"`\n- Claim/profile-verification flow\n- Verified-owner dashboard with leads, messages, competition, profile analytics and rank/score cards\n- Live-emblem architecture using a single iframe URL per company; update generated widget data and the emblem changes without changing embed code\n- TexasBusinessWorth.com handoff on claim page and owner dashboard\n- Static market/category index pages for Austin, North Austin, South Austin and San Antonio\n- Sitemap and robots.txt\n\n## Important before production\n`DEMO_MODE=True` is intentionally enabled in `scripts/build_site.py`. This outputs `noindex,nofollow` and blocks crawling in `robots.txt` so placeholder rankings cannot accidentally be indexed. After replacing the sample dataset with validated companies, set `DEMO_MODE=False` and rebuild.\n\nThe included company records and ranking numbers are **illustrative placeholder data** for design/development. Do not publish them as factual rankings. Replace `data/companies.json` with validated businesses and finalize the production scoring methodology/data ingestion.\n\n## Regenerate static pages\nRun:\n\n```bash\npython3 scripts/build_site.py\n```\n\nThe generator creates all company pages, market/category ranking pages, widget pages and the sitemap.\n\n## Production backend still required for\n- authentication / owner verification\n- database-backed profile edits\n- lead ingestion + email delivery\n- on-site messaging\n- real-time analytics\n- automated scoring/rank updates\n- owner notifications\n\n## Domain\nThe public root is `https://texasrated.com/`. A `CNAME` file is included for GitHub Pages; Cloudflare can provide DNS/proxying or deploy the repository directly with Cloudflare Pages.\n'''
(ROOT/'README.md').write_text(readme,encoding='utf-8')

print(f'Built {len(companies)} company pages and {len(locations)*len(categories)} ranking pages.')
