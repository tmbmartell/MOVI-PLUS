'use strict';
/* MOVI+ V8 · tela do gestor: mesma marca do app do motorista.
   O que o gestor faz todo dia (aprovar cadastros, responder pedidos, convidar) fica no topo do
   Painel; o que é de configuração fica no fim do menu, menor e com uma frase explicando.
   Camada carregada depois de driver-v8.js: as telas antigas continuam funcionando por baixo. */
const GV_NAV=[
 ['DIA A DIA',[
  ['home','Painel','home','Pendências e números do mês'],
  ['drivers','Motoristas','user','Ver e acompanhar cada motorista'],
  ['report','Relatórios','pie','Gráficos e exportação em CSV']]],
 ['TODA SEMANA',[
  ['benefits','Benefícios','gift','Catálogo e pedidos dos motoristas'],
  ['campaigns','Campanhas','news','Ofertas e avisos no app'],
  ['tasks','Operação','list','Tarefas da equipe'],
  ['invites','Convites','plus','Convidar e aprovar cadastros']]],
 ['CONFIGURAR E CONSULTAR',[
  ['agent-manage','Agente financeiro','spark','Liberar ou pausar o assistente'],
  ['whatsapp','WhatsApp','chat','Conexão do número do MOVI+'],
  ['distribution','Distribuição','pie','Simulador de divisão de valores'],
  ['privacy','Pedidos de exclusão','lock','Motoristas que pediram para apagar dados'],
  ['audit','Auditoria','file','Histórico de ações no sistema'],
  ['settings','Minha conta','key','Senha, 2 etapas e chave do agente']]]
];
const GV_MOBILE=[['home','Painel','home'],['drivers','Motoristas','user'],['report','Relatórios','pie'],['menu','Menu','grid']];
const gvIsAdmin=()=>!!(user&&user.role==='admin');

function gvShell(){
 let shell=document.getElementById('gvShell');
 if(!shell){
  const navHtml=GV_NAV.map(([group,items],gi)=>'<p class="gv-group">'+group+'</p>'+items.map(([id,label,icon,sub])=>
   '<button type="button" class="gv-link dv-press'+(gi===2?' gv-link-minor':'')+'" data-gtab="'+id+'">'+v8i(icon)+'<span><b>'+label+'</b>'+(gi===2?'<small>'+sub+'</small>':'')+'</span></button>').join('')).join('');
  document.getElementById('app').innerHTML='<div class="gv-shell" id="gvShell">'+
   '<aside class="gv-side" aria-label="Menu do gestor"><div class="gv-logo">'+v8Logo(true)+'<span>GESTÃO</span></div><div class="gv-nav-list" role="navigation" aria-label="Seções">'+navHtml+'</div>'+
   '<div class="gv-user"><span>'+v8i('user')+'<b>'+safe(user.name)+'</b></span><button type="button" class="dv-btn dv-btn-ghost dv-press" data-glogout>Sair</button></div></aside>'+
   '<header class="gv-top"><span class="gv-top-brand">'+v8Logo(true)+'<small>GESTÃO</small></span></header>'+
   '<main id="body" class="gv-main dv-legacy" tabindex="-1"></main>'+
   '<div class="gv-tabbar" role="navigation" aria-label="Menu principal">'+GV_MOBILE.map(([id,l,ic])=>'<button type="button" class="dv-tab dv-press" data-gtab="'+id+'">'+v8i(ic)+'<span>'+l+'</span></button>').join('')+'</div></div>';
  shell=document.getElementById('gvShell');
  shell.addEventListener('click',gvClick);
  // Telas antigas redesenham partes da tabela (filtros); a tradução roda a cada mudança.
  new MutationObserver(gvPolish).observe(document.getElementById('body'),{childList:true,subtree:true});
 }
 const mobileIds=GV_MOBILE.map(x=>x[0]);
 shell.querySelectorAll('[data-gtab]').forEach(b=>{
  const on=b.dataset.gtab===tab||(b.dataset.gtab==='menu'&&!mobileIds.includes(tab));
  if(on)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current');
 });
}
async function gvClick(e){
 if(e.target.closest('[data-retry]')){render();return}
 const t=e.target.closest('[data-gtab],[data-glogout]');if(!t)return;
 if('glogout' in t.dataset){
  if(!await v8Ask('Sair da gestão?','Para entrar de novo, use seu usuário, senha e o código de 2 etapas, se tiver ativado.','Sim, sair'))return;
  try{await request('logout',{})}catch{}
  user=null;tab='home';login();return;
 }
 if(t.dataset.gtab==='menu'){gvMenuSheet();return}
 tab=t.dataset.gtab;render();
}
/* No celular, o menu completo abre num painel, com a mesma ordem e explicações. */
function gvMenuSheet(){
 const s=v8Sheet('<div class="dv-sheet-head"><h2>Menu da gestão</h2><button type="button" class="dv-x dv-press" data-close aria-label="Fechar">'+v8i('x')+'</button></div>'+
  GV_NAV.map(([group,items])=>'<h3 class="dv-group-title">'+group+'</h3><div class="dv-group">'+items.map(([id,label,icon,sub])=>
   '<button type="button" class="dv-row dv-row-compact dv-press" data-go-g="'+id+'"><span class="dv-row-ic dv-tone-gold">'+v8i(icon)+'</span><span class="dv-row-txt"><b>'+label+'</b><small>'+sub+'</small></span>'+v8i('chev','dv-chev')+'</button>').join('')+'</div>').join('')+
  '<div style="margin-top:18px"><button type="button" class="dv-btn dv-btn-ghost dv-press" data-glogout-s>Sair</button></div>',{label:'Menu da gestão'});
 s.el.onclick=e=>{
  const b=e.target.closest('[data-go-g]');if(b){s.close();tab=b.dataset.goG;render();return}
  if(e.target.closest('[data-glogout-s]')){s.close();gvClick({target:document.querySelector('[data-glogout]')})}
 };
}

