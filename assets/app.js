document.addEventListener('click',function(e){
  const s=e.target.closest('[data-share]');
  if(s){e.preventDefault(); const data={title:s.dataset.title||document.title,text:s.dataset.text||'',url:s.dataset.url||location.href}; if(navigator.share){navigator.share(data).catch(()=>{});}else{navigator.clipboard&&navigator.clipboard.writeText(data.url); s.textContent='Link copied'; setTimeout(()=>s.textContent='Share',1500);}}
  const t=e.target.closest('[data-toggle]'); if(t){const id=t.dataset.toggle; document.getElementById(id)?.classList.toggle('open');}
});
const filters=document.querySelectorAll('[data-filter-group] select'); filters.forEach(el=>el.addEventListener('change',()=>{ const group=el.closest('[data-filter-group]'); const market=group.querySelector('[name=market]')?.value||''; const category=group.querySelector('[name=category]')?.value||''; group.querySelectorAll('[data-score-row]').forEach(row=>{ const okM=!market||row.dataset.markets.split('|').includes(market); const okC=!category||row.dataset.categories.split('|').includes(category); row.hidden=!(okM&&okC); }); }));
const q=document.querySelector('[data-company-search]'); if(q){q.addEventListener('input',()=>{const v=q.value.toLowerCase().trim(); document.querySelectorAll('[data-company-result]').forEach(r=>r.hidden=v&&!r.dataset.companyResult.includes(v));});}
