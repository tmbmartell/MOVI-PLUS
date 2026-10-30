/* MOVI+ opt-in monthly/weekly WhatsApp report preferences; separate from finance consent. */
(function(){
  "use strict";
  const $ = id => document.getElementById(id);
  const form = $("auto-report-form");
  if (!form) return;
  const enabled = $("report-enabled"),frequency=$("report-frequency"),
        weekday=$("report-weekday"),hour=$("report-hour"),feedback=$("auto-report-info");
  function sync(){
    weekday.disabled = frequency.value !== "weekly";
  }
  async function request(method,body){
    const response=await fetch("/api/finance/auto-report",{
      method,credentials:"same-origin",cache:"no-store",
      headers:method==="PUT"?{"Content-Type":"application/json","X-Requested-With":"NOVAGENTE-V5"}:{"Accept":"application/json"},
      body:method==="PUT"?JSON.stringify(body):undefined
    });
    const result=await response.json().catch(()=>({}));
    if(!response.ok) throw new Error(result.detail||"Não foi possível salvar suas escolhas.");
    return result;
  }
  async function start(){
    try{
      const x=await request("GET");
      enabled.checked=Boolean(x.enabled);
      frequency.value=x.frequency;
      weekday.value=String(x.weekday);
      hour.value=String(x.hour);
      sync();
      if(!x.linked){
        feedback.textContent="Seu WhatsApp ainda não está vinculado. Para ativar, abra Foto e Áudio > WhatsApp no MOVI+ e siga as instruções. Você pode deixar o recebimento desativado.";
      }else if(!x.financial_agent_authorized){
        feedback.textContent="Ative a autorização do agente financeiro antes de optar por mensagens automáticas.";
      }else{
        feedback.textContent=x.enabled?"Preferência registrada. O envio depende da ativação segura do Clube.":"Envio automático desligado. Você controla essa escolha.";
      }
    }catch(error){feedback.textContent=error.message||"Não consegui consultar sua preferência.";}
  }
  form.addEventListener("submit",async function(ev){
    ev.preventDefault();
    try{
      const x=await request("PUT",{
        enabled:enabled.checked,frequency:frequency.value,
        weekday:Number(weekday.value),hour:Number(hour.value)
      });
      feedback.textContent=x.enabled?"Autorização registrada. Você pode desligar a qualquer momento.":"Envio automático desativado.";
    }catch(error){feedback.textContent=error.message||"Não foi possível salvar.";}
  });
  frequency.addEventListener("change",sync);
  start();
})();
