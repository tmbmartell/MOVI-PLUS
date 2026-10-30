"""Exact cent amounts across month lengths and the three daily slots."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from finance_deposit_planner_v1 import month_plan

examples=[
    ("2026-02",28),
    ("2028-02",29),
    ("2026-04",30),
    ("2026-10",31),
]
for month,length in examples:
    plan=month_plan(month,150000)
    assert plan["days_in_month"]==length and len(plan["days"])==length
    assert sum(d["total_cents"] for d in plan["days"])==150000
    assert all(len(d["slots"])==3 for d in plan["days"])
    assert all(sum(slot["amount_cents"] for slot in day["slots"])==day["total_cents"]
               for day in plan["days"])
    assert all(slot["status"]=="previsto" for day in plan["days"] for slot in day["slots"])
    print(f"PASS {month}: {length} days, precisely R$ 1.500,00, no additional money")
    if length==30:
        assert all([s["amount_cents"] for s in d["slots"]]==[1500,1500,2000] for d in plan["days"])
    if length==31:
        assert all(d["total_cents"]<=4839 for d in plan["days"])
    if length==28:
        assert all(d["total_cents"]>=5357 for d in plan["days"])
print("01 - correct February/leap year/30/31 day totals and 3-shift proportions: PASS")

for total in (1,2,3,4,5,49,100,12345,10000000000):
    plan=month_plan("2026-02",total,weights=(1,1,1))
    assert sum(sum(slot["amount_cents"] for slot in day["slots"])
               for day in plan["days"])==total
    assert all(slot["amount_cents"]>=0 for day in plan["days"] for slot in day["slots"])
print("02 - 1-cent to large values allocated exactly without negative balances: PASS")

for args in (("2026-13",150000, (15,15,20)),("2026/10",150000,(15,15,20)),
             ("2026-02",-1,(15,15,20)),("2026-02",100.0,(15,15,20)),
             ("2026-02",True,(15,15,20)),("2026-02",100,(15,0,20)),
             ("2026-02",100,(15,20)),("2026-02",100,(15,15,True))):
    try:month_plan(*args)
    except ValueError:pass
    else:raise AssertionError(f"Accepted invalid value: {args}")
print("03 - invalid months, values and weights rejected: PASS")

assert month_plan("2026-02",150000)["provider_connected"] is False
print("04 - pure planning never suggests a payment was processed: PASS")
print("4/4 deposit planning tests PASS. No bank/API/WhatsApp connection.")
