"""Testes isolados, sem conta real, sem WhatsApp ou Pix."""
import os
import sys
import tempfile

from fastapi.testclient import TestClient

with tempfile.TemporaryDirectory(prefix="movi_flow_test_") as directory:
    os.environ["CLUBE_DATA"] = directory
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    import app
    from finance_flow_v1 import build_flow

    client = TestClient(app.app, base_url="https://movi-qa.local")
    assert client.get("/api/finance/flow").status_code == 401
    assert client.get("/meu-fluxo").status_code == 401
    print("01 - summary and page require driver login: PASS")

    with app.db() as c:
        for uid in (2, 3):
            c.execute(
                "INSERT INTO users(id,username,phash,role,status,name,created_at,must_change) VALUES(?,?,?,?,?,?,?,0)",
                (uid, "test" + str(uid), "test", "driver", "active", "Fake", app.now())
            )
        app.save_profile(c, 2, {
            "vehicle_installment": 900,
            "other_debts": 100,
            "household_expenses": 1500,
            "monthly_maintenance": 200
        })
        for uid, kind, category, cents, date in (
            (2, "income", "APLICATIVO", 100000, "2026-10-11"),
            (2, "expense", "Combustível", 25000, "2026-10-11"),
            (2, "expense", "Casa e contas", 15000, "2026-10-12"),
            (2, "income", "OUTROS", 15000, "2026-09-05"),
            (3, "income", "APLICATIVO", 900000, "2026-10-11")
        ):
            c.execute(
                "INSERT INTO transactions(uid,kind,category,amount_cents,entry_date,note,at) VALUES(?,?,?,?,?,?,?)",
                (uid, kind, category, cents, date, "", app.now())
            )
        c.commit()
    app.app.dependency_overrides[app.driver] = lambda: {"id": 2, "role": "driver"}
    response = client.get("/api/finance/flow?month=2026-10")
    assert response.status_code == 200, response.text
    data = response.json()
    assert (data["income_cents"], data["expense_cents"], data["result_cents"]) == (100000, 40000, 60000)
    assert data["positive"] is True
    assert data["recurring_commitments_total_cents"] == 100000
    assert data["expense_cents"] == 40000   # no double counting declared commitments
    assert len(data["expense_categories"]) == 2
    assert data["other_monthly_estimates"][0]["amount_cents"] == 150000
    assert "900000" not in response.text
    print("02 - real totals, category split, declarations not double-counted, account isolation: PASS")

    older = client.get("/api/finance/flow?month=2026-09").json()
    assert older["has_data"] is True and older["income_cents"] == 15000
    empty_month = client.get("/api/finance/flow?month=2026-08").json()
    assert empty_month["has_data"] is False and empty_month["income_cents"] == 0
    for bad in ("2026-13", "x", "2026/10", "2026-00"):
        assert client.get("/api/finance/flow?month=" + bad).status_code == 422
    print("03 - month filter, empty month and invalid input: PASS")

    assert client.get("/meu-fluxo").status_code == 200
    assert "MOVI+" in client.get("/meu-fluxo").text
    app.app.dependency_overrides.clear()
    print("04 - responsive page only after authentication: PASS")

    with app.db() as c:
        c.execute(
            "INSERT INTO users(id,username,phash,role,status,name,created_at,must_change) VALUES(?,?,?,?,?,?,?,0)",
            (1, "admin_test", "test", "admin", "active", "Fake admin", app.now())
        )
        c.execute(
            "INSERT INTO sessions(hash,uid,expires) VALUES(?,?,?)",
            (app.sha("admin-test-token"), 1, app.stamp() + 3600)
        )
        c.commit()
    client.cookies.set("clube_session", "admin-test-token", secure=True)
    assert client.get("/api/finance/flow").status_code == 403
    assert client.get("/meu-fluxo").status_code == 403
    print("05 - administrator cannot open a driver's private statement: PASS")

print("5/5 isolated flow report tests passed. No real user data and no WAHA sends.")
