'use strict';
/* Clube do Motorista - Etapa 2: painel, beneficios, campanhas internas e operacao. */
am[0]=['home','Gestão do Clube'];
am.splice(3,0,['benefits','Benefícios'],['tasks','Operação']);
dm.splice(2,0,['benefits','Benefícios']);
const stage2OldRender=render;
render=async function(){
 if(!user || !(['home','benefits','tasks','campaigns'].includes(tab)))return stage2OldRender();
 if(tab==='tasks' && user.role!=='admin')return stage2OldRender();
 nav();
 try{
  if(tab==='home' && user.role==='admin')await stage2Dashboard();
  else if(tab==='benefits')await stage2Benefits();
  else if(tab==='tasks')await stage2Tasks();
  else if(tab==='campaigns')await stage2Campaigns();
  else await stage2OldRender();
 }catch(err){const content=document.getElementById('body');if(content)content.innerHTML='<div class="card"><b>Não foi possível abrir esta área.</b><p>'+safe(err.message)+'</p></div>';}
};

const stage2Money=v=>brl(v);
const stage2When=s=>s?new Date(s).toLocaleDateString('pt-BR'): '—';
const stage2Labels={pending:'Aguardando',approved:'Aprovado',rejected:'Recusado',new:'Novo',doing:'Em andamento',done:'Concluído',draft:'Rascunho',published:'Publicada'};
const stage2Status=v=>'<span class="s2-status s2-status-'+safe(v)+'">'+safe(stage2Labels[v]||v)+'</span>';
const stage2Empty=(text='Nenhuma informação registrada.')=>'<p class="muted s2-empty">'+safe(text)+'</p>';
function stage2Bars(series,key,maxValue=0){
 const maximum=Math.max(maxValue,1,...series.map(x=>Number(x[key])||0));
 return '<div class="s2-bars">'+series.map((x,i)=>{
  const value=Number(x[key])||0;
  return '<div class="s2-bar-line"><div class="s2-bar-label">'+safe(x.label||x.month||x.name)+'</div><div class="s2-bar-track"><div class="s2-bar-fill" style="width:'+(value/maximum*100).toFixed(2)+'%"></div></div><strong>'+safe(x.shown??value)+'</strong></div>'
 }).join('')+'</div>';
}
function stage2Media(row){
 if(!row.media_id)return '';
 let uri='/api/program/media/'+encodeURIComponent(row.media_id),mime=row.mime||'';
 if(mime.startsWith('image/'))return '<div class="s2-media"><img src="'+uri+'" alt="Mídia da campanha" loading="lazy"></div>';
 if(mime.startsWith('video/'))return '<div class="s2-media"><video controls preload="metadata" src="'+uri+'"></video></div>';
 if(mime.startsWith('audio/'))return '<div class="s2-media"><audio controls preload="metadata" src="'+uri+'"></audio></div>';
 return '';
}
function stage2Cards(items){
 return '<div class="s2-metrics">'+items.map(x=>'<div class="s2-metric"><div class="s2-kicker">'+safe(x[0])+'</div><strong>'+safe(x[1])+'</strong><small>'+safe(x[2]||'')+'</small></div>').join('')+'</div>';
}
async function stage2Dashboard(month){
 const current=month||new Date().toISOString().slice(0,7);
 const d=await request('program/dashboard?month='+encodeURIComponent(current));
 $('#body').innerHTML=heading('Gestão do Clube','Resumo operacional e financeiro: somente números efetivamente registrados e autorizados.')+
 '<div class="s2-toolbar"><div><label for="s2Month">Período dos lançamentos</label><input id="s2Month" type="month" value="'+safe(d.month)+'"></div>'+
 '<a id="s2Export" class="btn-lite" href="/api/program/report.csv?month='+encodeURIComponent(d.month)+'">Exportar relatório CSV</a></div>'+
 stage2Cards([['Motoristas',d.drivers,'Cadastros totais'],['Ativos',d.active,'Acessos aprovados'],['Cadastros pendentes',d.pending,'Aguardando aprovação'],['Análise permitida',d.authorized,'Consentimento válido'],['Receitas registradas',stage2Money(d.income_declared),'Autodeclaradas, não bancárias'],['Despesas registradas',stage2Money(d.expense_declared),'Autodeclaradas, não bancárias'],['Resultado registrado',stage2Money(d.net_declared),'Não é saldo em conta'],['Lançamentos',d.entry_count,'No mês selecionado']])+
 '<div class="s2-dashboard-grid"><section class="card"><h3>Receita mensal declarada — últimos seis meses</h3>'+
 stage2Bars(d.months.map(m=>({label:m.month, income:m.income,shown:stage2Money(m.income)})),'income')+'</section>'+
 '<section class="card"><h3>Plataformas dos participantes</h3><p class="muted">Apenas dos motoristas ativos que autorizaram a análise.</p>'+
 (Object.keys(d.platforms).length?stage2Bars(Object.entries(d.platforms).map(([label,total])=>({label,total,shown:total})),'total'):stage2Empty('Sem dados autorizados para este gráfico.'))+'</section>'+
 '<section class="card"><h3>Andamento dos cadastros</h3><p class="muted">Faixas de preenchimento dos motoristas que autorizaram análise.</p>'+
 stage2Bars(Object.entries(d.progress).map(([label,total])=>({label,total,shown:total})),'total')+'</section>'+
 '<section class="card"><h3>Acompanhamento operacional</h3>'+stage2Cards([['Benefícios pendentes',d.benefit_requests,'Aguardando revisão'],['Tarefas abertas',d.open_tasks,'Em fila e andamento'],['Campanhas',d.campaigns_published,'Publicadas no sistema'],['Campanhas autorizadas',d.marketing_opt_in,'Motoristas com opt-in']])+
 '<div class="s2-cta"><button class="btn-lite" id="s2GoTasks">Abrir operação</button><button class="btn-lite" id="s2GoBenefits">Gerenciar benefícios</button></div></section></div>'+
 '<div class="notice">'+safe(d.data_scope)+' O controle de depósitos e a conciliação de pagamentos serão trabalhados em outra etapa.</div>';
 $('#s2Month').onchange=e=>stage2Dashboard(e.target.value);
 $('#s2GoTasks').onclick=()=>{tab='tasks';render()};
 $('#s2GoBenefits').onclick=()=>{tab='benefits';render()};
}
async function stage2Benefits(){
 const d=await request('program/benefits');
 const adminMode=user.role==='admin';
 const requests=adminMode?await request('program/claims'):null;
 let head=heading('Benefícios do Clube',adminMode?'Catálogo, estoque e aprovação manual dos pedidos.':'Acompanhe sua pontuação indicativa e solicite benefícios disponíveis.');
 let score=!adminMode?stage2Cards([['Seus pontos',d.points.total,'Indicativos, não são dinheiro'],['Cadastro',d.points.profile,'Até 60 pontos'],['Dias registrados',d.points.diary,'Até 40 pontos']]):'';
 let form=adminMode?'<section class="card"><h3>Adicionar benefício</h3><form id="s2BenefitForm" class="stack">'+
 '<div><label>Nome do benefício</label><input name="title" maxlength="90" required placeholder="Ex.: Check-up do veículo"></div>'+
 '<div><label>Como funciona</label><textarea name="description" maxlength="500" required placeholder="Regras e condições do benefício"></textarea></div>'+
 '<div class="fields"><div><label>Pontos indicativos necessários (0–100)</label><input name="points_required" type="number" min="0" max="100" step="1" value="20" required></div>'+
 '<div><label>Quantidade disponível</label><input name="stock" type="number" min="0" max="100000" step="1" value="10" required></div></div>'+
 '<button type="submit" class="btn">Criar benefício</button></form></section>':'<div class="notice">Os pontos são um indicador educativo de participação. Solicitações precisam ser revisadas pelo gestor. Não há prêmio financeiro automático nem pagamento associado.</div>';
 let cards=d.items.length?'<div class="s2-benefit-grid">'+d.items.map(b=>'<article class="card s2-benefit">'+
 '<div class="row">'+stage2Status(b.active?'published':'draft')+'<span class="s2-point-tag">'+b.points_required+' pontos</span></div>'+
 '<h3>'+safe(b.title)+'</h3><p>'+safe(b.description)+'</p><div class="s2-benefit-bottom"><span>Disponíveis: <b>'+b.remaining+'</b> / '+b.stock+'</span>'+
 (adminMode?'<div class="row"><button class="btn-lite btn-sm" data-ben-toggle="'+b.id+'" data-active="'+b.active+'" data-stock="'+b.stock+'">'+(b.active?'Desativar':'Ativar')+'</button><button class="btn-lite btn-sm" data-ben-stock="'+b.id+'" data-stock="'+b.stock+'">Alterar quantidade</button></div>':
  '<button class="btn" data-ben-claim="'+b.id+'" '+(b.remaining<=0||d.points.total<b.points_required?'disabled':'')+'>Solicitar</button>')+
 '</div></article>').join('')+'</div>':stage2Empty('Nenhum benefício cadastrado.');
 const list=adminMode?
 '<section class="card"><h3>Solicitações aguardando avaliação</h3><div class="scroll"><table><thead><tr><th>Participante</th><th>Benefício</th><th>Pontos indicados</th><th>Data</th><th>Situação</th><th>Ações</th></tr></thead><tbody>'+
 requests.items.map(c=>'<tr><td>'+safe(c.name)+'</td><td>'+safe(c.title)+'</td><td>'+c.points_at_request+'</td><td>'+safe(stage2When(c.created_at))+'</td><td>'+stage2Status(c.status)+'</td><td>'+(c.status==='pending'?'<button class="btn-lite btn-sm" data-claim-action="approved" data-claim-id="'+c.id+'">Aprovar</button> <button class="btn-lite btn-red btn-sm" data-claim-action="rejected" data-claim-id="'+c.id+'">Recusar</button>':'—')+'</td></tr>').join('')+
 '</tbody></table></div>'+(!requests.items.length?stage2Empty('Sem solicitações no momento.'):'')+'</section>':
 '<section class="card"><h3>Minhas solicitações</h3>'+ (d.claims.length?d.claims.map(x=>'<div class="s2-claim-row"><b>'+safe(x.title)+'</b>'+stage2Status(x.status)+'<small>'+safe(stage2When(x.created_at))+'</small></div>').join(''):stage2Empty('Nenhuma solicitação até agora.'))+'</section>';
 $('#body').innerHTML=head+score+(adminMode?'<div class="s2-dashboard-grid">'+form+'<section class="card"><h3>Como é calculada a pontuação?</h3><p>Até 60 pontos de acordo com o preenchimento das informações financeiras disponíveis e até 40 pontos pelos dias distintos em que o motorista fez lançamentos nos últimos 90 dias.</p><div class="notice warn">É uma pontuação de participação com registros autodeclarados. O gestor decide manualmente sobre benefícios. Não implica dinheiro, crédito, depósitos comprovados ou recompensas automáticas.</div></section></div>':form)+
 '<h3>Catálogo de benefícios</h3>'+cards+list;
 if(adminMode){
  bind('s2BenefitForm',async f=>{
   await request('program/benefits',{title:f.get('title'),description:f.get('description'),
     points_required:Number(f.get('points_required')),stock:Number(f.get('stock'))});msg('Benefício cadastrado');await stage2Benefits();
  });
  $('#body').onclick=async e=>{
   let toggle=e.target.closest('[data-ben-toggle]'),stock=e.target.closest('[data-ben-stock]'),decision=e.target.closest('[data-claim-action]');
   try{
    if(toggle){let id=toggle.dataset.benToggle;await request('program/benefits/'+id,
     {active:toggle.dataset.active==='0',stock:Number(toggle.dataset.stock)},'PUT');msg('Atualizado');await stage2Benefits();}
    else if(stock){let value=prompt('Quantidade total (inclui os já aprovados):',stock.dataset.stock);
     if(value===null)return;
     if(!/^\d+$/.test(value.trim()))return msg('Informe quantidade inteira.');
     let original=d.items.find(x=>String(x.id)===stock.dataset.benStock);
     await request('program/benefits/'+stock.dataset.benStock,{active:!!original.active,stock:Number(value)},'PUT');
     msg('Quantidade atualizada');await stage2Benefits();
    }else if(decision){
     if(!confirm((decision.dataset.claimAction==='approved'?'Aprovar':'Recusar')+' esta solicitação? Esta ação é registrada.'))return;
     await request('program/claims/'+decision.dataset.claimId+'/decide',{status:decision.dataset.claimAction});
     msg('Solicitação analisada');await stage2Benefits();
    }
   }catch(err){msg(err.message)}
  };
 }else{
  $('#body').onclick=async e=>{
   let el=e.target.closest('[data-ben-claim]');if(!el)return;
   if(!confirm('Solicitar este benefício para avaliação humana do gestor?'))return;
   try{await request('program/benefits/'+el.dataset.benClaim+'/claim',{});msg('Solicitação enviada ao gestor');await stage2Benefits()}
   catch(err){msg(err.message)}
  };
 }
}
async function stage2Tasks(){
 const d=await request('program/tasks');
 const layout=heading('Operação do Clube','Tarefas internas com prioridade, responsável e acompanhamento por status.')+
 '<div class="s2-dashboard-grid"><section class="card"><h3>Nova tarefa</h3><form id="s2TaskForm" class="stack">'+
 '<div><label>Título</label><input name="title" maxlength="110" required placeholder="Ex.: Revisar cadastros da semana"></div>'+
 '<div><label>Detalhamento</label><textarea name="details" maxlength="700" placeholder="Instruções para a equipe"></textarea></div>'+
 '<div class="fields"><div><label>Responsável</label><input name="owner" maxlength="70" value="Equipe" required></div>'+
 '<div><label>Prioridade</label><select name="priority"><option value="normal">Normal</option><option value="high">Alta</option><option value="low">Baixa</option></select></div><div><label>Prazo</label><input name="due_on" type="date"></div></div>'+
 '<button class="btn" type="submit">Adicionar tarefa</button></form></section>'+
 '<section class="card"><h3>Visão da operação</h3>'+stage2Cards([['Novas',d.items.filter(x=>x.status==='new').length],['Em andamento',d.items.filter(x=>x.status==='doing').length],['Concluídas',d.items.filter(x=>x.status==='done').length]])+
 '<p class="muted">As atividades são gerenciadas dentro do Clube, sem notificações externas.</p></section></div>'+
 '<div class="s2-kanban">'+[['new','A fazer'],['doing','Em andamento'],['done','Concluídas']].map(([id,title])=>
  '<section class="s2-kanban-col"><h3>'+title+' <span>'+d.items.filter(x=>x.status===id).length+'</span></h3>'+
  (d.items.filter(x=>x.status===id).map(x=>'<article class="s2-task"><div class="row"><small>'+safe(x.priority==='high'?'Prioridade alta':x.priority==='low'?'Prioridade baixa':'Prioridade normal')+'</small><small>'+safe(x.due_on||'Sem prazo')+'</small></div>'+
   '<b>'+safe(x.title)+'</b><p>'+safe(x.details)+'</p><div class="row"><small>'+safe(x.owner)+'</small><select data-task-id="'+x.id+'" aria-label="Estado da tarefa"><option value="new" '+(id==='new'?'selected':'')+'>A fazer</option><option value="doing" '+(id==='doing'?'selected':'')+'>Em andamento</option><option value="done" '+(id==='done'?'selected':'')+'>Concluída</option></select></div></article>').join('')||stage2Empty('Nenhuma tarefa.'))+'</section>').join('')+'</div>';
 $('#body').innerHTML=layout;
 bind('s2TaskForm',async f=>{await request('program/tasks',{title:f.get('title'),details:f.get('details'),
  owner:f.get('owner'),priority:f.get('priority'),due_on:f.get('due_on')});msg('Tarefa criada');await stage2Tasks()});
 $('#body').onchange=async e=>{let n=e.target.closest('[data-task-id]');if(!n)return;
  try{await request('program/tasks/'+n.dataset.taskId,{status:n.value},'PUT');await stage2Tasks()}catch(err){msg(err.message)}};
}
function stage2CampaignCard(x,adminMode,legacy=false){
 return '<article class="card s2-campaign-card"><div class="row">'+stage2Status(x.status)+'<small>'+safe(x.segment&&x.segment!=='all'?'Público: '+x.segment:'Público geral com autorização')+'</small></div>'+
 '<h3>'+safe(x.title)+'</h3><p class="s2-campaign-copy">'+safe(x.body)+'</p>'+stage2Media(x)+
 (adminMode&&!legacy?'<div class="row" style="margin-top:12px"><small>Somente dentro do sistema</small><button type="button" class="btn-lite btn-sm" data-edit-campaign="'+x.id+'">Editar texto e banner</button><button type="button" class="btn-lite btn-sm" data-campaign-id="'+x.id+'" data-publish="'+(x.status==='published'?'draft':'published')+'">'+(x.status==='published'?'Voltar a rascunho':'Publicar no Clube')+'</button></div>':'')+
 '</article>';
}
async function stage2Campaigns(){
 const [feed,old]=await Promise.all([request('program/campaigns'),request('campaigns')]);
 const adminMode=user.role==='admin';
 let intro=heading(adminMode?'Campanhas e comunicação':'Novidades do Clube',
 adminMode?'Crie, edite e publique banners, ofertas e comunicados pelo painel, com público selecionável.':'Acompanhe comunicados que você autorizou receber dentro do Clube.');
 let form=adminMode?'<section class="card"><h3 id="s2CampaignFormTitle">Nova campanha ou banner</h3><p class="muted" id="s2CampaignEditHint">Você pode salvar como rascunho e publicar depois. Campanhas existentes também podem ser editadas.</p><form class="stack" id="s2CampaignForm"><div><label>Título</label><input name="title" maxlength="100" required></div>'+
 '<div><label>Mensagem</label><textarea name="body" maxlength="1200" required></textarea></div>'+
 '<div class="fields"><div><label>Segmento</label><select name="segment">'+[
 ['all','Todos que autorizaram campanhas'],['UBER','Uber'],['99','99'],['URBANO NORTE','Urbano Norte'],['LEVA EU','Leva Eu'],['IN DRIVE','InDrive'],['Outro','Outra plataforma']
 ].map(([v,l])=>'<option value="'+safe(v)+'">'+safe(l)+'</option>').join('')+'</select></div>'+
 '<div><label>Situação</label><select name="status"><option value="draft">Rascunho</option><option value="published">Publicar no sistema</option></select></div></div>'+
 '<div><label>Banner ou mídia (opcional, até 8 MB)</label><input type="file" name="file" accept="image/png,image/jpeg,image/gif,image/webp,video/mp4,audio/mpeg"><span class="muted">Imagem PNG/JPG, GIF, WebP, MP4 ou MP3. Ao editar, um novo arquivo substitui o anterior. Publicação apenas dentro do MOVI+.</span></div>'+ '<label class="muted"><input type="checkbox" name="remove_media"> Remover banner/mídia da campanha ao salvar</label>'+
 '<div class="row"><button class="btn" type="submit" id="s2CampaignSave">Salvar campanha</button><button class="btn-lite" type="button" id="s2CampaignCancel" hidden>Cancelar edição</button></div></form></section>':'<div class="notice">Você vê somente campanhas permitidas pelas suas autorizações. Não há envio de mensagens ao seu WhatsApp.</div>';
 $('#body').innerHTML=intro+(adminMode?'<div class="s2-dashboard-grid">'+form+'<section class="card"><h3>Segmentação e privacidade</h3><p>Campanhas gerais só aparecem para participantes que autorizaram marketing. Campanhas específicas por plataforma exigem também autorização de análise socioeconômica.</p><div class="notice">Campanhas podem ser atualizadas pelo gestor quando necessário. Banner e texto ficam no MOVI+. Nenhum envio automático por WhatsApp, cobrança ou movimentação Pix acontece ao publicar.</div></section></div>':form)+
 '<h3>'+ (adminMode?'Campanhas cadastradas':'Campanhas para você')+'</h3>'+
 (feed.items.length?'<div class="s2-campaign-grid">'+feed.items.map(x=>stage2CampaignCard(x,adminMode)).join('')+'</div>':stage2Empty('Nenhuma campanha nova publicada para este perfil.'))+
 (old.items.length?'<section class="card"><h3>Publicações anteriores</h3><div class="s2-campaign-grid">'+old.items.map(x=>stage2CampaignCard(x,adminMode,true)).join('')+'</div></section>':'');
 if(adminMode){
  const form=document.getElementById('s2CampaignForm');
  const resetCampaignEdit=()=>{
   form.reset();delete form.dataset.editId;
   document.getElementById('s2CampaignFormTitle').textContent='Nova campanha ou banner';
   document.getElementById('s2CampaignEditHint').textContent='Você pode salvar como rascunho e publicar depois. Campanhas existentes também podem ser editadas.';
   document.getElementById('s2CampaignSave').textContent='Salvar campanha';
   document.getElementById('s2CampaignCancel').hidden=true;
  };
  document.getElementById('s2CampaignCancel').onclick=resetCampaignEdit;
  form.onsubmit=async e=>{
   e.preventDefault();let b=form.querySelector('[type=submit]');b.disabled=true;
   try{
    const f=new FormData(form),file=f.get('file'),body={
     title:f.get('title'),body:f.get('body'),segment:f.get('segment'),status:f.get('status')
    };
    if(file&&file.size){
     let upload=new FormData();upload.append('file',file);
     const reply=await fetch('/api/program/media',{method:'POST',credentials:'same-origin',
      headers:{'X-Requested-With':'NOVAGENTE-V5'},body:upload});
     let j=await reply.json();
     if(!reply.ok)throw Error(j.detail||'Erro ao enviar mídia');
     body.media_id=j.id;
    }else if(form.dataset.editId&&f.get('remove_media')==='on'){
     body.media_id=null;
    }
    const editing=form.dataset.editId;
    if(editing)await request('program/campaigns/'+editing,body,'PUT');
    else await request('program/campaigns',body);
    msg(editing?'Campanha atualizada. Nenhum WhatsApp foi enviado.':'Campanha salva internamente. Nenhum WhatsApp foi enviado.');
    await stage2Campaigns();
   }catch(err){msg(err.message)}finally{b.disabled=false}
  };
  document.getElementById('body').onclick=async e=>{
   const edit=e.target.closest('[data-edit-campaign]');
   if(edit){
    const c=feed.items.find(x=>String(x.id)===edit.dataset.editCampaign);
    if(!c)return;
    form.dataset.editId=String(c.id);
    for(const k of ['title','body','segment','status'])form.elements.namedItem(k).value=c[k];
    form.elements.namedItem('file').value='';
    form.elements.namedItem('remove_media').checked=false;
    document.getElementById('s2CampaignFormTitle').textContent='Editar campanha #'+c.id;
    document.getElementById('s2CampaignEditHint').textContent=(c.media_id?'A mídia atual será mantida se você não enviar outra. ':'Esta campanha ainda não tem banner. ')+(c.status==='published'?'Atenção: alterações salvas ficam visíveis imediatamente aos motoristas autorizados.':'Ela continuará em rascunho até ser publicada.');
    document.getElementById('s2CampaignSave').textContent='Salvar alterações';
    document.getElementById('s2CampaignCancel').hidden=false;
    form.scrollIntoView({behavior:'smooth',block:'start'});
    return;
   }
   let t=e.target.closest('[data-campaign-id]');if(!t)return;
   if(t.dataset.publish==='published'&&!confirm('Publicar esta campanha somente no sistema para os motoristas autorizados?'))return;
   try{await request('program/campaigns/'+t.dataset.campaignId,{status:t.dataset.publish},'PUT');msg('Estado atualizado');await stage2Campaigns()}
   catch(err){msg(err.message)}
  };
 }
}
