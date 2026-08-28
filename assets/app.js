const TEXAS_RATED_APP={
  async loadCompanies(){
    if(this.companies)return this.companies;
    const res=await fetch(this.dataPath||'data/companies.json');
    this.companies=await res.json();
    return this.companies;
  },
  money(n){return Number(n).toLocaleString()},
  logoMark(name){const initials=name.split(/\s+/).slice(0,2).map(x=>x[0]).join('').toUpperCase();return `<span class="company-logo">${initials}</span>`},
  setupSearch(){
    const input=document.querySelector('#companySearch'),results=document.querySelector('#companySearchResults');
    if(!input||!results)return;
    const prefix=input.dataset.profilePrefix||'company/';
    const draw=async()=>{const v=input.value.trim().toLowerCase();if(v.length<2){results.hidden=true;return}const all=await this.loadCompanies();const found=all.filter(c=>c.name.toLowerCase().includes(v)).slice(0,7);results.innerHTML=found.map(c=>`<a href="${prefix}${c.slug}.html">${this.logoMark(c.name)}<span><strong>${c.name}</strong><small>#${c.rank} ${c.location} ${c.category} · TR Score ${c.score.toFixed(1)}</small></span></a>`).join('')||'<div style="padding:12px;color:#66758b">No matching company found.</div>';results.hidden=false};
    input.addEventListener('input',draw);input.addEventListener('focus',draw);document.addEventListener('click',e=>{if(!e.target.closest('.company-search-wrap'))results.hidden=true});
  },
  async setupClaim(){const form=document.querySelector('#claimForm'),done=document.querySelector('#claimDone');if(!form)return;const params=new URLSearchParams(location.search),slug=params.get('company');if(slug){const all=await this.loadCompanies(),c=all.find(x=>x.slug===slug);if(c){document.querySelectorAll('[data-claim-company]').forEach(x=>x.textContent=c.name);document.querySelectorAll('[data-claim-rank]').forEach(x=>x.textContent='#'+c.rank);document.querySelectorAll('[data-claim-score]').forEach(x=>x.textContent=c.score.toFixed(1));const business=document.querySelector('#claimBusiness');if(business)business.value=c.name}}form.addEventListener('submit',e=>{e.preventDefault();form.hidden=true;done.hidden=false;done.scrollIntoView({behavior:'smooth'});localStorage.setItem('texas_rated_demo_claimed','1')})},
  setupLeadToggle(){const t=document.querySelector('#leadToggle'),s=document.querySelector('#leadStatus');if(!t||!s)return;t.addEventListener('change',()=>s.textContent=t.checked?'ON':'PAUSED')},
  setupMessages(){document.querySelectorAll('[data-message]').forEach(row=>row.addEventListener('click',()=>{document.querySelectorAll('[data-message]').forEach(x=>x.classList.remove('active'));row.classList.add('active');const d=document.querySelector('#messageDetail');d.innerHTML=`<div class="message-detail-head"><strong>${row.dataset.name}</strong><span>${row.dataset.type} • ${row.dataset.zip}</span></div><div class="message-bubble">${row.dataset.body}</div><div class="reply-box"><textarea placeholder="Reply to this customer…"></textarea><button class="btn primary">Send Reply</button></div>`}))},
  setupCopy(){document.querySelectorAll('[data-copy]').forEach(btn=>btn.addEventListener('click',async()=>{const text=document.querySelector(btn.dataset.copy)?.textContent||'';try{await navigator.clipboard.writeText(text);const old=btn.textContent;btn.textContent='Copied ✓';setTimeout(()=>btn.textContent=old,1600)}catch(e){}}))},
  setupShare(){document.querySelectorAll('[data-share]').forEach(btn=>btn.addEventListener('click',async()=>{const title=btn.dataset.shareTitle||document.title;const url=location.href;try{if(navigator.share){await navigator.share({title,url})}else{await navigator.clipboard.writeText(url);const old=btn.textContent;btn.textContent='Link copied ✓';setTimeout(()=>btn.textContent=old,1600)}}catch(e){}}))},
  setupFilter(){const f=document.querySelector('#rankingFilter');if(!f)return;f.addEventListener('submit',e=>{e.preventDefault();const loc=f.location.value,cat=f.category.value;location.href=`rankings/${slugify(loc)}/${slugify(cat)}.html`})}
};
function slugify(s){return s.toLowerCase().replace(/&/g,'and').replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'')}
document.addEventListener('DOMContentLoaded',()=>{TEXAS_RATED_APP.setupSearch();TEXAS_RATED_APP.setupClaim();TEXAS_RATED_APP.setupLeadToggle();TEXAS_RATED_APP.setupMessages();TEXAS_RATED_APP.setupCopy();TEXAS_RATED_APP.setupShare();TEXAS_RATED_APP.setupFilter()});
