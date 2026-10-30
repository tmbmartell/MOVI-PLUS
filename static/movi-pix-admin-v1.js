(function(){"use strict";
const $=id=>document.getElementById(id);
async function api(path,method="GET",data){
 const r=await fetch(path,{method,credentials:"same-origin",cache:"no-store",headers:{"Content-Type":"application/json","X-Requested-With":"NOVAGENTE-V5"},body:data?JSON.stringify(data):undefined});
 const o=await r.json().catch(()=>({}));if(!r.ok)throw Error(o.detail||"Não foi possível concluir a operação");return o;
}
const rf=$("receiver-form"),df=$("driver-form");
function field(form,k){return form.elements.namedItem(k)}
async function load(){
 try{
  const [p,users,d]=await Promise.all([api("/api/admin/pix"),api("/api/admin/pix/drivers"),api("/api/admin/pix/declarations")]);
  field(rf,"key").value=p.key||"";field(rf,"recipient_name").value=p.recipient_name||"";
  field(rf,"bank_verified").checked=!!p.bank_verified;field(rf,"enabled").checked=!!p.enabled;
  $("receiver-status").textContent=p.enabled?"Chave ativa para os motoristas autorizados.":"Chave não liberada para os motoristas.";
  const select=$("driver-select");select.replaceChildren(new Option("Selecione um motorista",""));
  (users.items||[]).forEach(u=>{const opt=new Option(u.name+" (#"+u.id+")"+(u.monthly_cents?" · R$ "+(u.monthly_cents/100).toFixed(2):""),String(u.id));opt.dataset.monthly=String(u.monthly_cents||"");opt.dataset.active=String(u.active??true);select.add(opt)});
  select.addEventListener("change",()=>{const o=select.selectedOptions[0];field(df,"monthly_amount").value=o?.dataset.monthly?(Number(o.dataset.monthly)/100).toFixed(2):"";field(df,"active").checked=o?.dataset.active!=="0"});
  const box=$("declared-list");box.replaceChildren();
  if(!(d.items||[]).length){box.textContent="Nenhuma declaração registrada.";return}
  d.items.forEach(x=>{const row=document.createElement("p");row.className="note";row.textContent=x.entry_day+" · "+x.name+" · "+x.slot+" · R$ "+(x.expected_cents/100).toFixed(2).replace(".",",")+" · declarado, não conciliado";box.append(row)});
 }catch(e){$("receiver-status").textContent=e.message}
}
rf.addEventListener("submit",async ev=>{ev.preventDefault();try{
 const data={key:field(rf,"key").value,recipient_name:field(rf,"recipient_name").value,bank_verified:field(rf,"bank_verified").checked,enabled:field(rf,"enabled").checked};
 await api("/api/admin/pix","PUT",data);$("receiver-status").textContent="Configuração salva.";await load()
}catch(e){$("receiver-status").textContent=e.message}});
df.addEventListener("submit",async ev=>{ev.preventDefault();try{
 const uid=$("driver-select").value;if(!uid)throw Error("Selecione o motorista");
 await api("/api/admin/pix/driver/"+encodeURIComponent(uid),"PUT",{monthly_amount:field(df,"monthly_amount").value,active:field(df,"active").checked});
 $("driver-status").textContent="Parcela configurada.";await load()
}catch(e){$("driver-status").textContent=e.message}});
load();
})();