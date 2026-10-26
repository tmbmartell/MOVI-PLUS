'use strict';
/* MOVI+ V8 · tela do motorista: escura, letra grande, o mais usado primeiro.
   Camada carregada por último, como as etapas anteriores: usa as mesmas rotas da API
   e não muda nenhuma regra do servidor. O gestor continua com as telas atuais. */
const V8_ICONS={
 home:'<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V21h14V9.5"/><path d="M10 21v-6h4v6"/>',
 list:'<path d="M9 6h12M9 12h12M9 18h12"/><circle cx="4" cy="6" r="1.2"/><circle cx="4" cy="12" r="1.2"/><circle cx="4" cy="18" r="1.2"/>',
 chat:'<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20.5l1.4-4.9A8 8 0 1 1 21 12Z"/>',
 grid:'<rect x="3.5" y="3.5" width="7" height="7" rx="2"/><rect x="13.5" y="3.5" width="7" height="7" rx="2"/><rect x="3.5" y="13.5" width="7" height="7" rx="2"/><rect x="13.5" y="13.5" width="7" height="7" rx="2"/>',
 plus:'<path d="M12 5v14M5 12h14"/>',
 minus:'<path d="M5 12h14"/>',
 up:'<path d="M12 19V5M6 11l6-6 6 6"/>',
 down:'<path d="M12 5v14M6 13l6 6 6-6"/>',
 car:'<path d="M4 16v-4l2.2-5.2A2 2 0 0 1 8 5.5h8a2 2 0 0 1 1.8 1.3L20 12v4"/><rect x="2.5" y="12" width="19" height="5" rx="1.5"/><path d="M5.5 17v2M18.5 17v2"/>',
 fuel:'<path d="M4 21V5a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v16"/><path d="M3 21h12M4 10h10"/><path d="M14 8h2a2 2 0 0 1 2 2v6a1.5 1.5 0 0 0 3 0V8l-3-3"/>',
 food:'<path d="M7 3v8M4 3v5a3 3 0 0 0 6 0V3M7 11v10"/><path d="M17 21V3c-2 1.5-3 4-3 7h3"/>',
 wrench:'<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.8-3.8a6 6 0 0 1-7.9 7.9l-6.9 6.9a2.1 2.1 0 0 1-3-3l6.9-6.9a6 6 0 0 1 7.9-7.9z"/>',
 card:'<rect x="2.5" y="5" width="19" height="14" rx="2"/><path d="M2.5 10h19M6 15h4"/>',
 shield:'<path d="M12 3 4 6v6c0 4.5 3.4 8 8 9 4.6-1 8-4.5 8-9V6z"/>',
 drop:'<path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z"/>',
 phone:'<rect x="6" y="2.5" width="12" height="19" rx="2.5"/><path d="M11 18h2"/>',
 dots:'<circle cx="5" cy="12" r="1.4"/><circle cx="12" cy="12" r="1.4"/><circle cx="19" cy="12" r="1.4"/>',
 user:'<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
 gift:'<rect x="3" y="8" width="18" height="4" rx="1"/><path d="M5 12v9h14v-9M12 8v13"/><path d="M12 8S10.5 3 7.5 3.5 7 8 12 8zM12 8s1.5-5 4.5-4.5S17 8 12 8z"/>',
 news:'<path d="M3 10v4a1 1 0 0 0 1 1h3l6 4V5L7 9H4a1 1 0 0 0-1 1z"/><path d="M17 8.5a5 5 0 0 1 0 7M19.5 6a8.5 8.5 0 0 1 0 12"/>',
 clipboard:'<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4V3h6v1M9 10h6M9 14h6M9 18h3"/>',
 pie:'<path d="M12 3a9 9 0 1 0 9 9h-9z"/><path d="M15 3.5A9 9 0 0 1 20.5 9H15z"/>',
 spark:'<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/><path d="M19 16v4M17 18h4"/>',
 file:'<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/>',
 lock:'<rect x="4.5" y="10.5" width="15" height="10" rx="2"/><path d="M8 10.5V7a4 4 0 0 1 8 0v3.5"/>',
 key:'<circle cx="8" cy="15" r="4"/><path d="M11 12 20 3M16 7l3 3"/>',
 logout:'<path d="M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3"/><path d="M10 17l5-5-5-5M15 12H3"/>',
 back:'<path d="M15 5l-7 7 7 7"/>',
 chev:'<path d="M9 5l7 7-7 7"/>',
 left:'<path d="M15 5l-7 7 7 7"/>',
 right:'<path d="M9 5l7 7-7 7"/>',
 check:'<path d="M4.5 12.5l5 5 10-11"/>',
 x:'<path d="M6 6l12 12M18 6 6 18"/>',
 trash:'<path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/>',
 send:'<path d="M4 12 20 4l-4 16-4-7z"/><path d="M12 13l8-9"/>',
 eye:'<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
 backspace:'<path d="M21 5H9l-6 7 6 7h12z"/><path d="M12.5 9.5l5 5M17.5 9.5l-5 5"/>',
 camera:'<path d="M4 8h3l2-3h6l2 3h3v11H4z"/><circle cx="12" cy="13" r="3.5"/>',
 mic:'<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V21M9 21h6"/>',
 star:'<path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z"/>',
 bell:'<path d="M6 16V11a6 6 0 0 1 12 0v5l2 2H4z"/><path d="M10 20a2 2 0 0 0 4 0"/>',
 wheel:'<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="2.5"/><path d="M3.5 10.5c3-1.8 5.6-2.5 8.5-2.5s5.5.7 8.5 2.5M10.5 14l-4 6M13.5 14l4 6"/>'
};
/* Marca MOVI+: volante com estrada e o "+" âmbar. Desenhado em SVG para ficar nítido em
   qualquer tamanho; o anel usa currentColor (creme no fundo escuro) e as linhas da estrada
   usam a cor do fundo onde o símbolo está (--mark-bg). */
const V8_MARK='<svg class="dv-mark" viewBox="0 0 100 100" aria-hidden="true" focusable="false">'+
 '<path d="M83.7 41A38 38 0 1 1 57.8 17.3" fill="none" stroke="currentColor" stroke-width="13" stroke-linecap="round"/>'+
 '<path d="M15 50C30 39 64 38 81 47L81 56C66 49 30 50 15 58Z" fill="currentColor"/>'+
 '<path d="M38 53H58L69 93H27Z" fill="currentColor"/>'+
 '<path d="M45.5 60 39 92M50.5 60 57 92" stroke="var(--mark-bg)" stroke-width="3.2" fill="none"/>'+
 '<path d="M48 62V90" stroke="var(--mark-bg)" stroke-width="2.4" stroke-dasharray="5 4" fill="none"/>'+
 '<path d="M80 9v26M67 22h26" stroke="var(--mark-bg)" stroke-width="16" fill="none"/>'+
 '<path d="M80 11v22M69 22h22" stroke="#f2ae40" stroke-width="9" fill="none"/></svg>';
const V8_PLUS='<svg class="dv-word-plus" viewBox="0 0 10 10" aria-hidden="true" focusable="false"><path d="M5 0v10M0 5h10" stroke="#f2ae40" stroke-width="3.4"/></svg>';
function v8Logo(word){return '<span class="dv-brand" role="img" aria-label="MOVI+">'+V8_MARK+(word?'<span class="dv-word" aria-hidden="true">MOVI'+V8_PLUS+'</span>':'')+'</span>'}
function v8i(name,cls){return '<svg class="dv-ic'+(cls?' '+cls:'')+'" viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'+(V8_ICONS[name]||'')+'</svg>'}

/* Onde o motorista ganha e com o que gasta: as categorias mais comuns primeiro. */
const V8_IN=[
 {cat:'Corridas Uber',label:'Uber',brand:true},{cat:'Corridas 99',label:'99',brand:true},
 {cat:'Corridas inDrive',label:'inDrive',brand:true},{cat:'Corridas Urbano Norte',label:'Urbano Norte',brand:true},
 {cat:'Corrida particular',label:'Corrida particular',icon:'user'},{cat:'Outros ganhos',label:'Outro ganho',icon:'dots'}
];
const V8_OUT=[
 {cat:'Combustível',label:'Combustível',icon:'fuel'},{cat:'Alimentação',label:'Comida',icon:'food'},
 {cat:'Manutenção',label:'Oficina',icon:'wrench'},{cat:'Parcela do carro',label:'Parcela do carro',icon:'card'},
 {cat:'Seguro',label:'Seguro',icon:'shield'},{cat:'Lavagem',label:'Lavagem',icon:'drop'},
 {cat:'Celular e internet',label:'Celular',icon:'phone'},{cat:'Outras despesas',label:'Outro gasto',icon:'dots'}
];
const V8_LEGACY={'Corridas Urbano Norte':'Urbano Norte','APLICATIVO':'Aplicativo','OUTROS':'Outros','Manutenção do veículo':'Oficina','Alimentação fora':'Comida fora','Outros / a confirmar':'Outros'};
function v8Cat(kind,cat,note){
 const origin=String(note||'').match(/^Origem: ([^|]+?) \|/);
 if(origin&&/^(APLICATIVO|OUTROS|Corridas|Outras receitas)$/.test(cat))return {label:origin[1].trim(),icon:'car'};
 const found=[...V8_IN,...V8_OUT].find(x=>x.cat===cat);
 if(found)return {label:found.label,icon:found.icon||'car'};
 if(/combust/i.test(cat))return {label:cat,icon:'fuel'};
 if(/corrida|uber|99|indrive|aplicativo/i.test(cat))return {label:V8_LEGACY[cat]||cat,icon:'car'};
 if(/manuten|oficina/i.test(cat))return {label:V8_LEGACY[cat]||cat,icon:'wrench'};
 if(/aliment|comida|mercado/i.test(cat))return {label:V8_LEGACY[cat]||cat,icon:'food'};
 return {label:V8_LEGACY[cat]||cat,icon:kind==='income'?'up':'down'};
}

const V8_MAIN=[['home','Início','home'],['history','Anotações','list'],['assistant','Assistente','chat'],['more','Mais','grid']];
const V8_ALIAS={finances:'history',chat:'assistant',consents:'privacy',form:'profile',interview:'profile',settings:'password','finance-agent':'agent',campaigns:'news',distribution:'plan'};
const V8_SUB={
 benefits:{title:'Benefícios',fn:()=>v8Benefits},news:{title:'Novidades',fn:()=>v8News},
 profile:{title:'Meu cadastro',fn:()=>v8Profile},'profile-all':{title:'Minhas respostas',fn:()=>v8ProfileAll,parent:'profile'},
 plan:{title:'Dividir meu dinheiro',fn:()=>v8Plan},agent:{title:'Foto e áudio',fn:()=>v8Agent},
 'agent-whats':{title:'WhatsApp',fn:()=>v8AgentWhats,parent:'agent',legacy:true},
 documents:{title:'Documentos',fn:()=>v8Docs},privacy:{title:'Privacidade',fn:()=>v8Privacy},
 password:{title:'Trocar senha',fn:()=>v8Password}
};
let v8Seq=0,v8Month='',v8LastTab='';

const v8Day=(d=new Date())=>d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0');
const v8Cap=s=>s.charAt(0).toUpperCase()+s.slice(1);
function v8DayLabel(iso){
 const today=v8Day(),y=new Date();y.setDate(y.getDate()-1);
 if(iso===today)return 'Hoje';
 if(iso===v8Day(y))return 'Ontem';
 const [a,m,d]=iso.split('-').map(Number);
 return v8Cap(new Date(a,m-1,d).toLocaleDateString('pt-BR',{weekday:'long',day:'numeric',month:'long'}));
}
function v8MonthLabel(ym){const [a,m]=ym.split('-').map(Number);return v8Cap(new Date(a,m-1,1).toLocaleDateString('pt-BR',{month:'long',year:'numeric'}))}
function v8Sign(kind,v){return (kind==='income'?'+ ':'− ')+brl(v)}
function v8Pretty(opt){const s=String(opt);return /[a-zà-ú]/.test(s)||s.length<4?s:v8Cap(s.toLowerCase())}
const v8Stale=seq=>seq!==v8Seq;

function v8Theme(on){
 document.documentElement.classList.toggle('dv-on',on);
 if(on)document.title='MOVI+';
 const meta=document.querySelector('meta[name=theme-color]');if(meta)meta.content=on?'#061a24':'#173f33';
}
v8Theme(true);

/* Aviso rápido no rodapé, com ação opcional (ex.: Desfazer). */
let v8ToastTimer=0;
function v8Toast(text,action,onAction){
 let el=document.getElementById('dvToast');
 if(!el){el=document.createElement('div');el.id='dvToast';el.className='dv-toast';el.setAttribute('role','status');el.setAttribute('aria-live','polite');document.body.appendChild(el)}
 el.classList.toggle('dv-toast-low',!document.getElementById('dvShell'));
 el.classList.toggle('dv-toast-high',!!document.getElementById('dvComposer'));
 el.innerHTML='<span>'+safe(text)+'</span>'+(action?'<button type="button" class="dv-press">'+safe(action)+'</button>':'');
 const b=el.querySelector('button');
 if(b)b.onclick=()=>{el.classList.remove('on');clearTimeout(v8ToastTimer);onAction()};
 requestAnimationFrame(()=>el.classList.add('on'));
 clearTimeout(v8ToastTimer);
 v8ToastTimer=setTimeout(()=>el.classList.remove('on'),action?6500:2800);
}
const v8PrevMsg=msg;
msg=function(t){if(document.documentElement.classList.contains('dv-on'))return v8Toast(t);return v8PrevMsg(t)};

/* Painel que sobe de baixo. Fecha no X, no fundo escuro ou com Esc. */
function v8Sheet(html,opts={}){
 const wrap=document.createElement('div');
 wrap.className='dv-sheet-wrap';
 wrap.innerHTML='<div class="dv-sheet-back"'+(opts.locked?'':' data-close')+'></div><section class="dv-sheet'+(opts.full?' dv-sheet-full':'')+'" role="dialog" aria-modal="true" aria-label="'+safe(opts.label||'Janela')+'">'+(opts.full?'':'<div class="dv-grip" aria-hidden="true"></div>')+html+'</section>';
 const last=document.activeElement;
 document.body.appendChild(wrap);
 document.body.style.overflow='hidden';
 requestAnimationFrame(()=>requestAnimationFrame(()=>wrap.classList.add('is-open')));
 let closed=false;
 const api={el:wrap.querySelector('.dv-sheet'),close(){
  if(closed)return;closed=true;
  wrap.classList.remove('is-open');document.removeEventListener('keydown',onKey,true);
  setTimeout(()=>{wrap.remove();if(!document.querySelector('.dv-sheet-wrap'))document.body.style.overflow=''},220);
  if(last&&last.focus&&document.contains(last))last.focus({preventScroll:true});
  if(opts.onClose)opts.onClose();
 }};
 function onKey(e){
  const all=document.querySelectorAll('.dv-sheet-wrap');if(all[all.length-1]!==wrap)return; // só o painel de cima
  if(e.key==='Escape'){e.preventDefault();if(!opts.locked)api.close();return}
  if(opts.onKey)opts.onKey(e);
 }
 document.addEventListener('keydown',onKey,true);
 wrap.addEventListener('click',e=>{if(e.target.closest('[data-close]'))api.close()});
 const first=api.el.querySelector('[data-autofocus]')||api.el.querySelector('button,input');
 if(first)setTimeout(()=>first.focus({preventScroll:true}),30);
 return api;
}
/* Pergunta de confirmação no lugar do confirm() do navegador. */
function v8Ask(title,text,yes,{danger=false}={}){
 return new Promise(resolve=>{
  let answered=false;
  const s=v8Sheet('<h2 class="dv-q">'+safe(title)+'</h2>'+(text?'<p class="dv-p" style="margin:10px 0 18px">'+safe(text)+'</p>':'<div style="height:16px"></div>')+
   '<div style="display:grid;gap:10px"><button type="button" class="dv-btn dv-press '+(danger?'dv-btn-red':'dv-btn-gold')+'" data-yes>'+safe(yes)+'</button>'+
   '<button type="button" class="dv-btn dv-btn-ghost dv-press" data-close>Não, voltar</button></div>',{label:title,onClose:()=>{if(!answered)resolve(false)}});
  s.el.querySelector('[data-yes]').onclick=()=>{answered=true;resolve(true);s.close()};
 });
}
function v8Busy(btn,on,label){if(!btn)return;if(on){btn.dataset.label=btn.innerHTML;btn.disabled=true;if(label)btn.textContent=label}else{btn.disabled=false;if(btn.dataset.label)btn.innerHTML=btn.dataset.label}}
function v8Error(text){return '<div class="dv-empty">'+v8i('x')+'<p>Não deu para abrir agora.</p><p class="dv-small">'+safe(text)+'</p><button type="button" class="dv-btn dv-btn-gold dv-press" data-retry>Tentar de novo</button></div>'}

