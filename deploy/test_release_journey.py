"""Synthetic full-journey QA: invite > legal consent > approve > login > finances.

No remote providers, no real driver data, no outgoing messages or production writes.
"""
import os
import sys
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient

with tempfile.TemporaryDirectory(prefix="movi_release_journey_") as folder:
    os.environ["CLUBE_DATA"] = folder
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    import app
    import legal_v8
    cli=TestClient(app.app,base_url="https://movi-qa.local")
    H={"X-Requested-With":"NOVAGENTE-V5"}
    admin_password="QaAdminPassword2026!"
    driver_password="QaDriverPassword2026!"

    with app.db() as conn:
        conn.execute(
            "INSERT INTO users(id,username,phash,role,status,name,created_at,must_change) "
            "VALUES(1,'qaadmin',?,'admin','active','Gestor Teste',?,0)",
            (app.password_hash(admin_password),app.now()))
        conn.commit()
    admin_login=cli.post("/api/login",json={"username":"qaadmin","password":admin_password},headers=H)
    assert admin_login.status_code==200,admin_login.text
    assert cli.get("/api/me").json()["user"]["role"]=="admin"
    invite=cli.post("/api/admin/invites",json={},headers=H)
    assert invite.status_code==200,invite.text
    token=invite.json()["invite"]
    print("01 - real session login: admin role + individual invitation: PASS")

    assert cli.post("/api/logout",json={},headers=H).status_code==200
    legal=cli.get("/api/legal").json()
    required={x["id"]:True for x in legal["required"]}
    options={"assisted_entry":False,"sharing":False,"insights":False,"marketing":False,
             "documents":False,"identity_collection":False}
    driver_enroll={"name":"Motorista Fictício","username":"qateste1",
                  "password":driver_password,"invite":token,"accepted_rules":True,
                  "legal":{"version":legal["version"],"required":required,"optional":options}}
    no_accept=cli.post("/api/enroll",json={**driver_enroll,"legal":{}},headers=H)
    assert no_accept.status_code in (409,422)
    registered=cli.post("/api/enroll",json=driver_enroll,headers=H)
    assert registered.status_code==200,registered.text
    assert cli.post("/api/login",json={"username":"qateste1","password":driver_password},headers=H).status_code==401
    print("02 - terms required; invited driver stays pending until admin approves: PASS")

    assert cli.post("/api/login",json={"username":"qaadmin","password":admin_password},headers=H).status_code==200
    with app.db() as conn:
        driver_id=conn.execute("SELECT id FROM users WHERE username='qateste1'").fetchone()["id"]
    assert cli.post("/api/admin/activate/"+str(driver_id),json={},headers=H).status_code==200
    assert cli.post("/api/logout",json={},headers=H).status_code==200
    assert cli.post("/api/login",json={"username":"qateste1","password":driver_password},headers=H).status_code==200
    assert cli.get("/api/me").json()["user"]["role"]=="driver"
    assert cli.get("/meu-fluxo").status_code==200
    assert cli.get("/api/admin/finance/auto-report").status_code==403
    print("03 - approved driver opens private dashboard but not admin controls: PASS")

    r=cli.get("/api/finance/flow?month=2026-10")
    assert r.status_code==200,r.text
    assert r.json()["result_cents"]==0
    created=cli.post("/api/finance/recurring",json={
        "title":"Aluguel do carro","category":"Veículo","amount":"850.50",
        "due_day":12,"starts":"2026-10","active":True
    },headers=H)
    assert created.status_code==200,created.text
    updated=cli.get("/api/finance/flow?month=2026-10").json()
    assert updated["scheduled_expenses_total_cents"]==85050
    assert updated["expense_cents"]==0
    print("04 - monthly planned expenses visible but not booked as paid: PASS")

    paid=cli.post("/api/finances",json={"kind":"income","category":"APLICATIVO",
        "amount":"250.00","date":"2026-10-30","note":"Corrida de teste"},headers=H)
    assert paid.status_code==200,paid.text
    expense=cli.post("/api/finances",json={"kind":"expense","category":"Combustível",
        "amount":"45.00","date":"2026-10-30","note":"Combustível fictício"},headers=H)
    assert expense.status_code==200,expense.text
    s=cli.get("/api/finance/flow?month=2026-10").json()
    assert (s["income_cents"],s["expense_cents"],s["result_cents"])==(25000,4500,20500)
    assert s["scheduled_expenses_total_cents"]==85050
    print("05 - confirmed movements correctly feed balance; no fixed-expense double count: PASS")

    assert cli.get("/api/finance/auto-report").json()["enabled"] is False
    attempted=cli.put("/api/finance/auto-report",json={
        "enabled":True,"frequency":"weekly","weekday":1,"hour":9
    },headers=H)
    assert attempted.status_code==403,attempted.text
    assert cli.put("/api/finance-agent/consent",json={
        "enabled":True,"media_ai":False,"trends":False,"offers":False,"text_ai":False
    },headers=H).status_code==200
    attempted=cli.put("/api/finance/auto-report",json={
        "enabled":True,"frequency":"weekly","weekday":1,"hour":9
    },headers=H)
    assert attempted.status_code==409,attempted.text
    assert cli.get("/api/finance/auto-report").json()["enabled"] is False
    print("06 - separate agent consent and verified phone link required: PASS")

    assert cli.post("/api/logout",json={},headers=H).status_code==200
    assert cli.get("/api/finance/flow").status_code==401
    assert cli.get("/meu-fluxo").status_code==401
    with app.db() as conn:
        assert conn.execute("PRAGMA quick_check(1)").fetchone()[0]=="ok"
    print("07 - logout revokes private financial access and DB integrity stays healthy: PASS")

print("7/7 release journey tests passed. All data fictitious, no WAHA/Pix calls.")
