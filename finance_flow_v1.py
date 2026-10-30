"""Resumo financeiro leve e privado do motorista (somente dados confirmados).
Não acessa banco, não confirma Pix e não envia mensagens automaticamente.
"""
import datetime
import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app import ROOT, db, driver, profile
from finance_agent_conversation_v2 import month_data

router = APIRouter()
TZ = ZoneInfo("America/Porto_Velho")
# Os valores abaixo vêm do questionário e NÃO são despesas pagas.
RECURRING = (
    ("vehicle_installment", "Parcela mensal do veículo"),
    ("other_debts", "Parcelas mensais de outras dívidas"),
)
ESTIMATES = (
    ("household_expenses", "Despesas mensais da família (estimativa)"),
    ("monthly_maintenance", "Reserva mensal para manutenção (meta)"),
)

def _reported_cents(value):
    if value in (None, "") or isinstance(value, bool):
        return 0
    try:
        number = Decimal(str(value))
        if not number.is_finite() or number <= 0:
            return 0
        return int((number * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    except (InvalidOperation, ValueError, TypeError):
        return 0

def _month(value):
    if not value:
        return datetime.datetime.now(TZ).strftime("%Y-%m")
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", value):
        raise HTTPException(422, "Informe o mês no formato AAAA-MM")
    return value

def build_flow(c, uid, requested_month=""):
    month = _month(requested_month)
    at = datetime.datetime(int(month[:4]), int(month[5:]), 1, tzinfo=TZ)
    data = month_data(c, uid, at)
    p = profile(c, uid)
    commitments = [
        {"label": label, "amount_cents": _reported_cents(p.get(key))}
        for key, label in RECURRING if _reported_cents(p.get(key)) > 0
    ]
    estimates = [
        {"label": label, "amount_cents": _reported_cents(p.get(key))}
        for key, label in ESTIMATES if _reported_cents(p.get(key)) > 0
    ]
    expense_categories = [
        {"label": str(name)[:60], "amount_cents": int(amount)}
        for name, amount in data["categories"] if int(amount) > 0
    ]
    # Uma parcela pode estar registrada também como despesa: não somar os dois
    # conjuntos nem deduzir "saldo disponível" ou dinheiro já pago.
    return {
        "month": month,
        "label": data["label"],
        "has_data": data["has_data"],
        "income_cents": data["income"],
        "expense_cents": data["expense"],
        "result_cents": data["balance"],
        "positive": data["balance"] >= 0 if data["has_data"] else None,
        "expense_categories": expense_categories,
        "income_by_channel": data["income_labels"],
        "pending_suggestions": data["pending"],
        "recurring_commitments_declared": commitments,
        "recurring_commitments_total_cents": sum(x["amount_cents"] for x in commitments),
        "other_monthly_estimates": estimates,
        "notice": "Somente lançamentos registrados/confirmados. O resultado não é saldo bancário. Compromissos e estimativas declarados não são comprovantes de pagamento e não são somados novamente às despesas.",
    }

@router.get("/api/finance/flow")
def finance_flow(month: str = "", u=Depends(driver)):
    with db() as c:
        return build_flow(c, u["id"], month)

@router.get("/meu-fluxo")
def finance_flow_page(u=Depends(driver)):
    # URL protegida pelo mesmo cookie HttpOnly do MOVI+.
    return FileResponse(ROOT / "static" / "movi-fluxo-v1.html", media_type="text/html")
