'use strict';
const $=s=>document.querySelector(s), safe=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])),brl=v=>Number(v||0).toLocaleString('pt-BR',{style:'currency',currency:'BRL'});
let user=null,tab='home',fields=[],sensitive=false;
async function request(path,data,method){
 const o={credentials:'same-origin',headers:{}};
 if(data!==undefined){o.method=method||'POST';o.headers={'Content-Type':'application/json','X-Requested-With':'NOVAGENTE-V5'};o.body=JSON.stringify(data);}
 if(method==='DELETE'){o.method='DELETE';o.headers={'X-Requested-With':'NOVAGENTE-V5'};}
 const res=await fetch('/api/'+path,o);let j={};try{j=await res.json()}catch{}
 if(!res.ok)throw Error(j.detail||j.error||'Falha');
 return j;
}
function msg(t){const el=$('#toast');el.textContent=t;el.style.display='block';setTimeout(()=>el.style.display='none',4000)}
function heading(t,sub=''){return '<div class="eyebrow">CLUBE DO MOTORISTA / '+(user.role==='admin'?'GESTÃO':'MOTORISTA')+'</div><h2>'+safe(t)+'</h2><p class="muted">'+safe(sub)+'</p>'}
function tile(label,value,note=''){return '<div class="tile"><div class="eyebrow">'+safe(label)+'</div><div class="value">'+safe(value)+'</div><span class="muted">'+safe(note)+'</span></div>'}
function bind(id,fn){let form=$('#'+id);if(!form)return;form.onsubmit=async e=>{e.preventDefault();const b=form.querySelector('[type=submit]');if(b)b.disabled=true;try{await fn(new FormData(form))}catch(err){msg(err.message)}finally{if(b)b.disabled=false}}}
function login(mode='login'){
 if(mode==='login' && new URLSearchParams(location.search).has('convite'))mode='enroll';
 user=null;
 $('#app').innerHTML='<div class="login"><section class="hero"><div class="eyebrow" style="color:#b9ddc6">CLUBE DO MOTORISTA · ÁREA FINANCEIRA</div><h1>Seu dinheiro, sob controle.</h1><p>Organize corridas, acompanhe despesas e planeje o próximo carro com mais clareza.</p><p class="more" style="color:#bad4c6">Gestão financeira pessoal · Diagnóstico socioeconômico · Metas de renda</p></section><section class="auth"><div class="authmain"><div class="brand">CLUBE DO MOTORISTA ↗</div><p class="muted">Ambiente individual de acompanhamento financeiro</p><div class="row" style="justify-content:start;margin:15px 0"><button id="tabLogin" class="btn-lite">Entrar</button><button id="tabEnroll" class="btn-lite">Tenho convite</button></div><div class="card" id="authform"></div><div class="notice warn">Não há movimentação bancária. Dados pessoais e documentos só podem ser cadastrados após autorização específica; a segurança e a publicação definitiva ainda estão em homologação.</div></div></section></div>';
 $('#tabLogin').onclick=()=>paintLogin('login');$('#tabEnroll').onclick=()=>paintLogin('enroll');paintLogin(mode);
}
function paintLogin(mode){
 if(mode==='login'){
 $('#authform').innerHTML='<h3>Acesse sua conta</h3><form id="loginForm" class="stack"><div><label>Usuário</label><input name="username" autocomplete="username" required></div><div><label>Senha</label><input name="password" type="password" autocomplete="current-password" required></div><div><label>Código de autenticação (somente se ativou a proteção de 2 etapas)</label><input name="otp" maxlength="70" autocomplete="one-time-code" placeholder="6 dígitos ou código de recuperação"></div><button class="btn" type="submit">Entrar</button></form>';
 bind('loginForm',async f=>{await request('login',{username:f.get('username'),password:f.get('password'),otp:f.get('otp')||''});tab='home';await bootstrap()});
 }else{
 let token=new URLSearchParams(location.search).get('convite')||'';
 $('#authform').innerHTML='<h3>Cadastro por convite</h3><form id="enrollForm" class="stack"><div><label>Código de convite</label><input name="invite" value="'+safe(token)+'" required></div><div><label>Nome de exibição</label><input name="name" required></div><div><label>Usuário (4 a 32 letras/números)</label><input name="username" pattern="[a-z0-9_]{4,32}" required></div><div><label>Senha própria (14+ caracteres, letras e números)</label><input name="password" type="password" minlength="14" required></div><label><input name="accepted_rules" type="checkbox" required> Estou ciente de que o sistema não movimenta meu dinheiro e que meu acesso depende de aprovação.</label><button class="btn" type="submit">Solicitar acesso</button></form>';
 bind('enrollForm',async f=>{await request('enroll',{invite:f.get('invite'),name:f.get('name'),username:f.get('username'),password:f.get('password'),accepted_rules:f.has('accepted_rules')});if(typeof ngLandingPaintLogin==='function'&&document.getElementById('ng-auth-modal')){history.replaceState(null,'',location.pathname);ngLandingPaintLogin('login')}else paintLogin('login');msg('Cadastro solicitado. Aguarde aprovação do gestor.')});
 }
}
const dm=[['home','Painel'],['form','Cadastro'],['interview','Conversa guiada'],['finances','Ganhos e despesas'],['consents','Autorizações'],['documents','Documentos'],['campaigns','Novidades'],['settings','Conta']];
const am=[['home','Painel'],['drivers','Motoristas'],['invites','Convites'],['campaigns','Campanhas'],['privacy','Privacidade'],['audit','Auditoria'],['settings','Conta']];
function nav(){
 let links=user.role==='admin'?am:dm;if(!links.some(x=>x[0]===tab))tab='home';
 $('#app').innerHTML='<div class="top"><b class="brand">CLUBE DO MOTORISTA</b><div class="row"><span class="more" style="color:#bed9c6">'+safe(user.name)+'</span><button id="logout" class="btn-lite btn-sm">Sair</button></div></div><div class="shell"><nav>'+links.map(x=>'<button data-tab="'+x[0]+'" class="'+(x[0]===tab?'active':'')+'">'+safe(x[1])+'</button>').join('')+'</nav><main id="body"></main></div><footer class="app-system-footer"><span class="app-credit-brand">SISTEMA NOVAGENTE</span><span class="app-credit-version">2026 · V7</span></footer>';
 $('#logout').onclick=async()=>{try{await request('logout',{})}catch{}tab='home';login()};
 $('nav').onclick=e=>{let t=e.target.closest('[data-tab]');if(t){tab=t.dataset.tab;render()}};
}
function inputFor(f,answers={}){
 let name=safe(f.key),value=answers[f.key]??'';
 let label='<label>'+safe(f.label)+(f.required_in_source?' *':'')+'</label>';
 if(f.protected&&!sensitive)return '<div class="datafield locked">'+label+'<input disabled placeholder="Pendente de ambiente seguro"><span class="muted">Coleta temporariamente bloqueada</span></div>';
 let box='';
 if(f.type==='file')box='<div class="notice">O anexo é feito na seção Documentos.</div>';
 else if(f.type==='select')box='<select name="'+name+'"><option value="">Selecione</option>'+f.options.map(x=>'<option '+(x===value?'selected':'')+'>'+safe(x)+'</option>').join('')+'</select>';
 else if(f.type==='multi')box='<div class="opts">'+f.options.map(x=>'<label><input type="checkbox" name="'+name+'" value="'+safe(x)+'" '+(Array.isArray(value)&&value.includes(x)?'checked':'')+'>'+safe(x)+'</label>').join('')+'</div>';
 else if(f.type==='textarea')box='<textarea name="'+name+'" maxlength="350">'+safe(value)+'</textarea>';
 else box='<input name="'+name+'" type="'+(f.type==='date'?'date':f.type==='email'?'email':f.type==='number'||f.type==='money'?'number':'text')+'" '+(f.type==='number'||f.type==='money'?'min="0" step="'+(f.type==='money'?'0.01':'1')+'"':'')+' value="'+safe(value)+'">';
 return '<div class="datafield">'+label+box+'</div>';
}
function fieldsData(form,arr){
 const f=new FormData(form),d={};
 arr.forEach(x=>{if(x.type==='file'||x.protected&&!sensitive)return;d[x.key]=x.type==='multi'?f.getAll(x.key):String(f.get(x.key)||'')});
 return d;
}
async function bootstrap(){
 const m=await request('me');user=m.user;sensitive=m.limits.sensitive;
 if(!user)return login();
 if(user.must_change)tab='settings';
 else if(user.role==='driver')fields=(await request('schema')).fields;
 await render();
 if(user.must_change)msg('Troque sua senha inicial para liberar as demais funções.');
}
async function driverHome(){
 const [p,fin]=await Promise.all([request('profile'),request('finances')]);
 const x=fin.summary;
 $('#body').innerHTML=heading('Bem-vindo ao seu clube','Acompanhe sua evolução com informações registradas por você.')+
 '<div class="grid">'+tile('Entradas',brl(x.income),'Lançamentos manuais')+tile('Despesas',brl(x.expense),'Lançamentos manuais')+tile('Resultado parcial',brl(x.partial),'Não é saldo bancário')+tile('Cadastro',p.progress.percent+'%','Campos disponíveis')+'</div>'+
 '<div class="cols"><div class="card"><h3>Planejamento financeiro</h3>'+(x.estimate?'<div class="detailgrid"><div>Receita mensal estimada<br><b>'+brl(x.estimate.revenue)+'</b></div><div>Combustível estimado<br><b>'+brl(x.estimate.fuel)+'</b></div><div>Outras despesas<br><b>'+brl(x.estimate.other)+'</b></div><div>Restante estimado<br><b>'+brl(x.estimate.remaining)+'</b></div></div>':'<p>Registre o ganho diário, combustível e dias de trabalho por semana para calcular uma projeção mensal.</p>')+'<div class="notice">'+safe(x.note)+'</div></div>'+
 '<div class="card"><h3>Continue seu cadastro</h3><div class="progress"><b style="width:'+p.progress.percent+'%"></b></div><p class="muted">'+p.progress.completed+' de '+p.progress.total+' campos disponíveis.</p><button class="btn" id="openForm">Completar cadastro</button><hr><h3>Sua privacidade</h3><p class="muted">O gestor só recebe seu diagnóstico detalhado se você autorizar.</p><button class="btn-lite" id="openConsents">Autorizações</button></div></div>';
 $('#openForm').onclick=()=>{tab='form';render()};$('#openConsents').onclick=()=>{tab='consents';render()};
}
async function form(){
 let p=await request('profile');
 let original=fields.filter(x=>x.source==='original'),extra=fields.filter(x=>x.source==='complementar');
 $('#body').innerHTML=heading('Cadastro socioeconômico','23 perguntas originais preservadas e 15 questões financeiras adicionais.')+
 '<div class="card"><div class="row"><h3>Seu progresso</h3><span class="tag">'+p.progress.percent+'%</span></div><div class="progress"><b style="width:'+p.progress.percent+'%"></b></div><p class="muted">'+p.progress.completed+' de '+p.progress.total+' campos disponíveis.</p><div class="notice warn">Dados de identificação e CNH estão previstos, mas não são coletados nesta etapa.</div><form id="profileForm"><hr><h3>01 · Formulário original</h3><div class="fields">'+original.map(x=>inputFor(x,p.answers)).join('')+'</div><hr><h3>02 · Diagnóstico complementar</h3><div class="fields">'+extra.map(x=>inputFor(x,p.answers)).join('')+'</div><hr><button type="submit" class="btn">Salvar respostas</button></form></div>';
 bind('profileForm',async()=>{await request('profile',fieldsData($('#profileForm'),fields),'PUT');msg('Dados registrados');render()});
}