const gvPrevNav=nav;
nav=function(){if(gvIsAdmin()){v8Theme(true);return gvShell()}return gvPrevNav()};
const gvPrevHeading=heading;
heading=function(t,sub){
 if(gvIsAdmin())return '<div class="gv-head"><h1>'+safe(String(t).replace(/^Gestão do Clube$/,'Relatórios').replace(/\bClube\b/,'MOVI+'))+'</h1>'+(sub?'<p>'+safe(sub)+'</p>':'')+'</div>';
 return gvPrevHeading(t,sub);
};
const gvPrevRender=render;
render=async function(){
 if(!gvIsAdmin())return gvPrevRender();
 v8Theme(true);
 if(!user.must_change&&(tab==='home'||tab==='report')){
  nav();
  const body=document.getElementById('body');body.onclick=null;body.onchange=null;window.scrollTo(0,0);
  try{if(tab==='home')await gvHome();else await stage2Dashboard()}
  catch(err){body.innerHTML=v8Error(err.message)}
  return;
 }
 await gvPrevRender();
 window.scrollTo(0,0);
};

/* ---------- Painel: primeiro o que precisa de ação hoje ---------- */
async function gvHome(){
 const month=v8Day().slice(0,7);
 const [ov,claims,dels,dash,tasks]=await Promise.allSettled([request('admin/overview'),request('program/claims'),request('admin/delete-requests'),
  request('program/dashboard?month='+month),request('program/tasks')]);
 const ok=x=>x.status==='fulfilled'?x.value:null;
 const pendDrivers=ok(ov)?ok(ov).items.filter(x=>x.status==='pending'):[];
 const pendClaims=ok(claims)?ok(claims).items.filter(x=>x.status==='pending'):[];
 const pendDels=ok(dels)?ok(dels).items.filter(x=>x.status==='pending'):[];
 const openTasks=ok(tasks)?ok(tasks).items.filter(x=>x.status!=='done').length:0;
 const d=ok(dash),h=new Date().getHours(),hello=h<12?'Bom dia':h<18?'Boa tarde':'Boa noite';
 const todo=pendDrivers.length+pendClaims.length+pendDels.length;
 const when=s=>s?new Date(s).toLocaleDateString('pt-BR'):'';
 document.getElementById('body').innerHTML=
 '<div class="gv-head"><h1>'+hello+', '+safe(String(user.name||'').split(' ')[0])+'</h1><p>'+(todo?'Você tem '+todo+' '+(todo===1?'coisa':'coisas')+' para resolver.':'Nada pendente agora. Tudo em dia.')+'</p></div>'+
 '<div class="gv-grid">'+
 '<section class="gv-panel gv-panel-main"><h2 class="dv-group-title">PARA RESOLVER HOJE</h2>'+
  (todo?'':'<div class="dv-empty">'+v8i('check')+'<p>Nenhuma pendência</p><p class="dv-small">Novos cadastros e pedidos aparecem aqui.</p></div>')+
  (pendDrivers.length?'<div class="gv-block"><h3>'+v8i('user')+'Cadastros esperando aprovação <span class="gv-count">'+pendDrivers.length+'</span></h3>'+
   pendDrivers.map(x=>'<div class="gv-item"><span><b>'+safe(x.name)+'</b><small>Usuário '+safe(x.username)+' · pediu em '+safe(when(x.created_at))+'</small></span>'+
   '<button type="button" class="dv-btn dv-btn-gold dv-press" data-approve="'+x.id+'" data-name="'+safe(x.name)+'">Aprovar</button></div>').join('')+'</div>':'')+
  (pendClaims.length?'<div class="gv-block"><h3>'+v8i('gift')+'Pedidos de benefício <span class="gv-count">'+pendClaims.length+'</span></h3>'+
   pendClaims.map(x=>'<div class="gv-item"><span><b>'+safe(x.name)+' quer '+safe(x.title)+'</b><small>'+safe(x.points_at_request)+' pontos no pedido · '+safe(when(x.created_at))+'</small></span>'+
   '<span class="gv-actions"><button type="button" class="dv-btn dv-btn-green dv-press" data-claim="'+x.id+'" data-decision="approved">Aprovar</button><button type="button" class="dv-btn dv-btn-ghost dv-press" data-claim="'+x.id+'" data-decision="rejected">Recusar</button></span></div>').join('')+'</div>':'')+
  (pendDels.length?'<div class="gv-block"><h3>'+v8i('lock')+'Pedidos para apagar dados <span class="gv-count">'+pendDels.length+'</span></h3><p class="dv-small">A LGPD pede resposta rápida. Confira obrigações de guarda antes de apagar.</p>'+
   '<button type="button" class="dv-btn dv-btn-ghost dv-press" data-gtab-go="privacy">Ver pedidos de exclusão</button></div>':'')+
 '</section>'+
 '<section class="gv-panel"><h2 class="dv-group-title">AÇÕES RÁPIDAS</h2>'+
  '<button type="button" class="dv-btn dv-btn-gold dv-press" id="gvInvite">'+v8i('plus')+'Gerar convite</button><div id="gvInviteOut"></div>'+
  '<button type="button" class="dv-btn dv-btn-ghost dv-press" data-gtab-go="campaigns">'+v8i('news')+'Nova campanha</button>'+
  '<button type="button" class="dv-btn dv-btn-ghost dv-press" data-gtab-go="tasks">'+v8i('list')+'Tarefas abertas: '+openTasks+'</button></section>'+
 '</div>'+
 (d?'<h2 class="dv-group-title">'+safe(v8MonthLabel(month).toUpperCase())+'</h2><div class="gv-metrics">'+
  [['Motoristas ativos',d.active,'de '+d.drivers+' cadastrados'],['Ganhos anotados',brl(d.income_declared),'pelos motoristas que autorizaram'],
   ['Gastos anotados',brl(d.expense_declared),'pelos motoristas que autorizaram'],['Análise permitida',d.authorized,'motoristas deixaram o gestor ver']].map(([l,v,s])=>
   '<div class="gv-metric"><span>'+l+'</span><b>'+safe(v)+'</b><small>'+s+'</small></div>').join('')+'</div>'+
  '<p class="dv-small" style="margin-top:10px">Valores anotados pelos próprios motoristas, sem conferência bancária. <button type="button" class="dv-link" data-gtab-go="report">Ver relatório completo</button></p>':'');
 const body=document.getElementById('body');
 body.onclick=async e=>{
  const go=e.target.closest('[data-gtab-go]');if(go){tab=go.dataset.gtabGo;render();return}
  const ap=e.target.closest('[data-approve]');
  if(ap){
   if(!await v8Ask('Aprovar '+ap.dataset.name+'?','A pessoa passa a entrar no MOVI+ com o usuário que escolheu.','Sim, aprovar'))return;
   try{await request('admin/activate/'+ap.dataset.approve,{});v8Toast('Cadastro aprovado');render()}catch(err){v8Toast(err.message)}
   return;
  }
  const cl=e.target.closest('[data-claim]');
  if(cl){
   const yes=cl.dataset.decision==='approved';
   if(!await v8Ask(yes?'Aprovar este pedido?':'Recusar este pedido?',yes?'O motorista vê "Aprovado" no app. Combine a entrega do benefício com ele.':'O motorista vê "Recusado" no app.',yes?'Sim, aprovar':'Sim, recusar',{danger:!yes}))return;
   try{await request('program/claims/'+cl.dataset.claim+'/decide',{status:cl.dataset.decision});v8Toast(yes?'Pedido aprovado':'Pedido recusado');render()}catch(err){v8Toast(err.message)}
  }
 };
 document.getElementById('gvInvite').onclick=async e=>{
  const b=e.currentTarget;v8Busy(b,true,'Gerando...');
  try{
   const r=await request('admin/invites',{}),u=new URL(location.href);u.search='';u.hash='';u.searchParams.set('convite',r.invite);
   document.getElementById('gvInviteOut').innerHTML='<div class="gv-invite"><p class="dv-small">Mande este link para o motorista. Vale por 48 horas e para um cadastro só.</p>'+
    '<input class="dv-input" readonly value="'+safe(u.toString())+'" aria-label="Link do convite"><button type="button" class="dv-btn dv-btn-green dv-press" id="gvCopy">Copiar link</button></div>';
   document.getElementById('gvCopy').onclick=async()=>{try{await navigator.clipboard.writeText(u.toString());v8Toast('Link copiado')}catch{v8Toast('Selecione o link e copie')}};
  }catch(err){v8Toast(err.message)}
  finally{v8Busy(b,false)}
 };
}

