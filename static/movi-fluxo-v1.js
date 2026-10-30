/* MOVI+ · visão financeira leve; nunca insere HTML de dados de usuário. */
(function () {
  "use strict";
  var byId = function (id) { return document.getElementById(id); };
  var money = function (cents) {
    return (Number(cents || 0) / 100).toLocaleString("pt-BR", {style:"currency",currency:"BRL"});
  };
  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text !== undefined) node.textContent = text;
    return node;
  }
  function empty(root, text) {
    root.replaceChildren(el("p", "small", text));
  }
  function lines(root, items, emptyMessage) {
    root.replaceChildren();
    if (!items.length) return empty(root, emptyMessage);
    items.forEach(function (x) {
      var line = el("div", "line");
      line.append(el("span", "", x.label), el("strong", "", money(x.amount_cents)));
      root.append(line);
    });
  }
  function render(data) {
    byId("period").textContent = data.label;
    byId("income").textContent = money(data.income_cents);
    byId("expense").textContent = money(data.expense_cents);
    var result = byId("result");
    result.textContent = money(data.result_cents);
    result.classList.toggle("negative", data.result_cents < 0);
    byId("result-note").textContent = !data.has_data
      ? "Nenhum lançamento confirmado neste mês."
      : data.positive ? "O mês está positivo pelos valores anotados." : "Os gastos anotados superaram os ganhos.";
    var root = byId("categories");
    root.replaceChildren();
    var categories = data.expense_categories || [];
    var max = categories.reduce(function (m, x) { return Math.max(m, x.amount_cents); }, 0);
    if (!categories.length) empty(root, "Sem despesas registradas neste mês.");
    categories.forEach(function (cat) {
      var line = el("div", "cat");
      line.append(el("span", "name", cat.label), el("span", "value", money(cat.amount_cents)));
      var bar = el("div", "bar");
      var fill = el("div", "fill");
      fill.style.width = (max ? Math.max(1, Math.min(100, cat.amount_cents / max * 100)) : 0) + "%";
      bar.append(fill);
      root.append(line, bar);
    });
    lines(byId("scheduled"), data.scheduled_expenses || [], "Nenhuma conta fixa prevista neste mês.");
    byId("scheduled-total").textContent = money(data.scheduled_expenses_total_cents);
    lines(byId("recurring"), data.recurring_commitments_declared || [], "Nenhuma parcela recorrente informada.");
    byId("recurring-total").textContent = money(data.recurring_commitments_total_cents);
    lines(byId("estimates"), data.other_monthly_estimates || [], "Nenhuma estimativa adicional informada.");
    byId("notice").textContent = data.notice;
    byId("pending").textContent = data.pending_suggestions
      ? String(data.pending_suggestions) + " lançamento(s) sugerido(s) ainda aguardam confirmação e não entram nos totais."
      : "";
  }
  async function load() {
    byId("error").hidden = true;
    var month = byId("month").value;
    try {
      var res = await fetch("/api/finance/flow?month=" + encodeURIComponent(month), {
        credentials: "same-origin", headers: {"Accept":"application/json"}, cache:"no-store"
      });
      if (res.status === 401 || res.status === 428) {
        throw new Error("Sua sessão precisa ser renovada. Entre no MOVI+ e abra Meu fluxo novamente.");
      }
      if (!res.ok) throw new Error("Não consegui carregar os dados deste mês.");
      render(await res.json());
      byId("content").hidden = false;
      await loadRecurringList();
    } catch (err) {
      byId("content").hidden = true;
      byId("error").hidden = false;
      byId("error").textContent = err.message || "Falha de conexão.";
    }
  }
  var parts = new Intl.DateTimeFormat("en-US", {
    timeZone:"America/Porto_Velho",year:"numeric",month:"2-digit"
  }).formatToParts(new Date());
  var year = parts.find(function (p) { return p.type === "year"; }).value;
  var monthNumber = parts.find(function (p) { return p.type === "month"; }).value;
  var localYearMonth = year + "-" + monthNumber;
  byId("month").value = localYearMonth;
  var selectedId = null, knownRecurring = [];
  var form = byId("recurring-form");
  function field(key) { return form.elements.namedItem(key); }
  function resetForm() {
    selectedId = null;
    form.reset();
    field("starts").value = byId("month").value;
    byId("save-recurring").textContent = "Salvar conta";
    byId("cancel-recurring").hidden = true;
  }
  function feedback(message) { byId("recurring-feedback").textContent = message; }
  async function recurringRequest(path, method, data) {
    var resp = await fetch(path, {
      method:method,credentials:"same-origin",cache:"no-store",
      headers:{"X-Requested-With":"NOVAGENTE-V5","Content-Type":"application/json"},
      body:data ? JSON.stringify(data) : undefined
    });
    var payload = await resp.json().catch(function(){return {};});
    if (!resp.ok) throw new Error(payload.detail || "Não foi possível salvar. Verifique os campos.");
    return payload;
  }
  async function loadRecurringList() {
    try {
      var resp = await fetch("/api/finance/recurring", {credentials:"same-origin",cache:"no-store"});
      if (!resp.ok) throw new Error("Não consegui carregar suas contas fixas.");
      knownRecurring = (await resp.json()).items || [];
      var root = byId("scheduled-manage");
      root.replaceChildren();
      if (!knownRecurring.length) empty(root, "Você ainda não cadastrou nenhuma conta recorrente.");
      knownRecurring.forEach(function (item) {
        var row = el("div","recurring-row");
        var label = el("div","");
        label.append(
          el("p","",item.title + " · " + money(item.amount_cents)),
          el("p","small","Dia " + item.due_day + " · " + item.category + (item.active?"":" · Pausada"))
        );
        var actions = el("div","recurring-actions");
        var edit = el("button","smallbtn","Editar");
        edit.type = "button";
        edit.addEventListener("click",function() {
          selectedId = item.id;
          field("title").value = item.title;
          field("category").value = item.category;
          field("amount").value = (item.amount_cents/100).toFixed(2);
          field("due_day").value = item.due_day;
          field("starts").value = item.starts;
          field("ends").value = item.ends || "";
          field("active").checked = item.active;
          byId("save-recurring").textContent = "Salvar alterações";
          byId("cancel-recurring").hidden = false;
          form.scrollIntoView({behavior:"smooth",block:"center"});
        });
        var del = el("button","smallbtn","Excluir");
        del.type = "button";
        del.addEventListener("click",async function() {
          if (!window.confirm("Excluir definitivamente esta conta recorrente?")) return;
          try {
            await recurringRequest("/api/finance/recurring/"+item.id,"DELETE");
            feedback("Conta removida.");
            if (selectedId === item.id) resetForm();
            await load();
          } catch(error) { feedback(error.message); }
        });
        actions.append(edit,del);
        row.append(label,actions);
        root.append(row);
      });
    } catch(error) {
      feedback(error.message || "Erro ao carregar as contas fixas.");
    }
  }
  form.addEventListener("submit",async function(ev) {
    ev.preventDefault();
    var item = {
      title:field("title").value.trim(),category:field("category").value,
      amount:field("amount").value,due_day:Number(field("due_day").value),
      starts:field("starts").value,ends:field("ends").value,
      active:field("active").checked
    };
    try {
      await recurringRequest("/api/finance/recurring"+(selectedId?"/"+selectedId:""), selectedId?"PUT":"POST",item);
      resetForm(); feedback("Conta salva com sucesso."); await load();
    } catch(error) { feedback(error.message); }
  });
  byId("cancel-recurring").addEventListener("click",function(){resetForm();feedback("");});
  byId("month").addEventListener("change", load);
  resetForm();
  load();
})();
