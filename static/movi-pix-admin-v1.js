(function(){
"use strict";
const $=id=>document.getElementById(id);
async function api(path,method="GET",data){
  const r=await fetch(path,{method,credentials:"same-origin",cache:"no-store",
    headers:{"Content-Type":"application/json","X-Requested-With":"NOVAGENTE-V5"},
    body:data?JSON.stringify(data):undefined});
  const o=await r.json().catch(()=>({}));
  if(!r.ok)throw Error(o.detail||"Não foi possível concluir a operação");
  return o;
}
const rf=$("receiver-form"),df=$("driver-form"),sf=$("schedule-form");
const field=(form,k)=>form.elements.namedItem(k);
const brl=cents=>"R$ "+(Number(cents)/100).toLocaleString("pt-BR",{minimumFractionDigits:2,maximumFractionDigits:2});
function elem(tag,cls,text){
 const e=document.createElement(tag);if(cls)e.className=cls;
 if(text!==undefined)e.textContent=text;return e;
}
const currentDay=()=>{
 const parts=Object.fromEntries(new Intl.DateTimeFormat("en-US",{timeZone:"America/Porto_Velho",
 year:"numeric",month:"2-digit",day:"2-digit"}).formatToParts(new Date()).map(p=>[p.type,p.value]));
 return parts.year+"-"+parts.month+"-"+parts.day;
};
function reviewPanel(x){
 const section=elem("details","review-item");
 const state=x.review_state||"pending";
 const statuses={pending:"Aguardando conferência","confirmed_manual":"Confirmado manualmente no extrato",
    unmatched:"Divergência / não localizado"};
 section.append(elem("summary","",
   "#"+x.id+" · "+x.entry_day+" · "+x.name+" · "+x.slot+" · "+brl(x.expected_cents)+
   " · "+(statuses[state]||state)));
 if(state==="confirmed_manual")return section;
 const form=elem("form","review-form");
 const decision=elem("select");decision.name="decision";
 [ ["confirmed_manual","Confirmar após conferir crédito"],["unmatched","Divergência / não localizado"] ]
 .forEach(([v,t])=>{const o=new Option(t,v);decision.add(o)});
 const amount=elem("input");amount.name="bank_amount";amount.type="number";
 amount.min="0";amount.step=".01";amount.value=(x.expected_cents/100).toFixed(2);
 const reference=elem("input");reference.name="reference";reference.maxLength=90;
 reference.placeholder="Identificador único do crédito no extrato";
 const day=elem("input");day.type="date";day.name="statement_day";day.value=currentDay();
 const note=elem("input");note.name="note";note.maxLength=240;
 note.placeholder="Observação (obrigatória em divergência)";
 const checked=elem("input");checked.type="checkbox";checked.name="statement_checked";
 const submit=elem("button","gold","Registrar conferência");submit.type="submit";
 function wrap(title,input){const label=elem("label","",title);label.append(input);return label;}
 form.append(wrap("Decisão",decision),wrap("Valor localizado no extrato (R$)",amount),
   wrap("Referência / identificador da transação",reference),
   wrap("Data do crédito",day),wrap("Observação",note),
   wrap("Confirmo que consultei o extrato bancário",checked),submit);
 decision.addEventListener("change",()=>{
   const unmatched=decision.value==="unmatched";
   amount.value=unmatched?"0":(x.expected_cents/100).toFixed(2);
   reference.disabled=unmatched;day.disabled=unmatched;
   if(unmatched){reference.value="";day.value=""}else{day.value=currentDay()}
 });
 form.addEventListener("submit",async event=>{
   event.preventDefault();
   if(!checked.checked){$("review-status").textContent="Confirme a consulta ao extrato antes de registrar.";return}
   if(!window.confirm("A decisão foi realmente conferida no extrato bancário?"))return;
   submit.disabled=true;
   try{
     const payload={decision:decision.value,statement_checked:checked.checked,
      bank_amount:amount.value,reference:reference.value,statement_day:day.value,note:note.value};
     await api("/api/admin/pix/review/"+x.id,"POST",payload);
     $("review-status").textContent="Conferência registrada com auditoria.";
     await load();
   }catch(e){$("review-status").textContent=e.message}
   finally{submit.disabled=false}
 });
 section.append(form);return section;
}
async function load(){
 try{
  const [p,users,review,schedule]=await Promise.all([
    api("/api/admin/pix"),api("/api/admin/pix/drivers"),api("/api/admin/pix/reviews"),
    api("/api/admin/pix/schedule")
  ]);
  for(const slot of ["manha","tarde","noite"]){
    field(sf,slot).value=String(schedule.hours[slot]);
  }
  field(rf,"key").value=p.key||"";
  field(rf,"recipient_name").value=p.recipient_name||"";
  field(rf,"bank_verified").checked=!!p.bank_verified;
  field(rf,"enabled").checked=!!p.enabled;
  $("receiver-status").textContent=p.enabled?
    "Chave ativa para motoristas autorizados.":
    "Chave não liberada: confira a titularidade no aplicativo do banco antes de ativar.";
  const select=$("driver-select");
  const selected=select.value;
  select.replaceChildren(new Option("Selecione um motorista",""));
  (users.items||[]).forEach(u=>{
    const opt=new Option(u.name+" (#"+u.id+")"+(u.monthly_cents?" · "+brl(u.monthly_cents):""),String(u.id));
    opt.dataset.monthly=String(u.monthly_cents||"");
    opt.dataset.active=String(u.active??true);
    select.add(opt);
  });
  select.value=selected;
  select.onchange=()=>{
    const o=select.selectedOptions[0];
    field(df,"monthly_amount").value=o?.dataset.monthly?(Number(o.dataset.monthly)/100).toFixed(2):"";
    field(df,"active").checked=o?.dataset.active!=="0";
  };
  const box=$("declared-list");box.replaceChildren();
  const summary=elem("p","note",
    "Declarações: "+review.count+" · Confirmados manualmente: "+brl(review.confirmed_manually_cents)+
    " · Pendentes: "+review.pending_count+" · Divergências: "+review.unmatched_count);
  box.append(summary);
  if(!(review.items||[]).length){box.append(elem("p","note","Nenhuma declaração registrada."));return}
  review.items.forEach(x=>box.append(reviewPanel(x)));
 }catch(e){$("receiver-status").textContent=e.message}
}
rf.addEventListener("submit",async ev=>{
 ev.preventDefault();
 try{
  await api("/api/admin/pix","PUT",{
   key:field(rf,"key").value,recipient_name:field(rf,"recipient_name").value,
   bank_verified:field(rf,"bank_verified").checked,enabled:field(rf,"enabled").checked});
  $("receiver-status").textContent="Configuração salva.";
  await load();
 }catch(e){$("receiver-status").textContent=e.message}
});
sf.addEventListener("submit",async ev=>{
 ev.preventDefault();
 try{
  const hours=Object.fromEntries(["manha","tarde","noite"].map(slot=>[slot,Number(field(sf,slot).value)]));
  await api("/api/admin/pix/schedule","PUT",hours);
  $("schedule-status").textContent="Horários salvos. Avisos continuam dependendo da autorização e da liberação técnica.";
  await load();
 }catch(e){$("schedule-status").textContent=e.message}
});
df.addEventListener("submit",async ev=>{
 ev.preventDefault();
 try{
  const uid=$("driver-select").value;if(!uid)throw Error("Selecione o motorista");
  await api("/api/admin/pix/driver/"+encodeURIComponent(uid),"PUT",{
    monthly_amount:field(df,"monthly_amount").value,active:field(df,"active").checked});
  $("driver-status").textContent="Parcela configurada.";await load();
 }catch(e){$("driver-status").textContent=e.message}
});
load();
})();