/* ---------- Clareza nas telas antigas do gestor ---------- */
/* Traduz códigos técnicos para português e mostra horário local, sem mexer nas telas originais. */
const GV_STATUS={pending:'Aguardando aprovação',active:'Ativo',suspended:'Suspenso'};
const GV_AUDIT={'login':'Entrou no sistema','logout':'Saiu do sistema','finance:created':'Anotou ganho ou gasto','finance:removed':'Apagou uma anotação',
 'consents:updated':'Mudou permissões de privacidade','legal:accepted':'Aceitou os termos','distribution:updated':'Salvou divisão do dinheiro',
 'distribution:reset':'Apagou divisão do dinheiro','profile:updated':'Atualizou o cadastro','interview:answer':'Respondeu pergunta do cadastro',
 'enroll:requested':'Pediu cadastro por convite','chat:finance':'Anotou pelo assistente','privacy:export':'Baixou os próprios dados',
 'privacy:requested':'Pediu exclusão dos dados','privacy:fulfilled':'Exclusão de dados concluída','identity_collection:granted':'Permitiu guardar dados pessoais',
 'identity_collection:revoked':'Retirou permissão de dados pessoais','document:uploaded':'Enviou documento','document:read':'Abriu documento',
 'document:removed':'Apagou documento','password:changed':'Trocou a senha','invite:created':'Gerou convite','driver:activated':'Aprovou cadastro',
 'finance_agent:consent':'Mudou permissões do agente','finance_agent:confirmed':'Confirmou sugestão do agente','finance_agent:discarded':'Descartou sugestão do agente',
 'finance_agent:proposal':'Agente sugeriu uma anotação','mfa:enabled':'Ativou 2 etapas','mfa:disabled':'Desativou 2 etapas'};
