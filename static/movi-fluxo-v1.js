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
  byId("month").addEventListener("change", load);
  load();
})();