/* Estrutura: topo + conteúdo + menu de baixo com 4 itens. */
function v8Shell(){
 let shell=document.getElementById('dvShell');
 if(!shell){
  const app=document.getElementById('app');
  app.innerHTML='<div class="dv-shell" id="dvShell"><header class="dv-top" id="dvTop"></header><main id="body" class="dv-main" tabindex="-1"></main>'+
   '<div class="dv-tabbar" role="navigation" aria-label="Menu principal">'+V8_MAIN.map(([id,label,icon])=>'<button type="button" class="dv-tab dv-press" data-tab="'+id+'">'+v8i(icon)+'<span>'+label+'</span></button>').join('')+'</div></div>';
  shell=document.getElementById('dvShell');
  shell.addEventListener('click',v8ShellClick);
 }
 const sub=V8_SUB[tab],active=sub?'more':tab;
 shell.querySelectorAll('.dv-tab').forEach(b=>{if(b.dataset.tab===active)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current')});
 const top=document.getElementById('dvTop');
 if(sub){
  const parent=sub.parent||'more',lockBack=user&&user.must_change;
  top.innerHTML=(lockBack?'':'<button type="button" class="dv-back dv-press" data-go="'+parent+'" aria-label="Voltar">'+v8i('back')+'Voltar</button>')+'<h1 class="dv-top-title">'+safe(sub.title)+'</h1>';
 }else if(tab==='home'){
  const first=String(user.name||'').trim().split(/\s+/)[0]||'motorista';
  top.innerHTML='<span class="dv-top-mark">'+v8Logo(false)+'</span><div class="dv-hello"><small>'+safe(v8Cap(new Date().toLocaleDateString('pt-BR',{weekday:'long',day:'numeric',month:'long'})))+'</small><h1>Olá, '+safe(first)+'</h1></div>';
 }else{
  top.innerHTML='<h1>'+safe(V8_MAIN.find(x=>x[0]===tab)[1])+'</h1>';
 }
 document.getElementById('body').classList.toggle('dv-has-composer',tab==='assistant');
}
function v8Go(next){tab=next;render()}
async function v8ShellClick(e){
 const t=e.target.closest('[data-tab],[data-go],[data-add],[data-retry],[data-logout]');
 if(!t)return;
 if(t.dataset.tab){v8Go(t.dataset.tab);return}
 if(t.dataset.go){v8Go(t.dataset.go);return}
 if(t.dataset.add){v8OpenAdd(t.dataset.add);return}
 if('retry' in t.dataset){render();return}
 if('logout' in t.dataset){
  if(!await v8Ask('Sair do aplicativo?','Para entrar de novo, você vai precisar do seu usuário e senha.','Sim, sair'))return;
  try{await request('logout',{})}catch{}
  user=null;tab='home';login();
 }
}

const v8PrevNav=nav;
nav=function(){if(user&&user.role==='driver')return v8Shell();v8Theme(false);return v8PrevNav()};
const v8PrevHeading=heading;
heading=function(t,sub){if(user&&user.role==='driver')return '';return v8PrevHeading(t,sub)};

const v8PrevRender=render;
render=async function(){
 // O gestor também usa o tema da marca (gestor-v8.js); só a página pública antiga é clara.
 if(!user||user.role!=='driver'){if(!user||user.role!=='admin')v8Theme(false);return v8PrevRender()}
 v8Theme(true);
 if(V8_ALIAS[tab])tab=V8_ALIAS[tab];
 if(user.must_change)tab='password';
 if(!V8_SUB[tab]&&!V8_MAIN.some(x=>x[0]===tab))tab='home';
 if(!user.must_change&&v8LegalChecked!==user.id){
  try{if(!await v8TermsGate())return;v8LegalChecked=user.id}
  catch(err){v8Toast(err.message);return}
 }
 const seq=++v8Seq,changed=tab!==v8LastTab;v8LastTab=tab;
 v8Shell();
 const body=document.getElementById('body');
 if(changed){body.onclick=null;body.onchange=null;window.scrollTo(0,0);if(tab!=='plan')v8PlanDraft=null}
 body.classList.toggle('dv-legacy',!!(V8_SUB[tab]&&V8_SUB[tab].legacy));
 const screens={home:v8Home,history:v8History,assistant:v8Assistant,more:v8More};
 try{await (V8_SUB[tab]?V8_SUB[tab].fn():screens[tab])(seq)}
 catch(err){
  // Termos atualizados durante o uso: o servidor recusa (428) e pedimos o aceite de novo.
  if(/Aceite os termos/.test(err.message)){v8LegalChecked=null;return render()}
  if(!v8Stale(seq))body.innerHTML=v8Error(err.message);
 }
};

/* ---------- Início ---------- */
async function v8Pending(){
 try{const r=await request('finance-agent/proposals');return r.items.filter(x=>x.status==='pending')}catch{return []}
}
async function v8Home(seq){
 const today=v8Day(),month=today.slice(0,7);
 const [fin,pending,extra]=await Promise.all([request('finances?month='+month),v8Pending(),
  Promise.allSettled([request('program/benefits'),request('profile')])]);
 if(v8Stale(seq))return;
 const todayItems=fin.items.filter(x=>x.entry_date===today);
 const tin=todayItems.filter(x=>x.kind==='income').reduce((a,x)=>a+x.amount,0);
 const tout=todayItems.filter(x=>x.kind==='expense').reduce((a,x)=>a+x.amount,0);
 const left=Math.round((tin-tout)*100)/100,s=fin.summary;
 const mLeft=Math.round((s.income-s.expense)*100)/100,ratio=s.income>0?Math.max(0,Math.min(100,mLeft/s.income*100)):0;
 document.getElementById('body').innerHTML=
 '<section class="dv-today" aria-label="Resumo de hoje"><p class="dv-kicker">'+(left<0?'Hoje faltou':'Hoje sobrou')+'</p>'+
 '<p class="dv-big dv-money '+(left<0?'dv-neg':'dv-pos')+'">'+brl(Math.abs(left))+'</p>'+
 '<div class="dv-split"><div><span class="dv-in">'+v8i('up')+'Ganhei</span><b class="dv-money">'+brl(tin)+'</b></div><div><span class="dv-out">'+v8i('down')+'Gastei</span><b class="dv-money">'+brl(tout)+'</b></div></div></section>'+
 '<div class="dv-actions"><button type="button" class="dv-act dv-act-in dv-press" data-add="income">'+v8i('plus')+'GANHEI</button><button type="button" class="dv-act dv-act-out dv-press" data-add="expense">'+v8i('minus')+'GASTEI</button></div>'+
 // Dica só para quem está começando: some quando a pessoa já anota com frequência.
 (fin.items.length<5?'<p class="dv-small dv-center">Toque em <b>GANHEI</b> quando receber e em <b>GASTEI</b> quando pagar algo.</p>':'')+
 (pending.length?'<button type="button" class="dv-pending dv-press" data-pending>'+v8i('bell')+'<span>Você tem '+pending.length+' anotaç'+(pending.length>1?'ões':'ão')+' para conferir</span>'+v8i('chev','dv-chev')+'</button>':'')+
 '<section class="dv-card"><h2 class="dv-h">'+safe(v8MonthLabel(month))+'</h2><div class="dv-month-rows">'+
 '<div class="dv-month-row"><span>Ganhei</span><b class="dv-money dv-in">'+brl(s.income)+'</b></div>'+
 '<div class="dv-month-row"><span>Gastei</span><b class="dv-money dv-out">'+brl(s.expense)+'</b></div>'+
 '<div class="dv-bar" aria-hidden="true"><i style="width:'+ratio.toFixed(1)+'%"></i></div>'+
 '<div class="dv-month-row"><span>'+(mLeft<0?'Faltou':'Sobrou')+'</span><b class="dv-money '+(mLeft<0?'dv-neg':'')+'">'+brl(Math.abs(mLeft))+'</b></div></div></section>'+
 '<section><div class="dv-rowhead"><h2 class="dv-h">Últimas anotações</h2>'+(fin.items.length?'<button type="button" class="dv-link" data-go="history">Ver todas</button>':'')+'</div>'+
 (fin.items.length?'<div class="dv-list">'+fin.items.slice(0,3).map(v8ItemRow).join('')+'</div>':
  '<div class="dv-empty">'+v8i('list')+'<p>Nada anotado ainda</p><p class="dv-small">Toque em GANHEI ou GASTEI para começar.</p></div>')+'</section>'+
 v8HomeHints(extra);
 v8BindItems(fin.items);
 const p=document.querySelector('[data-pending]');if(p)p.onclick=()=>v8ReviewPending(pending);
}

/* Segundo plano do Início: sugestões pequenas, explicadas, para quando houver tempo. */
function v8HomeHints([ben,prof]){
 const cards=[];
 if(prof.status==='fulfilled'&&prof.value.progress.percent<100){
  const pr=prof.value.progress;
  cards.push(['profile','clipboard','green','Complete seu cadastro','Está '+pr.percent+'% pronto. Cada resposta dá pontos para pedir benefícios.']);
 }
 if(ben.status==='fulfilled'){
  const pts=ben.value.points.total,list=ben.value.items.filter(b=>b.active&&b.remaining>0).sort((a,b)=>a.points_required-b.points_required);
  const can=list.find(b=>pts>=b.points_required),next=list.find(b=>pts<b.points_required);
  if(can)cards.push(['benefits','gift','gold','Você já pode pedir um benefício',can.title+'. Você tem '+pts+' pontos.']);
  else if(next)cards.push(['benefits','gift','gold','Faltam '+(next.points_required-pts)+' pontos',' para pedir: '+next.title+'.']);
 }
 if(!cards.length)return '';
 return '<section><h2 class="dv-group-title">QUANDO TIVER UM TEMPINHO</h2><div class="dv-group">'+cards.slice(0,2).map(([go,icon,tone,t,s])=>
  '<button type="button" class="dv-row dv-row-compact dv-press" data-go="'+go+'"><span class="dv-row-ic dv-tone-'+tone+'">'+v8i(icon)+'</span><span class="dv-row-txt"><b>'+safe(t)+'</b><small>'+safe(s)+'</small></span>'+v8i('chev','dv-chev')+'</button>').join('')+'</div></section>';
}

/* ---------- Anotar (2 passos: valor e onde) ---------- */
function v8FormatTyped(v){
 const [i,d]=String(v||'').split(',');
 const int=(i||'0').replace(/^0+(?=\d)/,'').replace(/\B(?=(\d{3})+(?!\d))/g,'.');
 return int+(d===undefined?'<span class="dv-ph">,00</span>':','+d+'<span class="dv-ph">'+'0'.repeat(2-d.length)+'</span>');
}
function v8KeyPress(typed,k,maxInt=7){
 if(k==='del')return typed.slice(0,-1);
 if(k===',')return typed.includes(',')?typed:(typed||'0')+',';
 const [i,d]=typed.split(',');
 if(d!==undefined)return d.length<2?typed+k:typed;
 return (i||'').length<maxInt?(typed==='0'?'':typed)+k:typed;
}
const v8Typed=n=>{const [i,d]=Number(n||0).toFixed(2).split('.');return Number(n)>0?(d==='00'?i:i+','+d):''};
const v8TypedValue=t=>Number((t||'0').replace(',','.'));
const v8KeysHtml=()=>'<div class="dv-keys" role="group" aria-label="Teclado de números">'+['1','2','3','4','5','6','7','8','9',',','0','del'].map(k=>
 '<button type="button" class="dv-key dv-press" data-key="'+k+'" aria-label="'+(k==='del'?'Apagar':k===','?'Vírgula dos centavos':k)+'">'+(k==='del'?v8i('backspace'):k)+'</button>').join('')+'</div>';
function v8KeyboardKey(e,press,enter){
 if(/^[0-9]$/.test(e.key)){e.preventDefault();press(e.key)}
 else if(e.key===','||e.key==='.'){e.preventDefault();press(',')}
 else if(e.key==='Backspace'){e.preventDefault();press('del')}
 else if(e.key==='Enter'&&enter){e.preventDefault();enter()}
}
/* Teclado de valor em painel próprio (corrigir valor, total da divisão). */
function v8Keypad({title,tone,initial,done,onDone,maxInt=7}){
 let typed=v8Typed(initial);
 const s=v8Sheet('<div class="dv-add dv-add-'+(tone||'in')+'"><div class="dv-sheet-head"><h2>'+safe(title)+'</h2><button type="button" class="dv-x dv-press" data-close aria-label="Fechar">'+v8i('x')+'</button></div>'+
  '<div class="dv-step"><div class="dv-amount" aria-live="polite"><span class="dv-cur">R$</span><span id="dvAmt">'+v8FormatTyped(typed)+'</span></div><p class="dv-err" id="dvKpErr" role="alert"></p>'+v8KeysHtml()+
  '<button type="button" class="dv-btn dv-btn-gold dv-press" id="dvKpOk">'+safe(done||'Pronto')+'</button></div></div>',{full:true,label:title,onKey:e=>v8KeyboardKey(e,press,()=>ok.click())});
 const el=s.el,ok=el.querySelector('#dvKpOk');
 function press(k){typed=v8KeyPress(typed,k,maxInt);el.querySelector('#dvAmt').innerHTML=v8FormatTyped(typed);ok.disabled=!(v8TypedValue(typed)>0)}
 el.querySelector('.dv-keys').onclick=e=>{const k=e.target.closest('[data-key]');if(k)press(k.dataset.key)};
 ok.disabled=!(v8TypedValue(typed)>0);
 ok.onclick=async()=>{
  v8Busy(ok,true,'Salvando...');
  try{await onDone(v8TypedValue(typed));s.close()}
  catch(err){v8Busy(ok,false);el.querySelector('#dvKpErr').textContent=err.message}
 };
}
function v8OpenAdd(kind){
 const isIn=kind==='income',list=isIn?V8_IN:V8_OUT;
 let typed='',date=v8Day();
 const y=new Date();y.setDate(y.getDate()-1);
 const s=v8Sheet('<div class="dv-add '+(isIn?'dv-add-in':'dv-add-out')+'">'+
  '<div class="dv-sheet-head"><h2 id="dvAddTitle">'+(isIn?'Quanto você ganhou?':'Quanto você gastou?')+'</h2><button type="button" class="dv-x dv-press" data-close aria-label="Fechar">'+v8i('x')+'</button></div>'+
  '<div class="dv-step" id="dvStep1"><div class="dv-amount" aria-live="polite"><span class="dv-cur">R$</span><span id="dvAmt">'+v8FormatTyped('')+'</span></div>'+
  '<p class="dv-hint" id="dvHint">Digite o valor nos números abaixo</p>'+v8KeysHtml()+
  '<button type="button" class="dv-btn '+(isIn?'dv-btn-green':'dv-btn-red')+' dv-press" id="dvNext" disabled>Continuar</button></div>'+
  '<div class="dv-step" id="dvStep2" hidden><button type="button" class="dv-chosen dv-press" id="dvEdit"><span>Valor<br><small>Tocar para mudar</small></span><b class="dv-money" id="dvAmt2"></b></button>'+
  '<div><p class="dv-label" style="margin:4px 0 8px">Qual dia?</p><div class="dv-chips" role="group" aria-label="Dia">'+
  '<button type="button" class="dv-chip dv-press" data-day="'+v8Day()+'" aria-pressed="true">Hoje</button><button type="button" class="dv-chip dv-press" data-day="'+v8Day(y)+'" aria-pressed="false">Ontem</button><button type="button" class="dv-chip dv-press" data-day="other" aria-pressed="false">Outro dia</button></div>'+
  '<input type="date" class="dv-input dv-date" id="dvDate" min="'+v8Day(new Date(Date.now()-729*864e5))+'" max="'+v8Day()+'" aria-label="Escolha o dia"></div>'+
  '<p class="dv-q">'+(isIn?'Onde você ganhou?':'Com o que você gastou?')+'</p><p class="dv-small" style="margin-top:-8px">Toque em uma opção para salvar</p>'+
  '<div class="dv-tiles">'+list.map(c=>'<button type="button" class="dv-tile dv-press" data-cat="'+safe(c.cat)+'">'+(c.brand?'<span class="dv-tile-brand">'+safe(c.label)+'</span>':v8i(c.icon)+'<span>'+safe(c.label)+'</span>')+'</button>').join('')+'</div></div></div>',
  {full:true,label:isIn?'Anotar ganho':'Anotar gasto',onKey:e=>{if(!s1.hidden)v8KeyboardKey(e,press,()=>{if(!next.disabled)next.click()})}});
 const el=s.el,s1=el.querySelector('#dvStep1'),s2=el.querySelector('#dvStep2'),next=el.querySelector('#dvNext');
 const value=()=>v8TypedValue(typed);
 function press(k){
  typed=v8KeyPress(typed,k,5);
  el.querySelector('#dvAmt').innerHTML=v8FormatTyped(typed);
  next.disabled=!(value()>0);
  el.querySelector('#dvHint').textContent=value()>0?'Confira o valor e toque em Continuar':'Digite o valor nos números abaixo';
 }
 el.querySelector('.dv-keys').onclick=e=>{const k=e.target.closest('[data-key]');if(k)press(k.dataset.key)};
 next.onclick=()=>{
  if(!(value()>0))return;
  el.querySelector('#dvAmt2').textContent=brl(value());
  el.querySelector('#dvAddTitle').textContent=isIn?'Ganhei '+brl(value()):'Gastei '+brl(value());
  s1.hidden=true;s2.hidden=false;
  const first=s2.querySelector('.dv-tile');if(first)first.focus({preventScroll:true});
 };
 el.querySelector('#dvEdit').onclick=()=>{s2.hidden=true;s1.hidden=false;el.querySelector('#dvAddTitle').textContent=isIn?'Quanto você ganhou?':'Quanto você gastou?';next.focus()};
 const dateInput=el.querySelector('#dvDate');
 el.querySelector('.dv-chips').onclick=e=>{
  const c=e.target.closest('[data-day]');if(!c)return;
  el.querySelectorAll('[data-day]').forEach(b=>b.setAttribute('aria-pressed',String(b===c)));
  if(c.dataset.day==='other'){dateInput.classList.add('on');dateInput.value=date;dateInput.focus()}
  else{dateInput.classList.remove('on');date=c.dataset.day}
 };
 dateInput.onchange=()=>{if(dateInput.value)date=dateInput.value};
 el.querySelector('.dv-tiles').onclick=async e=>{
  const t=e.target.closest('[data-cat]');if(!t)return;
  el.querySelectorAll('[data-cat]').forEach(b=>b.disabled=true);
  const amount=value().toFixed(2),cat=t.dataset.cat;
  try{
   await request('finances',{kind,category:cat,amount,date,note:''});
   s.close();
   let newest=null;
   try{const d=await request('finances?month='+date.slice(0,7));newest=d.items.reduce((m,x)=>x.id>(m?m.id:0)?x:m,null)}catch{}
   if(['home','history'].includes(tab))await render();
   v8Toast('Anotado: '+v8Sign(kind,amount)+' · '+v8Cat(kind,cat).label,newest?'Desfazer':'',async()=>{
    try{await request('finances/'+newest.id,undefined,'DELETE');v8Toast('Anotação desfeita');if(['home','history'].includes(tab))render()}catch(err){v8Toast(err.message)}
   });
  }catch(err){
   el.querySelectorAll('[data-cat]').forEach(b=>b.disabled=false);
   v8Toast(err.message);
  }
 };
}

/* ---------- Anotações ---------- */
function v8ItemRow(x){
 const c=v8Cat(x.kind,x.category,x.note),isIn=x.kind==='income';
 const note=String(x.note||'').replace(/^Origem: [^|]+\| ?/,'');
 return '<button type="button" class="dv-item dv-press" data-item="'+x.id+'"><span class="dv-badge '+(isIn?'dv-badge-in':'dv-badge-out')+'">'+v8i(c.icon)+'</span>'+
  '<span class="dv-item-txt"><b>'+safe(c.label)+'</b><small>'+safe(note||v8DayLabel(x.entry_date))+'</small></span>'+
  '<span class="dv-item-val dv-money '+(isIn?'dv-in':'dv-out')+'">'+v8Sign(x.kind,x.amount)+'</span></button>';
}
function v8BindItems(items){
 document.querySelectorAll('#body [data-item]').forEach(b=>{
  b.onclick=()=>{const x=items.find(i=>String(i.id)===b.dataset.item);if(x)v8ItemSheet(x)};
 });
}
function v8ItemSheet(x){
 const c=v8Cat(x.kind,x.category,x.note),isIn=x.kind==='income';
 const s=v8Sheet('<div class="dv-sheet-head"><h2>'+(isIn?'Ganho':'Gasto')+'</h2><button type="button" class="dv-x dv-press" data-close aria-label="Fechar">'+v8i('x')+'</button></div>'+
  '<p class="dv-big dv-money '+(isIn?'dv-pos':'dv-neg')+'" style="margin:6px 0 4px">'+v8Sign(x.kind,x.amount)+'</p>'+
  '<p class="dv-p"><b style="color:var(--text)">'+safe(c.label)+'</b> · '+safe(v8DayLabel(x.entry_date))+'</p>'+
  (x.note?'<p class="dv-small" style="margin-top:8px">'+safe(x.note)+'</p>':'')+
  '<div id="dvDel" style="display:grid;gap:10px;margin-top:22px"><button type="button" class="dv-btn dv-btn-gold dv-press" data-fix>Mudar o valor</button>'+
  '<button type="button" class="dv-btn dv-btn-danger dv-press" data-del>'+v8i('trash')+'Apagar</button></div>',{label:'Anotação'});
 s.el.querySelector('[data-fix]').onclick=()=>{
  s.close();
  v8Keypad({title:'Qual é o valor certo?',tone:isIn?'in':'out',initial:x.amount,maxInt:5,done:'Salvar valor novo',onDone:async v=>{
   // Não existe rota de edição: cria o registro corrigido e só então apaga o antigo.
   await request('finances',{kind:x.kind,category:x.category,amount:v.toFixed(2),date:x.entry_date,note:x.note||''});
   await request('finances/'+x.id,undefined,'DELETE');
   v8Toast('Valor corrigido: '+v8Sign(x.kind,v));render();
  }});
 };
 s.el.querySelector('[data-del]').onclick=()=>{
  const box=s.el.querySelector('#dvDel');
  // "Não" fica onde o dedo estava; "Sim" vai para baixo, para evitar apagar com toque duplo.
  box.innerHTML='<p class="dv-q" style="margin:0">Apagar mesmo?</p><p class="dv-small">Não dá para desfazer depois.</p>'+
   '<button type="button" class="dv-btn dv-btn-ghost dv-press" data-close>Não, deixar como está</button><button type="button" class="dv-btn dv-btn-red dv-press" data-yes>Sim, apagar</button>';
  box.querySelector('[data-yes]').onclick=async e=>{
   v8Busy(e.currentTarget,true,'Apagando...');
   try{await request('finances/'+x.id,undefined,'DELETE');s.close();v8Toast('Anotação apagada');render()}
   catch(err){v8Busy(e.currentTarget,false);v8Toast(err.message)}
  };
 };
}
async function v8History(seq){
 const now=v8Day().slice(0,7);
 if(!v8Month||v8Month>now)v8Month=now;
 const d=await request('finances?month='+v8Month);
 if(v8Stale(seq))return;
 const s=d.summary,left=Math.round((s.income-s.expense)*100)/100,groups={};
 d.items.forEach(x=>{(groups[x.entry_date]=groups[x.entry_date]||[]).push(x)});
 document.getElementById('body').innerHTML=
 '<div class="dv-monthnav"><button type="button" class="dv-iconbtn dv-press" data-month="-1" aria-label="Mês anterior">'+v8i('left')+'</button><b>'+safe(v8MonthLabel(v8Month))+'</b>'+
 '<button type="button" class="dv-iconbtn dv-press" data-month="1" aria-label="Próximo mês" '+(v8Month>=now?'disabled':'')+'>'+v8i('right')+'</button></div>'+
 '<div class="dv-sum3"><div><span>Ganhei</span><b class="dv-money dv-in">'+brl(s.income)+'</b></div><div><span>Gastei</span><b class="dv-money dv-out">'+brl(s.expense)+'</b></div><div><span>'+(left<0?'Faltou':'Sobrou')+'</span><b class="dv-money'+(left<0?' dv-out':'')+'">'+brl(Math.abs(left))+'</b></div></div>'+
 (d.items.length?Object.keys(groups).map(day=>'<h2 class="dv-day">'+safe(v8DayLabel(day))+'</h2><div class="dv-list">'+groups[day].map(v8ItemRow).join('')+'</div>').join(''):
  '<div class="dv-empty">'+v8i('list')+'<p>Nenhuma anotação em '+safe(v8MonthLabel(v8Month).toLowerCase())+'</p><button type="button" class="dv-btn dv-btn-green dv-press" data-add="income">'+v8i('plus')+'Anotar um ganho</button></div>')+
 (d.items.length?'<p class="dv-small" style="text-align:center">Toque numa anotação para ver ou apagar.</p>':'');
 v8BindItems(d.items);
 document.querySelectorAll('[data-month]').forEach(b=>b.onclick=()=>{
  const [a,m]=v8Month.split('-').map(Number),dt=new Date(a,m-1+Number(b.dataset.month),1);
  v8Month=v8Day(dt).slice(0,7);render();
 });
}

/* Sugestões do agente (WhatsApp, foto ou áudio) que esperam confirmação. */
function v8ReviewPending(items){
 const rows=items.map(x=>{const p=x.proposal||{},kind=p.kind==='income'?'income':'expense';
  return '<div class="dv-card" data-prop="'+x.id+'" style="background:var(--surface-2)"><p class="dv-big dv-money '+(kind==='income'?'dv-pos':'dv-neg')+'" style="font-size:40px;margin:0">'+(p.amount==null?'Valor ?':v8Sign(kind,p.amount))+'</p>'+
  '<p class="dv-p">'+safe(p.category||'Sem categoria')+(p.summary?' · '+safe(String(p.summary).slice(0,80)):'')+'</p><div class="dv-btn-row" style="margin-top:12px">'+
  (p.amount==null?'':'<button type="button" class="dv-btn dv-btn-green dv-press" data-ok="'+x.id+'">'+v8i('check')+'Está certo</button>')+
  '<button type="button" class="dv-btn dv-btn-ghost dv-press" data-no="'+x.id+'">Jogar fora</button></div></div>'}).join('');
 const s=v8Sheet('<div class="dv-sheet-head"><h2>Conferir anotações</h2><button type="button" class="dv-x dv-press" data-close aria-label="Fechar">'+v8i('x')+'</button></div><p class="dv-p" style="margin-bottom:14px">O assistente leu estas mensagens. Confira o valor antes de salvar.</p><div style="display:grid;gap:12px">'+rows+'</div>',{label:'Conferir anotações'});
 s.el.onclick=async e=>{
  const ok=e.target.closest('[data-ok]'),no=e.target.closest('[data-no]');if(!ok&&!no)return;
  const id=(ok||no).dataset.ok||(ok||no).dataset.no,x=items.find(i=>String(i.id)===id),p=x.proposal||{};
  try{
   if(ok)await request('finance-agent/proposals/'+id+'/confirm',{kind:p.kind==='income'?'income':'expense',amount:p.amount,category:p.category||'Outros',note:String(p.summary||'').slice(0,200),date:p.date||v8Day()});
   else await request('finance-agent/proposals/'+id+'/discard',{});
   s.el.querySelector('[data-prop="'+id+'"]').remove();
   v8Toast(ok?'Anotação salva':'Sugestão descartada');
   if(!s.el.querySelector('[data-prop]'))s.close();
   render();
  }catch(err){v8Toast(err.message)}
 };
}

/* ---------- Assistente (conversa por regras, sem custo de IA) ---------- */
/* As respostas do servidor usam termos contábeis e ponto decimal; aqui viram fala do dia a dia. */
function v8Plain(text){
 let t=String(text||'').replace(/R\$ ?(-?\d+)\.(\d{2})/g,(m,i,d)=>brl(Number(i+'.'+d)));
 let m=t.match(/^Registrei (R\$\s?[\d.,]+) em (.+?)\. É uma declaração sua/);
 if(m)return 'Anotei '+m[1]+' em '+({APLICATIVO:'corridas de aplicativo',OUTROS:'outros ganhos'}[m[2]]||m[2])+'.';
 m=t.match(/^Você informou (R\$\s?-?[\d.,]+) de entradas e (R\$\s?-?[\d.,]+) de despesas\. O resultado parcial é (R\$\s?(-?)[\d.,]+)\./);
 if(m)return 'Somando tudo o que você anotou:\nGanhou '+m[1]+'\nGastou '+m[2]+'\n'+(m[4]?'Faltou ':'Sobrou ')+m[3].replace('-','')+'\n\nConta só o que você anotou aqui.';
 if(/^Posso registrar mensagens como/.test(t))return 'Não entendi. Tente escrever assim:\n• Ganhei 200 na Uber\n• Gastei 80 de gasolina\n• Quanto sobrou?';
 if(/ainda não informou sua meta de economia/.test(t))return 'Você ainda não disse quanto quer guardar por mês. Responda em Mais › Meu cadastro.';
 m=t.match(/^Sua meta mensal de economia é (R\$\s?[\d.,]+)\./);
 if(m)return 'Sua meta é guardar '+m[1]+' por mês. Continue anotando para ver se está dando certo.';
 return t;
}
function v8Bubble(who,text){return '<div class="dv-msg '+(who==='me'?'dv-msg-me':'dv-msg-bot')+'">'+(who==='me'?'':'<b>ASSISTENTE</b>')+safe(who==='me'?text:v8Plain(text))+'</div>'}
async function v8Assistant(seq){
 const d=await request('chat');
 if(v8Stale(seq))return;
 const body=document.getElementById('body');
 body.innerHTML='<div class="dv-chat" id="dvChat" aria-live="polite">'+
  v8Bubble('bot','Oi! Me conte o que você ganhou ou gastou, do seu jeito. Eu anoto para você.')+
  d.items.map(x=>v8Bubble(x.speaker==='motorista'?'me':'bot',x.body)).join('')+'</div>'+
  '<div class="dv-composer" id="dvComposer"><div class="dv-chips dv-chips-row" role="group" aria-label="Atalhos">'+
  [['ask','Quanto sobrou?'],['ask','Qual é a minha meta?'],['fill','Ganhei 200 na Uber'],['fill','Gastei 80 de gasolina']].map(([k,t])=>'<button type="button" class="dv-chip dv-press" data-'+k+'="'+safe(t)+'">'+safe(t)+'</button>').join('')+'</div>'+
  '<form class="dv-composer-form" id="dvChatForm"><input name="text" maxlength="400" autocomplete="off" placeholder="Escreva aqui..." aria-label="Mensagem para o assistente" required><button type="submit" class="dv-send dv-press" aria-label="Enviar">'+v8i('send')+'</button></form></div>';
 const chat=document.getElementById('dvChat'),form=document.getElementById('dvChatForm'),input=form.elements.text;
 const toBottom=()=>window.scrollTo(0,document.body.scrollHeight);
 toBottom();
 async function send(text){
  text=String(text||'').trim();if(!text)return;
  chat.insertAdjacentHTML('beforeend',v8Bubble('me',text)+'<div class="dv-msg dv-msg-bot dv-msg-wait" id="dvWait"><b>ASSISTENTE</b>Escrevendo...</div>');
  input.value='';toBottom();
  const btn=form.querySelector('button');btn.disabled=true;
  try{
   const r=await request('chat',{text});
   const w=document.getElementById('dvWait');if(w)w.outerHTML=v8Bubble('bot',r.answer);
   if(/^Registrei/.test(r.answer)){
    let newest=null;
    try{const f=await request('finances?month='+v8Day().slice(0,7));newest=f.items.reduce((m,x)=>x.id>(m?m.id:0)?x:m,null)}catch{}
    const last=chat.querySelector('.dv-msg-bot:last-child');
    if(newest&&last)last.innerHTML='<b>ASSISTENTE</b>'+safe('Anotei '+brl(newest.amount)+(newest.kind==='income'?' de ':' em ')+v8Cat(newest.kind,newest.category,newest.note).label+'.');
    v8Toast('Anotado: '+(newest?v8Sign(newest.kind,newest.amount):''),newest?'Desfazer':'',async()=>{
     try{await request('finances/'+newest.id,undefined,'DELETE');chat.insertAdjacentHTML('beforeend',v8Bubble('bot','Pronto, apaguei essa anotação.'));toBottom()}catch(err){v8Toast(err.message)}
    });
   }
  }catch(err){const w=document.getElementById('dvWait');if(w)w.outerHTML=v8Bubble('bot','Não consegui responder agora. Tente de novo.')}
  finally{btn.disabled=false;toBottom()}
 }
 form.onsubmit=e=>{e.preventDefault();send(input.value)};
 document.getElementById('dvComposer').onclick=e=>{
  const a=e.target.closest('[data-ask]'),f=e.target.closest('[data-fill]');
  if(a)send(a.dataset.ask);
  if(f){input.value=f.dataset.fill;input.focus();input.setSelectionRange(input.value.length,input.value.length)}
 };
}

/* ---------- Mais ---------- */
async function v8More(seq){
 const [ben,prof,news]=await Promise.allSettled([request('program/benefits'),request('profile'),request('program/campaigns')]);
 if(v8Stale(seq))return;
 const pts=ben.status==='fulfilled'?ben.value.points.total:null,pct=prof.status==='fulfilled'?prof.value.progress.percent:null;
 const n=news.status==='fulfilled'?news.value.items.length:0;
 const row=(go,icon,tone,title,sub)=>'<button type="button" class="dv-row dv-press" data-go="'+go+'"><span class="dv-row-ic dv-tone-'+tone+'">'+v8i(icon)+'</span><span class="dv-row-txt"><b>'+title+'</b>'+(sub?'<small>'+sub+'</small>':'')+'</span>'+v8i('chev','dv-chev')+'</button>';
 const small=(go,icon,tone,title,sub)=>'<button type="button" class="dv-row dv-row-compact dv-press" data-go="'+go+'"><span class="dv-row-ic dv-tone-'+tone+'">'+v8i(icon)+'</span><span class="dv-row-txt"><b>'+title+'</b><small>'+sub+'</small></span>'+v8i('chev','dv-chev')+'</button>';
 const big=(go,icon,tone,title,value,sub)=>'<button type="button" class="dv-bigtile dv-press" data-go="'+go+'"><span class="dv-row-ic dv-tone-'+tone+'">'+v8i(icon)+'</span><b>'+title+'</b><strong>'+value+'</strong><small>'+sub+'</small></button>';
 document.getElementById('body').innerHTML=
 '<h2 class="dv-group-title" style="margin-top:0">MAIS USADOS</h2><div class="dv-bigtiles">'+
  big('benefits','gift','gold','Benefícios',pts===null?'—':pts+' pts','Descontos e prêmios')+
  big('news','news','blue','Novidades',n?String(n):'0',n===1?'novidade para você':'novidades para você')+'</div>'+
 '<h2 class="dv-group-title">OUTRAS FUNÇÕES</h2><div class="dv-group">'+
  small('profile','clipboard','green','Meu cadastro','Perguntas sobre seu trabalho e seu carro. Cada resposta dá pontos.'+(pct===null?'':' Está '+pct+'% pronto.'))+
  small('plan','pie','gold','Dividir meu dinheiro','Planeje quanto do que você ganha vai para combustível, carro e reserva.')+
  small('agent','spark','blue','Foto e áudio','Em vez de digitar, mande a foto do cupom ou um áudio. Você confere antes de salvar.')+
  small('documents','file','green','Documentos','Envie sua CNH com segurança, para o Programa de Renovação de Frota.')+'</div>'+
 '<h2 class="dv-group-title">MINHA CONTA</h2><div class="dv-group">'+
  small('privacy','lock','green','Privacidade','Escolha se quer ofertas e se o gestor pode preencher seu cadastro.')+
  small('password','key','gold','Trocar senha','Crie uma senha nova para entrar no MOVI+.')+
  '<button type="button" class="dv-row dv-row-compact dv-row-danger dv-press" data-logout><span class="dv-row-ic dv-tone-red">'+v8i('logout')+'</span><span class="dv-row-txt"><b>Sair</b><small>Fecha sua conta neste aparelho.</small></span></button></div>'+
 '<div class="dv-foot-brand">'+v8Logo(true)+'<p class="dv-small">2026 · V8</p></div>';
}

/* ---------- Benefícios ---------- */
async function v8Benefits(seq){
 const d=await request('program/benefits');
 if(v8Stale(seq))return;
 const p=d.points,labels={pending:'Esperando o gestor',approved:'Aprovado',rejected:'Recusado'};
 document.getElementById('body').innerHTML=
 '<section class="dv-card"><div class="dv-points">'+v8i('star')+'<div><b>'+p.total+'</b> <span>pontos</span></div></div>'+
 '<p class="dv-p" style="margin-top:12px">Ganhe pontos assim:</p>'+
 '<div class="dv-meter"><div class="dv-meter-top"><span>Respondendo o cadastro</span><span>'+p.profile+' de 60</span></div><div class="dv-meter-track"><i style="width:'+Math.min(100,p.profile/60*100)+'%"></i></div></div>'+
 '<div class="dv-meter"><div class="dv-meter-top"><span>Anotando em dias diferentes</span><span>'+p.diary+' de 40</span></div><div class="dv-meter-track"><i style="width:'+Math.min(100,p.diary/40*100)+'%"></i></div></div>'+
 '<p class="dv-small" style="margin-top:12px">Pontos não são dinheiro. Servem para pedir os benefícios abaixo.</p>'+
 (p.profile<60?'<button type="button" class="dv-btn dv-btn-ghost dv-press" style="margin-top:14px" data-go="profile">'+v8i('clipboard')+'Ganhar pontos agora</button>':'')+'</section>'+
 '<h2 class="dv-h" style="margin-top:22px">O que você pode pedir</h2>'+
 (d.items.some(b=>b.active)?d.items.filter(b=>b.active).sort((a,b)=>a.points_required-b.points_required).map(b=>{const missing=Math.max(0,b.points_required-p.total),out=b.remaining<=0;
  return '<article class="dv-card dv-ben"><span class="dv-pill">'+v8i('star')+b.points_required+' pontos</span><h3>'+safe(b.title)+'</h3><p class="dv-p">'+safe(b.description)+'</p>'+
  '<div style="margin-top:14px">'+(out?'<button type="button" class="dv-btn dv-btn-ghost" disabled>Acabou</button>':missing?'<button type="button" class="dv-btn dv-btn-ghost" disabled>Faltam '+missing+' pontos</button>':
  '<button type="button" class="dv-btn dv-btn-gold dv-press" data-claim="'+b.id+'">Quero este</button>')+'</div></article>'}).join(''):
  '<div class="dv-empty">'+v8i('gift')+'<p>Ainda não tem benefício</p><p class="dv-small">Quando o MOVI+ colocar, aparece aqui.</p></div>')+
 '<h2 class="dv-h" style="margin-top:22px">Meus pedidos</h2><section class="dv-card">'+
 (d.claims.length?d.claims.map(x=>'<div class="dv-claim"><b>'+safe(x.title)+'</b><span class="dv-status dv-status-'+safe(x.status)+'">'+safe(labels[x.status]||x.status)+'</span></div>').join(''):'<p class="dv-p">Você ainda não pediu nada.</p>')+'</section>';
 document.getElementById('body').onclick=async e=>{
  const b=e.target.closest('[data-claim]');if(!b)return;
  const item=d.items.find(x=>String(x.id)===b.dataset.claim);
  if(!await v8Ask('Pedir "'+item.title+'"?','O gestor do MOVI+ vai olhar seu pedido e responder aqui.','Sim, quero pedir'))return;
  try{await request('program/benefits/'+item.id+'/claim',{});v8Toast('Pedido enviado!');render()}catch(err){v8Toast(err.message)}
 };
}

/* ---------- Novidades ---------- */
async function v8News(seq){
 const [feed,old,cons]=await Promise.all([request('program/campaigns'),request('campaigns'),request('consents')]);
 if(v8Stale(seq))return;
 const all=[...feed.items,...old.items];
 const card=x=>'<article class="dv-card"><h3 class="dv-h">'+safe(x.title)+'</h3><p class="dv-p">'+safe(x.body)+'</p>'+(typeof stage2Media==='function'?stage2Media(x).replace('s2-media','dv-media'):'')+'</article>';
 document.getElementById('body').innerHTML=
 (!cons.choices.marketing?'<section class="dv-card" style="border-color:#7a5a1f"><h2 class="dv-h">Quer ver ofertas do MOVI+?</h2><p class="dv-p">Para mostrar ofertas e novidades aqui, precisamos da sua permissão. Você pode desligar depois em Privacidade.</p>'+
  '<button type="button" class="dv-btn dv-btn-gold dv-press" style="margin-top:14px" data-optin>Quero ver as ofertas</button></section>':'')+
 (all.length?all.map(card).join(''):cons.choices.marketing?'<div class="dv-empty">'+v8i('news')+'<p>Nenhuma novidade agora</p><p class="dv-small">Quando tiver, aparece aqui.</p></div>':'');
 const b=document.querySelector('[data-optin]');
 if(b)b.onclick=async()=>{
  v8Busy(b,true,'Salvando...');
  try{await request('consents',{...v8ConsentPayload(cons.choices),marketing:true},'PUT');v8Toast('Pronto! Agora você vê as ofertas.');render()}
  catch(err){v8Busy(b,false);v8Toast(err.message)}
 };
}
const V8_CONSENTS=[
 ['insights','Gestor pode ver meus números','Deixo o gestor do MOVI+ analisar meu cadastro e o que eu anoto.'],
 ['marketing','Ver ofertas e novidades','Quero ver ofertas e avisos do MOVI+ aqui no aplicativo.'],
 ['sharing','Compartilhar com parceiros','Deixo o MOVI+ passar meus dados a parceiros, só para um motivo combinado.'],
 ['documents','Gestor pode ver meus documentos','Quando o envio estiver liberado, o gestor pode olhar os documentos que eu mandar.'],
 ['assisted_entry','Gestor pode preencher meu cadastro','O gestor pode preencher e corrigir minhas respostas por mim.'],
 ['identity_collection','Guardar meus dados pessoais','Nome, CPF, RG, nascimento, contato, endereço, placa e CNH, guardados com proteção, para o Programa de Renovação de Frota.']
];
function v8ConsentPayload(c){const out={};V8_CONSENTS.forEach(([k])=>out[k]=!!c[k]);return out}

/* ---------- Termos de uso e privacidade ---------- */
/* O texto vem do servidor (legal_v8.py), que também registra cada aceite com versão e data. */
let v8LegalDoc=null,v8LegalChecked=null;
async function v8Legal(){if(!v8LegalDoc)v8LegalDoc=await request('legal');return v8LegalDoc}
/* Leitor dos documentos, por cima de qualquer tela (inclusive antes do login). */
async function v8LegalReader(start){
 let doc;try{doc=await v8Legal()}catch(err){v8Toast(err.message);return}
 const s=v8Sheet('<div class="dv-sheet-head"><h2>Termos e privacidade</h2><button type="button" class="dv-x dv-press" data-close aria-label="Fechar">'+v8i('x')+'</button></div>'+
  '<div class="dv-chips dv-chips-row" role="tablist" aria-label="Documentos">'+doc.sections.map(x=>'<button type="button" class="dv-chip dv-press" role="tab" data-doc-tab="'+x.id+'" aria-pressed="false">'+safe(x.title)+'</button>').join('')+'</div>'+
  '<div class="dv-legal-text" id="dvLegalText" tabindex="0"></div>'+
  '<p class="dv-small" style="margin-top:12px">Versão '+safe(doc.version)+'. Também dá para ler em <a href="/termos" target="_blank" rel="noopener" style="color:var(--gold)">'+safe(location.host)+'/termos</a>.</p>',{full:true,label:'Termos e privacidade'});
 const show=id=>{
  const sec=doc.sections.find(x=>x.id===id)||doc.sections[0];
  s.el.querySelectorAll('[data-doc-tab]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.docTab===sec.id)));
  const box=s.el.querySelector('#dvLegalText');
  box.innerHTML='<h3>'+safe(sec.title)+'</h3>'+sec.parts.map(p=>'<h4>'+safe(p.title)+'</h4><p>'+safe(p.text)+'</p>').join('');
  box.scrollTop=0;
 };
 s.el.querySelector('[role=tablist]').onclick=e=>{const b=e.target.closest('[data-doc-tab]');if(b)show(b.dataset.docTab)};
 show(start||'termos');
}
/* Popup de aceite. Obrigatórios: todos desmarcados até a pessoa marcar um por um.
   Opcionais: separados, começam como a pessoa já tinha escolhido (ou desligados). */
async function v8Terms({mode,current}){
 const doc=await v8Legal(),must=doc.must_answer||[],defaults=doc.default_on||[];
 return new Promise(resolve=>{
  let done=false;
  // Ofertas começam ligadas na conta nova; na reaceitação, vale o que a pessoa já tinha escolhido.
  // Perguntas obrigatórias (gestor) sempre começam sem resposta: consentimento não vem pré-marcado.
  const req={},opt={};
  doc.optional.forEach(o=>opt[o.id]=must.includes(o.id)?null:current?!!current[o.id]:defaults.includes(o.id));
  const asks=doc.optional.filter(o=>must.includes(o.id)),toggles=doc.optional.filter(o=>!must.includes(o.id));
  const s=v8Sheet('<div class="dv-sheet-head"><h2>'+(mode==='enroll'?'Antes de criar sua conta':'Antes de entrar')+'</h2></div>'+
   '<p class="dv-p">'+(mode==='enroll'?'Leia e marque os itens abaixo para criar sua conta no MOVI+.':'Os termos do MOVI+ foram atualizados. Leia e marque os itens para continuar.')+'</p>'+
   '<div class="dv-doc-links">'+doc.sections.map(x=>'<button type="button" class="dv-btn dv-btn-ghost dv-press" data-read="'+x.id+'">'+v8i('file')+safe(x.title)+'</button>').join('')+'</div>'+
   '<h3 class="dv-group-title">OBRIGATÓRIO PARA USAR O MOVI+</h3><div class="dv-group" role="group" aria-label="Itens obrigatórios">'+
   doc.required.map(r=>'<button type="button" class="dv-checkrow dv-press" role="checkbox" aria-checked="false" data-req="'+r.id+'"><span class="dv-box" aria-hidden="true">'+v8i('check')+'</span><span>'+safe(r.text)+'</span></button>').join('')+'</div>'+
   asks.map(o=>'<h3 class="dv-group-title">RESPONDA</h3><div class="dv-card" style="display:grid;gap:12px"><p class="dv-q" style="margin:0;font-size:21px">'+safe(o.text)+'</p>'+
    '<div class="dv-options" role="radiogroup" aria-label="'+safe(o.text)+'"><button type="button" class="dv-option dv-press" role="radio" aria-checked="false" aria-pressed="false" data-ask="'+o.id+'" data-val="1"><span class="dv-dot">'+v8i('check')+'</span>Sim, pode</button>'+
    '<button type="button" class="dv-option dv-press" role="radio" aria-checked="false" aria-pressed="false" data-ask="'+o.id+'" data-val="0"><span class="dv-dot">'+v8i('check')+'</span>Não</button></div></div>').join('')+
   '<h3 class="dv-group-title">OPCIONAL: VOCÊ ESCOLHE</h3><p class="dv-small" style="margin:-2px 6px 10px">Sem estes, você usa o MOVI+ do mesmo jeito. Dá para mudar depois em Mais › Privacidade.</p>'+
   '<div class="dv-group" role="group" aria-label="Escolhas opcionais">'+toggles.map(o=>
    '<button type="button" class="dv-switchrow" role="switch" aria-checked="'+opt[o.id]+'" data-optin="'+o.id+'"><span class="dv-row-txt"><small style="color:var(--text);font-size:17px;font-weight:700">'+safe(o.text)+'</small></span><span class="dv-switch-wrap"><span class="dv-switch" aria-hidden="true"></span><span class="dv-switch-word">'+(opt[o.id]?'LIGADO':'DESLIGADO')+'</span></span></button>').join('')+'</div>'+
   '<div class="dv-terms-foot"><p class="dv-small" id="dvReqLeft" role="status" aria-live="polite"></p>'+
   '<button type="button" class="dv-btn dv-btn-gold dv-press" id="dvTermsOk" disabled>Aceitar e continuar</button>'+
   '<button type="button" class="dv-btn dv-btn-quiet" id="dvTermsNo">Não aceito</button></div>',
   {full:true,locked:true,label:'Termos de uso',onClose:()=>{if(!done)resolve(null)}});
  const el=s.el,ok=el.querySelector('#dvTermsOk');
  const sync=()=>{
   const left=doc.required.filter(r=>!req[r.id]).length,open=asks.filter(o=>opt[o.id]===null).length;
   ok.disabled=left>0||open>0;
   el.querySelector('#dvReqLeft').textContent=left?'Falta marcar '+left+' ite'+(left>1?'ns':'m')+' obrigatório'+(left>1?'s':'')+'.':open?'Falta responder se o gestor pode preencher seu cadastro.':'Tudo certo. Pode continuar.';
  };
  const setOpt=(k,v)=>{
   opt[k]=v;
   const sw=el.querySelector('[data-optin="'+k+'"]');
   if(sw){sw.setAttribute('aria-checked',String(v));sw.querySelector('.dv-switch-word').textContent=v?'LIGADO':'DESLIGADO'}
   el.querySelectorAll('[data-ask="'+k+'"]').forEach(b=>{const on=v!==null&&b.dataset.val===(v?'1':'0');b.setAttribute('aria-pressed',String(on));b.setAttribute('aria-checked',String(on))});
  };
  el.onclick=e=>{
   const r=e.target.closest('[data-req]'),o=e.target.closest('[data-optin]'),a=e.target.closest('[data-ask]'),d=e.target.closest('[data-read]');
   if(d){v8LegalReader(d.dataset.read);return}
   if(r){req[r.dataset.req]=!req[r.dataset.req];r.setAttribute('aria-checked',String(req[r.dataset.req]))}
   if(a){
    const k=a.dataset.ask,v=a.dataset.val==='1';setOpt(k,v);
    // O gestor só consegue preencher se também puder ver o cadastro (regra do servidor).
    if(k==='assisted_entry'&&v&&!opt.insights){setOpt('insights',true);v8Toast('Ligamos também "gestor ver meu cadastro": ele precisa ver para preencher.')}
   }
   if(o){
    const k=o.dataset.optin;setOpt(k,!opt[k]);
    if(k==='insights'&&!opt[k]&&opt.assisted_entry){setOpt('assisted_entry',false);v8Toast('Sem ver o cadastro, o gestor também não consegue preencher. Mudamos a resposta para Não.')}
   }
   sync();
  };
  ok.onclick=()=>{done=true;resolve({version:doc.version,required:Object.fromEntries(doc.required.map(r=>[r.id,true])),optional:{...opt}});s.close()};
  el.querySelector('#dvTermsNo').onclick=()=>{done=true;resolve(null);s.close()};
  sync();
 });
}
/* Depois do login: quem ainda não aceitou a versão atual precisa aceitar antes de usar. */
async function v8TermsGate(){
 const st=await request('legal/status');
 if(!st.needs)return true;
 const answer=await v8Terms({mode:'login',current:st.choices});
 if(!answer){
  try{await request('logout',{})}catch{}
  user=null;tab='home';login();
  v8Toast('Para usar o MOVI+ é preciso aceitar os termos.');
  return false;
 }
 await request('legal/accept',answer);
 v8Toast('Termos aceitos. Bem-vindo!');
 return true;
}

/* ---------- Privacidade ---------- */
/* Em destaque, as duas escolhas do dia a dia. As demais, dadas no cadastro, ficam num bloco
   menor só para poder desligar ou ligar de novo (o direito de revogar não pode sumir). */
const V8_PRIV_MAIN=[
 ['marketing','Receber propostas e ofertas novas','Ofertas e novidades do MOVI+ aparecem para você no aplicativo.'],
 ['assisted_entry','Gestor pode preencher meu cadastro','O gestor preenche e corrige suas respostas por você.']
];
const V8_PRIV_MORE=[
 ['insights','Gestor pode ver meu cadastro e meus totais','O gestor vê suas respostas e quanto você ganhou e gastou.'],
 ['sharing','Compartilhar com parceiros','Seus dados de cadastro vão para os parceiros listados na Política de Privacidade.'],
 ['identity_collection','Guardar meus dados pessoais','CPF, RG, CNH e endereço, guardados com proteção, para o Programa de Renovação de Frota.'],
 ['documents','Gestor pode ver meus documentos','O gestor pode abrir os documentos que você enviar.']
];
function v8SwitchRow(k,t,s,on){return '<button type="button" class="dv-switchrow" role="switch" aria-checked="'+on+'" data-switch="'+k+'"><span class="dv-row-txt"><b>'+safe(t)+'</b><small>'+safe(s)+'</small></span><span class="dv-switch-wrap"><span class="dv-switch" aria-hidden="true"></span><span class="dv-switch-word">'+(on?'LIGADO':'DESLIGADO')+'</span></span></button>'}
async function v8Privacy(seq){
 const [d,hist,doc]=await Promise.all([request('consents'),request('legal/history').catch(()=>({items:[]})),v8Legal().catch(()=>null)]);
 if(v8Stale(seq))return;
 const state=v8ConsentPayload(d.choices),last=hist.items[hist.items.length-1];
 // Itens obrigatórios: só informamos que foram aceitos; não há como desligá-los (sem eles não há conta).
 const when=last?new Date(last.accepted_at).toLocaleDateString('pt-BR'):'',created=hist.items.length&&hist.items[0].origin==='cadastro';
 const accepted=doc&&last?'<h2 class="dv-group-title">ACEITO NOS TERMOS DE USO</h2><div class="dv-group dv-accepted">'+
  '<p class="dv-small" style="padding:14px 16px 4px;margin:0">'+(created&&hist.items.length===1?'Você aceitou estes itens quando criou sua conta, em ':'Você aceitou estes itens nos Termos de Uso, em ')+safe(when)+'. Eles são necessários para usar o MOVI+.</p>'+
  doc.required.map(r=>'<div class="dv-accepted-row">'+v8i('check')+'<span>'+safe(r.text)+'</span></div>').join('')+'</div>':'';
 const moreOn=V8_PRIV_MORE.filter(([k])=>state[k]).length;
 document.getElementById('body').innerHTML='<p class="dv-p">Você escolhe o que o MOVI+ pode fazer com seus dados. Cada mudança é salva na hora.</p>'+
 '<div class="dv-group" role="group" aria-label="Suas escolhas">'+V8_PRIV_MAIN.map(([k,t,s])=>v8SwitchRow(k,t,s,state[k])).join('')+'</div>'+accepted+
 '<details class="dv-more"'+(moreOn?'':'')+'><summary class="dv-press"><span>Outras permissões do cadastro</span><small>'+moreOn+' ligada'+(moreOn===1?'':'s')+' · tocar para ver</small></summary>'+
 '<p class="dv-small" style="margin:10px 6px">Você escolheu estas ao aceitar os termos. Pode desligar quando quiser, de graça.</p>'+
 '<div class="dv-group" role="group" aria-label="Outras permissões">'+V8_PRIV_MORE.map(([k,t,s])=>v8SwitchRow(k,t,s,state[k])).join('')+'</div></details>'+
 '<h2 class="dv-group-title">TERMOS E MEUS DADOS</h2><div class="dv-group">'+
 '<button type="button" class="dv-row dv-press" id="dvReadTerms"><span class="dv-row-ic dv-tone-gold">'+v8i('file')+'</span><span class="dv-row-txt"><b>Termos e privacidade</b><small>'+(last?'Você aceitou a versão '+safe(last.version)+' em '+safe(new Date(last.accepted_at).toLocaleDateString('pt-BR')):'Ler os documentos')+'</small></span>'+v8i('chev','dv-chev')+'</button>'+
 '<button type="button" class="dv-row dv-press" id="dvExport"><span class="dv-row-ic dv-tone-blue">'+v8i('down')+'</span><span class="dv-row-txt"><b>Baixar meus dados</b><small>Um arquivo com tudo que você informou</small></span></button>'+
 '<button type="button" class="dv-row dv-row-danger dv-press" id="dvErase"><span class="dv-row-ic dv-tone-red">'+v8i('trash')+'</span><span class="dv-row-txt"><b>Pedir para apagar meus dados</b><small>O gestor recebe o pedido</small></span></button></div>';
 const body=document.getElementById('body');
 const ask={identity_collection:['Guardar seus dados pessoais?','Seu CPF, RG, CNH e endereço ficam guardados com proteção neste sistema. Você pode desligar depois.','Sim, pode guardar'],
  sharing:['Compartilhar com parceiros?','Seus dados de cadastro vão para os parceiros listados na Política de Privacidade. Você pode desligar depois.','Sim, pode compartilhar']};
 const paint=()=>body.querySelectorAll('[data-switch]').forEach(b=>{const on=state[b.dataset.switch];b.setAttribute('aria-checked',String(on));b.querySelector('.dv-switch-word').textContent=on?'LIGADO':'DESLIGADO'});
 let busy=false;
 body.onclick=async e=>{
  const sw=e.target.closest('[data-switch]');if(!sw||busy)return;
  const k=sw.dataset.switch,next={...state,[k]:!state[k]};
  if(next[k]&&ask[k]&&!await v8Ask(...ask[k]))return;
  // Preencher depende de ver o cadastro; avisamos e ligamos/desligamos juntos, nunca escondido.
  if(k==='assisted_entry'&&next[k]&&!next.insights){
   if(!await v8Ask('O gestor precisa ver seu cadastro','Para preencher por você, o gestor também precisa ver seu cadastro e seus totais. Ligar as duas permissões?','Sim, ligar as duas'))return;
   next.insights=true;
  }
  if(k==='insights'&&!next[k])next.assisted_entry=false;
  busy=true;
  try{
   await request('consents',next,'PUT');
   const changedId=state.identity_collection!==next.identity_collection;
   Object.assign(state,next);paint();
   if(changedId)fields=(await request('schema')).fields;
   v8Toast(next[k]?'Ligado e salvo':'Desligado e salvo');
  }catch(err){v8Toast(err.message)}
  finally{busy=false}
 };
 document.getElementById('dvReadTerms').onclick=()=>v8LegalReader('termos');
 document.getElementById('dvExport').onclick=async()=>{
  try{const x=await request('privacy/export'),blob=new Blob([JSON.stringify(x,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');
   a.href=url;a.download='meus_dados_movi.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1500);v8Toast('Arquivo baixado')}catch(err){v8Toast(err.message)}
 };
 document.getElementById('dvErase').onclick=async()=>{
  if(!await v8Ask('Pedir para apagar seus dados?','O gestor do MOVI+ vai receber seu pedido e apagar seu cadastro.','Sim, pedir',{danger:true}))return;
  try{await request('privacy/delete-request',{});v8Toast('Pedido enviado ao gestor')}catch(err){v8Toast(err.message)}
 };
}

/* ---------- Trocar senha ---------- */
function v8PassField(name,label,auto){
 return '<div class="dv-field"><label for="dv-'+name+'">'+label+'</label><div class="dv-pass"><input class="dv-input" id="dv-'+name+'" name="'+name+'" type="password" autocomplete="'+auto+'" required>'+
  '<button type="button" class="dv-eye dv-press" data-eye="dv-'+name+'" aria-label="Mostrar senha">'+v8i('eye')+'Ver</button></div></div>';
}
function v8BindEyes(root){
 root.querySelectorAll('[data-eye]').forEach(b=>b.onclick=()=>{const i=document.getElementById(b.dataset.eye),show=i.type==='password';i.type=show?'text':'password';b.lastChild.textContent=show?'Esconder':'Ver';b.setAttribute('aria-label',show?'Esconder senha':'Mostrar senha')});
}
function v8Rules(){const mark='<span class="dv-rule-mark" aria-hidden="true">'+v8i('check')+'</span>';return '<ul class="dv-rules" id="dvRules" aria-live="polite"><li data-rule="len">'+mark+'<span>14 letras ou números, no mínimo</span></li><li data-rule="let">'+mark+'<span>Pelo menos uma letra</span></li><li data-rule="num">'+mark+'<span>Pelo menos um número</span></li></ul>'}
function v8WatchRules(input){
 const upd=()=>{const v=input.value,ok={len:v.length>=14,let:/[A-Za-z]/.test(v),num:/\d/.test(v)};
  Object.entries(ok).forEach(([k,on])=>document.querySelector('[data-rule="'+k+'"]').classList.toggle('ok',on));
  document.querySelector('[data-rule="len"] span:last-child').textContent='14 letras ou números, no mínimo'+(v.length&&v.length<14?' (você digitou '+v.length+')':'');
  return ok.len&&ok.let&&ok.num};
 input.addEventListener('input',upd);return upd;
}
async function v8Password(){
 document.getElementById('body').innerHTML=(user.must_change?'<div class="dv-card" style="border-color:#7a5a1f"><p class="dv-p" style="color:var(--text)"><b>Primeiro acesso:</b> crie uma senha só sua para continuar.</p></div>':'')+
 '<form id="dvPwd" class="dv-card" style="display:grid;gap:18px">'+v8PassField('current','Senha de agora','current-password')+v8PassField('new','Senha nova','new-password')+v8Rules()+
 '<p class="dv-err" id="dvPwdErr" role="alert"></p><button type="submit" class="dv-btn dv-btn-gold dv-press">Trocar senha</button></form>';
 const f=document.getElementById('dvPwd');v8BindEyes(f);
 const valid=v8WatchRules(f.elements.new);
 f.onsubmit=async e=>{
  e.preventDefault();const err=document.getElementById('dvPwdErr'),b=f.querySelector('[type=submit]');err.textContent='';
  if(!valid()){err.textContent='A senha nova ainda não cumpre as regras acima.';return}
  v8Busy(b,true,'Trocando...');
  try{await request('password',{current:f.elements.current.value,new:f.elements.new.value});user.must_change=0;v8Toast('Senha trocada!');tab='home';render()}
  catch(x){v8Busy(b,false);err.textContent=/atual|incorret/i.test(x.message)?'A senha de agora está errada.':x.message}
 };
}

/* ---------- Meu cadastro: uma pergunta por vez ---------- */
/* As perguntas originais do Programa são preservadas no servidor; aqui só a forma de perguntar muda. */
const V8_Q={
 gross_income:['Quanto entra por mês, antes de tirar os gastos?','Some tudo o que você recebe no mês. Exemplo: 4000'],
 other_job:['Você tem outro trabalho além de dirigir?',''],
 platform:['Em qual aplicativo você mais roda?',''],
 since:['Há quanto tempo você é motorista de aplicativo?','Exemplo: 2 anos'],
 team:['Você faz parte de alguma equipe? Qual?','Se não fizer, toque em Pular'],
 banks:['Em quais destes bancos você tem conta?',''],
 main_bank:['Qual banco você mais usa?',''],
 bid_resources:['Para dar entrada num carro novo, você tem o quê?',''],
 bid_cash:['Quanto dinheiro você tem para a entrada?','Exemplo: 5000'],
 vehicle_finance:['Seu carro está financiado? Quanto é a parcela e quanto falta pagar?','Exemplo: parcela de 900, faltam 20 mil'],
 cpf_bank_restriction:['Seu nome está sujo em algum banco?',''],
 cpf_store_restriction:['Seu nome está sujo em alguma loja?','Por exemplo: Gazin, Havan, Riachuelo'],
 move_brasil:['Você já se cadastrou no programa Move Brasil?',''],
 car_model_interest:['Qual carro você gostaria de ter?',''],
 weekly_hours:['Quantas horas você dirige por semana?','Exemplo: 50'],
 weekly_days:['Quantos dias por semana você trabalha?','De 1 a 7'],
 daily_km:['Quantos quilômetros você roda por dia?','Exemplo: 200'],
 daily_revenue:['Quanto você ganha num dia normal?','Exemplo: 250'],
 daily_fuel:['Quanto gasta de combustível por dia?','Exemplo: 80'],
 monthly_maintenance:['Quanto separa por mês para cuidar do carro?','Óleo, pneu, oficina. Exemplo: 300'],
 vehicle_type:['O carro que você dirige é...',''],
 vehicle_installment:['Quanto é a parcela do carro por mês?','Se não tem parcela, toque em Pular'],
 vehicle_outstanding:['Quanto ainda falta pagar do carro?','Mais ou menos. Exemplo: 25000'],
 household_expenses:['Quanto a sua casa gasta por mês?','Aluguel, luz, água, mercado...'],
 other_debts:['Quanto você paga por mês de outras dívidas?','Cartão, empréstimo, crediário...'],
 monthly_saving_goal:['Quanto você quer guardar por mês?','Exemplo: 300'],
 monthly_income_goal:['Quanto você quer ganhar por mês?','Exemplo: 5000'],
 car_change_horizon:['Quando você pensa em trocar de carro?',''],
 uses_other_apps:['Você roda em mais de um aplicativo?',''],
 full_name:['Qual é o seu nome completo?',''],cpf:['Qual é o seu CPF?','Só os números'],rg:['Qual é o seu RG?',''],
 birth_date:['Qual é a sua data de nascimento?',''],email:['Qual é o seu e-mail?','Se não tiver, toque em Pular'],
 address_cep:['Qual é o seu endereço com CEP?','Rua, número, bairro, cidade e CEP'],whatsapp:['Qual é o seu número de WhatsApp?','Com DDD'],
 vehicle_plate:['Qual é a placa do carro da entrada?','']
};
const V8_OPT={
 other_job:{'Não':'Não, só dirijo','CLT':'Sim, com carteira assinada','Autônomo':'Sim, por conta própria','Outro':'Sim, outro tipo'},
 platform:{'UBER':'Uber','99':'99','IN DRIVE':'inDrive','URBANO NORTE':'Urbano Norte','LEVA EU':'Leva Eu'},
 banks:{'CAIXA ECONOMICA FEDERAL':'Caixa','BANCO DO BRASIL':'Banco do Brasil','SICOOB':'Sicoob'},
 main_bank:{'BRADESCO':'Bradesco','SANTANDER':'Santander','NU':'Nubank'},
 bid_resources:{'não tenho':'Não tenho nada','dinheiro':'Dinheiro','carro/moto':'Meu carro ou moto'},
 cpf_bank_restriction:{'NAO':'Não','SIM':'Sim'},cpf_store_restriction:{'Não':'Não','SIM':'Sim'},
 move_brasil:{'AINDA NÃO ME CADASTREI':'Ainda não me cadastrei','AGUARDANDO RESPOSTA':'Me cadastrei, esperando resposta','APROVADO':'Sim, fui aprovado','RECUSADO':'Sim, mas fui recusado'},
 car_model_interest:{'BYD - DOLPHIN MINI GL':'BYD Dolphin Mini GL','BYD - DOLPHIN GS':'BYD Dolphin GS','GEELY EX2':'Geely EX2'}
};
/* Mostra primeiro as opções do mapa (na ordem mais comum) e depois as demais. */
function v8Options(q){
 const map=V8_OPT[q.key]||{},known=Object.keys(map).filter(o=>q.options.includes(o));
 return [...known,...q.options.filter(o=>!known.includes(o))].map(o=>[o,map[o]||v8Pretty(o)]);
}
/* ---------- Formatos de resposta: máscara enquanto digita e conferência antes de salvar ---------- */
/* Cada pergunta do cadastro tem um formato. O servidor continua validando; aqui o motorista
   só consegue digitar o que faz sentido e recebe o aviso antes de enviar. */
const V8_FMT={
 gross_income:{f:'money'},bid_cash:{f:'money'},daily_revenue:{f:'money'},daily_fuel:{f:'money'},
 monthly_maintenance:{f:'money'},vehicle_installment:{f:'money'},vehicle_outstanding:{f:'money'},
 household_expenses:{f:'money'},other_debts:{f:'money'},monthly_saving_goal:{f:'money'},monthly_income_goal:{f:'money'},
 weekly_hours:{f:'int',min:1,max:168,unit:'horas'},weekly_days:{f:'int',min:1,max:7,unit:'dias'},daily_km:{f:'int',min:1,max:2000,unit:'km'},
 since:{f:'duration'},team:{f:'text',max:60},
 full_name:{f:'name'},cpf:{f:'cpf'},rg:{f:'rg'},birth_date:{f:'birth'},email:{f:'email'},
 address_cep:{f:'address'},whatsapp:{f:'phone'},vehicle_plate:{f:'plate'},vehicle_finance:{f:'finance'}
};
const V8_DDD=new Set([11,12,13,14,15,16,17,18,19,21,22,24,27,28,31,32,33,34,35,37,38,41,42,43,44,45,46,47,48,49,51,53,54,55,61,62,63,64,65,66,67,68,69,71,73,74,75,77,79,81,82,83,84,85,86,87,88,89,91,92,93,94,95,96,97,98,99]);
const V8_UF=['AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG','PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO'];
const v8Digits=v=>String(v||'').replace(/\D/g,'');
const v8Thousands=d=>d.replace(/^0+(?=\d)/,'').replace(/\B(?=(\d{3})+(?!\d))/g,'.');
function v8CpfOk(d){
 if(!/^\d{11}$/.test(d)||/^(\d)\1{10}$/.test(d))return false;
 for(const n of [9,10]){let s=0;for(let i=0;i<n;i++)s+=Number(d[i])*(n+1-i);if(s*10%11%10!==Number(d[n]))return false}
 return true;
}
/* Máscaras: recebem o texto digitado e devolvem o texto permitido, já formatado. */
const V8_MASK={
 money:v=>v8Thousands(v8Digits(v).slice(0,9)),
 int:v=>v8Digits(v).replace(/^0+(?=\d)/,'').slice(0,4),
 cpf:v=>{const d=v8Digits(v).slice(0,11);return d.replace(/^(\d{3})(\d)/,'$1.$2').replace(/^(\d{3}\.\d{3})(\d)/,'$1.$2').replace(/^(\d{3}\.\d{3}\.\d{3})(\d)/,'$1-$2')},
 rg:v=>{const s=String(v||'').toUpperCase().replace(/[^0-9X]/g,'');const d=s.replace(/X/g,'');return (d+(/X$/.test(s)&&d.length>=5?'X':'')).slice(0,14)},
 phone:v=>{const d=v8Digits(v).slice(0,11);if(d.length<=2)return d.length?'('+d:'';const mid=d.length>10?7:6;return '('+d.slice(0,2)+') '+d.slice(2,mid)+(d.length>mid?'-'+d.slice(mid):'')},
 cep:v=>{const d=v8Digits(v).slice(0,8);return d.length>5?d.slice(0,5)+'-'+d.slice(5):d},
 plate:v=>{
  // ABC1234 (antiga) ou ABC1D23 (Mercosul): letras, número, letra ou número, números.
  let out='';for(const ch of String(v||'').toUpperCase().replace(/[^A-Z0-9]/g,'')){
   const i=out.length;if(i>=7)break;
   if(i<3?/[A-Z]/.test(ch):i===4?/[A-Z0-9]/.test(ch):/[0-9]/.test(ch))out+=ch;
  }
  return out.length>3&&/\d/.test(out[4]||'')&&out.length===7?out.slice(0,3)+'-'+out.slice(3):out;
 },
 name:v=>String(v||'').replace(/[^A-Za-zÀ-ÖØ-öø-ÿ' -]/g,'').replace(/\s{2,}/g,' ').replace(/^\s/,'').slice(0,80),
 email:v=>String(v||'').toLowerCase().replace(/\s/g,'').slice(0,120),
 text:v=>String(v||'').replace(/[<>]/g,'').slice(0,60),
 street:v=>String(v||'').replace(/[<>]/g,'').slice(0,80),
 number:v=>String(v||'').toUpperCase().replace(/[^0-9A-Z/ -]/g,'').slice(0,8),
 city:v=>V8_MASK.name(v).slice(0,40),
 username:v=>String(v||'').normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase().replace(/[^a-z0-9_]/g,'').slice(0,32),
 invite:v=>String(v||'').replace(/[^A-Za-z0-9_-]/g,'').slice(0,120)
};
/* Aplica a máscara mantendo o cursor no fim (campos curtos, digitação sequencial). */
function v8Mask(input,kind){
 // maxlength só vale para digitação; ao colar, a máscara também corta.
 const fix=()=>{let next=V8_MASK[kind](input.value);if(input.maxLength>0)next=next.slice(0,input.maxLength);if(next!==input.value)input.value=next};
 input.addEventListener('input',fix);fix();
}
function v8WireFormat(root){root.querySelectorAll('[data-mask]').forEach(i=>{if(!i.dataset.wired){i.dataset.wired='1';v8Mask(i,i.dataset.mask)}})}
/* Campo com partes fixas: "R$" antes e ",00" depois, ou a unidade (horas, dias, km). */
function v8Affix(id,{mask,pre,suf,value,inputmode,label,placeholder,max}){
 return '<div class="dv-affix'+(pre?' dv-affix-pre':'')+'">'+(pre?'<span class="dv-affix-a" aria-hidden="true">'+pre+'</span>':'')+
  '<input class="dv-input dv-input-big" id="'+id+'" data-mask="'+mask+'" inputmode="'+(inputmode||'numeric')+'" autocomplete="off" aria-label="'+safe(label||'Sua resposta')+'" placeholder="'+safe(placeholder||'0')+'" value="'+safe(value||'')+'"'+(max?' maxlength="'+max+'"':'')+'>'+
  (suf?'<span class="dv-affix-b" aria-hidden="true">'+suf+'</span>':'')+'</div>';
}
const v8MoneyField=(id,value,label)=>v8Affix(id,{mask:'money',pre:'R$',suf:',00',value:value?v8Thousands(String(Math.round(Number(value)))):'',label});
function v8Field(id,label,inner,hint){return '<div class="dv-field"><label for="'+id+'">'+label+'</label>'+inner+(hint?'<p class="dv-small">'+hint+'</p>':'')+'</div>'}

function v8QuestionInput(q,current){
 const cur=current==null?'':current,fmt=(V8_FMT[q.key]||{}).f,opt=V8_FMT[q.key]||{};
 if(q.type==='select')return '<div class="dv-options" role="group" aria-label="Opções">'+v8Options(q).map(([o,l])=>'<button type="button" class="dv-option dv-press" data-opt="'+safe(o)+'" aria-pressed="'+(cur===o)+'"><span class="dv-dot">'+v8i('check')+'</span>'+safe(l)+'</button>').join('')+'</div>';
 if(q.type==='multi')return '<p class="dv-small">Pode marcar mais de um.</p><div class="dv-options" role="group" aria-label="Opções">'+v8Options(q).map(([o,l])=>'<button type="button" class="dv-option dv-press" data-multi="'+safe(o)+'" aria-pressed="'+(Array.isArray(cur)&&cur.includes(o))+'"><span class="dv-dot">'+v8i('check')+'</span>'+safe(l)+'</button>').join('')+'</div>';
 const input=(mask,extra)=>'<input class="dv-input dv-input-big" id="dvAns" data-mask="'+mask+'" aria-label="Sua resposta" value="'+safe(V8_MASK[mask]?V8_MASK[mask](cur):cur)+'" '+extra+'>';
 switch(fmt){
  case 'money':return v8MoneyField('dvAns',cur);
  case 'int':return v8Affix('dvAns',{mask:'int',suf:opt.unit,value:cur===''?'':String(Math.round(Number(cur))),placeholder:String(opt.min),max:String(opt.max).length})+'<p class="dv-small">De '+opt.min+' a '+opt.max+' '+opt.unit+'.</p>';
  case 'cpf':return input('cpf','inputmode="numeric" autocomplete="off" placeholder="000.000.000-00"')+'<p class="dv-small" id="dvLive" aria-live="polite"></p>';
  case 'rg':return input('rg','inputmode="numeric" autocomplete="off" placeholder="Só números"')+'<p class="dv-small">Só os números. Se o seu RG termina com X, digite o X no fim.</p>';
  case 'phone':return input('phone','inputmode="numeric" autocomplete="tel-national" placeholder="(69) 99999-9999"')+'<p class="dv-small" id="dvLive" aria-live="polite"></p>';
  case 'plate':return input('plate','autocomplete="off" autocapitalize="characters" spellcheck="false" placeholder="ABC1D23"')+'<p class="dv-small">Placa nova (ABC1D23) ou antiga (ABC-1234).</p>';
  case 'name':return input('name','autocomplete="name" autocapitalize="words" spellcheck="false" placeholder="Nome e sobrenome"');
  case 'email':return input('email','type="email" inputmode="email" autocomplete="email" autocapitalize="none" spellcheck="false" placeholder="nome@exemplo.com"');
  case 'text':return input('text','autocomplete="off" maxlength="'+opt.max+'"');
  case 'birth':{const now=new Date(),max=new Date(now.getFullYear()-18,now.getMonth(),now.getDate()),min=new Date(now.getFullYear()-100,now.getMonth(),now.getDate());
   return '<input class="dv-input dv-input-big" id="dvAns" type="date" min="'+v8Day(min)+'" max="'+v8Day(max)+'" value="'+safe(/^\d{4}-\d{2}-\d{2}$/.test(cur)?cur:'')+'" aria-label="Data de nascimento"><p class="dv-small">Toque para abrir o calendário. É preciso ter 18 anos ou mais.</p>'}
  case 'duration':{const m=String(cur).match(/(\d+)\s*(ano|m[eê]s)/i),n=m?m[1]:'',unit=m&&/m[eê]s/i.test(m[2])?'meses':'anos';
   return v8Affix('dvAns',{mask:'int',value:n,placeholder:'0',max:2,label:'Quanto tempo'})+
    '<div class="dv-chips" role="group" aria-label="Meses ou anos"><button type="button" class="dv-chip dv-press" data-unit="meses" aria-pressed="'+(unit==='meses')+'">Meses</button><button type="button" class="dv-chip dv-press" data-unit="anos" aria-pressed="'+(unit==='anos')+'">Anos</button></div>'}
  case 'finance':{const yes=/^sim/i.test(cur),no=/^n[aã]o/i.test(cur),nums=String(cur).match(/R\$\s?[\d.]+/g)||[];
   const val=s=>s?v8Digits(s.replace(/,\d{2}$/,'')):'';
   return '<div class="dv-options" role="group" aria-label="Está financiado?"><button type="button" class="dv-option dv-press" data-fin="nao" aria-pressed="'+no+'"><span class="dv-dot">'+v8i('check')+'</span>Não, já está pago</button><button type="button" class="dv-option dv-press" data-fin="sim" aria-pressed="'+yes+'"><span class="dv-dot">'+v8i('check')+'</span>Sim, está financiado</button></div>'+
    '<div id="dvFinMore" style="display:grid;gap:14px"'+(yes?'':' hidden')+'>'+v8Field('dvFinPay','Quanto é a parcela por mês?',v8MoneyField('dvFinPay',val(nums[0])))+v8Field('dvFinLeft','Quanto ainda falta pagar?',v8MoneyField('dvFinLeft',val(nums[1])),'Mais ou menos.')+'</div>'}
  case 'address':return (cur?'<p class="dv-small">Endereço de agora: '+safe(cur)+'</p>':'')+
   v8Field('dvCep','CEP','<input class="dv-input" id="dvCep" data-mask="cep" inputmode="numeric" autocomplete="postal-code" placeholder="00000-000">')+
   v8Field('dvStreet','Rua ou avenida','<input class="dv-input" id="dvStreet" data-mask="street" autocomplete="address-line1">')+
   '<div class="dv-2col">'+v8Field('dvNum','Número','<input class="dv-input" id="dvNum" data-mask="number" inputmode="numeric" autocomplete="off" placeholder="Ex.: 120">')+
   v8Field('dvUf','Estado','<select class="dv-input" id="dvUf" autocomplete="address-level1"><option value="">Escolha</option>'+V8_UF.map(u=>'<option>'+u+'</option>').join('')+'</select>')+'</div>'+
   '<label class="dv-check"><input type="checkbox" id="dvNoNum"><span>Minha casa não tem número</span></label>'+
   v8Field('dvHood','Bairro','<input class="dv-input" id="dvHood" data-mask="street" autocomplete="address-level3">')+
   v8Field('dvCity','Cidade','<input class="dv-input" id="dvCity" data-mask="city" autocomplete="address-level2">');
 }
 if(q.type==='textarea')return '<textarea class="dv-input" id="dvAns" maxlength="350" aria-label="Sua resposta">'+safe(cur)+'</textarea>';
 return input('text','autocomplete="off" maxlength="120"');
}
const v8Money=id=>{const el=document.getElementById(id);return el?Number(v8Digits(el.value)):0};
/* Lê e confere a resposta; devolve {value} ou {error} com uma frase simples. */
function v8ReadAnswer(root,q){
 if(q.type==='select'){const b=root.querySelector('[data-opt][aria-pressed="true"]');return b?{value:b.dataset.opt}:{error:'Toque em uma das opções.'}}
 if(q.type==='multi'){const v=[...root.querySelectorAll('[data-multi][aria-pressed="true"]')].map(b=>b.dataset.multi);return v.length?{value:v}:{error:'Marque pelo menos uma opção.'}}
 const opt=V8_FMT[q.key]||{},$a=root.querySelector('#dvAns'),raw=$a?$a.value.trim():'';
 switch(opt.f){
  case 'money':{if(!raw)return {error:'Digite o valor. Se for zero, digite 0.'};return {value:String(Number(v8Digits(raw)))}}
  case 'int':{const n=Number(raw);if(!raw)return {error:'Digite um número.'};if(n<opt.min||n>opt.max)return {error:'Digite um número de '+opt.min+' a '+opt.max+'.'};return {value:String(n)}}
  case 'cpf':{const d=v8Digits(raw);if(d.length<11)return {error:'O CPF tem 11 números. Faltam '+(11-d.length)+'.'};if(!v8CpfOk(d))return {error:'Esse CPF não existe. Confira os números no seu documento.'};return {value:d}}
  case 'rg':{const d=v8Digits(raw);if(d.length<5)return {error:'O RG tem pelo menos 5 números.'};return {value:raw}}
  case 'phone':{const d=v8Digits(raw);if(d.length<11)return {error:'Digite o DDD e os 9 números do celular.'};if(!V8_DDD.has(Number(d.slice(0,2))))return {error:'Esse DDD não existe. Confira os 2 primeiros números.'};if(d[2]!=='9')return {error:'Celular começa com 9 depois do DDD.'};return {value:d}}
  case 'plate':{const p=raw.replace('-','');if(!/^[A-Z]{3}\d[A-Z0-9]\d{2}$/.test(p))return {error:'A placa tem 3 letras e 4 números. Exemplo: ABC1D23.'};return {value:raw}}
  case 'name':{const parts=raw.trim().split(/\s+/).filter(x=>x.replace(/['-]/g,'').length>=2);if(parts.length<2)return {error:'Escreva o nome e o sobrenome.'};return {value:raw.trim()}}
  case 'email':{if(!/^[^@\s]+@[^@\s]+\.[a-z]{2,}$/.test(raw))return {error:'O e-mail precisa ter @ e um ponto. Exemplo: nome@gmail.com'};return {value:raw}}
  case 'text':{if(!raw)return {error:'Escreva sua resposta ou toque em Pular.'};return {value:raw}}
  case 'birth':{if(!raw)return {error:'Escolha a data no calendário.'};if(raw<$a.min||raw>$a.max)return {error:'A data precisa ser de alguém com 18 anos ou mais.'};return {value:raw}}
  case 'duration':{const n=Number(raw),u=root.querySelector('[data-unit][aria-pressed="true"]');if(!raw||n<1)return {error:'Digite quanto tempo. Exemplo: 2'};if(!u)return {error:'Toque em Meses ou Anos.'};
   const word=u.dataset.unit==='anos'?(n===1?'ano':'anos'):(n===1?'mês':'meses');if(u.dataset.unit==='anos'&&n>60)return {error:'Confira os anos: até 60.'};return {value:n+' '+word}}
  case 'finance':{const c=root.querySelector('[data-fin][aria-pressed="true"]');if(!c)return {error:'Toque em Sim ou Não.'};if(c.dataset.fin==='nao')return {value:'Não'};
   const pay=v8Money('dvFinPay'),left=v8Money('dvFinLeft');if(!pay||!left)return {error:'Digite a parcela e quanto falta pagar.'};
   return {value:'Sim. Parcela de '+brl(pay)+'. Faltam '+brl(left)+'.'}}
  case 'address':{const g=id=>(root.querySelector('#'+id)||{}).value||'',cep=v8Digits(g('dvCep')),noNum=root.querySelector('#dvNoNum').checked;
   if(cep.length!==8)return {error:'O CEP tem 8 números.'};
   if(g('dvStreet').trim().length<3)return {error:'Escreva o nome da rua.'};
   if(!noNum&&!g('dvNum').trim())return {error:'Digite o número da casa ou marque que não tem número.'};
   if(g('dvHood').trim().length<2)return {error:'Escreva o bairro.'};
   if(g('dvCity').trim().length<2)return {error:'Escreva a cidade.'};
   if(!g('dvUf'))return {error:'Escolha o estado.'};
   return {value:g('dvStreet').trim()+', '+(noNum?'s/n':g('dvNum').trim())+' - '+g('dvHood').trim()+', '+g('dvCity').trim()+'/'+g('dvUf')+' - CEP '+cep.slice(0,5)+'-'+cep.slice(5)}}
 }
 if(!raw)return {error:'Escreva sua resposta ou toque em Pular.'};
 return {value:raw};
}
function v8BindOptions(root,onPick){
 root.addEventListener('click',e=>{
  const o=e.target.closest('[data-opt]'),m=e.target.closest('[data-multi]'),u=e.target.closest('[data-unit]'),f=e.target.closest('[data-fin]');
  if(o){root.querySelectorAll('[data-opt]').forEach(b=>b.setAttribute('aria-pressed',String(b===o)));if(onPick)onPick(o.dataset.opt)}
  if(m)m.setAttribute('aria-pressed',String(m.getAttribute('aria-pressed')!=='true'));
  if(u)root.querySelectorAll('[data-unit]').forEach(b=>b.setAttribute('aria-pressed',String(b===u)));
  if(f){root.querySelectorAll('[data-fin]').forEach(b=>b.setAttribute('aria-pressed',String(b===f)));root.querySelector('#dvFinMore').hidden=f.dataset.fin!=='sim'}
 });
 v8WireFormat(root);
 // Retorno imediato de CPF e celular: diz se está certo antes de tocar em Responder.
 const live=root.querySelector('#dvLive'),ans=root.querySelector('#dvAns');
 if(live&&ans){
  const kind=ans.dataset.mask,check=()=>{
   const d=v8Digits(ans.value),full=kind==='cpf'?d.length===11:d.length===11;
   if(!full){live.textContent='';live.className='dv-small';return}
   const ok=kind==='cpf'?v8CpfOk(d):V8_DDD.has(Number(d.slice(0,2)))&&d[2]==='9';
   live.textContent=ok?(kind==='cpf'?'✓ CPF certo':'✓ Número certo'):(kind==='cpf'?'✗ Esse CPF não existe. Confira os números.':'✗ Confira o DDD e o número.');
   live.className='dv-small '+(ok?'dv-live-ok':'dv-live-bad');
  };
  ans.addEventListener('input',check);check();
 }
 const nn=root.querySelector('#dvNoNum');
 if(nn)nn.onchange=()=>{const n=root.querySelector('#dvNum');n.disabled=nn.checked;if(nn.checked)n.value=''};
}
async function v8Profile(seq){
 if(!fields.length)fields=(await request('schema')).fields;
 const d=await request('profile/next');
 if(v8Stale(seq))return;
 const q=d.question,pr=d.progress;
 const head='<section class="dv-card"><div class="dv-meter-top" style="font-size:19px"><span>Seu cadastro</span><b style="color:var(--text)">'+pr.percent+'% pronto</b></div><div class="dv-progress" style="margin-top:10px"><i style="width:'+pr.percent+'%"></i></div>'+
  '<p class="dv-small" style="margin-top:10px">Cada resposta dá pontos para os Benefícios.</p></section>';
 const body=document.getElementById('body');
 if(!q){
  body.innerHTML=head+'<div class="dv-empty">'+v8i('check')+'<p>Tudo respondido!</p><p class="dv-small">Obrigado. Se quiser, você pode ver ou mudar suas respostas.</p>'+
   '<button type="button" class="dv-btn dv-btn-gold dv-press" data-go="profile-all">Ver minhas respostas</button></div>';
  return;
 }
 const [label,hint]=V8_Q[q.key]||[q.label,''];
 body.innerHTML=head+'<section class="dv-card" id="dvQ" style="display:grid;gap:16px"><div><p class="dv-q" style="margin:0">'+safe(label)+'</p>'+(hint?'<p class="dv-small" style="margin-top:6px">'+safe(hint)+'</p>':'')+'</div>'+v8QuestionInput(q,'')+
  '<p class="dv-err" id="dvAnsErr" role="alert"></p>'+(q.type==='select'?'':'<button type="button" class="dv-btn dv-btn-gold dv-press" id="dvAnswer">Responder</button>')+
  '<button type="button" class="dv-btn dv-btn-quiet" id="dvSkip">Pular esta pergunta</button></section>'+
  '<button type="button" class="dv-btn dv-btn-ghost dv-press" data-go="profile-all">Ver todas as respostas</button>';
 const box=document.getElementById('dvQ'),err=document.getElementById('dvAnsErr');
 let sending=false;
 async function answer(value){
  if(sending)return;sending=true;err.textContent='';
  try{await request('profile/answer',{key:q.key,value});v8Toast('Resposta salva');render()}
  catch(x){err.textContent=x.message;sending=false}
 }
 // Escolha única salva no toque, sem botão extra.
 v8BindOptions(box,q.type==='select'?answer:null);
 const a=document.getElementById('dvAnswer');
 if(a)a.onclick=()=>{const r=v8ReadAnswer(box,q);if(r.error){err.textContent=r.error;return}answer(r.value)};
 const ans=document.getElementById('dvAns');
 if(ans&&ans.tagName==='INPUT'){ans.focus({preventScroll:true});ans.onkeydown=e=>{if(e.key==='Enter'&&a){e.preventDefault();a.click()}}}
 document.getElementById('dvSkip').onclick=async()=>{
  try{await request('profile/answer',{key:q.key,skip:true});render()}catch(x){err.textContent=x.message}
 };
}
/* Minhas respostas: lista simples, cada uma com "Mudar". */
const V8_GROUPS=[['Trabalho e renda',0],['Bancos e dinheiro',1],['Carro',2],['Metas e gastos da casa',3],['Dados pessoais',4]];
function v8AnswerText(q,v){
 if(v==null||v===''||(Array.isArray(v)&&!v.length))return '';
 const map=V8_OPT[q.key]||{};
 if(Array.isArray(v))return v.map(x=>map[x]||v8Pretty(x)).join(', ');
 if(q.type==='money')return brl(v);
 const fmt=(V8_FMT[q.key]||{}).f;
 if(fmt==='cpf'||fmt==='phone')return V8_MASK[fmt](v);
 if(fmt==='int')return v+' '+V8_FMT[q.key].unit;
 if(q.type==='date'){const [y,m,d]=String(v).split('-');return d?d+'/'+m+'/'+y:String(v)}
 return map[v]||(q.type==='select'?v8Pretty(v):String(v));
}
async function v8ProfileAll(seq){
 if(!fields.length)fields=(await request('schema')).fields;
 const p=await request('profile');
 if(v8Stale(seq))return;
 const answers=p.answers,open=f=>f.type!=='file'&&(!f.protected||p.identity_collection_enabled);
 const byKey=Object.fromEntries(fields.map(f=>[f.key,f]));
 const groups=V8_GROUPS.map(([title,i])=>[title,(SOCIO_STAGES[i]?SOCIO_STAGES[i].keys:[]).map(k=>byKey[k]).filter(f=>f&&open(f))]).filter(g=>g[1].length);
 const body=document.getElementById('body');
 body.innerHTML='<section class="dv-card"><div class="dv-meter-top" style="font-size:19px"><span>Seu cadastro</span><b style="color:var(--text)">'+p.progress.percent+'% pronto</b></div><div class="dv-progress" style="margin-top:10px"><i style="width:'+p.progress.percent+'%"></i></div></section>'+
  groups.map(([title,list])=>'<h2 class="dv-group-title">'+safe(title.toUpperCase())+'</h2><div class="dv-group">'+list.map(f=>{
   const t=v8AnswerText(f,answers[f.key]);
   return '<button type="button" class="dv-row dv-press" data-edit="'+safe(f.key)+'"><span class="dv-row-txt"><small>'+safe((V8_Q[f.key]||[f.label])[0])+'</small><b'+(t?'':' class="dv-missing"')+'>'+safe(t||'Sem resposta')+'</b></span><span class="dv-link" aria-hidden="true">'+(t?'Mudar':'Responder')+'</span></button>'}).join('')+'</div>').join('')+
  (p.identity_collection_enabled?'':'<p class="dv-small" style="margin-top:14px">Seus dados pessoais (CPF, RG, CNH) só aparecem aqui se você deixar em Privacidade.</p>');
 body.onclick=e=>{
  const b=e.target.closest('[data-edit]');if(!b)return;
  const q=byKey[b.dataset.edit],[label,hint]=V8_Q[q.key]||[q.label,''];
  const s=v8Sheet('<div class="dv-sheet-head"><h2>'+safe(label)+'</h2><button type="button" class="dv-x dv-press" data-close aria-label="Fechar">'+v8i('x')+'</button></div>'+
   (hint?'<p class="dv-small" style="margin:-4px 0 14px">'+safe(hint)+'</p>':'')+'<div style="display:grid;gap:14px">'+v8QuestionInput(q,answers[q.key])+
   '<p class="dv-err" role="alert"></p><button type="button" class="dv-btn dv-btn-gold dv-press" data-save>Salvar</button></div>',{label});
  v8BindOptions(s.el,null);
  const err=s.el.querySelector('.dv-err'),save=s.el.querySelector('[data-save]');
  save.onclick=async()=>{
   const r=v8ReadAnswer(s.el,q);if(r.error){err.textContent=r.error;return}
   v8Busy(save,true,'Salvando...');
   try{await request('profile',{[q.key]:r.value},'PUT');s.close();v8Toast('Resposta salva');render()}
   catch(x){v8Busy(save,false);err.textContent=x.message.replace(/^[^:]+: /,'')}
  };
 };
}

/* ---------- Dividir meu dinheiro: potes com − e + ---------- */
let v8PlanDraft=null;
async function v8Plan(seq){
 if(!v8PlanDraft){
  const month=v8Day().slice(0,7),[d,fin]=await Promise.all([request('distribution-plan'),request('finances?month='+month).catch(()=>null)]);
  if(v8Stale(seq))return;
  v8PlanDraft={total:d.total,saved:d.saved,income:fin?fin.summary.income:0,month,rows:d.rows.map(r=>({name:r.name,percentage:Number(r.percentage),reported_sent:Number(r.reported_sent)}))};
 }
 const p=v8PlanDraft,sum=Math.round(p.rows.reduce((a,r)=>a+r.percentage,0)*100)/100;
 const status=sum===100?'<span class="dv-in">'+v8i('check')+'Tudo dividido certinho</span>':sum<100?'<span class="dv-gold">Ainda falta dividir '+(100-sum).toLocaleString('pt-BR')+'%. Use o botão + em algum pote.</span>':'<span class="dv-out">Passou '+(sum-100).toLocaleString('pt-BR')+'%. Tire de algum pote com o botão −.</span>';
 document.getElementById('body').innerHTML=
 '<p class="dv-p">Escolha um valor e diga quanto vai para cada coisa. É só um plano: o aplicativo não mexe no seu dinheiro.</p>'+
 '<button type="button" class="dv-chosen dv-press" id="dvPlanTotal"><span>Valor para dividir<br><small>Tocar para mudar</small></span><b class="dv-money">'+brl(p.total)+'</b></button>'+
 (p.income>0&&p.income!==p.total?'<button type="button" class="dv-btn dv-btn-ghost dv-press" data-useincome>Usar o que ganhei em '+safe(v8MonthLabel(p.month).split(' ')[0].toLowerCase())+': '+brl(p.income)+'</button>':'')+
 '<div class="dv-list">'+p.rows.map((r,i)=>'<div class="dv-pot"><div class="dv-pot-txt"><b>'+safe(r.name)+'</b><span class="dv-money">'+brl(p.total*r.percentage/100)+'</span></div>'+
  '<div class="dv-stepper"><button type="button" class="dv-iconbtn dv-press" data-pct="'+i+'" data-step="-5" aria-label="Diminuir '+safe(r.name)+'" '+(r.percentage<=0?'disabled':'')+'>'+v8i('minus')+'</button>'+
  '<b aria-live="polite">'+r.percentage.toLocaleString('pt-BR')+'%</b><button type="button" class="dv-iconbtn dv-press" data-pct="'+i+'" data-step="5" aria-label="Aumentar '+safe(r.name)+'" '+(r.percentage>=100?'disabled':'')+'>'+v8i('plus')+'</button></div></div>').join('')+'</div>'+
 '<p class="dv-status-line" role="status">'+status+'</p>'+
 '<div class="dv-sticky"><button type="button" class="dv-btn dv-btn-gold dv-press" id="dvPlanSave" '+(sum===100?'':'disabled')+'>'+(sum===100?'Salvar minha divisão':'Ajuste até dar 100%')+'</button></div>';
 document.getElementById('body').onclick=e=>{
  if(e.target.closest('[data-useincome]')){p.total=p.income;render();return}
  const b=e.target.closest('[data-pct]');if(!b)return;
  const r=p.rows[Number(b.dataset.pct)];
  r.percentage=Math.max(0,Math.min(100,Math.round((r.percentage+Number(b.dataset.step))*100)/100));
  render();
 };
 document.getElementById('dvPlanTotal').onclick=()=>v8Keypad({title:'Quanto você quer dividir?',tone:'in',initial:p.total,done:'Usar este valor',onDone:async v=>{p.total=v;render()}});
 const save=document.getElementById('dvPlanSave');
 save.onclick=async()=>{
  v8Busy(save,true,'Salvando...');
  try{const d=await request('distribution-plan',{total:p.total,rows:p.rows},'PUT');v8PlanDraft=null;v8Toast('Divisão salva!');render()}
  catch(err){v8Busy(save,false);v8Toast(err.message)}
 };
}

/* ---------- Foto e áudio: uma permissão de cada vez, um botão grande por ação ---------- */
async function v8Agent(seq){
 const [c,release,link,pending]=await Promise.all([request('finance-agent/consent'),request('finance-agent/release'),
  request('finance-agent/whatsapp/link-status').catch(()=>({})),v8Pending()]);
 if(v8Stale(seq))return;
 const o={enabled:false,media_ai:false,trends:false,offers:false,text_ai:false,...c.options};
 const ready=release.available&&o.enabled&&o.media_ai,canRead=ready&&release.message_types&&release.message_types.image;
 const sw=(k,t,s,on,dis)=>'<button type="button" class="dv-switchrow" role="switch" aria-checked="'+on+'" data-agent="'+k+'" '+(dis?'disabled':'')+'><span class="dv-row-txt"><b>'+t+'</b><small>'+s+'</small></span><span class="dv-switch-wrap"><span class="dv-switch" aria-hidden="true"></span><span class="dv-switch-word">'+(on?'LIGADO':'DESLIGADO')+'</span></span></button>';
 document.getElementById('body').innerHTML=
 (!release.available?'<div class="dv-empty">'+v8i('spark')+'<p>O MOVI+ pausou esta função por enquanto.</p><p class="dv-small">Você pode continuar anotando pelo Início ou pelo Assistente.</p></div>':
 '<p class="dv-p">Mande a foto do cupom ou um áudio contando o gasto. O assistente lê e você confere antes de salvar.</p>'+
 '<h2 class="dv-group-title">1. LIGUE AS PERMISSÕES</h2><div class="dv-group">'+
  sw('enabled','Usar o assistente','Ele organiza o que você manda.',!!o.enabled,false)+
  sw('media_ai','Deixar ler fotos e áudios','As fotos e textos vão para o serviço de inteligência artificial DeepSeek, que pode guardar os dados fora do Brasil. O áudio vira texto no servidor do MOVI+.',!!o.media_ai,!o.enabled)+'</div>'+
 '<h2 class="dv-group-title">2. MANDE</h2>'+
 (canRead?'<div class="dv-actions"><label class="dv-act dv-act-file dv-press">'+v8i('camera')+'FOTO<input type="file" accept="image/png,image/jpeg,image/webp" capture="environment" data-media hidden></label>'+
  '<label class="dv-act dv-act-file dv-press">'+v8i('mic')+'ÁUDIO<input type="file" accept="audio/ogg,audio/mpeg,audio/wav,audio/mp4" data-media hidden></label></div>'+
  '<p class="dv-small">Não mande foto de cartão, senha ou documento.</p>':
  '<div class="dv-card"><p class="dv-p">'+(!ready?'Ligue as duas permissões acima para mandar foto ou áudio.':'O MOVI+ ainda está ligando a leitura de fotos e áudios. Enquanto isso, use o Assistente escrevendo.')+'</p></div>')+
 (pending.length?'<button type="button" class="dv-pending dv-press" data-pending>'+v8i('bell')+'<span>Conferir '+pending.length+' anotaç'+(pending.length>1?'ões':'ão')+'</span>'+v8i('chev','dv-chev')+'</button>':'')+
 (link.pilot_allowed?'<h2 class="dv-group-title">WHATSAPP</h2><div class="dv-group"><button type="button" class="dv-row dv-press" data-go="agent-whats"><span class="dv-row-ic dv-tone-green">'+v8i('chat')+'</span><span class="dv-row-txt"><b>Usar pelo WhatsApp</b><small>'+(link.linked?'Seu WhatsApp está ligado':'Ligar meu número')+'</small></span>'+v8i('chev','dv-chev')+'</button></div>':''));
 const body=document.getElementById('body');
 body.onclick=async e=>{
  const s=e.target.closest('[data-agent]');
  if(s&&!s.disabled){
   const next={...o,[s.dataset.agent]:!o[s.dataset.agent]};
   if(!next.enabled)next.media_ai=false;
   if(s.dataset.agent==='media_ai'&&next.media_ai&&!await v8Ask('Deixar ler fotos e áudios?','As fotos e textos que você mandar vão para o serviço DeepSeek e podem ser processados fora do Brasil. Os áudios viram texto aqui no MOVI+. Você pode desligar quando quiser.','Sim, pode ler'))return;
   try{await request('finance-agent/consent',{enabled:!!next.enabled,media_ai:!!next.media_ai,trends:!!next.trends,offers:!!next.offers,text_ai:!!next.text_ai},'PUT');v8Toast('Salvo');render()}
   catch(err){v8Toast(err.message)}
  }
  if(e.target.closest('[data-pending]'))v8ReviewPending(pending);
 };
 body.onchange=async e=>{
  const input=e.target.closest('[data-media]');if(!input||!input.files.length)return;
  const fd=new FormData();fd.append('file',input.files[0]);input.value='';
  v8Toast('Lendo... espere um pouco');
  try{
   const r=await fetch('/api/finance-agent/media',{method:'POST',credentials:'same-origin',headers:{'X-Requested-With':'NOVAGENTE-V5'},body:fd});
   const j=await r.json().catch(()=>({}));if(!r.ok)throw Error(j.detail||'Não consegui ler o arquivo.');
   v8ReviewPending([{id:j.id,proposal:j.proposal}]);
  }catch(err){v8Toast(err.message)}
 };
}
async function v8AgentWhats(){await financeAgentScreen()}

/* ---------- Documentos ---------- */
async function v8Docs(seq){
 const [d,cons]=await Promise.all([request('documents'),request('consents')]);
 if(v8Stale(seq))return;
 const body=document.getElementById('body');
 if(!d.enabled){
  body.innerHTML='<div class="dv-empty">'+v8i('lock')+'<p>Para mandar sua CNH, primeiro deixe o MOVI+ guardar seus dados pessoais.</p>'+
   '<p class="dv-small">Eles ficam guardados com proteção, só para o Programa de Renovação de Frota.</p>'+
   '<button type="button" class="dv-btn dv-btn-gold dv-press" data-allow>Deixar guardar meus dados</button></div>';
  body.querySelector('[data-allow]').onclick=async()=>{
   if(!await v8Ask('Guardar seus dados pessoais?','Seu CPF, RG, CNH e endereço ficam guardados com proteção neste sistema. Você pode desligar em Privacidade.','Sim, pode guardar'))return;
   try{await request('consents',{...v8ConsentPayload(cons.choices),identity_collection:true},'PUT');fields=(await request('schema')).fields;v8Toast('Pronto! Agora você pode mandar.');render()}
   catch(err){v8Toast(err.message)}
  };
  return;
 }
 const full=d.items.length>=5;
 body.innerHTML=(full?'<div class="dv-card"><p class="dv-p">Você já mandou 5 arquivos, o máximo. Apague um para mandar outro.</p></div>':
  '<label class="dv-btn dv-btn-gold dv-press" style="min-height:96px;font-size:23px">'+v8i('camera')+'Mandar foto da CNH<input type="file" accept=".pdf,.jpg,.jpeg,.png,image/jpeg,image/png,application/pdf" data-doc hidden></label>'+
  '<p class="dv-small">Foto (JPG ou PNG) ou PDF, até 8 MB. Fica guardado com proteção.</p>')+
  '<h2 class="dv-group-title">ARQUIVOS QUE VOCÊ MANDOU</h2>'+
  (d.items.length?'<div class="dv-group">'+d.items.map(x=>'<div class="dv-row"><span class="dv-row-ic dv-tone-green">'+v8i('file')+'</span><span class="dv-row-txt"><b>Documento</b><small>Enviado em '+safe(new Date(x.at).toLocaleDateString('pt-BR'))+'</small></span>'+
   '<a class="dv-iconbtn dv-press" href="/api/documents/'+safe(x.id)+'" aria-label="Baixar documento">'+v8i('down')+'</a><button type="button" class="dv-iconbtn dv-press" data-deldoc="'+safe(x.id)+'" aria-label="Apagar documento">'+v8i('trash')+'</button></div>').join('')+'</div>':
   '<div class="dv-card"><p class="dv-p">Nenhum arquivo ainda.</p></div>');
 body.onchange=async e=>{
  const input=e.target.closest('[data-doc]');if(!input||!input.files.length)return;
  const fd=new FormData();fd.append('file',input.files[0]);input.value='';
  v8Toast('Enviando...');
  try{const r=await fetch('/api/documents',{method:'POST',body:fd,headers:{'X-Requested-With':'NOVAGENTE-V5'},credentials:'same-origin'});
   if(!r.ok)throw Error((await r.json().catch(()=>({}))).detail||'Não consegui enviar.');v8Toast('Documento enviado!');render()}
  catch(err){v8Toast(err.message)}
 };
 body.onclick=async e=>{
  const b=e.target.closest('[data-deldoc]');if(!b)return;
  if(!await v8Ask('Apagar este documento?','Ele sai do MOVI+ e não dá para recuperar.','Sim, apagar',{danger:true}))return;
  try{await request('documents/'+b.dataset.deldoc,undefined,'DELETE');v8Toast('Documento apagado');render()}catch(err){v8Toast(err.message)}
 };
}

/* ---------- Entrar / cadastro por convite ---------- */
function v8AuthErr(m){
 if(/Credenciais|incorret/i.test(m))return 'Usuário ou senha errados. Confira e tente de novo.';
 if(/Aguarde 15/i.test(m))return 'Muitas tentativas. Espere 15 minutos e tente de novo.';
 if(/Código/i.test(m))return m;
 return m;
}
function v8Login(mode){
 user=null;v8Seq++;v8LastTab='';v8LegalChecked=null;
 v8Theme(true);window.scrollTo(0,0);
 const invite=new URLSearchParams(location.search).get('convite')||'';
 mode=mode==='enroll'||invite?'enroll':'login';
 const logo='<div class="dv-logo">'+v8Logo(true)+'<p class="dv-tag">SEU DINHEIRO E SEUS BENEFÍCIOS</p></div>';
 const app=document.getElementById('app');
 if(mode==='login'){
  app.innerHTML='<div class="dv-auth dv-noshell">'+logo+'<h1>Entrar</h1><form id="dvLogin" novalidate>'+
  '<div class="dv-field"><label for="dv-user">Seu usuário</label><input class="dv-input" id="dv-user" name="username" data-mask="username" autocomplete="username" autocapitalize="none" spellcheck="false" required></div>'+
  v8PassField('password','Sua senha','current-password')+
  '<div class="dv-field" id="dvOtp" hidden><label for="dv-otp">Código do aplicativo autenticador</label><input class="dv-input" id="dv-otp" name="otp" inputmode="numeric" autocomplete="one-time-code" maxlength="70"></div>'+
  '<p class="dv-err" id="dvLoginErr" role="alert"></p><button type="submit" class="dv-btn dv-btn-gold dv-press">Entrar</button></form>'+
  '<div class="dv-divider">ou</div><button type="button" class="dv-btn dv-btn-ghost dv-press" data-mode="enroll">Recebi um convite</button>'+
  '<div class="dv-auth-foot"><button type="button" class="dv-btn-quiet dv-btn" style="width:auto" data-otp>Sou gestor</button><button type="button" class="dv-btn-quiet dv-btn" style="width:auto" data-landing>Conhecer o MOVI+</button><button type="button" class="dv-btn-quiet dv-btn" style="width:auto" data-terms>Termos e privacidade</button></div></div>';
  const f=document.getElementById('dvLogin');v8BindEyes(f);v8WireFormat(f);
  f.onsubmit=async e=>{
   e.preventDefault();const err=document.getElementById('dvLoginErr'),b=f.querySelector('[type=submit]');err.textContent='';
   if(!f.elements.username.value.trim()||!f.elements.password.value){err.textContent='Preencha o usuário e a senha.';return}
   v8Busy(b,true,'Entrando...');
   try{await request('login',{username:f.elements.username.value,password:f.elements.password.value,otp:f.elements.otp.value||''});tab='home';await bootstrap()}
   catch(x){v8Busy(b,false);err.textContent=v8AuthErr(x.message);if(/Código/i.test(x.message))document.getElementById('dvOtp').hidden=false}
  };
  setTimeout(()=>document.getElementById('dv-user').focus({preventScroll:true}),30);
 }else{
  app.innerHTML='<div class="dv-auth dv-noshell">'+logo+'<h1>Criar minha conta</h1><p class="dv-p">Use o código do convite que o MOVI+ mandou para você.</p><form id="dvEnroll" novalidate>'+
  '<div class="dv-field"><label for="dv-inv">Código do convite</label><input class="dv-input" id="dv-inv" name="invite" data-mask="invite" value="'+safe(invite)+'" autocomplete="off" required></div>'+
  '<div class="dv-field"><label for="dv-name">Seu nome</label><input class="dv-input" id="dv-name" name="name" data-mask="name" autocapitalize="words" autocomplete="name" required></div>'+
  '<div class="dv-field"><label for="dv-un">Escolha um usuário</label><input class="dv-input" id="dv-un" name="username" data-mask="username" autocapitalize="none" spellcheck="false" maxlength="32" required><p class="dv-small">Só letras minúsculas e números, sem espaço. Exemplo: joao2026</p></div>'+
  v8PassField('pwd','Crie uma senha','new-password')+v8Rules()+
  '<label class="dv-check"><input type="checkbox" name="accepted_rules" required><span>Entendi que o aplicativo não mexe no meu dinheiro e que o gestor precisa aprovar meu acesso.</span></label>'+
  '<p class="dv-err" id="dvEnrollErr" role="alert"></p><button type="submit" class="dv-btn dv-btn-gold dv-press">Pedir meu acesso</button></form>'+
  '<button type="button" class="dv-btn dv-btn-ghost dv-press" data-mode="login">Já tenho conta</button><div class="dv-auth-foot"><button type="button" class="dv-btn-quiet dv-btn" style="width:auto" data-terms>Termos e privacidade</button></div></div>';
  const f=document.getElementById('dvEnroll');v8BindEyes(f);v8WireFormat(f);
  const valid=v8WatchRules(f.elements.pwd);
  f.onsubmit=async e=>{
   e.preventDefault();const err=document.getElementById('dvEnrollErr'),b=f.querySelector('[type=submit]');err.textContent='';
   const v=k=>f.elements[k].value.trim();
   if(!v('invite')){err.textContent='Preencha o código do convite.';return}
   if(v('name').split(/\s+/).filter(x=>x.length>=2).length<2){err.textContent='Escreva seu nome e sobrenome.';return}
   if(!/^[a-z0-9_]{4,32}$/.test(v('username'))){err.textContent='O usuário precisa ter de 4 a 32 letras ou números.';return}
   if(!valid()){err.textContent='A senha ainda não cumpre as regras.';return}
   if(!f.elements.accepted_rules.checked){err.textContent='Marque a caixa dizendo que entendeu.';return}
   let legal;
   try{legal=await v8Terms({mode:'enroll'})}catch(x){err.textContent=x.message;return}
   if(!legal){err.textContent='Para criar a conta, é preciso aceitar os termos.';return}
   v8Busy(b,true,'Enviando...');
   try{
    await request('enroll',{invite:v('invite'),name:v('name'),username:v('username'),password:f.elements.pwd.value,accepted_rules:true,legal});
    history.replaceState(null,'',location.pathname);v8Login('login');v8Toast('Pedido enviado! Espere o gestor aprovar.');
   }catch(x){v8Busy(b,false);err.textContent=x.message}
  };
 }
 app.onclick=e=>{
  const m=e.target.closest('[data-mode]');if(m){if(m.dataset.mode==='login')history.replaceState(null,'',location.pathname);v8Login(m.dataset.mode);return}
  if(e.target.closest('[data-otp]')){const o=document.getElementById('dvOtp');o.hidden=!o.hidden;if(!o.hidden)o.querySelector('input').focus();return}
  if(e.target.closest('[data-terms]')){v8LegalReader('termos');return}
  if(e.target.closest('[data-landing]')){v8Theme(false);ngLandingPublic()}
 };
}
login=v8Login;
// A página de apresentação antiga abre a entrada nova (com os termos), não o formulário antigo.
if(typeof ngLandingOpenAuth==='function')ngLandingOpenAuth=function(mode){v8Login(mode==='enroll'?'enroll':'login')};