let gvPolishing=false;
function gvPolish(){
 if(gvPolishing||!gvIsAdmin())return;
 const body=document.getElementById('body');if(!body)return;
 gvPolishing=true;
 try{
  body.querySelectorAll('td,option').forEach(el=>{
   const t=el.textContent.trim();
   if(GV_STATUS[t]&&el.children.length===0){
    // <option> sem value usa o texto como valor: guardamos o código original antes de traduzir.
    if(el.tagName==='OPTION'&&!el.hasAttribute('value'))el.setAttribute('value',t);
    el.textContent=GV_STATUS[t];
   }
  });
  body.querySelectorAll('.dist-header .eyebrow').forEach(el=>el.remove());
  if(tab==='audit'){
   body.querySelectorAll('th').forEach(th=>{if(th.textContent==='Data UTC')th.textContent='Data e hora'});
   body.querySelectorAll('tr').forEach(tr=>{
    const td=tr.querySelectorAll('td');if(td.length<3)return;
    if(GV_AUDIT[td[0].textContent]){td[0].title=td[0].textContent;td[0].textContent=GV_AUDIT[td[0].textContent]}
    if(/^\d{4}-\d{2}-\d{2}T/.test(td[2].textContent)){const d=new Date(td[2].textContent);if(!isNaN(d))td[2].textContent=d.toLocaleString('pt-BR')}
   });
  }
  if(tab==='privacy'&&!body.querySelector('[data-erasure]')&&!body.querySelector('.gv-none')){
   const table=body.querySelector('table');
   if(table)table.insertAdjacentHTML('afterend','<p class="dv-small gv-none" style="padding:14px 8px">Nenhum pedido de exclusão agora.</p>');
  }
 }finally{gvPolishing=false}
}
