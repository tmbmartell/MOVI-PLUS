"""Contrato de gastos fixos: armazenamento isolado, CRUD, meses e sem baixa automática."""
import os
import sys
import tempfile

from fastapi.testclient import TestClient

with tempfile.TemporaryDirectory(prefix="movi_recurring_test_") as temporary:
    os.environ["CLUBE_DATA"] = temporary
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    import app

    client = TestClient(app.app, base_url="https://movi-qa.local")
    headers = {"X-Requested-With": "NOVAGENTE-V5"}
    create_url = "/api/finance/recurring"
    assert client.get(create_url).status_code == 401
    assert client.post(create_url,json={},headers=headers).status_code == 401
    print("01 - driver authentication required: PASS")

    with app.db() as conn:
        for user_id, role in ((1,"admin"),(2,"driver"),(3,"driver")):
            conn.execute(
                "INSERT INTO users(id,username,phash,role,status,name,created_at,must_change)"
                " VALUES(?,?,?,?,?,?,?,0)",
                (user_id, f"fake{user_id}", "notused", role, "active", f"Fake {user_id}", app.now())
            )
        conn.commit()

    def as_user(uid,role):
        app.app.dependency_overrides[app.driver] = lambda: {"id":uid,"role":role}

    as_user(2,"driver")
    valid = {"title":"Aluguel do carro","category":"Veículo","amount":"1200.50",
             "due_day":31,"starts":"2026-10","ends":"2026-12","active":True}
    result = client.post(create_url,json=valid,headers=headers)
    assert result.status_code == 200, result.text
    rid = result.json()["id"]
    data = client.get(create_url).json()
    assert len(data["items"]) == 1 and data["total_cents"] == 120050
    assert data["items"][0]["title"] == "Aluguel do carro"
    print("02 - recurring fixed expense created and listed: PASS")

    octo = client.get(create_url+"?month=2026-10").json()
    nov = client.get(create_url+"?month=2026-11").json()
    feb = client.get(create_url+"?month=2027-02").json()
    assert octo["items"][0]["due_date"] == "2026-10-31"
    assert nov["items"][0]["due_date"] == "2026-11-30"
    assert not feb["items"]
    assert client.get(create_url+"?month=2026-13").status_code == 422
    print("03 - active months and short-month due date correct: PASS")

    flow = client.get("/api/finance/flow?month=2026-11").json()
    assert flow["scheduled_expenses_total_cents"] == 120050
    assert flow["result_cents"] == 0 and flow["expense_cents"] == 0
    assert flow["scheduled_expenses"][0]["due_date"] == "2026-11-30"
    with app.db() as conn:
        assert conn.execute("SELECT COUNT(*) FROM transactions WHERE uid=2").fetchone()[0] == 0
    print("04 - scheduled amounts NEVER post ledger or distort result: PASS")

    as_user(3,"driver")
    assert client.get(create_url).json()["items"] == []
    assert client.put(f"{create_url}/{rid}",json=valid,headers=headers).status_code == 404
    assert client.delete(f"{create_url}/{rid}",headers=headers).status_code == 404
    as_user(1,"admin")
    # An authentic admin cookie must not receive private data (dependency overrides bypass role checking).
    app.app.dependency_overrides.clear()
    with app.db() as conn:
        conn.execute("INSERT INTO sessions(hash,uid,expires) VALUES(?,?,?)",
                     (app.sha("admin-recurring-test"),1,app.stamp()+3600))
        conn.commit()
    client.cookies.set("clube_session","admin-recurring-test")
    assert client.get(create_url).status_code == 403
    assert client.post(create_url,json=valid,headers=headers).status_code == 403
    client.cookies.clear()
    as_user(2,"driver")
    print("05 - other driver and administrator cannot read or change private items: PASS")

    for invalid in (
        {**valid,"amount":0},
        {**valid,"due_day":0},
        {**valid,"ends":"2026-09"},
        {**valid,"title":"X"},
        {**valid,"active":"false"},
        {**valid,"extra":"value"},
    ):
        assert client.post(create_url,json=invalid,headers=headers).status_code == 422
    assert client.post(create_url,json=valid).status_code == 403
    print("06 - input boundaries and CSRF protection: PASS")

    changed = {**valid, "amount":"840.00","due_day":5,"active":False}
    assert client.put(f"{create_url}/{rid}",json=changed,headers=headers).status_code == 200
    assert client.get(create_url).json()["items"][0]["active"] is False
    assert client.get(create_url+"?month=2026-11").json()["items"] == []
    changed["active"] = True
    assert client.put(f"{create_url}/{rid}",json=changed,headers=headers).status_code == 200
    assert client.get(create_url+"?month=2026-11").json()["total_cents"] == 84000
    print("07 - edit/pause/reactivate lifecycle: PASS")

    assert client.delete(f"{create_url}/{rid}",headers=headers).status_code == 200
    assert client.delete(f"{create_url}/{rid}",headers=headers).status_code == 404
    assert client.get(create_url).json()["items"] == []
    with app.db() as conn:
        assert conn.execute("SELECT COUNT(*) FROM audit WHERE actor=2 AND action LIKE 'recurring:%'").fetchone()[0] == 4
    print("08 - deletion and audit trail: PASS")

print("8/8 recurring expense contract tests PASS; no real bank or WhatsApp calls.")
