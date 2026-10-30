'use strict';
/* Clube do Motorista · conexão WAHA e status; mensagens apenas no piloto de um número vinculado. */
am.splice(3,0,['whatsapp','WhatsApp · Conexão']);
const whatsappOldRender=render;
async function whatsappFixAccountSwitch(err){
 if(!/Acesso restrito|Faça login|Sessão inválida|Acesso temporário expirado/i.test(String(err.message||'')))return false;
 // Another tab may have logged in as motorista, replacing the cookie while this tab
 // still displays the administrator's screen. Query the server instead of overriding roles.
 let session;
 try{session=await request('me')}catch{session=null}
 if(session&&session.user&&session.user.role==='driver'){
  user=session.user;
  tab='finance-agent';
  try{await render();msg('Sua sessão atual é de motorista. Mostrei a conexão na área Meu agente financeiro.')}
  catch(error){msg(error.message)}
  return true;
 }
 if(!session||!session.user){
  user=null;tab='home';login();
  msg('Sua sessão terminou. Entre novamente com a conta correta.');
  return true;
 }
 return false;
}
render=async function(){
 if(!user||user.role!=='admin'||tab!=='whatsapp')return whatsappOldRender();
 nav();
 try{await whatsappPage()}
 catch(e){
  if(await whatsappFixAccountSwitch(e))return;
  $('#body').innerHTML='<div class="card">Não foi possível abrir a configuração: '+safe(e.message)+'</div>';
 }
};
async function whatsappPage(){
 const c=await request('admin/whatsapp-bridge');
 let pilot=null;
 try{pilot=await request('admin/finance-agent/whatsapp')}catch(err){/* Independent pilot status is optional here. */}
 const isSet=c.configured;
 $('#body').innerHTML=heading('WhatsApp do Clube','Confira a conexão já pareada sem precisar escanear QR novamente. O atendimento está restrito ao número do piloto depois da vinculação.')+
 '<div class="grid">'+
  tile('Conector','WAHA','Em preparação')+
  tile('Credenciais',isSet?'Guardadas':'Pendentes','Protegidas no servidor')+
  tile('Mensagens',pilot&&pilot.enabled?'Piloto controlado':'Desativadas',pilot&&pilot.enabled?(pilot.pilot_linked?'1 número de teste vinculado':'Aguardando vínculo do motorista'):'Aguardando liberação')+
  tile('Pix','Desativado','Fora do escopo')+
 '</div>'+
 '<div class="cols"><div class="card"><h3>1. Configuração segura</h3><p class="muted">Informe o endereço da sua instância WAHA e uma chave de API específica. Use localhost, HTTPS público ou o endereço Tailscale da sua infraestrutura.</p>'+
 '<form id="waConfig" class="stack"><div><label>Provedor</label><input value="WAHA · conexão via QR" disabled></div>'+
 '<div><label>Endereço do WAHA</label><input type="url" name="base_url" maxlength="220" placeholder="http://127.0.0.1:3000" value="'+safe(c.base_url)+'" autocomplete="off" required><span class="muted">Somente URL-base. Nunca cole token ou senha na URL.</span></div>'+
 '<div><label>Nome da sessão exclusiva</label><input name="session" pattern="[a-z][a-z0-9_-]{2,39}" minlength="3" maxlength="40" value="'+safe(c.session||'clube-motorista')+'" required><span class="muted">Não utilize default ou main para evitar conflito com outros agentes.</span></div>'+
 '<div><label>Chave X-Api-Key do WAHA</label><input type="password" name="api_key" minlength="8" maxlength="250" placeholder="'+(c.api_key_set?'Chave salva · deixe em branco para manter':'Cole a chave da sua instância')+'" autocomplete="new-password" '+(c.api_key_set?'':'required')+'><span class="muted">'+(c.api_key_set?'Uma chave está guardada de forma criptografada. Não é exibida novamente.':'A chave não será exibida nas telas após o salvamento.')+'</span></div>'+
 '<div class="row"><button type="submit" class="btn">Salvar configuração</button><button type="button" class="btn-lite btn-red" id="waRemove">Limpar configuração</button></div></form></div>'+
 '<div class="card"><h3>2. Emparelhamento sob seu controle</h3><div class="notice">É necessário ter a instância WAHA configurada, com a sessão exclusiva para este projeto. Cada etapa depende de um clique seu.</div>'+
 '<div id="waState"><div class="tag">Situação: '+(isSet?'Configuração guardada':'Aguardando configuração')+'</div></div>'+
 '<div class="notice"><b>Já fez o pareamento?</b> Clique em <b>Verificar conexão e sessão</b>. Se aparecer WORKING, não use Criar, Iniciar nem Mostrar QR. Essas opções servem apenas para configuração inicial.</div>'+
 '<div class="stack"><button type="button" id="waCheck" class="btn-lite" '+(isSet?'':'disabled')+'>Verificar conexão e sessão</button>'+
 '<button type="button" id="waCreate" class="btn-lite" '+(isSet?'':'disabled')+'>Criar sessão do Clube (parada)</button>'+
 '<button type="button" id="waStart" class="btn-lite" '+(isSet?'':'disabled')+'>Iniciar sessão para emparelhar</button>'+
 '<button type="button" id="waQR" class="btn" '+(isSet?'':'disabled')+'>Mostrar QR Code temporário</button>'+
 '<button type="button" id="waRefresh" class="btn-lite" '+(isSet?'':'disabled')+'>Renovar QR travado (apenas sessão desconectada)</button></div>'+
 '<div class="notice">Se está usando apenas o celular, pode vincular pelo código. O telefone não é armazenado pelo MOVI+.</div>'+
 '<div class="stack"><label>Telefone do WhatsApp a vincular (DDI + DDD + número, só algarismos)</label>'+
 '<input id="waPhoneNumber" type="tel" inputmode="tel" maxlength="16" placeholder="55 + DDD + telefone" autocomplete="off">'+
 '<button type="button" id="waCode" class="btn-lite" '+(isSet?'':'disabled')+'>Gerar código de pareamento</button></div>'+
 '<div id="waQRArea" class="wa-qr-area"></div></div></div>'+
 '<div class="card"><h3>3. Próximo passo para testar</h3><div class="wa-steps"><div><span>01</span><b>Verificar sessão</b><p>O estado WORKING confirma que a WAHA está pareada.</p></div><div><span>02</span><b>Entrar como motorista de teste</b><p>Na aba Agente financeiro, autorize o uso do agente e gere o código individual.</p></div><div><span>03</span><b>Vincular número do piloto</b><p>Envie VINCULAR e o código do seu WhatsApp de teste para o número pareado do Clube.</p></div></div>'+
 '<div class="notice warn"><b>Somente o piloto autorizado.</b> Até o vínculo, o Clube não responde a nenhum número. Não existem campanhas automáticas ou transferências Pix.</div></div>';
 const form=$('#waConfig');
 form.onsubmit=async e=>{
  e.preventDefault();
  const btn=form.querySelector('[type=submit]');btn.disabled=true;
  try{
   let f=new FormData(form),d={provider:'WAHA',base_url:f.get('base_url'),session:f.get('session'),api_key:f.get('api_key')};
   await request('admin/whatsapp-bridge',d,'PUT');msg('Configuração salva com proteção de credenciais.');await whatsappPage();
  }catch(err){msg(err.message)}finally{btn.disabled=false}
 };
 $('#waRemove').onclick=async()=>{
  if(!isSet)return msg('Não existe configuração salva.');
  if(!confirm('Remover as credenciais locais do Clube? Isso não desconectará nem apagará uma sessão WAHA existente.'))return;
  try{await request('admin/whatsapp-bridge',undefined,'DELETE');msg('Configuração local removida.');await whatsappPage()}catch(err){msg(err.message)}
 };
 function setState(html){$('#waState').innerHTML=html}
 function busy(button,value){button.disabled=value}
 async function action(id,path,confirmText,fn){
  const btn=$(id);btn.onclick=async()=>{
   if(confirmText&&!confirm(confirmText))return;
   busy(btn,true);
   $('#waQRArea').replaceChildren();
   try{
    const d=await request('admin/whatsapp-bridge/'+path,{});
    fn(d);
   }catch(err){
    if(await whatsappFixAccountSwitch(err))return;
    setState('<div class="notice warn">'+safe(err.message)+'</div>');msg(err.message)
   }finally{busy(btn,false)}
  };
 }
 action('#waCheck','check',null,d=>{
  setState('<div class="notice"><b>Provedor: '+(d.provider_reachable?'Acessível':'Não acessível')+'</b><br>Sessão: '+safe(d.session_exists?d.status:'Ainda não criada')+
   '<br>Conectado: '+(d.connected?'Sim':'Não')+
   (d.connected?'<br><strong>Tudo certo! Você não precisa parear de novo.</strong>':'<br>Aguarde alguns segundos se a sessão estiver iniciando.')+'</div>');
  if(d.connected){
   $('#waCreate').disabled=true;
   $('#waStart').disabled=true;
   $('#waQR').disabled=true;
  }
 });
 action('#waCreate','create','Criar uma sessão EXCLUSIVA e parada no servidor WAHA configurado?',d=>{
  setState('<div class="notice"><b>Sessão preparada.</b> Ela permanece parada até você clicar em Iniciar.</div>');msg('Sessão preparada sem mensagens.');
 });
 action('#waStart','start','Iniciar esta sessão WAHA para permitir emparelhamento? Nenhuma mensagem será enviada.',d=>{
  setState('<div class="notice"><b>Iniciada para emparelhamento.</b> Espere alguns segundos e abra o QR Code.</div>');msg('Sessão iniciada.');
 });
 action('#waRefresh','refresh-qr','Atenção: atualizar o QR reinicia somente a sessão desconectada do Clube. Confirmar?',d=>{
  setState('<div class="notice"><b>Renovação solicitada.</b> Verifique o status e, quando indicar SCAN_QR_CODE, clique em Mostrar QR Code.</div>');
  msg('QR anterior invalidado. Exiba o novo QR após a sessão iniciar.');
 });
 $('#waCode').onclick=async()=>{
  const number=$('#waPhoneNumber').value.trim().replace(/^\+/,'');
  if(!/^[0-9]{10,15}$/.test(number))return msg('Digite DDI, DDD e telefone, usando apenas números.');
  const btn=$('#waCode');btn.disabled=true;
  $('#waQRArea').replaceChildren();
  try{
   const d=await request('admin/whatsapp-bridge/request-code',{phone_number:number});
   $('#waPhoneNumber').value='';
   const area=$('#waQRArea');
   const heading=document.createElement('h4');heading.textContent='Código temporário de pareamento';
   const code=document.createElement('p');code.className='wa-pairing-code';
   code.style.cssText='font:700 1.65rem monospace;letter-spacing:.14em;text-align:center';
   code.textContent=d.code;
   const help=document.createElement('p');
   help.textContent='No celular: WhatsApp → Aparelhos conectados → Conectar aparelho → Vincular com número de telefone. Digite o código e depois clique em Verificar conexão e sessão.';
   area.append(heading,code,help);
  }catch(err){msg(err.message)}
  finally{btn.disabled=false}
 };
 action('#waQR','qr',null,d=>{
  const area=$('#waQRArea');
  const h=document.createElement('h4');h.textContent='Escaneie no WhatsApp';
  const img=document.createElement('img');img.src=d.data_url;img.alt='QR Code temporário para emparelhar o WhatsApp do Clube do Motorista';
  img.referrerPolicy='no-referrer';
  const p=document.createElement('p');p.textContent='WhatsApp → Aparelhos conectados → Conectar aparelho. O QR expira rapidamente; use o botão novamente se necessário.';
  area.append(h,img,p);
 });
}
