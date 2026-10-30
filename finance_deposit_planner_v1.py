"""MOVI+ P1: deterministic installment *planning* only. NO Pix/WAHA actions.

Use a monthly capped plan, never naively repeat R$ 15+15+20 for 31 days.
The actual payment provider must be confirmed and separately integrated.
"""
import calendar
import datetime as dt
import re

MONTH = re.compile(r"^(20\d{2}|2100)-(0[1-9]|1[0-2])$")
SLOTS = ("manha", "tarde", "noite")
DEFAULT_WEIGHTS = (15, 15, 20)

def _allocation(total, weights):
    """Hamilton rounding: all integer cents allocated exactly and nonnegatively."""
    if not isinstance(total,int) or isinstance(total,bool) or total<0:
        raise ValueError("Total deve ser um inteiro não negativo em centavos")
    if (not isinstance(weights,(tuple,list)) or len(weights)==0 or
        any(not isinstance(w,int) or isinstance(w,bool) or w<=0 for w in weights)):
        raise ValueError("Pesos devem ser inteiros positivos")
    base=sum(weights)
    raw=[divmod(total*w,base) for w in weights]
    allocations=[q for q,r in raw]
    missing=total-sum(allocations)
    # Largest remainder, stable tie-breaking. At most one extra cent per slot.
    ranked=sorted(range(len(weights)),key=lambda i:(-raw[i][1],i))
    for i in ranked[:missing]:
        allocations[i]+=1
    if sum(allocations)!=total:
        raise AssertionError("Falha interna de arredondamento")
    return allocations

def month_plan(month, installment_cents, weights=DEFAULT_WEIGHTS):
    """Returns exact, calendar-aware 3-turn projection. No payment status."""
    if not isinstance(month,str) or not MONTH.fullmatch(month):
        raise ValueError("Mês deve estar em AAAA-MM entre 2000 e 2100")
    if (not isinstance(installment_cents,int) or isinstance(installment_cents,bool)
        or installment_cents<=0 or installment_cents>100_000_000_00):
        raise ValueError("Parcela deve ser um inteiro positivo de centavos")
    if len(weights)!=3:
        raise ValueError("O Clube opera em três turnos")
    year,mon=map(int,month.split("-"))
    days=calendar.monthrange(year,mon)[1]
    daily=_allocation(installment_cents,[1]*days)
    result=[]
    for index,amount in enumerate(daily,1):
        portions=_allocation(amount,weights)
        date=dt.date(year,mon,index).isoformat()
        result.append({"date":date,"total_cents":amount,"slots":[
            {"slot":slot,"amount_cents":cents,"status":"previsto"}
            for slot,cents in zip(SLOTS,portions)
        ]})
    if sum(d["total_cents"] for d in result)!=installment_cents:
        raise AssertionError("Projeção ultrapassou a parcela")
    return {"month":month,"installment_cents":installment_cents,
            "days_in_month":days,"slots_per_day":3,"weights":list(weights),
            "days":result,"provider_connected":False,
            "notice":"Somente previsão matemática: não gera cobrança, Pix ou recibo."}
