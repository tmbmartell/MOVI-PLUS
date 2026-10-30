(function(){"use strict";
const $=id=>document.getElementById(id);
const pt=n=>"R$ "+(Number(n)/100).toLocaleString("pt-BR",{minimumFractionDigits:2,maximumFractionDigits:2});
async function api(path,method="GET",data){const r=await fetch(path,{method,credentials:"same-origin",cache:"no-store",headers:{"Content-Type":"application/json","X-Requested-With":"NOVAGENTE-V5"},body:data?JSON.stringify(data):undefined});const out=await r.json().catch(()=>({}));if(!r.ok)throw Error(out.detail||"Erro ao consultar");return out}
let pixKey="",dayData;
async function show(){try{
 dayData=await api("/api/driver/pix/day?date="+encodeURIComponent($("day").value));pixKey=dayData.pix_key;
 $("pix-content").hidden=false;$("pix-key").textContent=pixKey;
 $("pix-name").textContent="Titular informado pelo gestor: "+dayData.recipient_name_configured;
 const root=$("turns");root.replaceChildren();
 (dayData.slots||[]).forEach(s=>{
  const row=document.createElement("div");row.className="turn";
  const label=document.createElement("strong");label.textContent=({manha:"Manhã",tarde:"Tarde",noite:"Noite"})[s.slot]+" · "+pt(s.amount_cents);
  const note=document.createElement("p");note.className="note";note.textContent=s.declared_by_driver?"Você informou que já pagou. A confirmação bancária está pendente.":"Previsto para este turno; não é comprovante.";
  const buttons=document.createElement("div");buttons.className="actions";
  const copy=document.createElement("button");copy.type="button";copy.textContent="Copiar solicitação";
  copy.onclick=()=>navigator.clipboard.writeText(s.message).then(()=>{$("day-status").textContent="Mensagem copiada."}).catch(()=>{$("day-status").textContent="Não consegui copiar. Selecione o texto manualmente."});
  const declare=document.createElement("button");declare.type="button";declare.className="gold";declare.textContent=s.declared_by_driver?"Já informado":"Informar que paguei";declare.disabled=!!s.declared_by_driver;
  declare.onclick=async()=>{if(!confirm("Você realmente realizou essa transferência no seu banco? Esta declaração não confirma o recebimento."))return;
   try{await api("/api/driver/pix/declare","POST",{date:dayData.day,slot:s.slot});$("day-status").textContent="Pagamento declarado, aguardando conferência bancária.";await show()}catch(e){$("day-status").textContent=e.message}};
  buttons.append(copy,declare);row.append(label,note,buttons);root.append(row)
 });
 $("day-status").textContent="Solicitações programadas. Confira a chave e o titular antes de pagar.";
 const consent=await api("/api/driver/pix/notice-consent");$("notice-consent").checked=!!consent.enabled;
}catch(e){$("pix-content").hidden=true;$("day-status").textContent=e.message}}
$("day").value=new Intl.DateTimeFormat("en-CA",{timeZone:"America/Porto_Velho",year:"numeric",month:"2-digit",day:"2-digit"}).format(new Date());
$("show-day").onclick=show;
$("copy-key").onclick=()=>navigator.clipboard.writeText(pixKey).then(()=>{$("day-status").textContent="Chave Pix copiada."}).catch(()=>{$("day-status").textContent="Não consegui copiar automaticamente."});
$("save-consent").onclick=async()=>{try{let r=await api("/api/driver/pix/notice-consent","PUT",{enabled:$("notice-consent").checked});$("consent-status").textContent=r.enabled?"Escolha registrada. O envio depende da liberação do Clube.":"Avisos desligados."}catch(e){$("consent-status").textContent=e.message}};
show();
})();