async function interview(){
 const d=await request('profile/next'),f=d.question;
 $('#body').innerHTML=heading('Conversa guiada','O agente faz uma pergunta de cada vez, dentro do sistema.')+
 '<div class="cols"><div class="card"><div class="row"><h3>Próxima pergunta</h3><span class="tag">'+d.progress.percent+'% concluído</span></div><div class="progress"><b style="width:'+d.progress.percent+'%"></b></div><hr>'+(f?'<div class="bubble">'+safe(f.label)+'</div><form id="questionForm" class="stack">'+inputFor({...f,label:'Sua resposta',required_in_source:false},{})+'<div class="row"><button class="btn" type="submit">Responder</button><button class="btn-lite" id="skip" type="button">Depois</button></div></form>':'<p class="notice">Todas as perguntas disponíveis foram respondidas ou deixadas para depois.</p>')+'</div><div class="card"><h3>Você decide o ritmo</h3><p class="muted">As respostas ficam no seu cadastro. Não existe disparo de mensagens para WhatsApp nesta versão.</p></div></div>';
 if(f){
  bind('questionForm',async fd=>{let value=f.type==='multi'?fd.getAll(f.key):fd.get(f.key);if(f.type==='multi'&&!value.length)return msg('Selecione uma opção');await request('profile/answer',{key:f.key,value});await render()});
  $('#skip').onclick=async()=>{try{await request('profile/answer',{key:f.key,skip:true});render()}catch(e){msg(e.message)}};
 }
}
async function finances(){
 let d=await request('finances'),s=d.summary;
 $('#body').innerHTML=heading('Ganhos e despesas','Registros inseridos manualmente, sem conta bancária conectada.')+
 '<div class="notice"><a href="/meu-fluxo">Abrir meu fluxo financeiro mensal</a> — veja o resumo visual dos seus registros e compromissos informados.</div>'+
 '<div class="grid">'+tile('Entradas',brl(s.income))+tile('Saídas',brl(s.expense))+tile('Resultado parcial',brl(s.partial))+tile('Registros',d.items.length)+'</div>'+
 '<div class="cols"><div class="card"><h3>Registrar movimentação</h3><form id="financeForm" class="stack"><div class="fields"><div><label>Tipo</label><select name="kind"><option value="income">Receita</option><option value="expense">Despesa</option></select></div><div><label>Categoria</label><select name="category"><option>APLICATIVO</option><option>OUTROS</option><option>Corridas Uber</option><option>Corridas 99</option><option>Corridas Urbano Norte</option><option>Combustível</option><option>Manutenção</option><option>Alimentação</option><option>Parcela do carro</option><option>Seguro</option><option>Outras despesas</option></select></div><div><label>Valor em reais</label><input type="number" name="amount" min=".01" step=".01" required></div><div><label>Data</label><input type="date" name="date" required value="'+new Date().toISOString().slice(0,10)+'"></div></div><div><label>Observação</label><input name="note"></div><button class="btn" type="submit">Salvar lançamento</button></form><div class="notice">'+safe(s.note)+'</div></div><div class="card"><h3>Extrato manual</h3><div class="scroll"><table><tr><th>Data</th><th>Categoria</th><th>Valor</th><th></th></tr>'+d.items.map(x=>'<tr><td>'+safe(x.entry_date)+'</td><td>'+safe(x.category)+'</td><td>'+brl(x.amount)+'</td><td><button class="btn-lite btn-sm btn-red" data-del="'+x.id+'">Excluir</button></td></tr>').join('')+'</table></div>'+(d.items.length?'':'<p class="muted">Nenhum lançamento informado ainda.</p>')+'</div></div>';
 bind('financeForm',async f=>{await request('finances',{kind:f.get('kind'),category:f.get('category'),amount:f.get('amount'),date:f.get('date'),note:f.get('note')});msg('Movimentação salva');render()});
 $('#body').onclick=async e=>{let el=e.target.closest('[data-del]');if(!el)return;if(!confirm('Excluir esse lançamento?'))return;try{await request('finances/'+el.dataset.del,undefined,'DELETE');render()}catch(err){msg(err.message)}};
}
async function consents(){
 const d=await request('consents'),c=d.choices;
 const labels=[['insights','Autorizo o gestor a analisar meu cadastro e meus indicadores financeiros.'],['marketing','Quero visualizar ofertas e campanhas facultativas.'],['sharing','Autorizo compartilhamento adicional com parceiros, sujeito a finalidade específica.'],['documents','Autorizo eventual consulta administrativa de meus documentos, quando habilitados.'],['assisted_entry','Autorizo o gestor a preencher e corrigir minhas respostas socioeconômicas, em meu nome, conforme as outras autorizações concedidas.'],['identity_collection','Autorizo o cadastro e o armazenamento criptografado dos meus dados de identificação (nome, CPF, RG, data de nascimento, contato, endereço, placa e CNH) para o Programa de Renovação de Frota. Posso retirar esta autorização.']];
 $('#body').innerHTML=heading('Privacidade e autorizações','Seis autorizações independentes e alteráveis a qualquer momento.')+
 '<div class="notice"><b>Para liberar os campos do cadastro:</b> ative a opção de identificação pessoal abaixo e clique em Salvar escolhas. A partir daí, volte em Cadastro → Identificação e documentos. A autorização para o gestor editar é separada. Os dados são criptografados e não são enviados por WhatsApp.</div>'+
 '<div class="cols"><div class="card"><form id="consentForm" class="stack">'+
 '<div class="consent-select-all"><label for="consentAll"><input id="consentAll" type="checkbox"> <strong>Marcar todas as 6 autorizações</strong></label>'+
 '<button id="consentClear" type="button" class="btn-lite btn-sm">Desmarcar todas</button>'+
 '<p id="consentSelectedCount" class="muted" role="status" aria-live="polite"></p>'+
 '<p class="muted">Esta escolha inclui ofertas facultativas e compartilhamento adicional com parceiros. Leia cada autorização antes de salvar; você pode alterar qualquer uma separadamente.</p></div>'+
 labels.map(x=>'<label class="consent-choice" style="font-weight:500"><input type="checkbox" name="'+x[0]+'" '+(c[x[0]]?'checked':'')+'>'+safe(x[1])+'</label>').join('')+
 '<button type="submit" class="btn">Salvar escolhas</button></form></div>'+
 '<div class="card"><h3>Controle dos seus dados</h3><p class="muted">Você pode baixar suas respostas e solicitar a exclusão de seus registros.</p><button class="btn-lite" id="downloadData">Exportar meu cadastro</button><hr><button class="btn-lite btn-red" id="erase">Solicitar exclusão</button></div></div>';
 const consentForm=$('#consentForm');
 const consentAll=$('#consentAll');
 const consentBoxes=labels.map(([name])=>consentForm.elements.namedItem(name));
 const syncConsentAll=()=>{
  const marked=consentBoxes.filter(input=>input.checked).length;
  consentAll.checked=marked===consentBoxes.length;
  consentAll.indeterminate=marked>0&&marked<consentBoxes.length;
  $('#consentSelectedCount').textContent=marked+' de '+consentBoxes.length+' autorizações selecionadas. As mudanças só serão aplicadas quando você clicar em Salvar escolhas.';
 };
 consentAll.onchange=()=>{
  consentBoxes.forEach(input=>{input.checked=consentAll.checked});
  syncConsentAll();
 };
 $('#consentClear').onclick=()=>{
  consentBoxes.forEach(input=>{input.checked=false});
  syncConsentAll();
 };
 consentBoxes.forEach(input=>input.addEventListener('change',syncConsentAll));
 syncConsentAll();
 bind('consentForm',async f=>{
 let x={};labels.forEach(y=>x[y[0]]=f.has(y[0]));
 if(x.identity_collection&&!c.identity_collection){
  if(!confirm('Confirma que deseja liberar o preenchimento de documentos e dados pessoais de identificação? Eles serão armazenados de forma criptografada neste sistema de testes.'))return;
 }
 await request('consents',x,'PUT');
 if(x.identity_collection!==Boolean(c.identity_collection))fields=(await request('schema')).fields;
 msg('Autorizações atualizadas. '+(x.identity_collection?'Campos de identificação liberados no seu cadastro.':'Dados de identificação bloqueados para novos envios.'));
 render();
});
 $('#downloadData').onclick=async()=>{try{let x=await request('privacy/export'),blob=new Blob([JSON.stringify(x,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='novagente_meus_dados.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1500)}catch(e){msg(e.message)}};
 $('#erase').onclick=async()=>{if(!confirm('Solicitar exclusão dos seus dados?'))return;try{await request('privacy/delete-request',{});msg('Solicitação enviada ao gestor')}catch(e){msg(e.message)}};
}
async function documents(){
 let d=await request('documents');
 $('#body').innerHTML=heading('Meus documentos','Área de documentação protegida por acesso individual.')+
 '<div class="cols"><div class="card"><h3>Identificação e CNH</h3>'+(d.enabled?'<div class="notice">Você autorizou o cadastro de identificação. Anexe somente documentos necessários ao programa (PDF, JPG ou PNG, até 8 MB). O arquivo é guardado criptografado e não será publicado.</div><form id="uploadForm" class="stack"><input type="file" accept=".pdf,.jpg,.jpeg,.png" name="file" required><button type="submit" class="btn">Anexar documento</button></form>':'<div class="notice warn">Para desbloquear o envio da CNH, abra <b>Autorizações</b>, marque <b>Cadastro de identificação pessoal</b> e salve sua escolha.</div><button type="button" id="docAuthorize" class="btn">Abrir Autorizações</button>')+'</div><div class="card"><h3>Arquivos protegidos</h3>'+(d.items.length?d.items.map(x=>'<p><a href="/api/documents/'+safe(x.id)+'">Documento de '+safe(x.at)+'</a></p>').join(''):'<p class="muted">Nenhum documento armazenado.</p>')+'</div></div>';
 if($('#docAuthorize'))$('#docAuthorize').onclick=()=>{tab='consents';render()};
 if($('#uploadForm'))$('#uploadForm').onsubmit=async e=>{e.preventDefault();try{let r=await fetch('/api/documents',{method:'POST',body:new FormData(e.target),headers:{'X-Requested-With':'NOVAGENTE-V5'},credentials:'same-origin'});if(!r.ok)throw Error((await r.json()).detail);msg('Arquivo salvo');render()}catch(err){msg(err.message)}};
}
async function campaigns(){
 let d=await request('campaigns');
 $('#body').innerHTML=heading('Campanhas internas','Publicações dentro do sistema, sem envios externos.')+
 '<div class="cols">'+(user.role==='admin'?'<div class="card"><h3>Criar campanha</h3><form id="campForm" class="stack"><div><label>Título</label><input name="title" required></div><div><label>Mensagem</label><textarea name="body" required></textarea></div><div><label>Estado</label><select name="status"><option value="draft">Rascunho</option><option value="published">Publicar</option></select></div><button type="submit" class="btn">Salvar campanha</button></form></div>':'<div class="card"><h3>Suas novidades</h3><p class="muted">Somente para participantes que autorizam campanhas.</p></div>')+
 '<div class="card"><h3>Publicações</h3>'+(d.items.length?d.items.map(x=>'<div><span class="tag">'+safe(x.status)+'</span><h3>'+safe(x.title)+'</h3><p>'+safe(x.body)+'</p><hr></div>').join(''):'<p class="muted">Nenhuma publicação disponível.</p>')+'</div></div>';
 bind('campForm',async f=>{await request('admin/campaigns',{title:f.get('title'),body:f.get('body'),status:f.get('status')});msg('Salva internamente');render()});
}
async function settings(){
 $('#body').innerHTML=heading('Minha conta','Proteja o acesso à sua área pessoal.')+
 '<div class="card" style="max-width:520px"><h3>Atualizar senha</h3><form id="pwdForm" class="stack"><div><label>Senha atual</label><input type="password" name="current" required></div><div><label>Nova senha (14+ caracteres, letras e números)</label><input type="password" name="new" minlength="14" required></div><button class="btn" type="submit">Alterar senha</button></form></div>';
 bind('pwdForm',async f=>{await request('password',{current:f.get('current'),new:f.get('new')});user.must_change=0;msg('Senha atualizada');tab='home';render()});
}

async function adminHome(){
 let d=await request('admin/overview');
 $('#body').innerHTML=heading('Painel do gestor','Gerencie cadastros, consentimentos e programas de acompanhamento.')+
 '<div class="grid">'+tile('Motoristas',d.items.length,'Cadastros')+tile('Ativos',d.items.filter(x=>x.status==='active').length)+tile('Pendentes',d.pending,'Aprovação humana')+tile('Análises autorizadas',d.authorized)+'</div>'+
 '<div class="cols"><div class="card"><h3>Próximos passos</h3><p>1. Gerar convites de acesso.</p><p>2. Aprovar os motoristas cadastrados.</p><p>3. Acompanhar somente diagnósticos autorizados.</p><p>4. Revisar documentação jurídica antes da coleta de CPF e CNH.</p><button class="btn" id="jump">Convites e aprovações</button></div><div class="card"><h3>Integrações</h3><div class="notice">Ganhos e despesas: registro manual ativo.</div><div class="notice">WhatsApp e API bancária: não configurados.</div><div class="notice warn">Coleta pessoal protegida: bloqueada nesta etapa.</div></div></div>';
 $('#jump').onclick=()=>{tab='invites';render()};
}
async function adminDrivers(){
 let d=await request('admin/overview'),list=d.items;
 fields=(await request('schema')).fields;
 $('#body').innerHTML=heading('Base de motoristas','Consulta de informações detalhadas condicionada ao consentimento.')+
 '<div class="card"><div class="fields"><div><label>Nome ou usuário</label><input id="searchDriver"></div><div><label>Plataforma</label><select id="filterPlatform"><option value="">Todas</option>'+[...new Set(list.map(x=>x.platform).filter(Boolean))].map(x=>'<option>'+safe(x)+'</option>').join('')+'</select></div><div><label>Status</label><select id="filterStatus"><option value="">Todos</option><option>active</option><option>pending</option><option>suspended</option></select></div><div><label>Análise autorizada?</label><select id="filterConsent"><option value="">Todos</option><option value="yes">Sim</option><option value="no">Não</option></select></div></div><hr><div class="row"><h3>Participantes</h3><a class="btn-lite" href="/api/admin/export">Exportar autorizados (CSV)</a></div><div id="driverTable"></div></div><div class="card" id="driverDetails"><h3>Detalhes individuais</h3><p class="muted">Clique num motorista para consultar as informações autorizadas.</p></div>';
 function paint(){
  let name=$('#searchDriver').value.toLowerCase(),p=$('#filterPlatform').value,status=$('#filterStatus').value,auth=$('#filterConsent').value;
  let filtered=list.filter(x=>(x.name+' '+x.username).toLowerCase().includes(name)&&(!p||p===x.platform)&&(!status||status===x.status)&&(!auth||(auth==='yes')===!!x.insights));
  $('#driverTable').innerHTML='<div class="scroll"><table><tr><th>Motorista</th><th>Plataforma</th><th>Status</th><th>Preenchimento</th><th>Análise</th><th></th></tr>'+filtered.map(x=>'<tr><td>'+safe(x.name)+'</td><td>'+safe(x.platform||'Privado')+'</td><td>'+safe(x.status)+'</td><td>'+(x.completion===null?'Oculto':x.completion+'%')+'</td><td>'+safe(x.insights?'Autorizado':'Sem autorização')+'</td><td><button data-driver="'+x.id+'" class="btn-lite btn-sm">Detalhar</button></td></tr>').join('')+'</table></div>';
 }
 ['searchDriver','filterPlatform','filterStatus','filterConsent'].forEach(i=>$('#'+i).addEventListener('input',paint));paint();
 $('#driverTable').onclick=async e=>{
  let b=e.target.closest('[data-driver]');if(!b)return;
  try{let d=await request('admin/driver/'+b.dataset.driver);
   $('#driverDetails').innerHTML='<h3>'+safe(d.driver.name)+'</h3>'+(d.authorized?
   '<div class="grid">'+tile('Receitas',brl(d.summary.income))+tile('Despesas',brl(d.summary.expense))+tile('Resultado',brl(d.summary.partial))+tile('Cadastro',d.completion.percent+'%')+'</div><div class="detailgrid">'+Object.entries(d.answers).filter(([k])=>fields.find(f=>f.key===k)).map(([k,v])=>'<div><span class="muted">'+safe(fields.find(f=>f.key===k).label)+'</span><br><b>'+safe(Array.isArray(v)?v.join(', '):v)+'</b></div>').join('')+'</div><div class="notice">Informações autodeclaradas; não comprovam renda ou crédito.</div>'
   :'<div class="notice warn">O motorista não autorizou análise detalhada.</div>');
   if(d.authorized){
    let slot=document.createElement('div');slot.className='socio-admin-callout';
    slot.innerHTML=d.assisted_entry?'<div class="notice"><b>Preenchimento assistido autorizado.</b> O motorista permitiu que o gestor registre respostas não protegidas em nome dele.</div><button id="socioAdminEdit" class="btn" type="button">Preencher cadastro autorizado</button>':'<div class="notice warn">Para preencher o cadastro pelo gestor, o motorista precisa ativar separadamente as opções <b>Análise socioeconômica</b> e <b>Preenchimento assistido</b> em Autorizações. Nenhum consentimento será ativado automaticamente.</div>';
    $('#driverDetails').appendChild(slot);
    const btn=document.getElementById('socioAdminEdit');if(btn)btn.onclick=()=>socioAdminEdit(Number(b.dataset.driver));
   }
  }catch(err){msg(err.message)}
 };
}
async function invites(){
 let d=await request('admin/overview'),pending=d.items.filter(x=>x.status==='pending');
 $('#body').innerHTML=heading('Convites e aprovações','Código individual, válido por 48 horas e uso único.')+
 '<div class="cols"><div class="card"><h3>Convidar motorista</h3><p class="muted">Você compartilha o link manualmente, sem envios automáticos.</p><button class="btn" id="generate">Gerar convite</button><div id="inviteResult"></div></div><div class="card"><h3>Cadastros aguardando</h3>'+(pending.length?pending.map(x=>'<div class="row"><div><b>'+safe(x.name)+'</b><div class="muted">'+safe(x.username)+'</div></div><button class="btn-lite btn-sm" data-approve="'+x.id+'">Aprovar</button></div><hr>').join(''):'<p class="muted">Nenhum motorista pendente.</p>')+'</div></div>';
 $('#generate').onclick=async()=>{
  try{let result=await request('admin/invites',{});let u=new URL(location.href);u.search='';u.searchParams.set('convite',result.invite);
  $('#inviteResult').innerHTML='<div class="notice"><label>Link individual</label><input id="invLink" readonly value="'+safe(u.toString())+'"><p class="muted">Expira em 48 horas, apenas um cadastro.</p><button class="btn-lite" id="copyLink">Copiar</button></div>';
  $('#copyLink').onclick=async()=>{try{await navigator.clipboard.writeText(u.toString());msg('Link copiado')}catch{msg('Selecione e copie o campo acima')}};
  }catch(err){msg(err.message)}
 };
 $('#body').onclick=async e=>{let b=e.target.closest('[data-approve]');if(!b)return;if(!confirm('Aprovar cadastro?'))return;try{await request('admin/activate/'+b.dataset.approve,{});msg('Acesso aprovado');render()}catch(err){msg(err.message)}};
}
async function privacyAdmin(){
 let d=await request('admin/delete-requests');
 $('#body').innerHTML=heading('Solicitações de privacidade','Pedidos de exclusão são analisados e executados pelo administrador.')+
 '<div class="card"><h3>Solicitações</h3><div class="scroll"><table><tr><th>Motorista</th><th>Data</th><th>Status</th><th>Ação</th></tr>'+d.items.map(x=>'<tr><td>'+safe(x.name)+'</td><td>'+safe(x.at)+'</td><td>'+safe(x.status)+'</td><td><button class="btn-lite btn-red btn-sm" data-erasure="'+x.id+'">Excluir cadastro</button></td></tr>').join('')+'</table></div><div class="notice warn">Verifique obrigações legais de retenção antes da exclusão. Cópias de segurança têm ciclo próprio de retenção.</div></div>';
 $('#body').onclick=async e=>{let b=e.target.closest('[data-erasure]');if(!b)return;if(!confirm('Excluir definitivamente o cadastro no banco ativo?'))return;try{await request('admin/delete-requests/'+b.dataset.erasure+'/complete',{});msg('Exclusão concluída');render()}catch(err){msg(err.message)}};
}
async function auditAdmin(){
 let d=await request('admin/audit');
 $('#body').innerHTML=heading('Auditoria','Eventos sem armazenamento de senhas ou respostas em texto aberto.')+
 '<div class="card"><div class="scroll"><table><tr><th>Ação</th><th>Referência</th><th>Data UTC</th></tr>'+d.items.map(x=>'<tr><td>'+safe(x.action)+'</td><td>'+safe(x.target)+'</td><td>'+safe(x.at)+'</td></tr>').join('')+'</table></div></div>';
}
async function render(){
 if(!user)return login();
 nav();
 try{
  if(tab==='settings')await settings();
  else if(user.role==='admin'){
   if(tab==='home')await adminHome();
   if(tab==='drivers')await adminDrivers();
   if(tab==='invites')await invites();
   if(tab==='campaigns')await campaigns();
   if(tab==='privacy')await privacyAdmin();
   if(tab==='audit')await auditAdmin();
  }else{
   if(tab==='home')await driverHome();
   if(tab==='form')await form();
   if(tab==='interview')await interview();
   if(tab==='finances')await finances();
   if(tab==='consents')await consents();
   if(tab==='documents')await documents();
   if(tab==='campaigns')await campaigns();
  }
 }catch(err){$('#body').innerHTML='<div class="card"><h3>Não foi possível abrir esta área</h3><p>'+safe(err.message)+'</p></div>'}
}
dm.splice(2,0,['chat','Meu consultor']);
async function chatPage(){
 const d=await request('chat');
 $('#body').innerHTML=heading('Meu consultor financeiro','Registre ganhos, despesas e veja seus números por conversa, sem WhatsApp.')+
 '<div class="cols"><div class="card"><h3>Conversa com o assistente</h3><div style="max-height:390px;overflow:auto;padding:12px;background:#f5f9f6;border-radius:14px" id="chatScroll">'+
 (d.items.length?d.items.map(x=>'<div style="margin:10px 0;display:flex;justify-content:'+(x.speaker==='motorista'?'flex-end':'flex-start')+'"><div style="background:'+(x.speaker==='motorista'?'#d9f1dd':'white')+';border-radius:13px;padding:12px;max-width:90%;white-space:pre-wrap">'+safe(x.body)+'</div></div>').join(''):'<div class="bubble">Oi! Me diga quanto você ganhou ou gastou hoje, e eu registro.</div>')+
 '</div><form id="chatForm" class="row" style="margin-top:15px"><input name="text" placeholder="Ex.: Gastei R$ 80 com gasolina" maxlength="400" required style="flex:1;min-width:180px"><button class="btn" type="submit">Enviar</button></form></div>'+
 '<div class="card"><h3>Experimente perguntar</h3><p class="muted">“Ganhei R$ 250 na Uber”</p><p class="muted">“Gastei R$ 75 de gasolina”</p><p class="muted">“Quanto sobrou?”</p><p class="muted">“Qual a minha meta?”</p><div class="notice warn">A interpretação é baseada em regras e não substitui consultoria financeira. Confira os valores registrados na aba Ganhos e despesas.</div></div></div>';
 bind('chatForm',async f=>{let answer=await request('chat',{text:f.get('text')});msg('Registrado no histórico');await chatPage()});
 let el=$('#chatScroll');el.scrollTop=el.scrollHeight;
}
const oldRender=render;
render=async function(){
 if(user&&user.role==='driver'&&tab==='chat'){nav();try{await chatPage()}catch(e){$('#body').innerHTML='<div class="card">'+safe(e.message)+'</div>'};return;}
 return oldRender();
};

document.addEventListener('DOMContentLoaded',()=>bootstrap().catch(e=>{login();msg('Falha de conexão: '+e.message)}));
